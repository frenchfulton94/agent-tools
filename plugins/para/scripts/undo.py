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


def undo(manifest_path, root):
    restored, skipped = 0, []
    lines = pathlib.Path(manifest_path).read_text(encoding="utf-8").splitlines()

    # Reverse order, so nested destinations unwind before their parents.
    for line in reversed(lines):
        if not line.strip():
            continue
        record = json.loads(line)
        current = root / record["to"]
        origin = root / record["from"]

        if not current.exists() and not current.is_symlink():
            skipped.append({"file": record["to"], "reason": "already restored"})
            continue

        info = current.lstat()
        unchanged = (
            info.st_size == record["size"]
            and info.st_mtime_ns == record["mtime_ns"]
            and info.st_ino == record["inode"]
        )
        if not unchanged:
            skipped.append({"file": record["to"], "reason": "modified since the move"})
            continue

        origin.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(current), str(pp.safe_destination(origin)))
        restored += 1

    return {"restored": restored, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(description="Reverse a PARA apply run.")
    parser.add_argument("manifest")
    parser.add_argument("--root", default=None,
                        help="Defaults to the grandparent of the manifest (<root>/.para/).")
    args = parser.parse_args()

    manifest = pathlib.Path(args.manifest).resolve()
    raw_root = args.root or str(manifest.parent.parent)
    try:
        root = pp.validate_root(raw_root)
    except pp.UnsafeRoot as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)

    result = undo(manifest, root)
    print(json.dumps(result, indent=2))
    for entry in result["skipped"]:
        print(f"skipped {entry['file']}: {entry['reason']}", file=sys.stderr)


if __name__ == "__main__":
    main()
