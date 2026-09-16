#!/usr/bin/env python3
"""Reverse an apply run from its manifest.

Per-file refusal, never whole-run abort: a file edited since the move is
reported and skipped while the rest proceed. Re-running a reversed manifest is
a no-op, not an error.

The change detector is size + mtime_ns + inode. A content hash would cost a
full read of every large file and adds nothing over the triple for spotting a
post-move edit.
"""

import argparse
import json
import pathlib
import shutil
import sys

import para_paths as pp


def _restore_one(line, root):
    """Restore a single manifest line.

    Returns (True, None) when a file was restored, or (False, reason) when it
    was deliberately skipped. It may raise anything at all: the caller's
    blanket handler is the backstop. Three rounds of bounding the failure
    surface by exception type proved that approach does not hold.
    """
    record = json.loads(line)
    origin_rel = record["from"]
    target_rel = record["to"]
    size = record["size"]
    mtime_ns = record["mtime_ns"]
    inode = record["inode"]

    if not isinstance(origin_rel, str) or not isinstance(target_rel, str):
        raise TypeError("manifest paths must be strings")

    for rel in (origin_rel, target_rel):
        candidate = pathlib.PurePath(rel)
        if candidate.is_absolute() or ".." in candidate.parts:
            return False, "manifest path escapes the root"

    # `root / ""` is `root` itself, which would move the root into its own child.
    if not pathlib.PurePath(origin_rel).parts or not pathlib.PurePath(target_rel).parts:
        return False, "unreadable manifest line"

    current = root / target_rel
    origin = root / origin_rel

    if not current.exists() and not current.is_symlink():
        return False, "already restored"

    info = current.lstat()
    if (info.st_size, info.st_mtime_ns, info.st_ino) != (size, mtime_ns, inode):
        return False, "modified since the move"

    origin.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(current), str(pp.safe_destination(origin)))
    return True, None


def undo(manifest_path, root):
    restored, skipped = 0, []
    # `surrogateescape` decodes undecodable bytes into surrogates instead of
    # raising. A partially written or corrupted manifest is exactly the artifact
    # this tool exists to read, so the whole-file read must not abort the run
    # either; the surrogates flow on into `_restore_one` and land in its
    # blanket handler when they reach the filesystem.
    try:
        raw = pathlib.Path(manifest_path).read_text(
            encoding="utf-8", errors="surrogateescape"
        )
    except OSError as error:
        # An unreadable manifest is a clean, reported failure — never a traceback.
        return {
            "restored": 0,
            "skipped": [{"file": str(manifest_path), "reason": "unreadable manifest line"}],
        }
    lines = raw.splitlines()

    # Reverse order, so nested destinations unwind before their parents.
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            ok, reason = _restore_one(line, root)
        except Exception:
            # The backstop. A hand-edited or truncated manifest line must cost
            # only itself, no matter which exception it provokes.
            ok, reason = False, "unreadable manifest line"
        if ok:
            restored += 1
        else:
            skipped.append({"file": line.strip()[:60], "reason": reason})

    return {"restored": restored, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(description="Reverse a PARA apply run.")
    parser.add_argument("manifest")
    parser.add_argument("--root", default=None,
                        help="Defaults to the grandparent of the manifest (<root>/.para/).")
    args = parser.parse_args()

    manifest = pathlib.Path(args.manifest).resolve()
    if args.root:
        raw_root = args.root
    else:
        if manifest.parent.name != ".para":
            print(
                f"{manifest} is not inside a .para directory, so the root cannot be "
                "inferred. Pass --root explicitly.",
                file=sys.stderr,
            )
            sys.exit(2)
        raw_root = str(manifest.parent.parent)
    try:
        root = pp.validate_root(raw_root)
    except pp.UnsafeRoot as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)

    result = undo(manifest, root)
    print(json.dumps(result, indent=2))
    for entry in result["skipped"]:
        print(f"skipped {entry['file']}: {entry['reason']}", file=sys.stderr)

    # "already restored" is the idempotent re-run and is a success. Any other
    # skip is a file this tool was asked to restore and did not.
    refused = [e for e in result["skipped"] if e["reason"] != "already restored"]
    if refused:
        sys.exit(1)


if __name__ == "__main__":
    main()
