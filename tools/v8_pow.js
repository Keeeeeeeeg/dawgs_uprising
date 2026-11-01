// Math.pow exactly as V8 12.4 computes it (src/base/ieee754.cc, fdlibm's __ieee754_pow), the version the port's DMath
// reproduces and tests/golden/math.json was recorded with. Newer V8 (14.x, Node 26) computes pow differently in the
// last bit for about 1 input in 10, so the recording tools install this one in the web SIM's context: recordings then
// come out the same on every Node version. Check it against the 1810 recorded V8 12.4 results:
//   node -e "require('./tools/v8_pow.js').check()"
'use strict';
const dv = new DataView(new ArrayBuffer(8));
const hi = x => { dv.setFloat64(0, x); return dv.getInt32(0); };
const lo = x => { dv.setFloat64(0, x); return dv.getUint32(4); };
const words = (h, l) => { dv.setInt32(0, h); dv.setUint32(4, l >>> 0); return dv.getFloat64(0); };
const setLo = (x, l) => words(hi(x), l);
const setHi = (x, h) => words(h, lo(x));
const fromBits = big => { dv.setBigUint64(0, big); return dv.getFloat64(0); };
function scaleB(z, n) {
  while (n < -1000) { z *= fromBits(0x0170000000000000n); n += 1000; }
  while (n > 1000) { z *= fromBits(0x7E70000000000000n); n -= 1000; }
  return z * fromBits(BigInt(n + 1023) << 52n);
}

const two53 = 9007199254740992.0, huge = 1.0e300, tiny = 1.0e-300,
  L1 = 5.99999999999994648725e-01, L2 = 4.28571428578550184252e-01, L3 = 3.33333329818377432918e-01,
  L4 = 2.72728123808534006489e-01, L5 = 2.30660745775561754067e-01, L6 = 2.06975017800338417784e-01,
  P1 = 1.66666666666666019037e-01, P2 = -2.77777777770155933842e-03, P3 = 6.61375632143793436117e-05,
  P4 = -1.65339022054652515390e-06, P5 = 4.13813679705723846039e-08,
  lg2 = 6.93147180559945286227e-01, lg2_h = 6.93147182464599609375e-01, lg2_l = -1.90465429995776804525e-09,
  ovt = 8.0085662595372944372e-0017, cp = 9.61796693925975554329e-01, cp_h = 9.61796700954437255859e-01,
  cp_l = -7.02846165095275826516e-09, ivln2 = 1.44269504088896338700e+00,
  ivln2_h = 1.44269502162933349609e+00, ivln2_l = 1.92596299112661746887e-08;
const bp = [1.0, 1.5], dp_h = [0.0, 5.84962487220764160156e-01], dp_l = [0.0, 1.35003920212974897128e-08];

function pow(x, y) {
  x = +x; y = +y;
  let z, ax, z_h, z_l, p_h, p_l, y1, t1, t2, r, s, t, u, v, w, i, j, k, yisint, n;
  const hx = hi(x), hy = hi(y), lx = lo(x), ly = lo(y);
  let ix = hx & 0x7fffffff;
  const iy = hy & 0x7fffffff;
  if ((iy | ly) === 0) return 1.0;
  if (ix > 0x7ff00000 || (ix === 0x7ff00000 && lx !== 0) || iy > 0x7ff00000 || (iy === 0x7ff00000 && ly !== 0)) return x + y;
  yisint = 0;
  if (hx < 0) {
    if (iy >= 0x43400000) yisint = 2;
    else if (iy >= 0x3ff00000) {
      k = (iy >> 20) - 0x3ff;
      if (k > 20) { j = (ly >>> (52 - k)) | 0; if (((j << (52 - k)) | 0) === (ly | 0)) yisint = 2 - (j & 1); }
      else if (ly === 0) { j = iy >> (20 - k); if ((j << (20 - k)) === iy) yisint = 2 - (j & 1); }
    }
  }
  if (ly === 0) {
    if (iy === 0x7ff00000) {
      if (((ix - 0x3ff00000) | lx) === 0) return y - y;
      else if (ix >= 0x3ff00000) return hy >= 0 ? y : 0.0;
      else return hy < 0 ? -y : 0.0;
    }
    if (iy === 0x3ff00000) return hy < 0 ? 1.0 / x : x;
    if (hy === 0x40000000) return x * x;
    if (hy === 0x3fe00000 && hx >= 0) return Math.sqrt(x);
  }
  ax = Math.abs(x);
  if (lx === 0 && (ix === 0x7ff00000 || ix === 0 || ix === 0x3ff00000)) {
    z = ax;
    if (hy < 0) z = 1.0 / z;
    if (hx < 0) {
      if (((ix - 0x3ff00000) | yisint) === 0) z = NaN;
      else if (yisint === 1) z = -z;
    }
    return z;
  }
  n = (hx >> 31) + 1;
  if ((n | yisint) === 0) return NaN;
  s = 1.0;
  if ((n | (yisint - 1)) === 0) s = -1.0;
  if (iy > 0x41e00000) {
    if (iy > 0x43f00000) {
      if (ix <= 0x3fefffff) return hy < 0 ? huge * huge : tiny * tiny;
      if (ix >= 0x3ff00000) return hy > 0 ? huge * huge : tiny * tiny;
    }
    if (ix < 0x3fefffff) return hy < 0 ? s * huge * huge : s * tiny * tiny;
    if (ix > 0x3ff00000) return hy > 0 ? s * huge * huge : s * tiny * tiny;
    t = ax - 1.0;
    w = (t * t) * (0.5 - t * (0.3333333333333333333333 - t * 0.25));
    u = ivln2_h * t;
    v = t * ivln2_l - w * ivln2;
    t1 = setLo(u + v, 0);
    t2 = v - (t1 - u);
  } else {
    let ss, s2, s_h, s_l, t_h, t_l;
    n = 0;
    if (ix < 0x00100000) { ax *= two53; n -= 53; ix = hi(ax); }
    n += (ix >> 20) - 0x3ff;
    j = ix & 0x000fffff;
    ix = j | 0x3ff00000;
    if (j <= 0x3988E) k = 0;
    else if (j < 0xBB67A) k = 1;
    else { k = 0; n += 1; ix -= 0x00100000; }
    ax = setHi(ax, ix);
    u = ax - bp[k];
    v = 1.0 / (ax + bp[k]);
    ss = u * v;
    s_h = setLo(ss, 0);
    t_h = words(((ix >> 1) | 0x20000000) + 0x00080000 + (k << 18), 0);
    t_l = ax - (t_h - bp[k]);
    s_l = v * ((u - s_h * t_h) - s_h * t_l);
    s2 = ss * ss;
    r = s2 * s2 * (L1 + s2 * (L2 + s2 * (L3 + s2 * (L4 + s2 * (L5 + s2 * L6)))));
    r += s_l * (s_h + ss);
    s2 = s_h * s_h;
    t_h = setLo(3.0 + s2 + r, 0);
    t_l = r - ((t_h - 3.0) - s2);
    u = s_h * t_h;
    v = s_l * t_h + t_l * ss;
    p_h = setLo(u + v, 0);
    p_l = v - (p_h - u);
    z_h = cp_h * p_h;
    z_l = cp_l * p_h + p_l * cp + dp_l[k];
    t = n;
    t1 = setLo(((z_h + z_l) + dp_h[k]) + t, 0);
    t2 = z_l - (((t1 - t) - dp_h[k]) - z_h);
  }
  y1 = setLo(y, 0);
  p_l = (y - y1) * t1 + y * t2;
  p_h = y1 * t1;
  z = p_l + p_h;
  j = hi(z); i = lo(z) | 0;
  if (j >= 0x40900000) {
    if (((j - 0x40900000) | i) !== 0) return s * huge * huge;
    if (p_l + ovt > z - p_h) return s * huge * huge;
  } else if ((j & 0x7fffffff) >= 0x4090cc00) {
    if (((j - (0xc090cc00 | 0)) | i) !== 0) return s * tiny * tiny;
    if (p_l <= z - p_h) return s * tiny * tiny;
  }
  i = j & 0x7fffffff;
  k = (i >> 20) - 0x3ff;
  n = 0;
  if (i > 0x3fe00000) {
    n = j + (0x00100000 >> (k + 1));
    k = ((n & 0x7fffffff) >> 20) - 0x3ff;
    t = words(n & ~(0x000fffff >> k), 0);
    n = ((n & 0x000fffff) | 0x00100000) >> (20 - k);
    if (j < 0) n = -n;
    p_h -= t;
  }
  t = setLo(p_l + p_h, 0);
  u = t * lg2_h;
  v = (p_l - (t - p_h)) * lg2 + t * lg2_l;
  z = u + v;
  w = v - (z - u);
  t = z * z;
  t1 = z - t * (P1 + t * (P2 + t * (P3 + t * (P4 + t * P5))));
  r = (z * t1) / ((t1 - 2.0) - (w + z * w));
  z = 1.0 - (r - z);
  j = hi(z);
  j = (j + (n << 20)) | 0;
  if ((j >> 20) <= 0) z = scaleB(z, n);
  else z = setHi(z, (hi(z) + (n << 20)) | 0);
  return s * z;
}

/// Checks this pow against the V8 12.4 results in tests/golden/math.json.
function check() {
  const g = require('../tests/golden/math.json');
  const f = h => fromBits(BigInt('0x' + h));
  const hex = x => { dv.setFloat64(0, x); return dv.getBigUint64(0).toString(16).padStart(16, '0'); };
  let bad = 0;
  for (const row of g.cases.pow) { const got = pow(f(row[0]), f(row[1])), want = f(row[2]); if (hex(got) !== row[2] && !(Number.isNaN(got) && Number.isNaN(want))) bad++; }
  console.log(`v8_pow: ${g.cases.pow.length - bad} of ${g.cases.pow.length} match V8 ${g.v8}`);
  return bad === 0;
}

/// Installs this pow as Math.pow in a vm context (the web SIM's), so the recording is the same on any Node version.
function install(ctx) {
  const vm = require('vm');
  ctx.__v8pow = pow;
  vm.runInContext('Math.pow = globalThis.__v8pow;', ctx);
}

module.exports = { pow, check, install };
