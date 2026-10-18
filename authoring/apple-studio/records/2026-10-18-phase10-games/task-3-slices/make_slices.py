#!/usr/bin/env python3
"""Build sources.tsv and slices.tsv for the Phase 10 reading corpus.

Standard library only. Run from anywhere:

    python3 make_slices.py [--check]

Inputs (none of them is committed):
  - ../task-1-manifest/manifest.tsv, and the page cache it names under
    pipeline/tmp/corpus/ (the cache key comes from crawl_corpus.key).
  - pipeline/tmp/pdf/msl-4.1.txt and fst.txt, the `pdftotext -layout` extracts
    of the MSL 4.1 spec and the Feature Set Tables. Pages are separated by form
    feeds, so a page range is exact.
  - The metal-by-tutorials book skill, under ~/Projects/book-skills.

Outputs, beside this script:
  - sources.tsv: the manifest's columns, for the sources the crawler did not
    fetch (MSL chapters, the Feature Set Tables, the book).
  - slices.tsv: slice_id, dest, path. At most MAX_WORDS words per slice, rows
    packed in manifest order within one dest.

--check re-derives both files and fails if they differ from what is on disk.
"""
import argparse
import importlib.util
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
AS = HERE.parents[2]  # authoring/apple-studio
PIPE = AS / "pipeline"
MANIFEST = HERE.parent / "task-1-manifest" / "manifest.tsv"
CORPUS = PIPE / "tmp" / "corpus"
PDF = PIPE / "tmp" / "pdf"
BOOK = pathlib.Path.home() / "Projects" / "book-skills" / ".agents" / "skills" / "metal-by-tutorials"

MAX_WORDS = 60_000
MSL_PAGES = 383
MSL_SHA256 = "41538b30d2f1140a5b2a0c84ce0a9f7b67bf0c707e224cfea0bfe5a44aa26cf5"
HEADER = ("path", "seed", "bound", "depth", "documentType", "role", "words", "http", "dest")
SLICE_PREFIX = {"apple-metal": "m", "apple-games": "g", "apple-performance": "p", "app-release": "r"}

# Top-level chapters of the MSL 4.1 table of contents. Printed page numbers equal
# PDF page indices, so (first, last) are 1-based PDF pages. Pages 1-10 are the
# cover, the contents, and the table lists; they get their own row, so the rows
# tile pages 1..383 with no gap.
MSL_CHAPTERS = [
    ("front", "Front matter, contents, table lists", 1, 10),
    ("ch1", "Introduction", 11, 24),
    ("ch2", "Data Types", 25, 111),
    ("ch3", "Operators", 112, 117),
    ("ch4", "Address Spaces", 118, 123),
    ("ch5", "Function and Variable Declarations", 124, 199),
    ("ch6", "Metal Standard Library", 200, 348),
    ("ch7", "Metal Performance Primitives", 349, 367),
    ("ch8", "Numerical Compliance", 368, 381),
    ("ch9", "Appendix", 382, 383),
]
# What the first non-blank line of each chapter's first page must start with.
MSL_HEADINGS = {"ch1": "1 Introduction", "ch2": "2 Data Types", "ch3": "3 Operators", "ch4": "4 Address Spaces",
                "ch5": "5 Function and Variable Declarations", "ch6": "6 Metal Standard Library",
                "ch7": "7 Metal Performance Primitives", "ch8": "8 Numerical Compliance",
                "ch9": "9 Appendix"}


def load_crawler():
    spec = importlib.util.spec_from_file_location("crawl_corpus", PIPE / "crawl_corpus.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_manifest():
    rows = []
    lines = MANIFEST.read_text(encoding="utf-8").splitlines()
    assert tuple(lines[0].split("\t")) == HEADER, "unexpected manifest header"
    for line in lines[1:]:
        if line:
            rows.append(dict(zip(HEADER, line.split("\t"))))
    seen = {}
    for r in rows:
        k = r["path"].lower()
        assert k not in seen, f"manifest repeats {r['path']!r} case-insensitively"
        seen[k] = r
    return rows


def measure_manifest(rows, crawler):
    """Check each 200 row against its cached page, and set r["load"].

    `words` in the manifest excludes the page's leading metadata comment, but a
    reader loads the whole file, so `load` (the whole file's whitespace tokens)
    is what the slice cap bounds. Returns the rows whose `words` the cache
    contradicts.
    """
    bad = []
    for r in rows:
        r["load"] = 0
        if r["http"] != "200":
            assert r["words"] == "0", f"{r['path']}: non-200 row with words"
            continue
        f = CORPUS / f"{crawler.key(r['path'])}.md"
        if not f.is_file():
            bad.append((r["path"], r["words"], None))
            continue
        text = f.read_text(encoding="utf-8")
        r["load"] = len(text.split())
        if crawler.page_words(text) != int(r["words"]):
            bad.append((r["path"], r["words"], crawler.page_words(text)))
    return bad


def split_pages(first, last, page_words, cap=MAX_WORDS):
    """Split pages first..last into the fewest ranges of at most `cap` words.

    Returns [(a, b), ...] with words balanced across the ranges. A single page
    over the cap is an error: no page-range split can fix it.
    """
    pw = [page_words[p - 1] for p in range(first, last + 1)]
    total = sum(pw)
    if max(pw) > cap:
        raise ValueError(f"one page of {first}-{last} has more than {cap} words")
    parts = max(1, math.ceil(total / cap))
    while True:
        target = total / parts
        ranges, start, acc = [], first, 0
        for i, w in enumerate(pw):
            page = first + i
            if acc and acc + w > cap or (acc and len(ranges) < parts - 1
                                         and abs(acc - target) < abs(acc + w - target)):
                ranges.append((start, page - 1))
                start, acc = page, 0
            acc += w
        ranges.append((start, last))
        if all(sum(page_words[p - 1] for p in range(a, b + 1)) <= cap for a, b in ranges):
            return ranges
        parts += 1


def source_row(path, seed, doc_type, role, words):
    return {"path": path, "seed": seed, "bound": "page", "depth": "0", "documentType": doc_type,
            "role": role, "words": str(words), "http": "200", "dest": "apple-metal", "load": words}


def msl_rows():
    text = (PDF / "msl-4.1.txt").read_text(encoding="utf-8")
    pages = text.split("\f")
    if not pages[-1].strip():
        pages.pop()
    assert len(pages) == MSL_PAGES, f"MSL extract has {len(pages)} pages, expected {MSL_PAGES}"
    pw = [len(p.split()) for p in pages]
    expect = 1
    rows = []
    for ch, title, first, last in MSL_CHAPTERS:
        assert first == expect, f"{ch} starts at {first}, expected {expect}: pages must tile"
        expect = last + 1
        if ch in MSL_HEADINGS:
            head = next(l for l in pages[first - 1].splitlines() if l.strip())
            assert " ".join(head.split()).startswith(MSL_HEADINGS[ch]), \
                f"{ch}: page {first} opens with {head!r}"
        total = sum(pw[first - 1:last])
        if total <= MAX_WORDS:
            parts = [(first, last, ch)]
        else:  # ruling P6
            parts = [(a, b, f"{ch}-p{a}-{b}") for a, b in split_pages(first, last, pw)]
        for a, b, suffix in parts:
            rows.append(source_row(f"pdf:msl-4.1#{suffix}", "pdf:msl-4.1", "pdf-chapter",
                                   f"MSL 4.1 {title} (pages {a}-{b})", sum(pw[a - 1:b])))
    assert expect == MSL_PAGES + 1, "chapter table does not reach the last page"
    return rows


def fst_row():
    text = (PDF / "fst.txt").read_text(encoding="utf-8")
    return source_row("pdf:fst#all", "pdf:fst", "pdf", "Metal Feature Set Tables (18 pages)",
                      len(text.split()))


def book_rows():
    files = sorted((BOOK / "chapters").glob("ch*.md"))
    assert len(files) == 31, f"expected 31 chapter files, found {len(files)}"
    rel = [f"chapters/{f.name}" for f in files] + ["glossary.md", "patterns.md", "cheatsheet.md", "SKILL.md"]
    rows = []
    for r in rel:
        n = len((BOOK / r).read_text(encoding="utf-8").split())
        rows.append(source_row(f"book:metal-by-tutorials/{r}", "book:metal-by-tutorials", "book",
                               "Metal by Tutorials" if r.startswith("chapters/") else "book skill file", n))
    return rows


def pack(rows, cap=MAX_WORDS):
    """Pack rows in order into slices of at most `cap` words, balanced across the slices.

    Next-fit in the given order, so neighbouring pages stay together. A slice
    closes when the next row would pass the cap, or when stopping is closer to
    the even-share target than adding the row, as long as slices remain to take
    the rest.
    """
    total = sum(r["load"] for r in rows)
    parts = max(1, math.ceil(total / cap))
    while True:
        target = total / parts
        out, cur, acc = [], [], 0
        for r in rows:
            w = r["load"]
            if w > cap:
                raise ValueError(f"{r['path']} has {w} words, over the {cap} cap")
            if cur and (acc + w > cap or (len(out) < parts - 1 and abs(acc - target) < abs(acc + w - target))):
                out.append(cur)
                cur, acc = [], 0
            cur.append(r)
            acc += w
        out.append(cur)
        if len(out) <= parts:
            return out
        parts += 1  # the cap forced an extra slice: re-balance for one more


def build():
    manifest = read_manifest()
    bad = measure_manifest(manifest, load_crawler())
    if bad:
        raise SystemExit(f"manifest words disagree with the cache for {len(bad)} rows, e.g. {bad[:3]}")
    sources = msl_rows() + [fst_row()] + book_rows()
    allrows = {}
    for r in manifest + sources:
        k = r["path"].lower()
        assert k not in allrows, f"duplicate path {r['path']!r}"
        allrows[k] = r
    slices = []
    for dest, prefix in SLICE_PREFIX.items():
        rows = [r for r in manifest if r["dest"] == dest] + [r for r in sources if r["dest"] == dest]
        for i, group in enumerate(pack(rows), 1):
            slices.append((f"{prefix}{i:02d}", dest, group))
    return sources, slices


def render_sources(sources):
    return "".join("\t".join(r[c] for c in HEADER) + "\n" for r in [dict(zip(HEADER, HEADER))] + sources)


def render_slices(slices):
    lines = ["slice_id\tdest\tpath\n"]
    for sid, dest, group in slices:
        lines += [f"{sid}\t{dest}\t{r['path']}\n" for r in group]
    return "".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if the files on disk differ")
    a = ap.parse_args(argv)
    sources, slices = build()
    out = {"sources.tsv": render_sources(sources), "slices.tsv": render_slices(slices)}
    if a.check:
        stale = [n for n, t in out.items() if not (HERE / n).is_file() or (HERE / n).read_text() != t]
        if stale:
            print("stale: " + ", ".join(stale), file=sys.stderr)
            return 1
        return 0
    for name, text in out.items():
        (HERE / name).write_text(text, encoding="utf-8")
    by_dest = {}
    for sid, dest, group in slices:
        by_dest.setdefault(dest, []).append(
            (sid, len(group), sum(int(r["words"]) for r in group), sum(r["load"] for r in group)))
    for dest, items in by_dest.items():
        big = max(items, key=lambda t: t[3])
        print(f"{dest}: {len(items)} slices, {sum(t[1] for t in items)} rows, "
              f"{sum(t[2] for t in items)} words ({sum(t[3] for t in items)} loaded); "
              f"largest {big[0]}: {big[2]} words ({big[3]} loaded, {big[1]} rows)")
    for sid, dest, group in slices:
        print(f"  {sid}\t{len(group)} rows\t{sum(int(r['words']) for r in group)} words\t"
              f"{sum(r['load'] for r in group)} loaded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
