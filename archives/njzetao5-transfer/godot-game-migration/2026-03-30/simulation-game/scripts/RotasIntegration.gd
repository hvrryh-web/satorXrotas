extends Node
class_name RotasIntegration

## ROTAS proprietary analysis/formulas integration
## Offline simple, online advanced w/webhooks

signal analysis_ready(data: Dictionary)

var offline_formulas: Dictionary = {
	'kd_expected': 'kills / (deaths + 1)',
	'headshot_rate': 'headshots / shots * 100',
	'eco_efficiency': 'rounds_won_no_buy / eco_rounds'
}

var online_endpoint: String = 'https://sator-api.onrender.com/api/rotas'
var is_online: bool = false

func _ready():
	check_online_status()

func check_online_status():
	is_online = ProjectSettings.get_setting('application/config/online_mode', false)
	
func get_analysis(match_data: Dictionary) -> Dictionary:
	if is_online:
		return await _fetch_online_analysis(match_data)
	else:
		return _compute_offline_analysis(match_data)

func _compute_offline_analysis(data: Dictionary) -> Dictionary:
	var analysis = {}
	for formula in offline_formulas:
		analysis[formula] = _eval_formula(offline_formulas[formula], data)
	return analysis

func _fetch_online_analysis(data: Dictionary) -> Dictionary:
	# Webhook to SATOR for advanced stats
	var http = HTTPRequest.new()
	add_child(http)
	
	var body = JSON.stringify(data)
	var error = http.request(online_endpoint, [], HTTPClient.METHOD_POST, body)
	if error != OK:
		return _compute_offline_analysis(data)  # Fallback
	
	# Await response (simplified)
	await http.request_completed
	var response = http.get_parsed_result()
	return response.body if response.success else {}

func _eval_formula(formula: String, data: Dictionary) -> float:
	# Simple eval (secure in production)
	match formula:
		'kd_expected': return float(data.get('kills', 0)) / max(1, data.get('deaths', 0))
		_: return 0.0

# Drill-down insights
func drill_down(player_id: int, metric: String):
	var query = {'player': player_id, 'metric': metric}
	get_analysis(query)

