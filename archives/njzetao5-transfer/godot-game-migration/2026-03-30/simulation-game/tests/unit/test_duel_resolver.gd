extends "res://addons/gut/GutTest.gd"

## Unit tests for DuelResolver
## Tests duel mechanics, LOD determination, and win probability calculations

var duel_resolver: DuelResolver
var mock_context: DuelContext
var mock_map: MapData

func before_each():
	duel_resolver = DuelResolver.new()
	mock_map = MapData.new()
	mock_map.bounds = Rect2(0, 0, 100, 100)
	
	duel_resolver.set_map(mock_map)
	duel_resolver.set_seed(12345)
	
	# Create mock duel context
	mock_context = DuelContext.new()

func after_each():
	duel_resolver = null
	mock_context = null

func test_duel_resolver_initialization():
	assert_not_null(duel_resolver, "Duel resolver should be initialized")
	assert_not_null(duel_resolver.raycast_engine, "Raycast engine should exist")
	assert_not_null(duel_resolver.ttk_engine, "TTK engine should exist")

func test_seed_setting():
	duel_resolver.set_seed(99999)
	assert_eq(duel_resolver.raycast_engine.rng.seed, 99999, 
		"Raycast engine RNG should be set")
	assert_eq(duel_resolver.ttk_engine.rng.seed, 99999,
		"TTK engine RNG should be set")

func test_viewport_setting():
	var viewport = Rect2(10, 10, 50, 50)
	duel_resolver.set_spectator_viewport(viewport)
	assert_eq(duel_resolver.spectator_viewport, viewport,
		"Viewport should be set correctly")

func test_lod_determination_in_viewport():
	duel_resolver.spectator_viewport = Rect2(0, 0, 100, 100)
	
	# Setup context with positions inside viewport
	mock_context.shooter_state = DuelContext.PlayerState.new()
	mock_context.shooter_state.pos = Vector2(50, 50)
	mock_context.target_state = DuelContext.PlayerState.new()
	mock_context.target_state.pos = Vector2(60, 60)
	
	var lod = duel_resolver._determine_lod(mock_context, 5, 5)
	
	assert_eq(lod, DuelResolver.LODLevel.HIGH,
		"Duel in viewport should get HIGH LOD")

func test_lod_determination_outside_viewport():
	duel_resolver.spectator_viewport = Rect2(0, 0, 50, 50)
	
	# Setup context with positions outside viewport
	mock_context.shooter_state = DuelContext.PlayerState.new()
	mock_context.shooter_state.pos = Vector2(80, 80)
	mock_context.target_state = DuelContext.PlayerState.new()
	mock_context.target_state.pos = Vector2(90, 90)
	
	var lod = duel_resolver._determine_lod(mock_context, 5, 5)
	
	# Outside viewport, not clutch, should get LOW LOD
	assert_eq(lod, DuelResolver.LODLevel.LOW,
		"Duel outside viewport should get LOW LOD")

func test_lod_determination_clutch_situation():
	duel_resolver.spectator_viewport = Rect2(0, 0, 50, 50)
	
	# Setup context outside viewport but with clutch situation
	mock_context.shooter_state = DuelContext.PlayerState.new()
	mock_context.shooter_state.pos = Vector2(80, 80)
	mock_context.target_state = DuelContext.PlayerState.new()
	mock_context.target_state.pos = Vector2(90, 90)
	
	# Only 1 vs 1 left - clutch situation
	var lod = duel_resolver._determine_lod(mock_context, 1, 1)
	
	assert_eq(lod, DuelResolver.LODLevel.HIGH,
		"Clutch situation should get HIGH LOD regardless of viewport")

func test_is_clutch_detection():
	# Threshold is 2 players
	assert_true(duel_resolver._is_clutch(1, 5), "1 vs 5 should be clutch")
	assert_true(duel_resolver._is_clutch(2, 5), "2 vs 5 should be clutch")
	assert_false(duel_resolver._is_clutch(3, 5), "3 vs 5 should not be clutch")
	assert_true(duel_resolver._is_clutch(5, 1), "5 vs 1 should be clutch")
	assert_false(duel_resolver._is_clutch(5, 3), "5 vs 3 should not be clutch")

func test_round_impact_calculation():
	# Early round - many players
	var early_impact = duel_resolver._estimate_round_impact(mock_context, 5, 5)
	
	# Late round - few players
	var late_impact = duel_resolver._estimate_round_impact(mock_context, 1, 1)
	
	assert_gt(late_impact, early_impact,
		"Late round should have higher impact")
	assert_eq(late_impact, 1.0, "1v1 should have maximum impact")

func test_resolve_duel_returns_valid_result():
	# Setup basic context
	mock_context.shooter_state = DuelContext.PlayerState.new()
	mock_context.shooter_state.id = 1
	mock_context.shooter_state.pos = Vector2(0, 0)
	mock_context.shooter_state.hp = 100
	mock_context.shooter_state.accuracy = 0.5
	
	mock_context.target_state = DuelContext.PlayerState.new()
	mock_context.target_state.id = 2
	mock_context.target_state.pos = Vector2(20, 0)
	mock_context.target_state.hp = 100
	mock_context.target_state.reaction_time = 0.2
	
	var result = duel_resolver.resolve_duel(mock_context, 5, 5)
	
	assert_not_null(result, "Result should not be null")
	assert_has(result, "winner_id", "Result should have winner_id")
	assert_has(result, "ttk", "Result should have ttk")
	assert_has(result, "hits", "Result should have hits")

func test_batch_resolution():
	var contexts = []
	for i in range(5):
		var ctx = DuelContext.new()
		ctx.shooter_state = DuelContext.PlayerState.new()
		ctx.shooter_state.pos = Vector2(i * 10, 0)
		ctx.target_state = DuelContext.PlayerState.new()
		ctx.target_state.pos = Vector2(i * 10 + 5, 0)
		contexts.append(ctx)
	
	var results = duel_resolver.resolve_batch(contexts, 5, 5)
	
	assert_eq(results.size(), 5, "Should return result for each context")
	for result in results:
		assert_not_null(result, "Each result should not be null")

func test_quick_compare():
	var ctx_a = DuelContext.new()
	ctx_a.shooter_state = DuelContext.PlayerState.new()
	ctx_a.shooter_state.accuracy = 0.8
	
	var ctx_b = DuelContext.new()
	ctx_b.shooter_state = DuelContext.PlayerState.new()
	ctx_b.shooter_state.accuracy = 0.3
	
	var comparison = duel_resolver.quick_compare(ctx_a, ctx_b)
	
	# A should win due to higher accuracy
	assert_eq(comparison, 1, "Higher accuracy should predict win")

func test_quick_compare_similar():
	var ctx_a = DuelContext.new()
	ctx_a.shooter_state = DuelContext.PlayerState.new()
	ctx_a.shooter_state.accuracy = 0.51
	
	var ctx_b = DuelContext.new()
	ctx_b.shooter_state = DuelContext.PlayerState.new()
	ctx_b.shooter_state.accuracy = 0.50
	
	var comparison = duel_resolver.quick_compare(ctx_a, ctx_b)
	
	# Too close to call
	assert_eq(comparison, 0, "Similar accuracy should be uncertain")
