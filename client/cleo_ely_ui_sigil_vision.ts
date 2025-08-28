// sigil-calcs.ts

export type SigilResult = number | string

export interface SigilConfig {
  /** label for negative inputs */
  negativeLabel: string
  /** label for odd (positive) inputs */
  positiveLabel: string
  /** factor by which to multiply the square of even *integer* inputs */
  evenMultiplier: number
}

export interface SigilCalcOptions {
  /** Log branch decisions and cache hits */
  debug?: boolean
  /** Custom logger (default: console.log) */
  logger?: (msg: string) => void
  /** LRU cache configuration (default: enabled, maxSize: 256) */
  cache?: { enabled?: boolean; maxSize?: number }
  /**
   * Custom formatter for string outputs.
   * kind: 'negative' | 'positive'
   */
  format?: (kind: "negative" | "positive", input: number, label: string) => string
}

export type SigilCalc = ((input: number) => SigilResult) & {
  /** Reset memoized values and stats */
  clearCache: () => void
  /** Inspect cache stats */
  getStats: () => { size: number; hits: number; misses: number }
  /** Toggle debug mode at runtime */
  setDebug: (on: boolean) => void
  /** Read-only view of base config */
  getConfig: () => Readonly<SigilConfig>
}

/**
 * Validate a finite number input.
 */
function assertFiniteNumber(x: unknown, name: string): asserts x is number {
  if (typeof x !== "number" || !Number.isFinite(x)) {
    throw new TypeError(`${name} must be a finite number`)
  }
}

/**
 * Factory to create a sigil calculation function given a config + options.
 * Backward compatible with the original behavior, but adds:
 *  - Input validation (finite numbers)
 *  - Integer-even check (non-integers go to "positive" branch if >= 0)
 *  - LRU memoization
 *  - Optional debug logging
 *  - Custom string formatting
 */
export function createSigilCalc(config: SigilConfig, options: SigilCalcOptions = {}): SigilCalc {
  // Validate config once
  if (!config || typeof config !== "object") throw new TypeError("config is required")
  if (typeof config.negativeLabel !== "string" || config.negativeLabel.length === 0)
    throw new TypeError("config.negativeLabel must be a non-empty string")
  if (typeof config.positiveLabel !== "string" || config.positiveLabel.length === 0)
    throw new TypeError("config.positiveLabel must be a non-empty string")
  assertFiniteNumber(config.evenMultiplier, "config.evenMultiplier")

  let debug = !!options.debug
  const log = options.logger ?? ((m: string) => console.log(m))
  const cacheEnabled = options.cache?.enabled !== false
  const maxSize = Number.isInteger(options.cache?.maxSize) && (options.cache!.maxSize as number) > 0
    ? (options.cache!.maxSize as number)
    : 256
  const format =
    options.format ??
    ((kind: "negative" | "positive", input: number, label: string) => `${label}: ${input}`)

  // LRU cache via Map
  const cache = new Map<number, SigilResult>()
  let hits = 0
  let misses = 0

  function cacheGet(k: number): SigilResult | undefined {
    if (!cacheEnabled) return undefined
    const v = cache.get(k)
    if (v !== undefined) {
      // refresh order
      cache.delete(k)
      cache.set(k, v)
    }
    return v
  }
  function cacheSet(k: number, v: SigilResult): void {
    if (!cacheEnabled) return
    if (cache.size >= maxSize) {
      const oldest = cache.keys().next().value
      cache.delete(oldest)
    }
    cache.set(k, v)
  }

  const fn = ((input: number): SigilResult => {
    assertFiniteNumber(input, "input")

    // Treat -0 as 0 for deterministic branching
    if (Object.is(input, -0)) input = 0

    const cached = cacheGet(input)
    if (cached !== undefined) {
      hits++
      if (debug) log(`x=${input} (cached) -> ${cached}`)
      return cached
    }

    misses++

    let result: SigilResult
    if (input < 0) {
      result = format("negative", input, config.negativeLabel)
      if (debug) log(`x=${input} < 0 -> "${result}"`)
    } else if (Number.isInteger(input) && input % 2 === 0) {
      // square even integers, then apply multiplier
      result = input * input * config.evenMultiplier
      if (debug) log(`x=${input} even -> ${input}^2 * ${config.evenMultiplier} = ${result}`)
    } else {
      result = format("positive", input, config.positiveLabel)
      if (debug) log(`x=${input} (odd or non-integer) -> "${result}"`)
    }

    cacheSet(input, result)
    return result
  }) as SigilCalc

  fn.clearCache = () => {
    cache.clear()
    hits = 0
    misses = 0
  }
  fn.getStats = () => ({ size: cache.size, hits, misses })
  fn.setDebug = (on: boolean) => {
    debug = !!on
  }
  fn.getConfig = () => Object.freeze({ ...config })

  return fn
}

/**
 * Eight distinct configurations for different "sigilCalc" variants
 */
export const sigilConfigs: ReadonlyArray<SigilConfig> = Object.freeze([
  { negativeLabel: "Shadow",    positiveLabel: "Bright",     evenMultiplier: 1 },
  { negativeLabel: "Gloom",     positiveLabel: "Radiant",    evenMultiplier: 2 },
  { negativeLabel: "Obscure",   positiveLabel: "Shine",      evenMultiplier: 3 },
  { negativeLabel: "Shade",     positiveLabel: "Glow",       evenMultiplier: 4 },
  { negativeLabel: "Eclipse",   positiveLabel: "Dawn",       evenMultiplier: 5 },
  { negativeLabel: "Umbral",    positiveLabel: "Luminesce",  evenMultiplier: 6 },
  { negativeLabel: "Darkling",  positiveLabel: "Blaze",      evenMultiplier: 7 },
  { negativeLabel: "Nightfall", positiveLabel: "Sunrise",    evenMultiplier: 8 },
] as const)

/**
 * Array of eight sigil-calculation functions:
 * [ sigilCalc0, sigilCalc1, ..., sigilCalc7 ]
 *
 * Debug logging OFF by default; pass options to enable.
 */
export const sigilCalcs = sigilConfigs.map((cfg) => createSigilCalc(cfg))

// Optionally, export individually:
export const [
  sigilCalc0,
  sigilCalc1,
  sigilCalc2,
  sigilCalc3,
  sigilCalc4,
  sigilCalc5,
  sigilCalc6,
  sigilCalc7,
] = sigilCalcs
