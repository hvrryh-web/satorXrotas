extends "res://addons/gut/GutTest.gd"

## Unit tests for Player Movement
## Tests movement mechanics, velocity, and collision

class MockMovementController:
	extends RefCounted
	
	var position: Vector2 = Vector2.ZERO
	var velocity: Vector2 = Vector2.ZERO
	var speed: float = 5.0
	var max_speed: float = 10.0
	var friction: float = 0.8
	var acceleration: float = 2.0
	
	# Movement states
	var is_moving: bool = false
	var is_crouching: bool = false
	var is_walking: bool = false
	
	# Speed multipliers
	const WALK_MULTIPLIER: float = 0.5
	const CROUCH_MULTIPLIER: float = 0.3
	const RUN_MULTIPLIER: float = 1.0
	
	func update(delta: float):
		# Apply velocity to position
		position += velocity * delta
		
		# Apply friction
		velocity *= friction
		
		# Stop if very slow
		if velocity.length() < 0.1:
			velocity = Vector2.ZERO
			is_moving = false
	
	func move(direction: Vector2, delta: float):
		if direction.length() > 1.0:
			direction = direction.normalized()
		
		var speed_mult = _get_speed_multiplier()
		var target_speed = max_speed * speed_mult
		
		# Accelerate towards target velocity
		var target_velocity = direction * target_speed
		velocity = velocity.lerp(target_velocity, acceleration * delta)
		
		is_moving = velocity.length() > 0.1
	
	func _get_speed_multiplier() -> float:
		if is_crouching:
			return CROUCH_MULTIPLIER
		elif is_walking:
			return WALK_MULTIPLIER
		else:
			return RUN_MULTIPLIER
	
	func set_crouch(crouch: bool):
		is_crouching = crouch
	
	func set_walk(walk: bool):
		is_walking = walk
	
	func get_current_speed() -> float:
		return velocity.length()
	
	func stop():
		velocity = Vector2.ZERO
		is_moving = false

var movement: MockMovementController

func before_each():
	movement = MockMovementController.new()

func after_each():
	movement = null

func test_initial_position():
	assert_eq(movement.position, Vector2.ZERO, "Initial position should be zero")

func test_initial_velocity():
	assert_eq(movement.velocity, Vector2.ZERO, "Initial velocity should be zero")

func test_move_in_direction():
	movement.move(Vector2.RIGHT, 1.0)
	movement.update(1.0)
	
	assert_gt(movement.position.x, 0, "Position should move right")
	assert_true(movement.is_moving, "Should be moving")

func test_move_normalization():
	# Move with unnormalized vector
	movement.move(Vector2(10, 0), 1.0)
	var speed = movement.get_current_speed()
	
	assert_lte(speed, movement.max_speed, 
		"Speed should not exceed max speed even with large input")

func test_crouch_speed_reduction():
	movement.set_crouch(true)
	movement.move(Vector2.RIGHT, 1.0)
	
	var crouch_speed = movement.get_current_speed()
	
	movement.stop()
	movement.set_crouch(false)
	movement.move(Vector2.RIGHT, 1.0)
	
	var run_speed = movement.get_current_speed()
	
	assert_lt(crouch_speed, run_speed,
		"Crouch speed should be less than run speed")

func test_walk_speed_reduction():
	movement.set_walk(true)
	movement.move(Vector2.RIGHT, 1.0)
	
	var walk_speed = movement.get_current_speed()
	
	movement.stop()
	movement.set_walk(false)
	movement.move(Vector2.RIGHT, 1.0)
	
	var run_speed = movement.get_current_speed()
	
	assert_lt(walk_speed, run_speed,
		"Walk speed should be less than run speed")

func test_friction_slows_movement():
	movement.move(Vector2.RIGHT, 1.0)
	var initial_speed = movement.get_current_speed()
	
	# Stop input and let friction work
	movement.update(1.0)
	movement.update(1.0)
	movement.update(1.0)
	
	var final_speed = movement.get_current_speed()
	
	assert_lt(final_speed, initial_speed,
		"Friction should slow down movement")

func test_stop_clears_velocity():
	movement.move(Vector2.RIGHT, 1.0)
	assert_gt(movement.get_current_speed(), 0, "Should be moving")
	
	movement.stop()
	
	assert_eq(movement.velocity, Vector2.ZERO, "Velocity should be zero")
	assert_false(movement.is_moving, "Should not be moving")

func test_diagonal_movement():
	movement.move(Vector2(1, 1), 1.0)
	
	var speed = movement.get_current_speed()
	assert_lte(speed, movement.max_speed,
		"Diagonal speed should not exceed max speed")

func test_position_update():
	var start_pos = Vector2(10, 20)
	movement.position = start_pos
	movement.velocity = Vector2(5, 0)
	
	movement.update(1.0)
	
	assert_eq(movement.position, Vector2(15, 20),
		"Position should update based on velocity")
