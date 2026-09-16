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
import os
import pathlib
import plistlib
import re
import stat
import subprocess
import sys

import para_paths as pp
from para_index import Index, parse_index

SAMPLE_CAP = 5
# The plugin's own output, at the top level of a root it has organized: the
# user's index and previous runs' undo manifests. Both are input to a later
# run, never subjects of one.
PLUGIN_ARTIFACTS = (".para", "PARA.md")
MONTH_SECONDS = 30.44 * 86400


def _tokens(rel):
    """Lowercase word-ish tokens from a relative path, for name matching."""
    return set(re.split(r"[^a-z0-9]+", rel.casefold())) - {""}


MDLS_KEYS = (
    "kMDItemLastUsedDate", "kMDItemUserTags",
    "kMDItemWhereFroms", "kMDItemContentTypeTree",
)


def spotlight(path):
    """Best-effort macOS metadata. Every field may be absent.

    Spotlight indexing is off on many external and network volumes, so this
    reports `indexed` and the caller falls back to portable metadata.
    """
    blank = {"last_used": None, "tags": [], "where_from": [], "indexed": False}
    try:
        result = subprocess.run(
            ["mdls", "-plist", "-", str(path)],
            capture_output=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return blank
    if result.returncode != 0 or not result.stdout:
        return blank
    try:
        data = plistlib.loads(result.stdout)
    except Exception:
        return blank
    if not isinstance(data, dict):
        return blank

    used = data.get("kMDItemLastUsedDate")
    return {
        "last_used": used.timestamp() if hasattr(used, "timestamp") else None,
        "tags": [str(t) for t in (data.get("kMDItemUserTags") or [])],
        "where_from": [str(w) for w in (data.get("kMDItemWhereFroms") or [])],
        "indexed": any(data.get(key) is not None for key in MDLS_KEYS),
    }


def peek(path, limit_bytes):
    """Decode a bounded prefix. Returns '' for binary or unreadable files.

    O_NOFOLLOW closes the window between peek_candidates vetting the path and
    this open: a file swapped for a symlink in between is refused rather than
    followed. closefd=False plus the finally keeps ownership of the descriptor
    here, so a directory -- a package is one -- cannot leak it.
    """
    try:
        handle = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        return ""
    try:
        if stat.S_ISDIR(os.fstat(handle).st_mode):
            return ""
        with os.fdopen(handle, "rb", closefd=False) as stream:
            chunk = stream.read(limit_bytes)
    except OSError:
        return ""
    finally:
        os.close(handle)
    if b"\x00" in chunk:
        return ""
    return chunk.decode("utf-8", errors="replace")


def peek_candidates(entries, root, index, *, peek_files=200):
    """Relative paths eligible for a content read, denylist first, then budget.

    The denylist is checked before the budget, so a never-read path cannot be
    opened by raising the budget. Three guards, because path identity — not the
    budget — is where this actually fails:
      - a symlink is never read, since open() would follow it to a target the
        denylist never saw;
      - the resolved path is checked as well as the literal one;
      - a candidate resolving outside the root is refused.
    """
    never_read = tuple(pp.DEFAULT_NEVER_READ) + tuple(index.never_read)
    root_resolved = root.resolve()
    eligible = []
    for entry in entries:
        candidate = root / entry["rel"]
        if candidate.is_symlink():
            continue
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved != root_resolved and root_resolved not in resolved.parents:
            continue
        if pp.matches_any(candidate, root, never_read):
            continue
        if pp.matches_any(resolved, root_resolved, never_read):
            continue
        eligible.append(entry["rel"])
        if len(eligible) >= peek_files:
            break
    return eligible


def walk(root, index, *, metadata_only=False):
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
        signals = {"last_used": None, "tags": [], "where_from": [], "indexed": False}
        if not metadata_only:
            signals = spotlight(path)
        entries.append({
            "rel": str(path.relative_to(root)),
            # Last-used beats mtime: mtime churns on sync, copy, and restore.
            "last_used": signals["last_used"] or info.st_mtime,
            "size": info.st_size,
            "indexed": signals["indexed"],
            "tags": signals["tags"],
            "where_from": signals["where_from"],
        })

    for child in sorted(root.iterdir()):
        # The skeleton is output, not input. A re-run works 0-Inbox only, which
        # the maintaining-para-systems skill drives.
        if child.name in pp.SKELETON:
            continue
        # So are PARA.md and .para/ -- the plugin's own output. Filing the
        # index away makes every later scan match nothing; filing .para/ away
        # leaves undo.py unable to infer the root from a manifest.
        if child.name in PLUGIN_ARTIFACTS:
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


def scan(root, *, archive_after_months=12, metadata_only=False,
         peek_files=200, peek_bytes=8192, para=None):
    index = parse_index(para) if para else Index()
    entries, stats = walk(root, index, metadata_only=metadata_only)
    clusters = cluster(entries, index, archive_after_months=archive_after_months)

    peeked = []
    if not metadata_only:
        unresolved = [c for c in clusters if c["kind"] == "unresolved"]
        if unresolved:
            pending = [{"rel": rel} for rel in unresolved[0]["files"]]
            for rel in peek_candidates(pending, root, index, peek_files=peek_files):
                text = peek(root / rel, peek_bytes)
                if not text:
                    continue
                peeked.append(rel)
                for name in index.all_names():
                    if name.casefold() in text.casefold():
                        unresolved[0].setdefault("peek_hints", {})[rel] = name
                        break

    return {
        "version": 1,
        "root": str(root),
        "volume": pp.volume_of(root),
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "metadata_only": metadata_only,
        "peeked": peeked,
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
    parser.add_argument("--peek-files", type=int, default=200)
    parser.add_argument("--peek-bytes", type=int, default=8192)
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
             metadata_only=args.metadata_only, peek_files=args.peek_files,
             peek_bytes=args.peek_bytes, para=para),
        sys.stdout, indent=2,
    )
    print()


if __name__ == "__main__":
    main()
