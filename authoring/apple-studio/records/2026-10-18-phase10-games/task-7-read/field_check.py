#!/usr/bin/env python3
"""P22 field checks for the Phase 10 Task 7 ledgers and notes (standard library only).

Usage: field_check.py            (run from the worktree root)

Adapted from task-4-read/field_check.py for the g, p, and r slices. Under
ruling P37, a bare file name means the slice's own skill: apple-games in a g
slice, apple-performance in p01, and app-release in r01. Every other skill is
named as `<skill>/<file>`.

1. Every ledger `words` equals the manifest or sources value for that path.
2. Every `fed` is `nothing: <non-empty reason>`, or `;`-separated targets of the
   form `<file>.md[#section]` or `<skill>/<file>.md[#section]`, where the file is
   a destination named in the reader brief, or an existing app-release
   reference under plugins/apple-studio/skills/app-release/references/.
3. Every `## ` heading in the notes file is one of those targets, resolved the
   same way, or `(none)`. `### ` subheadings are not checked.
"""
import csv
import pathlib
import re
import sys

REC = pathlib.Path("authoring/apple-studio/records/2026-10-18-phase10-games")
RELEASE_REFS = pathlib.Path("plugins/apple-studio/skills/app-release/references")

DEST = {
    "apple-metal": {
        "command-model.md", "pipelines-and-render-passes.md", "apple-gpu-tbdr.md",
        "resources-and-memory.md", "shading-language.md", "compute-and-gpu-driven.md",
        "display-and-upscaling.md", "gpu-debugging-and-profiling.md", "cpp-and-rust.md",
    },
    "apple-games": {
        "game-loop-and-threading.md", "input.md", "audio-and-haptics.md",
        "game-center-and-online.md", "assets.md", "game-design.md",
    },
    "apple-performance": {"profiling-workflow.md"},
    # The new file, plus every app-release reference that already exists.
    "app-release": {"direct-distribution.md"} | {p.name for p in RELEASE_REFS.glob("*.md")},
}
OWN = {"g": "apple-games", "p": "apple-performance", "r": "app-release"}
TARGET = re.compile(r"\A(?:(?P<skill>[a-z-]+)/)?(?P<file>[a-z0-9-]+\.md)(?:#(?P<sec>.+))?\Z")


def read_tsv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE))


def resolve(target, own):
    """Return (skill, file, section) or None if malformed."""
    m = TARGET.match(target)
    if not m:
        return None
    return (m.group("skill") or own, m.group("file"), m.group("sec"))


def main():
    words = {}
    for f in (REC / "task-1-manifest/manifest.tsv", REC / "task-3-slices/sources.tsv"):
        for row in read_tsv(f)[1:]:
            words[row[0].lower()] = row[6]
    problems = []
    rows = headings = 0
    ledgers = sorted(p for p in (REC / "ledger").glob("*.tsv") if p.stem[0] in OWN)
    for led in ledgers:
        own = OWN[led.stem[0]]
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
                r = resolve(t, own)
                if r is None:
                    problems.append(f"{where} malformed fed target {t!r}: {path}")
                    continue
                skill, file, sec = r
                if skill not in DEST or file not in DEST[skill]:
                    problems.append(f"{where} unknown destination {t!r}: {path}")
                if sec is not None and not sec.strip():
                    problems.append(f"{where} empty section in {t!r}: {path}")
        notes = REC / "notes" / f"{led.stem}.md"
        if not notes.exists():
            problems.append(f"{notes.name} missing")
            continue
        for n, line in enumerate(notes.read_text(encoding="utf-8").splitlines(), 1):
            if not line.startswith("## "):
                continue
            headings += 1
            h = line[3:].strip()
            if h == "(none)":
                continue
            r = resolve(h, own)
            if r is None or r[2] is not None:
                problems.append(f"{notes.name}:{n} malformed heading {h!r}")
                continue
            skill, file, _ = r
            if skill not in DEST or file not in DEST[skill]:
                problems.append(f"{notes.name}:{n} unknown heading {h!r} (resolves to {skill}/{file})")
    print(f"ledgers: {', '.join(p.stem for p in ledgers)}")
    print(f"ledger rows checked: {rows}")
    print(f"notes headings checked: {headings}")
    for p in problems:
        print("VIOLATION", p)
    print(f"violations: {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
