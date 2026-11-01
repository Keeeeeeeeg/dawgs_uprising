extends RefCounted
## Map definitions. Fixed maps come from data/maps.json (exported from the web game by
## tools/export_maps.js). Chaos Isles is rolled for every battle here, ported from the web SIM's
## genMap (chaos style), convertMap, scaleMap and makeChaosMap. Numbers come from data/mapgen.json
## and balance.json.
##
## A map is a Dictionary like the web one: W, H, ns, maxPlayers, blobs [{x,z,rx,rz}],
## necks [{a:[x,z], b:[x,z], w}], carves [{x,z,r}], ridges [{a,b,w,h}],
## zones [[name, type, x, z, port]], slots [zone index of each HQ start], mix, palette...

const DMath := preload("res://sim/dmath.gd")
const Rng := preload("res://sim/rng.gd")

## Loads data/maps.json (path given so tests can load other copies). "#hex" strings become exact doubles.
static func load_maps(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("Maps: cannot open %s" % path)
		return {}
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if not parsed is Dictionary:
		push_error("Maps: %s is not a JSON object" % path)
		return {}
	return _decode(parsed.get("maps", {}))


static func _decode(v: Variant) -> Variant:
	if v is String and (v as String).begins_with("#") and (v as String).length() == 17:
		var h := (v as String).substr(1)
		return DMath._f((h.substr(0, 8).hex_to_int() << 32) | h.substr(8, 8).hex_to_int())
	if v is Array:
		var out := []
		for x: Variant in v:
			out.append(_decode(x))
		return out
	if v is Dictionary:
		var o := {}
		for k: Variant in v:
			o[k] = _decode(v[k])
		return o
	return v


# ---------- geometry helpers (web: segDist, smooth, landRaw) ----------

static func seg_dist(px: float, pz: float, ax: float, az: float, bx: float, bz: float) -> float:
	var dx := bx - ax
	var dz := bz - az
	var t := ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz)
	if is_nan(t):
		return NAN # JS Math.max/min pass NaN through
	t = maxf(0.0, minf(1.0, t))
	return DMath.hypot(px - (ax + dx * t), pz - (az + dz * t))


static func smooth(e0: float, e1: float, x: float) -> float:
	var t := maxf(0.0, minf(1.0, (x - e0) / (e1 - e0)))
	return t * t * (3.0 - 2.0 * t)


## The island shape without noise (web landRaw, same rules as the terrain builder's land()).
static func land_raw(m: Dictionary, x: float, z: float, cv: Dictionary) -> float:
	var L := -2.0
	for b: Dictionary in m.blobs:
		var v := 1.0 - DMath.hypot((x - b.x) / b.rx, (z - b.z) / b.rz)
		if v > L:
			L = v
	for c: Dictionary in m.carves:
		var d := DMath.hypot(x - c.x, z - c.z)
		if d < c.r:
			L = minf(L, -(1.0 - d / c.r) * cv.carveDepth - cv.carveFloor)
	for n: Dictionary in m.necks:
		var nv: float = 1.0 - seg_dist(x, z, n.a[0], n.a[1], n.b[0], n.b[1]) / n.w
		if nv * cv.neckLand > L:
			L = nv * cv.neckLand
	var W: float = m.W
	var H: float = m.H
	var ex := minf(minf(x + W / 2.0, W / 2.0 - x), minf(z + H / 2.0, H / 2.0 - z))
	L -= maxf(0.0, (cv.edgeFade - ex) / cv.edgeFade)
	return L


## Metres past the ring to deep water, or INF (web coastDist). reach <= 0 means the default.
static func coast_dist(m: Dictionary, x: float, z: float, r: float, reach: float, mx: Dictionary, cv: Dictionary) -> float:
	if m.get("noWater", false):
		return INF
	var top: float = reach if reach > 0.0 else mx.portReachMax
	var d: float = mx.portReachMin
	while d <= top:
		for a in int(cv.coastRays):
			var t: float = float(a) / cv.coastRays * cv.turn
			if land_raw(m, x + DMath.cos_(t) * (r + d), z + DMath.sin_(t) * (r + d), cv) < mx.portWater:
				return d
		d += cv.coastStep
	return INF


## Counts of each base type (web baseMix).
static func base_mix(zones: Array) -> Dictionary:
	var c := {"hq": 0, "fortress": 0, "town": 0, "airbase": 0, "port": 0}
	for z: Array in zones:
		c[z[1]] = c.get(z[1], 0) + 1
		if z.size() > 4 and z[4] and z[1] in ["hq", "fortress", "town"]:
			c.port += 1
	return c


## Stable sort by a JS-style comparator (negative = a first). V8's sort is stable; Godot's isn't.
static func sort_stable(a: Array, cmp: Callable) -> Array:
	if a.size() < 2:
		return a.duplicate()
	var mid := a.size() / 2
	var l := sort_stable(a.slice(0, mid), cmp)
	var r := sort_stable(a.slice(mid), cmp)
	var out := []
	var i := 0
	var j := 0
	while i < l.size() and j < r.size():
		if cmp.call(r[j], l[i]) < 0:
			out.append(r[j])
			j += 1
		else:
			out.append(l[i])
			i += 1
	out.append_array(l.slice(i))
	out.append_array(r.slice(j))
	return out


# ---------- Chaos Isles (web makeChaosMap) ----------

## Rolls the Chaos Isles map for a battle seed. Same seed = same map as the web game.
static func make_chaos(seed_in: float, gen: Dictionary, balance: Dictionary) -> Dictionary:
	var C: Dictionary = gen.chaos
	var seed := int(floorf(absf(seed_in)))
	if seed == 0:
		seed = 1
	seed = seed % int(C.seedMod) + 1
	var tries := 0
	while true:
		var m := _gen_chaos(seed, gen)
		if m.zones.size() < C.minZones and tries < C.maxRetries:
			tries += 1
			seed = seed % int(C.retryMod) + int(C.retryStep)
			continue
		convert_map(m, gen, balance)
		scale_map(m, gen)
		return m
	return {}


static func _gen_chaos(seed: int, gen: Dictionary) -> Dictionary:
	var C: Dictionary = gen.chaos
	var S: Dictionary = gen.sites
	var rng := Rng.new(seed)
	var R := func(a: float, b: float) -> float: return a + rng.next() * (b - a)
	var W: float = C.W
	var H: float = C.H
	var hw := W / 2.0
	var hh := H / 2.0
	var blobs := []
	var necks := []
	var carves := []
	var ridges := []
	var neck := func(a: Dictionary, b: Dictionary) -> void:
		necks.append({"a": [a.x, a.z], "b": [b.x, b.z], "w": gen.neckWidth})
	# islands, spaced apart
	var n := int(DMath.round_js(R.call(C.islands[0], C.islands[1])))
	var isl := []
	var k := 0
	while k < C.islandTries and isl.size() < n:
		k += 1
		var c := {}
		c.x = R.call(-hw + C.edgeX, hw - C.edgeX)
		c.z = R.call(-hh + C.edgeZ, hh - C.edgeZ)
		c.rx = R.call(C.islandRx[0], C.islandRx[1])
		c.rz = R.call(C.islandRz[0], C.islandRz[1])
		var clash := false
		for q: Dictionary in isl:
			if DMath.hypot(q.x - c.x, q.z - c.z) < (maxf(q.rx, q.rz) + maxf(c.rx, c.rz)) * C.islandGap:
				clash = true
				break
		if not clash:
			isl.append(c)
	for c: Dictionary in isl:
		blobs.append(c)
		if rng.next() < C.lobeChance:
			var lobe := {}
			lobe.x = c.x + R.call(-C.lobeDx, C.lobeDx)
			lobe.z = c.z + R.call(-C.lobeDz, C.lobeDz)
			lobe.rx = c.rx * R.call(C.lobeScale[0], C.lobeScale[1])
			lobe.rz = c.rz * R.call(C.lobeScale[0], C.lobeScale[1])
			blobs.append(lobe)
	# join each island to its nearest already-joined one
	var done := [isl[0]]
	for c: Dictionary in isl.slice(1):
		var b: Dictionary = done[0]
		var bd := 1e9
		for d: Dictionary in done:
			var q := DMath.hypot(d.x - c.x, d.z - c.z)
			if q < bd:
				bd = q
				b = d
		neck.call(c, b)
		done.append(c)
	# a few extra causeways
	k = 0
	while k < DMath.round_js(n / C.extraNecksDiv):
		k += 1
		var a: Dictionary = isl[int(floorf(rng.next() * isl.size()))]
		var b = null
		var bd := 1e9
		for c: Dictionary in isl:
			if is_same(c, a):
				continue
			var q: float = DMath.hypot(a.x - c.x, a.z - c.z) * R.call(C.extraNeckJitter[0], C.extraNeckJitter[1])
			if q < bd:
				bd = q
				b = c
		if b != null:
			neck.call(a, b)
	# ridges and lakes. The web loops re-roll their limit on every pass, so do the same.
	k = 0
	while k < DMath.round_js(R.call(C.ridges[0], C.ridges[1])):
		k += 1
		var c: Dictionary = isl[int(floorf(rng.next() * isl.size()))]
		var x: float = c.x + R.call(-c.rx * C.ridgeSpread, c.rx * C.ridgeSpread)
		var z: float = c.z + R.call(-c.rz * C.ridgeSpread, c.rz * C.ridgeSpread)
		var ang: float = R.call(0.0, C.ridgeTurn)
		var L: float = R.call(C.ridgeLen[0], C.ridgeLen[1])
		var rg := {"a": [x, z], "b": [x + DMath.cos_(ang) * L, z + DMath.sin_(ang) * L]}
		rg.w = R.call(C.ridgeW[0], C.ridgeW[1])
		rg.h = R.call(C.ridgeH[0], C.ridgeH[1])
		ridges.append(rg)
	k = 0
	while k < DMath.round_js(R.call(C.lakes[0], C.lakes[1])):
		k += 1
		var c: Dictionary = isl[int(floorf(rng.next() * isl.size()))]
		var lake := {}
		lake.x = c.x + R.call(-c.rx * C.lakeSpread, c.rx * C.lakeSpread)
		lake.z = c.z + R.call(-c.rz * C.lakeSpread, c.rz * C.lakeSpread)
		lake.r = R.call(C.lakeR[0], C.lakeR[1])
		carves.append(lake)
	var m := {"blobs": blobs, "necks": necks, "carves": carves, "ridges": ridges}
	return _place_sites(m, rng, R, W, H, {
		"zones": C.zones, "spacing": C.spacing, "maxPlayers": C.maxPlayers,
		"palette": C.palettes[seed % C.palettes.size()]}, gen)


## The second half of the web genMap: base sites, HQ start slots, site kinds and names.
static func _place_sites(m: Dictionary, rng, R: Callable, W: float, H: float, o: Dictionary, gen: Dictionary) -> Dictionary:
	var S: Dictionary = gen.sites
	var hw := W / 2.0
	var hh := H / 2.0
	var cv: Dictionary = gen.convert
	var base := func(x: float, z: float) -> float:
		var L := -2.0
		for b: Dictionary in m.blobs:
			var v := 1.0 - DMath.hypot((x - b.x) / b.rx, (z - b.z) / b.rz)
			if v > L:
				L = v
		for c: Dictionary in m.carves:
			var d := DMath.hypot(x - c.x, z - c.z)
			if d < c.r:
				L = minf(L, -(1.0 - d / c.r) * cv.carveDepth - cv.carveFloor)
		return L
	var ok := func(x: float, z: float, mn: float) -> bool:
		if not (base.call(x, z) > mn):
			return false
		for g: Dictionary in m.ridges:
			if not (seg_dist(x, z, g.a[0], g.a[1], g.b[0], g.b[1]) > g.w + S.ridgeClear):
				return false
		for g: Dictionary in m.necks:
			if not (seg_dist(x, z, g.a[0], g.a[1], g.b[0], g.b[1]) > S.neckClear):
				return false
		return absf(x) < hw - S.edge and absf(z) < hh - S.edge
	var pts := []
	var want: int = o.get("zones", S.defaultZones)
	var spacing: float = o.get("spacing", S.defaultSpacing)
	var k := 0
	while k < S.tries and pts.size() < want:
		k += 1
		var x: float = R.call(-hw + S.edge, hw - S.edge)
		var z: float = R.call(-hh + S.edge, hh - S.edge)
		if not ok.call(x, z, S.landMin):
			continue
		var near := false
		for p: Dictionary in pts:
			if DMath.hypot(p.x - x, p.z - z) < spacing:
				near = true
				break
		if near:
			continue
		var pr: float = S.probe
		var around := int(ok.call(x + pr, z, S.probeLand)) + int(ok.call(x - pr, z, S.probeLand)) \
			+ int(ok.call(x, z + pr, S.probeLand)) + int(ok.call(x, z - pr, S.probeLand))
		if around < S.probeNeed:
			continue
		pts.append({"x": x, "z": z})
	# HQ slots: farthest-point picks, starting from the westernmost site
	pts = sort_stable(pts, func(a: Dictionary, b: Dictionary) -> float: return a.x - b.x)
	var slots := [0]
	var players: int = o.get("maxPlayers", S.defaultPlayers)
	while slots.size() < mini(players, pts.size()):
		var best := -1
		var bd := -1.0
		for i in pts.size():
			if i in slots:
				continue
			var md := 1e9
			for s: int in slots:
				md = minf(md, DMath.hypot(pts[i].x - pts[s].x, pts[i].z - pts[s].z))
			if md > bd:
				bd = md
				best = i
		slots.append(best)
	# the most central sites become strongholds, the rest a mix
	var others := []
	for i in pts.size():
		if not i in slots:
			others.append(i)
	others = sort_stable(others, func(a: int, b: int) -> float:
		return DMath.hypot(pts[a].x, pts[a].z) - DMath.hypot(pts[b].x, pts[b].z))
	var types := []
	types.resize(pts.size())
	for i: int in slots:
		types[i] = "hq"
	var strongholds: int = o.get("strongholds", S.defaultStrongholds)
	for kk in others.size():
		types[others[kk]] = "stronghold" if kk < strongholds else S.mix[kk % S.mix.size()]
	# names stitched from two halves, shuffled, never repeating
	var pool := []
	for a: String in S.nameA:
		for b: String in S.nameB:
			pool.append(a + b)
	var i2 := pool.size() - 1
	while i2 > 0:
		var j := int(floorf(rng.next() * (i2 + 1)))
		var t: Variant = pool[i2]
		pool[i2] = pool[j]
		pool[j] = t
		i2 -= 1
	var zones := []
	for i in pts.size():
		zones.append([pool[i % pool.size()], types[i], DMath.round_js(pts[i].x), DMath.round_js(pts[i].z)])
	m.merge({"id": "chaos", "name": "Chaos Isles", "W": W, "H": H, "ns": [2.0, 2.0],
		"maxPlayers": mini(players, slots.size()), "zones": zones, "slots": slots, "generated": true,
		"palette": o.get("palette", "earth"), "chaos": true, "large": true}, true)
	return m


# ---------- convertMap / scaleMap ----------

## Turns the old site kinds into Fortresses, Towns and Airbases and marks Ports (web convertMap,
## the path for generated maps; fixed maps arrive already converted in maps.json).
static func convert_map(m: Dictionary, gen: Dictionary, balance: Dictionary) -> void:
	var MX: Dictionary = balance.mapMix
	var cv: Dictionary = gen.convert
	var BZ: Dictionary = balance.zones
	var Z: Array = m.zones
	var slots: Array = m.slots
	var diag := DMath.hypot(m.W, m.H)
	var old := Z.map(func(z: Array) -> String: return z[1])
	var R0 := func(t: String) -> float: return BZ[t].r if BZ.has(t) else cv.defaultR
	var coast := []
	for i in Z.size():
		coast.append(coast_dist(m, Z[i][2], Z[i][3], R0.call("hq" if i in slots else "town"), 0.0, MX, cv))
	var ridge_clear := func(x: float, z: float) -> float:
		var a: float = cv.ridgeClearStart
		for g: Dictionary in m.ridges:
			a = minf(a, seg_dist(x, z, g.a[0], g.a[1], g.b[0], g.b[1]) - g.w)
		return a
	var free := []
	for i in Z.size():
		if not i in slots:
			free.append(i)
	var n := free.size()
	var type := []
	for i in Z.size():
		type.append("hq" if i in slots else null)
	var spread := func(i: int, set: Array) -> float:
		var d := 1e9
		for k: int in set:
			d = minf(d, DMath.hypot(Z[i][2] - Z[k][2], Z[i][3] - Z[k][3]))
		return minf(1.0, d / (diag * cv.spreadDiag))
	var pick := func(count: int, score: Callable) -> Array:
		var out := []
		for k in count:
			var b := -1
			var bs := -1e9
			for i: int in free:
				if type[i] != null or i in out:
					continue
				var s: float = score.call(i, out)
				if s > bs:
					bs = s
					b = i
			if b < 0:
				break
			out.append(b)
		return out
	# airbases: open, inland ground, spread apart (a site already called an airfield always is one)
	var n_air := maxi(int(MX.minAirbases), int(DMath.round_js(n * MX.airbase)))
	var air_score := func(i: int, out: Array) -> float:
		var s: float = (cv.airfieldBonus if (Z[i][0] as String).to_lower().contains("airfield") else 0.0)
		s += minf(1.0, ridge_clear.call(Z[i][2], Z[i][3]) / cv.ridgeNorm)
		s += minf(1.0, maxf(0.0, land_raw(m, Z[i][2], Z[i][3], cv)) / cv.landNorm) * cv.landWeight
		s -= cv.coastPenalty if coast[i] < INF else 0.0
		return s + cv.airSpread * spread.call(i, slots + out)
	for i: int in pick.call(n_air, air_score):
		type[i] = "airbase"
	# fortresses: walled sites first (strongholds, then outposts), spread across the map
	var n_fort := int(DMath.round_js(n * MX.fortress))
	var fort_score := func(i: int, out: Array) -> float:
		var s: float = cv.strongholdScore if old[i] == "stronghold" else (cv.outpostScore if old[i] == "outpost" else 0.0)
		return s + cv.fortSpread * spread.call(i, slots + out)
	for i: int in pick.call(n_fort, fort_score):
		type[i] = "fortress"
	for i: int in free:
		if type[i] == null:
			type[i] = "town"
	# Ports: minPorts of them outside the HQs, at least one Port Fortress and one Port Town
	if not m.get("noWater", false):
		var ports := func(t: String) -> Array:
			return free.filter(func(i: int) -> bool: return type[i] == t and coast[i] < INF)
		for reach: float in [MX.portFallbackReach, MX.portFallbackReach * cv.fallbackReachGrow]:
			var far := []
			for i in Z.size():
				far.append(INF if coast[i] < INF or i in slots else coast_dist(m, Z[i][2], Z[i][3], R0.call(type[i]), reach, MX, cv))
			var nearest := func(t: String) -> Variant:
				var c := free.filter(func(i: int) -> bool: return type[i] == t and coast[i] == INF and far[i] < INF)
				c = sort_stable(c, func(a: int, b: int) -> float: return far[a] - far[b])
				return c[0] if c.size() > 0 else null
			for t: String in ["town", "fortress"]:
				while ports.call("town").size() + ports.call("fortress").size() < MX.minPorts:
					var f: Variant = nearest.call(t)
					if f == null:
						break
					coast[f] = far[f]
			for want: String in ["fortress", "town"]:
				if ports.call(want).is_empty():
					var f: Variant = nearest.call(want)
					if f != null:
						coast[f] = far[f]
		for pair: Array in [["fortress", "town"], ["town", "fortress"]]:
			if not ports.call(pair[0]).is_empty():
				continue
			var c: Array = ports.call(pair[1])
			if c.size() > 1:
				for d: int in free:
					if type[d] == pair[0] and coast[d] == INF:
						type[c[0]] = pair[0]
						type[d] = pair[1]
						break
	var zs := []
	for i in Z.size():
		zs.append([Z[i][0], type[i], Z[i][2], Z[i][3], coast[i] < INF])
	m.zones = zs
	m.mix = base_mix(zs)


## Draws the battlefield MAP_SCALE times larger than it was laid out (web scaleMap).
static func scale_map(m: Dictionary, gen: Dictionary) -> void:
	if m.get("scaled", false):
		return
	m.scaled = true
	var S: float = gen.mapScale
	var step: float = gen.sizeStep
	m.W = DMath.round_js(m.W * S / step) * step
	m.H = DMath.round_js(m.H * S / step) * step
	for z: Array in m.zones:
		z[2] *= S
		z[3] *= S
	var seen := []
	for b: Dictionary in m.blobs:
		if _once(seen, b):
			b.x *= S; b.z *= S; b.rx *= S; b.rz *= S
	for c: Dictionary in m.carves:
		if _once(seen, c):
			c.x *= S; c.z *= S; c.r *= S
	for r: Dictionary in m.ridges + m.necks:
		if _once(seen, r):
			r.a = [r.a[0] * S, r.a[1] * S]
			r.b = [r.b[0] * S, r.b[1] * S]
			r.w *= S
	m.ns = [m.ns[0] * S, m.ns[1] * S]


## Features shared between maps (or listed twice) are scaled once, like the web's WeakSet.
static func _once(seen: Array, o: Dictionary) -> bool:
	for x: Dictionary in seen:
		if is_same(x, o):
			return false
	seen.append(o)
	return true


# ---------- start slots (web createGame: "assign HQ start slots") ----------

## Picks each army's HQ start and returns {slotOf, zonesFinal, NF, teamOf, mode}.
## opts: like the web createGame options (humans, ai, mode). rnd: the battle's Rng (Chaos Isles
## shuffles the starts with it). Unused HQ slots become neutral Fortresses.
static func battle_zones(m: Dictionary, opts: Dictionary, rnd, gen: Dictionary) -> Dictionary:
	var far: float = gen.slots.far
	var worst: float = gen.slots.teamWorst
	var max_p: int = int(m.maxPlayers)
	var humans: Array = opts.get("humans", [])
	if humans.is_empty():
		humans = [{"team": 1}]
	humans = humans.slice(0, max_p)
	var H := humans.size()
	var ai: Array = opts.get("ai", [{"p": 0, "team": 2}, {"p": 1, "team": 3}, {"p": 2, "team": 4}])
	ai = ai.slice(0, maxi(0, max_p - H))
	var NF := ai.size() + H
	var mode := "teams" if opts.get("mode", "") == "teams" or m.get("carrier", false) else "ffa"
	var team_of := []
	for i in H:
		team_of.append(humans[i].get("team", 1) if mode == "teams" else i)
	for i in ai.size():
		team_of.append(ai[i].get("team", 2) if mode == "teams" else H + i)
	var sp := []
	for i: Variant in m.slots:
		sp.append([float(m.zones[int(i)][2]), float(m.zones[int(i)][3])])
	var dist := func(a: Array, b: Array) -> float: return DMath.hypot(a[0] - b[0], a[1] - b[1])
	var slot_of := []
	slot_of.resize(NF)
	slot_of.fill(-1)
	var used := {}
	slot_of[0] = 0
	used[0] = true
	var order := range(1, NF)
	if mode == "teams":
		var teams := []
		for t: Variant in team_of:
			if not t in teams:
				teams.append(t)
		for t: Variant in teams:
			var members := order.filter(func(f: int) -> bool: return team_of[f] == t and slot_of[f] < 0)
			if members.is_empty():
				continue
			var anchor := 0 if t == team_of[0] else -1
			for f: int in members:
				var best := -1
				var bs := worst
				for k in sp.size():
					if used.has(k):
						continue
					var sc: float
					if anchor >= 0:
						sc = -dist.call(sp[k], sp[anchor])
					else:
						sc = far
						for g in NF:
							if slot_of[g] >= 0 and team_of[g] != t:
								sc = minf(sc, dist.call(sp[k], sp[slot_of[g]]))
					if sc > bs:
						bs = sc
						best = k
				slot_of[f] = best
				used[best] = true
				if anchor < 0:
					anchor = best
	else:
		for f: int in order:
			var best := -1
			var bs := -1.0
			for k in sp.size():
				if used.has(k):
					continue
				var md := far
				for g in NF:
					if slot_of[g] >= 0:
						md = minf(md, dist.call(sp[k], sp[slot_of[g]]))
				if md > bs:
					bs = md
					best = k
			slot_of[f] = best
			used[best] = true
	# Chaos Isles: throw the plan away and shuffle every army onto a random start
	if m.get("chaos", false):
		used.clear()
		var perm := range(sp.size())
		var i := perm.size() - 1
		while i > 0:
			var j := int(floorf(rnd.next() * (i + 1)))
			var tmp: int = perm[i]
			perm[i] = perm[j]
			perm[j] = tmp
			i -= 1
		for f in NF:
			slot_of[f] = perm[f]
			used[perm[f]] = true
	var zones_final := []
	for z: Array in m.zones:
		zones_final.append(z.duplicate())
	for k in m.slots.size():
		if not used.has(k):
			zones_final[int(m.slots[k])][1] = "fortress"
	return {"slotOf": slot_of, "zonesFinal": zones_final, "NF": NF, "teamOf": team_of, "mode": mode}
