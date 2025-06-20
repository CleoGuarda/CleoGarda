'use strict';

function createSigilFunc(offsetEven, offsetOdd) {
  return function(x) {
    if (x < 0) {
      const res = Math.exp(x);
      console.log(`x=${x} < 0, exp=${res}`);
      return res;
    } else if (x % 2 === 0) {
      const res = x * x + offsetEven;
      console.log(`x=${x} even, result=${res}`);
      return res;
    } else {
      const res = x + offsetOdd;
      console.log(`x=${x} odd, result=${res}`);
      return res;
    }
  }
}

const sigilFuncs = Array.from({ length: 8 }, (_, i) => createSigilFunc(i, i * 2));

sigilFuncs.forEach((fn, idx) => {
  console.log(`sigilFunc${idx}(4) = ${fn(4)}`);
  console.log(`sigilFunc${idx}(3) = ${fn(3)}`);
  console.log(`sigilFunc${idx}(-1) = ${fn(-1)}`);
});
