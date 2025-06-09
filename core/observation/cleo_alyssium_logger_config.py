import requests

import logging

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

    return round(min(score, 1.0), 2)





def fetch_token_data(api_url):

    try:

        response = requests.get(api_url)

        if response.status_code == 200:

            return response.json()

        else:

            logging.error("API error: %s", response.status_code)

            return None

    except Exception as e:

        logging.error("Exception during fetch: %s", e)

        return None





def summarize_metrics(metrics):

    return {

        "avg": sum(metrics) / len(metrics) if metrics else 0,

        "max": max(metrics) if metrics else 0,

        "min": min(metrics) if metrics else 0,

    }





class WalletAnalyzer:

    def __init__(self, address):

        self.address = address

        self.transactions = []



    def load_transactions(self, tx_list):

