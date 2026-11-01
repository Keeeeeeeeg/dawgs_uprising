class_name Sim
extends RefCounted
## The game simulation, ported from the web game's SIM script (createGame and everything in it).
##
## Rules for everything under sim/:
## - Pure logic. Extend RefCounted (or nothing), never Node. No scenes, input, rendering or autoloads.
## - Everything it needs comes in through new(): the game data and the battle options.
## - Deterministic: same seed + same commands = same result on every machine (multiplayer relies on it).
##   Use the seeded RNG only, never Godot's global random functions. Maths through dmath.gd.
## - No gameplay numbers in code: read them from the data files.
## - The renderer listens to `event` and reads state; it changes the SIM only through apply_cmd().
##
## Armies (factions) and bases (zones) are Dictionaries with the web game's field names, because
## they pick up optional fields as a battle goes on. Units get a typed class (phase 2b).

const DMath := preload("res://sim/dmath.gd")
const Rng := preload("res://sim/rng.gd")
const Maps := preload("res://sim/maps.gd")
const Terrain := preload("res://sim/terrain.gd")
const Pathing := preload("res://sim/pathing.gd")
const Spatial := preload("res://sim/spatial.gd")
const Tables := preload("res://sim/tables.gd")

## Same events the web SIM emits through on()/emit(): 'shot', 'death', 'zone', 'spawn', 'end', ...
signal event(name: StringName, a: Variant, b: Variant, c: Variant)

var data: Dictionary          # balance, maps, mapgen, factions (see data/game_data.gd)
var balance: Dictionary
var opts: Dictionary
var time := 0.0
var ticks := 0
var over := false

# battle setup (web createGame)
var seed := 0
var rnd                        # the battle's Rng (web rnd)
var map_def: Dictionary        # the map, with zonesFinal
var mode := "ffa"
var carrier_mode := false      # web CVM
var NF := 0                    # number of armies
var H := 0                     # number of human players
var humans: Array = []
var ai_cfg: Array = []
var team_of: Array = []
var slot_of: Array = []
var terrain                    # sim/terrain.gd
var pathing                    # sim/pathing.gd
var spatial                    # sim/spatial.gd
var tables                     # sim/tables.gd
var factions: Array = []       # web G.factions / F
var zones: Array = []          # web G.zones
var units: Array = []          # web G.units
var home := -1                 # web G.home: the player's HQ zone
var homes: Array = []          # web G.homes
var ai_passive := false

var _step := 0.0
var _max_frame := 0.0
var _acc := 0.0


## data: {balance, maps, mapgen, factions}. opts: like the web createGame options
## (map, seed, rngSeed, mapSeed, mode, humans, ai, easyAI, passiveAI, noStartZones).
## With data = {balance} only (no maps) the SIM just ticks, for low-level tests.
func _init(p_data: Dictionary, p_opts: Dictionary = {}) -> void:
	data = p_data
	balance = data.get("balance", {})
	opts = p_opts
	var engine: Dictionary = balance.get("engine", {})
	_step = engine.get("step", 0.0)
	_max_frame = engine.get("maxFrame", 0.0)
	if _step <= 0.0 or _max_frame <= 0.0:
		push_error("Sim: balance.json needs engine.step and engine.maxFrame")
		over = true
		return
	if data.has("maps"):
		_setup()


# ---------- battle setup (web createGame) ----------

func _setup() -> void:
	var gen: Dictionary = data.mapgen
	var ST: Dictionary = balance.start
	seed = int(opts.get("seed", 0))
	if seed == 0:
		seed = int(gen.defaultSeed)
	var rng_seed := int(opts.get("rngSeed", 0))
	rnd = Rng.new((rng_seed if rng_seed != 0 else seed) ^ int(gen.rngXor))
	var maps: Dictionary = data.maps
	map_def = maps.get(opts.get("map", ""), maps[gen.defaultMap]).duplicate(true)
	if map_def.get("chaos", false) or opts.get("map", "") == "chaos":
		var ms := int(opts.get("mapSeed", 0))
		map_def = Maps.make_chaos(float(ms if ms != 0 else (rng_seed if rng_seed != 0 else seed)), gen, balance)
	carrier_mode = map_def.get("carrier", false)
	var bz := Maps.battle_zones(map_def, opts, rnd, gen)
	NF = bz.NF
	team_of = bz.teamOf
	mode = bz.mode
	slot_of = bz.slotOf
	humans = bz.humans
	ai_cfg = bz.ai
	H = humans.size()
	map_def.zonesFinal = bz.zonesFinal
	terrain = Terrain.build(map_def, seed, balance, gen)
	pathing = Pathing.new(terrain, balance.engine)
	spatial = Spatial.new(terrain.W, terrain.H, terrain.X0, terrain.Z0, balance.engine.hashBucket)
	tables = Tables.new(balance)
	_setup_factions(ST)
	_setup_zones(ST)


func _difficulty(f: int) -> String:
	if opts.get("easyAI", false):
		return "easy"
	var d: String = ai_cfg[f - H].get("diff", "")
	return d if d in ["easy", "normal", "hard"] else "hard"


static func _color(c: Variant) -> Variant:
	if c is String and (c as String).begins_with("#"):
		return (c as String).substr(1).hex_to_int()
	return c


func _setup_factions(ST: Dictionary) -> void:
	var player: Dictionary = data.factions.player
	var pool: Array = data.factions.ai
	for f in NF:
		var fd: Dictionary
		var col: Variant = null
		if f < H:
			var hu: Dictionary = humans[f]
			fd = player.duplicate(true)
			if hu.get("name", null) != null:
				fd.name = hu.name
				fd.short = hu.name
			elif H > 1:
				fd.name = "Player %d" % (f + 1)
				fd.short = "P%d" % (f + 1)
			col = hu.get("color", null)
		else:
			var a: Dictionary = ai_cfg[f - H]
			fd = (pool[int(a.p) % pool.size()] as Dictionary).duplicate(true)
			if a.get("name", null) != null:
				fd.name = a.name
				fd.short = a.get("short", a.name)
			col = a.get("color", null)
		fd.color = _color(fd.color)
		if col is Dictionary and col.has("css"):
			fd.css = col.css
			fd.color = _color(col.hex)
		var is_player: bool = fd.get("player", false)
		var aggro := []
		aggro.resize(NF)
		aggro.fill(0.0)
		fd.merge({"id": f, "team": team_of[f], "money": ST.money.player if is_player else ST.money.ai,
			"hr": ST.manpower if is_player else 0.0, "aggro": aggro, "alive": true,
			"kills": 0, "losses": 0, "lostTo": null, "autoGarrison": true}, true)
		if is_player:
			fd.diff = null
			fd.ai = null
		else:
			var d := _difficulty(f)
			fd.diff = d
			fd.ai = {"t": ST.aiThink + f * ST.aiThinkStagger,
				"waveT": (ST.aiWave + f * ST.aiWaveStagger) * balance.ai.difficulty[d].first,
				"groups": [], "qrf": {}}
		factions.append(fd)
	# tutorial: the AI holds back until release_ai()
	ai_passive = opts.get("passiveAI", false)
	if ai_passive:
		for fac: Dictionary in factions:
			if fac.ai != null:
				fac.ai.waveT = balance.ai.passiveWave
	# starting grudges toward every enemy
	var AG: Dictionary = balance.aggro
	for a: Dictionary in factions:
		for b: Dictionary in factions:
			if hostile(a.id, b.id):
				a.aggro[b.id] = AG.start + rnd.next() * AG.startSpread


func hostile(a: Variant, b: Variant) -> bool:
	return a != b and a != null and b != null and factions[a].team != factions[b].team


func allied(a: Variant, b: Variant) -> bool:
	return a != null and b != null and factions[a].team == factions[b].team


func _setup_zones(ST: Dictionary) -> void:
	var ZT: Dictionary = tables.ztypes
	var zf: Array = map_def.zonesFinal
	for i in zf.size():
		var d: Array = zf[i]
		var t: Dictionary = ZT[d[1]]
		var counts := []
		counts.resize(NF)
		counts.fill(0)
		zones.append({"id": i, "name": d[0], "type": d[1], "x": float(d[2]), "z": float(d[3]), "r": t.r,
			"owner": null, "cap": {"f": null, "p": 0}, "coastal": d.size() > 4 and d[4], "port": false,
			"garN": 0, "garHp": 0, "counts": counts, "contested": false,
			"prodT": t.prod.every * (ST.zoneProdMin + rnd.next() * ST.zoneProdSpread),
			"prodI": 0, "prodState": "idle", "capturedT": -999, "threatT": -999,
			"y": terrain.height_at(float(d[2]), float(d[3]))})
	var slots: Array = map_def.slots
	if not carrier_mode:
		for f in NF:
			var zi := int(slots[slot_of[f]])
			zones[zi].owner = f
			zones[zi].home = f
	home = int(slots[slot_of[0]])
	homes = []
	for f in NF:
		homes.append(int(slots[slot_of[f]]))
	if not opts.get("noStartZones", false) and not carrier_mode:
		var slot_zone := {}
		for s: Variant in slots:
			slot_zone[int(s)] = true
		for round in 2:
			for f in NF:
				var hq: Dictionary = zones[int(slots[slot_of[f]])]
				var best = null
				var bd: float = data.mapgen.slots.far
				for z: Dictionary in zones:
					if z.owner != null or slot_zone.has(z.id):
						continue
					var d := DMath.hypot(z.x - hq.x, z.z - hq.z)
					if d < bd:
						bd = d
						best = z
				if best != null:
					best.owner = f


# ---------- running ----------

## Advance by real time. Like the web G.update(): each call is capped at engine.maxFrame
## and run in fixed engine.step ticks.
func update(dt: float) -> void:
	if over:
		return
	_acc += minf(dt, _max_frame)
	while _acc >= _step:
		_tick(_step)
		_acc -= _step
		if over:
			break


func _tick(dt: float) -> void:
	time += dt
	ticks += 1
	# Port order, from the web SIM's tick(): rebuildHash, airbaseUpkeep, updateUnit (each unit),
	# separate, updateProjectiles, recruitTick, autoMan, then every 0.25 s updateZones/produce/
	# updateFacilities, economy, missiles, heal every 0.5 s, carrierTick, faction AI, visibility
	# every 0.2 s, and dead-unit cleanup every 1 s.


## Every player action arrives here as plain data, so multiplayer can send it. Ported in phase 7.
func apply_cmd(_cmd: Dictionary) -> void:
	pass


## Fingerprint of the game state, to spot machines drifting apart in multiplayer.
## Placeholder until units are ported.
func state_hash() -> int:
	return hash([ticks, time])
