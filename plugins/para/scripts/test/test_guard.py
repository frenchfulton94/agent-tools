import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import guard_para_moves as guard

SCRIPT = str(pathlib.Path(__file__).resolve().parents[1] / "guard_para_moves.py")
ROOTS = ["/Users/me/Documents"]


class Evaluate(unittest.TestCase):
    def test_denies_rm_inside_a_registered_root(self):
        verdict = guard.evaluate("rm -rf /Users/me/Documents/4-Archives/old", ROOTS)
        self.assertEqual(verdict[0], "deny")

    def test_denies_bare_mv_inside_a_registered_root(self):
        verdict = guard.evaluate("mv /Users/me/Documents/a.pdf /Users/me/Documents/b.pdf", ROOTS)
        self.assertEqual(verdict[0], "deny")

    def test_allows_mv_through_apply(self):
        self.assertIsNone(guard.evaluate("python3 apply.py /Users/me/Documents/.para/plan.json", ROOTS))

    def test_allows_rm_outside_every_registered_root(self):
        self.assertIsNone(guard.evaluate("rm -rf /tmp/scratch/build", ROOTS))

    def test_allows_reads_inside_a_registered_root(self):
        self.assertIsNone(guard.evaluate("ls -la /Users/me/Documents", ROOTS))
        self.assertIsNone(guard.evaluate("grep -r todo /Users/me/Documents", ROOTS))

    def test_judges_each_segment_independently(self):
        verdict = guard.evaluate("ls /tmp && rm -rf /Users/me/Documents/x", ROOTS)
        self.assertEqual(verdict[0], "deny")

    def test_no_registry_means_no_opinion(self):
        self.assertIsNone(guard.evaluate("rm -rf /Users/me/Documents/x", []))


class Cli(unittest.TestCase):
    def _run(self, payload, roots_file):
        return subprocess.run(
            [sys.executable, SCRIPT],
            input=json.dumps(payload), capture_output=True, text=True,
            env={"PARA_ROOTS_FILE": roots_file, "PATH": "/usr/bin:/bin"},
        )

    def test_exits_zero_and_denies_via_json(self):
        with tempfile.TemporaryDirectory() as d:
            roots_file = str(pathlib.Path(d) / "roots")
            pathlib.Path(roots_file).write_text("/Users/me/Documents\n")
            result = self._run(
                {"tool_name": "Bash", "tool_input": {"command": "rm -rf /Users/me/Documents/x"}},
                roots_file,
            )
            self.assertEqual(result.returncode, 0)
            decision = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]
            self.assertEqual(decision, "deny")

    def test_stays_silent_for_non_bash_tools(self):
        with tempfile.TemporaryDirectory() as d:
            roots_file = str(pathlib.Path(d) / "roots")
            pathlib.Path(roots_file).write_text("/Users/me/Documents\n")
            result = self._run({"tool_name": "Read", "tool_input": {}}, roots_file)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_survives_a_malformed_payload(self):
        with tempfile.TemporaryDirectory() as d:
            roots_file = str(pathlib.Path(d) / "roots")
            result = subprocess.run(
                [sys.executable, SCRIPT], input="not json",
                capture_output=True, text=True,
                env={"PARA_ROOTS_FILE": roots_file, "PATH": "/usr/bin:/bin"},
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
