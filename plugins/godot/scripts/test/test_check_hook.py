import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import engine

HOOK = Path(__file__).resolve().parents[2] / "hooks" / "scripts" / "check-gdscript.sh"
SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"
HAS_GODOT = engine.find_binary() is not None


def run_hook(file_path, env=None):
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}})
    merged = dict(os.environ)
    if env:
        merged.update(env)
    proc = subprocess.run(
        ["bash", str(HOOK)], input=payload, capture_output=True, text=True,
        timeout=60, env=merged,
    )
    return proc


class TestAlwaysAdvisory(unittest.TestCase):
    def test_always_exits_zero(self):
        self.assertEqual(run_hook("/tmp/nowhere.gd").returncode, 0)

    def test_non_gd_files_produce_no_output(self):
        self.assertEqual(run_hook(SAMPLE / "main.tscn").stdout.strip(), "")

    def test_file_outside_a_project_produces_no_output(self):
        tmp = Path(tempfile.mkdtemp()) / "loose.gd"
        tmp.write_text("extends Node\n")
        self.assertEqual(run_hook(tmp).stdout.strip(), "")

    def test_missing_binary_is_silent(self):
        proc = run_hook(SAMPLE / "broken.gd", env={"GODOT_BIN": "/nonexistent/godot-x"})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")


@unittest.skipUnless(HAS_GODOT, "godot not on PATH")
class TestWithEngine(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "proj"
        shutil.copytree(SAMPLE, self.root)
        subprocess.run(
            [engine.find_binary(), "--headless", "--path", str(self.root), "--import"],
            capture_output=True, timeout=180,
        )

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_broken_script_produces_advisory_context(self):
        proc = run_hook(self.root / "broken.gd")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("broken.gd", context)
        self.assertIn("5", context)

    def test_clean_script_produces_no_output(self):
        proc = run_hook(self.root / "scripts" / "player.gd")
        self.assertEqual(proc.stdout.strip(), "")

    def test_unimported_project_stays_silent(self):
        # Without .godot/, a class_name from another file reports a false error.
        shutil.rmtree(self.root / ".godot", ignore_errors=True)
        proc = run_hook(self.root / "broken.gd")
        self.assertEqual(proc.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
