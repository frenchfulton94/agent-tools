import os
import tempfile
import unittest
from pathlib import Path
import sys

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


@unittest.skipUnless(HAS_DISPLAY, "needs godot and a display")
class TestScreenshot(unittest.TestCase):
    def test_captures_a_non_empty_png_without_touching_the_project(self):
        before = sorted(p.name for p in SAMPLE.iterdir())
        out = Path(tempfile.mkdtemp()) / "shot.png"
        result = render.screenshot_scene(str(SAMPLE), "res://main.tscn", str(out))
        self.assertTrue(out.is_file())
        self.assertGreater(out.stat().st_size, 100)
        self.assertEqual(result["path"], str(out))
        after = sorted(p.name for p in SAMPLE.iterdir())
        created = set(after) - set(before)
        self.assertTrue(
            created <= {".godot"} or all(c.endswith(".uid") for c in created),
            f"screenshot wrote unexpected files into the project: {created}",
        )


if __name__ == "__main__":
    unittest.main()
