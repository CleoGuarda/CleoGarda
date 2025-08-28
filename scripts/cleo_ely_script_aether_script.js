'use strict';

/**
 * createSigilFunc — enhanced, backward-compatible, and deterministic
 * - Supports options object OR (offsetEven, offsetOdd, debug) legacy signature
 * - Bounded LRU memoization (default maxSize=256)
 * - Safe input validation, consistent logging, and introspection helpers
 *
 * @param {number|Object} offsetEvenOrOptions
 *   Either offsetEven (number) for legacy signature, or an options object:
 *   {
 *     offsetEven: number,
 *     offsetOdd: number,
 *     debug?: boolean,
 *     logger?: (msg: string) => void,
 *     cache?: { enabled?: boolean, maxSize?: number }
 *   }
 * @param {number} [offsetOdd]
 * @param {boolean} [debug=false]
 * @returns {((x:number)=>number) & {
 *   clearCache: () => void,
 *   getStats: () => { size:number, hits:number, misses:number },
 *   setDebug: (on:boolean) => void
 * }}
 */
function createSigilFunc(offsetEvenOrOptions, offsetOdd, debug = false) {
  // ---- Parse options (backward compatible) ----
  /** @type {{offsetEven:number, offsetOdd:number, debug:boolean, logger:(m:string)=>void, cache:{enabled:boolean, maxSize:number}}} */
  const cfg = (function resolveConfig() {
    if (typeof offsetEvenOrOptions === 'object' && offsetEvenOrOptions !== null) {
      const {
        offsetEven,
        offsetOdd,
        debug = false,
        logger = (m) => console.log(m),
        cache = {},
      } = offsetEvenOrOptions;

      assertNumber(offsetEven, 'offsetEven');
      assertNumber(offsetOdd, 'offsetOdd');

      return {
        offsetEven,
        offsetOdd,
        debug: !!debug,
        logger,
        cache: {
          enabled: cache.enabled !== false,
          maxSize: Number.isInteger(cache.maxSize) && cache.maxSize > 0 ? cache.maxSize : 256,
        },
      };
    }

    // Legacy (offsetEven, offsetOdd, debug)
    assertNumber(offsetEvenOrOptions, 'offsetEven');
    assertNumber(offsetOdd, 'offsetOdd');

    return {
      offsetEven: Number(offsetEvenOrOptions),
      offsetOdd: Number(offsetOdd),
      debug: !!debug,
      logger: (m) => console.log(m),
      cache: { enabled: true, maxSize: 256 },
    };
  })();

  // ---- Bounded LRU cache via Map (insertion order) ----
  const cache = new Map();
  let hits = 0;
  let misses = 0;

  /** @param {number} key @param {number} value */
  function cacheSet(key, value) {
    if (!cfg.cache.enabled) return;
    // Evict least-recently-used (oldest) if at capacity
    if (cache.size >= cfg.cache.maxSize) {
      // Map keys() iteration order is insertion order
      const oldestKey = cache.keys().next().value;
      cache.delete(oldestKey);
    }
    cache.set(key, value);
  }

  /** @param {number} key */
  function cacheGet(key) {
    if (!cfg.cache.enabled) return undefined;
    if (!cache.has(key)) return undefined;
    const val = cache.get(key);
    // Refresh entry to mark as most-recently-used
    cache.delete(key);
    cache.set(key, val);
    return val;
  }

  // ---- Core function ----
  const fn = function sigil(x) {
    // Input validation
    if (typeof x !== 'number' || Number.isNaN(x) || !Number.isFinite(x)) {
      throw new TypeError(`Expected finite number x, got ${x}`);
    }

    // Treat -0 as 0 for deterministic behavior
    if (Object.is(x, -0)) x = 0;

    // Memoization check
    const cached = cacheGet(x);
    if (cached !== undefined) {
      hits++;
      if (cfg.debug) cfg.logger(`x=${x} (cached) -> ${cached}`);
      return cached;
    }

    misses++;

    let res;
    if (x < 0) {
      // Negative branch: exponential
      res = Math.exp(x);
      if (cfg.debug) cfg.logger(`x=${x} < 0 -> exp(${x}) = ${res}`);
    } else if (Number.isInteger(x) && x % 2 === 0) {
      // Even integer branch: square + offsetEven
      res = x * x + cfg.offsetEven;
      if (cfg.debug) cfg.logger(`x=${x} even -> ${x}^2 + ${cfg.offsetEven} = ${res}`);
    } else {
      // Odd or non-integer non-negative branch: x + offsetOdd
      res = x + cfg.offsetOdd;
      if (cfg.debug) cfg.logger(`x=${x} other -> ${x} + ${cfg.offsetOdd} = ${res}`);
    }

    cacheSet(x, res);
    return res;
  };

  // ---- Introspection / controls ----
  fn.clearCache = function clearCache() {
    cache.clear();
    hits = 0;
    misses = 0;
  };
  fn.getStats = function getStats() {
    return { size: cache.size, hits, misses };
  };
  fn.setDebug = function setDebug(on) {
    cfg.debug = !!on;
  };

  return fn;
}

/** @param {unknown} n @param {string} name */
function assertNumber(n, name) {
  if (typeof n !== 'number' || Number.isNaN(n) || !Number.isFinite(n)) {
    throw new TypeError(`${name} must be a finite number`);
  }
}

// ------------------ Demo ------------------
// Build an array of 8 sigil funcs (debug on)
const sigilFuncs = Array.from({ length: 8 }, (_, i) =>
  createSigilFunc({ offsetEven: i, offsetOdd: i * 2, debug: true, cache: { maxSize: 64 } })
);

// Demo calls
for (let idx = 0; idx < sigilFuncs.length; idx++) {
  const fn = sigilFuncs[idx];
  console.log(`--- sigilFunc${idx} ---`);
  [4, 3, -1, 4 /* repeat to show cache */].forEach((v) => {
    const out = fn(v);
    console.log(`sigilFunc${idx}(${v}) = ${out}`);
  });
  console.log('stats:', fn.getStats());
}
