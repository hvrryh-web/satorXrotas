extends Node3D
class_name Viewer3D

## 3D/2.5D holographic viewer for enhanced replays/match views
## NJZ materialized physics-ready animations

@export var agent_mesh: MeshInstance3D
@export var map_material: StandardMaterial3D
@export var holographic_shader: ShaderMaterial

var agents_3d: Dictionary = {}  # agent_id -> Node3D
var camera_3d: Camera3D
var physics_world: PhysicsWorld3D

# Metrics tracking
var metric_tracker: Dictionary = {
	'spatial_fps': [],
	'agent_positions': [],
	'combat_events': 0,
	'utility_deployed': 0
}

func _ready():
	setup_3d_scene()
	
func setup_3d_scene():
	camera_3d = Camera3D.new()
	camera_3d.position = Vector3(0, 20, 30)
	camera_3d.look_at(Vector3.ZERO)
	add_child(camera_3d)
	
	# Holographic material
	map_material = StandardMaterial3D.new()
	map_material.albedo_color = Color(0.05, 0.05, 0.1)
	map_material.emission_enabled = true
	map_material.emission = Color(0.2, 0.3, 0.8, 0.5)
	map_material.emission_energy = 0.5
	add_child(MeshInstance3D.new().set_material_override(map_material))
	
	# Physics
	physics_world = PhysicsWorld3D.new()
	add_child(physics_world)

func add_agent_3d(agent_id: int, pos: Vector3):
	var agent_node = RigidBody3D.new()
	agent_node.position = pos
	agent_node.linear_damp = 0.8  # Materialized feel
	agent_node.angular_damp = 0.9
	
	var mesh = MeshInstance3D.new()
	mesh.mesh = SphereMesh.new()
	mesh.mesh.radius = 0.5
	mesh.material_override = holographic_shader  # Holo effect
	agent_node.add_child(mesh)
	
	add_child(agent_node)
	agents_3d[agent_id] = agent_node

func update_metrics(tick: int, event: String):
	metric_tracker.combat_events += 1 if 'combat' in event else 0
	metric_tracker.spatial_fps.append(Engine.get_frames_per_second())
	if metric_tracker.spatial_fps.size() > 1000:
		metric_tracker.spatial_fps.pop_front()

func _physics_process(delta):
	# Physics for materialized holograms
	for agent_node in agents_3d.values():
		agent_node.apply_central_force(Vector3.UP * 9.81 * agent_node.mass * delta)  # Gravity sim
