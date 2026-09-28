import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import engine

SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"
CRASH_PROJECT = Path(__file__).parent / "fixtures" / "crash-project"
HAS_GODOT = engine.find_binary() is not None

FAKE_GODOT_ORPHAN = (
    Path(__file__).parent / "fixtures" / "fake-binaries" / "hangs_with_orphan.sh"
)

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

# Captured verbatim from the real engine (godot 4.7.2.stable.official) by
# pointing the sample project's main.tscn ext_resource at broken.gd with a
# stale UID: `godot --headless --path <project> --quit-after 2`. The WARNING's
# own `at:` frame points into engine C++ (resource_format_text.cpp) and is
# rejected, so a naive fixed-window lookahead reaches past it into the next
# diagnostic and reports the WARNING as living at broken.gd:5 -- an unrelated
# script's parse error, not the stale-UID problem the warning is actually
# about.
MISATTRIBUTION_STDERR = """WARNING: res://main.tscn:3 - ext_resource, invalid UID: uid://zzinvaliduid00 - using text path instead: res://broken.gd
     at: load (scene/resources/resource_format_text.cpp:501)
SCRIPT ERROR: Parse Error: Cannot assign a value of type "String" as "int".
          at: GDScript::reload (res://broken.gd:5)
"""

# Constructed (not captured -- unlike MISATTRIBUTION_STDERR above) to guard a
# related but distinct regression class: a clamp that resolves to the header
# *after* next (e.g. `header_idxs[pos + 2]` in place of `header_idxs[pos + 1]`)
# rather than the immediate next one. With three diagnostics in a row where
# the first two both lack a res:// frame of their own, that bug lets the
# SECOND diagnostic's window skip past itself and steal the THIRD
# diagnostic's location -- not just the first stealing from the second,
# which is all the two-header MISATTRIBUTION_STDERR case above can expose.
# The "ERROR: Failed to load script" line is real engine phrasing (seen
# verbatim in this project's own captured output), reordered here into the
# middle position to build the specific three-header shape under test.
SKIP_AHEAD_STDERR = """WARNING: res://main.tscn:3 - ext_resource, invalid UID: uid://zzinvaliduid00 - using text path instead: res://broken.gd
     at: load (scene/resources/resource_format_text.cpp:501)
ERROR: Failed to load script "res://broken.gd" with error "Parse error".
   at: load (modules/gdscript/gdscript_resource_format.cpp:46)
SCRIPT ERROR: Parse Error: Cannot assign a value of type "String" as "int".
          at: GDScript::reload (res://broken.gd:5)
"""

# Captured verbatim from the real engine (godot 4.7.2.stable.official): a
# scene whose script crashes three calls deep (_ready -> level_one ->
# level_two, an out-of-bounds Array read in level_two), run headless via
# `godot --headless --path <project> --quit-after 5`. This is the exact
# shape the tool's own description promises ("...with their GDScript
# backtraces") and the one the fix this test guards makes true: before it,
# `run_scene`'s returned diagnostics carried only the crash site
# (level_two:11), and level_one/_ready were silently unreachable anywhere
# in the tool's result even though the engine printed them.
BACKTRACE_STDERR = """SCRIPT ERROR: Out of bounds get index '5' (on base: 'Array')
          at: level_two (res://main.gd:11)
          GDScript backtrace (most recent call first):
              [0] level_two (res://main.gd:11)
              [1] level_one (res://main.gd:7)
              [2] _ready (res://main.gd:4)
"""

# Constructed (not captured): guards the same res://-only rule `_AT` already
# enforces for a diagnostic's own location, applied to one frame INSIDE a
# backtrace instead. Every backtrace this plan's own testing produced (a
# three-deep call chain, a Timer-signal-triggered crash, a 60-deep
# recursion) only ever contained res:// frames -- native call boundaries
# simply end the chain rather than inserting a C++ frame -- so this
# specific shape wasn't observed against the real engine. The brief still
# calls for the same defensive rule `_AT` uses, on the reasoning that a
# frame's location is exactly the same kind of string `_AT` already can't
# trust to be a project file, so this pins that the parser doesn't assume
# it either, without asserting a real engine ever produces it.
BACKTRACE_WITH_ENGINE_FRAME_STDERR = """SCRIPT ERROR: Something broke
          at: helper (res://main.gd:20)
          GDScript backtrace (most recent call first):
              [0] helper (res://main.gd:20)
              [1] some_native_bridge (modules/gdscript/gdscript_vm.cpp:1234)
              [2] _ready (res://main.gd:4)
"""


def _make_deep_backtrace_stderr(depth):
    """Build a synthetic backtrace `depth` frames deep, all res://, to drive
    the MAX_BACKTRACE_FRAMES cap without hand-writing dozens of literal
    lines. Frame [0] is the crash site (matching the leading `at:` line);
    frames [1..depth-1] are synthetic callers. Shape matches the real
    60-deep recursion this plan captured directly against the engine
    (`recurse()` calling itself, `--quit-after 10`) -- Godot itself did not
    truncate that real backtrace at any point, so a cap has to be enforced
    here, not assumed to already exist upstream.
    """
    lines = [
        "SCRIPT ERROR: Out of bounds get index '9' (on base: 'Array')",
        "          at: recurse (res://main.gd:9)",
        "          GDScript backtrace (most recent call first):",
        "              [0] recurse (res://main.gd:9)",
    ]
    for n in range(1, depth):
        lines.append(f"              [{n}] recurse (res://main.gd:11)")
    return "\n".join(lines) + "\n"


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

    def test_header_lookahead_does_not_cross_into_the_next_diagnostic(self):
        # CRITICAL 2 pin: a header whose own `at:` frame is rejected (it
        # points into engine C++, not res://) must not reach past itself and
        # steal the FOLLOWING diagnostic's res:// location. The WARNING here
        # must report no location of its own, not broken.gd:5 -- that line
        # belongs to the unrelated SCRIPT ERROR right after it.
        found = engine.diagnostics(MISATTRIBUTION_STDERR)
        self.assertEqual(len(found), 2)
        warning, script_error = found
        self.assertEqual(warning["severity"], "WARNING")
        self.assertIsNone(warning["file"])
        self.assertIsNone(warning["line"])
        self.assertEqual(script_error["severity"], "SCRIPT ERROR")
        self.assertEqual(script_error["file"], "res://broken.gd")
        self.assertEqual(script_error["line"], 5)

    def test_lookahead_does_not_skip_past_an_intermediate_header_either(self):
        # A related failure mode to the test above: the clamp must stop at
        # the IMMEDIATE next header, not some header further ahead. With
        # three diagnostics where the first two both have only an
        # engine-C++ frame of their own, the middle one must not reach past
        # itself and steal the THIRD diagnostic's res:// location.
        found = engine.diagnostics(SKIP_AHEAD_STDERR)
        self.assertEqual(len(found), 3)
        warning, load_error, script_error = found
        self.assertEqual(warning["severity"], "WARNING")
        self.assertIsNone(warning["file"])
        self.assertIsNone(warning["line"])
        self.assertEqual(load_error["severity"], "ERROR")
        self.assertIsNone(load_error["file"])
        self.assertIsNone(load_error["line"])
        self.assertEqual(script_error["severity"], "SCRIPT ERROR")
        self.assertEqual(script_error["file"], "res://broken.gd")
        self.assertEqual(script_error["line"], 5)

    def test_a_crash_with_no_backtrace_still_returns_cleanly(self):
        # check_script's own stderr (GDSCRIPT_STDERR) never has a backtrace
        # section -- --check-only never runs anything, so nothing ever
        # crashes at runtime. Nothing here should raise, and no entry should
        # grow a `backtrace` key it has no data for.
        found = engine.diagnostics(GDSCRIPT_STDERR)
        self.assertEqual(len(found), 3)
        for entry in found:
            self.assertNotIn("backtrace", entry)
            self.assertNotIn("backtrace_truncated", entry)

    def test_shader_errors_never_get_a_backtrace(self):
        # Shader compile errors are compile-time, exactly like check_script's
        # parse errors above -- nothing has run, so there is nothing to
        # unwind. Guards the same absence for a different diagnostic shape.
        found = engine.diagnostics(SHADER_STDERR)
        self.assertEqual(len(found), 1)
        self.assertNotIn("backtrace", found[0])

    def test_backtrace_frames_come_back_in_order_with_correct_files_and_lines(self):
        found = engine.diagnostics(BACKTRACE_STDERR)
        self.assertEqual(len(found), 1)
        entry = found[0]
        self.assertEqual(entry["file"], "res://main.gd")
        self.assertEqual(entry["line"], 11)
        self.assertIn("backtrace", entry)
        self.assertNotIn("backtrace_truncated", entry)
        self.assertEqual(
            entry["backtrace"],
            [
                {"frame": 0, "function": "level_two", "file": "res://main.gd", "line": 11},
                {"frame": 1, "function": "level_one", "file": "res://main.gd", "line": 7},
                {"frame": 2, "function": "_ready", "file": "res://main.gd", "line": 4},
            ],
        )

    def test_backtrace_frame_pointing_into_engine_cpp_is_not_a_user_file(self):
        found = engine.diagnostics(BACKTRACE_WITH_ENGINE_FRAME_STDERR)
        self.assertEqual(len(found), 1)
        backtrace = found[0]["backtrace"]
        self.assertEqual(len(backtrace), 3)
        # Frame 1's function name is real and kept; its location is engine
        # C++, not a res:// path, so file/line are None -- the same
        # treatment _AT already gives a diagnostic's own engine-C++ frame.
        self.assertEqual(backtrace[1]["function"], "some_native_bridge")
        self.assertIsNone(backtrace[1]["file"])
        self.assertIsNone(backtrace[1]["line"])
        # The frames on either side are ordinary res:// frames and must not
        # be collateral damage from the one in the middle being rejected.
        self.assertEqual(backtrace[0]["file"], "res://main.gd")
        self.assertEqual(backtrace[2]["file"], "res://main.gd")

    def test_backtrace_deeper_than_the_cap_is_truncated_with_a_count(self):
        # Godot itself does not cap a deep recursion's backtrace (measured
        # directly: a 60-deep recursion produced 61 uncapped frames plus
        # _ready, 62 total, no truncation marker from the engine at any
        # point) -- so a cap has to be enforced downstream of the engine,
        # not assumed to already exist. 45 synthetic frames, capped to
        # MAX_BACKTRACE_FRAMES (40), 5 left over.
        stderr = _make_deep_backtrace_stderr(45)
        found = engine.diagnostics(stderr)
        self.assertEqual(len(found), 1)
        entry = found[0]
        self.assertEqual(len(entry["backtrace"]), engine.MAX_BACKTRACE_FRAMES)
        self.assertEqual(entry["backtrace_truncated"], 5)
        # The frames actually kept are the first 40 (most-recent-call-first
        # order preserved), not an arbitrary 40 out of 45.
        self.assertEqual(entry["backtrace"][0]["frame"], 0)
        self.assertEqual(entry["backtrace"][-1]["frame"], 39)

    def test_backtrace_at_or_under_the_cap_is_not_marked_truncated(self):
        stderr = _make_deep_backtrace_stderr(engine.MAX_BACKTRACE_FRAMES)
        found = engine.diagnostics(stderr)
        entry = found[0]
        self.assertEqual(len(entry["backtrace"]), engine.MAX_BACKTRACE_FRAMES)
        self.assertNotIn("backtrace_truncated", entry)


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

    def test_run_scene_surfaces_the_real_backtrace_end_to_end(self):
        # fixtures/crash-project/crash.tscn crashes three calls deep
        # (_ready -> level_one -> level_two). Its own project, separate from
        # SAMPLE, so it doesn't perturb any test that scans SAMPLE's exact
        # file inventory (test_refs.py pins tscn.parse's call count against
        # it). This is the end-to-end counterpart to the string-level
        # BACKTRACE_STDERR tests above: it drives the real engine, not a
        # captured transcript, confirming run_scene's own return value --
        # not just diagnostics() in isolation -- actually carries the full
        # chain.
        result = engine.run_scene(str(CRASH_PROJECT), frames=5)
        with_backtrace = [d for d in result["diagnostics"] if d.get("backtrace")]
        self.assertEqual(len(with_backtrace), 1, "expected exactly one diagnostic with a backtrace")
        entry = with_backtrace[0]
        self.assertEqual(entry["file"], "res://crasher.gd")
        functions = [f["function"] for f in entry["backtrace"]]
        self.assertEqual(functions, ["level_two", "level_one", "_ready"])
        for frame in entry["backtrace"]:
            self.assertEqual(frame["file"], "res://crasher.gd")
            self.assertIsInstance(frame["line"], int)


class TestOrphanOnTimeout(unittest.TestCase):
    """CRITICAL 1 pin: a timeout must kill the whole process group, not just
    the immediate PID, and must not itself block forever doing it.

    Uses a fake "godot" binary (fixtures/fake-binaries/hangs_with_orphan.sh)
    that writes a diagnostic to stderr, then backgrounds a 30s-sleeping
    grandchild and exits. That grandchild inherits the stderr pipe and keeps
    its write end open long after the immediate child is gone -- exactly the
    shape of a scene that calls OS.execute()/OS.create_process() and hangs.
    Does not need Godot installed; runs unconditionally.
    """

    def test_timeout_kills_the_whole_process_group_not_just_the_child(self):
        os.environ["GODOT_BIN"] = str(FAKE_GODOT_ORPHAN)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                start = time.monotonic()
                # The fake binary itself returns almost instantly; 0.4s is
                # plenty for run()'s own TimeoutExpired to fire reliably
                # without padding out the suite the way a multi-second
                # timeout here would (this is most of what the suite gained
                # when these tests were added).
                result = engine.run([], cwd=tmp, timeout=0.4)
                elapsed = time.monotonic() - start
        finally:
            del os.environ["GODOT_BIN"]

        self.assertTrue(result.timed_out)
        # Generous ceiling: this must be bounded by our own timeout plus the
        # bounded backstop, nowhere near the grandchild's 30s sleep. A
        # regression here would hang the test itself well past this.
        self.assertLess(
            elapsed, 15,
            "run() blocked far past its own timeout -- an orphaned "
            "grandchild is likely still holding the stderr pipe open",
        )

    def test_the_orphaned_grandchild_does_not_survive(self):
        os.environ["GODOT_BIN"] = str(FAKE_GODOT_ORPHAN)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result = engine.run([], cwd=tmp, timeout=0.4)
                self.assertTrue(result.timed_out)
                pid_path = Path(tmp) / "child.pid"
                self.assertTrue(pid_path.exists(), "fake binary never wrote its child's pid")
                child_pid = int(pid_path.read_text().strip())

                deadline = time.monotonic() + 3
                alive = True
                while time.monotonic() < deadline:
                    try:
                        os.kill(child_pid, 0)
                    except ProcessLookupError:
                        alive = False
                        break
                    time.sleep(0.1)
                self.assertFalse(
                    alive,
                    f"grandchild pid {child_pid} survived proc.kill() as an orphan",
                )
        finally:
            del os.environ["GODOT_BIN"]


class TestNonTimeoutExceptionAlsoKillsTheGroup(unittest.TestCase):
    """IMPORTANT 6 pin: run() only killed the whole process group inside the
    TimeoutExpired branch. Any OTHER exception unwinding through
    communicate() (a KeyboardInterrupt, a bug in calling code on this
    thread) left the child's whole process group -- including a grandchild
    it had already spawned -- untouched. This predates Task 7 (every
    engine.run caller was already exposed), but Task 7's windowed drivers
    are the first callers where the orphan left behind is a VISIBLE WINDOW
    on the user's screen, not an invisible headless process.

    Reuses the same orphan-spawning fake binary as TestOrphanOnTimeout, but
    forces a non-timeout exception out of communicate() instead of a real
    timeout, by swapping the real Popen instance's own `communicate` method
    after it's constructed.
    """

    def test_a_non_timeout_exception_during_communicate_still_kills_the_group(self):
        os.environ["GODOT_BIN"] = str(FAKE_GODOT_ORPHAN)
        real_popen = subprocess.Popen

        class Boom(Exception):
            pass

        def raising_popen(*args, **kwargs):
            proc = real_popen(*args, **kwargs)

            def boom_communicate(*a, **kw):
                # Give the fake binary time to actually run (background its
                # sleeping grandchild and write child.pid) before the
                # exception hits -- a real communicate() would have blocked
                # this long anyway; raising instantly would race the shell
                # script's own startup instead of exercising the fix.
                time.sleep(0.3)
                raise Boom("simulated non-timeout failure")

            proc.communicate = boom_communicate
            return proc

        try:
            with tempfile.TemporaryDirectory() as tmp:
                with mock.patch.object(subprocess, "Popen", side_effect=raising_popen):
                    with self.assertRaises(Boom):
                        engine.run([], cwd=tmp, timeout=5)

                pid_path = Path(tmp) / "child.pid"
                self.assertTrue(pid_path.exists(), "fake binary never wrote its child's pid")
                child_pid = int(pid_path.read_text().strip())

                deadline = time.monotonic() + 3
                alive = True
                while time.monotonic() < deadline:
                    try:
                        os.kill(child_pid, 0)
                    except ProcessLookupError:
                        alive = False
                        break
                    time.sleep(0.1)
                self.assertFalse(
                    alive,
                    f"grandchild pid {child_pid} survived a non-timeout exception "
                    "during communicate()",
                )
        finally:
            del os.environ["GODOT_BIN"]


class TestFindBinary(unittest.TestCase):
    def test_env_override_wins(self):
        os.environ["GODOT_BIN"] = "/nonexistent/godot-x"
        try:
            self.assertEqual(engine.find_binary(), "/nonexistent/godot-x")
        finally:
            del os.environ["GODOT_BIN"]

    def test_bad_override_raises_missing_binary_not_a_raw_oserror(self):
        # IMPORTANT 3: find_binary() must keep returning the override
        # unconditionally (test_env_override_wins pins that contract), so
        # the validation has to happen where the binary is actually
        # invoked: run() must translate the resulting FileNotFoundError into
        # this module's own MissingBinary, not leak a bare traceback.
        os.environ["GODOT_BIN"] = "/nonexistent/godot-x"
        try:
            with self.assertRaises(engine.MissingBinary):
                engine.run(["--version"])
        finally:
            del os.environ["GODOT_BIN"]

    def test_finds_godot4_when_godot_is_absent(self):
        # IMPORTANT 4: untested branch, made testable with no engine
        # installed by monkeypatching shutil.which.
        os.environ.pop("GODOT_BIN", None)

        def fake_which(name):
            return "/usr/local/bin/godot4" if name == "godot4" else None

        with mock.patch.object(engine.shutil, "which", side_effect=fake_which):
            self.assertEqual(engine.find_binary(), "/usr/local/bin/godot4")

    def test_finds_mac_app_bundle_when_nothing_is_on_path(self):
        # IMPORTANT 4: same technique, one fallback further.
        os.environ.pop("GODOT_BIN", None)
        with mock.patch.object(engine.shutil, "which", return_value=None), \
             mock.patch.object(engine.os.path, "isfile", return_value=True):
            self.assertEqual(engine.find_binary(), engine.MAC_APP)

    def test_returns_none_when_nothing_is_found_anywhere(self):
        os.environ.pop("GODOT_BIN", None)
        with mock.patch.object(engine.shutil, "which", return_value=None), \
             mock.patch.object(engine.os.path, "isfile", return_value=False):
            self.assertIsNone(engine.find_binary())


if __name__ == "__main__":
    unittest.main()
