import requests
import logging
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger("cleo_garda")
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    "cleo_garda.log", maxBytes=1_000_000, backupCount=3
)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%dT%H:%M:%SZ"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class Transaction:
    tx_hash: str
    value: float
    timestamp: datetime

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Transaction":
        return Transaction(
            tx_hash=data.get("hash", ""),
            value=float(data.get("value", 0)),
            timestamp=datetime.fromisoformat(data.get("timestamp"))
        )


class TokenDataFetcher:
    """Fetch token data from a REST API with retry logic."""

    def __init__(self, base_url: str, timeout: float = 5.0, max_retries: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    def fetch(self, endpoint: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                logger.info("Fetched data from %s (attempt %d)", url, attempt)
                return response.json()
            except requests.RequestException as e:
                logger.warning(
                    "Attempt %d: failed to fetch %s: %s", attempt, url, e
                )
        logger.error("All %d attempts failed for %s", self.max_retries, url)
        return None


def log_event(event_type: str, metadata: Dict[str, Any]) -> None:
    """Append a JSON-formatted event log entry to logfile.json."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        "meta": metadata,
    }
    try:
        with open("logfile.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info("Logged event %s", event_type)
    except IOError as e:
        logger.error("Failed to write log entry: %s", e)


class WalletAnalyzer:
    """Analyzes a list of transactions for anomalies."""

    def __init__(self, threshold: float = 10_000.0):
        self.threshold = threshold
        self.transactions: List[Transaction] = []

    def load_transactions(self, tx_list: List[Dict[str, Any]]) -> None:
        self.transactions = [
            Transaction.from_dict(tx) for tx in tx_list
        ]
        logger.info("Loaded %d transactions", len(self.transactions))

    def detect_anomalies(self) -> List[Transaction]:
        anomalies = [tx for tx in self.transactions if tx.value > self.threshold]
        logger.info("Detected %d anomalies (threshold=%s)", len(anomalies), self.threshold)
        return anomalies


def classify_token(risk_score: float) -> str:
    """
    Classify token risk level based on a normalized risk_score (0.0–1.0).
    """
    if risk_score > 0.8:
        return "High Risk"
    if risk_score > 0.5:
        return "Moderate Risk"
    return "Low Risk"


if __name__ == "__main__":
    # Example usage
    fetcher = TokenDataFetcher(base_url="https://api.cleogarda.com/tokens")
    data = fetcher.fetch("some-token-address")
    if data:
        log_event("token_fetched", {"address": "some-token-address", "data_length": len(json.dumps(data))})
        analyzer = WalletAnalyzer(threshold=5_000.0)
        transactions = data.get("transactions", [])
        analyzer.load_transactions(transactions)
        anomalies = analyzer.detect_anomalies()
        for tx in anomalies:
            log_event("anomaly_detected", asdict(tx))
        risk = data.get("risk_score", 0.0)
        classification = classify_token(float(risk))
        print(f"Token classified as {classification}")
    else:
        print("Failed to fetch token data")
