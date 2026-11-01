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
const GOLDEN := "res://tests/golden" # recorded from the web SIM by tools/web_trace.js
const CHUNK := 0.25 # matches the web harness: G.update() is stepped in 0.25 s chunks
const SECONDS := 30.0
const UNIT_FIELDS := ["name", "cost", "hp", "speed", "range", "dmg", "rof", "acc", "weapon", "armor"]

var _passed := 0
var _failed := 0
var _lines: PackedStringArray = []


func _ready() -> void:
	_check_balance()
	_check_sim_steps()
	_check_sim_is_pure()
	_check_rng_matches_web()
	var total := _passed + _failed
	var summary := "TESTS PASSED %d/%d" % [_passed, total] if _failed == 0 else "TESTS FAILED %d of %d" % [_failed, total]
	print(summary)
	_lines.insert(0, summary + "\n")
	if DisplayServer.get_name() == "headless":
		get_tree().quit(0 if _failed == 0 else 1)
	else:
		_show(_lines, _failed == 0)


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


func _check_balance() -> void:
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


func _run_sim() -> SimCore:
	var sim := SimCore.new(Balance.data, {"seed": 7})
	var t := 0.0
	while t < SECONDS:
		sim.update(CHUNK)
		t += CHUNK
	return sim


func _check_sim_steps() -> void:
	var a := _run_sim()
	var b := _run_sim()
	var step: float = Balance.value("engine.step")
	_ok(not a.over, "sim starts and runs")
	_ok(absf(a.ticks - SECONDS / step) <= 1.0, "%.0f s of play = %d ticks at %.4f s" % [SECONDS, a.ticks, step])
	_ok(a.state_hash() == b.state_hash(), "two runs, same seed, same state_hash")
	var capped := SimCore.new(Balance.data, {"seed": 7})
	capped.update(10.0)
	var max_frame: float = Balance.value("engine.maxFrame")
	_ok(capped.time <= max_frame + 1e-9, "one long frame is capped at maxFrame (%.2f s)" % capped.time)


## The SIM must stay free of nodes so it can run headless and in lockstep.
func _check_sim_is_pure() -> void:
	var dir := DirAccess.open(SIM_DIR)
	_ok(dir != null, "sim/ folder exists")
	if dir == null:
		return
	for file in dir.get_files():
		if not file.ends_with(".gd"):
			continue
		var script: Script = load(SIM_DIR.path_join(file))
		var base := script.get_instance_base_type()
		_ok(not ClassDB.is_parent_class(base, "Node"), "sim/%s is not a Node (%s)" % [file, base])
		var src := FileAccess.get_file_as_string(SIM_DIR.path_join(file))
		var banned := ["randf(", "randi(", "Balance.", "get_tree(", "Input."]
		var found := banned.filter(func(s: String) -> bool: return src.contains(s))
		_ok(found.is_empty(), "sim/%s uses no globals or unseeded randomness %s" % [file, "" if found.is_empty() else str(found)])


## sim/rng.gd must give exactly the numbers the web game's mulberry32 gives (tests/golden/rng.json).
func _check_rng_matches_web() -> void:
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
