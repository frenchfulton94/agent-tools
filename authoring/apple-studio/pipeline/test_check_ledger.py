#!/usr/bin/env python3
"""Tests for check_ledger.py. Standard library only.

Run: python3 -m unittest test_check_ledger -v   (from this directory)

The ledger checker is the gate that proves every page of the reading corpus was
read: one ledger row per page, no strays, no malformed read_in_full values.
Fixtures sit in fixtures/ledger: a manifest, a sources file, a slices file, and
one ledger directory per failure mode.
"""
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
FX = HERE / "fixtures" / "ledger"
SCRIPT = HERE / "check_ledger.py"


def run(ledger, *extra, slices=None, sources=None):
    cmd = [sys.executable, str(SCRIPT), str(FX / "manifest.tsv"),
           str(sources or FX / "sources.tsv"), str(slices or FX / "slices.tsv"),
           str(ledger), *extra]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def copy_complete(dest):
    dest = pathlib.Path(dest)
    for f in (FX / "complete").glob("*.tsv"):
        (dest / f.name).write_text(f.read_text())
    return dest


class CheckLedger(unittest.TestCase):
    def test_complete_passes(self):
        code, out = run(FX / "complete")
        self.assertEqual(code, 0, out)

    def test_missing_row_fails(self):
        code, out = run(FX / "missing")
        self.assertEqual(code, 1, out)
        self.assertIn("missing: /documentation/x", out)

    def test_duplicate_row_fails(self):
        code, out = run(FX / "duplicate")
        self.assertEqual(code, 1, out)
        self.assertIn("duplicate: /documentation/x", out)

    def test_extra_row_fails(self):
        code, out = run(FX / "extra")
        self.assertEqual(code, 1, out)
        self.assertIn("extra: /documentation/never-assigned", out)

    def test_unfetchable_needs_deferred_id(self):
        code, out = run(FX / "bad-unfetchable")
        self.assertEqual(code, 1, out)
        self.assertIn("malformed: /documentation/dead", out)
        self.assertIn("no-unfetchable:404", out)

    def test_only_filters_slices(self):
        # m01 is incomplete in "missing", but m02 and g01 are complete.
        code, out = run(FX / "missing", "--only", "m02,g01")
        self.assertEqual(code, 0, out)
        code, out = run(FX / "missing", "--only", "m01")
        self.assertEqual(code, 1, out)
        self.assertIn("missing: /documentation/x", out)

    def test_empty_ledger_fails_with_missing(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = run(d)
        self.assertEqual(code, 1, out)
        self.assertIn("missing: /documentation/Metal/a", out)
        self.assertIn("missing: pdf:fst#all", out)

    def test_unfetchable_http_must_match_manifest(self):
        # A reader may not call a page that fetched fine "unfetchable".
        with tempfile.TemporaryDirectory() as d:
            d = copy_complete(d)
            m = d / "m01.tsv"
            m.write_text(m.read_text().replace(
                "/documentation/x\t80\tyes", "/documentation/x\t80\tno-unfetchable:404:deferred-4"))
            code, out = run(d)
        self.assertEqual(code, 1, out)
        self.assertIn("malformed: /documentation/x", out)

    def test_yes_on_a_404_row_fails(self):
        with tempfile.TemporaryDirectory() as d:
            d = copy_complete(d)
            m = d / "m01.tsv"
            m.write_text(m.read_text().replace(
                "no-unfetchable:404:deferred-3", "yes"))
            code, out = run(d)
        self.assertEqual(code, 1, out)
        self.assertIn("malformed: /documentation/dead", out)

    def test_unsliced_path_fails_without_only(self):
        with tempfile.TemporaryDirectory() as d:
            s = pathlib.Path(d) / "slices.tsv"
            lines = (FX / "slices.tsv").read_text().splitlines(keepends=True)
            s.write_text("".join(l for l in lines if "gamekit" not in l))
            code, out = run(FX / "complete", slices=s)
        self.assertEqual(code, 1, out)
        self.assertIn("unsliced: /documentation/gamekit/g", out)


if __name__ == "__main__":
    unittest.main()
