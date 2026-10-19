#!/usr/bin/env python3
"""P22 field checks for the Phase 10 Task 4 ledgers (standard library only).

Usage: field_check.py            (run from the worktree root)

1. Every ledger `words` equals the manifest or sources value for that path.
2. Every `fed` is `nothing: <non-empty reason>`, or `;`-separated targets of the
   form `<file>.md[#section]` or `<skill>/<file>.md[#section]`, where the file is
   a destination named in the reader brief.
"""
import csv
import pathlib
import re
import sys

REC = pathlib.Path("authoring/apple-studio/records/2026-10-18-phase10-games")

DEST = {
    "": {  # apple-metal, bare names
        "command-model.md", "pipelines-and-render-passes.md", "apple-gpu-tbdr.md",
        "resources-and-memory.md", "shading-language.md", "compute-and-gpu-driven.md",
        "display-and-upscaling.md", "gpu-debugging-and-profiling.md", "cpp-and-rust.md",
    },
    "apple-games": {
        "game-loop-and-threading.md", "input.md", "audio-and-haptics.md",
        "game-center-and-online.md", "assets.md", "game-design.md",
    },
    "apple-performance": {"profiling-workflow.md"},
    "app-release": {"direct-distribution.md"},
}
TARGET = re.compile(r"\A(?:(?P<skill>[a-z-]+)/)?(?P<file>[a-z0-9-]+\.md)(?:#(?P<sec>.+))?\Z")


def read_tsv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE))


def main():
    words = {}
    for f in (REC / "task-1-manifest/manifest.tsv", REC / "task-3-slices/sources.tsv"):
        for row in read_tsv(f)[1:]:
            words[row[0].lower()] = row[6]
    problems = []
    rows = 0
    for led in sorted((REC / "ledger").glob("m*.tsv")):
        for n, row in enumerate(read_tsv(led), 1):
            if n == 1:
                if row != ["path", "words", "read_in_full", "fed"]:
                    problems.append(f"{led.name}:1 bad header {row}")
                continue
            where = f"{led.name}:{n}"
            if len(row) != 4:
                problems.append(f"{where} expected 4 fields, got {len(row)}: {row[:1]}")
                continue
            rows += 1
            path, w, _, fed = row
            want = words.get(path.lower())
            if want is None:
                problems.append(f"{where} path not in manifest or sources: {path}")
            elif w != want:
                problems.append(f"{where} words {w} != {want} for {path}")
            if fed.startswith("nothing:"):
                if not fed[len("nothing:"):].strip():
                    problems.append(f"{where} empty 'nothing' reason: {path}")
                continue
            for t in fed.split(";"):
                t = t.strip()
                m = TARGET.match(t)
                if not m:
                    problems.append(f"{where} malformed fed target {t!r}: {path}")
                    continue
                skill = m.group("skill") or ""
                if skill not in DEST or m.group("file") not in DEST[skill]:
                    problems.append(f"{where} unknown destination {t!r}: {path}")
                if m.group("sec") is not None and not m.group("sec").strip():
                    problems.append(f"{where} empty section in {t!r}: {path}")
    print(f"ledger rows checked: {rows}")
    for p in problems:
        print("VIOLATION", p)
    print(f"violations: {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
