import { FETCH_POOL_DATA_KEY } from "@/ai/modules/liquidity/solana/pool-fetcher/key"
import { toolkitBuilder } from "@/ai/core"
import { FetchPoolDataAction } from "@/ai/modules/liquidity/solana/pool-fetcher/action"

export const SOLANA_LIQUIDITY_AGENTS = {
  /**
   * Solana pool data fetcher
   * Provides real-time on-chain liquidity metrics including reserves, volume, and fees
   */
  [`solanaLiquidity:${FETCH_POOL_DATA_KEY}`]: toolkitBuilder(
    new FetchPoolDataAction(),
    {
      id: `solanaLiquidity:${FETCH_POOL_DATA_KEY}`,
      name: "SolanaPoolDataFetcher",
      description:
        "Fetches liquidity pool reserves, trading volume, and fee metrics from Solana AMMs for analysis",
      category: "liquidity",
      network: "solana",
    }
  ),
} as const
