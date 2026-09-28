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

    def test_stale_cross_file_class_name_stays_silent(self):
        # Fix round 1, IMPORTANT 1. The project is already imported (setUp
        # ran --import), but a class_name is added in one file and used from
        # a second file in the very next edit, before anything re-imports.
        # Confirmed against the engine: this reports "Could not find type
        # EnemyType in the current scope" even though EnemyType is spelled
        # correctly and its declaring file is sitting right there,
        # unimported. A directory-existence check for .godot/ (the original
        # version of this hook) does not catch this -- .godot/ already
        # exists from setUp -- only a freshness check does.
        (self.root / "enemy_type.gd").write_text("class_name EnemyType\nextends Resource\n")
        uses = self.root / "uses_enemy.gd"
        uses.write_text(
            'extends Node\n\nfunc _ready() -> void:\n\tvar e: EnemyType = EnemyType.new()\n'
        )
        proc = run_hook(uses)
        self.assertEqual(proc.stdout.strip(), "")

    def test_unrelated_newer_file_without_class_name_still_reports(self):
        # Fix round 2, IMPORTANT 1, case B. The ordinary session shape: an
        # agent edits several .gd files in a row before anything reimports.
        # After the first edit, every subsequent edit sees some OTHER .gd
        # file that is also newer than the cache. A content-blind "is
        # anything else newer" check (fix round 1's version of this
        # staleness test) suppresses every one of those subsequent edits --
        # for the rest of the session -- even on files with real, unrelated
        # errors, because a stale cache can only produce a spurious
        # diagnostic through one mechanism: an unindexed class_name. This is
        # the same shape as test_stale_cross_file_class_name_stays_silent
        # immediately above, with the one line that matters removed: no
        # class_name here, so nothing about the cache being behind can make
        # any reference in broken.gd wrong, and the real error must be
        # reported.
        (self.root / "enemy_type.gd").write_text("extends Resource\n")
        broken = self.root / "broken.gd"
        broken.write_text(
            'extends Node\n\nfunc _ready() -> void:\n\tvar x: int = "still broken"\n'
        )
        proc = run_hook(broken)
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("broken.gd", context)
        self.assertIn("String", context)

    def test_editing_only_the_checked_file_still_reports(self):
        # Companion to the fix above. PostToolUse fires right after Claude
        # wrote the exact file being checked, so that file's mtime is
        # *always* newer than the class cache -- a staleness test that does
        # not exclude the file under check from its own "is anything newer
        # than the cache" scan would treat every single post-import edit as
        # proof of a stale cache, and silence the hook permanently on real,
        # unrelated errors from then on. Confirmed empirically: touching only
        # the target file (nothing else in the project) makes a same-file
        # inclusive `find -newer` "find" staleness on every run.
        broken = self.root / "broken.gd"
        broken.write_text(
            'extends Node\n\nfunc _ready() -> void:\n\tvar x: int = "still broken"\n'
        )
        proc = run_hook(broken)
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("broken.gd", context)
        self.assertIn("String", context)

    def test_large_output_is_truncated(self):
        # Fix round 1, IMPORTANT 2. One bad pattern repeated many times in a
        # single file (here, 15 mistyped member variables) produces one
        # diagnostic block per occurrence -- 61 filtered lines, measured --
        # and an uncapped dump floods the transcript on every edit to that
        # file until it's fixed.
        lines = ["extends Node", ""]
        for i in range(15):
            lines.append(f'var bad_{i}: int = "not an int"')
        many = self.root / "many_errors.gd"
        many.write_text("\n".join(lines) + "\n")
        proc = run_hook(many)
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("truncated", context)
        # 40 kept diagnostic lines is the cap; the message overall (header +
        # blank line + 40 lines + the truncation note) should be well short
        # of the untruncated ~61-line dump.
        self.assertLessEqual(context.count("\n"), 50)

    def test_preload_error_is_not_misattributed_to_the_edited_file(self):
        # Fix round 1, IMPORTANT 3. A clean file that preloads a broken one:
        # confirmed against the engine that every root-cause diagnostic
        # points at the preloaded file, not at the file just edited. The
        # header must not claim the errors ARE in the edited file.
        #
        # Both files are new, so re-import once after adding them: without
        # that, the fix-round-1 freshness check (IMPORTANT 1, tested above)
        # would correctly-but-irrelevantly silence this case too, since
        # bad_preload_target.gd is a second, non-checked file newer than the
        # cache. Re-importing isolates the misattribution question from the
        # staleness question.
        (self.root / "bad_preload_target.gd").write_text(
            'extends Node\n\nfunc _ready() -> void:\n\tvar x: int = "not an int"\n'
        )
        user = self.root / "uses_preload.gd"
        user.write_text(
            'extends Node\n\nconst Bad = preload("res://bad_preload_target.gd")\n'
        )
        subprocess.run(
            [engine.find_binary(), "--headless", "--path", str(self.root), "--import"],
            capture_output=True, timeout=180,
        )
        proc = run_hook(user)
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("errors in uses_preload.gd", context)
        self.assertIn("bad_preload_target.gd", context)

    def test_engine_cpp_frames_never_appear_in_context(self):
        # Fix round 1, IMPORTANT 4. broken.gd's stderr always ends with a
        # trailing `at: load (modules/gdscript/gdscript_resource_format.cpp:
        # 46)` frame that points into engine C++, not a res:// file. The
        # res:// qualifier on the `at:` branch of the filtering grep is the
        # only thing keeping it out of additionalContext.
        proc = run_hook(self.root / "broken.gd")
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("modules/gdscript", context)


if __name__ == "__main__":
    unittest.main()
