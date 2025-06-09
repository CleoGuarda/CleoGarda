import logging

import json

import time





def summarize_metrics(metrics):

    return {

        "avg": sum(metrics) / len(metrics) if metrics else 0,

        "max": max(metrics) if metrics else 0,

        "min": min(metrics) if metrics else 0,

    }





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





def calculate_risk_score(price_change, liquidity, flags):

    score = abs(price_change) / max(liquidity, 1)

    if 'suspicious' in flags:

