import json
import os
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
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._prev = os.environ.get("PARA_ROOTS_FILE")
        os.environ["PARA_ROOTS_FILE"] = str(pathlib.Path(self._tmp.name) / "roots")

    def tearDown(self):
        if self._prev is None:
            os.environ.pop("PARA_ROOTS_FILE", None)
        else:
            os.environ["PARA_ROOTS_FILE"] = self._prev
        self._tmp.cleanup()

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

    def test_a_truncated_final_line_costs_only_itself(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("alpha")
            (root / "b.pdf").write_text("beta")
            plan = {
                "version": 1, "root": str(root),
                "groups": [{
                    "id": "g1", "rule": "r", "reason": "w", "destination": "4-Archives",
                    "count": 2, "samples": [], "files": ["a.pdf", "b.pdf"],
                }],
            }
            manifest = pathlib.Path(ap.apply_plan(plan, root)["manifest"])
            manifest.write_text(manifest.read_text() + '{"from": "c.pdf", "to": "4-Archiv')
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 2)
            self.assertEqual((root / "a.pdf").read_text(), "alpha")
            self.assertEqual((root / "b.pdf").read_text(), "beta")
            self.assertIn("unreadable manifest line", [s["reason"] for s in result["skipped"]])

    def test_a_line_missing_a_key_costs_only_itself(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            manifest = pathlib.Path(moved_fixture(root))
            manifest.write_text(manifest.read_text() + json.dumps({"from": "z.pdf"}) + "\n")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 1)
            self.assertIn("unreadable manifest line", [s["reason"] for s in result["skipped"]])

    def test_refuses_an_absolute_manifest_path(self):
        with tempfile.TemporaryDirectory() as outer:
            o = pathlib.Path(outer)
            victim = o / "victim.txt"
            victim.write_text("SECRET")
            root = o / "root"
            (root / ".para").mkdir(parents=True)
            manifest = root / ".para" / "undo-x.jsonl"
            info = victim.lstat()
            manifest.write_text(json.dumps({
                "from": "pulled-in.txt", "to": str(victim),
                "size": info.st_size, "mtime_ns": info.st_mtime_ns, "inode": info.st_ino,
            }) + "\n")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 0)
            self.assertEqual(result["skipped"][0]["reason"], "manifest path escapes the root")
            self.assertTrue(victim.exists())

    def test_refuses_a_traversing_manifest_path(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / ".para").mkdir()
            manifest = root / ".para" / "undo-x.jsonl"
            manifest.write_text(json.dumps({
                "from": "ok.txt", "to": "../escape.txt",
                "size": 1, "mtime_ns": 1, "inode": 1,
            }) + "\n")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 0)
            self.assertEqual(result["skipped"][0]["reason"], "manifest path escapes the root")

    def test_a_non_string_manifest_path_costs_only_itself(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("alpha")
            (root / "b.pdf").write_text("beta")
            plan = {
                "version": 1, "root": str(root),
                "groups": [{
                    "id": "g1", "rule": "r", "reason": "w", "destination": "4-Archives",
                    "count": 2, "samples": [], "files": ["a.pdf", "b.pdf"],
                }],
            }
            manifest = pathlib.Path(ap.apply_plan(plan, root)["manifest"])
            manifest.write_text(manifest.read_text() + json.dumps(
                {"from": "c.pdf", "to": 42, "size": 1, "mtime_ns": 1, "inode": 1}) + "\n")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 2)
            self.assertEqual((root / "a.pdf").read_text(), "alpha")
            self.assertEqual((root / "b.pdf").read_text(), "beta")
            self.assertIn("unreadable manifest line", [s["reason"] for s in result["skipped"]])

    def test_an_empty_manifest_path_costs_only_itself(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("alpha")
            plan = {
                "version": 1, "root": str(root),
                "groups": [{
                    "id": "g1", "rule": "r", "reason": "w", "destination": "4-Archives",
                    "count": 1, "samples": [], "files": ["a.pdf"],
                }],
            }
            manifest = pathlib.Path(ap.apply_plan(plan, root)["manifest"])
            info = root.lstat()
            manifest.write_text(manifest.read_text() + json.dumps({
                "from": "recovered.pdf", "to": "",
                "size": info.st_size, "mtime_ns": info.st_mtime_ns, "inode": info.st_ino,
            }) + "\n")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 1)
            self.assertEqual((root / "a.pdf").read_text(), "alpha")
            self.assertTrue(root.is_dir())

    def test_an_empty_origin_does_not_restore_outside_the_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "4-Archives").mkdir()
            (root / "4-Archives" / "a.pdf").write_text("alpha")
            (root / ".para").mkdir()
            manifest = root / ".para" / "undo-x.jsonl"
            info = (root / "4-Archives" / "a.pdf").lstat()
            manifest.write_text(json.dumps({
                "from": "", "to": "4-Archives/a.pdf",
                "size": info.st_size, "mtime_ns": info.st_mtime_ns, "inode": info.st_ino,
            }) + "\n")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 0)
            self.assertFalse(root.parent.joinpath(f"{root.name} (2)").exists())
            self.assertTrue((root / "4-Archives" / "a.pdf").exists())

    def test_pathological_unicode_costs_only_itself(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("alpha")
            (root / "b.pdf").write_text("beta")
            plan = {
                "version": 1, "root": str(root),
                "groups": [{
                    "id": "g1", "rule": "r", "reason": "w", "destination": "4-Archives",
                    "count": 2, "samples": [], "files": ["a.pdf", "b.pdf"],
                }],
            }
            manifest = pathlib.Path(ap.apply_plan(plan, root)["manifest"])
            archived = root / "4-Archives" / "a.pdf"
            info = archived.lstat()
            for hostile in ("\ud800", "a\x00b"):
                manifest.write_text(manifest.read_text() + json.dumps({
                    "from": hostile, "to": "4-Archives/a.pdf",
                    "size": info.st_size, "mtime_ns": info.st_mtime_ns, "inode": info.st_ino,
                }) + "\n")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 2)
            self.assertEqual((root / "a.pdf").read_text(), "alpha")
            self.assertEqual((root / "b.pdf").read_text(), "beta")


if __name__ == "__main__":
    unittest.main()
