import logging
import json
import requests
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Union

# Configure module-level logger
logger = logging.getLogger("cleo_garda")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def summarize_metrics(metrics: List[float]) -> Dict[str, float]:
    """
    Calculate basic statistics for a list of numeric metrics.
    Returns average, max, and min (0 if list is empty).
    """
    if not metrics:
        return {"avg": 0.0, "max": 0.0, "min": 0.0}
    avg = sum(metrics) / len(metrics)
    return {"avg": avg, "max": max(metrics), "min": min(metrics)}


def log_event(event_type: str, metadata: Dict[str, Any]) -> None:
    """
    Append a JSON-formatted event entry to logfile.json and log to console.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        "meta": metadata,
    }
    try:
        with open("logfile.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info("Logged event: %s", event_type)
    except IOError as e:
        logger.error("Failed to write log entry: %s", e)


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
    Analyzes wallet transactions for anomalies and aggregates metrics.
    """
    def __init__(self, threshold: float = 10_000.0):
        self.threshold = threshold
        self.transactions: List[Transaction] = []

    def load_transactions(self, tx_list: List[Dict[str, Any]]) -> None:
        self.transactions = [Transaction.from_dict(tx) for tx in tx_list]
        logger.info("Loaded %d transactions", len(self.transactions))

    def detect_anomalies(self) -> List[Transaction]:
        anomalies = [tx for tx in self.transactions if tx.value > self.threshold]
        logger.info("Detected %d anomalies (threshold=%s)", len(anomalies), self.threshold)
        return anomalies

    def transaction_metrics(self) -> Dict[str, float]:
        values = [tx.value for tx in self.transactions]
        metrics = summarize_metrics(values)
        logger.info("Transaction metrics: %s", metrics)
        return metrics


class TokenDataFetcher:
    """
    Fetch token data from a REST API endpoint with simple error handling.
    """
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    def fetch(self, api_url: str) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(api_url, timeout=self.timeout)
            resp.raise_for_status()
            logger.info("Fetched token data from %s", api_url)
            return resp.json()
        except requests.RequestException as e:
            logger.error("Failed to fetch token data: %s", e)
            return None


def calculate_risk_score(
    price_change: float,
    liquidity: float,
    flags: int,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate a normalized risk score [0.0 – 1.0] based on:
      - price_change: absolute percentage change (e.g., 0.05 for 5%)
      - liquidity: normalized [0.0 – 1.0], where lower liquidity increases risk
      - flags: count of on-chain alerts or suspicious indicators

    weights: optional dict with keys "price", "liquidity", "flags"
    """
    # Default weight distribution
    w = weights or {"price": 0.5, "liquidity": 0.3, "flags": 0.2}

    # Normalize inputs
    pct_change = min(abs(price_change), 1.0)  # cap at 100%
    illiquidity = 1.0 - max(min(liquidity, 1.0), 0.0)  # invert liquidity

    # Simple risk formula
    raw_score = (pct_change * w["price"]
                 + illiquidity * w["liquidity"]
                 + (flags / (flags + 1)) * w["flags"])

    # Clamp between 0 and 1
    score = max(0.0, min(raw_score, 1.0))
    logger.info(
        "Calculated risk score: %.3f (price=%.3f, illiq=%.3f, flags=%d)",
        score, pct_change, illiquidity, flags
    )
    return score


# Example usage
if __name__ == "__main__":
    fetcher = TokenDataFetcher()
    data = fetcher.fetch("https://api.example.com/token/ABC123")
    if data:
        log_event("token_fetch", {"symbol": data.get("symbol")})
        analyzer = WalletAnalyzer(threshold=5_000.0)
        analyzer.load_transactions(data.get("transactions", []))
        anomalies = analyzer.detect_anomalies()
        log_event("anomalies_found", {"count": len(anomalies)})
        metrics = analyzer.transaction_metrics()
        log_event("metrics_summary", metrics)

        price_chg = data.get("price_change", 0.0)
        liq = data.get("liquidity", 1.0)
        flags = data.get("alert_flags", 0)
        risk = calculate_risk_score(price_chg, liq, flags)
        classification = (
            "High Risk" if risk > 0.8
            else "Moderate Risk" if risk > 0.5
            else "Low Risk"
        )
        print(f"Token risk classification: {classification}")
    else:
        logger.error("No token data available.")
