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

    def test_a_comment_mentioning_apply_does_not_bypass(self):
        self.assertEqual(
            guard.evaluate("rm -rf /Users/me/Documents/x  # see apply.py", ROOTS)[0], "deny")

    def test_a_file_named_apply_py_does_not_bypass(self):
        self.assertEqual(
            guard.evaluate("rm -rf /Users/me/Documents/apply.py.bak", ROOTS)[0], "deny")

    def test_a_sibling_directory_is_not_treated_as_the_root(self):
        self.assertIsNone(guard.evaluate("rm -rf /Users/me/Documents-backup/x", ROOTS))
        self.assertIsNone(guard.evaluate("rm -rf /Users/me/Documents.old/y", ROOTS))

    def test_relative_deletion_after_cd_into_the_root(self):
        self.assertEqual(guard.evaluate("cd /Users/me/Documents && rm -rf x", ROOTS)[0], "deny")

    def test_cd_elsewhere_then_delete_is_allowed(self):
        self.assertIsNone(guard.evaluate("cd /tmp/scratch && rm -rf x", ROOTS))

    def test_wrappers_do_not_hide_the_verb(self):
        for cmd in ("sudo rm -rf /Users/me/Documents/x",
                    "env FOO=bar rm -rf /Users/me/Documents/x",
                    "nohup rm -rf /Users/me/Documents/x",
                    "time rm -rf /Users/me/Documents/x",
                    "(rm -rf /Users/me/Documents/x)"):
            with self.subTest(cmd=cmd):
                self.assertEqual(guard.evaluate(cmd, ROOTS)[0], "deny")

    def test_deletion_without_a_destructive_verb(self):
        for cmd in ("find /Users/me/Documents -name '*.tmp' -delete",
                    "rsync -a --remove-source-files /Users/me/Documents/a/ /tmp/b/",
                    "git clean -fdx /Users/me/Documents"):
            with self.subTest(cmd=cmd):
                self.assertEqual(guard.evaluate(cmd, ROOTS)[0], "deny")

    def test_a_real_apply_invocation_is_still_allowed(self):
        self.assertIsNone(
            guard.evaluate("python3 apply.py /Users/me/Documents/.para/plan.json", ROOTS))

    def test_reads_inside_the_root_are_still_allowed(self):
        for cmd in ("ls -la /Users/me/Documents", "grep -r todo /Users/me/Documents",
                    "cat /Users/me/Documents/notes.md"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(guard.evaluate(cmd, ROOTS))

    def test_a_quote_split_path_does_not_bypass(self):
        self.assertEqual(guard.evaluate('rm -rf /Users/me/"Documents"/x', ROOTS)[0], "deny")

    def test_a_wrapper_flag_with_a_value_does_not_bypass(self):
        for cmd in ("sudo -u root rm -rf /Users/me/Documents/x",
                    "sudo -u root -g wheel rm -rf /Users/me/Documents/x"):
            with self.subTest(cmd=cmd):
                self.assertEqual(guard.evaluate(cmd, ROOTS)[0], "deny")

    def test_pushd_is_tracked_like_cd(self):
        self.assertEqual(guard.evaluate("pushd /Users/me/Documents && rm -rf x", ROOTS)[0], "deny")

    def test_a_relative_cd_stays_inside_the_root(self):
        self.assertEqual(
            guard.evaluate("cd /Users/me/Documents && cd sub && rm -rf x", ROOTS)[0], "deny")

    def test_an_absolute_cd_away_leaves_the_root(self):
        self.assertIsNone(
            guard.evaluate("cd /Users/me/Documents && cd /tmp && rm -rf x", ROOTS))

    def test_deep_wrapper_stacking_does_not_fail_open(self):
        self.assertEqual(
            guard.evaluate("sudo sudo sudo sudo sudo sudo sudo sudo rm -rf /Users/me/Documents/x",
                           ROOTS)[0], "deny")

    def test_a_git_clean_dry_run_is_allowed(self):
        for cmd in ("git clean --dry-run -fdx /Users/me/Documents",
                    "git clean -n /Users/me/Documents"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(guard.evaluate(cmd, ROOTS))

    def test_a_real_git_clean_is_still_denied(self):
        self.assertEqual(guard.evaluate("git clean -fdx /Users/me/Documents", ROOTS)[0], "deny")

    def test_unknown_wrapper_flags_do_not_hide_the_verb(self):
        for cmd in ("sudo -D /tmp rm -rf /Users/me/Documents/x",
                    "sudo -R /var/tmp rm -rf /Users/me/Documents/x",
                    "sudo --close-from 3 rm -rf /Users/me/Documents/x",
                    "time -o /tmp/out rm -rf /Users/me/Documents/x"):
            with self.subTest(cmd=cmd):
                self.assertEqual(guard.evaluate(cmd, ROOTS)[0], "deny")

    def test_an_apostrophe_in_a_sibling_name_is_not_the_root(self):
        self.assertIsNone(guard.evaluate("rm -rf \"/Users/me/Documents'/x\"", ROOTS))

    def test_a_relative_cd_away_leaves_the_root(self):
        for cmd in ("cd /Users/me/Documents && cd ../elsewhere && rm -rf x",
                    "cd /Users/me/Documents && cd .. && rm -rf x"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(guard.evaluate(cmd, ROOTS))

    def test_reading_a_file_that_mentions_rm_is_allowed(self):
        for cmd in ("grep rm /Users/me/Documents/notes.txt",
                    "cat /Users/me/Documents/how-to-rm.txt",
                    'echo "rm -rf /Users/me/Documents/x"'):
            with self.subTest(cmd=cmd):
                self.assertIsNone(guard.evaluate(cmd, ROOTS))

    def test_cd_dotdot_back_into_the_root_is_still_guarded(self):
        self.assertEqual(
            guard.evaluate("cd /Users/me/Documents/sub && cd .. && rm -rf x", ROOTS)[0], "deny")

    def test_cd_dotdot_out_of_the_root_is_allowed(self):
        self.assertIsNone(guard.evaluate("cd /Users/me/Documents && cd .. && rm -rf x", ROOTS))

    def test_nested_cd_and_dotdot_resolve_lexically(self):
        self.assertEqual(
            guard.evaluate("cd /Users/me/Documents && cd sub/deeper && cd ../.. && rm -rf x",
                           ROOTS)[0], "deny")
        self.assertIsNone(
            guard.evaluate("cd /Users/me/Documents/sub && cd ../../elsewhere && rm -rf x", ROOTS))

    def test_find_searching_for_a_file_named_rm_is_allowed(self):
        for cmd in ("find /Users/me/Documents -name rm -type f",
                    "find /Users/me/Documents -name mv -type f"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(guard.evaluate(cmd, ROOTS))

    def test_find_delete_is_still_denied(self):
        self.assertEqual(
            guard.evaluate("find /Users/me/Documents -name '*.tmp' -delete", ROOTS)[0], "deny")


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
