import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import project

SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"


class TestParseCfg(unittest.TestCase):
    def test_sections_and_keys(self):
        cfg = project.parse_cfg((SAMPLE / "project.godot").read_text())
        self.assertEqual(cfg["application"]["config/name"], '"Sample"')
        self.assertEqual(cfg["rendering"]["renderer/rendering_method"], '"forward_plus"')

    def test_multiline_value_is_joined(self):
        cfg = project.parse_cfg((SAMPLE / "project.godot").read_text())
        self.assertIn("deadzone", cfg["input"]["jump"])

    def test_leading_keys_without_section(self):
        cfg = project.parse_cfg((SAMPLE / "project.godot").read_text())
        self.assertEqual(cfg[""]["config_version"], "5")

    def test_unterminated_multiline_value_raises(self):
        text = """[section]
key={
"deadzone": 0.5,
"""
        with self.assertRaises(ValueError) as ctx:
            project.parse_cfg(text)
        self.assertIn("Value not closed", str(ctx.exception))
        self.assertIn("section", str(ctx.exception))
        self.assertIn("key", str(ctx.exception))


class TestOverview(unittest.TestCase):
    def setUp(self):
        self.ov = project.overview(str(SAMPLE))

    def test_name_and_main_scene(self):
        self.assertEqual(self.ov["name"], "Sample")
        self.assertEqual(self.ov["main_scene"], "res://main.tscn")

    def test_features(self):
        self.assertIn("4.4", self.ov["features"])

    def test_autoloads_strip_the_singleton_marker(self):
        self.assertEqual(self.ov["autoloads"]["GameState"], "res://scripts/game_state.gd")
        self.assertEqual(self.ov["autoloads"]["Audio"], "res://scripts/audio.gd")

    def test_input_actions(self):
        self.assertEqual(sorted(self.ov["input_actions"]), ["fire", "jump"])

    def test_rendering_method(self):
        self.assertEqual(self.ov["rendering_method"], "forward_plus")

    def test_export_presets(self):
        presets = self.ov["export_presets"]
        self.assertEqual(len(presets), 2)
        # Verify numeric sorting: preset.0 should come first even though preset.1 appears first in the file
        self.assertEqual(presets[0]["name"], "macOS")
        self.assertEqual(presets[0]["platform"], "macOS")
        self.assertTrue(presets[0]["runnable"])
        self.assertEqual(presets[1]["name"], "Web")
        self.assertEqual(presets[1]["export_path"], "builds/web/index.html")
        self.assertFalse(presets[1]["runnable"])


class TestFindRoot(unittest.TestCase):
    def test_finds_root_from_nested_path(self):
        found = project.find_root(str(SAMPLE / "scripts"))
        self.assertEqual(Path(found).resolve(), SAMPLE.resolve())

    def test_returns_none_outside_a_project(self):
        self.assertIsNone(project.find_root("/"))


if __name__ == "__main__":
    unittest.main()
