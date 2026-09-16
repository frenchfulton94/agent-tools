#!/usr/bin/env python3
"""Scan a directory and emit aggregated clusters.

Clusters, not rows: counts and samples are what reach the agent's context, so
review cost scales with decisions rather than file count. That is also why the
plugin needs no classifier subagent.

Tier one (this module's walk and cluster) uses portable metadata only. Tier two
adds macOS signals and a bounded content peek.
"""

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

import para_paths as pp
from para_index import Index, parse_index

SAMPLE_CAP = 5
MONTH_SECONDS = 30.44 * 86400


def _tokens(rel):
    """Lowercase word-ish tokens from a relative path, for name matching."""
    return set(re.split(r"[^a-z0-9]+", rel.casefold())) - {""}


def walk(root, index):
    """Collect entries beneath root. Packages are single items."""
    entries = []
    stats = {"unreadable": 0, "skipped_never_move": 0}
    never_move = tuple(pp.DEFAULT_NEVER_MOVE) + tuple(index.never_move)

    def visit(directory):
        try:
            children = sorted(directory.iterdir())
        except (PermissionError, OSError):
            stats["unreadable"] += 1
            return
        for child in children:
            if child.is_symlink():
                record(child)
                continue
            if pp.is_package(child):
                record(child)
                continue
            if child.is_dir():
                visit(child)
            else:
                record(child)

    def record(path):
        if pp.matches_any(path, root, never_move):
            stats["skipped_never_move"] += 1
            return
        try:
            info = path.lstat()
        except OSError:
            stats["unreadable"] += 1
            return
        entries.append({
            "rel": str(path.relative_to(root)),
            "last_used": info.st_mtime,
            "size": info.st_size,
            "indexed": False,
        })

    for child in sorted(root.iterdir()):
        # The skeleton is output, not input. A re-run works 0-Inbox only, which
        # the maintaining-para-systems skill drives.
        if child.name in pp.SKELETON:
            continue
        if child.is_symlink() or pp.is_package(child) or not child.is_dir():
            record(child)
        else:
            visit(child)
    return entries, stats


def _make(kind, rule, reason, destination, files):
    return {
        "kind": kind,
        "rule": rule,
        "reason": reason,
        "destination": destination,
        "count": len(files),
        "samples": files[:SAMPLE_CAP],
        "files": files,
    }


def cluster(entries, index, *, archive_after_months=12, now=None):
    """Assign every entry to exactly one cluster, highest precedence first."""
    now = now if now is not None else dt.datetime.now().timestamp()
    cutoff = now - archive_after_months * MONTH_SECONDS
    remaining = {e["rel"]: e for e in entries}
    clusters = []

    # 1. Name matches against the user's confirmed commitments.
    for name in index.all_names():
        destination = index.classify(name)
        wanted = set(re.split(r"[^a-z0-9]+", name.casefold())) - {""}
        if not wanted:
            continue
        hits = sorted(
            rel for rel in remaining if wanted <= _tokens(rel)
        )
        if hits:
            kind = {"1-Projects": "project-match", "2-Areas": "area-match"}.get(
                destination, "resource-match"
            )
            clusters.append(_make(
                kind,
                f'path mentions "{name}"',
                f'matches "{name}" in PARA.md',
                f"{destination}/{name}",
                hits,
            ))
            for rel in hits:
                del remaining[rel]

    # 2. Age, bucketed by year of last use.
    by_year = {}
    for rel, entry in list(remaining.items()):
        if entry["last_used"] < cutoff:
            year = dt.datetime.fromtimestamp(entry["last_used"]).year
            by_year.setdefault(year, []).append(rel)
            del remaining[rel]
    for year, files in sorted(by_year.items()):
        clusters.append(_make(
            "age",
            f"last used before {archive_after_months} months ago",
            f"{len(files)} files last used in {year}",
            f"4-Archives/{year}",
            sorted(files),
        ))

    # 3. Whatever is left. 0-Inbox is a correct answer, not a failure.
    if remaining:
        clusters.append(_make(
            "unresolved",
            "no match in PARA.md and recently used",
            "needs a human decision",
            "0-Inbox",
            sorted(remaining),
        ))
    return clusters


def scan(root, *, archive_after_months=12, metadata_only=False, para=None):
    index = parse_index(para) if para else Index()
    entries, stats = walk(root, index)
    clusters = cluster(entries, index, archive_after_months=archive_after_months)
    return {
        "version": 1,
        "root": str(root),
        "volume": pp.volume_of(root),
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "metadata_only": metadata_only,
        "peeked": [],
        "unindexed": sum(1 for e in entries if not e["indexed"]),
        "unreadable": stats["unreadable"],
        "skipped_never_move": stats["skipped_never_move"],
        "clusters": clusters,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan a directory into PARA clusters.")
    parser.add_argument("root")
    parser.add_argument("--archive-after", type=int, default=12, metavar="MONTHS")
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()

    try:
        root = pp.validate_root(args.root)
    except pp.UnsafeRoot as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)

    index_file = root / "PARA.md"
    para = index_file.read_text(encoding="utf-8") if index_file.exists() else None
    json.dump(
        scan(root, archive_after_months=args.archive_after,
             metadata_only=args.metadata_only, para=para),
        sys.stdout, indent=2,
    )
    print()


if __name__ == "__main__":
    main()
