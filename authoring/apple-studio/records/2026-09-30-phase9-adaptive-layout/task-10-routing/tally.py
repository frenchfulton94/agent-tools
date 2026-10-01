#!/usr/bin/env python3
"""Tally three run-N/results.tsv files from the Task 10 Duo-routing sweep.

Usage: python3 tally.py [run-dir ...]
Defaults to run-1 run-2 run-3 in the script's own directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

HEADER = ["id", "skill", "expect", "fired", "verdict", "note", "wrote", "log"]


def read_results(path: Path) -> dict[str, dict]:
    rows = {}
    lines = path.read_text().splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        row = dict(zip(HEADER, parts + [""] * (len(HEADER) - len(parts))))
        rows[row["id"]] = row
    return rows


def main() -> int:
    here = Path(__file__).resolve().parent
    run_dirs = [Path(a) for a in sys.argv[1:]] or [here / f"run-{n}" for n in (1, 2, 3)]
    runs = [read_results(d / "results.tsv") for d in run_dirs]

    ids = list(runs[0].keys())
    for r in runs[1:]:
        assert list(r.keys()) == ids, "row ids differ across runs"

    print(f"{'id':<12} {'expect':<7} {'pass/3':<7} {'run1->fired':<16} {'run2->fired':<16} {'run3->fired':<16} notes")
    for row_id in ids:
        rows = [r[row_id] for r in runs]
        expect = rows[0]["expect"]
        passes = sum(1 for r in rows if r["verdict"] == "PASS")
        fired_cols = [f"{r['fired']}({r['verdict']})" for r in rows]
        notes = [r["note"] for r in rows if r["note"]]
        note_str = ",".join(notes) if notes else ""
        print(
            f"{row_id:<12} {expect:<7} {passes}/3{'':<4} "
            f"{fired_cols[0]:<16} {fired_cols[1]:<16} {fired_cols[2]:<16} {note_str}"
        )

    print()
    print("Rows not holding (PASS count < 2/3):")
    any_fail = False
    for row_id in ids:
        rows = [r[row_id] for r in runs]
        passes = sum(1 for r in rows if r["verdict"] == "PASS")
        if passes < 2:
            any_fail = True
            print(f"  {row_id}: {passes}/3 PASS  fired={[r['fired'] for r in rows]}  notes={[r['note'] for r in rows]}")
    if not any_fail:
        print("  (none)")

    print()
    print("Duo FIRE rows (ad-fire-7, ad-fire-8, ad-fire-9, ad-fire-10):")
    for row_id in ("ad-fire-7", "ad-fire-8", "ad-fire-9", "ad-fire-10"):
        rows = [r[row_id] for r in runs]
        passes = sum(1 for r in rows if r["verdict"] == "PASS")
        holds = "HOLDS" if passes >= 2 else "does not hold"
        print(f"  {row_id}: {passes}/3 PASS -> {holds}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
