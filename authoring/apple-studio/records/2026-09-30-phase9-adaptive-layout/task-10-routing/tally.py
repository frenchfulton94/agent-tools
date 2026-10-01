#!/usr/bin/env python3
"""Tally the Task 10 Duo-routing sweeps: the original 28-row sweep
(run-1..3), the revision round (run-rev-1..3, 18 rows), and the
single-row baseline re-runs (baseline-<id>-1..3).

Usage: python3 tally.py
Reads everything from the script's own directory; no arguments needed.
"""
from __future__ import annotations

from pathlib import Path

HEADER = ["id", "skill", "expect", "fired", "verdict", "note", "wrote", "log"]

HERE = Path(__file__).resolve().parent

DUO_ROWS = ("ad-fire-7", "ad-fire-8", "ad-fire-9", "ad-fire-10")


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


def tally_group(title: str, run_dirs: list[Path], duo_note: bool = True) -> None:
    runs = [read_results(d / "results.tsv") for d in run_dirs]
    n = len(runs)
    ids = list(runs[0].keys())
    for r in runs[1:]:
        assert list(r.keys()) == ids, f"row ids differ across runs in {title}"

    print(f"## {title} ({n} run{'s' if n != 1 else ''}: "
          f"{', '.join(d.name for d in run_dirs)})")
    print()
    cols = "  ".join(f"{'run%d->fired' % (i+1):<20}" for i in range(n))
    print(f"{'id':<14} {'expect':<7} {'pass/' + str(n):<8} {cols} notes")
    for row_id in ids:
        rows = [r[row_id] for r in runs]
        expect = rows[0]["expect"]
        passes = sum(1 for r in rows if r["verdict"] == "PASS")
        fired_cols = [f"{r['fired']}({r['verdict']})" for r in rows]
        notes = [r["note"] for r in rows if r["note"]]
        note_str = ",".join(notes) if notes else ""
        cols_str = "  ".join(f"{c:<20}" for c in fired_cols)
        print(f"{row_id:<14} {expect:<7} {passes}/{n}{'':<5} {cols_str} {note_str}")

    print()
    print(f"Rows not holding (PASS count < {(n // 2) + 1}/{n}):")
    any_fail = False
    for row_id in ids:
        rows = [r[row_id] for r in runs]
        passes = sum(1 for r in rows if r["verdict"] == "PASS")
        holds = passes >= 2 if n == 3 else passes > n / 2
        if not holds:
            any_fail = True
            print(f"  {row_id}: {passes}/{n} PASS  fired={[r['fired'] for r in rows]}  "
                  f"notes={[r['note'] for r in rows]}")
    if not any_fail:
        print("  (none)")

    if duo_note:
        print()
        print(f"Duo FIRE rows ({', '.join(DUO_ROWS)}):")
        for row_id in DUO_ROWS:
            if row_id not in ids:
                continue
            rows = [r[row_id] for r in runs]
            passes = sum(1 for r in rows if r["verdict"] == "PASS")
            holds = "HOLDS" if passes >= 2 else "does not hold"
            print(f"  {row_id}: {passes}/{n} PASS -> {holds}")
    print()


def tally_baseline(row_id: str, run_dirs: list[Path]) -> None:
    runs = [read_results(d / "results.tsv") for d in run_dirs]
    print(f"## Baseline re-run: {row_id} ({len(run_dirs)} runs, "
          f"{', '.join(d.name for d in run_dirs)})")
    print()
    passes = 0
    for i, r in enumerate(runs, start=1):
        row = r[row_id]
        print(f"  baseline-{i}: {row['fired']}({row['verdict']})")
        if row["verdict"] == "PASS":
            passes += 1
    holds = "HOLDS" if passes >= 2 else "does not hold"
    print(f"  {passes}/{len(run_dirs)} PASS -> {holds} at baseline")
    print()


def main() -> int:
    tally_group(
        "Original sweep (28 rows, Step 1/2 descriptions)",
        [HERE / f"run-{n}" for n in (1, 2, 3)],
    )
    tally_baseline("ad-fire-5", [HERE / f"baseline-ad-fire-5-{n}" for n in (1, 2, 3)])
    tally_group(
        "Revision round (18 rows: ad-fire-1..10, ad-nofire-1..6, "
        "ar-fire-8, ar-nofire-3 — revised apple-design description)",
        [HERE / f"run-rev-{n}" for n in (1, 2, 3)],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
