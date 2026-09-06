#!/usr/bin/env python3
"""PreToolUse guard for destructive Unraid storage commands.

Reads a PreToolUse payload on stdin, inspects Bash commands, and returns a
permission decision. Exit 0 always; the decision travels in the JSON body.

Design notes:
  - deny is reserved for patterns that are never correct on an Unraid server.
  - ask is used where the same command is legitimate on a pool or unassigned
    device but catastrophic on an array member, because the hook cannot tell
    which a given /dev/sdX is. Surfacing it to the human is the honest move.
  - Commands are split on shell separators and judged per segment, so
    `ls /mnt/user && ls /mnt/disk1` is not mistaken for a cross-view copy.
"""

import json
import re
import sys

# Leading commands that only read. Cross-view path pairs in these are almost
# always a grep pattern or a path listing, not a copy.
READ_ONLY = {
    "echo", "grep", "egrep", "fgrep", "rg", "cat", "less", "more", "head",
    "tail", "ls", "stat", "du", "df", "file", "wc", "find", "test", "[",
    "printf", "diff", "cmp", "md5sum", "sha256sum", "tree",
}

WHOLE_DISK = r"/dev/(?:sd[a-z]+|nvme\d+n\d+|hd[a-z]+)(?![\dp])"
PARTITION = r"/dev/(?:sd[a-z]+\d+|nvme\d+n\d+p\d+|hd[a-z]+\d+)"
REPAIR_TOOL = r"\b(?:xfs_repair|e2fsck|fsck(?:\.\w+)?)\b"

DOCS = "docs.unraid.net"


def segments(command):
    """Split a command line into independently executed segments."""
    return [s for s in re.split(r"&&|\|\||[;|&\n]", command) if s.strip()]


def leading_word(segment):
    stripped = segment.strip()
    # Skip leading env assignments like FOO=bar cmd
    while re.match(r"^\w+=\S*\s+", stripped):
        stripped = re.sub(r"^\w+=\S*\s+", "", stripped)
    match = re.match(r"^([\w./\[-]+)", stripped)
    return match.group(1).split("/")[-1] if match else ""


def evaluate(segment):
    """Return (decision, reason) or None if the segment looks fine."""
    lead = leading_word(segment)
    read_only = lead in READ_ONLY

    # --- deny: documented data-loss paths that are never correct ---

    if not read_only and "/mnt/user" in segment and re.search(r"/mnt/disk\d", segment):
        return (
            "deny",
            "This command references both /mnt/user and /mnt/diskN. They are two "
            "views of the same files, and cp/rsync cannot tell them apart — the "
            "documented result is corruption or data loss. Stay entirely within "
            "one view: copy between /mnt/diskN paths, or between /mnt/user paths, "
            "or use Mover. See the shares-and-mover reference.",
        )

    if re.search(REPAIR_TOOL, segment) and re.search(WHOLE_DISK, segment):
        return (
            "deny",
            "A filesystem repair tool is targeting a whole disk rather than a "
            "partition. Unraid array disks are repaired through the Unraid device "
            "(/dev/mdXp1 on 6.12+, /dev/mdX on 6.11 and earlier) with the array in "
            "Maintenance Mode. Targeting a whole disk is never correct, and "
            "targeting /dev/sdX1 on an array member bypasses the parity layer and "
            "invalidates parity.",
        )

    if re.search(r"\bdd\b", segment) and re.search(
        r"\bof=/dev/(?:sd[a-z]|nvme\d|hd[a-z])", segment
    ):
        return (
            "deny",
            "dd is writing directly to a raw disk device. The documented Unraid "
            "disk-zeroing procedure writes to the Unraid device instead "
            "(of=/dev/mdXp1 on 6.12+, of=/dev/mdX earlier) so parity stays valid. "
            "Writing to /dev/sdX on an array member destroys the disk and leaves "
            "parity inconsistent.",
        )

    # --- ask: legitimate somewhere, catastrophic elsewhere ---

    if re.search(r"\bmkfs(?:\.\w+)?\b", segment):
        return (
            "ask",
            "This formats a device. Formatting is normally done from the WebGUI, "
            "and formatting an existing array disk erases it AND updates parity, "
            "so the data can no longer be reconstructed. Confirm the target is a "
            "new or unassigned device, by serial number, before allowing.",
        )

    if re.search(REPAIR_TOOL, segment) and re.search(PARTITION, segment):
        return (
            "ask",
            "A filesystem repair is targeting a raw partition. That is correct for "
            "a pool or unassigned device, but on an array member it bypasses the "
            "parity layer and invalidates parity — array disks must be repaired "
            "via /dev/mdXp1 in Maintenance Mode. Confirm which this device is.",
        )

    if re.search(r"\bbtrfs\s+check\b", segment) and "--repair" in segment:
        return (
            "ask",
            "btrfs check --repair can make damage worse. The documented order is "
            "`btrfs scrub` first, then a read-only `btrfs check --readonly`, and "
            "--repair only with a backup in hand and after consulting the forums.",
        )

    if re.search(r"\bzpool\s+(?:destroy|labelclear)\b", segment):
        return (
            "ask",
            "This destroys a ZFS pool or its labels. Confirm the pool name and "
            "that its data is already moved or backed up.",
        )

    if re.search(r"\bwipefs\b", segment) and "/dev/" in segment:
        return (
            "ask",
            "wipefs removes filesystem signatures, which makes a disk unmountable "
            "and its data unrecoverable without specialist tools. Confirm the "
            "target device by serial number.",
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

    verdicts = [v for v in (evaluate(s) for s in segments(command)) if v]
    if not verdicts:
        sys.exit(0)

    # deny outranks ask, matching the harness's own precedence.
    decision, reason = next(
        (v for v in verdicts if v[0] == "deny"), verdicts[0]
    )

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": f"[unraid-ops] {reason} ({DOCS})",
            }
        },
        sys.stdout,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
