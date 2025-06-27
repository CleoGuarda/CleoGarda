```python
#!/usr/bin/env python3
import os
import csv
import logging
from datetime import datetime, timedelta
from statistics import mean, median, stdev
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import requests

# ─── Logger Setup ─────────────────────────────────────────────────────────────
logger = logging.getLogger("data_inspector")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)


# ─── Data Loading ─────────────────────────────────────────────────────────────
def load_csv(filepath: str) -> pd.DataFrame:
    """Load time-series CSV with columns timestamp, value."""
    df = pd.read_csv(filepath, parse_dates=["timestamp"])
    df.sort_values("timestamp", inplace=True)
    logger.info("Loaded %d rows from %s", len(df), filepath)
    return df


def fetch_remote_csv(url: str) -> pd.DataFrame:
    """Download CSV data over HTTP and load into DataFrame."""
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    filepath = "/tmp/remote_data.csv"
    with open(filepath, "wb") as f:
        f.write(r.content)
    return load_csv(filepath)


# ─── Feature Engineering ─────────────────────────────────────────────────────
def add_rolling_features(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Compute rolling mean, median, and std on 'value'."""
    df[f"roll_mean_{window}"] = df["value"].rolling(window).mean()
    df[f"roll_med_{window}"] = df["value"].rolling(window).median()
    df[f"roll_std_{window}"] = df["value"].rolling(window).std()
    logger.debug("Added rolling features with window=%d", window)
    return df


def add_diff_and_pct_change(df: pd.DataFrame) -> pd.DataFrame:
    """Compute first difference and percent change of 'value'."""
    df["diff"] = df["value"].diff()
    df["pct_change"] = df["value"].pct_change()
    return df


# ─── Anomaly Detection ────────────────────────────────────────────────────────
def z_score_anomalies(values: List[float], threshold: float = 3.0) -> List[int]:
    """Return indices where absolute z-score exceeds threshold."""
    arr = np.array(values)
    zs = (arr - arr.mean()) / (arr.std() or 1)
    return list(np.where(np.abs(zs) > threshold)[0])


def iqr_anomalies(values: List[float], multiplier: float = 1.5) -> List[int]:
    """Return indices of values outside the IQR fence."""
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - multiplier * iqr, q3 + multiplier * iqr
    return [i for i, v in enumerate(values) if v < lower or v > upper]


# ─── Reporting ────────────────────────────────────────────────────────────────
def summarize_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute overall stats on 'value'."""
    vals = df["value"].dropna().values
    return {
        "count": len(vals),
        "mean": mean(vals) if len(vals) else 0.0,
        "median": median(vals) if len(vals) else 0.0,
        "stdev": stdev(vals) if len(vals) > 1 else 0.0,
        "min": float(np.min(vals)) if len(vals) else 0.0,
        "max": float(np.max(vals)) if len(vals) else 0.0,
    }


def export_report(stats: Dict[str, Any], anomalies: Dict[str, List[int]], output: str):
    """Write JSON report to file."""
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "statistics": stats,
        "anomalies": anomalies,
    }
    with open(output, "w") as f:
        json.dump(report, f, indent=2)
    logger.info("Report saved to %s", output)


# ─── Main Workflow ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    import argparse

    parser = argparse.ArgumentParser(description="Time-series data inspector")
    parser.add_argument("--source", required=True, help="CSV filepath or HTTP URL")
    parser.add_argument("--window", type=int, default=5, help="Rolling window size")
    parser.add_argument("--z-threshold", type=float, default=3.0, help="Z-score cutoff")
    parser.add_argument("--iqr-mult", type=float, default=1.5, help="IQR multiplier")
    parser.add_argument("--report", default="report.json", help="Output report filename")
    args = parser.parse_args()

    # Load data
    if args.source.startswith("http"):
        data_df = fetch_remote_csv(args.source)
    else:
        data_df = load_csv(args.source)

    # Feature engineering
    data_df = add_rolling_features(data_df, window=args.window)
    data_df = add_diff_and_pct_change(data_df)

    # Detect anomalies
    values = data_df["value"].fillna(0).tolist()
    z_idxs = z_score_anomalies(values, threshold=args.z_threshold)
    iqr_idxs = iqr_anomalies(values, multiplier=args.iqr_mult)

    # Summarize and export
    stats = summarize_statistics(data_df)
    anomalies = {"z_score": z_idxs, "iqr": iqr_idxs}
    export_report(stats, anomalies, args.report)
    logger.info("Done")
```
