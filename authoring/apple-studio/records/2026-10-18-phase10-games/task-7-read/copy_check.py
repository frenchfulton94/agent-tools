#!/usr/bin/env python3
"""Copy check for the Phase 10 Task 7 notes (standard library only).

Usage: copy_check.py [N]        (run from the worktree root; N defaults to 12)

Adapted from task-4-read/copy_check.py for the g, p, and r slices. For each
notes file, finds every run of N or more consecutive words that also appears
verbatim in a source text its slice covered: the cached pages under
$TMP/corpus/ for the slice's /documentation and /design rows. r01 also read
two sources outside its ledger, and both are added for it: the saved
"Supported capabilities (macOS)" page in $TMP/r01-extra/ (HTML tags
stripped), and the man pages it read in place of the unfetchable
/documentation/os/reading-unix-manual-pages (deferred item 21), rendered with
`man`.

Normalization: lowercase, whitespace collapsed, Markdown punctuation ignored
(* ` # > | [ ] _ and typographic dashes/quotes), and sentence punctuation
stripped from each word's ends. Runs are found per notes line, so a run never
spans two bullets. A run that contains `::`, `(` or a `/documentation/` path is
reported as EXCLUDED (symbol, path, or signature material), not as a HIT.
"""
import csv
import html
import os
import pathlib
import re
import subprocess
import sys

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
AS = pathlib.Path("authoring/apple-studio")
REC = AS / "records/2026-10-18-phase10-games"
TMP = AS / "pipeline/tmp"
SLICES = ("g", "p", "r")
R01_MAN = ("codesign", "spctl", "hdiutil", "pkgbuild", "productbuild", "pkgutil", "stapler")

MD_PUNCT = re.compile(r"[*`#>|\[\]—–‘’“”\\]|(?<!\w)_|_(?!\w)")
EDGE = re.compile(r"\A[.,;:!?\"'-]+|[.,;:!?\"'-]+\Z")
TAG = re.compile(r"<script.*?</script>|<style.*?</style>|<[^>]+>", re.S | re.I)
OVERSTRIKE = re.compile(r".\x08")


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


def source_texts(ledger):
    """Return [(name, text)] for every source the slice read."""
    out = {}
    with open(ledger, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE))[1:]
    for row in rows:
        p = TMP / "corpus" / (key(row[0]) + ".md")
        if p.exists():
            out[p.name] = p.read_text(encoding="utf-8", errors="replace")
    if ledger.stem == "r01":
        for p in sorted((TMP / "r01-extra").glob("*.html")):
            out[p.name] = html.unescape(TAG.sub(" ", p.read_text(encoding="utf-8", errors="replace")))
        env = dict(os.environ, MANPAGER="cat", PAGER="cat", MANWIDTH="200")
        for m in R01_MAN:
            r = subprocess.run(["man", m], capture_output=True, text=True, env=env)
            if r.returncode == 0 and r.stdout.strip():
                out[f"man:{m}"] = OVERSTRIKE.sub("", r.stdout)
    return sorted(out.items())


def main():
    hits = excluded = 0
    log = [f"threshold: {N} words"]
    ledgers = sorted(p for p in (REC / "ledger").glob("*.tsv") if p.stem[0] in SLICES)
    for ledger in ledgers:
        sid = ledger.stem
        notes = REC / "notes" / f"{sid}.md"
        texts = source_texts(ledger)
        grams = {}
        for name, text in texts:
            w = words(text)
            for i in range(len(w) - N + 1):
                grams.setdefault(hash(tuple(w[i:i + N])), (name, i))
        log.append(f"== {sid}: {len(texts)} source texts, notes {notes.name}")
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
