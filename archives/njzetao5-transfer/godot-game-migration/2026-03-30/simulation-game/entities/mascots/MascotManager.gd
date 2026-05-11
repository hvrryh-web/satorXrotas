[Ver001.000]
## Mascot Manager
## Central coordinator for all mascot entities in the simulation
## Manages spawning, state synchronization, and performance monitoring

class_name MascotManager
extends Node

## Configuration
@export var auto_spawn_mascots: bool = true
@export var mascot_positions: Array[Vector2] = []

## Performance monitoring
var _total_render_time_us: int = 0
var _frame_count: int = 0
var _performance_history: Array[int] = []
const MAX_HISTORY_SIZE: int = 60  ## 1 second at 60fps
const BUDGET_PER_MASCOT_US: int = 2000  ## <2ms per mascot

## Mascot instances
var _mascots: Array[Mascot] = []
var _camera: MascotCamera = null

## Scene paths for each mascot type
const MASCOT_SCENES = {
	Mascot.Type.SOL: "res://entities/mascots/SolMascot.tscn",
	Mascot.Type.LUN: "res://entities/mascots/LunMascot.tscn",
	Mascot.Type.BIN: "res://entities/mascots/BinMascot.tscn",
	Mascot.Type.FAT: "res://entities/mascots/FatMascot.tscn",
	Mascot.Type.UNI: "res://entities/mascots/UniMascot.tscn"
}

func _ready():
	if auto_spawn_mascots:
		spawn_all_mascots()

func _process(_delta: float):
	_update_performance_metrics()

func _update_performance_metrics():
	## Calculate total render time for all mascots
	_total_render_time_us = 0
	for mascot in _mascots:
		_total_render_time_us += mascot._render_time_us
	
	## Track history
	_performance_history.append(_total_render_time_us)
	if _performance_history.size() > MAX_HISTORY_SIZE:
		_performance_history.remove_at(0)
	
	_frame_count += 1
	
	## Log warning if total budget exceeded (5 mascots * 2ms = 10ms)
	var total_budget = _mascots.size() * BUDGET_PER_MASCOT_US
	if _total_render_time_us > total_budget and _frame_count % 60 == 0:
		push_warning("MascotManager: Total render time %d us exceeds budget %d us" % [_total_render_time_us, total_budget])

## Spawning

func spawn_all_mascots():
	## Spawn all 5 mascot types
	var types = [Mascot.Type.SOL, Mascot.Type.LUN, Mascot.Type.BIN, Mascot.Type.FAT, Mascot.Type.UNI]
	
	for i in range(types.size()):
		var pos = Vector2(100 + i * 150, 300)  ## Default spacing
		if i < mascot_positions.size():
			pos = mascot_positions[i]
		spawn_mascot(types[i], pos)

func spawn_mascot(type: Mascot.Type, position: Vector2) -> Mascot:
	## Spawn a single mascot of given type
	var scene_path = MASCOT_SCENES.get(type, MASCOT_SCENES[Mascot.Type.SOL])
	var scene = load(scene_path)
	
	if not scene:
		push_error("Failed to load mascot scene: %s" % scene_path)
		return null
	
	var mascot = scene.instantiate()
	mascot.position = position
	add_child(mascot)
	_mascots.append(mascot)
	
	mascot_spawned.emit(mascot)
	return mascot

func clear_all_mascots():
	## Remove all mascots
	for mascot in _mascots:
		if is_instance_valid(mascot):
			mascot.queue_free()
	_mascots.clear()

## Camera Integration

func setup_camera(camera: MascotCamera):
	## Link a camera for mascot focus mode
	_camera = camera

func focus_camera_on(mascot: Mascot):
	## Focus camera on specific mascot
	if _camera:
		_camera.focus_on_mascot(mascot)

func focus_camera_on_type(type: Mascot.Type):
	## Focus camera on first mascot of given type
	for mascot in _mascots:
		if mascot.mascot_type == type:
			focus_camera_on(mascot)
			return

## State Synchronization

func trigger_all_cheer(intensity: float = 1.0):
	## Make all mascots cheer
	for mascot in _mascots:
		mascot.trigger_cheer(intensity)

func trigger_all_reaction(reaction_type: String, context: Dictionary = {}):
	## Make all mascots react
	for mascot in _mascots:
		mascot.trigger_reaction(reaction_type, context)

func transition_all_to(state: Mascot.State, context: Dictionary = {}):
	## Transition all mascots to a state
	for mascot in _mascots:
		mascot.transition_to(state, context)

## Team-based reactions (for match events)

func celebrate_team_win(team: int):
	## Trigger celebration for winning team mascots
	## Odd mascot indices = Team A, Even = Team B
	for i in range(_mascots.size()):
		var mascot = _mascots[i]
		if (team == 0 and i % 2 == 0) or (team == 1 and i % 2 == 1):
			mascot.trigger_celebration()
		else:
			mascot.trigger_disappointment()

## Queries

func get_mascots() -> Array[Mascot]:
	## Get all managed mascots
	return _mascots

func get_mascot_by_type(type: Mascot.Type) -> Mascot:
	## Get first mascot of given type
	for mascot in _mascots:
		if mascot.mascot_type == type:
			return mascot
	return null

func get_mascot_by_name(name: String) -> Mascot:
	## Get mascot by name
	for mascot in _mascots:
		if mascot.mascot_name == name:
			return mascot
	return null

## Performance

func get_performance_report() -> Dictionary:
	## Get performance statistics
	var avg_time = 0
	if not _performance_history.is_empty():
		var total = 0
		for t in _performance_history:
			total += t
		avg_time = total / _performance_history.size()
	
	var within_budget = _mascots.size() > 0
	for mascot in _mascots:
		if not mascot.is_within_budget():
			within_budget = false
			break
	
	return {
		"mascot_count": _mascots.size(),
		"current_render_time_us": _total_render_time_us,
		"average_render_time_us": avg_time,
		"total_budget_us": _mascots.size() * BUDGET_PER_MASCOT_US,
		"within_budget": within_budget,
		"fps_impact_estimate_ms": _total_render_time_us / 1000.0
	}

func is_performance_ok() -> bool:
	## Check if all mascots are within performance budget
	return get_performance_report().within_budget

## Serialization

func get_all_states() -> Array[Dictionary]:
	## Get states of all mascots for save/replay
	var states: Array[Dictionary] = []
	for mascot in _mascots:
		states.append(mascot.get_state())
	return states

func set_all_states(states: Array):
	## Restore all mascot states
	for i in range(min(states.size(), _mascots.size())):
		_mascots[i].set_state(states[i])

## Signals
signal mascot_spawned(mascot: Mascot)
signal mascot_state_changed(mascot: Mascot, new_state: Mascot.State)
