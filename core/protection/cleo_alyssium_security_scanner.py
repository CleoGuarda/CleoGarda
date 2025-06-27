#!/usr/bin/env python3
import asyncio
import aiohttp
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from datetime import datetime

API_ENDPOINT = "https://api.example.com/metrics"

async def fetch_metrics(session, endpoint):
    async with session.get(endpoint) as resp:
        return await resp.json()

def prepare_dataframe(data):
    df = pd.DataFrame(data)
    df['ts'] = pd.to_datetime(df['timestamp'])
    df.set_index('ts', inplace=True)
    return df[['value']]

def add_features(df):
    df['delta'] = df['value'].diff().fillna(0)
    df['rolling_mean'] = df['value'].rolling(10, min_periods=1).mean()
    df['rolling_std'] = df['value'].rolling(10, min_periods=1).std().fillna(0)
    return df.dropna()

def detect_clusters(df):
    X = df[['value', 'delta', 'rolling_std']].values
    model = DBSCAN(eps=0.5, min_samples=5)
    df['cluster'] = model.fit_predict(X)
    return df

def summarize_clusters(df):
    clusters = df['cluster'].unique()
    summary = {}
    for c in clusters:
        group = df[df['cluster']==c]
        summary[int(c)] = {
            'count': int(len(group)),
            'mean_value': float(group['value'].mean()),
            'std_delta': float(group['delta'].std())
        }
    return summary

async def main():
    async with aiohttp.ClientSession() as session:
        data = await fetch_metrics(session, API_ENDPOINT)
    df = prepare_dataframe(data)
    df = add_features(df)
    df = detect_clusters(df)
    summary = summarize_clusters(df)
    print("Cluster Summary:", summary)
    now = datetime.utcnow().isoformat()
    df.to_csv(f"metrics_{now}.csv")
    pd.DataFrame([summary]).to_json(f"clusters_{now}.json", orient='records')

if __name__ == "__main__":
    asyncio.run(main())
