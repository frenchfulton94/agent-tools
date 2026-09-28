extends Node
# Fixture for the run_scene backtrace tests (test_engine.py). Crashes three
# calls deep so the tests can assert the whole chain -- not just the crash
# site -- comes back through run_scene's diagnostics. Kept in its own
# project (rather than added to fixtures/sample-project) so it doesn't
# perturb any test that scans sample-project's exact file inventory (e.g.
# test_refs.py's parse-call-count pin).


func _ready() -> void:
	level_one()


func level_one() -> void:
	level_two()


func level_two() -> void:
	var arr: Array = []
	print(arr[5])
