extends Control
## Main menu: title, version tag, "What's changed", and the way into a battle.
## Version and changelog come from data/version.json (bump both with every change).

const VERSION_PATH := "res://data/version.json"
const BATTLE_SCENE := "res://render/battle.tscn"

@onready var _version: Label = %Version
@onready var _changes: RichTextLabel = %Changes


func _ready() -> void:
	var info := Balance.load_file(VERSION_PATH)
	_version.text = "v%s · %s · %s   (web v%s)" % [
		info.get("number", "?"), info.get("name", ""), info.get("date", ""), info.get("webBase", "?")]
	var text := "[b]What's changed[/b]\n"
	for entry: Dictionary in info.get("changelog", []):
		text += "\n[b]v%s[/b] %s (%s)\n" % [entry.get("v", ""), entry.get("name", ""), entry.get("by", "Unrecorded")]
		for line: String in entry.get("changes", []):
			text += "• %s\n" % line
	_changes.text = text
	%Skirmish.pressed.connect(_on_skirmish)
	%Quit.pressed.connect(get_tree().quit)
	%Skirmish.grab_focus()


func _on_skirmish() -> void:
	get_tree().change_scene_to_file(BATTLE_SCENE)
