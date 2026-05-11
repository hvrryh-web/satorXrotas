@tool
extends EditorPlugin

const GUT_SCENE = preload("res://addons/gut/GutScene.tscn")
const GUT_DOCK_SCENE = preload("res://addons/gut/GutDock.tscn")

var _gut = null
var _dock = null
var _panel = null

func _enter_tree():
	_dock = GUT_DOCK_SCENE.instantiate()
	_dock.name = "GUT"
	add_control_to_dock(DOCK_SLOT_LEFT_UL, _dock)
	
func _exit_tree():
	if _dock:
		remove_control_from_docks(_dock)
		_dock.queue_free()
		_dock = null

func has_main_screen():
	return true

func make_visible(visible):
	if _gut:
		_gut.visible = visible

func get_plugin_name():
	return "GUT"
