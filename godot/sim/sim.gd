class_name Sim
extends RefCounted
## The game simulation, ported from the web game's SIM script.
##
## Rules for everything under sim/:
## - Pure logic. Extend RefCounted (or nothing), never Node. No scenes, input, rendering or autoloads.
## - Everything it needs comes in through new(): the balance data and the battle options.
## - Deterministic: same seed + same commands = same result on every machine (multiplayer relies on it).
##   Use the seeded RNG only, never Godot's global random functions.
## - No gameplay numbers in code: read them from `balance`.
## - The renderer listens to `event` and reads state; it changes the SIM only through apply_cmd().

## Same events the web SIM emits through on()/emit(): 'shot', 'death', 'zone', 'spawn', 'end', ...
signal event(name: StringName, a: Variant, b: Variant, c: Variant)

var balance: Dictionary
var opts: Dictionary
var time := 0.0
var ticks := 0
var over := false

var _step := 0.0
var _max_frame := 0.0
var _acc := 0.0


func _init(p_balance: Dictionary, p_opts: Dictionary = {}) -> void:
	balance = p_balance
	opts = p_opts
	var engine: Dictionary = balance.get("engine", {})
	_step = engine.get("step", 0.0)
	_max_frame = engine.get("maxFrame", 0.0)
	if _step <= 0.0 or _max_frame <= 0.0:
		push_error("Sim: balance.json needs engine.step and engine.maxFrame")
		over = true


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


## Every player action arrives here as plain data, so multiplayer can send it. Ported in step 2.
func apply_cmd(_cmd: Dictionary) -> void:
	pass


## Fingerprint of the game state, to spot machines drifting apart in multiplayer.
## Placeholder until units, factions and zones are ported.
func state_hash() -> int:
	return hash([ticks, time])
