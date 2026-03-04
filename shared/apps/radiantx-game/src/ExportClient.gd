class_name ExportClient
extends Node

## HTTP client wrapper for SATOR API calls
## Handles retry logic with exponential backoff and offline queueing

signal request_completed(success: bool, response: Dictionary)
signal queue_flushed()

# Configuration
@export var api_endpoint: String = ""
@export var api_key: String = ""
@export var request_timeout: float = 30.0
@export var max_retries: int = 3
@export var base_retry_delay: float = 1.0
@export var max_retry_delay: float = 60.0

# HTTPRequest node for async HTTP calls
var _http_request: HTTPRequest

# Offline queue for failed requests
var _offline_queue: Array[Dictionary] = []
var _is_processing_queue: bool = false

# Retry tracking
var _current_retries: int = 0
var _pending_request: Dictionary = {}

func _ready():
	# Create HTTPRequest node
	_http_request = HTTPRequest.new()
	_http_request.timeout = request_timeout
	_add_child_http_request()
	_http_request.request_completed.connect(_on_request_completed)

func _add_child_http_request():
	# Helper to add HTTPRequest as child (can be overridden in tests)
	add_child(_http_request)

## Set API configuration at runtime
func configure(endpoint: String, key: String) -> void:
	api_endpoint = endpoint
	api_key = key

## Send match data to API with automatic retry logic
func send_match_data(payload: Dictionary) -> bool:
	if api_endpoint.is_empty():
		push_warning("ExportClient: API endpoint not configured, queuing for offline mode")
		_queue_offline(payload)
		return false
	
	# Reset retry counter for new request
	_current_retries = 0
	_pending_request = payload.duplicate(true)
	
	return _execute_request(payload)

## Execute HTTP request
func _execute_request(payload: Dictionary) -> bool:
	var headers = PackedStringArray([
		"Content-Type: application/json",
		"Authorization: Bearer " + api_key
	])
	
	var body = JSON.stringify(payload)
	var error = _http_request.request(api_endpoint, headers, HTTPClient.METHOD_POST, body)
	
	if error != OK:
		push_error("ExportClient: Failed to start HTTP request, error code: " + str(error))
		_handle_request_failure()
		return false
	
	return true

## Handle HTTP response
func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	var success = result == HTTPRequest.RESULT_SUCCESS and response_code >= 200 and response_code < 300
	
	if success:
		var response_text = body.get_string_from_utf8()
		var response_data = {}
		
		if not response_text.is_empty():
			var json = JSON.new()
			var parse_error = json.parse(response_text)
			if parse_error == OK:
				response_data = json.data
		
		_current_retries = 0
		_pending_request.clear()
		request_completed.emit(true, response_data)
		
		# Try to flush any queued requests
		_process_offline_queue()
	else:
		push_warning("ExportClient: Request failed with result=" + str(result) + ", code=" + str(response_code))
		_handle_request_failure()

## Handle request failure with retry logic
func _handle_request_failure() -> void:
	if _current_retries < max_retries:
		_current_retries += 1
		var delay = _calculate_retry_delay(_current_retries)
		push_warning("ExportClient: Retrying request (attempt " + str(_current_retries) + "/" + str(max_retries) + ") after " + str(delay) + "s")
		
		# Use create_timer through the scene tree
		if is_inside_tree():
			await get_tree().create_timer(delay).timeout
			_execute_request(_pending_request)
	else:
		push_error("ExportClient: Max retries exceeded, queuing for later")
		_queue_offline(_pending_request.duplicate(true))
		_pending_request.clear()
		_current_retries = 0
		request_completed.emit(false, {"error": "Max retries exceeded, queued for offline mode"})

## Calculate exponential backoff delay with jitter
func _calculate_retry_delay(attempt: int) -> float:
	# Exponential backoff: base_delay * 2^(attempt-1)
	var delay = base_retry_delay * pow(2, attempt - 1)
	# Add jitter (0-1 second random)
	if is_inside_tree():
		delay += randf()
	# Clamp to max delay
	return minf(delay, max_retry_delay)

## Queue a request for offline mode
func _queue_offline(payload: Dictionary) -> void:
	_offline_queue.append({
		"timestamp": Time.get_unix_time_from_system(),
		"payload": payload.duplicate(true)
	})
	push_info("ExportClient: Request queued for offline mode. Queue size: " + str(_offline_queue.size()))

## Process offline queue
func _process_offline_queue() -> void:
	if _is_processing_queue or _offline_queue.is_empty():
		return
	
	if api_endpoint.is_empty():
		return  # Still offline
	
	_is_processing_queue = true
	
	while not _offline_queue.is_empty() and is_inside_tree():
		var queued_item = _offline_queue.pop_front()
		var success = await _send_queued_item(queued_item.payload)
		
		if not success:
			# Put back at front of queue and stop processing
			_offline_queue.push_front(queued_item)
			break
		
		# Small delay between queued requests to avoid overwhelming the API
		await get_tree().create_timer(0.5).timeout
	
	_is_processing_queue = false
	queue_flushed.emit()

## Send a queued item (helper for async processing)
func _send_queued_item(payload: Dictionary) -> bool:
	var completed = false
	var success = false
	
	var on_complete = func(s: bool, _r: Dictionary):
		completed = true
		success = s
	
	request_completed.connect(on_complete, CONNECT_ONE_SHOT)
	_execute_request(payload)
	
	while not completed and is_inside_tree():
		await get_tree().process_frame
	
	return success

## Get current queue size
func get_queue_size() -> int:
	return _offline_queue.size()

## Check if currently offline (queue not empty or no endpoint)
func is_offline() -> bool:
	return not _offline_queue.is_empty() or api_endpoint.is_empty()

## Clear the offline queue (use with caution)
func clear_queue() -> void:
	_offline_queue.clear()

## Get queue contents (for debugging/persistence)
func get_queue_contents() -> Array[Dictionary]:
	return _offline_queue.duplicate(true)

## Restore queue from saved data (e.g., after game restart)
func restore_queue(saved_queue: Array) -> void:
	_offline_queue.clear()
	for item in saved_queue:
		if item is Dictionary and item.has("payload"):
			_offline_queue.append(item)

## Helper to push info messages (can be overridden in tests)
func push_info(message: String) -> void:
	print(message)
