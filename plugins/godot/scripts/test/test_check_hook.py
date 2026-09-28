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
from .engine_gate import requires_engine  # noqa: E402


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


@requires_engine
class TestWithEngine(unittest.TestCase):
    """Imports the fixture ONCE, then hands each test its own copy.

    `setUp` used to run a full `--headless --import` per test method, which
    measured 20.0s across these 18 tests -- on its own more than half of the
    entire catalog's `bun test` gate. The per-test isolation it bought is
    real and must not be given up: several tests below mutate the project,
    including deleting `.godot/` outright and adding a `class_name` the cache
    has never seen, so a project shared between tests would leak state in the
    exact dimension these tests measure.

    So the import happens once into a pristine template, and each test gets a
    `copytree` of the ALREADY-IMPORTED project -- same isolation, one engine
    invocation instead of eighteen.

    Verified before relying on it, because a cache full of absolute paths
    would make a copied project behave differently from a freshly imported
    one: nothing under `.godot/` embeds the project path (both a text and a
    raw-byte scan of `editor/`, `imported/`, `uid_cache.bin` and
    `global_script_class_cache.cfg` came back empty), and driving the real
    hook against a copied-but-never-imported-at-that-path project produced
    byte-identical output to the freshly imported one. `copytree` uses
    `copy2`, so mtimes are preserved and the hook's cache-freshness check
    sees the same ordering it would after a real import.
    """

    @classmethod
    def setUpClass(cls):
        cls._template_dir = Path(tempfile.mkdtemp(prefix="godot-hook-template-"))
        cls._template = cls._template_dir / "proj"
        shutil.copytree(SAMPLE, cls._template)
        subprocess.run(
            [engine.find_binary(), "--headless", "--path", str(cls._template), "--import"],
            capture_output=True, timeout=180,
        )
        if not (cls._template / ".godot" / "global_script_class_cache.cfg").is_file():
            raise AssertionError(
                "the template import produced no class cache, so every test "
                "below would silently exercise the unimported path instead of "
                "the one it is written for"
            )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._template_dir, ignore_errors=True)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "proj"
        shutil.copytree(self._template, self.root)

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
        # Fix round 1, IMPORTANT 1. The project is already imported (the
        # the template import ran), but a class_name is added in one file and used
        # a second file in the very next edit, before anything re-imports.
        # Confirmed against the engine: this reports "Could not find type
        # EnemyType in the current scope" even though EnemyType is spelled
        # correctly and its declaring file is sitting right there,
        # unimported. A directory-existence check for .godot/ (the original
        # version of this hook) does not catch this -- .godot/ already
        # exists in the copied template -- only a freshness check does.
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
        # Both files are new; re-importing once after adding them is no
        # longer load-bearing under the round-3 per-diagnostic filter (these
        # diagnostics -- a type mismatch and a downstream compile failure --
        # never match the missing-type shapes that trigger a class_name
        # lookup at all, regardless of freshness), but it costs nothing and
        # keeps this test isolated from any future change to that filter.
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
        # Fix round 3: the hedge clause itself must be present here, since
        # every surviving `at:` location genuinely differs from $rel.
        self.assertIn("may live in a res://", context)

    def test_header_has_no_preload_hedge_when_error_is_local(self):
        # Fix round 3. The hedge ("errors may live in a preloaded file") is
        # only earned when some surviving `at:` location actually differs
        # from the edited file. Unconditionally hedging under-credits a
        # genuine local error on a skim -- broken.gd's errors are entirely
        # its own, so the header must not soften that.
        proc = run_hook(self.root / "broken.gd")
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("may live in a res://", context)

    def test_class_name_inside_multiline_string_does_not_suppress_unrelated_error(self):
        # Fix round 3, finding A. A bystander file containing the substring
        # "class_name" only inside a multi-line string (not a declaration at
        # all -- it compiles cleanly) must not suppress a real, unrelated
        # error in the file being checked. Confirmed against the engine:
        # round 2's file-content-blind check ("does any newer file contain
        # the text class_name") could not tell this apart from a genuine
        # declaration; the round-3 per-diagnostic filter can, because
        # broken2.gd's actual error ("Cannot assign...") never matches the
        # missing-type shapes that trigger a class_name lookup at all, so
        # what the bystander file contains is irrelevant.
        (self.root / "bystander.gd").write_text(
            'extends Resource\n\nconst NOTE = """\nclass_name NotARealDeclaration\n"""\n'
        )
        broken = self.root / "broken2.gd"
        broken.write_text(
            'extends Node\n\nfunc _ready() -> void:\n\tvar x: int = "still broken"\n'
        )
        proc = run_hook(broken)
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("broken2.gd", context)
        self.assertIn("String", context)

    def test_symlinked_target_with_class_name_still_reports_own_real_error(self):
        # Fix round 3, finding B. The checked path is a symlink to a file
        # that itself declares a class_name; -samefile's identity semantics
        # around a symlinked path are exactly the kind of thing that could
        # make the target look like "a different, newer, class_name-
        # declaring file" relative to the checked path. Under the round-3
        # design this cannot matter: the file's own error is a type
        # mismatch, never a missing-type diagnostic, so it is never a
        # candidate for the class_name lookup regardless of what -samefile
        # decides about the symlink's identity.
        real = self.root / "real_target.gd"
        real.write_text(
            'class_name SymlinkedClass\nextends Node\n\nfunc _ready() -> void:\n\tvar x: int = "still broken"\n'
        )
        link = self.root / "linked.gd"
        link.symlink_to(real)
        proc = run_hook(link)
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("String", context)

    def test_unrelated_class_name_elsewhere_does_not_suppress_unrelated_error(self):
        # Fix round 3, finding C. A class_name file exists elsewhere in the
        # project, newer than the cache, but names a class the checked
        # file's error has nothing to do with. Round 2's design suppressed
        # on this alone -- "any newer file containing class_name anywhere"
        # -- which would silence a project's entire error reporting during
        # active scaffolding, exactly when new class_name declarations are
        # being added on purpose. The round-3 filter requires the SPECIFIC
        # missing name to match, so an unrelated declaration cannot qualify.
        (self.root / "unrelated_class.gd").write_text(
            "class_name TotallyUnrelated\nextends Resource\n"
        )
        broken = self.root / "broken.gd"
        broken.write_text(
            'extends Node\n\nfunc _ready() -> void:\n\tvar x: int = "still broken"\n'
        )
        proc = run_hook(broken)
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("broken.gd", context)
        self.assertIn("String", context)

    def test_stale_and_real_error_in_same_file_reports_only_the_real_one(self):
        # Fix round 3. The strictly-better property the per-diagnostic
        # design gives over its predecessors: a file with BOTH a stale-cache
        # artifact (an unindexed class_name reference) AND a genuine,
        # unrelated error must report only the real one, dropping just the
        # stale-cache pairs rather than either reporting both (crying wolf)
        # or suppressing both (going silent on a real bug). Confirmed
        # against the engine that referencing an unindexed class_name
        # produces two diagnostic pairs (`Could not find type` for the type
        # annotation use, `Identifier ... not declared` for the constructor
        # call use) alongside the real error, all in the same file, in one
        # `--check-only` run.
        (self.root / "enemy_type.gd").write_text("class_name EnemyType\nextends Resource\n")
        combined = self.root / "combined.gd"
        combined.write_text(
            'extends Node\n\nfunc _ready() -> void:\n'
            '\tvar e: EnemyType = EnemyType.new()\n'
            '\tvar x: int = "still broken"\n'
        )
        proc = run_hook(combined)
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("EnemyType", context)
        self.assertIn("String", context)

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
