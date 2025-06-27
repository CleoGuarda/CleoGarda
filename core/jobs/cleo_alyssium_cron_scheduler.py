#!/usr/bin/env python3
import logging
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import requests

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logger = logging.getLogger("wallet_analyzer")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


# ─── Data Classes ─────────────────────────────────────────────────────────────
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
            timestamp=datetime.fromisoformat(data.get("timestamp")),
        )


# ─── Utility Functions ────────────────────────────────────────────────────────
def summarize_metrics(values: List[float]) -> Dict[str, float]:
    """
    Compute basic statistics: average, max, min (0 if empty).
    """
    if not values:
        return {"avg": 0.0, "max": 0.0, "min": 0.0}
    return {"avg": sum(values) / len(values), "max": max(values), "min": min(values)}


def fetch_json(
    url: str, timeout: float = 5.0, retries: int = 3, backoff: float = 1.0
) -> Optional[Dict[str, Any]]:
    """
    Perform GET request and return parsed JSON.
    Retries up to `retries` times with exponential backoff.
    """
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            logger.info("Fetched data from %s (attempt %d)", url, attempt)
            return resp.json()
        except requests.RequestException as exc:
            logger.warning(
                "Attempt %d failed for %s: %s", attempt, url, exc
            )
            time.sleep(backoff * attempt)
    logger.error("Failed to fetch data after %d attempts: %s", retries, url)
    return None


# ─── Core Classes ─────────────────────────────────────────────────────────────
class WalletAnalyzer:
    """
    Load wallet transactions, detect anomalies, and summarize values.
    """

    def __init__(self, address: str, anomaly_threshold: float = 10_000.0):
        self.address = address
        self.threshold = anomaly_threshold
        self.transactions: List[Transaction] = []

    def load_transactions(self, raw_list: List[Dict[str, Any]]) -> None:
        """
        Parse raw transaction dicts into Transaction objects.
        """
        self.transactions = [
            Transaction.from_dict(item) for item in raw_list
        ]
        logger.info(
            "Loaded %d transactions for wallet %s",
            len(self.transactions),
            self.address,
        )

    def detect_anomalies(self) -> List[Transaction]:
        """
        Return transactions with value above the anomaly threshold.
        """
        anomalies = [
            tx for tx in self.transactions if tx.value > self.threshold
        ]
        logger.info(
            "Detected %d anomalies (threshold=%.2f)",
            len(anomalies),
            self.threshold,
        )
        return anomalies

    def summarize_values(self) -> Dict[str, float]:
        """
        Return avg, max, min of transaction values.
        """
        values = [tx.value for tx in self.transactions]
        summary = summarize_metrics(values)
        logger.info("Transaction summary: %s", summary)
        return summary


# ─── Risk Scoring ─────────────────────────────────────────────────────────────
def calculate_risk_score(
    price_change: float,
    liquidity: float,
    flags: List[str],
    weights: Dict[str, float] = {"price": 0.4, "liquidity": 0.4, "flags": 0.2},
) -> float:
    """
    Compute a normalized risk score [0.0, 1.0].
    - price_change: absolute percent (0.0–1.0)
    - liquidity: normalized (0.0–1.0)
    - flags: list of indicators (e.g. ['suspicious'])
    """
    pct = min(abs(price_change), 1.0)
    illiq = 1.0 - max(min(liquidity, 1.0), 0.0)
    flag_score = flags.count("suspicious") / len(flags) if flags else 0.0

    raw = (
        pct * weights["price"]
        + illiq * weights["liquidity"]
        + flag_score * weights["flags"]
    )
    score = max(0.0, min(raw, 1.0))
    logger.info(
        "Risk score: %.3f (pct=%.3f, illiq=%.3f, flags=%.3f)",
        score,
        pct,
        illiq,
        flag_score,
    )
    return round(score, 2)


def classify_risk(score: float) -> str:
    """
    Map risk score to category.
    """
    if score > 0.8:
        return "High Risk"
    if score > 0.5:
        return "Moderate Risk"
    return "Low Risk"


# ─── Example Workflow ────────────────────────────────────────────────────────
if __name__ == "__main__":
    API_URL = "https://api.example.com/token/ABC123"
    data = fetch_json(API_URL)

    if not data:
        logger.error("Cannot proceed without token data")
        exit(1)

    # Analyze wallet transactions
    tx_list = data.get("transactions", [])
    analyzer = WalletAnalyzer(address=data.get("address", "unknown"), anomaly_threshold=5_000.0)
    analyzer.load_transactions(tx_list)
    anomalies = analyzer.detect_anomalies()
    summary = analyzer.summarize_values()

    # Compute and classify risk
    score = calculate_risk_score(
        price_change=data.get("price_change", 0.0),
        liquidity=data.get("liquidity", 1.0),
        flags=data.get("flags", []),
    )
    category = classify_risk(score)

    # Output results
    print(f"Wallet: {analyzer.address}")
    print(f"Anomalies found: {len(anomalies)}")
    print(f"Transaction summary: {summary}")
    print(f"Risk score: {score} → {category}")
