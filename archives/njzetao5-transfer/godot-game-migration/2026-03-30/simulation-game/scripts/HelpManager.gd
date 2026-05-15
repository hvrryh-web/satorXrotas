extends CanvasLayer
class_name HelpManager

var current_tip: int = 0
var tips = [
	'Hint: Press Space to play/pause simulation',
	'NJZ Cog toggles SFX (top right)',
	'Use +/- for speed, arrows for timeline',
	'Save replays for analysis',
	'Switch to 3D viewer for holo replays'
]

@onready var tip_label: Label
@onready var next_button: Button

func _ready():
	tip_label = Label.new()
	tip_label.text = tips[0]
	tip_label.position = Vector2(50, 50)
	add_child(tip_label)
	
	next_button = Button.new()
	next_button.text = 'Next Tip (Esc)'
	next_button.position = Vector2(50, 100)
	next_button.pressed.connect(_next_tip)
	add_child(next_button)

func _input(event):
	if event.is_action_pressed('ui_cancel'):
		_next_tip()

func _next_tip():
	current_tip = (current_tip + 1) % tips.size()
	tip_label.text = tips[current_tip]

