extends Node

## GUT-compatible test runner for Godot 4
## Discovers and runs all test files

const TEST_DIRS = [
	"res://tests/unit",
	"res://tests/integration"
]

var test_results: Dictionary = {
	"passed": 0,
	"failed": 0,
	"skipped": 0,
	"total": 0
}

func _ready():
	print("=== Godot Test Runner ===")
	print("Godot Version: %s" % Engine.get_version_info().string)
	print("")
	
	var exit_code = run_all_tests()
	
	print("")
	print("=== Test Summary ===")
	print("Total: %d, Passed: %d, Failed: %d, Skipped: %d" % [
		test_results.total,
		test_results.passed,
		test_results.failed,
		test_results.skipped
	])
	
	if test_results.failed > 0:
		print("\n✗ TESTS FAILED")
		get_tree().quit(1)
	else:
		print("\n✓ ALL TESTS PASSED")
		get_tree().quit(0)

func run_all_tests() -> int:
	var test_files = _discover_tests()
	
	if test_files.is_empty():
		print("No test files found!")
		return 0
	
	print("Found %d test files\n" % test_files.size())
	
	for test_file in test_files:
		_run_test_file(test_file)
	
	return test_results.failed

func _discover_tests() -> Array:
	var test_files: Array = []
	
	for dir_path in TEST_DIRS:
		test_files.append_array(_find_tests_in_dir(dir_path))
	
	return test_files

func _find_tests_in_dir(dir_path: String) -> Array:
	var files: Array = []
	var dir = DirAccess.open(dir_path)
	
	if not dir:
		print("Warning: Could not open directory: %s" % dir_path)
		return files
	
	dir.list_dir_begin()
	var file_name = dir.get_next()
	
	while file_name != "":
		if not dir.current_is_dir():
			if file_name.begins_with("test_") and file_name.ends_with(".gd"):
				var full_path = dir_path + "/" + file_name
				files.append(full_path)
				print("  Found: %s" % full_path)
		file_name = dir.get_next()
	
	dir.list_dir_end()
	return files

func _run_test_file(file_path: String):
	print("\n--- Running: %s ---" % file_path)
	
	# Load the test script
	var script = load(file_path)
	if not script:
		print("  ✗ Failed to load script")
		test_results.failed += 1
		test_results.total += 1
		return
	
	# Create test instance
	var test_instance = Node.new()
	test_instance.set_script(script)
	add_child(test_instance)
	
	# Run before_all if it exists
	if test_instance.has_method("before_all"):
		test_instance.before_all()
	
	# Find and run all test methods
	var test_methods = _get_test_methods(test_instance)
	
	for method in test_methods:
		_run_test_method(test_instance, method)
	
	# Run after_all if it exists
	if test_instance.has_method("after_all"):
		test_instance.after_all()
	
	# Cleanup
	test_instance.queue_free()

func _get_test_methods(instance) -> Array:
	var methods = []
	var method_list = instance.get_method_list()
	
	for method in method_list:
		var method_name = method.name
		if method_name.begins_with("test_"):
			methods.append(method_name)
	
	return methods

func _run_test_method(instance, method_name: String):
	# Run before_each if it exists
	if instance.has_method("before_each"):
		instance.before_each()
	
	var result = "PASS"
	var error_msg = ""
	
	# Run the test
	if instance.has_method(method_name):
		# Check if test should be skipped
		if instance.get(method_name + "_skip") == true:
			result = "SKIP"
		else:
			var success = _safe_call(instance, method_name)
			if not success:
				result = "FAIL"
				error_msg = "Test assertion failed"
	else:
		result = "FAIL"
		error_msg = "Method not found"
	
	# Run after_each if it exists
	if instance.has_method("after_each"):
		instance.after_each()
	
	# Record result
	match result:
		"PASS":
			test_results.passed += 1
			print("  ✓ %s" % method_name)
		"FAIL":
			test_results.failed += 1
			print("  ✗ %s: %s" % [method_name, error_msg])
		"SKIP":
			test_results.skipped += 1
			print("  ○ %s (skipped)" % method_name)
	
	test_results.total += 1

func _safe_call(instance, method_name: String) -> bool:
	# Wrap in try-catch equivalent for GDScript
	var success = true
	
	# Check if instance is still valid
	if not is_instance_valid(instance):
		return false
	
	# Call the method
	var result = instance.call(method_name)
	
	# If method returns false, it's a failure
	if typeof(result) == TYPE_BOOL and result == false:
		success = false
	
	return success
