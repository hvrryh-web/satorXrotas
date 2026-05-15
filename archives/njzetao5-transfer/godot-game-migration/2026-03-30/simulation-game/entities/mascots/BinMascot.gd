[Ver001.000]
## Bin Mascot - Binary Cyber Theme
## Tech-element mascot representing data, logic, and strategy

extends Mascot

func _init():
	mascot_name = "Bin"
	mascot_type = Type.BIN

func _ready():
	super._ready()
	## Bin-specific initialization
	modulate = Color(0.0, 1.0, 0.5, 1.0)  ## Matrix green glow

func _update_animations(delta: float):
	## Bin-specific animation updates - digital glitch effect
	if sprite and current_state == State.IDLE:
		if randf() < 0.02:  ## Occasional glitch
			sprite.position.x = randf_range(-1, 1)
		else:
			sprite.position.x = 0

func trigger_data_burst():
	## Bin-specific ability: data stream celebration
	trigger_reaction("data_burst", {"intensity": 1.0})
	
	## Create binary particles effect
	for i in range(5):
		var bit = Label.new()
		bit.text = "1" if randf() > 0.5 else "0"
		bit.modulate = Color(0, 1, 0.5, 1)
		bit.position = Vector2(randf_range(-20, 20), -30)
		add_child(bit)
		
		var tween = create_tween()
		tween.tween_property(bit, "position:y", -60, 0.5)
		tween.parallel().tween_property(bit, "modulate:a", 0, 0.5)
		tween.tween_callback(bit.queue_free)
