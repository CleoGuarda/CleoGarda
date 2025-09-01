import React, { useCallback, useMemo, useState } from "react"
import { Grid } from "@/components/ui/grid"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { DexscreenerAdapter } from "./dexscreener-adapter"
import { DexPairCard } from "./DexPairCard"
import { PublicKey } from "@solana/web3.js"

type PairResponse = {
  pair?: {
    address: string
    stats: Record<string, unknown>
  }
}

function isValidSolanaAddress(s: string): boolean {
  try {
    // Throws if invalid
    new PublicKey(s)
    return true
  } catch {
    return false
  }
}

export const SolanaDashboard: React.FC = () => {
  const [tokenAddress, setTokenAddress] = useState("")
  const [pairData, setPairData] = useState<PairResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<number | null>(null)

  const adapter = useMemo(
    () =>
      new DexscreenerAdapter({
        baseUrl: "https://api.dexscreener.com/latest/dex/solana",
        cacheTTL: 60,
      }),
    []
  )

  const canSubmit = tokenAddress.trim().length > 0 && isValidSolanaAddress(tokenAddress.trim())

  const handleLoadPair = useCallback(async () => {
    const addr = tokenAddress.trim()
    if (!addr) {
      setError("Address is required")
      return
    }
    if (!isValidSolanaAddress(addr)) {
      setError("Invalid Solana address")
      return
    }

    setLoading(true)
    setError(null)
    setPairData(null)
    try {
      const info = (await adapter.fetchPair(addr)) as PairResponse
      if (!info || !info.pair) {
        setError("Pair not found")
      } else {
        setPairData(info)
        setLastUpdated(Date.now())
      }
    } catch (e: any) {
      setError(e?.message ?? "Failed to load pair data")
    } finally {
      setLoading(false)
    }
  }, [adapter, tokenAddress])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter" && canSubmit && !loading) {
        void handleLoadPair()
      }
    },
    [canSubmit, loading, handleLoadPair]
  )

  const handleClear = useCallback(() => {
    setTokenAddress("")
    setError(null)
    setPairData(null)
    setLastUpdated(null)
  }, [])

  return (
    <div className="space-y-6">
      <Grid columns={3} gap="4">
        <Input
          placeholder="Token address on Solana"
          value={tokenAddress}
          onChange={(e) => setTokenAddress(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-invalid={Boolean(error) || (tokenAddress ? !isValidSolanaAddress(tokenAddress) : false)}
        />
        <Button onClick={handleLoadPair} disabled={!canSubmit || loading}>
          {loading ? "Loading..." : "Load Pair"}
        </Button>
        <Button variant="secondary" onClick={handleClear} disabled={loading && !pairData}>
          Clear
        </Button>
      </Grid>

      {tokenAddress && !isValidSolanaAddress(tokenAddress) && (
        <div className="text-yellow-600 text-sm">Address format is invalid</div>
      )}

      {error && <div className="text-red-500">{error}</div>}

      {pairData?.pair && (
        <div className="space-y-2">
          <DexPairCard pairAddress={pairData.pair.address} stats={pairData.pair.stats} />
          {lastUpdated && (
            <p className="text-xs text-muted-foreground">
              Last updated: {new Date(lastUpdated).toISOString()}
            </p>
          )}
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={handleLoadPair} disabled={loading}>
              Refresh
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
