[Ver001.000]
## Mascot Demo Scene Script
## Demonstrates mascot system functionality and provides interactive testing

extends Control

@onready var mascot_manager: MascotManager = $MascotManager
@onready var mascot_container: Node2D = %MascotContainer
@onready var info_text: Label = %InfoText
@onready var camera: Camera2D = %Camera2D

var mascot_camera: MascotCamera
var _mascot_types = [Mascot.Type.SOL, Mascot.Type.LUN, Mascot.Type.BIN, Mascot.Type.FAT, Mascot.Type.UNI]

func _ready():
	## Initialize mascot manager
	mascot_manager.auto_spawn_mascots = false
	
	## Create and setup mascot camera
	mascot_camera = MascotCamera.new()
	mascot_camera.position = camera.position
	add_child(mascot_camera)
	mascot_manager.setup_camera(mascot_camera)
	
	## Spawn all mascots
	_spawn_mascots()
	
	## Setup update timer
	var timer = Timer.new()
	timer.wait_time = 0.5
	timer.timeout.connect(_update_info)
	add_child(timer)
	timer.start()

func _spawn_mascots():
	## Spawn 5 mascots in a row
	var start_x = 200
	var spacing = 220
	
	for i in range(5):
		var pos = Vector2(start_x + i * spacing, 0)
		var mascot = mascot_manager.spawn_mascot(_mascot_types[i], pos)
		mascot_container.add_child(mascot)

func _input(event):
	## Camera focus keys (1-5)
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_1:
				_focus_mascot(0)
			KEY_2:
				_focus_mascot(1)
			KEY_3:
				_focus_mascot(2)
			KEY_4:
				_focus_mascot(3)
			KEY_5:
				_focus_mascot(4)
			KEY_C:
				mascot_manager.trigger_all_cheer(randf())
			KEY_R:
				_trigger_random_reactions()
			KEY_V:
				mascot_manager.celebrate_team_win(randi() % 2)
			KEY_SPACE:
				mascot_camera.cycle_to_next_mascot()
			KEY_ESCAPE:
				mascot_camera.return_to_default()

func _focus_mascot(index: int):
	var mascots = mascot_manager.get_mascots()
	if index < mascots.size():
		mascots[index].focus_camera()

func _trigger_random_reactions():
	var reactions = ["excited", "shocked", "happy", "surprised", "neutral"]
	for mascot in mascot_manager.get_mascots():
		var reaction = reactions[randi() % reactions.size()]
		mascot.trigger_reaction(reaction, {"intensity": randf()})

func _update_info():
	## Update performance info panel
	var report = mascot_manager.get_performance_report()
	var camera_info = mascot_camera.get_current_target_info()
	
	var text = "=== Performance ===\n"
	text += "Mascots: %d\n" % report.mascot_count
	text += "Render Time: %.2f ms\n" % (report.current_render_time_us / 1000.0)
	text += "Avg Time: %.2f ms\n" % (report.average_render_time_us / 1000.0)
	text += "Within Budget: %s\n\n" % ("Yes" if report.within_budget else "NO")
	
	text += "=== Camera ===\n"
	if camera_info.has_target:
		text += "Target: %s\n" % camera_info.mascot_name
		text += "State: %s\n" % camera_info.state
		text += "Render: %.2f ms\n" % camera_info.render_time_ms
	else:
		text += "Target: None (default view)\n"
	
	info_text.text = text
