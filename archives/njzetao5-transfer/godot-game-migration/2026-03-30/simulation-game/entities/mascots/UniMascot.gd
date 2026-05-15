[Ver001.000]
## Uni Mascot - Unicorn/Fantasy Theme
## Magic-element mascot representing purity, hope, and unity

extends Mascot

func _init():
	mascot_name = "Uni"
	mascot_type = Type.UNI

func _ready():
	super._ready()
	## Uni-specific initialization
	modulate = Color(1.0, 0.8, 0.95, 1.0)  ## Soft pink glow

func _update_animations(delta: float):
	## Uni-specific animation updates - rainbow shimmer
	if sprite and current_state == State.IDLE:
		var shimmer = 0.9 + sin(Time.get_ticks_msec() * 0.005) * 0.1
		sprite.modulate.v = shimmer

func trigger_rainbow_trail():
	## Uni-specific ability: rainbow celebration
	trigger_celebration()
	
	## Create rainbow arc effect
	var colors = [Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE]
	
	for i in range(colors.size()):
		var arc = ColorRect.new()
		arc.color = colors[i]
		arc.color.a = 0.6
		arc.size = Vector2(8, 40)
		var angle = -PI + (i / float(colors.size() - 1)) * PI
		arc.position = Vector2(cos(angle) * 30, sin(angle) * 20 - 20)
		arc.rotation = angle + PI / 2
		add_child(arc)
		
		var tween = create_tween()
		tween.tween_property(arc, "modulate:a", 0, 1.0)
		tween.tween_callback(arc.queue_free)
