extends "res://addons/gut/GutTest.gd"

## Unit tests for Round Management
## Tests round state, win conditions, and match flow

class MockRoundManager:
	extends RefCounted
	
	signal round_started(round_number)
	signal round_ended(winner_team, win_reason)
	signal match_ended(final_winner)
	
	# Round state
	var current_round: int = 0
	var max_rounds: int = 24
	var rounds_to_win: int = 13
	
	# Scores
	var team_scores: Dictionary = {0: 0, 1: 0}
	
	# Round state
	var round_in_progress: bool = false
	var round_timer: float = 0.0
	var round_duration: float = 100.0  # Seconds
	
	# Player states
	var alive_players: Dictionary = {0: 5, 1: 5}
	var bomb_planted: bool = false
	var bomb_site: String = ""
	var bomb_timer: float = 0.0
	var bomb_explode_time: float = 45.0
	
	# Match state
	var match_in_progress: bool = false
	var match_winner: int = -1
	
	func start_match():
		match_in_progress = true
		current_round = 0
		team_scores = {0: 0, 1: 0}
		start_round()
	
	func start_round():
		current_round += 1
		round_in_progress = true
		round_timer = 0.0
		alive_players = {0: 5, 1: 5}
		bomb_planted = false
		bomb_timer = 0.0
		round_started.emit(current_round)
	
	func update(delta: float):
		if not round_in_progress:
			return
		
		round_timer += delta
		
		if bomb_planted:
			bomb_timer += delta
			if bomb_timer >= bomb_explode_time:
				end_round(0, "bomb_exploded")  # Attackers win
		elif round_timer >= round_duration:
			end_round(1, "time_expired")  # Defenders win
	
	func kill_player(team: int):
		if alive_players[team] > 0:
			alive_players[team] -= 1
			_check_round_end()
	
	func plant_bomb(site: String):
		if not bomb_planted:
			bomb_planted = true
			bomb_site = site
			bomb_timer = 0.0
	
	func defuse_bomb():
		if bomb_planted:
			end_round(1, "bomb_defused")
	
	func _check_round_end():
		if alive_players[0] == 0:
			end_round(1, "elimination")
		elif alive_players[1] == 0 and not bomb_planted:
			end_round(0, "elimination")
	
	func end_round(winner: int, reason: String):
		round_in_progress = false
		team_scores[winner] += 1
		round_ended.emit(winner, reason)
		
		_check_match_end()
	
	func _check_match_end():
		if team_scores[0] >= rounds_to_win:
			match_winner = 0
			match_in_progress = false
			match_ended.emit(0)
		elif team_scores[1] >= rounds_to_win:
			match_winner = 1
			match_in_progress = false
			match_ended.emit(1)
		elif current_round >= max_rounds:
			# Overtime or tie
			if team_scores[0] != team_scores[1]:
				match_winner = 0 if team_scores[0] > team_scores[1] else 1
				match_ended.emit(match_winner)
	
	func get_score(team: int) -> int:
		return team_scores[team]
	
	func get_round_winner() -> int:
		return match_winner

var round_manager: MockRoundManager
var round_end_calls: Array = []
var match_end_calls: Array = []

func before_each():
	round_manager = MockRoundManager.new()
	round_end_calls = []
	match_end_calls = []
	
	round_manager.round_ended.connect(func(winner, reason): 
		round_end_calls.append({"winner": winner, "reason": reason}))
	round_manager.match_ended.connect(func(winner):
		match_end_calls.append(winner))

func after_each():
	round_manager = null

func test_initial_state():
	assert_eq(round_manager.current_round, 0, "Should start at round 0")
	assert_eq(round_manager.team_scores[0], 0, "TEAM_A should have 0 score")
	assert_eq(round_manager.team_scores[1], 0, "TEAM_B should have 0 score")
	assert_false(round_manager.round_in_progress, "Round should not be in progress")

func test_start_match():
	round_manager.start_match()
	
	assert_true(round_manager.match_in_progress, "Match should be in progress")
	assert_eq(round_manager.current_round, 1, "Should start at round 1")
	assert_true(round_manager.round_in_progress, "Round should be in progress")

func test_kill_player():
	round_manager.start_match()
	round_manager.kill_player(0)
	
	assert_eq(round_manager.alive_players[0], 4, "TEAM_A should have 4 alive")
	assert_eq(round_manager.alive_players[1], 5, "TEAM_B should still have 5 alive")

func test_round_end_by_elimination():
	round_manager.start_match()
	
	# Kill all TEAM_A players
	for i in range(5):
		round_manager.kill_player(0)
	
	assert_eq(round_end_calls.size(), 1, "Round should have ended")
	assert_eq(round_end_calls[0].winner, 1, "TEAM_B should win")
	assert_eq(round_end_calls[0].reason, "elimination", "Win reason should be elimination")

func test_bomb_plant():
	round_manager.start_match()
	round_manager.plant_bomb("A")
	
	assert_true(round_manager.bomb_planted, "Bomb should be planted")
	assert_eq(round_manager.bomb_site, "A", "Site should be A")

func test_bomb_explosion():
	round_manager.start_match()
	round_manager.plant_bomb("A")
	round_manager.update(50.0)  # Past bomb timer
	
	assert_eq(round_end_calls.size(), 1, "Round should have ended")
	assert_eq(round_end_calls[0].winner, 0, "Attackers (TEAM_A) should win")
	assert_eq(round_end_calls[0].reason, "bomb_exploded", "Win reason should be bomb")

func test_bomb_defuse():
	round_manager.start_match()
	round_manager.plant_bomb("A")
	round_manager.defuse_bomb()
	
	assert_eq(round_end_calls.size(), 1, "Round should have ended")
	assert_eq(round_end_calls[0].winner, 1, "Defenders (TEAM_B) should win")
	assert_eq(round_end_calls[0].reason, "bomb_defused", "Win reason should be defuse")

func test_time_expired():
	round_manager.start_match()
	round_manager.update(110.0)  # Past round timer
	
	assert_eq(round_end_calls.size(), 1, "Round should have ended")
	assert_eq(round_end_calls[0].winner, 1, "Defenders should win on time")
	assert_eq(round_end_calls[0].reason, "time_expired", "Win reason should be time")

func test_match_win_by_rounds():
	round_manager.start_match()
	
	# TEAM_A wins 13 rounds
	for i in range(13):
		round_manager.start_round() if i > 0 else null
		# Kill all TEAM_B players (but bomb not planted, so attackers need elim)
		for j in range(5):
			round_manager.kill_player(1)
		if i < 12:
			round_manager.start_round()
	
	assert_eq(match_end_calls.size(), 1, "Match should have ended")
	assert_eq(match_end_calls[0], 0, "TEAM_A should win match")
	assert_false(round_manager.match_in_progress, "Match should not be in progress")

func test_score_tracking():
	round_manager.start_match()
	
	# Win a round for TEAM_A
	for i in range(5):
		round_manager.kill_player(1)
	
	assert_eq(round_manager.get_score(0), 1, "TEAM_A should have 1 point")
	assert_eq(round_manager.get_score(1), 0, "TEAM_B should have 0 points")

func test_round_counter():
	round_manager.start_match()
	
	for i in range(5):
		round_manager.start_round() if i > 0 else null
		for j in range(5):
			round_manager.kill_player(1)
		if i < 4:
			round_manager.start_round()
	
	assert_eq(round_manager.current_round, 5, "Should be on round 5")
