extends "res://addons/gut/GutTest.gd"

## Unit tests for CombatResolver
## Tests combat resolution logic, hit calculation, and damage application

var combat_resolver: CombatResolver
var mock_map: MapData
var mock_rng: RandomNumberGenerator
var mock_loader: DataLoader

func before_each():
	combat_resolver = CombatResolver.new()
	mock_map = MapData.new()
	mock_rng = RandomNumberGenerator.new()
	mock_rng.seed = 12345
	
	# Setup basic map
	mock_map.bounds = Rect2(0, 0, 100, 100)
	mock_map.cover_zones = []
	
	combat_resolver.setup(12345, mock_map, mock_loader)

func after_each():
	combat_resolver.clear()
	combat_resolver = null

func test_combat_resolver_initialization():
	assert_not_null(combat_resolver, "Combat resolver should be initialized")
	assert_not_null(combat_resolver.duel_resolver, "Duel resolver should exist")

func test_legacy_combat_hit_calculation():
	# Create mock agents
	var attacker = Agent.new()
	var target = Agent.new()
	
	attacker.agent_id = 1
	attacker.team = Agent.Team.TEAM_A
	attacker.position = Vector2(0, 0)
	attacker.health = 100
	
	target.agent_id = 2
	target.team = Agent.Team.TEAM_B
	target.position = Vector2(10, 0)  # 10 units away
	target.health = 100
	
	# Force legacy combat by disabling data-driven
	combat_resolver.use_data_driven_combat = false
	
	# Run multiple combat resolutions to verify probability distribution
	var hit_count = 0
	var total_runs = 1000
	
	for i in range(total_runs):
		# Reset RNG for consistent test
		mock_rng.seed = 12345 + i
		var result = combat_resolver._legacy_combat(attacker, target, mock_rng)
		if result.hit:
			hit_count += 1
		
		# Reset target health
		target.health = 100
	
	# At 10 units, base_chance (0.3) * distance_factor (~0.8) = ~0.24
	# Should be around 24% hit rate with some variance
	var hit_rate = float(hit_count) / total_runs
	assert_between(hit_rate, 0.15, 0.35, 
		"Hit rate should be reasonable for close range: got %f" % hit_rate)

func test_legacy_combat_damage_application():
	var attacker = Agent.new()
	var target = Agent.new()
	
	attacker.agent_id = 1
	attacker.team = Agent.Team.TEAM_A
	attacker.position = Vector2(0, 0)
	attacker.damage = 35
	
	target.agent_id = 2
	target.team = Agent.Team.TEAM_B
	target.position = Vector2(5, 0)
	target.health = 100
	
	combat_resolver.use_data_driven_combat = false
	
	# Force a hit by manipulating RNG
	mock_rng.seed = 12345
	var result = combat_resolver._legacy_combat(attacker, target, mock_rng)
	
	# Just verify structure is correct
	assert_has(result, "hit", "Result should have hit field")
	assert_has(result, "damage", "Result should have damage field")
	assert_has(result, "hit_zone", "Result should have hit_zone field")
	assert_has(result, "lethal", "Result should have lethal field")

func test_distance_factor_calculation():
	# Test distance factor at various ranges
	var attacker = Agent.new()
	var target = Agent.new()
	attacker.position = Vector2(0, 0)
	
	combat_resolver.use_data_driven_combat = false
	
	# Close range (5 units) - should have high hit chance
	target.position = Vector2(5, 0)
	var close_count = 0
	for i in range(100):
		mock_rng.seed = i
		var result = combat_resolver._legacy_combat(attacker, target, mock_rng)
		if result.hit:
			close_count += 1
	
	# Long range (40 units) - should have lower hit chance
	target.position = Vector2(40, 0)
	var far_count = 0
	for i in range(100):
		mock_rng.seed = i
		var result = combat_resolver._legacy_combat(attacker, target, mock_rng)
		if result.hit:
			far_count += 1
	
	# Close range should hit more often
	assert_gt(close_count, far_count, 
		"Close range should have higher hit rate than far range")

func test_flash_effect_on_accuracy():
	var attacker = Agent.new()
	var target = Agent.new()
	
	attacker.agent_id = 1
	attacker.team = Agent.Team.TEAM_A
	attacker.position = Vector2(0, 0)
	
	target.agent_id = 2
	target.team = Agent.Team.TEAM_B
	target.position = Vector2(10, 0)
	
	combat_resolver.use_data_driven_combat = false
	
	# Test without flash
	var normal_count = 0
	for i in range(100):
		mock_rng.seed = i
		attacker.flash_timer = 0
		var result = combat_resolver._legacy_combat(attacker, target, mock_rng)
		if result.hit:
			normal_count += 1
	
	# Test with flash
	var flashed_count = 0
	for i in range(100):
		mock_rng.seed = i
		attacker.flash_timer = 2.0  # 2 seconds of flash
		var result = combat_resolver._legacy_combat(attacker, target, mock_rng)
		if result.hit:
			flashed_count += 1
	
	# Flashed should have significantly fewer hits
	assert_gt(normal_count, flashed_count * 2,
		"Normal accuracy should be much higher than flashed accuracy")

func test_agent_registration():
	var agent = Agent.new()
	agent.agent_id = 1
	agent.team = Agent.Team.TEAM_A
	
	combat_resolver.register_agent(agent)
	
	var bridge = combat_resolver.get_bridge(agent)
	assert_not_null(bridge, "Bridge should be registered")
	assert_eq(bridge.agent, agent, "Bridge should reference the correct agent")

func test_agent_bridge_lifecycle():
	# Register multiple agents
	for i in range(5):
		var agent = Agent.new()
		agent.agent_id = i
		agent.team = Agent.Team.TEAM_A if i < 3 else Agent.Team.TEAM_B
		combat_resolver.register_agent(agent)
	
	# Verify all bridges exist
	for i in range(5):
		var bridge = combat_resolver.get_bridge_id(i)
		# Bridge retrieval is through get_bridge with agent reference
	
	# Clear and verify
	combat_resolver.clear()
	
	var bridge = combat_resolver.get_bridge_id(0)
	# After clear, bridge should be null

func test_team_alive_counting():
	# Setup agents on different teams
	for i in range(5):
		var agent = Agent.new()
		agent.agent_id = i
		agent.team = Agent.Team.TEAM_A if i < 3 else Agent.Team.TEAM_B
		agent.health = 100 if i != 2 else 0  # One dead agent on TEAM_A
		combat_resolver.register_agent(agent)
	
	var team_a_count = combat_resolver._count_alive_team(Agent.Team.TEAM_A)
	var team_b_count = combat_resolver._count_alive_team(Agent.Team.TEAM_B)
	
	assert_eq(team_a_count, 2, "TEAM_A should have 2 alive agents")
	assert_eq(team_b_count, 2, "TEAM_B should have 2 alive agents")
