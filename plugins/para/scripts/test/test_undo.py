import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import apply as ap
import undo as un


def moved_fixture(root, content="hello"):
    (root / "a.pdf").write_text(content)
    plan = {
        "version": 1, "root": str(root),
        "groups": [{
            "id": "g1", "rule": "r", "reason": "why",
            "destination": "4-Archives/2024", "count": 1,
            "samples": ["a.pdf"], "files": ["a.pdf"],
        }],
    }
    return ap.apply_plan(plan, root)["manifest"]


class Undo(unittest.TestCase):
    def test_restores_a_moved_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            manifest = moved_fixture(root)
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 1)
            self.assertEqual((root / "a.pdf").read_text(), "hello")

    def test_refuses_a_file_modified_since_the_move(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            manifest = moved_fixture(root)
            (root / "4-Archives" / "2024" / "a.pdf").write_text("edited since")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 0)
            self.assertEqual(result["skipped"][0]["reason"], "modified since the move")
            self.assertFalse((root / "a.pdf").exists())

    def test_continues_past_a_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("one")
            (root / "b.pdf").write_text("two")
            plan = {
                "version": 1, "root": str(root),
                "groups": [{
                    "id": "g1", "rule": "r", "reason": "w",
                    "destination": "4-Archives", "count": 2,
                    "samples": [], "files": ["a.pdf", "b.pdf"],
                }],
            }
            manifest = ap.apply_plan(plan, root)["manifest"]
            (root / "4-Archives" / "a.pdf").write_text("changed")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 1)
            self.assertEqual(len(result["skipped"]), 1)
            self.assertEqual((root / "b.pdf").read_text(), "two")

    def test_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            manifest = moved_fixture(root)
            un.undo(manifest, root)
            second = un.undo(manifest, root)
            self.assertEqual(second["restored"], 0)
            self.assertEqual(second["skipped"][0]["reason"], "already restored")
            self.assertEqual((root / "a.pdf").read_text(), "hello")

    def test_restores_under_a_new_name_when_the_origin_is_occupied(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            manifest = moved_fixture(root)
            (root / "a.pdf").write_text("something new here")
            un.undo(manifest, root)
            self.assertEqual((root / "a.pdf").read_text(), "something new here")
            self.assertEqual((root / "a (2).pdf").read_text(), "hello")


if __name__ == "__main__":
    unittest.main()
