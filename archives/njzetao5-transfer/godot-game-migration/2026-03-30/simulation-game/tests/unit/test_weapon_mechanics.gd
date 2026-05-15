extends "res://addons/gut/GutTest.gd"

## Unit tests for Weapon Mechanics
## Tests weapon firing, reloading, damage calculation, and recoil

class MockWeapon:
	extends RefCounted
	
	# Weapon stats
	var name: String = "Phantom"
	var damage: int = 35
	var fire_rate: float = 0.1  # Seconds between shots
	var magazine_size: int = 30
	var ammo_in_mag: int = 30
	var reserve_ammo: int = 90
	var reload_time: float = 2.5
	
	# State
	var is_reloading: bool = false
	var last_fire_time: float = 0.0
	var current_time: float = 0.0
	
	# Accuracy
	var base_accuracy: float = 0.9
	var moving_accuracy_penalty: float = 0.2
	var jumping_accuracy_penalty: float = 0.5
	
	func update(delta: float):
		current_time += delta
		
		if is_reloading and current_time >= last_fire_time + reload_time:
			_finish_reload()
	
	func can_fire() -> bool:
		if is_reloading:
			return false
		if ammo_in_mag <= 0:
			return false
		if current_time - last_fire_time < fire_rate:
			return false
		return true
	
	func fire() -> bool:
		if not can_fire():
			return false
		
		ammo_in_mag -= 1
		last_fire_time = current_time
		return true
	
	func start_reload():
		if is_reloading or ammo_in_mag == magazine_size:
			return
		is_reloading = true
		last_fire_time = current_time
	
	func _finish_reload():
		var needed = magazine_size - ammo_in_mag
		var available = min(needed, reserve_ammo)
		
		ammo_in_mag += available
		reserve_ammo -= available
		is_reloading = false
	
	func cancel_reload():
		is_reloading = false
	
	func get_accuracy(is_moving: bool, is_jumping: bool) -> float:
		var accuracy = base_accuracy
		if is_moving:
			accuracy -= moving_accuracy_penalty
		if is_jumping:
			accuracy -= jumping_accuracy_penalty
		return max(accuracy, 0.1)
	
	func get_damage(distance: float) -> int:
		# Simple damage falloff
		if distance < 15:
			return damage
		elif distance < 30:
			return int(damage * 0.9)
		elif distance < 50:
			return int(damage * 0.8)
		else:
			return int(damage * 0.7)

var weapon: MockWeapon

func before_each():
	weapon = MockWeapon.new()

func after_each():
	weapon = null

func test_initial_ammo():
	assert_eq(weapon.ammo_in_mag, 30, "Magazine should be full")
	assert_eq(weapon.reserve_ammo, 90, "Reserve should be at max")

func test_can_fire_with_ammo():
	assert_true(weapon.can_fire(), "Should be able to fire with ammo")

func test_can_fire_empty_mag():
	weapon.ammo_in_mag = 0
	assert_false(weapon.can_fire(), "Should not fire with empty mag")

func test_can_fire_during_reload():
	weapon.start_reload()
	assert_false(weapon.can_fire(), "Should not fire during reload")

func test_fire_decrements_ammo():
	var initial = weapon.ammo_in_mag
	weapon.fire()
	assert_eq(weapon.ammo_in_mag, initial - 1, "Ammo should decrease by 1")

func test_fire_rate_limiting():
	weapon.fire()
	assert_false(weapon.can_fire(), "Should not fire faster than fire rate")
	
	# Advance time past fire rate
	weapon.current_time = weapon.fire_rate + 0.01
	assert_true(weapon.can_fire(), "Should fire after fire rate interval")

func test_reload_transfers_ammo():
	weapon.ammo_in_mag = 10
	weapon.reserve_ammo = 90
	
	weapon.start_reload()
	weapon.update(3.0)  # Past reload time
	
	assert_eq(weapon.ammo_in_mag, 30, "Magazine should be full")
	assert_eq(weapon.reserve_ammo, 70, "Reserve should decrease by 20")

func test_reload_partial_reserve():
	weapon.ammo_in_mag = 25
	weapon.reserve_ammo = 3
	
	weapon.start_reload()
	weapon.update(3.0)
	
	assert_eq(weapon.ammo_in_mag, 28, "Should only reload available ammo")
	assert_eq(weapon.reserve_ammo, 0, "Reserve should be empty")

func test_reload_not_needed_full_mag():
	weapon.ammo_in_mag = 30
	weapon.start_reload()
	assert_false(weapon.is_reloading, "Should not reload if mag is full")

func test_cancel_reload():
	weapon.ammo_in_mag = 10
	weapon.start_reload()
	weapon.cancel_reload()
	
	assert_eq(weapon.ammo_in_mag, 10, "Ammo should not change")
	assert_false(weapon.is_reloading, "Should not be reloading")

func test_accuracy_stationary():
	var acc = weapon.get_accuracy(false, false)
	assert_eq(acc, weapon.base_accuracy, "Stationary should have base accuracy")

func test_accuracy_moving():
	var stationary = weapon.get_accuracy(false, false)
	var moving = weapon.get_accuracy(true, false)
	
	assert_lt(moving, stationary, "Moving should reduce accuracy")

func test_accuracy_jumping():
	var stationary = weapon.get_accuracy(false, false)
	var jumping = weapon.get_accuracy(false, true)
	
	assert_lt(jumping, stationary, "Jumping should reduce accuracy")

func test_accuracy_minimum():
	# Even with all penalties, accuracy should have minimum
	var acc = weapon.get_accuracy(true, true)
	assert_gte(acc, 0.1, "Accuracy should have minimum floor")

func test_damage_close_range():
	var dmg = weapon.get_damage(10)
	assert_eq(dmg, 35, "Close range should have full damage")

func test_damage_long_range():
	var close = weapon.get_damage(10)
	var far = weapon.get_damage(60)
	
	assert_lt(far, close, "Long range should have reduced damage")

func test_damage_falloff_tiers():
	var tier1 = weapon.get_damage(10)   # < 15
	var tier2 = weapon.get_damage(20)   # 15-30
	var tier3 = weapon.get_damage(40)   # 30-50
	var tier4 = weapon.get_damage(60)   # > 50
	
	assert_eq(tier1, 35, "Tier 1 should be full damage")
	assert_eq(tier2, 31, "Tier 2 should be 90%")
	assert_eq(tier3, 28, "Tier 3 should be 80%")
	assert_eq(tier4, 24, "Tier 4 should be 70%")
