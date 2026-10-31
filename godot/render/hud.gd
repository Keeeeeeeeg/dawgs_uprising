extends CanvasLayer
## Battle HUD. Shows SIM state; sends player actions back as commands (later).

@onready var _status: Label = $Status


func show_status(sim) -> void:  # sim/sim.gd
	_status.text = "SIM  t %.1f s   tick %d   [Esc] menu" % [sim.time, sim.ticks]
