// ely_actions.ts
import { z } from "zod"

// Base schema for Alyssium actions
export type AlyssiumSchema = z.ZodObject<z.ZodRawShape>

// Standardized response for any action
export interface AlyssiumActionResponse<T> {
  notice: string
  data?: T
}

// Core structure defining an Alyssium action
export interface AlyssiumActionCore<
  S extends AlyssiumSchema,
  R,
  Ctx = unknown
> {
  id: string              // unique action identifier
  summary: string         // brief description of the action
  input: S                // Zod schema for input validation
  execute: (
    args: {
      payload: z.infer<S>
      context: Ctx
    }
  ) => Promise<AlyssiumActionResponse<R>>
}

// Union type covering any Alyssium action
export type AlyssiumAction = AlyssiumActionCore<AlyssiumSchema, unknown, unknown>

// Example: Define a tokenRisk action
export const tokenRiskAction: AlyssiumActionCore<
  z.ZodObject<{ tokenId: z.ZodString; }, "strip", z.ZodTypeAny>,
  { riskScore: number },
  { apiUrl: string }
> = {
  id: "tokenRisk",
  summary: "Calculate risk score for a given token",
  input: z.object({ tokenId: z.string() }),
  execute: async ({ payload, context }) => {
    const { tokenId } = payload
    const { apiUrl } = context
    const res = await fetch(`${apiUrl}/tokens/${tokenId}/risk`)
    const data = await res.json()
    return {
      notice: `Risk score fetched for ${tokenId}`,
      data: { riskScore: data.score }
    }
  }
}
