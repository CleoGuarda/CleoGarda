#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests

# ─── Logging Setup (UTC, structured-friendly) ─────────────────────────────────
logger = logging.getLogger("wallet_analyzer")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()

# Ensure timestamps are UTC
def _utc_converter(*args):
    return time.gmtime(*args)

formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
# type: ignore[attr-defined]
handler.formatter = formatter
handler.formatter.converter = _utc_converter  # force UTC
logger.handlers.clear()
logger.addHandler(handler)


# ─── Data Classes ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Transaction:
    tx_hash: str
    value: float
    timestamp: datetime  # tz-aware (UTC)

    @staticmethod
    def _parse_timestamp(ts: Any) -> datetime:
        """
        Parse ISO-8601 timestamps. Accepts 'Z' suffix and naive strings (assumed UTC).
        """
        if isinstance(ts, datetime):
            return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        if not isinstance(ts, str) or not ts:
            raise ValueError("timestamp must be a non-empty ISO-8601 string")
        # Support trailing 'Z'
        iso = ts.rstrip("Z")
        dt = datetime.fromisoformat(iso)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(
            tx_hash=str(data.get("hash") or data.get("tx_hash") or ""),
            value=float(data.get("value") or 0.0),
            timestamp=cls._parse_timestamp(data.get("timestamp")),
        )


# ─── Utility Functions ────────────────────────────────────────────────────────
def _finite_nums(values: Iterable[Any]) -> List[float]:
    out: List[float] = []
    for v in values:
        try:
            f = float(v)
            if f == f:  # exclude NaN
                out.append(f)
        except Exception:
            continue
    return out


def summarize_metrics(values: Sequence[float]) -> Dict[str, float]:
    """
    Compute basic statistics: average, max, min (0 if empty). Ignores NaN/invalid entries.
    """
    nums = _finite_nums(values)
    if not nums:
        return {"avg": 0.0, "max": 0.0, "min": 0.0}
    return {
        "avg": sum(nums) / len(nums),
        "max": max(nums),
        "min": min(nums),
    }


def _is_retryable_status(status: int) -> bool:
    return status == 429 or 500 <= status <= 599


def fetch_json(
    url: str,
    *,
    timeout: float = 5.0,
    retries: int = 2,
    backoff_ms: int = 500,
    session: Optional[requests.Session] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Perform a GET request and return parsed JSON.
    Deterministic linear backoff: delay = backoff_ms * attempt (attempt starts at 1).
    Retries on network errors, timeouts, 429 and 5xx.
    """
    sess = session or requests.Session()
    h = {"Accept": "application/json", **(headers or {})}

    last_error: Optional[Exception] = None
    # attempts = first + retries
    for attempt in range(1, retries + 2):
        try:
            resp = sess.get(url, timeout=timeout, headers=h)
            if _is_retryable_status(resp.status_code) and attempt <= retries + 0:
                logger.warning(
                    "Retryable HTTP status %s on attempt %d for %s",
                    resp.status_code,
                    attempt,
                    url,
                )
                # linear backoff
                time.sleep((backoff_ms * attempt) / 1000.0)
                continue

            resp.raise_for_status()
            logger.info("Fetched data from %s (attempt %d)", url, attempt)
            # ensure JSON content-type guard (best-effort)
            return resp.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt <= retries:
                logger.warning("Attempt %d failed for %s: %s", attempt, url, exc)
                time.sleep((backoff_ms * attempt) / 1000.0)
                continue
            break

    logger.error("Failed to fetch data after %d attempts: %s", retries + 1, url)
    if last_error:
        logger.error("Last error: %s", last_error)
    return None


# ─── Core Classes ─────────────────────────────────────────────────────────────
class WalletAnalyzer:
    """
    Load wallet transactions, detect anomalies, and summarize values.
    """

    def __init__(self, address: str, anomaly_threshold: float = 10_000.0):
        if not isinstance(address, str) or not address:
            raise ValueError("address must be a non-empty string")
        if anomaly_threshold < 0:
            raise ValueError("anomaly_threshold must be non-negative")
        self.address = address
        self.threshold = anomaly_threshold
        self.transactions: List[Transaction] = []

    def load_transactions(self, raw_list: Iterable[Dict[str, Any]]) -> None:
        """
        Parse raw transaction dicts into Transaction objects.
        Invalid entries are skipped with a warning.
        """
        txs: List[Transaction] = []
        for idx, item in enumerate(raw_list or []):
            try:
                txs.append(Transaction.from_dict(item))
            except Exception as e:
                logger.warning("Skipping invalid tx at index %d: %s", idx, e)
        self.transactions = txs
        logger.info("Loaded %d transactions for wallet %s", len(txs), self.address)

    def detect_anomalies(self) -> List[Transaction]:
        """
        Return transactions with value above the anomaly threshold.
        """
        anomalies = [tx for tx in self.transactions if tx.value > self.threshold]
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
    flags: Sequence[str],
    weights: Dict[str, float] | None = None,
) -> float:
    """
    Compute a normalized risk score [0.0, 1.0].
    - price_change: absolute percent (0.0–1.0)
    - liquidity: normalized (0.0–1.0)
    - flags: list of indicators (e.g. ['suspicious'])
    """
    w = {"price": 0.4, "liquidity": 0.4, "flags": 0.2, **(weights or {})}
    pct = min(max(abs(float(price_change)), 0.0), 1.0)
    liq = min(max(float(liquidity), 0.0), 1.0)
    illiq = 1.0 - liq
    # deterministic flag ratio with known "suspicious" emphasis
    total_flags = len(flags)
    flag_score = (flags.count("suspicious") / total_flags) if total_flags else 0.0

    raw = pct * w["price"] + illiq * w["liquidity"] + flag_score * w["flags"]
    score = max(0.0, min(raw, 1.0))
    logger.info(
        "Risk score: %.3f (pct=%.3f, illiq=%.3f, flags=%.3f)",
        score,
        pct,
        illiq,
        flag_score,
    )
    # 2 decimal places for presentation consistency
    return round(score, 2)


def classify_risk(score: float) -> str:
    """
    Map risk score to category.
    """
    s = float(score)
    if s > 0.8:
        return "High Risk"
    if s > 0.5:
        return "Moderate Risk"
    return "Low Risk"


# ─── Example Workflow ────────────────────────────────────────────────────────
def _print_human(analyzer: WalletAnalyzer, anomalies: List[Transaction], summary: Dict[str, float], score: float, category: str) -> None:
    print(f"Wallet: {analyzer.address}")
    print(f"Anomalies found: {len(anomalies)}")
    print(f"Transaction summary: {summary}")
    print(f"Risk score: {score} → {category}")


def _print_json(analyzer: WalletAnalyzer, anomalies: List[Transaction], summary: Dict[str, float], score: float, category: str) -> None:
    payload = {
        "wallet": analyzer.address,
        "anomalies": [t.tx_hash for t in anomalies],
        "summary": summary,
        "risk": {"score": score, "category": category},
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    API_URL = "https://api.example.com/token/ABC123"
    data = fetch_json(API_URL, timeout=8.0, retries=2, backoff_ms=600)

    if not data:
        logger.error("Cannot proceed without token data")
        raise SystemExit(1)

    # Analyze wallet transactions
    tx_list = data.get("transactions", [])
    analyzer = WalletAnalyzer(address=str(data.get("address") or "unknown"), anomaly_threshold=5_000.0)
    analyzer.load_transactions(tx_list)
    anomalies = analyzer.detect_anomalies()
    summary = analyzer.summarize_values()

    # Compute and classify risk
    score = calculate_risk_score(
        price_change=float(data.get("price_change") or 0.0),
        liquidity=float(data.get("liquidity") or 1.0),
        flags=list(data.get("flags") or []),
    )
    category = classify_risk(score)

    # Output results (both human-readable and JSON for machines)
    _print_human(analyzer, anomalies, summary, score, category)
    # Uncomment if you want structured JSON output as well:
    # _print_json(analyzer, anomalies, summary, score, category)
