#!/usr/bin/env python3
import os
import json
import csv
import logging
from datetime import datetime
from statistics import mean, median, stdev
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import requests
from argparse import ArgumentParser

# ─── Logger Setup ─────────────────────────────────────────────────────────────
logger = logging.getLogger("data_inspector")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)


# ─── Data Loading ─────────────────────────────────────────────────────────────
def load_csv(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=["timestamp"], infer_datetime_format=True)
    df = df.dropna(subset=["timestamp", "value"]).sort_values("timestamp").reset_index(drop=True)
    logger.info("Loaded %d rows from %s", len(df), filepath)
    return df


def fetch_remote_csv(url: str) -> pd.DataFrame:
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        tmp_path = os.path.join(os.getenv("TMPDIR", "/tmp"), "remote_data.csv")
        with open(tmp_path, "wb") as f:
            f.write(r.content)
        return load_csv(tmp_path)
    except Exception as e:
        logger.error("Failed to fetch remote CSV: %s", e)
        raise


# ─── Feature Engineering ─────────────────────────────────────────────────────
def add_rolling_features(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    df = df.copy()
    df[f"roll_mean_{window}"] = df["value"].rolling(window, min_periods=1).mean()
    df[f"roll_med_{window}"]  = df["value"].rolling(window, min_periods=1).median()
    df[f"roll_std_{window}"]  = df["value"].rolling(window, min_periods=1).std().fillna(0)
    logger.debug("Added rolling features with window=%d", window)
    return df


def add_diff_and_pct_change(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["diff"] = df["value"].diff().fillna(0)
    df["pct_change"] = df["value"].pct_change().fillna(0)
    return df


# ─── Anomaly Detection ────────────────────────────────────────────────────────
def z_score_anomalies(values: List[float], threshold: float = 3.0) -> List[int]:
    arr = np.array(values, dtype=float)
    mu, sigma = arr.mean(), arr.std() or 1.0
    zs = (arr - mu) / sigma
    return list(np.where(np.abs(zs) > threshold)[0])


def iqr_anomalies(values: List[float], multiplier: float = 1.5) -> List[int]:
    arr = np.array(values, dtype=float)
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - multiplier * iqr, q3 + multiplier * iqr
    return [i for i, v in enumerate(arr) if v < lower or v > upper]


# ─── Reporting ────────────────────────────────────────────────────────────────
def summarize_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    vals = df["value"].dropna().astype(float)
    count = len(vals)
    return {
        "count": count,
        "mean": float(mean(vals)) if count else 0.0,
        "median": float(median(vals)) if count else 0.0,
        "stdev": float(stdev(vals)) if count > 1 else 0.0,
        "min": float(vals.min()) if count else 0.0,
        "max": float(vals.max()) if count else 0.0,
    }


def export_report(stats: Dict[str, Any], anomalies: Dict[str, List[int]], output: str):
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "statistics": stats,
        "anomalies": anomalies,
    }
    with open(output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info("Report saved to %s", output)


# ─── Main Workflow ────────────────────────────────────────────────────────────
def main():
    parser = ArgumentParser(description="Time-series data inspector")
    parser.add_argument("--source", required=True, help="CSV filepath or HTTP URL")
    parser.add_argument("--window", type=int, default=5, help="Rolling window size")
    parser.add_argument("--z-threshold", type=float, default=3.0, help="Z-score cutoff")
    parser.add_argument("--iqr-mult", type=float, default=1.5, help="IQR multiplier")
    parser.add_argument("--report", default="report.json", help="Output report filename")
    args = parser.parse_args()

    # Load data
    if args.source.lower().startswith(("http://", "https://")):
        df = fetch_remote_csv(args.source)
    else:
        df = load_csv(args.source)

    # Features & anomalies
    df = add_rolling_features(df, window=args.window)
    df = add_diff_and_pct_change(df)
    values = df["value"].fillna(0).tolist()
    anomalies = {
        "z_score": z_score_anomalies(values, threshold=args.z_threshold),
        "iqr":    iqr_anomalies(values, multiplier=args.iqr_mult),
    }

    # Summarize & export
    stats = summarize_statistics(df)
    export_report(stats, anomalies, args.report)
    logger.info("Done")


if __name__ == "__main__":
    main()
