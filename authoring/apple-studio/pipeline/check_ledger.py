#!/usr/bin/env python3
"""Check that a reading ledger covers every page of its slices, exactly once.

Standard library only. Usage:

    check_ledger.py MANIFEST SOURCES SLICES LEDGER_DIR [--only m01,m02,...]

MANIFEST and SOURCES are TSV files with the crawler's columns
(path seed bound depth documentType role words http dest). SLICES is a TSV
file with the columns slice_id, dest, path. LEDGER_DIR holds one file per slice,
`<slice_id>.tsv`, with the columns path, words, read_in_full, fed:

  read_in_full  `yes`, or `no-unfetchable:<http>:deferred-<n>` for a page the
                manifest records as non-200 (the http code must match).
  fed           `;`-separated `<reference-file>#<section>` targets, or
                `nothing: <reason>`. Never empty.

The selection is every path in the selected slices (all slices, or those named
by --only). Paths compare case-insensitively; the order of the files does not
matter. Output lines, one problem each:

  missing:   a selected path with no ledger row
  duplicate: a path with more than one ledger row
  extra:     a ledger row whose path is not in its slice, or a ledger file
             that matches no slice
  malformed: a bad row, or a slice path unknown to the manifest and sources
  unsliced:  a manifest or sources path that no slice lists (whole-corpus
             checks only, that is, without --only)

Exit 0 when there are no problems, 1 when there are any, 2 on a usage error.
"""
import argparse
import pathlib
import re
import sys

UNFETCHABLE = re.compile(r"\Ano-unfetchable:(\d{3}):deferred-\d+\Z")
HEADS = ("path\t", "slice_id\t")


def read_rows(path):
    """Yield (line_number, fields) for each data row, skipping header and blanks."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if n == 1 and line.startswith(HEADS):
            continue
        yield n, line.split("\t")


def load_catalog(*files):
    """Map lowercased path -> (path, http) over the manifest and sources files."""
    cat = {}
    for f in files:
        for _, c in read_rows(f):
            http = c[7] if len(c) > 7 else "200"
            cat.setdefault(c[0].lower(), (c[0], http))
    return cat


def load_slices(path):
    """Return ordered {slice_id: [path, ...]} and the problems found loading it."""
    slices, problems = {}, []
    for n, c in read_rows(path):
        if len(c) != 3 or not all(c):
            problems.append(f"malformed: {path}:{n}: expected slice_id, dest, path")
            continue
        slices.setdefault(c[0], []).append(c[2])
    return slices, problems


def validate_row(c, http):
    """Return a reason the row is malformed, or None. `http` is the manifest's code."""
    if len(c) != 4:
        return f"expected 4 columns (path, words, read_in_full, fed), got {len(c)}"
    _, words, rif, fed = c
    if not words.isdigit():
        return f"words is not a whole number: {words!r}"
    m = UNFETCHABLE.match(rif)
    if rif == "yes":
        if http is not None and http != "200":
            return f"read_in_full is yes, but the manifest records http {http}"
    elif m:
        if http is not None and m.group(1) != http:
            return f"{rif} does not match the manifest's http {http}"
    else:
        return f"read_in_full {rif!r} is neither yes nor no-unfetchable:<http>:deferred-<n>"
    if not fed.strip():
        return "fed is empty"
    return None


def check(manifest, sources, slices_file, ledger_dir, only=None):
    problems = []
    cat = load_catalog(manifest, sources)
    slices, bad = load_slices(slices_file)
    problems += bad

    if only is not None:
        unknown = [s for s in only if s not in slices]
        if unknown:
            raise ValueError(f"--only names no such slice: {', '.join(sorted(unknown))}")
        selected = {s: slices[s] for s in slices if s in only}
    else:
        selected = slices

    # Every slice path must be a known page, and must sit in one slice only.
    owner = {}
    for sid, paths in slices.items():
        for p in paths:
            k = p.lower()
            if k not in cat:
                problems.append(f"malformed: {p}: in slice {sid} but not in the manifest or sources")
            if k in owner and owner[k] != sid:
                problems.append(f"malformed: {p}: in slices {owner[k]} and {sid}")
            elif k in owner:
                problems.append(f"malformed: {p}: listed twice in slice {sid}")
            owner.setdefault(k, sid)
    if only is None:
        for k, (p, _) in cat.items():
            if k not in owner:
                problems.append(f"unsliced: {p}")

    ledger_dir = pathlib.Path(ledger_dir)
    counts, first = {}, {}
    for sid, paths in selected.items():
        own = {p.lower() for p in paths}
        f = ledger_dir / f"{sid}.tsv"
        if not f.is_file():
            continue
        for n, c in read_rows(f):
            p = c[0] if c else ""
            k = p.lower()
            counts[k] = counts.get(k, 0) + 1
            first.setdefault(k, p)
            if k not in own:
                problems.append(f"extra: {p}: row in {f.name}, not in slice {sid}")
                continue
            why = validate_row(c, cat[k][1] if k in cat else None)
            if why:
                problems.append(f"malformed: {p}: {f.name}:{n}: {why}")
    if only is None and ledger_dir.is_dir():
        for f in sorted(ledger_dir.glob("*.tsv")):
            if f.stem not in slices:
                problems.append(f"extra: {f.name}: no slice has this id")

    for sid, paths in selected.items():
        for p in paths:
            if counts.get(p.lower(), 0) == 0:
                problems.append(f"missing: {p}")
    for k, n in counts.items():
        if n > 1:
            problems.append(f"duplicate: {first[k]}: {n} ledger rows")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("manifest")
    ap.add_argument("sources")
    ap.add_argument("slices")
    ap.add_argument("ledger_dir")
    ap.add_argument("--only", help="comma-separated slice ids to check")
    a = ap.parse_args(argv)
    only = None
    if a.only is not None:
        only = {s.strip() for s in a.only.split(",") if s.strip()}
        if not only:
            ap.error("--only needs at least one slice id")
    try:
        problems = check(a.manifest, a.sources, a.slices, a.ledger_dir, only)
    except ValueError as e:
        ap.error(str(e))
    for line in problems:
        print(line)
    if problems:
        print(f"{len(problems)} problem(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
