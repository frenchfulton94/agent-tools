import json
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import apply as ap


def plan_with(groups, root):
    return {"version": 1, "root": str(root), "groups": groups}


def group(files, destination, gid="g1"):
    return {
        "id": gid, "rule": "r", "reason": "why", "destination": destination,
        "count": len(files), "samples": files[:5], "files": files,
    }


class Validate(unittest.TestCase):
    def test_rejects_a_missing_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            errors = ap.validate_plan(plan_with([group(["ghost.pdf"], "0-Inbox")], root), root)
            self.assertTrue(any("ghost.pdf" in e for e in errors))

    def test_rejects_a_file_claimed_by_two_groups(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("x")
            plan = plan_with(
                [group(["a.pdf"], "0-Inbox", "g1"), group(["a.pdf"], "4-Archives", "g2")],
                root,
            )
            self.assertTrue(any("claimed by two" in e for e in ap.validate_plan(plan, root)))

    def test_rejects_an_escaping_destination(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("x")
            plan = plan_with([group(["a.pdf"], "../outside")], root)
            self.assertTrue(any("outside the root" in e for e in ap.validate_plan(plan, root)))

    def test_accepts_a_sound_plan(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("x")
            self.assertEqual(ap.validate_plan(plan_with([group(["a.pdf"], "0-Inbox")], root), root), [])

    def test_rejects_an_absolute_source_path(self):
        with tempfile.TemporaryDirectory() as outer:
            o = pathlib.Path(outer)
            victim = o / "victim.txt"
            victim.write_text("SECRET")
            root = o / "root"
            root.mkdir()
            errors = ap.validate_plan(plan_with([group([str(victim)], "0-Inbox")], root), root)
            self.assertTrue(errors)
            self.assertTrue(victim.exists())

    def test_rejects_a_group_with_no_destination(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.txt").write_text("x")
            (root / "b.txt").write_text("x")
            headless = group(["b.txt"], "0-Inbox", "g2")
            del headless["destination"]
            plan = plan_with([group(["a.txt"], "4-Archives", "g1"), headless], root)

            errors = ap.validate_plan(plan, root)
            self.assertTrue(any("missing a destination" in e for e in errors))

            # The whole point: the bad group is caught up front, so the good
            # group that precedes it never moves.
            with self.assertRaises(ap.InvalidPlan):
                ap.apply_plan(plan, root)
            self.assertTrue((root / "a.txt").exists())
            self.assertTrue((root / "b.txt").exists())
            self.assertFalse((root / "4-Archives").exists())

    def test_rejects_a_group_whose_destination_is_blank(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.txt").write_text("x")
            plan = plan_with([group(["a.txt"], "   ")], root)
            self.assertTrue(
                any("missing a destination" in e for e in ap.validate_plan(plan, root))
            )

    def test_rejects_a_traversing_source_path(self):
        with tempfile.TemporaryDirectory() as outer:
            o = pathlib.Path(outer)
            victim = o / "victim.txt"
            victim.write_text("SECRET")
            root = o / "root"
            root.mkdir()
            errors = ap.validate_plan(plan_with([group(["../victim.txt"], "0-Inbox")], root), root)
            self.assertTrue(errors)
            self.assertTrue(victim.exists())


class Apply(unittest.TestCase):
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

    def test_moves_files_and_writes_a_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("hello")
            result = ap.apply_plan(plan_with([group(["a.pdf"], "4-Archives/2024")], root), root)
            self.assertEqual(result["moved"], 1)
            self.assertFalse((root / "a.pdf").exists())
            self.assertEqual((root / "4-Archives" / "2024" / "a.pdf").read_text(), "hello")
            lines = pathlib.Path(result["manifest"]).read_text().strip().splitlines()
            self.assertEqual(json.loads(lines[0])["to"], "4-Archives/2024/a.pdf")

    def test_creates_the_skeleton_but_no_empty_subfolders(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("x")
            ap.apply_plan(plan_with([group(["a.pdf"], "0-Inbox")], root), root)
            for name in ("0-Inbox", "1-Projects", "2-Areas", "3-Resources", "4-Archives"):
                self.assertTrue((root / name).is_dir())
            self.assertEqual(list((root / "1-Projects").iterdir()), [])

    def test_renames_on_collision_and_records_the_real_destination(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("new")
            (root / "4-Archives").mkdir()
            (root / "4-Archives" / "a.pdf").write_text("existing")
            result = ap.apply_plan(plan_with([group(["a.pdf"], "4-Archives")], root), root)
            self.assertEqual((root / "4-Archives" / "a.pdf").read_text(), "existing")
            self.assertEqual((root / "4-Archives" / "a (2).pdf").read_text(), "new")
            entry = json.loads(pathlib.Path(result["manifest"]).read_text().strip())
            self.assertEqual(entry["to"], "4-Archives/a (2).pdf")

    def test_refuses_an_invalid_plan_whole(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("x")
            plan = plan_with([group(["a.pdf", "ghost.pdf"], "0-Inbox")], root)
            with self.assertRaises(ap.InvalidPlan):
                ap.apply_plan(plan, root)
            self.assertTrue((root / "a.pdf").exists())

    def test_does_not_rename_a_file_already_at_its_destination(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "0-Inbox").mkdir()
            (root / "0-Inbox" / "a.pdf").write_text("x")
            result = ap.apply_plan(plan_with([group(["0-Inbox/a.pdf"], "0-Inbox")], root), root)
            self.assertTrue((root / "0-Inbox" / "a.pdf").exists())
            self.assertFalse((root / "0-Inbox" / "a (2).pdf").exists())
            self.assertEqual(result["moved"], 0)

    def test_does_not_rename_when_the_destination_differs_only_by_case(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "0-Inbox").mkdir()
            (root / "0-Inbox" / "a.pdf").write_text("x")
            result = ap.apply_plan(plan_with([group(["0-Inbox/a.pdf"], "0-INBOX")], root), root)
            self.assertEqual(result["moved"], 0)
            self.assertFalse((root / "0-Inbox" / "a (2).pdf").exists())
            self.assertEqual((root / "0-Inbox" / "a.pdf").read_text(), "x")


if __name__ == "__main__":
    unittest.main()
