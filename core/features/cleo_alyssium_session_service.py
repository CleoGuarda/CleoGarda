import requests

import json

from datetime import datetime





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





