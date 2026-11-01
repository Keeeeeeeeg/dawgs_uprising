extends Node
## Headless checks. Run either way:
##   godot --headless --path godot res://tests/run_tests.tscn
##   or open tests/run_tests.tscn in the editor and press F6.
## Prints one line per check and "TESTS PASSED n/n" or "TESTS FAILED".
## Headless: exits with code 0 or 1. From the editor: stays open and shows every line in the window
## (quitting at once can cut off the editor's Output panel), close it when done.

const SIM_DIR := "res://sim"
const SimCore := preload("res://sim/sim.gd")
const Rng := preload("res://sim/rng.gd")
const DMath := preload("res://sim/dmath.gd")
const Maps := preload("res://sim/maps.gd")
const Terrain := preload("res://sim/terrain.gd")
const Pathing := preload("res://sim/pathing.gd")
const Spatial := preload("res://sim/spatial.gd")
const Tables := preload("res://sim/tables.gd")
const GOLDEN := "res://tests/golden" # recorded from the web SIM by tools/web_trace.js
const CHUNK := 0.25 # matches the web harness: G.update() is stepped in 0.25 s chunks
const SECONDS := 30.0
const UNIT_FIELDS := ["name", "cost", "hp", "speed", "range", "dmg", "rof", "acc", "weapon", "armor"]

var _passed := 0
var _failed := 0
var _lines: PackedStringArray = []


func _ready() -> void:
	_guard("balance", _check_balance)
	_guard("sim_steps", _check_sim_steps)
	_guard("sim_is_pure", _check_sim_is_pure)
	_guard("rng_matches_web", _check_rng_matches_web)
	_guard("dmath_matches_v8", _check_dmath_matches_v8)
	_guard("maps", _check_maps)
	_guard("terrain", _check_terrain)
	_guard("pathing", _check_pathing)
	_guard("spatial", _check_spatial)
	_guard("tables", _check_tables)
	_guard("setup", _check_setup)
	var total := _passed + _failed
	var summary := "TESTS PASSED %d/%d" % [_passed, total] if _failed == 0 else "TESTS FAILED %d of %d" % [_failed, total]
	print(summary)
	_lines.insert(0, summary + "\n")
	if DisplayServer.get_name() == "headless":
		get_tree().quit(0 if _failed == 0 else 1)
	else:
		_show(_lines, _failed == 0)


## Runs one check; if it crashes (script error) before reaching its end, that is a failure.
func _guard(name: String, check: Callable) -> void:
	var finished: Variant = check.call()
	if finished != true:
		_ok(false, "check '%s' crashed before finishing (see the error above)" % name)


func _ok(cond: bool, what: String) -> void:
	var line := ("  ok   " if cond else "  FAIL ") + what
	_lines.append(line)
	if cond:
		_passed += 1
		print(line)
	else:
		_failed += 1
		printerr(line)


## Editor runs: put the results in the window so nothing depends on the Output panel.
func _show(lines: PackedStringArray, passed: bool) -> void:
	var text := RichTextLabel.new()
	text.set_anchors_preset(Control.PRESET_FULL_RECT)
	text.selection_enabled = true
	text.add_theme_color_override("default_color", Color.PALE_GREEN if passed else Color.SALMON)
	text.text = "\n".join(lines) + "\n\n(Select and Ctrl+C to copy. Close this window when done.)"
	var layer := CanvasLayer.new()
	layer.add_child(text)
	add_child(layer)


func _check_balance() -> bool:
	var b: Dictionary = Balance.data
	_ok(not b.is_empty(), "balance.json loads")
	for key in ["engine", "units", "weapons", "walls", "zones", "economy", "combat", "ai", "campaign", "carrier", "manning"]:
		_ok(b.has(key), "balance has '%s'" % key)
	var units: Dictionary = b.get("units", {})
	_ok(units.size() > 10, "balance has %d unit types" % units.size())
	var missing: Array[String] = []
	for k: String in units:
		for f: String in UNIT_FIELDS:
			if not (units[k] as Dictionary).has(f):
				missing.append("%s.%s" % [k, f])
	_ok(missing.is_empty(), "every unit has the core stats %s" % ("" if missing.is_empty() else str(missing)))
	_ok(Balance.value("units.rifle.hp") == 45.0, "dotted lookup units.rifle.hp = 45 (web v22.5)")
	return true


func _run_sim() -> SimCore:
	var sim := SimCore.new({"balance": Balance.data}, {"seed": 7})
	var t := 0.0
	while t < SECONDS:
		sim.update(CHUNK)
		t += CHUNK
	return sim


func _check_sim_steps() -> bool:
	var a := _run_sim()
	var b := _run_sim()
	var step: float = Balance.value("engine.step")
	_ok(not a.over, "sim starts and runs")
	_ok(absf(a.ticks - SECONDS / step) <= 1.0, "%.0f s of play = %d ticks at %.4f s" % [SECONDS, a.ticks, step])
	_ok(a.state_hash() == b.state_hash(), "two runs, same seed, same state_hash")
	var capped := SimCore.new({"balance": Balance.data}, {"seed": 7})
	capped.update(10.0)
	var max_frame: float = Balance.value("engine.maxFrame")
	_ok(capped.time <= max_frame + 1e-9, "one long frame is capped at maxFrame (%.2f s)" % capped.time)
	return true


## The SIM must stay free of nodes so it can run headless and in lockstep.
func _check_sim_is_pure() -> bool:
	var dir := DirAccess.open(SIM_DIR)
	_ok(dir != null, "sim/ folder exists")
	if dir == null:
		return true
	for file in dir.get_files():
		if not file.ends_with(".gd"):
			continue
		var script: Script = load(SIM_DIR.path_join(file))
		var base := script.get_instance_base_type()
		_ok(not ClassDB.is_parent_class(base, "Node"), "sim/%s is not a Node (%s)" % [file, base])
		var src := FileAccess.get_file_as_string(SIM_DIR.path_join(file))
		var banned := ["randf(", "randi(", "Balance.", "get_tree(", "Input.", "Vector2", "Vector3"]
		var found := banned.filter(func(s: String) -> bool: return src.contains(s))
		_ok(found.is_empty(), "sim/%s uses no globals, unseeded randomness or 32-bit vectors %s" % [file, "" if found.is_empty() else str(found)])
	return true


## sim/rng.gd must give exactly the numbers the web game's mulberry32 gives (tests/golden/rng.json).
func _check_rng_matches_web() -> bool:
	var golden := Balance.load_file(GOLDEN.path_join("rng.json"))
	var seqs: Dictionary = golden.get("mulberry32", {})
	_ok(not seqs.is_empty(), "golden rng.json loads (web v%s)" % golden.get("web", "?"))
	for key: String in seqs:
		var rng := Rng.new(int(key))
		var bad := -1
		var want: Array = seqs[key]
		for i in want.size():
			# every value is k / 2^32, so compare the integer k (immune to JSON float rounding)
			if rng.next_u32() != roundi(float(want[i]) * Rng.TWO32):
				bad = i
				break
		_ok(bad == -1, "rng seed %s matches web for %d values%s" % [key, want.size(), "" if bad == -1 else " (differs at %d)" % bad])
	return true


## sim/dmath.gd must reproduce V8's Math functions bit for bit (tests/golden/math.json, from tools/web_math.js).
func _check_dmath_matches_v8() -> bool:
	var golden := Balance.load_file(GOLDEN.path_join("math.json"))
	var cases: Dictionary = golden.get("cases", {})
	_ok(not cases.is_empty(), "golden math.json loads (V8 %s)" % golden.get("v8", "?"))
	var fns := {
		"sin": func(a: Array) -> float: return DMath.sin_(a[0]),
		"cos": func(a: Array) -> float: return DMath.cos_(a[0]),
		"atan2": func(a: Array) -> float: return DMath.atan2_(a[0], a[1]),
		"pow": func(a: Array) -> float: return DMath.pow_(a[0], a[1]),
		"hypot": func(a: Array) -> float: return DMath.hypot(a[0], a[1]),
		"hypot3": func(a: Array) -> float: return DMath.hypot3(a[0], a[1], a[2]),
		"round": func(a: Array) -> float: return DMath.round_js(a[0]),
	}
	for name: String in fns:
		var rows: Array = cases.get(name, [])
		var bad := 0
		var first := ""
		for row: Array in rows:
			var args: Array = []
			for i in row.size() - 1:
				args.append(_hex_float(row[i]))
			var want := _hex_bits(row[row.size() - 1])
			var got: float = fns[name].call(args)
			if DMath.bits(got) != want and not (is_nan(got) and is_nan(DMath._f(want))):
				bad += 1
				if first.is_empty():
					first = " first: %s(%s) = %s, V8 %s" % [name, str(args), got, DMath._f(want)]
		_ok(rows.size() > 0 and bad == 0, "dmath %s matches V8 bit for bit on %d inputs%s" % [name, rows.size(), "" if bad == 0 else " (%d differ;%s)" % [bad, first]])
	return true


static func _hex_bits(h: String) -> int:
	return (h.substr(0, 8).hex_to_int() << 32) | h.substr(8, 8).hex_to_int()


static func _hex_float(h: String) -> float:
	return DMath._f(_hex_bits(h))


## data/maps.json must hold every map number exactly as the web game has it, and sim/maps.gd must
## roll the same Chaos Isles as the web game for the same seed (tests/golden/maps.json).
func _check_maps() -> bool:
	var maps := Maps.load_maps("res://data/maps.json")
	var golden := Balance.load_file(GOLDEN.path_join("maps.json"))
	var gm: Dictionary = golden.get("maps", {})
	_ok(maps.size() == gm.size() and maps.size() > 0, "maps.json has %d maps (web v%s has %d)" % [maps.size(), golden.get("web", "?"), gm.size()])
	var bad: Array[String] = []
	for id: String in gm:
		var want: Array = gm[id]
		var got := _fingerprint(maps.get(id, {}), [])
		if got.size() != want.size():
			bad.append("%s: %d numbers, web %d" % [id, got.size(), want.size()])
			continue
		for i in want.size():
			if got[i] != _hex_bits(want[i]):
				bad.append("%s: number %d differs" % [id, i])
				break
	_ok(bad.is_empty(), "every number on all %d maps matches the web game exactly %s" % [gm.size(), "" if bad.is_empty() else str(bad)])
	var gen := Balance.load_file("res://data/mapgen.json")
	var chaos: Dictionary = golden.get("chaos", {})
	for seed: String in chaos:
		var want: Dictionary = Maps._decode(chaos[seed].map)
		var got := Maps.make_chaos(float(seed), gen, Balance.data)
		var diff := _first_diff(want, got, "")
		_ok(diff.is_empty(), "Chaos Isles seed %s matches the web game (%d bases, %d islands) %s" % [seed, got.get("zones", []).size(), want.get("blobs", []).size(), diff])
	return true


## Every number in a map, keys sorted, as 64-bit patterns (same order as tools/export_maps.js).
func _fingerprint(v: Variant, out: Array) -> Array:
	if v is float or v is int:
		out.append(DMath.bits(float(v)))
	elif v is Array:
		for x: Variant in v:
			_fingerprint(x, out)
	elif v is Dictionary:
		var keys: Array = (v as Dictionary).keys()
		keys.sort()
		for k: Variant in keys:
			_fingerprint(v[k], out)
	return out


## "" if `got` has everything `want` has (numbers compared exactly), else where it first differs.
func _first_diff(want: Variant, got: Variant, at: String) -> String:
	if (want is float or want is int) and (got is float or got is int):
		return "" if DMath.bits(float(want)) == DMath.bits(float(got)) else "at %s: web %s, port %s" % [at, want, got]
	if want is Array and got is Array:
		if want.size() != got.size():
			return "at %s: web %d items, port %d" % [at, want.size(), got.size()]
		for i in want.size():
			var d := _first_diff(want[i], got[i], "%s[%d]" % [at, i])
			if not d.is_empty():
				return d
		return ""
	if want is Dictionary and got is Dictionary:
		for k: Variant in want:
			if want[k] is bool and not want[k] and not got.has(k):
				continue
			if not got.has(k):
				return "at %s.%s: missing" % [at, k]
			var d := _first_diff(want[k], got[k], "%s.%s" % [at, k])
			if not d.is_empty():
				return d
		return ""
	return "" if want == got else "at %s: web %s, port %s" % [at, want, got]


## sim/terrain.gd must build the same terrain as the web game's buildMap (tests/golden/terrain0.json):
## start slots, every height (as 32-bit floats), the passability and water grids, props and coves.
## Big maps take a while in GDScript, so by default a spread of maps runs; FULL_TERRAIN runs all.
const FULL_TERRAIN := false
const TERRAIN_QUICK := ["tutorial", "dawgs", "twinreach_teams", "brine", "moon_dawgs", "chaos_s8"]


func _check_terrain() -> bool:
	var golden := Balance.load_file(GOLDEN.path_join("terrain0.json"))
	var runs: Dictionary = golden.get("runs", {})
	_ok(not runs.is_empty(), "golden terrain0.json loads (web v%s)" % golden.get("web", "?"))
	var maps := Maps.load_maps("res://data/maps.json")
	var gen := Balance.load_file("res://data/mapgen.json")
	for name: String in runs:
		if not FULL_TERRAIN and not name in TERRAIN_QUICK:
			continue
		var g: Dictionary = runs[name]
		var opts: Dictionary = g.opts
		var seed := int(opts.seed)
		var m: Dictionary
		if opts.map == "chaos":
			m = Maps.make_chaos(float(seed), gen, Balance.data)
		else:
			m = maps[opts.map].duplicate(true)
		var rnd := Rng.new(seed ^ 0x9e3779b9)
		var bz := Maps.battle_zones(m, opts, rnd, gen)
		m.zonesFinal = bz.zonesFinal
		var diff := _first_diff(Maps._decode(g.zonesFinal), bz.zonesFinal, "zonesFinal")
		if diff.is_empty():
			diff = _first_diff(g.slotOf, bz.slotOf, "slotOf")
		var t0 := Time.get_ticks_msec()
		var t = Terrain.build(m, seed, Balance.data, gen)
		var ms := Time.get_ticks_msec() - t0
		var problems: Array[String] = []
		if not diff.is_empty():
			problems.append("start slots " + diff)
		if _sha(t.hv.to_byte_array()) != g.hv:
			var first := ""
			for s: Array in g.samples:
				if DMath.bits(t.hv[int(s[0])]) != _hex_bits(s[1]):
					first = " (first sampled difference at vertex %d: web %s, port %s)" % [s[0], DMath._f(_hex_bits(s[1])), t.hv[int(s[0])]]
					break
			problems.append("heights differ" + first)
		if _sha(t.land_grid) != g.pass:
			problems.append("passability differs (%d land cells, web %d)" % [_count(t.land_grid), g.passCount])
		if _sha(t.water_grid) != g.wpass:
			problems.append("water grid differs")
		var pd := _first_diff(Maps._decode(g.props), t.props, "props")
		if not pd.is_empty():
			problems.append(pd)
		var cd := _first_diff(Maps._decode(g.coves), t.coves, "coves")
		if not cd.is_empty():
			problems.append(cd)
		_ok(problems.is_empty(), "terrain %s identical to web (%dx%d cells, %d props, %d coves, built in %.1f s) %s" % [
			name, t.GW, t.GH, t.props.size(), t.coves.size(), ms / 1000.0, "; ".join(problems)])
	return true


static func _sha(b: PackedByteArray) -> String:
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	h.update(b)
	return h.finish().hex_encode()


static func _count(b: PackedByteArray) -> int:
	var n := 0
	for x in b:
		n += x
	return n


## sim/pathing.gd must find the same paths as the web game's findPath, waypoint for waypoint,
## on the same ground grid (tests/golden/paths.json, from tools/web_paths.js).
func _check_pathing() -> bool:
	var golden := Balance.load_file(GOLDEN.path_join("paths.json"))
	var runs: Dictionary = golden.get("runs", {})
	_ok(not runs.is_empty(), "golden paths.json loads (web v%s)" % golden.get("web", "?"))
	for name: String in runs:
		var g: Dictionary = runs[name]
		var fake := {"X0": float(g.X0), "Z0": float(g.Z0), "cell": float(g.CELL), "GW": int(g.GW), "GH": int(g.GH)}
		var p := Pathing.new(_Dims.new(fake), Balance.data.engine)
		var grid := Marshalls.base64_to_raw(g.pass)
		var bad := 0
		var first := ""
		var found := 0
		for q: Array in g.queries:
			var got: Variant = p.find_path(_hex_float(q[0]), _hex_float(q[1]), _hex_float(q[2]), _hex_float(q[3]), grid)
			var want: Variant = q[4]
			var same := (got == null) == (want == null)
			if same and want != null:
				found += 1
				same = (got as Array).size() == (want as Array).size()
				if same:
					for k in (want as Array).size():
						if DMath.bits(got[k][0]) != _hex_bits(want[k][0]) or DMath.bits(got[k][1]) != _hex_bits(want[k][1]):
							same = false
							break
			if not same:
				bad += 1
				if first.is_empty():
					first = " first: query %d, web %s waypoints, port %s" % [g.queries.find(q), "none" if want == null else str((want as Array).size()), "none" if got == null else str((got as Array).size())]
		_ok(bad == 0, "pathing %s: %d paths identical to web (%d found)%s" % [name, g.queries.size() - bad, found, "" if bad == 0 else " - %d differ;%s" % [bad, first]])
	return true


## Stand-in for a terrain: just the grid's size and position.
class _Dims:
	var X0: float
	var Z0: float
	var cell: float
	var GW: int
	var GH: int
	func _init(d: Dictionary) -> void:
		X0 = d.X0
		Z0 = d.Z0
		cell = d.cell
		GW = d.GW
		GH = d.GH


## sim/spatial.gd must find exactly the live units within range, in the web game's visit order.
func _check_spatial() -> bool:
	var rng := Rng.new(99)
	var W := 790.0
	var H := 450.0
	var units := []
	for k in 600:
		var u := _Dot.new()
		u.x = -W / 2.0 + rng.next() * W
		u.z = -H / 2.0 + rng.next() * H
		u.alive = rng.next() > 0.1
		units.append(u)
	var hash := Spatial.new(W, H, -W / 2.0, -H / 2.0, Balance.value("engine.hashBucket"))
	hash.rebuild(units)
	var bad := 0
	for q in 200:
		var x := -W / 2.0 + rng.next() * W
		var z := -H / 2.0 + rng.next() * H
		var r := 5.0 + rng.next() * 60.0
		var got := []
		hash.query(x, z, r, func(u: Object, _d2: float) -> void: got.append(u))
		# expected: bucket rows, then columns, then insertion order (the web visit order)
		var want := []
		for j in hash.BH:
			for i in hash.BW:
				for u: _Dot in units:
					if not u.alive:
						continue
					var ui := clampi(int(floorf((u.x - hash.X0) / hash.size)), 0, hash.BW - 1)
					var uj := clampi(int(floorf((u.z - hash.Z0) / hash.size)), 0, hash.BH - 1)
					if ui == i and uj == j and (u.x - x) * (u.x - x) + (u.z - z) * (u.z - z) <= r * r:
						want.append(u)
		if got != want:
			bad += 1
	_ok(bad == 0, "spatial hash: 200 range queries over 600 units match a full scan, in web order%s" % ("" if bad == 0 else " (%d differ)" % bad))
	return true


class _Dot:
	var x := 0.0
	var z := 0.0
	var alive := true


## sim/tables.gd must build the same unit, zone and facility tables as the web game.
func _check_tables() -> bool:
	var golden := Balance.load_file(GOLDEN.path_join("tables.json"))
	var t := Tables.new(Balance.data)
	for pair: Array in [["UTYPES", t.utypes], ["ZTYPES", t.ztypes], ["FACILITIES", t.facilities]]:
		var want: Dictionary = Maps._decode(golden.get(pair[0], {}))
		var diff := _first_diff(want, pair[1], pair[0])
		_ok(not want.is_empty() and diff.is_empty() and want.size() == (pair[1] as Dictionary).size(),
			"%s: %d entries identical to web %s" % [pair[0], want.size(), diff])
	var fac := Balance.load_file("res://data/factions.json")
	_ok(fac.has("player") and (fac.get("ai", []) as Array).size() == 15, "factions.json has the player and %d AI armies" % (fac.get("ai", []) as Array).size())
	return true


## Battle setup (sim.gd, the web createGame) must match the web game at each recorded checkpoint,
## including how many random numbers have been drawn (tests/golden/setup.json, tools/web_setup.js).
func _check_setup() -> bool:
	var golden := Balance.load_file(GOLDEN.path_join("setup.json"))
	var runs: Dictionary = golden.get("runs", {})
	_ok(not runs.is_empty(), "golden setup.json loads (web v%s)" % golden.get("web", "?"))
	for name: String in runs:
		var g: Dictionary = runs[name]
		var t0 := Time.get_ticks_msec()
		var sim := SimCore.new(Balance.game_data(), g.opts)
		var ms := Time.get_ticks_msec() - t0
		var cp: Dictionary = Maps._decode(g.checkpoints.zones)
		var problems: Array[String] = []
		if sim.rnd.draws != int(cp.rc):
			problems.append("random draws %d, web %d" % [sim.rnd.draws, cp.rc])
		for pair: Array in [["factions", sim.factions], ["zones", sim.zones], ["home", sim.home], ["homes", sim.homes]]:
			var d := _first_diff(cp[pair[0]], pair[1], pair[0])
			if not d.is_empty():
				problems.append(d)
		_ok(problems.is_empty(), "setup %s: %d armies, %d bases identical to web after %d draws (%.1f s) %s" % [
			name, sim.factions.size(), sim.zones.size(), int(cp.rc), ms / 1000.0, "; ".join(problems)])
	return true
