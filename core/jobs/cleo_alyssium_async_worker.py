import logging
import json
import requests
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger("token_analyzer")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%dT%H:%M:%SZ")
handler.setFormatter(formatter)
logger.addHandler(handler)


def summarize_metrics(metrics: List[float]) -> Dict[str, float]:
    """
    Return basic statistics for a list of numeric metrics.
    """
    if not metrics:
        return {"avg": 0.0, "max": 0.0, "min": 0.0}
    return {
        "avg": sum(metrics) / len(metrics),
        "max": max(metrics),
        "min": min(metrics),
    }


def fetch_token_data(api_url: str, timeout: float = 5.0, retries: int = 3) -> Optional[Dict[str, Any]]:
    """
    Fetch JSON token data from an HTTP API with simple retry logic.
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(api_url, timeout=timeout)
            response.raise_for_status()
            logger.info("Fetched data from %s (attempt %d)", api_url, attempt)
            return response.json()
        except requests.RequestException as e:
            logger.warning("Attempt %d failed: %s", attempt, e)
            time.sleep(1)
    logger.error("All %d attempts failed for %s", retries, api_url)
    return None


@dataclass
class Transaction:
    hash: str
    value: float
    timestamp: datetime

    @staticmethod
    def from_dict(data: Dict[str, Any]]) -> "Transaction":
        return Transaction(
            hash=data.get("hash", ""),
            value=float(data.get("value", 0)),
            timestamp=datetime.fromisoformat(data.get("timestamp"))
        )


class WalletAnalyzer:
    """
    Analyze wallet transactions for anomalies.
    """

    def __init__(self, address: str, anomaly_threshold: float = 10_000.0):
        self.address = address
        self.anomaly_threshold = anomaly_threshold
        self.transactions: List[Transaction] = []

    def load_transactions(self, tx_list: List[Dict[str, Any]]) -> None:
        """
        Load and parse transactions from raw dicts.
        """
        self.transactions = [Transaction.from_dict(tx) for tx in tx_list]
        logger.info("Loaded %d transactions for %s", len(self.transactions), self.address)

    def detect_anomalies(self) -> List[Transaction]:
        """
        Return transactions whose value exceeds the anomaly threshold.
        """
        anomalies = [tx for tx in self.transactions if tx.value > self.anomaly_threshold]
        logger.info("Detected %d anomalies (threshold=%.2f)", len(anomalies), self.anomaly_threshold)
        return anomalies


def classify_token(risk_score: float) -> str:
    """
    Classify token risk level based on a normalized score (0.0–1.0).
    """
    if risk_score > 0.8:
        return "High Risk"
    if risk_score > 0.5:
        return "Moderate Risk"
    return "Low Risk"


def calculate_risk_score(
    price_change: float,
    liquidity: float,
    flags: List[str],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate a risk score between 0.0 and 1.0 based on:
      - price_change: absolute percentage change (e.g. 0.05 for 5%)
      - liquidity: on-chain liquidity normalized to [0.0–1.0]
      - flags: list of string indicators (e.g. ['suspicious', 'large_sell'])
    """
    weights = weights or {"price": 0.4, "liquidity": 0.4, "flags": 0.2}

    # Normalize inputs
    pct_change = min(abs(price_change), 1.0)
    illiquidity = 1.0 - max(min(liquidity, 1.0), 0.0)

    # Flag penalty: proportion of known risky flags
    total_flags = len(flags)
    penalty = flags.count("suspicious") / total_flags if total_flags else 0.0

    # Raw score computation
    raw = (
        pct_change * weights["price"]
        + illiquidity * weights["liquidity"]
        + penalty * weights["flags"]
    )

    # Clamp to [0.0, 1.0]
    score = max(0.0, min(raw, 1.0))
    logger.info(
        "Risk score computed: %.3f (price=%.3f, illiq=%.3f, penalty=%.3f)",
        score, pct_change, illiquidity, penalty
    )
    return score


# Example usage
if __name__ == "__main__":
    api_url = "https://api.example.com/token/XYZ"
    data = fetch_token_data(api_url)
    if data:
        analyzer = WalletAnalyzer(address="XYZ", anomaly_threshold=5_000)
        analyzer.load_transactions(data.get("transactions", []))
        anomalies = analyzer.detect_anomalies()

        risk = calculate_risk_score(
            price_change=data.get("price_change", 0.0),
            liquidity=data.get("liquidity", 1.0),
            flags=data.get("flags", [])
        )
        classification = classify_token(risk)
        print(f"Token {data.get('symbol')} classified as {classification}")
    else:
        print("Failed to retrieve token data")
