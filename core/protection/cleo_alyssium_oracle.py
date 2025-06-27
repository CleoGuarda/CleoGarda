#!/usr/bin/env python3
import os
import asyncio
import aiohttp
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from datetime import datetime

API_BASE = os.getenv("API_BASE")
METRICS_ENDPOINT = f"{API_BASE}/metrics"
ALERTS_ENDPOINT = f"{API_BASE}/alerts"
TOKENS_ENDPOINT = f"{API_BASE}/tokens"
API_KEY = os.getenv("API_KEY", "")

async def fetch(session, url, params=None):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with session.get(url, headers=headers, params=params) as r:
        r.raise_for_status()
        return await r.json()

async def post(session, url, payload):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    async with session.post(url, headers=headers, json=payload) as r:
        r.raise_for_status()
        return await r.json()

def df_from(data):
    df = pd.DataFrame(data)
    df['ts'] = pd.to_datetime(df['timestamp'])
    return df.set_index('ts')[['value']]

def features(df):
    df['delta'] = df['value'].diff().fillna(0)
    df['rmean'] = df['value'].rolling(10, min_periods=1).mean()
    df['rstd'] = df['value'].rolling(10, min_periods=1).std().fillna(0)
    return df.dropna()

def cluster(df):
    X = df[['value','delta','rstd']].to_numpy()
    df['cluster'] = DBSCAN(eps=0.5, min_samples=5).fit_predict(X)
    return df

def summarize(df):
    out = {}
    for c in df['cluster'].unique():
        g = df[df['cluster']==c]
        out[int(c)] = {'count':len(g),'mean':float(g['value'].mean()),'std':float(g['delta'].std())}
    return out

async def integrate():
    async with aiohttp.ClientSession() as session:
        metrics = await fetch(session, METRICS_ENDPOINT, params={"limit":1000})
        tokens = await fetch(session, TOKENS_ENDPOINT)
        df = df_from(metrics)
        df = features(df)
        df = cluster(df)
        summary = summarize(df)
        now = datetime.utcnow().isoformat()
        await post(session, ALERTS_ENDPOINT, {"time":now,"clusters":summary,"tokens":tokens})
        df.to_csv(f"metrics_{now}.csv")
        pd.DataFrame([summary]).to_json(f"clusters_{now}.json",orient='records')

if __name__=="__main__":
    asyncio.run(integrate())
