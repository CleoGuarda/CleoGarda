import requests
import logging
import json
from datetime import datetime

def log_event(event_type, metadata):
    now = datetime.utcnow().isoformat()
    log_entry = {
        "timestamp": now,
        "event": event_type,
        "meta": metadata
    }
    with open("logfile.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def calculate_risk_score(price_change, liquidity, flags):
    score = abs(price_change) / max(liquidity, 1)
    if 'suspicious' in flags:
        score += 0.3
    if 'blacklisted' in flags:
        score += 0.4
    if 'honeypot' in flags:
        score += 0.25
    return round(min(score, 1.0), 3)

def fetch_token_data(api_url, timeout=10):
    try:
        response = requests.get(api_url, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error("API error: %s", response.status_code)
            return None
    except Exception as e:
        logging.error("Exception during fetch: %s", e)
        return None

def summarize_metrics(metrics):
    if not metrics:
        return {"avg": 0, "max": 0, "min": 0, "median": 0, "std_dev": 0}
    import numpy as np
    metrics_np = np.array(metrics)
    return {
        "avg": float(np.mean(metrics_np)),
        "max": float(np.max(metrics_np)),
        "min": float(np.min(metrics_np)),
        "median": float(np.median(metrics_np)),
        "std_dev": float(np.std(metrics_np))
    }

class WalletAnalyzer:
    def __init__(self, address):
        self.address = address
        self.transactions = []
        self.anomalies = []

    def load_transactions(self, tx_list):
        if not isinstance(tx_list, list):
            raise ValueError("Transactions must be provided as a list")
        self.transactions = tx_list

    def detect_anomalies(self, threshold=10000):
        self.anomalies = [tx for tx in self.transactions if tx.get('value', 0) > threshold]
        log_event("Anomalies detected", {"address": self.address, "count": len(self.anomalies)})
        return self.anomalies

    def total_volume(self):
        total = sum(tx.get('value', 0) for tx in self.transactions)
        return total

    def average_transaction_value(self):
        if not self.transactions:
            return 0
        return self.total_volume() / len(self.transactions)

    def transactions_per_day(self):
        from datetime import datetime
        if not self.transactions:
            return 0
        dates = []
        for tx in self.transactions:
            ts = tx.get('timestamp')
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    dates.append(dt.date())
                except Exception:
                    continue
        if not dates:
            return 0
        days_span = (max(dates) - min(dates)).days or 1
        return len(self.transactions) / days_span
