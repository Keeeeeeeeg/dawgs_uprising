extends Node
## Autoload "Balance". Loads data/balance.json, where every gameplay number lives
## (the web game's BALANCE object). Engine code reads numbers from here, never hard-codes them.
##
## The SIM does not use this autoload directly: it receives `Balance.data` in Sim.new(),
## so tests can run it with modified numbers and it stays free of nodes.

const PATH := "res://data/balance.json"

var data: Dictionary = {}
var _game: Dictionary = {}


func _init() -> void:
	data = load_file(PATH)


## Reads a JSON object from disk. Returns {} and reports an error if it is missing or malformed.
static func load_file(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("Balance: cannot open %s (%s)" % [path, error_string(FileAccess.get_open_error())])
		return {}
	var json := JSON.new()
	var err := json.parse(f.get_as_text())
	if err != OK:
		push_error("Balance: %s line %d: %s" % [path, json.get_error_line(), json.get_error_message()])
		return {}
	if typeof(json.data) != TYPE_DICTIONARY:
		push_error("Balance: %s is not a JSON object" % path)
		return {}
	return json.data


## Dotted lookup, e.g. value("economy.incomeDiv") or value("units.rifle.hp").
## Reports an error and returns `fallback` if any part of the path is missing.
func value(path: String, fallback: Variant = null) -> Variant:
	return lookup(data, path, fallback)


static func lookup(from: Dictionary, path: String, fallback: Variant = null) -> Variant:
	var cur: Variant = from
	for key in path.split("."):
		if cur is Dictionary and (cur as Dictionary).has(key):
			cur = cur[key]
		else:
			push_error("Balance: missing '%s'" % path)
			return fallback
	return cur


## Everything a battle needs, as Sim.new() takes it: balance, maps, mapgen and factions.
## Loaded once and shared (the SIM copies what it changes).
func game_data() -> Dictionary:
	if _game.is_empty():
		const Maps := preload("res://sim/maps.gd")
		_game = {"balance": data, "maps": Maps.load_maps("res://data/maps.json"),
			"mapgen": load_file("res://data/mapgen.json"), "factions": load_file("res://data/factions.json")}
	return _game
