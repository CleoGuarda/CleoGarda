import { SolanaStreamClient, Stream } from "@streamflow/stream/solana"
import LRU from "lru-cache"

const RPC_URL = process.env.NEXT_PUBLIC_SOLANA_RPC_URL
if (!RPC_URL) {
  throw new Error("Missing NEXT_PUBLIC_SOLANA_RPC_URL environment variable")
}

const recipientCache = new LRU<string, Stream[]>({
  max: 100,
  ttl: 1000 * 60 * 5, // 5 minutes
})

export async function getStreamsByRecipient(
  recipient: string
): Promise<Stream[]> {
  const cacheKey = `recipient:${recipient}`
  const cached = recipientCache.get(cacheKey)
  if (cached) {
    return cached
  }

  const client = new SolanaStreamClient(RPC_URL)
  let attempts = 0
  const maxRetries = 3
  while (attempts < maxRetries) {
    try {
      const allStreams = await client.searchStreams({ recipient })
      const validStreams = allStreams.filter(
        s => s.id && s.recipient === recipient
      )
      recipientCache.set(cacheKey, validStreams)
      return validStreams
    } catch (err: any) {
      attempts += 1
      console.warn(
        `getStreamsByRecipient attempt ${attempts} failed:`,
        err.message
      )
      if (attempts >= maxRetries) {
        console.error("getStreamsByRecipient: all retries failed")
        throw err
      }
      await new Promise(res => setTimeout(res, 500 * attempts))
    }
  }

  return []
}
