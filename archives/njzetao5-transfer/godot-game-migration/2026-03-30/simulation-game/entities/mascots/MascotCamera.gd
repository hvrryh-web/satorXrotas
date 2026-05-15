[Ver001.000]
## Mascot Camera System
## Spectator camera with smooth follow behavior for mascot focus mode

class_name MascotCamera
extends Camera2D

## Camera behavior settings
@export var smooth_follow: bool = true
@export var follow_speed: float = 5.0
@export var zoom_duration: float = 0.5
@export var focus_zoom: Vector2 = Vector2(1.5, 1.5)
@export var normal_zoom: Vector2 = Vector2(1.0, 1.0)

## Tracking targets
var current_target: Mascot = null
var default_position: Vector2 = Vector2.ZERO
var _is_focusing: bool = false

## Smooth follow variables
var _target_position: Vector2 = Vector2.ZERO
var _current_velocity: Vector2 = Vector2.ZERO

## Performance tracking
var _last_update_time: int = 0

func _ready():
	default_position = position
	_target_position = position
	
	## Connect to all mascot focus requests
	get_tree().node_added.connect(_on_node_added)
	_connect_to_existing_mascots()

func _on_node_added(node: Node):
	## Connect to new mascots as they're added
	if node is Mascot:
		node.camera_focus_requested.connect(_on_mascot_focus_requested)

func _connect_to_existing_mascots():
	## Connect to already existing mascots
	var mascots = get_tree().get_nodes_in_group("mascots")
	for mascot in mascots:
		if mascot is Mascot and not mascot.camera_focus_requested.is_connected(_on_mascot_focus_requested):
			mascot.camera_focus_requested.connect(_on_mascot_focus_requested)

func _on_mascot_focus_requested(mascot: Mascot):
	focus_on_mascot(mascot)

func _process(delta: float):
	if _is_focusing and current_target:
		_update_smooth_follow(delta)

func _update_smooth_follow(delta: float):
	## Smoothly interpolate towards target position
	if smooth_follow:
		_target_position = current_target.global_position
		position = position.lerp(_target_position, follow_speed * delta)
	else:
		position = current_target.global_position
	
	## Track update time for performance
	_update_performance_metrics()

func _update_performance_metrics():
	var current_time = Time.get_ticks_usec()
	if _last_update_time > 0:
		var update_time = current_time - _last_update_time
		## Warn if camera update exceeds budget
		if update_time > 500:  ## 500us budget for camera
			push_warning("MascotCamera exceeded update budget: %d us" % update_time)
	_last_update_time = current_time

## Public API

func focus_on_mascot(mascot: Mascot):
	## Focus camera on a specific mascot with smooth transition
	current_target = mascot
	_is_focusing = true
	
	## Smooth zoom in
	var tween = create_tween()
	tween.tween_property(self, "zoom", focus_zoom, zoom_duration)
	
	## Emit signal for UI updates
	mascot_focus_changed.emit(mascot)

func return_to_default():
	## Return camera to default position
	current_target = null
	_is_focusing = false
	
	## Smooth zoom out and return
	var tween = create_tween()
	tween.tween_property(self, "zoom", normal_zoom, zoom_duration)
	tween.parallel().tween_property(self, "position", default_position, zoom_duration)
	
	camera_returned.emit()

func cycle_to_next_mascot():
	## Cycle focus to next mascot in scene
	var mascots = get_tree().get_nodes_in_group("mascots")
	if mascots.is_empty():
		return
	
	var current_index = 0
	if current_target:
		current_index = mascots.find(current_target)
		current_index = (current_index + 1) % mascots.size()
	
	focus_on_mascot(mascots[current_index])

func get_current_target_info() -> Dictionary:
	## Get information about current camera target
	if not current_target:
		return {"has_target": false}
	
	return {
		"has_target": true,
		"mascot_name": current_target.mascot_name,
		"mascot_type": current_target.mascot_type,
		"state": current_target.get_state_name(),
		"render_time_ms": current_target.get_render_time_ms(),
		"within_budget": current_target.is_within_budget()
	}

func is_focusing() -> bool:
	## Check if camera is currently focused on a mascot
	return _is_focusing

## Signals
signal mascot_focus_changed(mascot: Mascot)
signal camera_returned()
