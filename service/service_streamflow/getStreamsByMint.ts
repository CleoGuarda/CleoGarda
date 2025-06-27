import { SolanaStreamClient, Stream } from "@streamflow/stream/solana"
import LRU from "lru-cache"

const cache = new LRU<string, Stream[]>({ max: 100, ttl: 1000 * 60 * 5 })

const RPC_URL = process.env.NEXT_PUBLIC_SOLANA_RPC_URL
if (!RPC_URL) {
  throw new Error("Missing NEXT_PUBLIC_SOLANA_RPC_URL environment variable")
}

export async function getStreamsByMint(
  mint: string
): Promise<Stream[]> {
  const cacheKey = `streams:${mint}`
  const cached = cache.get(cacheKey)
  if (cached) {
    return cached
  }

  const client = new SolanaStreamClient(RPC_URL)
  let attempts = 0
  const maxRetries = 3
  while (attempts < maxRetries) {
    try {
      const response = await client.searchStreams({ mint })
      // filter out incomplete entries
      const streams = response.filter(s => s.id && s.mint === mint)
      cache.set(cacheKey, streams)
      return streams
    } catch (err: any) {
      attempts += 1
      console.warn(`getStreamsByMint attempt ${attempts} failed:`, err.message)
      if (attempts >= maxRetries) {
        console.error("getStreamsByMint: all retries failed")
        throw err
      }
    }
  }

  return []
}
