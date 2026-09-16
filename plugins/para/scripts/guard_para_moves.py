#!/usr/bin/env python3
"""PreToolUse guard for a PARA-managed root.

Reads a PreToolUse payload on stdin and returns a permission decision. Exit 0
always; the decision travels in the JSON body, matching
plugins/unraid-ops/scripts/guard_destructive_storage.py.

Scope is deliberate. The guard only has an opinion inside a root that apply.py
has registered, which means it fails open elsewhere. The alternative — judging
every rm anywhere — fires on ordinary work, and a hook that annoys gets
disabled, which fails open permanently and everywhere. Narrow and durable beats
broad and switched off.

No imports from the other para modules: the guard must never fail to load
because a sibling module has a problem.

Accepted limitations: this is a lexical guard over the literal command text.
It cannot see through backticks or $(...) command substitution, $HOME/~
expansion, or an interpreter one-liner like `python3 -c "shutil.rmtree(...)"`.
Those are out of scope for a PreToolUse text match.
"""

import json
import os
import pathlib
import re
import sys

DESTRUCTIVE = ("rm", "rmdir", "unlink", "shred", "trash")
RELOCATING = ("mv", "rename")
WRAPPERS = {"sudo", "doas", "env", "nohup", "time", "command", "exec", "builtin", "xargs"}


def registry_path():
    override = os.environ.get("PARA_ROOTS_FILE")
    if override:
        return pathlib.Path(override)
    return pathlib.Path.home() / ".config" / "para" / "roots"


def registered_roots(path=None):
    target = pathlib.Path(path) if path else registry_path()
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    return [line.strip() for line in lines if line.strip()]


def segments(command):
    return [s for s in re.split(r"&&|\|\||[;|&\n]", command) if s.strip()]


def leading_word(segment):
    stripped = segment.strip().lstrip("({ \t")
    for _ in range(8):  # bounded: sudo env nohup ... nests only so far
        while re.match(r"^\w+=\S*\s+", stripped):
            stripped = re.sub(r"^\w+=\S*\s+", "", stripped)
        match = re.match(r"^([\w./-]+)", stripped)
        if not match:
            return ""
        word = match.group(1).split("/")[-1]
        if word not in WRAPPERS:
            return word
        stripped = stripped[match.end():].strip()
        while stripped.startswith("-"):
            stripped = re.sub(r"^\S+\s*", "", stripped)
    return ""


def touches_root(segment, roots):
    """Return the root a segment's path tokens actually fall inside.

    Boundary matching, never a substring test: a root of /Users/me/Documents
    must not match the unmanaged sibling /Users/me/Documents-backup.
    """
    tokens = re.findall(r"'[^']*'|\"[^\"]*\"|[^\s;|&]+", segment)
    for raw in tokens:
        token = raw.strip("'\"")
        for root in roots:
            base = root.rstrip("/")
            if token == base or token.startswith(base + "/"):
                return root
    return None


def _deletes_by_flag(segment, lead):
    """Deletion that does not lead with a destructive verb."""
    if lead == "find" and re.search(r"(?:^|\s)-delete(?:\s|$)", segment):
        return True
    if lead == "rsync" and "--remove-source-files" in segment:
        return True
    if lead == "git" and re.search(r"^\s*git\s+clean\b", segment):
        return True
    return False


def evaluate(command, roots):
    """Return (decision, reason), or None when the guard has no opinion."""
    if not roots:
        return None

    cwd_root = None
    for segment in segments(command):
        lead = leading_word(segment)

        # `cd <root> && rm -rf x` is an ordinary shape: after the cd, a bare
        # relative path is still inside the managed root.
        if lead == "cd":
            cwd_root = touches_root(segment, roots)
            continue

        root = touches_root(segment, roots) or cwd_root
        if not root:
            continue

        if lead in DESTRUCTIVE or _deletes_by_flag(segment, lead):
            return (
                "deny",
                f"This deletes inside the PARA root {root}. Deletion is not part of "
                "this plugin's vocabulary — archiving is a move. If something must "
                "go, move it to 4-Archives instead.",
            )
        if lead in RELOCATING:
            return (
                "deny",
                f"This moves files inside the PARA root {root} without going through "
                "apply.py, so no undo manifest would be written. Produce a plan and "
                "apply it, or run the move outside the managed root.",
            )
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # Malformed payload: stay out of the way.

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command.strip():
        sys.exit(0)

    verdict = evaluate(command, registered_roots())
    if not verdict:
        sys.exit(0)

    decision, reason = verdict
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": f"[para] {reason}",
            }
        },
        sys.stdout,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
