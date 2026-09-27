import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import engine, render

SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"
HAS_GODOT = engine.find_binary() is not None
HAS_DISPLAY = HAS_GODOT and render.has_display()


class TestDriversExist(unittest.TestCase):
    def test_driver_scripts_are_packaged(self):
        self.assertTrue(render.DRIVER_SCREENSHOT.is_file())
        self.assertTrue(render.DRIVER_SHADER.is_file())


@unittest.skipUnless(HAS_DISPLAY, "needs godot and a display")
class TestShaderCheck(unittest.TestCase):
    def test_good_shader_reports_nothing(self):
        self.assertEqual(render.check_shader(str(SAMPLE), "res://good.gdshader"), [])

    def test_broken_shader_is_reported(self):
        # Spec 3.5: the headless path passes this silently. This test is the
        # guard against anyone "optimising" check_shader to run headless.
        found = render.check_shader(str(SAMPLE), "res://bad.gdshader")
        self.assertTrue(found)
        self.assertTrue(any(d["severity"] == "SHADER ERROR" for d in found))
        self.assertTrue(any(d.get("line") == 4 for d in found))

    def test_headless_really_does_pass_the_broken_shader(self):
        result = engine.run(
            ["--headless", "--path", str(SAMPLE), "--quit-after", "2"], timeout=30
        )
        self.assertFalse(
            [d for d in engine.diagnostics(result.stderr) if d["severity"] == "SHADER ERROR"]
        )

    def test_broken_shader_via_include_is_not_dropped(self):
        # Measured against the real engine: a shader whose bug lives in a
        # #include'd file (badinclude.gdshader -> common.gdshaderinc) is
        # reported as "SHADER ERROR ... at: (res://common.gdshaderinc:2)" --
        # a real, located error, but not in a file ending ".gdshader". A
        # filter keyed on that literal suffix drops it silently. Guards
        # against reintroducing that filter.
        found = render.check_shader(str(SAMPLE), "res://badinclude.gdshader")
        self.assertTrue(found, "a real compile error in an included file must not vanish")
        self.assertTrue(any(d["severity"] == "SHADER ERROR" for d in found))

    def test_missing_shader_is_reported_not_swallowed(self):
        # Measured against the real engine: a shader_res_path that does not
        # exist produces "ERROR: Cannot load shader: res://..." and "ERROR:
        # Failed loading resource: res://...." -- both located only in
        # engine C++ (file=None), so a filter requiring a res:// location
        # drops them too, and check_shader would report "no errors" for a
        # shader that never loaded at all.
        found = render.check_shader(str(SAMPLE), "res://does_not_exist.gdshader")
        self.assertTrue(found, "an unloadable shader path must not be reported as clean")


class TestCheckShaderPathAnchoring(unittest.TestCase):
    """IMPORTANT 2 pin: `shader_res_path in d["message"]` is an unanchored
    substring test. A project with both "good.gdshader" and
    "good.gdshader_backup_v2.gdshader" (or any printerr mentioning a longer
    path with the checked one as a literal prefix) would have the unrelated
    file's errors misattributed to the shader actually being checked.

    Runs entirely against a mocked engine.run with synthetic stderr, so it
    needs neither Godot nor a display and always executes.
    """

    def _check(self, shader_path, stderr):
        with mock.patch.object(
            render.engine, "run",
            return_value=engine.Result(stdout="", stderr=stderr, returncode=1, timed_out=False),
        ), mock.patch.object(render, "has_display", return_value=True):
            return render.check_shader(str(SAMPLE), shader_path)

    def test_prefix_collision_with_a_longer_similarly_named_file_is_rejected(self):
        stderr = (
            'ERROR: Failed to load resource res://good.gdshader_backup_v2.gdshader: bogus reason\n'
            '   at: load (modules/whatever/thing.cpp:12)\n'
        )
        self.assertEqual(self._check("res://good.gdshader", stderr), [])

    def test_real_cannot_load_shader_message_still_matches(self):
        # End-of-string after the path -- the real shape of this message.
        stderr = (
            'ERROR: Cannot load shader: res://good.gdshader\n'
            '   at: load (scene/resources/shader_resource_format.cpp:43)\n'
        )
        self.assertEqual(len(self._check("res://good.gdshader", stderr)), 1)

    def test_real_failed_loading_resource_message_still_matches(self):
        # A "." immediately follows the path -- also real, also not a \w char.
        stderr = (
            'ERROR: Failed loading resource: res://good.gdshader.\n'
            '   at: _load (core/io/resource_loader.cpp:317)\n'
        )
        self.assertEqual(len(self._check("res://good.gdshader", stderr)), 1)


class TestCheckShaderTimeout(unittest.TestCase):
    """IMPORTANT 3 pin: a timed-out compile attempt is not the same fact as
    a clean compile, and must not fall through to the same empty list.
    Mocked -- no real engine or display needed to prove the branch exists.
    """

    def test_a_timed_out_compile_raises_rather_than_reporting_clean(self):
        with mock.patch.object(
            render.engine, "run",
            return_value=engine.Result(stdout="", stderr="", returncode=-1, timed_out=True),
        ), mock.patch.object(render, "has_display", return_value=True):
            with self.assertRaises(render.ShaderCheckTimedOut):
                render.check_shader(str(SAMPLE), "res://good.gdshader", timeout=1)


@unittest.skipUnless(HAS_DISPLAY, "needs godot and a display")
class TestCheckShaderRealTimeout(unittest.TestCase):
    def test_forced_short_timeout_raises_rather_than_returning_a_clean_verdict(self):
        # Against the real engine: 0.05s cannot possibly let Godot boot,
        # load the project, and compile a shader, so this must always hit
        # the timeout path, never a real verdict.
        with self.assertRaises(render.ShaderCheckTimedOut):
            render.check_shader(str(SAMPLE), "res://good.gdshader", timeout=0.05)


class TestHasDisplayDarwin(unittest.TestCase):
    """IMPORTANT 4 pin: has_display() used to return True unconditionally on
    darwin, so the NoDisplay guard could never fire there -- a headless
    macOS CI runner or LaunchDaemon would hit a raw renderer error instead
    of the clear message the guard exists to give. Mocked subprocess.run,
    so these do not depend on this machine's own actual session state.
    """

    def test_launchctl_exit_zero_means_display(self):
        with mock.patch.object(render.sys, "platform", "darwin"), \
             mock.patch.object(render.subprocess, "run", return_value=mock.Mock(returncode=0)):
            self.assertTrue(render.has_display())

    def test_launchctl_nonzero_exit_means_no_display(self):
        with mock.patch.object(render.sys, "platform", "darwin"), \
             mock.patch.object(render.subprocess, "run", return_value=mock.Mock(returncode=1)):
            self.assertFalse(render.has_display())

    def test_missing_launchctl_means_no_display_not_a_crash(self):
        with mock.patch.object(render.sys, "platform", "darwin"), \
             mock.patch.object(render.subprocess, "run", side_effect=OSError("no such command")):
            self.assertFalse(render.has_display())


@unittest.skipUnless(sys.platform == "darwin", "darwin-specific launchctl check")
class TestHasDisplayRealLaunchctl(unittest.TestCase):
    def test_real_launchctl_check_succeeds_on_this_dev_machine(self):
        # Not mocked: this machine has an interactive GUI session, so the
        # real subprocess call must agree.
        self.assertTrue(render.has_display())


class TestDriveEnvIsolation(unittest.TestCase):
    """CRITICAL 1 pin: _drive must never mutate process-wide os.environ.
    Old shape (os.environ.update(), restore in a finally, no lock) let one
    concurrent call's update win before another call's subprocess actually
    read the environment -- reproduced by the reviewer 3/3 with ordinary
    threading, no adversarial timing: two concurrent check_shader calls on
    DIFFERENT shaders both reported the SAME (wrong, for one of them)
    verdict.

    A barrier forces both calls to have already finished whatever
    env-preparation they do (the old mutate, or the new local-dict build)
    before either is inspected -- under the old code this guarantees a
    shared os.environ has already been stomped by whichever call updated
    it last by the time both reads happen; under the new code each call's
    env is a value fully local to its own stack, so the interleaving can't
    touch it no matter how it's forced.
    """

    def test_two_concurrent_check_shader_calls_never_cross_contaminate_env(self):
        # A bare threading.Barrier tried first here was NOT reliable: it
        # only guarantees both calls have done their own env-preparation
        # before either is inspected, not that the two inspections actually
        # overlap -- once released, a GIL-holding thread can run its own
        # read-and-restore to completion in one burst before the other ever
        # gets scheduled, in which case each thread happens to see its own
        # correct value even under the OLD buggy _drive (I confirmed this:
        # the barrier version passed against the reverted, unfixed code,
        # which means it wasn't testing anything). Event-staged instead, to
        # force the EXACT interleaving the bug needs: thread B's update must
        # still be active (not yet restored) at the moment thread A reads.
        recorded = {}
        a_updated = threading.Event()
        a_may_read = threading.Event()
        b_updated_and_read = threading.Event()
        b_may_finish = threading.Event()

        def fake_run_a(args, cwd=None, timeout=60, env=None):
            a_updated.set()
            # Paused here: A has done its own env-prep (the old mutate, or
            # the new local-dict build) but has not yet "spawned" -- the
            # real vulnerable window.
            self.assertTrue(a_may_read.wait(timeout=5), "test deadlocked waiting to release A")
            value = (env if env is not None else os.environ).get("GODOT_MCP_SHADER")
            recorded["a"] = value
            return engine.Result(stdout="", stderr="", returncode=0, timed_out=False)

        def fake_run_b(args, cwd=None, timeout=60, env=None):
            value = (env if env is not None else os.environ).get("GODOT_MCP_SHADER")
            recorded["b"] = value
            b_updated_and_read.set()
            # Held open deliberately: under the old code, B's os.environ
            # mutation is still live here, not yet restored by B's own
            # `finally` (that only runs once this call returns) -- exactly
            # the window the bug needs A to read through.
            self.assertTrue(b_may_finish.wait(timeout=5), "test deadlocked waiting to release B")
            return engine.Result(stdout="", stderr="", returncode=0, timed_out=False)

        def fake_run(args, cwd=None, timeout=60, env=None):
            if threading.current_thread().name == "checker-a":
                return fake_run_a(args, cwd=cwd, timeout=timeout, env=env)
            return fake_run_b(args, cwd=cwd, timeout=timeout, env=env)

        with mock.patch.object(render.engine, "run", side_effect=fake_run), \
             mock.patch.object(render, "has_display", return_value=True):
            t_a = threading.Thread(
                target=render.check_shader, args=(str(SAMPLE), "res://good.gdshader"),
                name="checker-a",
            )
            t_a.start()
            self.assertTrue(a_updated.wait(timeout=5), "thread A never reached its own env-prep")

            t_b = threading.Thread(
                target=render.check_shader, args=(str(SAMPLE), "res://bad.gdshader"),
                name="checker-b",
            )
            t_b.start()
            self.assertTrue(
                b_updated_and_read.wait(timeout=5), "thread B never reached its own read"
            )

            # B's value is live (and, under the bug, is what a shared
            # os.environ now holds) but B has not yet restored anything.
            # Let A read NOW, precisely inside that window.
            a_may_read.set()
            t_a.join(timeout=5)

            b_may_finish.set()
            t_b.join(timeout=5)

        self.assertEqual(
            recorded.get("a"), "res://good.gdshader",
            f"thread A (checking good.gdshader) saw {recorded}",
        )
        self.assertEqual(
            recorded.get("b"), "res://bad.gdshader",
            f"thread B (checking bad.gdshader) saw {recorded}",
        )
        self.assertNotIn(
            "GODOT_MCP_SHADER", os.environ,
            "_drive must never leave its env vars in the real process environment",
        )


@unittest.skipUnless(HAS_DISPLAY, "needs godot and a display")
class TestScreenshot(unittest.TestCase):
    def test_captures_a_non_empty_png_without_touching_the_project(self):
        before = sorted(p.name for p in SAMPLE.iterdir())
        out = Path(tempfile.mkdtemp()) / "shot.png"
        # 320x240 matches main.tscn's Probe ColorRect exactly (offset_right
        # = 320.0, offset_bottom = 240.0, no anchors -- anchors would
        # collapse to degenerate here since Probe's parent, Main, is a
        # Node2D and provides no Control rect for anchors to resolve
        # against; absolute offsets are what actually cover the viewport).
        # A solid-colour PNG compresses to nearly the same byte count as a
        # blank one (measured: ~790 bytes either way), so file size alone
        # cannot tell a real capture from an empty one -- the pixel probe
        # below is the actual content assertion; size is only a smoke check.
        result = render.screenshot_scene(
            str(SAMPLE), "res://main.tscn", str(out), width=320, height=240
        )
        self.assertTrue(out.is_file())
        self.assertGreater(out.stat().st_size, 100)
        self.assertEqual(result["path"], str(out))

        self.assertIsNotNone(result["pixel"], "screenshot.gd did not print a GODOT_MCP_PIXEL line")
        r, g, b = result["pixel"]
        # Tolerance, not bit-exact: exact (255, 0, 0) was only verified on
        # one GPU/driver (Metal/Forward+ on this machine) -- gamma handling
        # may differ elsewhere.
        self.assertAlmostEqual(r, 255, delta=20)
        self.assertAlmostEqual(g, 0, delta=20)
        self.assertAlmostEqual(b, 0, delta=20)

        after = sorted(p.name for p in SAMPLE.iterdir())
        created = set(after) - set(before)
        self.assertTrue(
            created <= {".godot"} or all(c.endswith(".uid") for c in created),
            f"screenshot wrote unexpected files into the project: {created}",
        )


if __name__ == "__main__":
    unittest.main()
