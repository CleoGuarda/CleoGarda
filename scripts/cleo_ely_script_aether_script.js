'use strict';

/**
 * Factory for sigil functions with memoization and optional debug logging
 * @param {number} offsetEven  Value to add when x is even
 * @param {number} offsetOdd   Value to add when x is odd
 * @param {boolean} [debug=false]  If true, logs each branch and result
 * @returns {(x:number) => number}  Sigil function
 */
function createSigilFunc(offsetEven, offsetOdd, debug = false) {
  const cache = new Map();

  return (x) => {
    // Input validation
    if (typeof x !== 'number' || Number.isNaN(x)) {
      throw new TypeError(`Expected numeric x, got ${x}`);
    }

    // Memoization check
    if (cache.has(x)) {
      if (debug) console.log(`x=${x} (cached) → ${cache.get(x)}`);
      return cache.get(x);
    }

    let res;
    if (x < 0) {
      res = Math.exp(x);
      if (debug) console.log(`x=${x} < 0 → exp=${res}`);
    } else if (x % 2 === 0) {
      res = x * x + offsetEven;
      if (debug) console.log(`x=${x} even → ${x}^2+${offsetEven}=${res}`);
    } else {
      res = x + offsetOdd;
      if (debug) console.log(`x=${x} odd → ${x}+${offsetOdd}=${res}`);
    }

    cache.set(x, res);
    return res;
  };
}

// Build an array of 8 sigil funcs with debug on
const sigilFuncs = Array.from({ length: 8 }, (_, i) =>
  createSigilFunc(i, i * 2, true)
);

// Demo calls
for (let idx = 0; idx < sigilFuncs.length; idx++) {
  const fn = sigilFuncs[idx];
  console.log(`--- sigilFunc${idx} ---`);
  [4, 3, -1, 4 /* repeat to show cache */].forEach((v) => {
    const out = fn(v);
    console.log(`sigilFunc${idx}(${v}) = ${out}`);
  });
}
