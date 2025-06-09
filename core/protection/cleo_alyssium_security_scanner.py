import math

from datetime import datetime

import logging





def calculate_risk_score(price_change, liquidity, flags):

    score = abs(price_change) / max(liquidity, 1)

    if 'suspicious' in flags:

        score += 0.3

    return round(min(score, 1.0), 2)





def log_event(event_type, metadata):

    now = datetime.utcnow().isoformat()

    log_entry = {

        "timestamp": now,

        "event": event_type,

        "meta": metadata

    }

    with open("logfile.json", "a") as f:

        f.write(json.dumps(log_entry) + "\n")





class WalletAnalyzer:

    def __init__(self, address):

        self.address = address

        self.transactions = []



    def load_transactions(self, tx_list):

        self.transactions = tx_list



    def detect_anomalies(self):

        return [tx for tx in self.transactions if tx['value'] > 10000]





def classify_token(risk_score):

    if risk_score > 0.8:

        return "High Risk"

    elif risk_score > 0.5:

        return "Moderate Risk"

    else:

        return "Low Risk"





def summarize_metrics(metrics):

    return {

        "avg": sum(metrics) / len(metrics) if metrics else 0,

        "max": max(metrics) if metrics else 0,

        "min": min(metrics) if metrics else 0,

    }

