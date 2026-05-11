[Ver001.000]
## Lun Mascot - Lunar Owl Theme
## Moon-element mascot representing night, wisdom, and support

extends Mascot

func _init():
	mascot_name = "Lun"
	mascot_type = Type.LUN

func _ready():
	super._ready()
	## Lun-specific initialization
	modulate = Color(0.7, 0.8, 1.0, 1.0)  ## Cool blue glow

func _update_animations(delta: float):
	## Lun-specific animation updates - gentle floating
	if sprite and current_state == State.IDLE:
		var float_y = sin(Time.get_ticks_msec() * 0.002) * 2.0
		sprite.position.y = float_y

func trigger_moon_glow():
	## Lun-specific ability: moonlight aura
	trigger_reaction("moon_glow", {"intensity": 0.8})
	
	## Create moon glow effect
	var glow = ColorRect.new()
	glow.color = Color(0.6, 0.7, 1.0, 0.4)
	glow.size = Vector2(60, 60)
	glow.position = Vector2(-30, -50)
	add_child(glow)
	
	var tween = create_tween()
	tween.tween_property(glow, "modulate:a", 0.0, 1.0)
	tween.tween_callback(glow.queue_free)
