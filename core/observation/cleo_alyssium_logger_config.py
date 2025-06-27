#!/usr/bin/env python3
import os
import sqlite3
import threading
import time
from datetime import datetime
from typing import List, Tuple

import pandas as pd
import requests
import websocket


# ─── Database Utilities ────────────────────────────────────────────────────────
DB_PATH = "market_data.db"


def init_db(path: str = DB_PATH) -> None:
    """Initialize SQLite database and tables."""
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            timestamp TEXT PRIMARY KEY,
            open REAL, high REAL, low REAL, close REAL, volume REAL
        )
    """)
    conn.commit()
    conn.close()


def insert_price(record: Tuple[str, float, float, float, float, float], path: str = DB_PATH) -> None:
    """Insert one OHLCV record into the database."""
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO prices(timestamp, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?)
    """, record)
    conn.commit()
    conn.close()


# ─── Data Fetching & Indicators ───────────────────────────────────────────────
def fetch_historical(symbol: str, interval: str = "1h") -> pd.DataFrame:
    """
    Fetch historical OHLCV data via REST API.
    Returns pandas DataFrame indexed by timestamp.
    """
    url = f"https://api.example.com/ohlcv/{symbol}/{interval}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df[["open", "high", "low", "close", "volume"]]


def ema(series: pd.Series, span: int) -> pd.Series:
    """Compute exponential moving average."""
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Compute Relative Strength Index."""
    delta = series.diff().dropna()
    up = delta.clip(lower=0).rolling(period).mean()
    down = -delta.clip(upper=0).rolling(period).mean()
    rs = up / down
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Compute MACD and signal line."""
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    })


# ─── Live WebSocket Feed ───────────────────────────────────────────────────────
class LiveTicker:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ws_url = f"wss://stream.example.com/{symbol}@trade"
        self.ws: websocket.WebSocketApp = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

    def on_message(self, ws, message):
        data = pd.json.loads(message)
        ts = datetime.utcfromtimestamp(data["T"] / 1000).isoformat()
        price = float(data["p"])
        volume = float(data["q"])
        record = (ts, price, price, price, price, volume)
        insert_price(record)
        print(f"[{ts}] Live price: {price}")

    def on_error(self, ws, error):
        print("WebSocket error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket closed:", close_status_code, close_msg)

    def run(self):
        self.ws.run_forever()


# ─── Scheduler ────────────────────────────────────────────────────────────────
def schedule_live_feed(symbol: str):
    """Start live feed in a background thread."""
    ticker = LiveTicker(symbol)
    thread = threading.Thread(target=ticker.run, daemon=True)
    thread.start()


# ─── Main Workflow ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()

    # Historical analysis
    symbol = os.getenv("TOKEN_SYMBOL", "ABCUSD")
    df = fetch_historical(symbol)
    df["ema_20"] = ema(df["close"], 20)
    df["rsi_14"] = rsi(df["close"], 14)
    indicators = macd(df["close"])
    print("Latest indicators:")
    print(indicators.tail(3))

    # Store historical into DB
    for ts, row in df.iterrows():
        record = (
            ts.isoformat(),
            row.open, row.high, row.low, row.close, row.volume
        )
        insert_price(record)

    # Start live feed
    schedule_live_feed(symbol)

    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Exiting...")
