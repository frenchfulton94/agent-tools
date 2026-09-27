"""Run the Godot binary and interpret what it says.

Three things make this less obvious than it looks.

First, exit codes are useless. `--check-only` returns 0 for a script with
parse errors (spec 3.1), so a wrapper that tests returncode reports broken code
as fine. Everything here classifies by reading stderr.

Second, macOS has no timeout(1) (spec 3.6), and a Godot scene with no quit
condition runs forever. Every call carries its own deadline and kill.

Third, killing the immediate child is not enough. `run_scene` executes
arbitrary agent-authored GDScript, which can call `OS.execute()` /
`OS.create_process()` and spawn its own children. If a scene hangs, those
grandchildren inherit the stdout/stderr pipes and keep their write ends open
even after the immediate child is killed, so `communicate()` blocks forever
waiting for an EOF that never comes, and the grandchild survives as an orphan.
Every subprocess here starts its own session (`start_new_session=True`) so its
whole process group can be killed at once with `killpg`, not just its PID.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
from dataclasses import dataclass

MAC_APP = "/Applications/Godot.app/Contents/MacOS/Godot"

_HEAD = re.compile(r"^(SCRIPT ERROR|SHADER ERROR|ERROR|WARNING):\s*(.*)$")
# Only res:// locations are the user's files; engine C++ frames are not.
_AT = re.compile(r"^\s*at:\s*.*\((res://[^:)]+):(\d+)\)\s*$")


class MissingBinary(Exception):
    pass


@dataclass
class Result:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool


def find_binary():
    override = os.environ.get("GODOT_BIN", "").strip()
    if override:
        return override
    for name in ("godot", "godot4"):
        found = shutil.which(name)
        if found:
            return found
    if os.path.isfile(MAC_APP):
        return MAC_APP
    return None


def run(args, cwd=None, timeout=60) -> Result:
    binary = find_binary()
    if not binary:
        raise MissingBinary(
            "Godot not found. Install it, or set GODOT_BIN to the binary path."
        )
    try:
        proc = subprocess.Popen(
            [binary, *args],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            # Its own session, so a hung run's whole process group -- not
            # just this one PID -- can be killed on timeout. See module
            # docstring: a scene's OS.execute()/OS.create_process() child
            # would otherwise survive `proc.kill()` as an orphan holding the
            # stderr pipe open, and communicate() would block forever.
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        # GODOT_BIN (or a stale PATH/app-bundle result) named a path that
        # does not exist. Surface this module's own error, not a raw OSError.
        raise MissingBinary(
            f"Godot binary not found at {binary!r}: {exc}"
        ) from exc
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return Result(stdout, stderr, proc.returncode, False)
    except subprocess.TimeoutExpired:
        # `start_new_session=True` above guarantees this process is its own
        # session AND process-group leader, so its pgid is its own pid --
        # for the life of the group, not just at creation. Use that directly
        # rather than os.getpgid(proc.pid): on macOS, getpgid raises
        # ProcessLookupError once the immediate child has already exited
        # (the common case -- it forks a grandchild and returns), even
        # though the group itself, still holding that live grandchild, is
        # perfectly valid to signal. Measured: getpgid failing here silently
        # skipped the kill entirely and left communicate() blocked forever.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            # The group kill itself didn't finish tearing things down in
            # time; fall back to killing just the PID we hold, then block
            # until the pipes actually close.
            proc.kill()
            stdout, stderr = proc.communicate()
        returncode = proc.returncode if proc.returncode is not None else -1
        return Result(stdout, stderr, returncode, True)


def diagnostics(stderr: str) -> list:
    lines = stderr.splitlines()
    header_idxs = [i for i, line in enumerate(lines) if _HEAD.match(line)]
    found = []
    for pos, i in enumerate(header_idxs):
        head = _HEAD.match(lines[i])
        entry = {
            "severity": head.group(1),
            "message": head.group(2).strip(),
            "file": None,
            "line": None,
        }
        # Look ahead for this header's own `at:` frame, but never past the
        # next header. Without this clamp, a header whose own frame points
        # into engine C++ (and is therefore rejected) reaches past it and
        # steals the *following* diagnostic's res:// location -- reporting
        # one error at another, unrelated error's file and line.
        next_header = header_idxs[pos + 1] if pos + 1 < len(header_idxs) else len(lines)
        limit = min(i + 4, next_header)
        for follow in lines[i + 1 : limit]:
            at = _AT.match(follow)
            if at:
                entry["file"] = at.group(1)
                entry["line"] = int(at.group(2))
                break
        found.append(entry)
    return found


def check_script(root: str, rel_path: str, timeout: int = 30) -> list:
    result = run(
        ["--headless", "--path", root, "--check-only", "--script", rel_path],
        timeout=timeout,
    )
    return diagnostics(result.stderr)


def run_scene(root: str, scene=None, frames: int = 120, timeout: int = 60) -> dict:
    args = ["--headless", "--path", root, "--quit-after", str(frames)]
    if scene:
        args += ["--scene", scene]
    result = run(args, timeout=timeout)
    return {
        "stdout": result.stdout,
        "diagnostics": diagnostics(result.stderr),
        "timed_out": result.timed_out,
    }
