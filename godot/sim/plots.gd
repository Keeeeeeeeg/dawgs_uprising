extends RefCounted
## Build plots: each base grows like a small settlement that follows the ground (web createGame,
## "build plots"). Airbases get a runway on the flattest open line, a taxiway, an apron and terminal
## stands; Towns and HQs run streets out through their gates; Fortresses get a gate road and a ring of
## bastions; Ports add quays along their cove or waterfront. Every plot is levelled into the ground.
## No randomness here, but the order things happen in matters (streets block later plots), so it
## follows the web code step by step. Numbers: data/mapgen.json "plots".

const DMath := preload("res://sim/dmath.gd")
const Maps := preload("res://sim/maps.gd")

var sim                       # sim/sim.gd
var t                         # sim/terrain.gd
var P: Dictionary             # mapgen.plots
var streets: Array = []       # web G.streets: {zone, pts [[x,z]...], w, quay?}
var air_corr: Array = []      # web G.airCorr: each airbase's runway frame (also zone.air)
var all_plots: Array = []
var _touched := {}            # cells to recheck after levelling (insertion-ordered set)
var _walk_cache := {}

const PORT_TYPES := ["hq", "fortress", "town"]


func _init(p_sim) -> void:
	sim = p_sim
	t = sim.terrain
	P = sim.data.mapgen.plots


func _angd(a: float, b: float) -> float:
	return absf(DMath.atan2_(DMath.sin_(a - b), DMath.cos_(a - b)))


func run() -> void:
	for c: Dictionary in t.coves:
		sim.zones[int(c.zone)].cove = c
	_airbases()
	_repass()
	var ZT: Dictionary = sim.tables.ztypes
	for z: Dictionary in sim.zones:
		_plots_for(z, ZT[z.type])
	# level the ground under every plot (a flat yard a little wider than the plate)
	for p: Dictionary in all_plots:
		var sm := 0.0
		var c := 0
		var b := 0.0
		while b < P.turn:
			sm += t.height_at(p.x + DMath.cos_(b) * P.plotLevelProbe, p.z + DMath.sin_(b) * P.plotLevelProbe)
			c += 1
			b += P.plotLevelStep
		var Hh := maxf(P.plotMinH, sm / c)
		var R: float = P.plotLevelR
		var inner: float = P.plotLevelInner
		var px: float = p.x
		var pz: float = p.z
		_level(px - R, pz - R, px + R, pz + R, func(x: float, zz: float) -> float:
			var d := DMath.hypot(x - px, zz - pz)
			return 0.0 if d > R else 1.0 - Maps.smooth(inner, R, d), Hh)
	_repass()
	for p: Dictionary in all_plots:
		p.y = t.height_at(p.x, p.z)


# ---------- ground levelling (web level / repass) ----------

## Blend heights toward Hh with weight w(x, z) in a box, and remember which cells to recheck.
func _level(x0: float, z0: float, x1: float, z1: float, w: Callable, Hh: float) -> void:
	var cell: float = t.cell
	for j in range(maxi(0, int(floorf((z0 - t.Z0) / cell))), mini(t.GH, int(ceilf((z1 - t.Z0) / cell))) + 1):
		for i in range(maxi(0, int(floorf((x0 - t.X0) / cell))), mini(t.GW, int(ceilf((x1 - t.X0) / cell))) + 1):
			var wt: float = w.call(t.X0 + i * cell, t.Z0 + j * cell)
			if wt <= 0.0:
				continue
			var k: int = j * t.VW + i
			t.hv[k] = t.hv[k] * (1.0 - wt) + Hh * wt
			for ab: Array in [[0, 0], [-1, 0], [0, -1], [-1, -1]]:
				_touched[(j + ab[1]) * t.GW + (i + ab[0])] = true


func _near_prop(x: float, z: float) -> bool:
	for q: Dictionary in t.props:
		for c: Dictionary in q.circles:
			if DMath.hypot(c.x - x, c.z - z) <= c.r + P.propPad:
				return true
	return false


func _repass() -> void:
	var T: Dictionary = sim.data.mapgen.terrain
	var GW: int = t.GW
	var VW: int = t.VW
	for k: int in _touched:
		if k < 0 or k >= GW * t.GH:
			continue
		var i := k % GW
		var j := (k - i) / GW
		var a: float = t.hv[j * VW + i]
		var b: float = t.hv[j * VW + i + 1]
		var c: float = t.hv[(j + 1) * VW + i]
		var d: float = t.hv[(j + 1) * VW + i + 1]
		var mx := maxf(maxf(a, b), maxf(c, d))
		var mn := minf(minf(a, b), minf(c, d))
		var av := (a + b + c + d) / 4.0
		var ok: bool = mn > T.passMinH and av < T.passMaxAvg and mx - mn < T.passMaxSlope
		if not ok:
			t.land_grid[k] = 0
		elif t.land_grid[k] == 0 and not _near_prop(t.X0 + (i + 0.5) * t.cell, t.Z0 + (j + 0.5) * t.cell):
			t.land_grid[k] = 1
		# walls (phase 4): wall cells stay blocked; sim.sync_cell(k) keeps the team grids in step
	_touched.clear()


# ---------- airbases: runway, taxiway, apron (web "airbases, laid out like an airport diagram") ----------

func _in_corr(x: float, z: float, pad: float) -> bool:
	for A: Dictionary in air_corr:
		var s: float = (x - A.cx) * A.ux + (z - A.cz) * A.uz
		var q: float = (x - A.cx) * A.nx + (z - A.cz) * A.nz
		if absf(s) <= A.L / 2.0 + P.corrEnd + pad and q >= P.corrQ0 - pad and q <= P.corrQ1 + pad:
			return true
	return false


func _airbases() -> void:
	var AB: Dictionary = sim.tables.ztypes.airbase
	var TAU: float = P.turn
	var off: float = P.runwayOffset
	for z: Dictionary in sim.zones:
		if z.type != "airbase":
			continue
		var L: float = AB.runway
		var half: float = L / 2.0 + P.runwayEndPad
		var to_c := DMath.atan2_(-z.z, -z.x)
		var best := to_c
		var bs: float = P.far
		for k in int(P.runwayDirs):
			var ang: float = float(k) / P.runwayDirs * TAU
			var ux := DMath.cos_(ang)
			var uz := DMath.sin_(ang)
			var nx := -uz
			var nz := ux
			var cx: float = z.x - nx * off
			var cz: float = z.z - nz * off
			var sc: float = _angd(ang, to_c) * P.runwayAngleWeight
			var tt := -half
			while tt <= half:
				for q: float in P.runwayProbeQ:
					var x := cx + ux * tt + nx * q
					var zz := cz + uz * tt + nz * q
					var e: float = P.runwayEdge
					if x < t.X0 + e or x > t.X0 + t.W - e or zz < t.Z0 + e or zz > t.Z0 + t.H - e:
						sc += P.runwayOffMapPenalty
						continue
					var h: float = t.height_at(x, zz)
					sc += absf(h - z.y) * P.runwayHeightWeight + (P.runwayLowPenalty if h < P.runwayLowH else 0.0) \
						+ (0.0 if t.passable(x, zz) else P.runwayBlockedPenalty)
					for o: Dictionary in sim.zones:
						if not is_same(o, z) and DMath.hypot(o.x - x, o.z - zz) < o.r + P.runwayZoneClear:
							sc += P.runwayZonePenalty
				tt += P.runwayProbeStep
			if sc < bs:
				bs = sc
				best = ang
		var ang := best
		var ux := DMath.cos_(ang)
		var uz := DMath.sin_(ang)
		var nx := -uz
		var nz := ux
		var cx: float = z.x - nx * off
		var cz: float = z.z - nz * off
		var terms := []
		var nt: int = int(AB.terminals)
		for k in nt:
			var o: float = (k - (nt - 1) / 2.0) * P.terminalSpacing
			terms.append({"x": cx + nx * P.terminalQ + ux * o, "z": cz + nz * P.terminalQ + uz * o, "u": null})
		z.air = {"ang": ang, "ux": ux, "uz": uz, "nx": nx, "nz": nz, "L": L, "cx": cx, "cz": cz,
			"a": {"x": cx - ux * L / 2.0, "z": cz - uz * L / 2.0}, "b": {"x": cx + ux * L / 2.0, "z": cz + uz * L / 2.0},
			"tx": cx + nx * P.taxiQ, "tz": cz + nz * P.taxiQ, "terms": terms, "rwyT": 0}
		air_corr.append(z.air)
		# level the strip (full inside, easing out past the perimeter)
		var ext: float = half + P.runwayLevelExt
		var box: float = P.runwayLevelBox
		var q0: float = P.corrQ0
		var q1: float = P.corrQ1
		var endp: float = P.runwayLevelEndPad
		var q0p: float = P.runwayLevelQ0Pad
		var q1p: float = P.runwayLevelQ1Pad
		var fade: float = P.runwayLevelFade
		_level(cx - ext - box, cz - ext - box, cx + ext + box, cz + ext + box, func(x: float, zz: float) -> float:
			var s := absf((x - cx) * ux + (zz - cz) * uz)
			var q := (x - cx) * nx + (zz - cz) * nz
			var ds := maxf(0.0, s - half - endp)
			var dq := maxf(maxf(0.0, q0 - q0p - q), q - q1 - q1p)
			var d := DMath.hypot(ds, dq)
			return 0.0 if d >= fade else 1.0 - Maps.smooth(0.0, fade, d), z.y)


# ---------- streets (web walkStreet, streetQuality, addStreet, lineStreet) ----------

func _street_dist(s: Dictionary, x: float, z: float) -> float:
	var d: float = P.far
	var pts: Array = s.pts
	for i in range(1, pts.size()):
		d = minf(d, Maps.seg_dist(x, z, pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]))
	return d


func _pad_fits(x: float, z: float, zone: Dictionary) -> bool:
	if not t.passable(x, z) or t.height_at(x, z) < P.padMinH:
		return false
	var lo: float = P.far
	var hi: float = P.worst
	var b := 0.0
	while b < P.turn:
		var px: float = x + DMath.cos_(b) * P.padProbeR
		var pz: float = z + DMath.sin_(b) * P.padProbeR
		if not t.passable(px, pz):
			return false
		var h: float = t.height_at(px, pz)
		if h < lo:
			lo = h
		if h > hi:
			hi = h
		b += P.padStep
	if hi - lo > P.padMaxRise:
		return false
	for p: Dictionary in all_plots:
		if absf(p.x - x) < P.padSpacing and DMath.hypot(p.x - x, p.z - z) < P.padSpacing:
			return false
	for o: Dictionary in sim.zones:
		if DMath.hypot(o.x - x, o.z - z) < o.r + (P.padOwnZoneClear if is_same(o, zone) else P.padZoneClear):
			return false
	for s: Dictionary in streets:
		if _street_dist(s, x, z) < s.w / 2.0 + P.padStreetClear:
			return false
	if _in_corr(x, z, P.padCorrClear):
		return false
	return true


## Walks a street outward: each step picks the bend that keeps it level and on dry, open ground.
func _walk_street(zone: Dictionary, x: float, z: float, a: float, length: float, score: Variant) -> Array:
	var pts := [[x, z]]
	var L := 0.0
	var step: float = P.streetStep
	while L < length:
		var best = null
		var bs: float = P.far
		var h0: float = t.height_at(x, z)
		for da: float in P.streetBends:
			var na := a + da
			var nx := x + DMath.cos_(na) * step
			var nz := z + DMath.sin_(na) * step
			if not t.passable(nx, nz):
				continue
			var h: float = t.height_at(nx, nz)
			if h < P.streetMinH:
				continue
			var clash := false
			for o: Dictionary in sim.zones:
				if not is_same(o, zone) and DMath.hypot(o.x - nx, o.z - nz) < o.r + P.streetZoneClear:
					clash = true
					break
			if clash:
				continue
			if DMath.hypot(nx - zone.x, nz - zone.z) < zone.r + P.streetOwnZoneClear or _in_corr(nx, nz, P.streetCorrClear):
				continue
			var sc: float = absf(h - h0) * P.streetRiseWeight + absf(da) * P.streetBendWeight \
				+ ((score as Callable).call(nx, nz, na) if score != null else 0.0)
			for sd: float in [P.quarterTurn, -P.quarterTurn]:
				if not t.passable(nx + DMath.cos_(na + sd) * P.streetSideProbe, nz + DMath.sin_(na + sd) * P.streetSideProbe):
					sc += P.streetSidePenalty
			if sc < bs:
				bs = sc
				best = [na, nx, nz]
		if best == null:
			break
		a = best[0]
		x = best[1]
		z = best[2]
		pts.append([x, z])
		L += step
	return pts


func _street_quality(zone: Dictionary, a: float, length: float) -> float:
	var key := "%d:%d:%s" % [zone.id, int(DMath.round_js(a * P.qualityAngleKey)), length]
	if _walk_cache.has(key):
		return _walk_cache[key]
	var out: float = zone.r + P.streetStartOut
	var p := _walk_street(zone, zone.x + DMath.cos_(a) * out, zone.z + DMath.sin_(a) * out, a, length, null)
	var open := 0
	for xz: Array in p:
		for sd: float in [P.quarterTurn, -P.quarterTurn]:
			if t.passable(xz[0] + DMath.cos_(a + sd) * P.qualitySideProbe, xz[1] + DMath.sin_(a + sd) * P.qualitySideProbe):
				open += 1
	var q: float = (p.size() - 1) * P.streetStep / length + float(open) / (2 * maxi(1, p.size())) * P.qualityOpenWeight
	_walk_cache[key] = q
	return q


func _add_street(zone: Dictionary, a: float, length: float, w: float, score: Variant, from: Variant) -> Variant:
	var out: float = zone.r + P.streetStartOut
	var sx: float = from[0] if from != null else zone.x + DMath.cos_(a) * out
	var sz: float = from[1] if from != null else zone.z + DMath.sin_(a) * out
	var pts := _walk_street(zone, sx, sz, a, length, score)
	if pts.size() < P.streetMinPts:
		return null
	if from == null:   # run in through the gate
		pts.push_front([zone.x + DMath.cos_(a) * zone.r * P.streetGateIn, zone.z + DMath.sin_(a) * zone.r * P.streetGateIn])
	var s := {"zone": zone.id, "pts": pts, "w": w}
	streets.append(s)
	return s


## Plot spots either side of a street, every ~7 m (sides: +1 left, -1 right). Like the web
## `o.start||3`, a start of 0 means the default.
func _line_street(s: Dictionary, out: Array, o: Dictionary = {}) -> void:
	var acc: float = o.get("start", 0.0)
	if acc == 0.0:
		acc = P.lineStart
	var every: float = o.get("every", P.lineEvery)
	var pts: Array = s.pts
	for i in range(1, pts.size()):
		var x0: float = pts[i - 1][0]
		var z0: float = pts[i - 1][1]
		var x1: float = pts[i][0]
		var z1: float = pts[i][1]
		acc += DMath.hypot(x1 - x0, z1 - z0)
		if acc < every:
			continue
		acc = 0.0
		var dir := DMath.atan2_(z1 - z0, x1 - x0)
		for sd: float in o.get("sides", [1.0, -1.0]):
			var na: float = dir + sd * P.quarterTurn
			var off: float = o.get("off", P.lineOffset)
			out.append({"x": x1 + DMath.cos_(na) * off, "z": z1 + DMath.sin_(na) * off, "ang": na, "tag": o.get("tag", "street")})


func _ring_spots(zone: Dictionary, out: Array, radii: Array, n: int, tag: String, skip: Variant = null) -> void:
	for rr: float in radii:
		for k in n:
			var a: float = zone.gate + (k + 0.5) / n * P.turn + fmod(rr, 2.0) * P.ringOddShift
			if skip != null and (skip as Callable).call(a):
				continue
			out.append({"x": zone.x + DMath.cos_(a) * rr, "z": zone.z + DMath.sin_(a) * rr, "ang": a, "tag": tag})


## Best rotation for a set of gate directions, judged by how far and how openly streets can run.
func _pick_gate(zone: Dictionary, offs: Array, length: float, bias: Variant) -> float:
	var best := 0.0
	var bs: float = P.worst
	for k in int(P.gateDirs):
		var g: float = float(k) / P.gateDirs * P.turn
		var q := 0.0
		for i in offs.size():
			q += _street_quality(zone, g + offs[i], length) * (P.gateFirstWeight if i == 0 else 1.0)
		if bias != null:
			q += (bias as Callable).call(g)
		if q > bs:
			bs = q
			best = g
	return best


func _water_dir(zone: Dictionary) -> Variant:
	var best = null
	var bd: float = P.far
	for k in int(P.waterDirs):
		var a: float = float(k) / P.waterDirs * P.turn
		var d: float = zone.r + P.waterFrom
		while d < zone.r + P.waterTo:
			if t.passable(zone.x + DMath.cos_(a) * d, zone.z + DMath.sin_(a) * d, t.water_grid):
				if d < bd:
					bd = d
					best = a
				break
			d += P.waterStep
	return best


## A quay down each side of the base's cove, running out toward the sea at a steady height.
func _cove_quays(z: Dictionary, out: Array, length: float) -> void:
	var c: Dictionary = z.cove
	var px: float = -c.uz
	var pz: float = c.ux
	for sd: float in [1.0, -1.0]:
		var sx := 0.0
		var sz := 0.0
		var ok := false
		for off: float in P.quayOffsets:
			sx = c.ax + px * sd * (c.R + off) - c.ux * P.quayBack
			sz = c.az + pz * sd * (c.R + off) - c.uz * P.quayBack
			if t.passable(sx, sz) and not _in_corr(sx, sz, P.streetCorrClear):
				ok = true
				break
		if not ok:
			continue
		for dir: float in [1.0, -1.0]:
			var qh: float = P.quayHeight
			var qw: float = P.quayHeightWeight
			var q: Variant = _add_street(z, DMath.atan2_(c.uz * dir, c.ux * dir), length if dir > 0.0 else length * P.quayInlandK, P.quayWidth,
				func(x: float, zz: float, _na: float) -> float: return absf(t.height_at(x, zz) - qh) * qw, [sx, sz])
			if q != null:
				q.quay = true
				_line_street(q, out, {"start": P.quayStart, "tag": "quay", "sides": [sd * dir]})


func _layout(z: Dictionary) -> Array:
	var out := []
	var T: String = z.type
	var wa: Variant = null
	if z.coastal and T in PORT_TYPES:
		wa = DMath.atan2_(z.cove.uz, z.cove.ux) if z.has("cove") else _water_dir(z)
	z.gate = 0.0
	if T == "airbase":
		var A: Dictionary = z.air
		z.gate = DMath.atan2_(A.nz, A.nx)
		var q1: float = P.corrQ1
		var q0: float = P.corrQ0
		for o: float in P.apronOffsets:
			out.append({"x": A.cx + A.nx * (q1 + P.apronQOut) + A.ux * o, "z": A.cz + A.nz * (q1 + P.apronQOut) + A.uz * o, "ang": z.gate, "tag": "apron"})
		for e: float in [1.0, -1.0]:
			for q: float in P.endQ:
				out.append({"x": A.cx + A.ux * e * (A.L / 2.0 + P.endOut) + A.nx * q, "z": A.cz + A.uz * e * (A.L / 2.0 + P.endOut) + A.nz * q,
					"ang": DMath.atan2_(A.uz * e, A.ux * e), "tag": "end"})
		for o: float in P.farOffsets:
			out.append({"x": A.cx + A.nx * (q0 - P.farQIn) + A.ux * o, "z": A.cz + A.nz * (q0 - P.farQIn) + A.uz * o, "ang": z.gate + PI, "tag": "far"})
		var s: Variant = _add_street(z, z.gate, P.airStreetLen, P.airStreetW, null,
			[A.cx + A.nx * (q1 + P.airStreetQ), A.cz + A.nz * (q1 + P.airStreetQ)])
		if s != null:
			s.pts.push_front([A.cx + A.nx * P.airStreetHeadQ, A.cz + A.nz * P.airStreetHeadQ])
			_line_street(s, out, {"start": P.airLineStart})
	elif T == "fortress":
		var fb: float = P.fortGateBias
		var wv: float = wa if wa != null else 0.0
		z.gate = _pick_gate(z, [0.0], P.fortGateLen, (func(g: float) -> float: return -_angd(g, wv) * fb) if wa != null else null)
		var s: Variant = _add_street(z, z.gate, P.fortStreetLen, P.fortStreetW, null, null)
		if s != null:
			_line_street(s, out, {"start": P.fortLineStart})
		if z.has("cove"):
			_cove_quays(z, out, P.fortQuayLen)
		elif wa != null:
			var q: Variant = _add_street(z, wa + P.fortWaterTurn, P.fortQuayLen, P.fortStreetW, null,
				[z.x + DMath.cos_(wa) * (z.r + P.fortWaterOut), z.z + DMath.sin_(wa) * (z.r + P.fortWaterOut)])
			if q != null:
				_line_street(q, out, {"tag": "quay"})
		var rings := []
		for r: float in P.fortRings:
			rings.append(z.r + r)
		var gclear: float = P.fortRingGateClear
		var gate: float = z.gate
		_ring_spots(z, out, rings, int(P.fortRingN), "ring", func(a: float) -> bool: return _angd(a, gate) < gclear)
	else:
		var hq := T == "hq"
		var offs: Array = P.hqOffsets if hq else P.townOffsets
		var length: float = P.hqLen if hq else P.townLen
		var wb: float = P.gateWaterBias
		var wv: float = wa if wa != null else 0.0
		z.gate = _pick_gate(z, offs, length, (func(g: float) -> float: return -_angd(g, wv + PI) * wb) if wa != null else null)
		var ranked := []
		for o: float in offs:
			ranked.append(z.gate + o)
		ranked = Maps.sort_stable(ranked, func(a: float, b: float) -> float: return _street_quality(z, b, length) - _street_quality(z, a, length))
		if z.has("cove"):
			_cove_quays(z, out, P.hqQuayLen if hq else P.townQuayLen)
		elif wa != null:
			var sx: float = z.x + DMath.cos_(wa) * (z.r + P.shoreOut)
			var sz: float = z.z + DMath.sin_(wa) * (z.r + P.shoreOut)
			var sh: float = P.shoreHeight
			var qw: float = P.quayHeightWeight
			for sd: float in [P.quarterTurn, -P.quarterTurn]:
				var q: Variant = _add_street(z, wa + sd, P.hqQuayLen if hq else P.townQuayLen, P.quayWidth,
					func(x: float, zz: float, _na: float) -> float: return absf(t.height_at(x, zz) - sh) * qw, [sx, sz])
				if q != null:
					_line_street(q, out, {"start": P.shoreLineStart, "tag": "quay"})
		for i in ranked.size():
			var s: Variant = _add_street(z, ranked[i], length if i == 0 else length * P.sideStreetK, P.mainStreetW if i == 0 else P.sideStreetW, null, null)
			if s != null:
				_line_street(s, out, {"start": P.mainLineStart if i == 0 else P.sideLineStart})
		var rings := []
		for r: float in P.townRings:
			rings.append(z.r + r)
		_ring_spots(z, out, rings, int(P.hqRingN if hq else P.townRingN), "ring")
	var fb_rings := []
	for r: float in P.fallbackRings:
		fb_rings.append(z.r + r)
	_ring_spots(z, out, fb_rings, int(P.fallbackRingN), "fallback")
	return out


# ---------- plots per base and their kinds ----------

func _plots_for(z: Dictionary, ZT: Dictionary) -> void:
	var want: Dictionary = ZT.slots.duplicate()
	if z.coastal and z.type == "fortress":
		want.fort += sim.balance.port.fortressFortSlots   # Port Fortress: coastal defences
	var n: int = int(want.mil + want.eco + want.fort)
	var plots := []
	z.budget = n
	var reach: float = sim.balance.mapMix.portFallbackReach + P.waterNearPad if z.coastal else P.waterNearInland
	for c: Dictionary in _layout(z):
		if plots.size() >= n:
			break
		if not _pad_fits(c.x, c.z, z):
			continue
		var pl := {"i": plots.size(), "x": c.x, "z": c.z, "y": 0.0, "ang": c.ang, "fac": null, "tag": c.tag}
		var wc: int = sim.pathing.nearest_pass_cell(t.cell_of(c.x, c.z), t.water_grid)
		if wc >= 0:
			var w: Array = sim.pathing.cell_center(wc)
			if DMath.hypot(w[0] - c.x, w[1] - c.z) < reach:
				pl.water = {"x": w[0], "z": w[1]}
		plots.append(pl)
		all_plots.append(pl)
	# plot kinds: defences on the outskirts, economy nearest the centre, military the rest
	var have := plots.size()
	var kinds := ["fort", "mil", "eco"]
	var share := {}
	var left := have
	for k: String in kinds:
		share[k] = int(floorf(want[k] * have / float(n)))
		left -= share[k]
	var order := Maps.sort_stable(kinds, func(a: String, b: String) -> float:
		return (want[b] * have / float(n) - share[b]) - (want[a] * have / float(n) - share[a]))
	for k: String in order:
		if left > 0:
			share[k] += 1
			left -= 1
	var free := plots.duplicate()
	var dc := func(p: Dictionary) -> float: return DMath.hypot(p.x - z.x, p.z - z.z)
	var has_water := false
	for pl: Dictionary in plots:
		if pl.has("water"):
			has_water = true
			break
	z.port = z.type in PORT_TYPES and z.coastal and has_water
	if z.port and share.mil > 0:
		var wet := free.filter(func(p: Dictionary) -> bool: return p.has("water"))
		wet = Maps.sort_stable(wet, func(a: Dictionary, b: Dictionary) -> float:
			return DMath.hypot(a.water.x - a.x, a.water.z - a.z) - DMath.hypot(b.water.x - b.x, b.water.z - b.z))
		var w: Dictionary = wet[0]
		w.kind = "mil"
		free.erase(w)
		share.mil -= 1
	var max_d := 1.0
	for p: Dictionary in free:
		max_d = maxf(max_d, dc.call(p))
	var chosen := []
	for k in share.fort:
		var best = null
		var bs: float = P.worst
		for p: Dictionary in free:
			var a := DMath.atan2_(p.z - z.z, p.x - z.x)
			var sep: float = P.turn
			for q: Dictionary in chosen:
				sep = minf(sep, _angd(a, DMath.atan2_(q.z - z.z, q.x - z.x)))
			var s: float = dc.call(p) / max_d * P.fortFarWeight + (sep if chosen.size() > 0 else 0.0) \
				+ (P.fortEdgeBonus if p.tag == "end" or p.tag == "ring" else 0.0)
			if s > bs:
				bs = s
				best = p
		if best == null:
			break
		best.kind = "fort"
		chosen.append(best)
		free.erase(best)
	free = Maps.sort_stable(free, func(a: Dictionary, b: Dictionary) -> float: return dc.call(a) - dc.call(b))
	var k2 := 0
	while k2 < share.eco and free.size() > 0:
		var p: Dictionary = free.pop_front()
		p.kind = "eco"
		k2 += 1
	for p: Dictionary in free:
		p.kind = "mil"
	z.slots = {"mil": 0, "eco": 0, "fort": 0}
	for pl: Dictionary in plots:
		z.slots[pl.kind] += 1
	z.spots = plots   # buildings are placed freely now; these laid-out spots are suggestions (and the AI's choices)
	z.plots = []
