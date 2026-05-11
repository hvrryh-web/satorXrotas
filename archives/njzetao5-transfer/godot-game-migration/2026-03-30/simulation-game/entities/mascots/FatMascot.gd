[Ver001.000]
## Fat Mascot - Phoenix/Mythical Theme
## Fire-element mascot representing rebirth, resilience, and power

extends Mascot

func _init():
	mascot_name = "Fat"
	mascot_type = Type.FAT

func _ready():
	super._ready()
	## Fat-specific initialization
	modulate = Color(1.0, 0.4, 0.2, 1.0)  ## Fiery red-orange glow

func _update_animations(delta: float):
	## Fat-specific animation updates - ember particles
	if sprite and current_state == State.IDLE:
		if randf() < 0.05:  ## Occasional ember
			_create_ember()

func _create_ember():
	## Create floating ember particle
	var ember = ColorRect.new()
	ember.color = Color(1.0, 0.6, 0.0, 0.8)
	ember.size = Vector2(3, 3)
	ember.position = Vector2(randf_range(-15, 15), -20)
	add_child(ember)
	
	var tween = create_tween()
	tween.tween_property(ember, "position:y", -50, 1.0)
	tween.parallel().tween_property(ember, "modulate:a", 0, 1.0)
	tween.tween_callback(ember.queue_free)

func trigger_rebirth():
	## Fat-specific ability: phoenix rebirth celebration
	trigger_celebration()
	
	## Intense flame burst effect
	for i in range(8):
		var flame = ColorRect.new()
		flame.color = Color(1.0, randf_range(0.3, 0.7), 0.0, 0.9)
		flame.size = Vector2(randf_range(10, 20), randf_range(20, 40))
		var angle = (i / 8.0) * TAU
		flame.position = Vector2(cos(angle) * 20, sin(angle) * 20 - 30)
		add_child(flame)
		
		var tween = create_tween()
		tween.tween_property(flame, "position", flame.position * 2, 0.6)
		tween.parallel().tween_property(flame, "modulate:a", 0, 0.6)
		tween.tween_callback(flame.queue_free)
