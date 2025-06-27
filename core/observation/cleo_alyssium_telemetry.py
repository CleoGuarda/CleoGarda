import logging
import requests
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

# Logger setup
logger = logging.getLogger("cleogarda")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%dT%H:%M:%SZ")
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class Transaction:
    tx_hash: str
    value: float
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(
            tx_hash=data.get("hash", ""),
            value=float(data.get("value", 0)),
            timestamp=datetime.fromisoformat(data.get("timestamp"))
        )


def calculate_risk_score(
    price_change: float,
    liquidity: float,
    flags: List[str],
    weight_price: float = 0.5,
    weight_liquidity: float = 0.3,
    weight_flags: float = 0.2,
    flag_penalty: float = 0.3
) -> float:
    """
    Normalize price_change and liquidity, apply flags penalty, and combine into [0,1] score.
    """
    pct = min(abs(price_change), 1.0)
    illiq = 1.0 - max(min(liquidity, 1.0), 0.0)
    penalty = flag_penalty if "suspicious" in flags else 0.0

    raw = pct * weight_price + illiq * weight_liquidity + penalty * weight_flags
    score = max(0.0, min(raw, 1.0))
    logger.debug("Risk calc: pct=%.3f illiq=%.3f penalty=%.3f -> score=%.3f",
                 pct, illiq, penalty, score)
    return round(score, 2)


class WalletAnalyzer:
    """
    Load and analyze transactions for a wallet.
    """
    def __init__(self, address: str, anomaly_threshold: float = 10_000.0):
        self.address = address
        self.threshold = anomaly_threshold
        self.transactions: List[Transaction] = []

    def load_transactions(self, tx_list: List[Dict[str, Any]]) -> None:
        """
        Parse raw transaction dicts into Transaction objects.
        """
        self.transactions = [Transaction.from_dict(tx) for tx in tx_list]
        logger.info("Loaded %d transactions for %s", len(self.transactions), self.address)

    def detect_anomalies(self) -> List[Transaction]:
        """
        Return transactions whose value exceeds the threshold.
        """
        anomalies = [tx for tx in self.transactions if tx.value > self.threshold]
        logger.info("Detected %d anomalies (threshold=%.2f)", len(anomalies), self.threshold)
        return anomalies

    def summarize_values(self) -> Dict[str, float]:
        """
        Compute avg, max, min of transaction values.
        """
        vals = [tx.value for tx in self.transactions]
        summary = {
            "avg": sum(vals) / len(vals) if vals else 0.0,
            "max": max(vals) if vals else 0.0,
            "min": min(vals) if vals else 0.0,
        }
        logger.info("Transaction summary: %s", summary)
        return summary


def fetch_token_data(api_url: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
    """
    GET JSON from api_url with basic error handling.
    """
    try:
        resp = requests.get(api_url, timeout=timeout)
        resp.raise_for_status()
        logger.info("Fetched token data from %s", api_url)
        return resp.json()
    except requests.RequestException as e:
        logger.error("Failed to fetch token data: %s", e)
        return None


def classify_token(risk_score: float) -> str:
    """
    Map normalized risk score to a category.
    """
    if risk_score >= 0.8:
        return "High Risk"
    if risk_score >= 0.5:
        return "Moderate Risk"
    return "Low Risk"


# Example usage
if __name__ == "__main__":
    API_URL = "https://api.example.com/token/XYZ"
    data = fetch_token_data(API_URL)
    if not data:
        logger.error("No data retrieved, exiting")
        exit(1)

    analyzer = WalletAnalyzer(address=data.get("address", "unknown"), anomaly_threshold=5_000.0)
    analyzer.load_transactions(data.get("transactions", []))
    anomalies = analyzer.detect_anomalies()
    summary = analyzer.summarize_values()

    score = calculate_risk_score(
        price_change=data.get("price_change", 0.0),
        liquidity=data.get("liquidity", 1.0),
        flags=data.get("flags", [])
    )
    category = classify_token(score)

    print(f"Address: {analyzer.address}")
    print(f"Anomalies: {len(anomalies)}")
    print(f"Summary: {summary}")
    print(f"Risk Score: {score} → {category}")
