import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import para_index as pi
import scan

DAY = 86400


def touch(path, age_days=0, content="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    when = time.time() - age_days * DAY
    os.utime(path, (when, when))
    return path


class Walk(unittest.TestCase):
    def test_treats_a_package_as_one_item(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "Thing.rtfd" / "Contents" / "Info.plist")
            entries, _ = scan.walk(root, pi.Index())
            rels = [e["rel"] for e in entries]
            self.assertIn("Thing.rtfd", rels)
            self.assertNotIn("Thing.rtfd/Contents/Info.plist", rels)

    def test_skips_an_app_bundle_as_never_move(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "Thing.app" / "Contents" / "Info.plist")
            touch(root / "keep.txt")
            entries, stats = scan.walk(root, pi.Index())
            self.assertEqual([e["rel"] for e in entries], ["keep.txt"])
            self.assertEqual(stats["skipped_never_move"], 1)

    def test_skips_never_move_entries(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "keep.txt")
            touch(root / "node_modules" / "dep" / "index.js")
            entries, stats = scan.walk(root, pi.Index())
            self.assertEqual([e["rel"] for e in entries], ["keep.txt"])
            self.assertEqual(stats["skipped_never_move"], 1)

    def test_does_not_descend_into_the_skeleton(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "4-Archives" / "old.pdf")
            touch(root / "loose.pdf")
            entries, _ = scan.walk(root, pi.Index())
            self.assertEqual([e["rel"] for e in entries], ["loose.pdf"])


class Cluster(unittest.TestCase):
    def test_groups_old_files_by_year_of_last_use(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "old.pdf", age_days=800)
            touch(root / "fresh.pdf", age_days=3)
            entries, _ = scan.walk(root, pi.Index())
            clusters = scan.cluster(entries, pi.Index(), archive_after_months=12)
            age = [c for c in clusters if c["kind"] == "age"]
            self.assertEqual(len(age), 1)
            self.assertEqual(age[0]["files"], ["old.pdf"])
            self.assertTrue(age[0]["destination"].startswith("4-Archives/"))

    def test_matches_a_project_by_name(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "client-redesign-brief.docx", age_days=2)
            index = pi.Index(projects=["client-redesign"])
            entries, _ = scan.walk(root, index)
            clusters = scan.cluster(entries, index)
            match = [c for c in clusters if c["kind"] == "project-match"]
            self.assertEqual(match[0]["destination"], "1-Projects/client-redesign")

    def test_project_match_beats_age(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "client-redesign-old.docx", age_days=800)
            index = pi.Index(projects=["client-redesign"])
            entries, _ = scan.walk(root, index)
            clusters = scan.cluster(entries, index, archive_after_months=12)
            kinds = {c["kind"] for c in clusters}
            self.assertIn("project-match", kinds)
            self.assertNotIn("age", kinds)

    def test_unmatched_recent_files_go_to_inbox(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "mystery.bin", age_days=1)
            entries, _ = scan.walk(root, pi.Index())
            clusters = scan.cluster(entries, pi.Index())
            unresolved = [c for c in clusters if c["kind"] == "unresolved"]
            self.assertEqual(unresolved[0]["destination"], "0-Inbox")

    def test_every_file_lands_in_exactly_one_cluster(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "client-redesign.docx", age_days=2)
            touch(root / "old.pdf", age_days=900)
            touch(root / "mystery.bin", age_days=1)
            index = pi.Index(projects=["client-redesign"])
            entries, _ = scan.walk(root, index)
            clusters = scan.cluster(entries, index)
            placed = [f for c in clusters for f in c["files"]]
            self.assertEqual(sorted(placed), sorted(e["rel"] for e in entries))
            self.assertEqual(len(placed), len(set(placed)))

    def test_samples_are_capped_but_counts_are_not(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            for i in range(30):
                touch(root / f"old{i}.pdf", age_days=900)
            entries, _ = scan.walk(root, pi.Index())
            age = [c for c in scan.cluster(entries, pi.Index()) if c["kind"] == "age"][0]
            self.assertEqual(age["count"], 30)
            self.assertLessEqual(len(age["samples"]), 5)


class Cli(unittest.TestCase):
    def test_emits_json_and_refuses_home(self):
        script = str(pathlib.Path(__file__).resolve().parents[1] / "scan.py")
        with tempfile.TemporaryDirectory() as d:
            touch(pathlib.Path(d) / "a.txt")
            ok = subprocess.run([sys.executable, script, d], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0)
            self.assertEqual(json.loads(ok.stdout)["version"], 1)

        refused = subprocess.run(
            [sys.executable, script, os.path.expanduser("~")],
            capture_output=True, text=True,
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("home directory", refused.stderr)


class TierTwo(unittest.TestCase):
    def test_peek_reads_a_bounded_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            f = touch(pathlib.Path(d) / "notes.txt", content="client-redesign " * 500)
            self.assertLessEqual(len(scan.peek(f, 64).encode("utf-8")), 64)

    def test_peek_returns_empty_on_binary(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "blob.bin"
            f.write_bytes(b"\x00\x01\x02\xff" * 64)
            self.assertEqual(scan.peek(f, 128), "")

    def test_denylist_is_enforced_regardless_of_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            secret = touch(root / ".env.local", content="TOKEN=abc")
            index = pi.Index(never_read=["**/.env*"])
            opened = scan.peek_candidates([{"rel": ".env.local"}], root, index,
                                          peek_files=100)
            self.assertEqual(opened, [])
            self.assertTrue(secret.exists())

    def test_peek_budget_caps_file_count(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            entries = []
            for i in range(10):
                touch(root / f"f{i}.txt")
                entries.append({"rel": f"f{i}.txt"})
            opened = scan.peek_candidates(entries, root, pi.Index(), peek_files=3)
            self.assertEqual(len(opened), 3)

    def test_metadata_only_peeks_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "mystery.txt", content="client-redesign notes")
            result = scan.scan(root, metadata_only=True)
            self.assertEqual(result["peeked"], [])

    def test_spotlight_degrades_without_raising(self):
        with tempfile.TemporaryDirectory() as d:
            f = touch(pathlib.Path(d) / "a.txt")
            signals = scan.spotlight(f)
            self.assertIn("indexed", signals)
            self.assertIsInstance(signals["tags"], list)

    def test_never_reads_through_a_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            secret = root / "_outside_secret"
            secret.write_text("PRIVATE-MUST-NOT-BE-READ")
            inner = root / "tree"
            inner.mkdir()
            (inner / "notes.txt").symlink_to(secret)
            opened = scan.peek_candidates(
                [{"rel": "notes.txt"}], inner, pi.Index(), peek_files=999)
            self.assertEqual(opened, [])

    def test_denylist_matches_case_insensitively(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / ".ENV.LOCAL", content="TOKEN=leaked")
            opened = scan.peek_candidates(
                [{"rel": ".ENV.LOCAL"}], root, pi.Index(), peek_files=999)
            self.assertEqual(opened, [])


if __name__ == "__main__":
    unittest.main()
