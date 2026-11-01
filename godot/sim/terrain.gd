extends RefCounted
## Terrain: heights, passability and props for one battle, ported from the web SIM's buildMap()
## and its terrain queries (heightAt, cellOf, passable). Bit-exact with the web game: heights are
## 32-bit floats like the web's Float32Array, all maths goes through dmath.gd, and every number
## comes from data/mapgen.json ("terrain").
##
## Speed: GDScript is much slower than JavaScript, so the per-vertex loops skip work that provably
## can't change the result (for example a blob whose nearest possible value is already below the
## current land value). Each shortcut is exact; the tests compare every height with the web game.

const DMath := preload("res://sim/dmath.gd")
const ValueNoise := preload("res://sim/noise.gd")
const Maps := preload("res://sim/maps.gd")

var W := 0.0
var H := 0.0
var X0 := 0.0
var Z0 := 0.0
var cell := 0.0
var GW := 0
var GH := 0
var VW := 0
var VH := 0
var hv := PackedFloat32Array()   # (GW+1) x (GH+1) vertex heights
var land_grid := PackedByteArray()    # GW x GH: 1 = ground units can stand here
var water_grid := PackedByteArray()   # GW x GH: 1 = deep enough for boats
var props: Array = []            # rocks, ruins, wrecks... {type,x,z,rot,v,h,circles}
var coves: Array = []            # inlets cut toward coastal bases {zone,ax,az,bx,bz,ux,uz,R}


# ---------- queries (web heightAt, cellOf, passable) ----------

func height_at(x: float, z: float) -> float:
	var fx := (x - X0) / cell
	var fz := (z - Z0) / cell
	fx = maxf(0.0, minf(GW - 0.001, fx))
	fz = maxf(0.0, minf(GH - 0.001, fz))
	var i := int(floorf(fx))
	var j := int(floorf(fz))
	var u := fx - i
	var v := fz - j
	var a: float = hv[j * VW + i]
	var b: float = hv[j * VW + i + 1]
	var c: float = hv[(j + 1) * VW + i]
	var d: float = hv[(j + 1) * VW + i + 1]
	return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v


func cell_of(x: float, z: float) -> int:
	var i := int(floorf((x - X0) / cell))
	var j := int(floorf((z - Z0) / cell))
	if i < 0 or j < 0 or i >= GW or j >= GH:
		return -1
	return j * GW + i


func passable(x: float, z: float, grid: PackedByteArray = PackedByteArray()) -> bool:
	var c := cell_of(x, z)
	if c < 0:
		return false
	return (grid if grid.size() > 0 else land_grid)[c] == 1


## Vertex height nearest a point (web hvAt / hAt inside buildMap).
func _hv_at(x: float, z: float) -> float:
	var i := int(maxf(0.0, minf(GW, DMath.round_js((x - X0) / cell))))
	var j := int(maxf(0.0, minf(GH, DMath.round_js((z - Z0) / cell))))
	return hv[j * VW + i]


# ---------- building (web buildMap) ----------

## m: the map with "zonesFinal" (after start slots). seed: the battle seed.
static func build(m: Dictionary, seed: int, balance: Dictionary, gen: Dictionary) -> RefCounted:
	var t := new()
	t._build(m, seed, balance, gen)
	return t


func _build(m: Dictionary, seed: int, balance: Dictionary, gen: Dictionary) -> void:
	var T: Dictionary = gen.terrain
	var BZ: Dictionary = balance.zones
	cell = T.cell
	W = m.W
	H = m.H
	GW = int(W / cell)
	GH = int(H / cell)
	X0 = -W / 2.0
	Z0 = -H / 2.0
	VW = GW + 1
	VH = GH + 1
	var ns: Array = T.noiseSeeds
	var size: int = T.noiseSize
	var n1 := ValueNoise.new(seed + int(ns[0]), size)
	var n2 := ValueNoise.new(seed + int(ns[1]), size)
	var n3 := ValueNoise.new(seed + int(ns[2]), size)
	var oct: int = T.octaves
	var gain: float = T.octaveGain
	var lac: float = T.octaveLacunarity
	var zones: Array = m.zonesFinal
	var SX: float = m.ns[0]
	var SZ: float = m.ns[1]

	# shapes as flat arrays for fast loops
	var bl := PackedFloat64Array()   # x, z, rx, rz
	for b: Dictionary in m.blobs:
		bl.append_array([b.x, b.z, b.rx, b.rz])
	var zb := PackedFloat64Array()   # zone blobs: x, z, r (rx = rz)
	var pad: float = T.zoneBlobPad
	for z: Array in zones:
		zb.append_array([z[2], z[3], BZ[z[1]].r + pad])
	var cvs := PackedFloat64Array()  # carves: x, z, r
	for c: Dictionary in m.carves:
		cvs.append_array([c.x, c.z, c.r])
	var nk := PackedFloat64Array()   # necks: ax, az, bx, bz, w, minx, maxx, minz, maxz
	for n: Dictionary in m.necks:
		nk.append_array([n.a[0], n.a[1], n.b[0], n.b[1], n.w,
			minf(n.a[0], n.b[0]), maxf(n.a[0], n.b[0]), minf(n.a[1], n.b[1]), maxf(n.a[1], n.b[1])])
	var rg := PackedFloat64Array()   # ridges: ax, az, bx, bz, w, h, minx, maxx, minz, maxz
	for r: Dictionary in m.ridges:
		rg.append_array([r.a[0], r.a[1], r.b[0], r.b[1], r.w, r.h,
			minf(r.a[0], r.b[0]), maxf(r.a[0], r.b[0]), minf(r.a[1], r.b[1]), maxf(r.a[1], r.b[1])])

	var land_start: float = T.landStart
	var zw: float = T.zoneBlobWeight
	var lf: float = T.landNoiseFreq
	var lox: float = T.landNoiseOffX
	var loz: float = T.landNoiseOffZ
	var lmid: float = T.landNoiseMid
	var lamp: float = T.landNoiseAmp
	var cdep: float = gen.convert.carveDepth
	var cflo: float = gen.convert.carveFloor
	var nland: float = gen.convert.neckLand
	var efade: float = gen.convert.edgeFade
	var sea_floor: float = T.seaFloor
	var sea_slope: float = T.seaSlope
	var sea_drop: float = T.seaDrop
	var rise: float = T.hillRise
	var base_h: float = T.baseHeight
	var cap: float = T.landCap
	var lift: float = T.landLift
	var hf: float = T.hillNoiseFreq
	var hmid: float = T.hillNoiseMid
	var hamp: float = T.hillAmp
	var rexp: float = T.ridgeExp
	var rbase: float = T.ridgeBase
	var rvar: float = T.ridgeVar
	var rf: float = T.ridgeNoiseFreq

	var land := func(x: float, z: float) -> float:
		var L := land_start
		var k := 0
		while k < bl.size():
			# hypot >= its larger argument, so 1 - max(...) bounds v from above: skip blobs that can't win
			var ax := absf((x - bl[k]) / bl[k + 2])
			var az := absf((z - bl[k + 1]) / bl[k + 3])
			if 1.0 - maxf(ax, az) > L:
				var v := 1.0 - DMath.hypot((x - bl[k]) / bl[k + 2], (z - bl[k + 1]) / bl[k + 3])
				if v > L:
					L = v
			k += 4
		k = 0
		while k < zb.size():
			var ax := absf((x - zb[k]) / zb[k + 2])
			var az := absf((z - zb[k + 1]) / zb[k + 2])
			if (1.0 - maxf(ax, az)) * zw > L:
				var v := (1.0 - DMath.hypot((x - zb[k]) / zb[k + 2], (z - zb[k + 1]) / zb[k + 2])) * zw
				if v > L:
					L = v
			k += 3
		L += (n1.fbm(x / SX * lf + lox, z / SZ * lf + loz, oct, gain, lac) - lmid) * lamp
		k = 0
		while k < cvs.size():
			# d >= max(|dx|, |dz|): only carves the point may be inside need the exact distance
			if absf(x - cvs[k]) < cvs[k + 2] and absf(z - cvs[k + 1]) < cvs[k + 2]:
				var d := DMath.hypot(x - cvs[k], z - cvs[k + 1])
				if d < cvs[k + 2]:
					L = minf(L, -(1.0 - d / cvs[k + 2]) * cdep - cflo)
			k += 3
		k = 0
		while k < nk.size():
			var nv := 1.0 - Maps.seg_dist(x, z, nk[k], nk[k + 1], nk[k + 2], nk[k + 3]) / nk[k + 4]
			if nv * nland > L:
				L = nv * nland
			k += 9
		var ex := minf(minf(x - X0, X0 + W - x), minf(z - Z0, Z0 + H - z))
		L -= maxf(0.0, (efade - ex) / efade)
		return L

	var height := func(x: float, z: float) -> float:
		var L: float = land.call(x, z)
		if L < 0.0:
			return maxf(sea_floor, L * sea_slope - sea_drop)
		var kk := minf(1.0, L * rise)
		var h := base_h + minf(L, cap) * lift + (n2.fbm(x * hf, z * hf, oct, gain, lac) - hmid) * hamp * kk
		var k := 0
		while k < rg.size():
			# the segment's box bounds the distance from below (1 unit of slack covers rounding)
			var bx := maxf(maxf(rg[k + 6] - x, x - rg[k + 7]), maxf(rg[k + 8] - z, z - rg[k + 9]))
			if bx < rg[k + 4] + 1.0:
				var d := Maps.seg_dist(x, z, rg[k], rg[k + 1], rg[k + 2], rg[k + 3])
				if d < rg[k + 4]:
					h += rg[k + 5] * DMath.pow_(1.0 - d / rg[k + 4], rexp) * (rbase + rvar * n3.fbm(x * rf, z * rf, oct, gain, lac)) * kk
			k += 10
		return h

	hv.resize(VW * VH)
	for j in VH:
		for i in VW:
			hv[j * VW + i] = height.call(X0 + i * cell, Z0 + j * cell)

	# flatten zone pads
	var tpad: float = T.townPadExtra
	var bin: float = T.padBlendIn
	var bout: float = T.padBlendOut
	for zd: Array in zones:
		var r: float = BZ[zd[1]].r + (tpad if zd[1] == "town" else 0.0)
		var cx: float = zd[2]
		var cz: float = zd[3]
		var base: float = maxf(T.padMin, minf(T.padMax, height.call(cx, cz)))
		var reach := r + bout
		# only vertices with |dx| and |dz| below the reach can be within it
		var i0 := maxi(0, int(ceilf((cx - reach - X0) / cell)) - 1)
		var i1 := mini(VW - 1, int(floorf((cx + reach - X0) / cell)) + 1)
		var j0 := maxi(0, int(ceilf((cz - reach - Z0) / cell)) - 1)
		var j1 := mini(VH - 1, int(floorf((cz + reach - Z0) / cell)) + 1)
		for j in range(j0, j1 + 1):
			for i in range(i0, i1 + 1):
				var x := X0 + i * cell
				var z := Z0 + j * cell
				var d := DMath.hypot(x - cx, z - cz)
				if d < reach:
					var t := 1.0 - Maps.smooth(r - bin, r + bout, d)
					var k := j * VW + i
					hv[k] = hv[k] * (1.0 - t) + base * t

	_cut_coves(m, zones, BZ, T)
	_grids(m, T)
	_place_props(m, zones, BZ, T, seed)


## Coastal bases sit on a cove: an inlet cut from the sea toward the base (web buildMap).
func _cut_coves(m: Dictionary, zones: Array, BZ: Dictionary, T: Dictionary) -> void:
	coves = []
	if m.get("noWater", false):
		return
	var skip: Array = T.coveSkip.get(m.get("id", ""), [])
	var water: float = T.coveWater
	var R: float = T.coveR
	for zi in zones.size():
		var zd: Array = zones[zi]
		if zd.size() < 5 or not zd[4] or zd[1] == "airbase" or float(zi) in skip or zi in skip:
			continue
		var r: float = BZ[zd[1]].r
		var cx: float = zd[2]
		var cz: float = zd[3]
		var best_a := 0.0
		var best_d := INF
		var found := false
		for k in int(T.coveRays):
			var a: float = float(k) / T.coveRays * T.coveTurn
			var d: float = r + T.coveSearchFrom
			while d < r + T.coveSearchTo:
				if _hv_at(cx + DMath.cos_(a) * d, cz + DMath.sin_(a) * d) < water:
					if not found or d < best_d:
						found = true
						best_a = a
						best_d = d
					break
				d += T.coveStep
		if not found:
			continue
		var ux := DMath.cos_(best_a)
		var uz := DMath.sin_(best_a)
		var ax := 0.0
		var az := 0.0
		var bx := 0.0
		var bz := 0.0
		var best_land := -1e9
		var side: float = r + T.coveSide
		for tri: Array in [[side, T.coveBack], [-side, T.coveBack], [side, r * T.coveMidK], [-side, r * T.coveMidK], [0.0, r + T.coveHeadOut]]:
			var lat: float = tri[0]
			var ax0: float = tri[1]
			var hx := cx - uz * lat + ux * ax0
			var hz := cz + ux * lat + uz * ax0
			var d := 0.0
			while d < T.coveMaxLen and _hv_at(hx + ux * d, hz + uz * d) > water:
				d += T.coveStep
			if d >= T.coveMaxLen:
				continue
			var l := 0.0
			var t := 0.0
			while t <= d:
				l += maxf(0.0, _hv_at(hx + ux * t, hz + uz * t))
				t += T.coveStep
			if l > best_land:
				best_land = l
				ax = hx
				az = hz
				bx = hx + ux * (d + T.coveTail)
				bz = hz + uz * (d + T.coveTail)
		if best_land < 0.0:
			continue
		var blocked := false
		for o: Array in zones:
			if not is_same(o, zd) and Maps.seg_dist(o[2], o[3], ax, az, bx, bz) < BZ[o[1]].r + R + T.coveZoneClear:
				blocked = true
				break
		if blocked:
			continue
		for n: Dictionary in m.necks:
			if Maps.seg_dist(n.a[0], n.a[1], ax, az, bx, bz) < R + T.coveNeckClear \
					or Maps.seg_dist(n.b[0], n.b[1], ax, az, bx, bz) < R + T.coveNeckClear:
				blocked = true
				break
		if blocked:
			continue
		var mg: float = T.coveMargin
		var j0 := maxi(0, int(floorf((minf(az, bz) - R - mg - Z0) / cell)))
		var j1 := mini(GH, int(ceilf((maxf(az, bz) + R + mg - Z0) / cell)))
		var i0 := maxi(0, int(floorf((minf(ax, bx) - R - mg - X0) / cell)))
		var i1 := mini(GW, int(ceilf((maxf(ax, bx) + R + mg - X0) / cell)))
		for j in range(j0, j1 + 1):
			for i in range(i0, i1 + 1):
				var d := Maps.seg_dist(X0 + i * cell, Z0 + j * cell, ax, az, bx, bz)
				if d > R + T.coveEdgeOut:
					continue
				var t := Maps.smooth(R - T.coveEdgeIn, R + T.coveEdgeOut, d)
				var k := j * VW + i
				hv[k] = minf(hv[k], hv[k] * t - T.coveDepth * (1.0 - t))
		coves.append({"zone": zi, "ax": ax, "az": az, "bx": bx, "bz": bz, "ux": ux, "uz": uz, "R": R})


func _grids(m: Dictionary, T: Dictionary) -> void:
	land_grid.resize(GW * GH)
	water_grid.resize(GW * GH)
	var no_water: bool = m.get("noWater", false)
	var min_h: float = T.passMinH
	var max_avg: float = T.passMaxAvg
	var max_slope: float = T.passMaxSlope
	var wmax: float = T.waterMaxH
	var we: int = int(T.waterEdge)
	for j in GH:
		for i in GW:
			var a: float = hv[j * VW + i]
			var b: float = hv[j * VW + i + 1]
			var c: float = hv[(j + 1) * VW + i]
			var d: float = hv[(j + 1) * VW + i + 1]
			var mx := maxf(maxf(a, b), maxf(c, d))
			var mn := minf(minf(a, b), minf(c, d))
			var av := (a + b + c + d) / 4.0
			land_grid[j * GW + i] = 1 if (mn > min_h and av < max_avg and mx - mn < max_slope) else 0
			water_grid[j * GW + i] = 1 if (not no_water and mx < wmax and i > we - 1 and j > we - 1 and i < GW - we and j < GH - we) else 0


## Terrain features scattered across the island (web buildMap props). They block movement.
func _place_props(m: Dictionary, zones: Array, BZ: Dictionary, T: Dictionary, seed: int) -> void:
	props = []
	const Rng := preload("res://sim/rng.gd")
	var pr := Rng.new(seed ^ int(T.propSeedXor))
	var types: Array = T.propTypesMoon if m.get("palette", "") == "moon" else T.propTypes
	var count := int(DMath.round_js(T.propBase * W * H / (T.propRefW * T.propRefH)))
	var edge: float = T.propEdge
	var k := 0
	while k < count * T.propTriesPer and props.size() < count:
		k += 1
		var x := X0 + edge + pr.next() * (W - 2.0 * edge)
		var z := Z0 + edge + pr.next() * (H - 2.0 * edge)
		var h := _hv_at(x, z)
		if h < T.propMinH or h > T.propMaxH:
			continue
		var bad := false
		for d: Array in zones:
			if DMath.hypot(d[2] - x, d[3] - z) < BZ[d[1]].r + T.propZoneClear:
				bad = true
				break
		if bad:
			continue
		for p: Dictionary in props:
			if DMath.hypot(p.x - x, p.z - z) < T.propSpacing:
				bad = true
				break
		if bad:
			continue
		for n: Dictionary in m.necks:
			if Maps.seg_dist(x, z, n.a[0], n.a[1], n.b[0], n.b[1]) < T.propNeckClear:
				bad = true
				break
		if bad:
			continue
		var a := 0.0
		while a < T.propRingEnd:
			if _hv_at(x + DMath.cos_(a) * T.propRingR, z + DMath.sin_(a) * T.propRingR) < T.propRingMinH:
				bad = true
			a += T.propRingStep
		if bad:
			continue
		var type: String = types[props.size() % types.size()]
		var rot: float = pr.next() * T.propTurn
		var v := pr.next()
		var p := {"type": type, "x": x, "z": z, "rot": rot, "v": v, "h": h, "circles": []}
		var PR: Dictionary = T.propR
		if type == "wreck":
			var span: float = T.wreckSpan
			var t := -span
			while t <= span:
				p.circles.append({"x": x + DMath.cos_(rot) * t, "z": z + DMath.sin_(rot) * t, "r": T.wreckR})
				t += span
		else:
			p.circles.append({"x": x, "z": z, "r": PR.get(type, PR.other)})
		for c: Dictionary in p.circles:
			_block_circle(c.x, c.z, c.r, T.propCellPad)
		props.append(p)


func _block_circle(x: float, z: float, r: float, padr: float) -> void:
	for j in range(int(floorf((z - r - Z0) / cell)), int(floorf((z + r - Z0) / cell)) + 1):
		for i in range(int(floorf((x - r - X0) / cell)), int(floorf((x + r - X0) / cell)) + 1):
			if i < 0 or j < 0 or i >= GW or j >= GH:
				continue
			var cx := X0 + (i + 0.5) * cell
			var cz := Z0 + (j + 0.5) * cell
			if DMath.hypot(cx - x, cz - z) <= r + padr:
				land_grid[j * GW + i] = 0
