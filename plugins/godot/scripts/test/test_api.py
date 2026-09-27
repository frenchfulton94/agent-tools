import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import api, engine

HAS_GODOT = engine.find_binary() is not None

FAKE_DUMP = {
    "header": {"version_full_name": "Godot Engine v4.7.2.stable.official"},
    "classes": [
        {"name": "Object", "inherits": None, "brief_description": "Base class.",
         "description": "", "methods": [], "properties": [], "signals": []},
        {"name": "Node", "inherits": "Object", "brief_description": "Base class for scene objects.",
         "description": "", "methods": [{"name": "add_child", "description": "Adds a child."}],
         "properties": [], "signals": [{"name": "ready", "description": "Emitted when ready."}]},
        {"name": "Node2D", "inherits": "Node", "brief_description": "A 2D game object.",
         "description": "", "methods": [], "properties": [], "signals": []},
        {"name": "CharacterBody2D", "inherits": "PhysicsBody2D",
         "brief_description": "A 2D physics body specialized for characters moved by script.",
         "description": "", "methods": [], "properties": [], "signals": []},
    ],
}


class TestLookupAndSearch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        api._CACHE.clear()
        (Path(self.tmp) / "extension_api.json").write_text(json.dumps(FAKE_DUMP))
        # NOTE: this must match what engine_version() actually returns, or
        # load_dump() sees a version mismatch against the live engine, deletes
        # this fixture, and regenerates from the real ~1,036-class dump --
        # silently making every assertion below exercise the real engine
        # instead of FAKE_DUMP. `godot --version` prints a bare
        # "4.7.2.stable.official.ed1daf0bf" (no "Godot Engine v" prefix, plus
        # a build hash), not the brief's original literal. When no binary is
        # present, engine_version() raises MissingBinary, which load_dump()
        # already handles by serving the cache -- so this stays hermetic
        # whether or not Godot is installed.
        (Path(self.tmp) / "VERSION").write_text(
            api.engine_version() if engine.find_binary() else "test"
        )

    def test_lookup_returns_inheritance_chain(self):
        found = api.lookup_class("Node2D", cache_dir=self.tmp)
        self.assertEqual(found["inheritance_chain"], ["Node", "Object"])

    def test_lookup_is_case_insensitive(self):
        self.assertIsNotNone(api.lookup_class("node2d", cache_dir=self.tmp))

    def test_lookup_unknown_class_returns_none(self):
        self.assertIsNone(api.lookup_class("NoSuchClass", cache_dir=self.tmp))

    def test_lookup_single_member(self):
        found = api.lookup_class("Node", member="add_child", cache_dir=self.tmp)
        self.assertEqual(found["member"]["name"], "add_child")

    def test_search_matches_brief_description(self):
        hits = api.search_classes("characters moved by script", cache_dir=self.tmp)
        self.assertEqual(hits[0]["name"], "CharacterBody2D")

    def test_search_matches_name(self):
        names = [h["name"] for h in api.search_classes("node2d", cache_dir=self.tmp)]
        self.assertIn("Node2D", names)


@unittest.skipUnless(HAS_GODOT, "godot not on PATH")
class TestAgainstRealEngine(unittest.TestCase):
    def test_dump_is_generated_and_cached_by_version(self):
        tmp = tempfile.mkdtemp()
        api._CACHE.clear()
        dump = api.load_dump(cache_dir=tmp)
        self.assertGreater(len(dump["classes"]), 500)
        self.assertTrue((Path(tmp) / "extension_api.json").is_file())

    def test_real_class_carries_documentation(self):
        tmp = tempfile.mkdtemp()
        api._CACHE.clear()
        found = api.lookup_class("CharacterBody2D", cache_dir=tmp)
        self.assertIn("character", (found["brief_description"] or "").lower())


if __name__ == "__main__":
    unittest.main()
