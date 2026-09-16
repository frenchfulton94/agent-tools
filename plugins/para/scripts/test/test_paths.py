import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import para_paths as pp


class ValidateRoot(unittest.TestCase):
    def test_refuses_home(self):
        with self.assertRaises(pp.UnsafeRoot):
            pp.validate_root(os.path.expanduser("~"))

    def test_refuses_filesystem_root(self):
        with self.assertRaises(pp.UnsafeRoot):
            pp.validate_root("/")

    def test_refuses_a_file(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "a.txt"
            f.write_text("x")
            with self.assertRaises(pp.UnsafeRoot):
                pp.validate_root(str(f))

    def test_accepts_an_ordinary_directory(self):
        with tempfile.TemporaryDirectory() as d:
            sub = pathlib.Path(d) / "Documents"
            sub.mkdir()
            self.assertEqual(pp.validate_root(str(sub)), sub.resolve())


class Globs(unittest.TestCase):
    def test_matches_dotfile_pattern(self):
        root = pathlib.Path("/r")
        self.assertTrue(pp.matches_any(root / "x" / ".env.local", root, ["**/.env*"]))

    def test_does_not_match_unrelated(self):
        root = pathlib.Path("/r")
        self.assertFalse(pp.matches_any(root / "notes.md", root, ["**/.env*"]))


class SafeDestination(unittest.TestCase):
    def test_returns_original_when_free(self):
        with tempfile.TemporaryDirectory() as d:
            dest = pathlib.Path(d) / "a.pdf"
            self.assertEqual(pp.safe_destination(dest), dest)

    def test_appends_counter_on_collision(self):
        with tempfile.TemporaryDirectory() as d:
            dest = pathlib.Path(d) / "a.pdf"
            dest.write_text("x")
            self.assertEqual(pp.safe_destination(dest).name, "a (2).pdf")

    def test_counts_past_an_existing_counter(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "a.pdf").write_text("x")
            (pathlib.Path(d) / "a (2).pdf").write_text("x")
            self.assertEqual(
                pp.safe_destination(pathlib.Path(d) / "a.pdf").name, "a (3).pdf"
            )


if __name__ == "__main__":
    unittest.main()
