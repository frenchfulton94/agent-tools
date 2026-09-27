import os
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import engine

SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"
HAS_GODOT = engine.find_binary() is not None

GDSCRIPT_STDERR = """SCRIPT ERROR: Parse Error: Cannot assign a value of type "String" as "int".
          at: GDScript::reload (res://broken.gd:5)
SCRIPT ERROR: Parse Error: Function "undefined_function_call()" not found in base self.
          at: GDScript::reload (res://broken.gd:6)
ERROR: Failed to load script "res://broken.gd" with error "Parse error".
   at: load (modules/gdscript/gdscript_resource_format.cpp:46)
"""

SHADER_STDERR = """SHADER ERROR: Invalid arguments for the built-in function: "vec4(float,float,float)".
          at: (null) (res://bad.gdshader:3)
"""


class TestDiagnostics(unittest.TestCase):
    def test_extracts_script_errors_with_file_and_line(self):
        found = engine.diagnostics(GDSCRIPT_STDERR)
        located = [d for d in found if d["file"]]
        self.assertEqual(len(located), 2)
        self.assertEqual(located[0]["file"], "res://broken.gd")
        self.assertEqual(located[0]["line"], 5)
        self.assertIn("Cannot assign", located[0]["message"])

    def test_engine_internal_cpp_locations_are_not_user_files(self):
        # `modules/gdscript/...cpp:46` is engine source, not the user's project.
        for d in engine.diagnostics(GDSCRIPT_STDERR):
            self.assertFalse((d["file"] or "").endswith(".cpp"))

    def test_extracts_shader_errors(self):
        found = engine.diagnostics(SHADER_STDERR)
        located = [d for d in found if d["file"]]
        self.assertEqual(located[0]["file"], "res://bad.gdshader")
        self.assertEqual(located[0]["line"], 3)
        self.assertEqual(located[0]["severity"], "SHADER ERROR")

    def test_clean_output_yields_nothing(self):
        self.assertEqual(engine.diagnostics("Godot Engine v4.7.2.stable\n"), [])


@unittest.skipUnless(HAS_GODOT, "godot not on PATH")
class TestAgainstRealEngine(unittest.TestCase):
    def test_broken_script_is_reported_broken_despite_exit_zero(self):
        # Spec 3.1: --check-only exits 0 on parse errors. This test is the guard
        # against anyone rewriting check_script to trust returncode.
        found = engine.check_script(str(SAMPLE), "broken.gd")
        self.assertTrue(found, "broken.gd must produce diagnostics")
        self.assertTrue(any(d["line"] == 5 for d in found))

    def test_exit_code_really_is_zero_for_broken_input(self):
        result = engine.run(
            ["--headless", "--path", str(SAMPLE), "--check-only", "--script", "broken.gd"]
        )
        self.assertEqual(result.returncode, 0)

    def test_clean_script_produces_no_diagnostics(self):
        self.assertEqual(engine.check_script(str(SAMPLE), "scripts/player.gd"), [])

    def test_timeout_is_enforced_by_us_not_by_timeout1(self):
        # macOS has no timeout(1); the wrapper owns the deadline.
        result = engine.run(["--headless", "--quit-after", "100000",
                             "--path", str(SAMPLE)], timeout=3)
        self.assertTrue(result.timed_out)


class TestFindBinary(unittest.TestCase):
    def test_env_override_wins(self):
        os.environ["GODOT_BIN"] = "/nonexistent/godot-x"
        try:
            self.assertEqual(engine.find_binary(), "/nonexistent/godot-x")
        finally:
            del os.environ["GODOT_BIN"]


if __name__ == "__main__":
    unittest.main()
