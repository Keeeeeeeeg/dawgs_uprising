extends Node3D
## Battle screen: owns one Sim, steps it every frame and draws it.
## Reads SIM state and listens to its events; changes it only through sim.apply_cmd().

const MENU_SCENE := "res://menus/main_menu.tscn"
const SimCore := preload("res://sim/sim.gd")

var sim: SimCore

@onready var hud = $Hud  # render/hud.gd


func _ready() -> void:
	sim = SimCore.new(Balance.data, {"seed": 1})
	sim.event.connect(_on_sim_event)


func _process(delta: float) -> void:
	sim.update(delta)
	hud.show_status(sim)


func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file(MENU_SCENE)


func _on_sim_event(_name: StringName, _a: Variant, _b: Variant, _c: Variant) -> void:
	pass  # muzzle flashes, deaths, zone captures... come with the renderer port
