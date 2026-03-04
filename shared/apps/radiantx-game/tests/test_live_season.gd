extends Node

## Unit tests for LiveSeasonModule
## Tests sanitization, data extraction, and firewall compliance

const LiveSeasonModule = preload("res://apps/radiantx-game/src/LiveSeasonModule.gd")
const ExportClient = preload("res://apps/radiantx-game/src/ExportClient.gd")

# Test state
var _test_results: Dictionary = {"passed": 0, "failed": 0, "tests": []}
var _current_module: LiveSeasonModule = null
var _mock_export_client: MockExportClient = null

# GAME-ONLY Fields that must be stripped (mirror of LiveSeasonModule.GAME_ONLY_FIELDS)
const GAME_ONLY_FIELDS = [
	"internalAgentState",
	"radarData",
	"detailedReplayFrameData",
	"simulationTick",
	"seedValue",
	"visionConeData",
	"smokeTickData",
	"recoilPattern",
]

func _ready():
	print("=== LiveSeasonModule Test Suite ===\n")
	
	# Run all tests
	await _run_all_tests()
	
	# Print summary
	_print_summary()
	
	# Exit with appropriate code
	var exit_code = 0 if _test_results.failed == 0 else 1
	get_tree().quit(exit_code)

func _run_all_tests():
	# Core sanitization tests
	await _test_sanitize_removes_game_only_fields()
	await _test_sanitize_preserves_safe_fields()
	await _test_sanitize_nested_dicts()
	await _test_sanitize_nested_arrays()
	
	# Firewall validation tests
	await _test_validate_detects_game_only_fields()
	await _test_validate_passes_for_clean_data()
	
	# Data extraction tests
	await _test_extract_player_stats_basic()
	await _test_extract_player_stats_from_node()
	await _test_calculate_derived_stats()
	
	# Match data building tests
	await _test_build_match_data_structure()
	await _test_match_data_contains_no_game_only()
	
	# Export client tests
	await _test_export_client_queue()
	await _test_export_client_retry_delay()
	
	# Integration tests
	await _test_full_match_export_flow()
	await _test_offline_mode_queueing()

# ============================================
# Sanitization Tests
# ============================================

func _test_sanitize_removes_game_only_fields():
	_test_start("sanitize_removes_game_only_fields")
	
	var module = _create_test_module()
	
	var dirty_data = {
		"kills": 10,
		"deaths": 5,
		"internalAgentState": {"ai_tree": "secret"},
		"radarData": [{"x": 1, "y": 2}],
		"seedValue": 12345,
		"playerName": "TestPlayer"
	}
	
	var sanitized = module._sanitize_for_web(dirty_data)
	
	# Check safe fields preserved
	_assert_equal(sanitized.get("kills"), 10, "Kills should be preserved")
	_assert_equal(sanitized.get("deaths"), 5, "Deaths should be preserved")
	_assert_equal(sanitized.get("playerName"), "TestPlayer", "Player name should be preserved")
	
	# Check game-only fields removed
	for field in GAME_ONLY_FIELDS:
		if dirty_data.has(field):
			_assert_false(sanitized.has(field), "Game-only field '" + field + "' should be removed")
	
	_test_end()
	await _wait_frame()

func _test_sanitize_preserves_safe_fields():
	_test_start("sanitize_preserves_safe_fields")
	
	var module = _create_test_module()
	
	var safe_data = {
		"playerId": "player_123",
		"username": "TestPlayer",
		"kills": 15,
		"deaths": 8,
		"assists": 3,
		"damage": 2400,
		"headshots": 5,
		"headshotPercentage": 33.3,
		"firstKills": 2,
		"clutchesWon": 1,
		"kast": 78.5,
		"adr": 150.0,
		"kpr": 0.75,
	}
	
	var sanitized = module._sanitize_for_web(safe_data)
	
	# All safe fields should be preserved
	for key in safe_data.keys():
		_assert_true(sanitized.has(key), "Safe field '" + key + "' should be preserved")
		_assert_equal(sanitized[key], safe_data[key], "Value for '" + key + "' should match")
	
	_test_end()
	await _wait_frame()

func _test_sanitize_nested_dicts():
	_test_start("sanitize_nested_dicts")
	
	var module = _create_test_module()
	
	var nested_data = {
		"matchId": "match_123",
		"players": [
			{
				"playerId": "p1",
				"kills": 10,
				"internalAgentState": "should_be_removed",
				"nested_stats": {
					"damage": 1000,
					"seedValue": 999,
					"radarData": [{"x": 1}]
				}
			}
		],
		"metadata": {
			"mapName": "TestMap",
			"simulationTick": 5000
		}
	}
	
	var sanitized = module._sanitize_for_web(nested_data)
	
	# Top level should be clean
	_assert_false(sanitized.has("internalAgentState"), "Top-level game field removed")
	
	# Nested in players
	var player = sanitized.players[0]
	_assert_false(player.has("internalAgentState"), "Player game field removed")
	_assert_true(player.has("kills"), "Player safe field preserved")
	
	# Deeply nested
	_assert_false(player.nested_stats.has("seedValue"), "Deeply nested seedValue removed")
	_assert_false(player.nested_stats.has("radarData"), "Deeply nested radarData removed")
	_assert_true(player.nested_stats.has("damage"), "Deeply nested damage preserved")
	
	# Metadata
	_assert_false(sanitized.metadata.has("simulationTick"), "Metadata simulationTick removed")
	_assert_true(sanitized.metadata.has("mapName"), "Metadata mapName preserved")
	
	_test_end()
	await _wait_frame()

func _test_sanitize_nested_arrays():
	_test_start("sanitize_nested_arrays")
	
	var module = _create_test_module()
	
	var data_with_arrays = {
		"rounds": [
			{
				"roundNumber": 1,
				"winner": "team_a",
				"detailedReplayFrameData": [{"tick": 1}]
			},
			{
				"roundNumber": 2,
				"winner": "team_b",
				"visionConeData": [{"angle": 90}]
			}
		],
		"events": [
			{"type": "kill", "simulationTick": 100},
			{"type": "death", "smokeTickData": [1, 2, 3]}
		]
	}
	
	var sanitized = module._sanitize_for_web(data_with_arrays)
	
	# Check rounds
	_assert_equal(sanitized.rounds.size(), 2, "Both rounds preserved")
	_assert_false(sanitized.rounds[0].has("detailedReplayFrameData"), "Round 1 replay data removed")
	_assert_false(sanitized.rounds[1].has("visionConeData"), "Round 2 vision data removed")
	_assert_true(sanitized.rounds[0].has("roundNumber"), "Round 1 number preserved")
	
	# Check events
	_assert_equal(sanitized.events.size(), 2, "Both events preserved")
	_assert_false(sanitized.events[0].has("simulationTick"), "Event 1 tick removed")
	_assert_false(sanitized.events[1].has("smokeTickData"), "Event 1 smoke data removed")
	_assert_true(sanitized.events[0].has("type"), "Event type preserved")
	
	_test_end()
	await _wait_frame()

# ============================================
# Firewall Validation Tests
# ============================================

func _test_validate_detects_game_only_fields():
	_test_start("validate_detects_game_only_fields")
	
	var module = _create_test_module()
	var signal_received = false
	var failed_field = ""
	
	module.sanitization_failed.connect(func(field):
		signal_received = true
		failed_field = field
	)
	
	var dirty_data = {
		"kills": 10,
		"internalAgentState": "secret"
	}
	
	var result = module._validate_no_game_only_fields(dirty_data)
	
	_assert_false(result, "Validation should fail for dirty data")
	_assert_true(signal_received, "Sanitization failed signal should be emitted")
	_assert_equal(failed_field, "internalAgentState", "Failed field should be reported")
	
	_test_end()
	await _wait_frame()

func _test_validate_passes_for_clean_data():
	_test_start("validate_passes_for_clean_data")
	
	var module = _create_test_module()
	var signal_received = false
	
	module.sanitization_failed.connect(func(_field):
		signal_received = true
	)
	
	var clean_data = {
		"kills": 10,
		"deaths": 5,
		"playerName": "Test",
		"nested": {
			"damage": 100,
			"headshots": 2
		}
	}
	
	var result = module._validate_no_game_only_fields(clean_data)
	
	_assert_true(result, "Validation should pass for clean data")
	_assert_false(signal_received, "No signal should be emitted for clean data")
	
	_test_end()
	await _wait_frame()

# ============================================
# Data Extraction Tests
# ============================================

func _test_extract_player_stats_basic():
	_test_start("extract_player_stats_basic")
	
	var module = _create_test_module()
	
	var agent_dict = {
		"id": 1,
		"name": "TestPlayer",
		"team": 0,
		"kills": 10,
		"deaths": 5,
		"assists": 3,
		"damage": 2000,
		"headshots": 3,
		"internalAgentState": "should_not_appear"
	}
	
	var stats = module._extract_player_stats(agent_dict)
	
	_assert_equal(stats.get("playerId"), "1", "Player ID extracted")
	_assert_equal(stats.get("username"), "TestPlayer", "Username extracted")
	_assert_equal(stats.get("kills"), 10, "Kills extracted")
	_assert_equal(stats.get("deaths"), 5, "Deaths extracted")
	_assert_false(stats.has("internalAgentState"), "Game-only field not in output")
	
	_test_end()
	await _wait_frame()

func _test_extract_player_stats_from_node():
	_test_start("extract_player_stats_from_node")
	
	var module = _create_test_module()
	
	# Create a mock agent node using a plain Node with meta data
	var mock_agent = Node.new()
	mock_agent.set("agent_id", 1)
	mock_agent.set("display_name", "MockPlayer")
	mock_agent.set("team", 0)
	mock_agent.set("kills", 15)
	mock_agent.set("deaths", 8)
	mock_agent.set("assists", 5)
	mock_agent.set("total_damage_dealt", 2500)
	mock_agent.set("headshot_kills", 5)
	
	var stats = module._extract_player_stats(mock_agent)
	
	_assert_equal(stats.get("playerId"), "1", "Node player ID extracted")
	_assert_equal(stats.get("kills"), 15, "Node kills extracted")
	_assert_equal(stats.get("damage"), 2500, "Node damage extracted")
	
	mock_agent.free()
	
	_test_end()
	await _wait_frame()

func _test_calculate_derived_stats():
	_test_start("calculate_derived_stats")
	
	var module = _create_test_module()
	
	var base_stats = {
		"kills": 10,
		"deaths": 5,
		"damage": 2000,
		"headshots": 3,
		"assists": 4,
		"roundsPlayed": 20,
	}
	
	module._calculate_derived_stats(base_stats)
	
	_assert_true(base_stats.has("headshotPercentage"), "HS% calculated")
	_assert_true(base_stats.has("adr"), "ADR calculated")
	_assert_true(base_stats.has("kpr"), "KPR calculated")
	
	_assert_approx_equal(base_stats.headshotPercentage, 30.0, 0.1, "HS% = 3/10 * 100")
	_assert_approx_equal(base_stats.adr, 100.0, 0.1, "ADR = 2000/20")
	_assert_approx_equal(base_stats.kpr, 0.5, 0.01, "KPR = 10/20")
	
	_test_end()
	await _wait_frame()

# ============================================
# Match Data Building Tests
# ============================================

func _test_build_match_data_structure():
	_test_start("build_match_data_structure")
	
	var module = _create_test_module()
	
	var match_result = {
		"map": "training_ground",
		"team_a_score": 13,
		"team_b_score": 10,
		"winner": "team_a",
		"agents": [
			{"id": 0, "name": "Player1", "team": 0, "kills": 20, "deaths": 10},
			{"id": 1, "name": "Player2", "team": 1, "kills": 15, "deaths": 15},
		]
	}
	
	var match_data = module._build_match_data(match_result)
	
	_assert_true(match_data.has("matchId"), "Has match ID")
	_assert_true(match_data.has("mapName"), "Has map name")
	_assert_true(match_data.has("players"), "Has players array")
	_assert_true(match_data.has("teamAScore"), "Has team A score")
	_assert_true(match_data.has("teamBScore"), "Has team B score")
	
	_assert_equal(match_data.get("mapName"), "training_ground", "Map name correct")
	_assert_equal(match_data.get("teamAScore"), 13, "Team A score correct")
	_assert_equal(match_data.players.size(), 2, "Two players in data")
	
	_test_end()
	await _wait_frame()

func _test_match_data_contains_no_game_only():
	_test_start("match_data_contains_no_game_only")
	
	var module = _create_test_module()
	module.debug_mode = true
	
	var match_result = {
		"map": "test_map",
		"seedValue": 12345,
		"simulationTick": 10000,
		"agents": [
			{
				"id": 0,
				"kills": 10,
				"internalAgentState": {"ai": "data"},
				"radarData": [{"x": 1}],
			}
		],
		"detailedReplayFrameData": [{"tick": 1}]
	}
	
	module.record_match_end(match_result)
	var match_data = module.get_match_data()
	
	# Verify all game-only fields are absent
	for field in GAME_ONLY_FIELDS:
		_assert_false(match_data.has(field), "Match data should not have: " + field)
	
	# Check nested in players
	if match_data.has("players") and match_data.players.size() > 0:
		var player = match_data.players[0]
		for field in GAME_ONLY_FIELDS:
			_assert_false(player.has(field), "Player should not have: " + field)
	
	_test_end()
	await _wait_frame()

# ============================================
# Export Client Tests
# ============================================

func _test_export_client_queue():
	_test_start("export_client_queue")
	
	var client = MockExportClient.new()
	add_child(client)
	
	_assert_equal(client.get_queue_size(), 0, "Queue starts empty")
	
	# Simulate offline by not configuring endpoint
	client._queue_offline({"test": "data"})
	
	_assert_equal(client.get_queue_size(), 1, "Item added to queue")
	_assert_true(client.is_offline(), "Client reports offline")
	
	client.clear_queue()
	_assert_equal(client.get_queue_size(), 0, "Queue cleared")
	
	client.free()
	
	_test_end()
	await _wait_frame()

func _test_export_client_retry_delay():
	_test_start("export_client_retry_delay")
	
	var client = MockExportClient.new()
	add_child(client)
	
	# Test exponential backoff calculation
	var delay1 = client._calculate_retry_delay(1)
	var delay2 = client._calculate_retry_delay(2)
	var delay3 = client._calculate_retry_delay(3)
	
	# Delays should increase (exponentially)
	_assert_true(delay2 > delay1, "Delay 2 > Delay 1")
	_assert_true(delay3 > delay2, "Delay 3 > Delay 2")
	
	# Should be capped at max
	var delay_high = client._calculate_retry_delay(10)
	_assert_true(delay_high <= client.max_retry_delay + 1.0, "Delay capped at max + jitter")
	
	client.free()
	
	_test_end()
	await _wait_frame()

# ============================================
# Integration Tests
# ============================================

func _test_full_match_export_flow():
	_test_start("full_match_export_flow")
	
	var module = _create_test_module()
	var mock_client = MockExportClient.new()
	
	# Replace the export client
	if module._export_client:
		module._export_client.free()
	module._export_client = mock_client
	add_child(mock_client)
	
	var export_completed = false
	var export_success = false
	
	module.match_exported.connect(func(success, _id):
		export_completed = true
		export_success = success
	)
	
	# Simulate match end
	var match_result = {
		"map": "integration_test_map",
		"team_a_score": 13,
		"team_b_score": 11,
		"winner": "team_a",
		"agents": [
			{"id": 0, "name": "P1", "team": 0, "kills": 25, "deaths": 12, "damage": 3000},
			{"id": 1, "name": "P2", "team": 1, "kills": 18, "deaths": 15, "damage": 2400},
		]
	}
	
	module.record_match_end(match_result)
	
	# Trigger export
	module.export_current_match()
	
	# Wait for async completion
	var timeout = 0.0
	while not export_completed and timeout < 2.0:
		timeout += 0.1
		await get_tree().create_timer(0.1).timeout
	
	# Check that data was sent to mock client
	_assert_true(mock_client.last_payload.has("mapName"), "Payload has map name")
	_assert_equal(mock_client.last_payload.get("mapName"), "integration_test_map", "Map name correct")
	
	mock_client.free()
	
	_test_end()
	await _wait_frame()

func _test_offline_mode_queueing():
	_test_start("offline_mode_queueing")
	
	var module = _create_test_module()
	module.api_endpoint = ""  # Force offline
	
	var mock_client = MockExportClient.new()
	if module._export_client:
		module._export_client.free()
	module._export_client = mock_client
	add_child(mock_client)
	
	var match_result = {
		"map": "offline_test",
		"agents": [{"id": 0, "name": "Test", "team": 0, "kills": 5, "deaths": 3}]
	}
	
	module.record_match_end(match_result)
	module.export_current_match()
	
	# Should be queued, not sent
	_assert_equal(mock_client.get_queue_size(), 1, "Request queued when offline")
	_assert_true(mock_client.last_payload.is_empty(), "No immediate request made")
	
	mock_client.free()
	
	_test_end()
	await _wait_frame()

# ============================================
# Helper Methods
# ============================================

func _create_test_module() -> LiveSeasonModule:
	if _current_module:
		_current_module.free()
	
	_current_module = LiveSeasonModule.new()
	_current_module.api_endpoint = "https://test.api.endpoint/matches"
	_current_module.api_key = "test_key"
	_current_module.debug_mode = false
	add_child(_current_module)
	
	return _current_module

func _test_start(name: String):
	print("  [RUNNING] " + name)
	_test_results.tests.append({"name": name, "status": "running", "assertions": []})

func _test_end():
	var test = _test_results.tests[_test_results.tests.size() - 1]
	if test.status == "running":
		test.status = "passed"
		_test_results.passed += 1
		print("    ✓ PASSED\n")

func _assert_true(condition: bool, message: String = ""):
	if not condition:
		_fail_test("Expected true but got false: " + message)

func _assert_false(condition: bool, message: String = ""):
	if condition:
		_fail_test("Expected false but got true: " + message)

func _assert_equal(actual, expected, message: String = ""):
	if actual != expected:
		_fail_test("Expected " + str(expected) + " but got " + str(actual) + ": " + message)

func _assert_approx_equal(actual: float, expected: float, tolerance: float, message: String = ""):
	if abs(actual - expected) > tolerance:
		_fail_test("Expected ~" + str(expected) + " but got " + str(actual) + " (tolerance: " + str(tolerance) + "): " + message)

func _fail_test(message: String):
	var test = _test_results.tests[_test_results.tests.size() - 1]
	test.status = "failed"
	test.error = message
	_test_results.failed += 1
	print("    ✗ FAILED: " + message)

func _wait_frame():
	await get_tree().process_frame

func _print_summary():
	print("\n=== Test Summary ===")
	print("Passed: " + str(_test_results.passed))
	print("Failed: " + str(_test_results.failed))
	print("Total:  " + str(_test_results.tests.size()))
	
	if _test_results.failed > 0:
		print("\nFailed tests:")
		for test in _test_results.tests:
			if test.status == "failed":
				print("  - " + test.name + ": " + test.get("error", "Unknown error"))
	
	print("")

# ============================================
# Mock Classes
# ============================================

class MockExportClient extends ExportClient:
	var last_payload: Dictionary = {}
	var should_succeed: bool = true
	var call_count: int = 0
	
	func _execute_request(payload: Dictionary) -> bool:
		last_payload = payload.duplicate(true)
		call_count += 1
		
		# Simulate async completion
		if is_inside_tree():
			_get_tree().create_timer(0.1).timeout.connect(func():
				request_completed.emit(should_succeed, {"mock": true})
			)
		
		return true
	
	func _add_child_http_request():
		# Don't add actual HTTPRequest in tests
		pass
	
	func push_info(_message: String) -> void:
		# Suppress logs in tests
		pass
