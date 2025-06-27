import logging
import requests
import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

# Configure root logger
logger = logging.getLogger("token_analyzer")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%dT%H:%M:%SZ")
handler.setFormatter(formatter)
logger.addHandler(handler)


def summarize_metrics(metrics: List[float]) -> Dict[str, float]:
    """
    Compute average, maximum, and minimum of a list of numeric metrics.
    Returns zeros if the list is empty.
    """
    if not metrics:
        return {"avg": 0.0, "max": 0.0, "min": 0.0}
    return {
        "avg": sum(metrics) / len(metrics),
        "max": max(metrics),
        "min": min(metrics),
    }


def fetch_json(api_url: str, timeout: float = 5.0, retries: int = 3) -> Optional[Dict[str, Any]]:
    """
    Fetch JSON data from the given URL with retry logic.
    Returns parsed JSON or None on failure.
    """
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(api_url, timeout=timeout)
            resp.raise_for_status()
            logger.info("Fetched JSON from %s (attempt %d)", api_url, attempt)
            return resp.json()
        except requests.RequestException as e:
            logger.warning("Attempt %d failed for %s: %s", attempt, api_url, e)
            time.sleep(1)
    logger.error("All %d attempts failed for %s", retries, api_url)
    return None


@dataclass
class Transaction:
    hash: str
    value: float
    timestamp: datetime

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Transaction":
        return Transaction(
            hash=data.get("hash", ""),
            value=float(data.get("value", 0.0)),
            timestamp=datetime.fromisoformat(data.get("timestamp"))
        )


class WalletAnalyzer:
    """
    Analyze wallet transactions and detect high-value anomalies.
    """
    def __init__(self, address: str, threshold: float = 10_000.0):
        self.address = address
        self.threshold = threshold
        self.transactions: List[Transaction] = []

    def load(self, tx_list: List[Dict[str, Any]]) -> None:
        """
        Parse and load raw transaction dictionaries.
        """
        self.transactions = [Transaction.from_dict(tx) for tx in tx_list]
        logger.info("Loaded %d transactions for %s", len(self.transactions), self.address)

    def detect_anomalies(self) -> List[Transaction]:
        """
        Return all transactions with value exceeding the threshold.
        """
        anomalies = [tx for tx in self.transactions if tx.value > self.threshold]
        logger.info("Detected %d anomalies (threshold=%.2f)", len(anomalies), self.threshold)
        return anomalies

    def metrics(self) -> Dict[str, float]:
        """
        Summarize transaction values with avg/max/min.
        """
        values = [tx.value for tx in self.transactions]
        summary = summarize_metrics(values)
        logger.info("Transaction metrics: %s", summary)
        return summary


def calculate_risk_score(
    price_change: float,
    liquidity: float,
    flags: List[str],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Compute a risk score in [0.0, 1.0] based on:
      - price_change: absolute percent change (0.0–1.0)
      - liquidity: normalized liquidity (0.0–1.0)
      - flags: list of risk indicators (e.g., ['suspicious'])
    """
    weights = weights or {"price": 0.4, "liquidity": 0.4, "flags": 0.2}

    pct = min(abs(price_change), 1.0)
    illiq = 1.0 - max(min(liquidity, 1.0), 0.0)
    flag_penalty = flags.count("suspicious") / len(flags) if flags else 0.0

    raw_score = pct * weights["price"] + illiq * weights["liquidity"] + flag_penalty * weights["flags"]
    score = max(0.0, min(raw_score, 1.0))
    logger.info(
        "Risk score: %.3f (price=%.3f, illiq=%.3f, penalty=%.3f)",
        score, pct, illiq, flag_penalty
    )
    return round(score, 2)


def classify_risk(score: float) -> str:
    """
    Map a normalized score to risk categories.
    """
    if score > 0.8:
        return "High Risk"
    if score > 0.5:
        return "Moderate Risk"
    return "Low Risk"


# Example workflow
if __name__ == "__main__":
    api_url = "https://api.example.com/token/XYZ123"
    data = fetch_json(api_url)
    if data:
        analyzer = WalletAnalyzer(address="XYZ123", threshold=5_000.0)
        analyzer.load(data.get("transactions", []))
        anomalies = analyzer.detect_anomalies()
        analyzer.metrics()

        score = calculate_risk_score(
            price_change=data.get("price_change", 0.0),
            liquidity=data.get("liquidity", 1.0),
            flags=data.get("flags", [])
        )
        category = classify_risk(score)
        print(f"Token {data.get('symbol')} classified as {category}")
    else:
        logger.error("Failed to fetch token data")
