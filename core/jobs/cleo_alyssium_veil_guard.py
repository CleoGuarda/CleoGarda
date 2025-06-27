#!/usr/bin/env python3
import logging
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import requests

# ─── Logger Configuration ──────────────────────────────────────────────────────
logger = logging.getLogger("cleogarda")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%dT%H:%M:%SZ")
)
logger.addHandler(handler)


# ─── Data Models ───────────────────────────────────────────────────────────────
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


# ─── Utilities ────────────────────────────────────────────────────────────────
def summarize_metrics(values: List[float]) -> Dict[str, float]:
    """Return average, max, min of a numeric list (zeros if empty)."""
    if not values:
        return {"avg": 0.0, "max": 0.0, "min": 0.0}
    return {"avg": sum(values) / len(values), "max": max(values), "min": min(values)}


def fetch_json(
    url: str, timeout: float = 5.0, retries: int = 3, backoff: float = 1.0
) -> Optional[Dict[str, Any]]:
    """
    GET JSON from URL with retry and exponential backoff.
    Returns dict or None.
    """
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            logger.info("Fetched JSON (%d): %s", attempt, url)
            return resp.json()
        except requests.RequestException as e:
            logger.warning("Fetch attempt %d failed: %s", attempt, e)
            time.sleep(backoff * attempt)
    logger.error("All %d fetch attempts failed: %s", retries, url)
    return None


# ─── Core Analyzer ────────────────────────────────────────────────────────────
class WalletAnalyzer:
    """
    Loads transactions, detects anomalies, and provides value summaries.
    """

    def __init__(self, address: str, anomaly_threshold: float = 10_000.0):
        self.address = address
        self.threshold = anomaly_threshold
        self.transactions: List[Transaction] = []

    def load(self, raw_txs: List[Dict[str, Any]]) -> None:
        """Parse raw dicts into Transaction instances."""
        self.transactions = [Transaction.from_dict(d) for d in raw_txs]
        logger.info("Loaded %d txs for %s", len(self.transactions), self.address)

    def anomalies(self) -> List[Transaction]:
        """Return txs exceeding the value threshold."""
        result = [tx for tx in self.transactions if tx.value > self.threshold]
        logger.info("Found %d anomalies (> %.2f)", len(result), self.threshold)
        return result

    def summary(self) -> Dict[str, float]:
        """Summarize values of all loaded transactions."""
        vals = [tx.value for tx in self.transactions]
        stats = summarize_metrics(vals)
        logger.info("Value summary: %s", stats)
        return stats


# ─── Risk Scoring ─────────────────────────────────────────────────────────────
def calculate_risk_score(
    price_change: float,
    liquidity: float,
    flags: List[str],
    weights: Dict[str, float] = {"price": 0.4, "liquidity": 0.4, "flags": 0.2},
) -> float:
    """
    Compute normalized risk [0.0–1.0] using:
      - price_change (abs pct, capped 1.0)
      - liquidity (inverted, 1 - value)
      - flags (fraction of 'suspicious')
    """
    pct = min(abs(price_change), 1.0)
    illiq = 1.0 - max(min(liquidity, 1.0), 0.0)
    flag_frac = flags.count("suspicious") / len(flags) if flags else 0.0

    raw = pct * weights["price"] + illiq * weights["liquidity"] + flag_frac * weights["flags"]
    score = max(0.0, min(raw, 1.0))
    logger.info("Risk score=%.3f (pct=%.3f, illiq=%.3f, flags=%.3f)", score, pct, illiq, flag_frac)
    return round(score, 2)


def classify_risk(score: float) -> str:
    """Map risk score to categorical labels."""
    if score > 0.8:
        return "High Risk"
    if score > 0.5:
        return "Moderate Risk"
    return "Low Risk"


# ─── Main Workflow ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    API = "https://api.example.com/token/ABC123"
    data = fetch_json(API)
    if not data:
        logger.error("Terminating: no data")
        exit(1)

    addr = data.get("address", "unknown")
    analyzer = WalletAnalyzer(address=addr, anomaly_threshold=5_000.0)
    analyzer.load(data.get("transactions", []))

    anomalies = analyzer.anomalies()
    stats = analyzer.summary()

    score = calculate_risk_score(
        price_change=data.get("price_change", 0.0),
        liquidity=data.get("liquidity", 1.0),
        flags=data.get("flags", []),
    )
    label = classify_risk(score)

    print(f"Address: {addr}")
    print(f"Anomalies: {len(anomalies)}")
    print(f"Stats: {stats}")
    print(f"Risk: {score} → {label}")
