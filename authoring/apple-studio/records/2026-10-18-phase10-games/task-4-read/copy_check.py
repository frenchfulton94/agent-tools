#!/usr/bin/env python3
"""Copy check for the Phase 10 Task 4 notes (standard library only).

Usage: copy_check.py            (run from the worktree root)

For each notes file, finds every run of N or more consecutive words (default 12)
that also appears verbatim in a source text its slice covered: the cached pages
under $TMP/corpus/ for the slice's /documentation and /design rows, the MSL and
Feature Set Tables extracts under $TMP/pdf/, and the book files.

Normalization: lowercase, whitespace collapsed, Markdown punctuation ignored
(* ` # > | [ ] _ and typographic dashes/quotes), and sentence punctuation
stripped from each word's ends. Runs are found per notes line, so a run never
spans two bullets. A run that contains `::`, `(` or a `/documentation/` path is
reported as EXCLUDED (symbol, path, or signature material), not as a HIT.
"""
import csv
import pathlib
import re
import sys

N = 12
AS = pathlib.Path("authoring/apple-studio")
REC = AS / "records/2026-10-18-phase10-games"
TMP = AS / "pipeline/tmp"
BOOK = pathlib.Path.home() / "Projects/book-skills/.agents/skills/metal-by-tutorials"

MD_PUNCT = re.compile(r"[*`#>|\[\]—–‘’“”\\]|(?<!\w)_|_(?!\w)")
EDGE = re.compile(r"\A[.,;:!?\"'-]+|[.,;:!?\"'-]+\Z")


def key(path):
    k = path.lstrip("/").lower().replace("/", "__")
    return re.sub(r"[^a-z0-9_.()'-]", "_", k)


def words(text):
    out = []
    for w in MD_PUNCT.sub(" ", text.lower()).split():
        w = EDGE.sub("", w)
        if w:
            out.append(w)
    return out


def source_files(ledger):
    files = []
    with open(ledger, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE))[1:]
    for path, _w, _r, _f in rows:
        if path.startswith("pdf:msl"):
            files.append(TMP / "pdf/msl-4.1.txt")
        elif path.startswith("pdf:fst"):
            files.append(TMP / "pdf/fst.txt")
        elif path.startswith("book:metal-by-tutorials/"):
            files.append(BOOK / path.split("/", 1)[1])
        else:
            p = TMP / "corpus" / (key(path) + ".md")
            if p.exists():
                files.append(p)
    return sorted(set(files))


def main():
    hits = excluded = 0
    log = []
    for ledger in sorted((REC / "ledger").glob("m*.tsv")):
        sid = ledger.stem
        notes = REC / "notes" / f"{sid}.md"
        files = source_files(ledger)
        grams = {}
        for f in files:
            w = words(f.read_text(encoding="utf-8", errors="replace"))
            for i in range(len(w) - N + 1):
                grams.setdefault(hash(tuple(w[i:i + N])), (f.name, i))
        log.append(f"== {sid}: {len(files)} source files, notes {notes.name}")
        for ln, line in enumerate(notes.read_text(encoding="utf-8").splitlines(), 1):
            w = words(line)
            flags = [hash(tuple(w[i:i + N])) in grams for i in range(len(w) - N + 1)]
            i = 0
            while i < len(flags):
                if not flags[i]:
                    i += 1
                    continue
                j = i
                while j + 1 < len(flags) and flags[j + 1]:
                    j += 1
                run = w[i:j + N]
                text = " ".join(run)
                src = grams[hash(tuple(w[i:i + N]))][0]
                if "::" in text or "(" in text or "/documentation/" in text:
                    excluded += 1
                    log.append(f"EXCLUDED {sid}.md:{ln} ({len(run)} words, src {src}): {text}")
                else:
                    hits += 1
                    log.append(f"HIT {sid}.md:{ln} ({len(run)} words, src {src}): {text}")
                i = j + 1
    log.append(f"hits: {hits}")
    log.append(f"excluded (symbol/path/signature): {excluded}")
    print("\n".join(log))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
