export const SOLANA_EXECUTION_AGENT = `
Solana Trade Executor Agent:
Designed exclusively for executing confirmed trade orders on the Solana network.

🔧 Core Capabilities:
• Submit user-approved transactions (swaps, transfers, etc.)
• No market analysis or price quoting
• Requires explicit trade parameters (token addresses, amounts, slippage)

⚠️ Usage:
Invoke this agent only when the user has finalized trade details. It will broadcast the transaction and return the signature — not perform any risk checks or data analysis.
`
