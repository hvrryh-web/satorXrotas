extends "res://addons/gut/GutTest.gd"

## Unit tests for Economy Simulation
## Tests buy system, money management, and round win/loss economics

class MockEconomySystem:
	extends RefCounted
	
	var team_money: Dictionary = {0: 4000, 1: 4000}  # TEAM_A, TEAM_B
	var player_money: Dictionary = {}
	var team_loadouts: Dictionary = {0: {}, 1: {}}
	
	const STARTING_MONEY = 4000
	const MAX_MONEY = 16000
	const WIN_REWARD = 3000
	const LOSS_REWARD_BASE = 1900
	const LOSS_BONUS_INCREMENT = 500
	const MAX_LOSS_BONUS = 3400
	
	var loss_streak: Dictionary = {0: 0, 1: 0}
	
	func reset():
		team_money = {0: STARTING_MONEY, 1: STARTING_MONEY}
		loss_streak = {0: 0, 1: 0}
		player_money.clear()
		team_loadouts = {0: {}, 1: {}}
	
	func get_loss_reward(team: int) -> int:
		var streak = min(loss_streak[team], 4)
		return LOSS_REWARD_BASE + (streak * LOSS_BONUS_INCREMENT)
	
	func award_round_win(winner_team: int, loser_team: int):
		# Winner gets win reward
		add_money(winner_team, WIN_REWARD)
		
		# Loser gets loss reward based on streak
		var loss_reward = get_loss_reward(loser_team)
		add_money(loser_team, loss_reward)
		
		# Update streaks
		loss_streak[winner_team] = 0
		loss_streak[loser_team] += 1
	
	func add_money(team: int, amount: int):
		team_money[team] = min(team_money[team] + amount, MAX_MONEY)
	
	func spend_money(team: int, amount: int) -> bool:
		if team_money[team] >= amount:
			team_money[team] -= amount
			return true
		return false
	
	func can_afford(team: int, cost: int) -> bool:
		return team_money[team] >= cost
	
	func get_buy_recommendation(team: int, round_number: int) -> String:
		var money = team_money[team]
		
		if money >= 4500:
			return "full_buy"
		elif money >= 3500:
			return "rifle_buy"
		elif money >= 2100:
			return "force_buy"
		elif money >= 1500:
			return "eco_with_util"
		else:
			return "full_eco"

var economy: MockEconomySystem

func before_each():
	economy = MockEconomySystem.new()

func after_each():
	economy = null

func test_initial_money():
	assert_eq(economy.team_money[0], 4000, "TEAM_A should start with $4000")
	assert_eq(economy.team_money[1], 4000, "TEAM_B should start with $4000")

func test_win_reward():
	var initial_money = economy.team_money[0]
	economy.award_round_win(0, 1)  # TEAM_A wins
	
	assert_eq(economy.team_money[0], initial_money + economy.WIN_REWARD,
		"Winning team should get $3000")

func test_loss_streak_progression():
	# Team 1 loses 4 rounds in a row
	for i in range(4):
		var prev_money = economy.team_money[1]
		economy.award_round_win(0, 1)
		
		var expected_reward = economy.LOSS_REWARD_BASE + (i * economy.LOSS_BONUS_INCREMENT)
		assert_eq(economy.team_money[1], prev_money + expected_reward,
			"Loss reward should increase with streak")

func test_max_loss_bonus():
	# Team 1 loses many rounds
	for i in range(10):
		economy.award_round_win(0, 1)
	
	var max_expected = economy.LOSS_REWARD_BASE + (4 * economy.LOSS_BONUS_INCREMENT)
	var actual_reward = economy.get_loss_reward(1)
	
	assert_eq(actual_reward, max_expected,
		"Loss reward should cap at $3400")

func test_money_cap():
	# Give team a lot of money
	economy.team_money[0] = 15000
	economy.add_money(0, 5000)
	
	assert_eq(economy.team_money[0], economy.MAX_MONEY,
		"Money should cap at $16000")

func test_spend_money_success():
	economy.team_money[0] = 5000
	var result = economy.spend_money(0, 3000)
	
	assert_true(result, "Should return true when purchase succeeds")
	assert_eq(economy.team_money[0], 2000, "Money should be deducted")

func test_spend_money_failure():
	economy.team_money[0] = 1000
	var result = economy.spend_money(0, 3000)
	
	assert_false(result, "Should return false when can't afford")
	assert_eq(economy.team_money[0], 1000, "Money should not change")

func test_can_afford():
	economy.team_money[0] = 3000
	
	assert_true(economy.can_afford(0, 2000), "Should afford cheaper item")
	assert_true(economy.can_afford(0, 3000), "Should afford exact cost")
	assert_false(economy.can_afford(0, 4000), "Should not afford expensive item")

func test_buy_recommendation_full_buy():
	economy.team_money[0] = 5000
	var rec = economy.get_buy_recommendation(0, 5)
	assert_eq(rec, "full_buy", "$5000 should be full buy")

func test_buy_recommendation_force_buy():
	economy.team_money[0] = 2500
	var rec = economy.get_buy_recommendation(0, 5)
	assert_eq(rec, "force_buy", "$2500 should be force buy")

func test_buy_recommendation_eco():
	economy.team_money[0] = 1000
	var rec = economy.get_buy_recommendation(0, 5)
	assert_eq(rec, "full_eco", "$1000 should be full eco")

func test_reset_between_matches():
	# Modify state
	economy.team_money[0] = 15000
	economy.loss_streak[0] = 5
	
	economy.reset()
	
	assert_eq(economy.team_money[0], economy.STARTING_MONEY,
		"Money should reset to starting amount")
	assert_eq(economy.loss_streak[0], 0,
		"Loss streak should reset to 0")
