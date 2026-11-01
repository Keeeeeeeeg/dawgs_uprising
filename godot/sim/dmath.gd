extends RefCounted
## Deterministic maths for the SIM: the exact results the web game gets from V8 (Node 22 / V8 12.4,
## which the golden recordings come from), on every OS. Godot's own sin/cos/atan2/pow call the
## platform C library, which can differ in the last bit between Windows, Linux and macOS, and from
## V8. One flipped bit is enough to make two lockstep machines drift apart.
##
## Ported from V8 12.4.254.21: src/base/ieee754.cc (fdlibm sin, cos, atan, atan2, pow) and
## src/builtins/math.tq (Math.hypot, Math.round). Every constant is stored as its exact bit
## pattern so it doesn't depend on how Godot parses long decimal literals.
##
## Use these in sim/ instead of sin(), cos(), atan2(), pow(), round() and Vector2.length().
## floor, ceil, abs, min, max, sqrt and + - * / are exact everywhere and can be used directly.

const M32 := 0xFFFFFFFF

static var _buf := PackedByteArray([0, 0, 0, 0, 0, 0, 0, 0])


# ---------- bit access (fdlibm's GET_HIGH_WORD and friends) ----------

static func bits(x: float) -> int:
	_buf.encode_double(0, x)
	return _buf.decode_s64(0)


static func _f(b: int) -> float:
	_buf.encode_s64(0, b)
	return _buf.decode_double(0)


## High word as a signed 32-bit int (like fdlibm's int32_t).
static func _hi(x: float) -> int:
	return bits(x) >> 32


## Low word as an unsigned 32-bit int.
static func _lo(x: float) -> int:
	return bits(x) & M32


static func _words(h: int, l: int) -> float:
	return _f(((h & M32) << 32) | (l & M32))


static func _set_lo(x: float, l: int) -> float:
	return _words(_hi(x), l)


static func _set_hi(x: float, h: int) -> float:
	return _words(h, _lo(x))


static func _i32(x: int) -> int:
	x &= M32
	return x - 0x100000000 if x >= 0x80000000 else x


# ---------- constants (fdlibm, as exact bits) ----------
static var INVPIO2: float = _f(0x3fe45f306dc9c883)
static var PIO2_1: float = _f(0x3ff921fb54400000)
static var PIO2_1T: float = _f(0x3dd0b4611a626331)
static var PIO2_2: float = _f(0x3dd0b4611a600000)
static var PIO2_2T: float = _f(0x3ba3198a2e037073)
static var PIO2_3: float = _f(0x3ba3198a2e000000)
static var PIO2_3T: float = _f(0x397b839a252049c1)
static var C1: float = _f(0x3fa555555555554c)
static var C2: float = _f(-0x40a93e93e93eae89)
static var C3: float = _f(0x3efa01a019cb1590)
static var C4: float = _f(-0x416d81b07f63ad53)
static var C5: float = _f(0x3e21ee9ebdb4b1c4)
static var C6: float = _f(-0x425705164177c72c)
static var S1: float = _f(-0x403aaaaaaaaaaab7)
static var S2: float = _f(0x3f8111111110f8a6)
static var S3: float = _f(-0x40d5fe5fe63e9e2b)
static var S4: float = _f(0x3ec71de357b1fe7d)
static var S5: float = _f(-0x41a51a1975d46315)
static var S6: float = _f(0x3de5d93a5acfd57c)
static var ATANHI0: float = _f(0x3fddac670561bb4f)
static var ATANHI1: float = _f(0x3fe921fb54442d18)
static var ATANHI2: float = _f(0x3fef730bd281f69b)
static var ATANHI3: float = _f(0x3ff921fb54442d18)
static var ATANLO0: float = _f(0x3c7a2b7f222f65e2)
static var ATANLO1: float = _f(0x3c81a62633145c07)
static var ATANLO2: float = _f(0x3c7007887af0cbbd)
static var ATANLO3: float = _f(0x3c91a62633145c07)
static var AT0: float = _f(0x3fd555555555550d)
static var AT1: float = _f(-0x403666666667143c)
static var AT2: float = _f(0x3fc24924920083ff)
static var AT3: float = _f(-0x40438e3901dce98f)
static var AT4: float = _f(0x3fb745cdc54c206e)
static var AT5: float = _f(-0x404c4f0d508b6593)
static var AT6: float = _f(0x3fb10d66a0d03d51)
static var AT7: float = _f(-0x405221d2ad210266)
static var AT8: float = _f(0x3fa97b4b24760deb)
static var AT9: float = _f(-0x405d4bbbd39593d1)
static var AT10: float = _f(0x3f90ad3ae322da11)
static var PI_O_4: float = _f(0x3fe921fb54442d18)
static var PI_O_2: float = _f(0x3ff921fb54442d18)
static var PI: float = _f(0x400921fb54442d18)
static var PI_LO: float = _f(0x3ca1a62633145c07)
static var DP_H1: float = _f(0x3fe2b80340000000)
static var DP_L1: float = _f(0x3e4cfdeb43cfd006)
static var L1: float = _f(0x3fe3333333333303)
static var L2: float = _f(0x3fdb6db6db6fabff)
static var L3: float = _f(0x3fd55555518f264d)
static var L4: float = _f(0x3fd17460a91d4101)
static var L5: float = _f(0x3fcd864a93c9db65)
static var L6: float = _f(0x3fca7e284a454eef)
static var P1: float = _f(0x3fc555555555553e)
static var P2: float = _f(-0x40993e93e941426d)
static var P3: float = _f(0x3f11566aaf25de2c)
static var P4: float = _f(-0x414442be3a2d940f)
static var P5: float = _f(0x3e66376972bea4d0)
static var LG2: float = _f(0x3fe62e42fefa39ef)
static var LG2_H: float = _f(0x3fe62e4300000000)
static var LG2_L: float = _f(-0x41dfa39ef35793c7)
static var OVT: float = _f(0x3c971547652b82fe)
static var CP: float = _f(0x3feec709dc3a03fd)
static var CP_H: float = _f(0x3feec709e0000000)
static var CP_L: float = _f(-0x41c1d01feba4fe0b)
static var IVLN2: float = _f(0x3ff71547652b82fe)
static var IVLN2_H: float = _f(0x3ff7154760000000)
static var IVLN2_L: float = _f(0x3e54ae0bf85ddf44)
static var THIRD: float = _f(0x3fd5555555555555)


# ---------- JS Math.round / Math.hypot ----------

## JS Math.round: halves go up (-2.5 -> -2), unlike Godot's round() (-2.5 -> -3).
static func round_js(x: float) -> float:
	var c := ceilf(x)
	return c - 1.0 if c - 0.5 > x else c


## JS Math.hypot(a, b), V8's exact algorithm (normalised Kahan sum), not sqrt(a*a+b*b).
static func hypot(a: float, b: float) -> float:
	if is_nan(a) or is_nan(b):
		return INF if is_inf(a) or is_inf(b) else NAN
	a = absf(a)
	b = absf(b)
	var mx := maxf(a, b)
	if is_inf(mx):
		return INF
	if mx == 0.0:
		return 0.0
	var s := 0.0
	var comp := 0.0
	for v in [a, b]:
		var n: float = v / mx
		var summand := n * n - comp
		var prelim := s + summand
		comp = (prelim - s) - summand
		s = prelim
	return sqrt(s) * mx


## JS Math.hypot with three arguments.
static func hypot3(a: float, b: float, c: float) -> float:
	if is_nan(a) or is_nan(b) or is_nan(c):
		return INF if is_inf(a) or is_inf(b) or is_inf(c) else NAN
	a = absf(a)
	b = absf(b)
	c = absf(c)
	var mx := maxf(a, maxf(b, c))
	if is_inf(mx):
		return INF
	if mx == 0.0:
		return 0.0
	var s := 0.0
	var comp := 0.0
	for v in [a, b, c]:
		var n: float = v / mx
		var summand := n * n - comp
		var prelim := s + summand
		comp = (prelim - s) - summand
		s = prelim
	return sqrt(s) * mx


# ---------- sin / cos (fdlibm) ----------

## Returns [n, y0, y1]: x = n*pi/2 + (y0 + y1). Handles |x| up to about 1.6e6;
## larger arguments (never used by the game) report an error.
static func _rem_pio2(x: float) -> Array:
	var hx := _hi(x)
	var ix := hx & 0x7FFFFFFF
	if ix <= 0x3FE921FB:
		return [0, x, 0.0]
	var z: float
	var y0: float
	var y1: float
	if ix < 0x4002D97C:
		if hx > 0:
			z = x - PIO2_1
			if ix != 0x3FF921FB:
				y0 = z - PIO2_1T
				y1 = (z - y0) - PIO2_1T
			else:
				z -= PIO2_2
				y0 = z - PIO2_2T
				y1 = (z - y0) - PIO2_2T
			return [1, y0, y1]
		z = x + PIO2_1
		if ix != 0x3FF921FB:
			y0 = z + PIO2_1T
			y1 = (z - y0) + PIO2_1T
		else:
			z += PIO2_2
			y0 = z + PIO2_2T
			y1 = (z - y0) + PIO2_2T
		return [-1, y0, y1]
	if ix <= 0x413921FB:
		var t := absf(x)
		var n := int(t * INVPIO2 + 0.5)
		var fn := float(n)
		var r := t - fn * PIO2_1
		var w := fn * PIO2_1T
		if n < 32 and ix != NPIO2_HW[n - 1]:
			y0 = r - w
		else:
			var j := ix >> 20
			y0 = r - w
			var i := j - ((_hi(y0) >> 20) & 0x7FF)
			if i > 16:
				t = r
				w = fn * PIO2_2
				r = t - w
				w = fn * PIO2_2T - ((t - r) - w)
				y0 = r - w
				i = j - ((_hi(y0) >> 20) & 0x7FF)
				if i > 49:
					t = r
					w = fn * PIO2_3
					r = t - w
					w = fn * PIO2_3T - ((t - r) - w)
					y0 = r - w
		y1 = (r - y0) - w
		if hx < 0:
			return [-n, -y0, -y1]
		return [n, y0, y1]
	if ix >= 0x7FF00000:
		return [0, x - x, x - x]
	push_error("dmath: argument %s too large for sin/cos" % x)
	return [0, NAN, NAN]


const NPIO2_HW := [
	0x3FF921FB, 0x400921FB, 0x4012D97C, 0x401921FB, 0x401F6A7A, 0x4022D97C,
	0x4025FDBB, 0x402921FB, 0x402C463A, 0x402F6A7A, 0x4031475C, 0x4032D97C,
	0x40346B9C, 0x4035FDBB, 0x40378FDB, 0x403921FB, 0x403AB41B, 0x403C463A,
	0x403DD85A, 0x403F6A7A, 0x40407E4C, 0x4041475C, 0x4042106C, 0x4042D97C,
	0x4043A28C, 0x40446B9C, 0x404534AC, 0x4045FDBB, 0x4046C6CB, 0x40478FDB,
	0x404858EB, 0x404921FB,
]


static func _k_cos(x: float, y: float) -> float:
	var ix := _hi(x) & 0x7FFFFFFF
	if ix < 0x3E400000:
		if int(x) == 0:
			return 1.0
	var z := x * x
	var r := z * (C1 + z * (C2 + z * (C3 + z * (C4 + z * (C5 + z * C6)))))
	if ix < 0x3FD33333:
		return 1.0 - (0.5 * z - (z * r - x * y))
	var qx: float
	if ix > 0x3FE90000:
		qx = 0.28125
	else:
		qx = _words(ix - 0x00200000, 0)
	var iz := 0.5 * z - qx
	var a := 1.0 - qx
	return a - (iz - (z * r - x * y))


static func _k_sin(x: float, y: float, iy: int) -> float:
	var ix := _hi(x) & 0x7FFFFFFF
	if ix < 0x3E400000:
		if int(x) == 0:
			return x
	var z := x * x
	var v := z * x
	var r := S2 + z * (S3 + z * (S4 + z * (S5 + z * S6)))
	if iy == 0:
		return x + v * (S1 + z * r)
	return x - ((z * (0.5 * y - v * r) - y) - v * S1)


static func sin_(x: float) -> float:
	var ix := _hi(x) & 0x7FFFFFFF
	if ix <= 0x3FE921FB:
		return _k_sin(x, 0.0, 0)
	if ix >= 0x7FF00000:
		return x - x
	var q := _rem_pio2(x)
	var y0: float = q[1]
	var y1: float = q[2]
	match int(q[0]) & 3:
		0: return _k_sin(y0, y1, 1)
		1: return _k_cos(y0, y1)
		2: return -_k_sin(y0, y1, 1)
		_: return -_k_cos(y0, y1)


static func cos_(x: float) -> float:
	var ix := _hi(x) & 0x7FFFFFFF
	if ix <= 0x3FE921FB:
		return _k_cos(x, 0.0)
	if ix >= 0x7FF00000:
		return x - x
	var q := _rem_pio2(x)
	var y0: float = q[1]
	var y1: float = q[2]
	match int(q[0]) & 3:
		0: return _k_cos(y0, y1)
		1: return -_k_sin(y0, y1, 1)
		2: return -_k_cos(y0, y1)
		_: return _k_sin(y0, y1, 1)


# ---------- atan / atan2 (fdlibm) ----------

static func atan_(x: float) -> float:
	var hx := _hi(x)
	var ix := hx & 0x7FFFFFFF
	var id: int
	if ix >= 0x44100000:
		if ix > 0x7FF00000 or (ix == 0x7FF00000 and _lo(x) != 0):
			return x + x
		return ATANHI3 + ATANLO3 if hx > 0 else -ATANHI3 - ATANLO3
	if ix < 0x3FDC0000:
		if ix < 0x3E400000:
			if 1.0e300 + x > 1.0:
				return x
		id = -1
	else:
		x = absf(x)
		if ix < 0x3FF30000:
			if ix < 0x3FE60000:
				id = 0
				x = (2.0 * x - 1.0) / (2.0 + x)
			else:
				id = 1
				x = (x - 1.0) / (x + 1.0)
		else:
			if ix < 0x40038000:
				id = 2
				x = (x - 1.5) / (1.0 + 1.5 * x)
			else:
				id = 3
				x = -1.0 / x
	var z := x * x
	var w := z * z
	var s1 := z * (AT0 + w * (AT2 + w * (AT4 + w * (AT6 + w * (AT8 + w * AT10)))))
	var s2 := w * (AT1 + w * (AT3 + w * (AT5 + w * (AT7 + w * AT9))))
	if id < 0:
		return x - x * (s1 + s2)
	var hi: float = [ATANHI0, ATANHI1, ATANHI2, ATANHI3][id]
	var lo: float = [ATANLO0, ATANLO1, ATANLO2, ATANLO3][id]
	z = hi - ((x * (s1 + s2) - lo) - x)
	return -z if hx < 0 else z


static func atan2_(y: float, x: float) -> float:
	const TINY := 1.0e-300
	var hx := _hi(x)
	var lx := _lo(x)
	var ix := hx & 0x7FFFFFFF
	var hy := _hi(y)
	var ly := _lo(y)
	var iy := hy & 0x7FFFFFFF
	if (ix | (1 if lx != 0 else 0)) > 0x7FF00000 or (iy | (1 if ly != 0 else 0)) > 0x7FF00000:
		return x + y
	if hx == 0x3FF00000 and lx == 0:
		return atan_(y)
	var m := ((hy >> 31) & 1) | ((hx >> 30) & 2)
	if (iy | ly) == 0:
		match m:
			0, 1: return y
			2: return PI + TINY
			_: return -PI - TINY
	if (ix | lx) == 0:
		return -PI_O_2 - TINY if hy < 0 else PI_O_2 + TINY
	if ix == 0x7FF00000:
		if iy == 0x7FF00000:
			match m:
				0: return PI_O_4 + TINY
				1: return -PI_O_4 - TINY
				2: return 3.0 * PI_O_4 + TINY
				_: return -3.0 * PI_O_4 - TINY
		else:
			match m:
				0: return 0.0
				1: return -0.0
				2: return PI + TINY
				_: return -PI - TINY
	if iy == 0x7FF00000:
		return -PI_O_2 - TINY if hy < 0 else PI_O_2 + TINY
	var k := (iy - ix) >> 20
	var z: float
	if k > 60:
		z = PI_O_2 + 0.5 * PI_LO
		m &= 1
	elif hx < 0 and k < -60:
		z = 0.0
	else:
		z = atan_(absf(y / x))
	match m:
		0: return z
		1: return -z
		2: return PI - (z - PI_LO)
		_: return (z - PI_LO) - PI


# ---------- pow (fdlibm) ----------

static func pow_(x: float, y: float) -> float:
	const HUGE := 1.0e300
	const TINY := 1.0e-300
	const TWO53 := 9007199254740992.0
	var hx := _hi(x)
	var lx := _lo(x)
	var hy := _hi(y)
	var ly := _lo(y)
	var ix := hx & 0x7fffffff
	var iy := hy & 0x7fffffff
	if (iy | ly) == 0:
		return 1.0
	if ix > 0x7ff00000 or (ix == 0x7ff00000 and lx != 0) or iy > 0x7ff00000 or (iy == 0x7ff00000 and ly != 0):
		return x + y
	var yisint := 0
	var j: int
	var k: int
	if hx < 0:
		if iy >= 0x43400000:
			yisint = 2
		elif iy >= 0x3ff00000:
			k = (iy >> 20) - 0x3ff
			if k > 20:
				j = ly >> (52 - k)
				if ((j << (52 - k)) & M32) == ly:
					yisint = 2 - (j & 1)
			elif ly == 0:
				j = iy >> (20 - k)
				if (j << (20 - k)) == iy:
					yisint = 2 - (j & 1)
	if ly == 0:
		if iy == 0x7ff00000:
			if ((ix - 0x3ff00000) | lx) == 0:
				return y - y
			elif ix >= 0x3ff00000:
				return y if hy >= 0 else 0.0
			else:
				return -y if hy < 0 else 0.0
		if iy == 0x3ff00000:
			return 1.0 / x if hy < 0 else x
		if hy == 0x40000000:
			return x * x
		if hy == 0x3fe00000 and hx >= 0:
			return sqrt(x)
	var ax := absf(x)
	var z: float
	if lx == 0:
		if ix == 0x7ff00000 or ix == 0 or ix == 0x3ff00000:
			z = ax
			if hy < 0:
				z = 1.0 / z
			if hx < 0:
				if ((ix - 0x3ff00000) | yisint) == 0:
					z = NAN
				elif yisint == 1:
					z = -z
			return z
	var n := (hx >> 31) + 1
	if (n | yisint) == 0:
		return NAN
	var s := 1.0
	if (n | (yisint - 1)) == 0:
		s = -1.0
	var t: float
	var t1: float
	var t2: float
	var u: float
	var v: float
	var w: float
	if iy > 0x41e00000:
		if iy > 0x43f00000:
			if ix <= 0x3fefffff:
				return HUGE * HUGE if hy < 0 else TINY * TINY
			if ix >= 0x3ff00000:
				return HUGE * HUGE if hy > 0 else TINY * TINY
		if ix < 0x3fefffff:
			return s * HUGE * HUGE if hy < 0 else s * TINY * TINY
		if ix > 0x3ff00000:
			return s * HUGE * HUGE if hy > 0 else s * TINY * TINY
		t = ax - 1.0
		w = (t * t) * (0.5 - t * (THIRD - t * 0.25))
		u = IVLN2_H * t
		v = t * IVLN2_L - w * IVLN2
		t1 = _set_lo(u + v, 0)
		t2 = v - (t1 - u)
	else:
		n = 0
		if ix < 0x00100000:
			ax *= TWO53
			n -= 53
			ix = _hi(ax)
		n += (ix >> 20) - 0x3ff
		j = ix & 0x000fffff
		ix = j | 0x3ff00000
		if j <= 0x3988E:
			k = 0
		elif j < 0xBB67A:
			k = 1
		else:
			k = 0
			n += 1
			ix -= 0x00100000
		ax = _set_hi(ax, ix)
		var bp := 1.5 if k == 1 else 1.0
		var dp_h := DP_H1 if k == 1 else 0.0
		var dp_l := DP_L1 if k == 1 else 0.0
		u = ax - bp
		v = 1.0 / (ax + bp)
		var ss := u * v
		var s_h := _set_lo(ss, 0)
		var t_h := _words(((ix >> 1) | 0x20000000) + 0x00080000 + (k << 18), 0)
		var t_l := ax - (t_h - bp)
		var s_l := v * ((u - s_h * t_h) - s_h * t_l)
		var s2 := ss * ss
		var r := s2 * s2 * (L1 + s2 * (L2 + s2 * (L3 + s2 * (L4 + s2 * (L5 + s2 * L6)))))
		r += s_l * (s_h + ss)
		s2 = s_h * s_h
		t_h = _set_lo(3.0 + s2 + r, 0)
		t_l = r - ((t_h - 3.0) - s2)
		u = s_h * t_h
		v = s_l * t_h + t_l * ss
		var p_h0 := _set_lo(u + v, 0)
		var p_l0 := v - (p_h0 - u)
		var z_h := CP_H * p_h0
		var z_l := CP_L * p_h0 + p_l0 * CP + dp_l
		t = float(n)
		t1 = _set_lo(((z_h + z_l) + dp_h) + t, 0)
		t2 = z_l - (((t1 - t) - dp_h) - z_h)
	var y1 := _set_lo(y, 0)
	var p_l := (y - y1) * t1 + y * t2
	var p_h := y1 * t1
	z = p_l + p_h
	j = _hi(z)
	var i := _i32(_lo(z))
	if j >= 0x40900000:
		if ((j - 0x40900000) | i) != 0:
			return s * HUGE * HUGE
		if p_l + OVT > z - p_h:
			return s * HUGE * HUGE
	elif (j & 0x7fffffff) >= 0x4090cc00:
		if ((j - _i32(0xc090cc00)) | i) != 0:
			return s * TINY * TINY
		if p_l <= z - p_h:
			return s * TINY * TINY
	i = j & 0x7fffffff
	k = (i >> 20) - 0x3ff
	n = 0
	if i > 0x3fe00000:
		n = j + (0x00100000 >> (k + 1))
		k = ((n & 0x7fffffff) >> 20) - 0x3ff
		t = _words(n & ~(0x000fffff >> k), 0)
		n = ((n & 0x000fffff) | 0x00100000) >> (20 - k)
		if j < 0:
			n = -n
		p_h -= t
	t = _set_lo(p_l + p_h, 0)
	u = t * LG2_H
	v = (p_l - (t - p_h)) * LG2 + t * LG2_L
	z = u + v
	w = v - (z - u)
	t = z * z
	t1 = z - t * (P1 + t * (P2 + t * (P3 + t * (P4 + t * P5))))
	var r2 := (z * t1) / ((t1 - 2.0) - (w + z * w))
	z = 1.0 - (r2 - z)
	j = _i32(_hi(z) + _i32((n & M32) << 20))
	if (j >> 20) <= 0:
		z = _scalbn(z, n)
	else:
		z = _set_hi(z, _i32(_hi(z) + _i32((n & M32) << 20)))
	return s * z


## z * 2^n, exactly (only reached for results near the bottom of the double range).
static func _scalbn(z: float, n: int) -> float:
	while n < -1000:
		z *= _f(0x0170000000000000) # 2^-1000
		n += 1000
	while n > 1000:
		z *= _f(0x7E70000000000000) # 2^1000
		n -= 1000
	return z * _words((n + 1023) << 20, 0)
