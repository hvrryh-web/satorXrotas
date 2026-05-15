[Ver001.000]
## Mascot Base Class
## Base class for all mascot characters in the simulation
## Provides animation state machine, spectator camera hooks, and performance optimization

class_name Mascot
extends Node2D

## Signals
signal state_changed(new_state: State, old_state: State)
signal animation_triggered(anim_name: String)
signal camera_focus_requested(mascot: Mascot)

## Animation States
enum State {
	IDLE,
	CHEER,
	REACT,
	CELEBRATE,
	SAD
}

## Mascot Types
enum Type {
	SOL,  ## Solar phoenix theme
	LUN,  ## Lunar owl theme
	BIN,  ## Binary cyber theme
	FAT,  ## Phoenix/mythical theme
	UNI   ## Unicorn/fantasy theme
}

## Configuration
@export var mascot_name: String = "Mascot"
@export var mascot_type: Type = Type.SOL
@export var animation_speed: float = 1.0
@export var state_transition_duration: float = 0.3

## Performance budget tracking
var _render_time_us: int = 0
var _max_render_time_us: int = 2000  ## <2ms budget (2000 microseconds)

## State machine
var current_state: State = State.IDLE
var _state_timer: float = 0.0
var _idle_time: float = 0.0

## Animation components
@onready var animation_player: AnimationPlayer
@onready var sprite: Sprite2D
@onready var state_machine: AnimationNodeStateMachinePlayback

## Context data for reactions
var _reaction_context: Dictionary = {}

func _ready():
	_setup_components()
	_enter_state(State.IDLE)
	add_to_group("mascots")

func _setup_components():
	## Find or create required components
	animation_player = get_node_or_null("AnimationPlayer")
	sprite = get_node_or_null("Sprite2D")
	
	if animation_player:
		animation_player.speed_scale = animation_speed

func _process(delta: float):
	var start_time = Time.get_ticks_usec()
	
	_update_state_machine(delta)
	_update_animations(delta)
	
	## Track render time for performance budget
	_render_time_us = Time.get_ticks_usec() - start_time
	if _render_time_us > _max_render_time_us:
		push_warning("Mascot %s exceeded render budget: %d us" % [mascot_name, _render_time_us])

func _update_state_machine(delta: float):
	_state_timer += delta
	_idle_time += delta
	
	match current_state:
		State.IDLE:
			## Random occasional micro-movements for liveliness
			if _idle_time > 3.0 and randf() < 0.1:
				_trigger_micro_movement()
				_idle_time = 0.0
		
		State.CHEER, State.REACT, State.CELEBRATE, State.SAD:
			## Return to idle after animation completes
			if _state_timer > 2.0:
				transition_to(State.IDLE)

func _update_animations(_delta: float):
	## Override in subclasses for specific animation updates
	pass

func _enter_state(new_state: State):
	var old_state = current_state
	current_state = new_state
	_state_timer = 0.0
	
	match new_state:
		State.IDLE:
			_play_animation("idle")
		State.CHEER:
			_play_animation("cheer")
		State.REACT:
			_play_reaction_animation()
		State.CELEBRATE:
			_play_animation("celebrate")
		State.SAD:
			_play_animation("sad")
	
	state_changed.emit(new_state, old_state)

func _play_animation(anim_name: String):
	if animation_player and animation_player.has_animation(anim_name):
		animation_player.play(anim_name)
		animation_triggered.emit(anim_name)

func _play_reaction_animation():
	## Context-aware reaction animation selection
	var reaction_type = _reaction_context.get("type", "neutral")
	var anim_name = "react_%s" % reaction_type
	
	if animation_player and animation_player.has_animation(anim_name):
		animation_player.play(anim_name)
	else:
		_play_animation("react")
	
	animation_triggered.emit(anim_name)

func _trigger_micro_movement():
	## Subtle movement for idle liveliness
	if sprite:
		var tween = create_tween()
		tween.tween_property(sprite, "position:y", sprite.position.y - 2, 0.1)
		tween.tween_property(sprite, "position:y", sprite.position.y, 0.1)

## Public API

func transition_to(new_state: State, context: Dictionary = {}):
	## Transition to a new animation state with optional context
	_reaction_context = context
	_enter_state(new_state)

func trigger_cheer(intensity: float = 1.0):
	## Trigger cheer animation with intensity (0.0 - 1.0)
	_reaction_context = {"intensity": intensity}
	transition_to(State.CHEER)

func trigger_reaction(reaction_type: String, context: Dictionary = {}):
	## Trigger contextual reaction
	context["type"] = reaction_type
	transition_to(State.REACT, context)

func trigger_celebration():
	## Trigger victory celebration
	transition_to(State.CELEBRATE)

func trigger_disappointment():
	## Trigger sad/disappointed reaction
	transition_to(State.SAD)

func focus_camera():
	## Request camera focus on this mascot
	camera_focus_requested.emit(self)

func get_render_time_ms() -> float:
	## Get last frame render time in milliseconds
	return _render_time_us / 1000.0

func is_within_budget() -> bool:
	## Check if mascot is within performance budget
	return _render_time_us <= _max_render_time_us

func get_state_name() -> String:
	## Get human-readable state name
	match current_state:
		State.IDLE: return "idle"
		State.CHEER: return "cheer"
		State.REACT: return "react"
		State.CELEBRATE: return "celebrate"
		State.SAD: return "sad"
		_: return "unknown"

func get_state() -> Dictionary:
	## Serialize mascot state for save/replay
	return {
		"mascot_name": mascot_name,
		"mascot_type": mascot_type,
		"current_state": current_state,
		"state_timer": _state_timer,
		"position": {"x": position.x, "y": position.y},
		"animation_speed": animation_speed
	}

func set_state(state: Dictionary):
	## Restore mascot state from dictionary
	mascot_name = state.get("mascot_name", mascot_name)
	mascot_type = state.get("mascot_type", mascot_type)
	current_state = state.get("current_state", State.IDLE)
	_state_timer = state.get("state_timer", 0.0)
	animation_speed = state.get("animation_speed", 1.0)
	
	var pos = state.get("position", {})
	position = Vector2(pos.get("x", 0), pos.get("y", 0))
