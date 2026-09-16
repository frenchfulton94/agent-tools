#!/usr/bin/env python3
"""Execute an approved plan.

Validation is whole-plan and up front: an invalid plan is refused entirely
rather than applied in part. Each manifest line is written BEFORE its move, so
an interrupted run still has a complete record of what it did.

Nothing here deletes. Archiving is a move.
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import sys

import para_paths as pp


class InvalidPlan(Exception):
    """The plan failed validation and was not applied."""


def register_root(root):
    """Record the root so the guard hook knows to have an opinion about it."""
    registry = pathlib.Path(
        os.environ.get("PARA_ROOTS_FILE")
        or pathlib.Path.home() / ".config" / "para" / "roots"
    )
    registry.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if registry.exists():
        existing = [l.strip() for l in registry.read_text(encoding="utf-8").splitlines() if l.strip()]
    if str(root) not in existing:
        existing.append(str(root))
        tmp = registry.with_name(registry.name + ".tmp")
        tmp.write_text("\n".join(existing) + "\n", encoding="utf-8")
        os.replace(tmp, registry)


def _resolve_destination(root, destination, name):
    # Compare against a resolved root: root itself may sit behind a symlink
    # (e.g. macOS TMPDIR, /var -> /private/var), and target is always fully
    # resolved. Comparing an unresolved root to target.parents would flag
    # every legitimate destination as escaping on such a root.
    root_resolved = root.resolve()
    target = (root / destination / name).resolve()
    if root_resolved not in target.parents and target != root_resolved:
        return None
    return target


def validate_plan(plan, root):
    """Return a list of error strings. Empty means the plan is sound."""
    errors = []
    seen = {}
    root_volume = pp.volume_of(root)
    root_resolved = root.resolve()

    for group in plan.get("groups", []):
        destination = group.get("destination", "")
        for rel in group.get("files", []):
            if pathlib.PurePath(rel).is_absolute() or ".." in pathlib.PurePath(rel).parts:
                errors.append(f"{rel}: source path must be relative to the root")
                continue
            source = root / rel
            if not source.exists() and not source.is_symlink():
                errors.append(f"{rel}: source no longer exists")
                continue
            try:
                parent_resolved = source.parent.resolve()
            except OSError:
                errors.append(f"{rel}: source directory is unreadable")
                continue
            if parent_resolved != root_resolved and root_resolved not in parent_resolved.parents:
                errors.append(f"{rel}: source is outside the root")
                continue
            if rel in seen:
                errors.append(f"{rel}: claimed by two groups ({seen[rel]} and {group.get('id')})")
                continue
            seen[rel] = group.get("id")

            target = _resolve_destination(root, destination, source.name)
            if target is None:
                errors.append(f"{rel}: destination {destination} is outside the root")
                continue

            anchor = root / destination
            while not anchor.exists() and anchor != root:
                anchor = anchor.parent
            if pp.volume_of(anchor) != root_volume:
                errors.append(f"{rel}: destination {destination} is on another volume")
    return errors


def apply_plan(plan, root):
    errors = validate_plan(plan, root)
    if errors:
        raise InvalidPlan("; ".join(errors))

    para_dir = root / ".para"
    para_dir.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    manifest = para_dir / f"undo-{stamp}.jsonl"

    for name in pp.SKELETON:
        (root / name).mkdir(exist_ok=True)

    register_root(root)

    moved, skipped = 0, []
    with open(manifest, "a", encoding="utf-8") as log:
        for group in plan.get("groups", []):
            for rel in group.get("files", []):
                source = root / rel
                target_dir = root / group["destination"]
                target_dir.mkdir(parents=True, exist_ok=True)
                planned = target_dir / source.name
                # Identity, not string equality: APFS is case-insensitive, so
                # "0-INBOX" and "0-Inbox" name the same directory and the file
                # would otherwise collide with itself and be renamed. lstat
                # rather than samefile, so a symlink is compared as the link
                # itself -- which is what shutil.move would relocate.
                try:
                    here, there = source.lstat(), planned.lstat()
                    already_there = (here.st_ino, here.st_dev) == (there.st_ino, there.st_dev)
                except OSError:
                    already_there = False
                if already_there:
                    skipped.append({"file": rel, "reason": "already at destination"})
                    continue
                target = pp.safe_destination(planned)
                try:
                    info = source.lstat()
                except OSError:
                    skipped.append({"file": rel, "reason": "unreadable"})
                    continue

                # Written before the move, so an interrupted run stays reversible.
                # A failed move therefore leaves a line whose `to` never appeared:
                # undo.py treats a missing `to` as "already restored" and skips it.
                log.write(json.dumps({
                    "from": rel,
                    "to": str(target.relative_to(root)),
                    "size": info.st_size,
                    "mtime_ns": info.st_mtime_ns,
                    "inode": info.st_ino,
                }) + "\n")
                log.flush()

                try:
                    shutil.move(str(source), str(target))
                    moved += 1
                except OSError as error:
                    print(f"Stopped at {rel}: {error}", file=sys.stderr)
                    print(f"Reverse with: python3 undo.py {manifest}", file=sys.stderr)
                    return {"moved": moved, "skipped": skipped, "manifest": str(manifest)}

    return {"moved": moved, "skipped": skipped, "manifest": str(manifest)}


def main():
    parser = argparse.ArgumentParser(description="Apply an approved PARA plan.")
    parser.add_argument("plan")
    args = parser.parse_args()

    plan = json.loads(pathlib.Path(args.plan).read_text(encoding="utf-8"))
    try:
        root = pp.validate_root(plan["root"])
    except pp.UnsafeRoot as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)

    try:
        result = apply_plan(plan, root)
    except InvalidPlan as error:
        print(f"Plan rejected, nothing moved: {error}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))
    print(
        f'\nReverse this run with:\n'
        f'  python3 "${{CLAUDE_PLUGIN_ROOT}}/scripts/undo.py" "{result["manifest"]}"',
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
