import React, { useState, useMemo } from 'react'
import { Grid } from '@/components/ui/grid'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { DexscreenerAdapter } from './dexscreener-adapter'
import { DexPairCard } from './DexPairCard'

export const SolanaDashboard: React.FC = () => {
  const [tokenAddress, setTokenAddress] = useState('')
  const [pairData, setPairData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const adapter = useMemo(
    () =>
      new DexscreenerAdapter({
        baseUrl: 'https://api.dexscreener.com/latest/dex/solana',
        cacheTTL: 60,
      }),
    []
  )

  const handleLoadPair = async () => {
    const addr = tokenAddress.trim()
    if (!addr) return
    setLoading(true)
    setError(null)
    setPairData(null)

    try {
      const info = await adapter.fetchPair(addr)
      if (!info || !info.pair) {
        setError('Pair not found')
      } else {
        setPairData(info)
      }
    } catch (e: any) {
      setError(e.message || 'Failed to load pair data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Grid columns={2} gap="4">
        <Input
          placeholder="Token address on Solana"
          value={tokenAddress}
          onChange={e => setTokenAddress(e.target.value)}
        />
        <Button
          onClick={handleLoadPair}
          disabled={!tokenAddress.trim() || loading}
        >
          {loading ? 'Loading...' : 'Load Pair'}
        </Button>
      </Grid>

      {error && (
        <div className="text-red-500">
          {error}
        </div>
      )}

      {pairData && (
        <DexPairCard
          pairAddress={pairData.pair.address}
          stats={pairData.pair.stats}
        />
      )}
    </div>
  )
}
