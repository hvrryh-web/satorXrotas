[Ver001.000]
## Unit tests for Mascot System
## Tests mascot state machine, animations, and performance

extends "res://addons/gut/GutTest.gd"

var mascot_manager: MascotManager
var test_mascot: Mascot

func before_each():
	mascot_manager = MascotManager.new()
	add_child_autofree(mascot_manager)

func after_each():
	mascot_manager = null
	test_mascot = null

## Mascot Base Class Tests

func test_mascot_initialization():
	var mascot = Mascot.new()
	mascot.mascot_name = "Test"
	mascot.mascot_type = Mascot.Type.SOL
	
	assert_eq(mascot.mascot_name, "Test", "Mascot name should be set")
	assert_eq(mascot.mascot_type, Mascot.Type.SOL, "Mascot type should be SOL")
	assert_eq(mascot.current_state, Mascot.State.IDLE, "Initial state should be IDLE")
	add_child_autofree(mascot)

func test_mascot_state_transitions():
	var mascot = Mascot.new()
	add_child_autofree(mascot)
	mascot._ready()
	
	## Test transition to CHEER
	mascot.transition_to(Mascot.State.CHEER)
	assert_eq(mascot.current_state, Mascot.State.CHEER, "Should transition to CHEER")
	
	## Test transition to REACT
	mascot.transition_to(Mascot.State.REACT, {"type": "test"})
	assert_eq(mascot.current_state, Mascot.State.REACT, "Should transition to REACT")
	
	## Test transition to CELEBRATE
	mascot.trigger_celebration()
	assert_eq(mascot.current_state, Mascot.State.CELEBRATE, "Should transition to CELEBRATE")

func test_mascot_state_serialization():
	var mascot = Mascot.new()
	mascot.mascot_name = "TestMascot"
	mascot.mascot_type = Mascot.Type.LUN
	mascot.position = Vector2(100, 200)
	
	var state = mascot.get_state()
	
	assert_eq(state.mascot_name, "TestMascot", "State should contain name")
	assert_eq(state.mascot_type, Mascot.Type.LUN, "State should contain type")
	assert_eq(state.position.x, 100, "State should contain X position")
	assert_eq(state.position.y, 200, "State should contain Y position")

func test_mascot_state_deserialization():
	var mascot = Mascot.new()
	var state = {
		"mascot_name": "Restored",
		"mascot_type": Mascot.Type.BIN,
		"current_state": Mascot.State.CHEER,
		"state_timer": 1.5,
		"position": {"x": 50, "y": 75},
		"animation_speed": 1.5
	}
	
	mascot.set_state(state)
	
	assert_eq(mascot.mascot_name, "Restored", "Name should be restored")
	assert_eq(mascot.mascot_type, Mascot.Type.BIN, "Type should be restored")
	assert_eq(mascot.current_state, Mascot.State.CHEER, "State should be restored")
	assert_eq(mascot.position, Vector2(50, 75), "Position should be restored")

## Individual Mascot Type Tests

func test_sol_mascot_creation():
	var sol = SolMascot.new()
	assert_eq(sol.mascot_name, "Sol", "Sol mascot should have correct name")
	assert_eq(sol.mascot_type, Mascot.Type.SOL, "Sol should have SOL type")
	add_child_autofree(sol)

func test_lun_mascot_creation():
	var lun = LunMascot.new()
	assert_eq(lun.mascot_name, "Lun", "Lun mascot should have correct name")
	assert_eq(lun.mascot_type, Mascot.Type.LUN, "Lun should have LUN type")
	add_child_autofree(lun)

func test_bin_mascot_creation():
	var bin = BinMascot.new()
	assert_eq(bin.mascot_name, "Bin", "Bin mascot should have correct name")
	assert_eq(bin.mascot_type, Mascot.Type.BIN, "Bin should have BIN type")
	add_child_autofree(bin)

func test_fat_mascot_creation():
	var fat = FatMascot.new()
	assert_eq(fat.mascot_name, "Fat", "Fat mascot should have correct name")
	assert_eq(fat.mascot_type, Mascot.Type.FAT, "Fat should have FAT type")
	add_child_autofree(fat)

func test_uni_mascot_creation():
	var uni = UniMascot.new()
	assert_eq(uni.mascot_name, "Uni", "Uni mascot should have correct name")
	assert_eq(uni.mascot_type, Mascot.Type.UNI, "Uni should have UNI type")
	add_child_autofree(uni)

## Mascot Manager Tests

func test_manager_spawn_mascot():
	var mascot = mascot_manager.spawn_mascot(Mascot.Type.SOL, Vector2(100, 100))
	assert_not_null(mascot, "Should spawn mascot")
	assert_eq(mascot.mascot_type, Mascot.Type.SOL, "Should spawn correct type")
	assert_eq(mascot.position, Vector2(100, 100), "Should set position")

func test_manager_get_mascot_by_type():
	mascot_manager.spawn_mascot(Mascot.Type.SOL, Vector2.ZERO)
	mascot_manager.spawn_mascot(Mascot.Type.LUN, Vector2.ZERO)
	
	var found = mascot_manager.get_mascot_by_type(Mascot.Type.SOL)
	assert_not_null(found, "Should find mascot by type")
	assert_eq(found.mascot_type, Mascot.Type.SOL, "Should find correct type")

func test_manager_get_mascot_by_name():
	mascot_manager.spawn_mascot(Mascot.Type.SOL, Vector2.ZERO)
	
	var found = mascot_manager.get_mascot_by_name("Sol")
	assert_not_null(found, "Should find mascot by name")
	assert_eq(found.mascot_name, "Sol", "Should find correct name")

func test_manager_spawn_all_mascots():
	mascot_manager.spawn_all_mascots()
	var mascots = mascot_manager.get_mascots()
	
	assert_eq(mascots.size(), 5, "Should spawn all 5 mascots")
	
	## Verify each type exists
	var types_found = []
	for m in mascots:
		types_found.append(m.mascot_type)
	
	assert_has(types_found, Mascot.Type.SOL, "Should have SOL")
	assert_has(types_found, Mascot.Type.LUN, "Should have LUN")
	assert_has(types_found, Mascot.Type.BIN, "Should have BIN")
	assert_has(types_found, Mascot.Type.FAT, "Should have FAT")
	assert_has(types_found, Mascot.Type.UNI, "Should have UNI")

func test_manager_trigger_all_cheer():
	mascot_manager.spawn_all_mascots()
	mascot_manager.trigger_all_cheer(1.0)
	
	for mascot in mascot_manager.get_mascots():
		assert_eq(mascot.current_state, Mascot.State.CHEER, "All should be cheering")

func test_manager_celebrate_team_win():
	mascot_manager.spawn_all_mascots()
	var mascots = mascot_manager.get_mascots()
	
	mascot_manager.celebrate_team_win(0)  ## Team A wins
	
	## Even indices (0, 2, 4) should celebrate, odd should be sad
	assert_eq(mascots[0].current_state, Mascot.State.CELEBRATE, "Team A mascot 0 should celebrate")
	assert_eq(mascots[1].current_state, Mascot.State.SAD, "Team B mascot 1 should be sad")

## Performance Tests

func test_mascot_performance_budget():
	var mascot = Mascot.new()
	add_child_autofree(mascot)
	
	## Run a few frames to get render time
	await get_tree().process_frame
	await get_tree().process_frame
	
	## Should be within budget (2000us = 2ms)
	assert_true(mascot.is_within_budget(), "Mascot should be within performance budget")

func test_manager_performance_report():
	mascot_manager.spawn_all_mascots()
	await get_tree().process_frame
	
	var report = mascot_manager.get_performance_report()
	
	assert_has(report, "mascot_count", "Report should have mascot_count")
	assert_has(report, "current_render_time_us", "Report should have render time")
	assert_has(report, "within_budget", "Report should have budget status")
	assert_eq(report.mascot_count, 5, "Should report 5 mascots")

func test_manager_is_performance_ok():
	mascot_manager.spawn_all_mascots()
	await get_tree().process_frame
	
	var ok = mascot_manager.is_performance_ok()
	## Just verify it returns a boolean
	assert_true(ok is bool, "is_performance_ok should return boolean")

## State Synchronization Tests

func test_manager_get_all_states():
	mascot_manager.spawn_all_mascots()
	
	var states = mascot_manager.get_all_states()
	assert_eq(states.size(), 5, "Should get 5 states")
	
	for state in states:
		assert_has(state, "mascot_name", "State should have name")
		assert_has(state, "mascot_type", "State should have type")

func test_manager_set_all_states():
	mascot_manager.spawn_all_mascots()
	
	var original_states = mascot_manager.get_all_states()
	
	## Modify and restore
	for state in original_states:
		state.current_state = Mascot.State.CHEER
	
	mascot_manager.set_all_states(original_states)
	
	for mascot in mascot_manager.get_mascots():
		assert_eq(mascot.current_state, Mascot.State.CHEER, "State should be restored")

## Signal Tests

func test_mascot_state_changed_signal():
	var mascot = Mascot.new()
	add_child_autofree(mascot)
	mascot._ready()
	
	var signal_received = false
	var received_state = -1
	
	mascot.state_changed.connect(func(new_state, old_state):
		signal_received = true
		received_state = new_state
	)
	
	mascot.transition_to(Mascot.State.CHEER)
	
	assert_true(signal_received, "Should emit state_changed signal")
	assert_eq(received_state, Mascot.State.CHEER, "Signal should have correct new state")

func test_manager_mascot_spawned_signal():
	var signal_received = false
	var spawned_mascot = null
	
	mascot_manager.mascot_spawned.connect(func(mascot):
		signal_received = true
		spawned_mascot = mascot
	)
	
	mascot_manager.spawn_mascot(Mascot.Type.SOL, Vector2.ZERO)
	
	assert_true(signal_received, "Should emit mascot_spawned signal")
	assert_not_null(spawned_mascot, "Signal should pass spawned mascot")
