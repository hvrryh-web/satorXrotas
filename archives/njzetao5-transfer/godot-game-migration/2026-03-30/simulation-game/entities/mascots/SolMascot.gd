[Ver001.000]
## Sol Mascot - Solar Phoenix Theme
## Fire-element mascot representing day, energy, and leadership

extends Mascot

func _init():
	mascot_name = "Sol"
	mascot_type = Type.SOL

func _ready():
	super._ready()
	## Sol-specific initialization
	modulate = Color(1.0, 0.8, 0.3, 1.0)  ## Warm golden glow

func _update_animations(delta: float):
	## Sol-specific animation updates - pulsing glow effect
	if sprite and current_state == State.IDLE:
		var pulse = 1.0 + sin(Time.get_ticks_msec() * 0.003) * 0.1
		sprite.scale = Vector2(pulse, pulse)

func trigger_flame_burst():
	## Sol-specific ability: flame burst celebration
	trigger_reaction("flame_burst", {"intensity": 1.0})
	
	## Create flame particles (placeholder for particle system)
	var flame = ColorRect.new()
	flame.color = Color(1.0, 0.5, 0.0, 0.8)
	flame.size = Vector2(20, 30)
	flame.position = Vector2(-10, -40)
	add_child(flame)
	
	var tween = create_tween()
	tween.tween_property(flame, "modulate:a", 0.0, 0.5)
	tween.tween_callback(flame.queue_free)
