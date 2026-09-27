import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import tscn

FIXTURES = Path(__file__).parent / "fixtures" / "scenes"


def load(name):
    return (FIXTURES / name).read_text()


class TestParse(unittest.TestCase):
    def test_heading_kinds_and_attrs(self):
        blocks = tscn.parse(load("simple.tscn"))
        kinds = [b.kind for b in blocks]
        self.assertEqual(kinds, ["gd_scene", "ext_resource", "node", "node"])
        self.assertEqual(blocks[0].attrs["uid"], "uid://cecaux1sm7mo0")
        self.assertEqual(blocks[0].attrs["format"], "3")

    def test_comments_and_blank_lines_ignored(self):
        blocks = tscn.parse(load("simple.tscn"))
        self.assertEqual(len(blocks), 4)

    def test_properties_attach_to_preceding_heading(self):
        blocks = tscn.parse(load("simple.tscn"))
        self.assertEqual(blocks[2].props["script"], 'ExtResource("1_abc")')
        self.assertEqual(blocks[3].props["position"], "Vector2(10, 20)")

    def test_multiline_property_value_is_joined(self):
        blocks = tscn.parse(load("nested.tscn"))
        deep = [b for b in blocks if b.attrs.get("name") == "Deep"][0]
        self.assertIn("300, 200", deep.props["polygon"])
        self.assertTrue(deep.props["polygon"].startswith("PackedVector2Array("))

    def test_deprecated_load_steps_does_not_break_parsing(self):
        blocks = tscn.parse(load("legacy_load_steps.tscn"))
        self.assertEqual(blocks[0].kind, "gd_scene")
        self.assertEqual(blocks[0].attrs["load_steps"], "2")

    def test_malformed_line_raises_with_line_number(self):
        with self.assertRaises(tscn.TscnParseError) as ctx:
            tscn.parse(load("malformed.tscn"))
        self.assertEqual(ctx.exception.line_no, 4)


class TestSceneTree(unittest.TestCase):
    def test_root_and_child_paths(self):
        root = tscn.scene_tree(tscn.parse(load("simple.tscn")))
        self.assertEqual(root.name, "Main")
        self.assertEqual(root.path, ".")
        self.assertEqual([c.name for c in root.children], ["Sprite"])
        self.assertEqual(root.children[0].path, "Sprite")

    def test_nested_parent_paths(self):
        root = tscn.scene_tree(tscn.parse(load("nested.tscn")))
        body = root.children[0]
        shape = body.children[0]
        deep = shape.children[0]
        self.assertEqual(body.path, "Body")
        self.assertEqual(shape.path, "Body/Shape")
        self.assertEqual(deep.path, "Body/Shape/Deep")

    def test_unknown_parent_raises(self):
        text = '[gd_scene format=3]\n\n[node name="A" type="Node"]\n\n[node name="B" type="Node" parent="Ghost"]\n'
        with self.assertRaises(tscn.TscnParseError):
            tscn.scene_tree(tscn.parse(text))


class TestExtResources(unittest.TestCase):
    def test_extracts_path_uid_type_id(self):
        res = tscn.ext_resources(tscn.parse(load("simple.tscn")))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["path"], "res://scripts/player.gd")
        self.assertEqual(res[0]["uid"], "uid://cnnyipgx21jca")
        self.assertEqual(res[0]["type"], "Script")
        self.assertEqual(res[0]["id"], "1_abc")


class TestEngineAttrs(unittest.TestCase):
    """Real Godot 4.7.2 output (engine_quirks.tscn was produced by a headless
    ResourceSaver.save() run, not hand-typed) exercises heading attributes
    whose values contain brackets, commas, and internal spaces. A parser that
    merely fails to raise on these is not enough: it must recover the exact
    value, because a silently truncated array reads as complete to anything
    downstream.
    """

    def test_block_count_and_kinds_are_not_mis_scoped(self):
        blocks = tscn.parse(load("engine_quirks.tscn"))
        kinds = [b.kind for b in blocks]
        self.assertEqual(
            kinds,
            [
                "gd_scene",
                "ext_resource",
                "ext_resource",
                "node",
                "node",
                "node",
                "node",
                "node",
                "connection",
            ],
        )

    def test_group_membership_is_not_truncated(self):
        blocks = tscn.parse(load("engine_quirks.tscn"))
        enemy = [b for b in blocks if b.attrs.get("name") == "Enemy"][0]
        self.assertEqual(enemy.attrs["groups"], '["damageable", "enemies"]')

    def test_multiple_node_paths_entries_are_not_truncated(self):
        blocks = tscn.parse(load("engine_quirks.tscn"))
        holder = [b for b in blocks if b.attrs.get("name") == "Holder"][0]
        self.assertEqual(
            holder.attrs["node_paths"],
            'PackedStringArray("target_a", "target_b")',
        )

    def test_connection_binds_survives_engines_space_after_equals(self):
        blocks = tscn.parse(load("engine_quirks.tscn"))
        connection = [b for b in blocks if b.kind == "connection"][0]
        self.assertEqual(connection.attrs["signal"], "tree_exiting")
        self.assertEqual(connection.attrs["binds"], '["extra", 42]')

    def test_scene_tree_still_builds_around_bracketed_attrs(self):
        root = tscn.scene_tree(tscn.parse(load("engine_quirks.tscn")))
        self.assertEqual(root.name, "Root")
        self.assertEqual(
            sorted(c.name for c in root.children),
            ["Enemy", "Holder", "TargetA", "TargetB"],
        )


if __name__ == "__main__":
    unittest.main()
