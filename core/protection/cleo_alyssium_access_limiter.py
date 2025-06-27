import os
import asyncio
import aiohttp
import requests_cache
import pandas as pd
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from datetime import datetime

CACHE_DB = "api_cache"
SESSION = requests_cache.CachedSession(CACHE_DB, expire_after=300)

REST_ENDPOINT = os.getenv("REST_ENDPOINT", "https://api.example.com/data")
GRAPHQL_ENDPOINT = os.getenv("GRAPHQL_ENDPOINT", "https://api.example.com/graphql")
API_KEY = os.getenv("API_KEY", "")

def fetch_rest(params: dict) -> dict:
    return SESSION.get(
        REST_ENDPOINT,
        params=params,
        headers={"Authorization": f"Bearer {API_KEY}"}
    ).json()

async def fetch_graphql(query: str, variables: dict = None) -> dict:
    transport = AIOHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    async with Client(transport=transport, fetch_schema_from_transport=True) as client:
        return await client.execute(gql(query), variable_values=variables or {})

def process_rest(data: dict) -> pd.DataFrame:
    df = pd.DataFrame(data.get("items", []))
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    df["price_change"] = df["close"].pct_change().fillna(0)
    df["vol_moving"] = df["volume"].rolling(window=20, min_periods=1).mean()
    return df

async def main():
    rest_data = fetch_rest({"limit": 500})
    df = process_rest(rest_data)

    query = """
    query getTokens($limit: Int!) {
      tokens(limit: $limit) {
        symbol
        riskScore
        lastUpdated
      }
    }
    """
    gql_result = await fetch_graphql(query, {"limit": 50})
    tokens_df = pd.DataFrame(gql_result.get("tokens", []))
    tokens_df["lastUpdated"] = pd.to_datetime(tokens_df["lastUpdated"])

    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    df.to_csv(f"rest_data_{now}.csv")
    tokens_df.to_json(f"tokens_{now}.json", orient="records")

if __name__ == "__main__":
    asyncio.run(main())
