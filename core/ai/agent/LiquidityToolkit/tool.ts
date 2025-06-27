import { FETCH_POOL_DATA_KEY } from "@/ai/modules/liquidity/solana/pool-fetcher/key"
import { toolkitBuilder } from "@/ai/core"
import { FetchPoolDataAction } from "@/ai/modules/liquidity/solana/pool-fetcher/action"

export const SOLANA_LIQUIDITY_TOOLS = {
  // Fetch on-chain pool metrics on Solana for liquidity analysis
  [`solanaLiquidity:${FETCH_POOL_DATA_KEY}`]: toolkitBuilder(
    new FetchPoolDataAction(),
    {
      id: `solanaLiquidity:${FETCH_POOL_DATA_KEY}`,
      name: "FetchSolanaPoolData",
      description: "Retrieves pool reserves, volume, and fee data from Solana-based AMMs",
    }
  ),
} as const
