class_name LiveSeasonModule
extends Node

## PURPOSE: Extract match statistics and export to SATOR API
## This is the PRIMARY enforcement point for data partition firewall
##
## This module ensures GAME_ONLY_FIELDS never reach the web platform:
## - internalAgentState — AI decision tree
## - radarData — Real-time position feed
## - detailedReplayFrameData — Per-tick simulation frames
## - simulationTick — Engine internal counter
## - seedValue — RNG seed
## - visionConeData — Agent vision state
## - smokeTickData — Smoke utility state
## - recoilPattern — Per-weapon recoil data

# Signals
signal match_exported(success: bool, match_id: String)
signal sanitization_failed(field_name: String)

# Configuration
@export var api_endpoint: String = ""
@export var api_key: String = ""
@export var auto_export: bool = false
@export var debug_mode: bool = false

# GAME-ONLY Fields that must NEVER be exported (mirrors FantasyDataFilter.GAME_ONLY_FIELDS)
const GAME_ONLY_FIELDS: Array[String] = [
	"internalAgentState",
	"radarData",
	"detailedReplayFrameData",
	"simulationTick",
	"seedValue",
	"visionConeData",
	"smokeTickData",
	"recoilPattern",
]

# Safe fields that CAN be exported to web
const SAFE_PLAYER_FIELDS: Array[String] = [
	"playerId",
	"playerName",
	"username",
	"team",
	"agentId",
	"role",
	"kills",
	"deaths",
	"assists",
	"damage",
	"headshots",
	"headshotPercentage",
	"utilityDamage",
	"firstKills",
	"firstDeaths",
	"clutchesWon",
	"clutchesLost",
	"kast",
	"adr",
	"kpr",
	"survivalRate",
	"roundsPlayed",
	"roundsWon",
	"roundsLost",
]

const SAFE_MATCH_FIELDS: Array[String] = [
	"matchId",
	"mapName",
	"startedAt",
	"endedAt",
	"winnerSide",
	"roundsPlayed",
	"duration",
	"teamAScore",
	"teamBScore",
]

# Internal state
var _match_data: Dictionary = {}
var _export_queue: Array = []
var _export_client: ExportClient = null
var _event_log_connection: Dictionary = {}

func _ready():
	_setup_export_client()

## Initialize the export client
func _setup_export_client() -> void:
	_export_client = ExportClient.new()
	_export_client.name = "ExportClient"
	_export_client.configure(api_endpoint, api_key)
	_export_client.request_completed.connect(_on_export_completed)
	add_child(_export_client)

## Called by MatchEngine when match ends
func record_match_end(match_result: Dictionary) -> void:
	if debug_mode:
		print("LiveSeasonModule: Recording match end")
	
	# Build match summary from match result
	_match_data = _build_match_data(match_result)
	
	# Validate no game-only fields are present
	if not _validate_no_game_only_fields(_match_data):
		push_error("LiveSeasonModule: FIREWALL VIOLATION - Game-only fields detected in match data!")
		match_exported.emit(false, "")
		return
	
	# Auto-export if enabled
	if auto_export:
		_export_current_match()

## Build comprehensive match data from match result
func _build_match_data(match_result: Dictionary) -> Dictionary:
	var match_data = {
		"matchId": _generate_match_id(),
		"exportedAt": Time.get_datetime_string_from_system(true),
		"version": "1.0.0",
	}
	
	# Extract match metadata
	_extract_match_metadata(match_data, match_result)
	
	# Extract player statistics
	var player_stats = _extract_all_player_stats(match_result)
	match_data["players"] = player_stats
	
	# Extract team statistics
	_extract_team_stats(match_data, match_result, player_stats)
	
	# Extract round summary (safe version, not detailed replay data)
	_extract_round_summary(match_data, match_result)
	
	return match_data

## Extract match metadata (safe fields only)
func _extract_match_metadata(match_data: Dictionary, match_result: Dictionary) -> void:
	# Copy safe match fields
	for field in SAFE_MATCH_FIELDS:
		if match_result.has(field):
			match_data[field] = match_result[field]
	
	# Handle various possible field names for map
	if match_result.has("map"):
		match_data["mapName"] = match_result.map
	elif match_result.has("mapName"):
		match_data["mapName"] = match_result.mapName
	elif match_result.has("map_data") and match_result.map_data is Dictionary:
		match_data["mapName"] = match_result.map_data.get("name", "unknown")
	
	# Handle winner field variations
	if match_result.has("winner"):
		var winner = match_result.winner
		if winner is String:
			match_data["winnerSide"] = winner
		elif winner is int:
			match_data["winnerSide"] = "team_a" if winner == 0 else "team_b"
	
	# Calculate duration from ticks if available
	if match_result.has("duration_ticks"):
		var ticks = match_result.duration_ticks
		match_data["duration"] = ticks / 20.0  # 20 TPS
	elif match_result.has("current_tick"):
		match_data["duration"] = match_result.current_tick / 20.0
	
	# Ensure required timestamps
	if not match_data.has("startedAt"):
		match_data["startedAt"] = Time.get_datetime_string_from_system(true)
	if not match_data.has("endedAt"):
		match_data["endedAt"] = Time.get_datetime_string_from_system(true)

## Extract player stats from all agents
func _extract_all_player_stats(match_result: Dictionary) -> Array[Dictionary]:
	var players: Array[Dictionary] = []
	
	# Get agents from match result
	var agents = match_result.get("agents", [])
	if agents.is_empty() and match_result.has("team_a") and match_result.has("team_b"):
		agents = match_result.team_a + match_result.team_b
	
	for agent in agents:
		if agent is Node or agent is Dictionary:
			var stats = _extract_player_stats(agent)
			if not stats.is_empty():
				players.append(stats)
	
	return players

## Extract player stats from agent (sanitize game-only fields)
func _extract_player_stats(agent) -> Dictionary:
	var stats: Dictionary = {}
	
	if agent is Node:
		# Extract from Agent node
		stats = _extract_from_agent_node(agent)
	elif agent is Dictionary:
		# Extract from dictionary data
		stats = _extract_from_agent_dict(agent)
	
	# Calculate derived stats
	_calculate_derived_stats(stats)
	
	# Sanitize to ensure only safe fields
	return _sanitize_player_stats(stats)

## Extract stats from Agent node
func _extract_from_agent_node(agent: Node) -> Dictionary:
	var stats = {}
	
	# Basic identity (safe fields only)
	stats["playerId"] = str(agent.get("agent_id", "unknown"))
	stats["playerName"] = agent.get("display_name", "Player " + str(agent.get("agent_id", "unknown")))
	stats["username"] = stats["playerName"]
	
	# Team assignment
	var team = agent.get("team", 0)
	if team is int:
		stats["team"] = "team_a" if team == 0 else "team_b"
	else:
		stats["team"] = str(team)
	
	# Agent/Role (from agent_def if available)
	var agent_def = agent.get("agent_def", null)
	if agent_def and agent_def is Dictionary:
		stats["agentId"] = agent_def.get("id", "unknown")
		stats["role"] = agent_def.get("role", "unknown")
	else:
		stats["agentId"] = "unknown"
		stats["role"] = "unknown"
	
	# Combat stats (safe to export)
	stats["kills"] = agent.get("kills", 0)
	stats["deaths"] = agent.get("deaths", 0)
	stats["assists"] = agent.get("assists", 0)
	stats["damage"] = agent.get("total_damage_dealt", agent.get("damage", 0))
	stats["headshots"] = agent.get("headshot_kills", agent.get("headshots", 0))
	stats["utilityDamage"] = agent.get("utility_damage", 0)
	
	# Performance stats
	stats["firstKills"] = agent.get("first_kills", 0)
	stats["firstDeaths"] = agent.get("first_deaths", 0)
	stats["clutchesWon"] = agent.get("clutches_won", 0)
	stats["clutchesLost"] = agent.get("clutches_lost", 0)
	
	# Round participation
	stats["roundsPlayed"] = agent.get("rounds_played", 1)
	
	return stats

## Extract stats from dictionary
func _extract_from_agent_dict(agent: Dictionary) -> Dictionary:
	var stats = {}
	
	# Copy safe fields
	for field in SAFE_PLAYER_FIELDS:
		if agent.has(field):
			stats[field] = agent[field]
	
	# Handle various field name mappings
	if agent.has("id") and not stats.has("playerId"):
		stats["playerId"] = str(agent.id)
	if agent.has("name") and not stats.has("playerName"):
		stats["playerName"] = agent.name
		stats["username"] = agent.name
	
	return stats

## Calculate derived statistics
func _calculate_derived_stats(stats: Dictionary) -> void:
	var kills = float(stats.get("kills", 0))
	var deaths = float(stats.get("deaths", 0))
	var damage = float(stats.get("damage", 0))
	var rounds = float(stats.get("roundsPlayed", 1))
	var headshots = float(stats.get("headshots", 0))
	
	# Headshot percentage
	if kills > 0:
		stats["headshotPercentage"] = (headshots / kills) * 100.0
	else:
		stats["headshotPercentage"] = 0.0
	
	# KAST (Kill, Assist, Survive, Trade) - simplified calculation
	# In a real implementation, this would track trades more carefully
	var survived = stats.get("survived_rounds", max(0, rounds - deaths))
	var kast_numerator = kills + stats.get("assists", 0) + survived
	stats["kast"] = (kast_numerator / rounds) * 100.0 if rounds > 0 else 0.0
	
	# ADR (Average Damage per Round)
	stats["adr"] = damage / rounds if rounds > 0 else 0.0
	
	# KPR (Kills per Round)
	stats["kpr"] = kills / rounds if rounds > 0 else 0.0
	
	# Survival rate
	stats["survivalRate"] = (survived / rounds) * 100.0 if rounds > 0 else 0.0

## Sanitize player stats - keep only safe fields
func _sanitize_player_stats(stats: Dictionary) -> Dictionary:
	var sanitized = {}
	
	for field in SAFE_PLAYER_FIELDS:
		if stats.has(field):
			sanitized[field] = stats[field]
	
	return sanitized

## Extract team statistics
func _extract_team_stats(match_data: Dictionary, match_result: Dictionary, player_stats: Array[Dictionary]) -> void:
	var team_a_wins = 0
	var team_b_wins = 0
	
	# Count from player stats
	for player in player_stats:
		var team = player.get("team", "")
		var rounds_won = player.get("roundsWon", 0)
		
		if team == "team_a":
			team_a_wins = max(team_a_wins, rounds_won)
		elif team == "team_b":
			team_b_wins = max(team_b_wins, rounds_won)
	
	# Override from match result if available
	if match_result.has("team_a_score"):
		team_a_wins = match_result.team_a_score
	if match_result.has("team_b_score"):
		team_b_wins = match_result.team_b_score
	
	match_data["teamAScore"] = team_a_wins
	match_data["teamBScore"] = team_b_wins
	match_data["roundsPlayed"] = team_a_wins + team_b_wins

## Extract round summary (safe data only, NOT detailed replay frames)
func _extract_round_summary(match_data: Dictionary, match_result: Dictionary) -> void:
	var rounds = match_result.get("rounds", [])
	var round_summaries = []
	
	for round_data in rounds:
		if round_data is Dictionary:
			# Only extract safe summary data
			var summary = {
				"roundNumber": round_data.get("round_number", round_summaries.size() + 1),
				"winner": round_data.get("winner", "unknown"),
				"winMethod": round_data.get("win_method", "unknown"),
			}
			
			# Include score at end of round (safe)
			if round_data.has("team_a_score") and round_data.has("team_b_score"):
				summary["scoreAtEnd"] = {
					"teamA": round_data.team_a_score,
					"teamB": round_data.team_b_score
				}
			
			round_summaries.append(summary)
	
	# Only store summary, NOT detailed frame data
	match_data["rounds"] = round_summaries

## Sanitize data - remove GAME_ONLY_FIELDS recursively
func _sanitize_for_web(data: Dictionary) -> Dictionary:
	var sanitized = data.duplicate(true)
	_remove_game_only_fields_recursive(sanitized)
	return sanitized

## Recursively remove game-only fields from dictionary
func _remove_game_only_fields_recursive(data) -> void:
	if data is Dictionary:
		for field in GAME_ONLY_FIELDS:
			if data.has(field):
				data.erase(field)
				if debug_mode:
					print("LiveSeasonModule: Removed game-only field: " + field)
		
		# Recurse into nested dictionaries
		for key in data.keys():
			if data[key] is Dictionary or data[key] is Array:
				_remove_game_only_fields_recursive(data[key])
	
	elif data is Array:
		for item in data:
			_remove_game_only_fields_recursive(item)

## Validate that no game-only fields are present
func _validate_no_game_only_fields(data) -> bool:
	if data is Dictionary:
		for field in GAME_ONLY_FIELDS:
			if data.has(field):
				sanitization_failed.emit(field)
				return false
		
		# Check nested structures
		for key in data.keys():
			if data[key] is Dictionary or data[key] is Array:
				if not _validate_no_game_only_fields(data[key]):
					return false
	
	elif data is Array:
		for item in data:
			if not _validate_no_game_only_fields(item):
				return false
	
	return true

## Export to API (with retry logic via ExportClient)
func _export_to_api(payload: Dictionary) -> bool:
	if _export_client == null:
		push_error("LiveSeasonModule: Export client not initialized")
		return false
	
	# Final sanitization pass
	var sanitized_payload = _sanitize_for_web(payload)
	
	if debug_mode:
		print("LiveSeasonModule: Exporting match data: " + JSON.stringify(sanitized_payload).substr(0, 200) + "...")
	
	return _export_client.send_match_data(sanitized_payload)

## Export the currently recorded match
func export_current_match() -> bool:
	return _export_current_match()

func _export_current_match() -> bool:
	if _match_data.is_empty():
		push_warning("LiveSeasonModule: No match data to export")
		return false
	
	return _export_to_api(_match_data)

## Handle export completion
func _on_export_completed(success: bool, response: Dictionary) -> void:
	var match_id = _match_data.get("matchId", "")
	match_exported.emit(success, match_id)
	
	if success:
		if debug_mode:
			print("LiveSeasonModule: Successfully exported match " + match_id)
	else:
		push_warning("LiveSeasonModule: Failed to export match " + match_id)

## Generate match summary for local storage
func generate_match_summary() -> Dictionary:
	if _match_data.is_empty():
		return {}
	
	# Return a copy of the sanitized match data
	return _sanitize_for_web(_match_data)

## Get raw match data (for testing/debugging only)
func get_match_data() -> Dictionary:
	return _match_data.duplicate(true)

## Get queue status
func get_export_status() -> Dictionary:
	return {
		"matchDataReady": not _match_data.is_empty(),
		"offlineQueueSize": _export_client.get_queue_size() if _export_client else 0,
		"isOffline": _export_client.is_offline() if _export_client else true,
		"apiEndpointConfigured": not api_endpoint.is_empty(),
	}

## Configure API settings at runtime
func configure(endpoint: String, key: String, auto: bool = false) -> void:
	api_endpoint = endpoint
	api_key = key
	auto_export = auto
	
	if _export_client:
		_export_client.configure(endpoint, key)

## Connect to EventLog for event stream processing
func connect_to_event_log(event_log: Node) -> void:
	# Store reference for potential future use
	_event_log_connection["connected"] = true
	_event_log_connection["event_log"] = event_log
	
	if debug_mode:
		print("LiveSeasonModule: Connected to EventLog")

## Process events from EventLog (for real-time updates if needed)
func process_event_stream(event_log: Node) -> void:
	# This method can be extended for real-time stat tracking
	# For now, we only process at match end
	pass

## Generate a unique match ID
func _generate_match_id() -> String:
	var timestamp = Time.get_unix_time_from_system()
	var random_suffix = randi() % 10000
	return "match_%d_%04d" % [timestamp, random_suffix]

## Save match data to local file (fallback)
func save_to_file(file_path: String) -> bool:
	if _match_data.is_empty():
		push_warning("LiveSeasonModule: No match data to save")
		return false
	
	var file = FileAccess.open(file_path, FileAccess.WRITE)
	if not file:
		push_error("LiveSeasonModule: Failed to open file for writing: " + file_path)
		return false
	
	var sanitized = _sanitize_for_web(_match_data)
	file.store_string(JSON.stringify(sanitized, "\t"))
	file.close()
	
	if debug_mode:
		print("LiveSeasonModule: Saved match data to: " + file_path)
	
	return true
