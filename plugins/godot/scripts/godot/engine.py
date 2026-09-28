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

# Since Godot 4.5, a runtime GDScript error is followed by its own call
# stack: a header line, then one `[N] function (location)` line per frame,
# most-recent-call-first. Frame lines never match _HEAD (they start with
# `[`, not a severity word), so they can never be mistaken for a diagnostic
# of their own; `_BT_LOC` below applies the exact same res://-only rule
# `_AT` does to each frame's location, since a frame can equally point into
# engine C++.
_BT_HEADER = re.compile(r"^\s*GDScript backtrace \(most recent call first\):\s*$")
_BT_FRAME = re.compile(r"^\s*\[(\d+)\]\s+(\S+)\s+\((.+)\)\s*$")
_BT_LOC = re.compile(r"^(res://[^:]+):(\d+)$")

# Mirrors check-gdscript.sh's own 40-line cap on the same class of problem: a
# deep or infinite recursion crash can print a backtrace hundreds of frames
# long, and an uncapped dump lands entirely in whatever is reading this
# tool's output. Frames beyond this are counted, not silently dropped --
# see `backtrace_truncated` below.
MAX_BACKTRACE_FRAMES = 40


class MissingBinary(Exception):
    pass


class ScriptCheckTimedOut(Exception):
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


def run(args, cwd=None, timeout=60, env=None) -> Result:
    binary = find_binary()
    if not binary:
        raise MissingBinary(
            "Godot not found. Install it, or set GODOT_BIN to the binary path."
        )
    try:
        proc = subprocess.Popen(
            [binary, *args],
            cwd=cwd,
            env=env,
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

    def _kill_group():
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
        stdout, stderr = proc.communicate(timeout=timeout)
        return Result(stdout, stderr, proc.returncode, False)
    except subprocess.TimeoutExpired:
        _kill_group()
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
    except BaseException:
        # Anything else unwinding through communicate() -- a
        # KeyboardInterrupt, a bug in a caller's own code running on this
        # thread, whatever -- must still tear down the whole process group
        # before propagating, exactly like the timeout path above. This
        # predates Task 7 (every engine.run caller was exposed), but Task
        # 7's windowed drivers are the first callers where the orphan left
        # behind is a VISIBLE WINDOW on the user's screen, not an invisible
        # headless process.
        _kill_group()
        # Reap rather than leave a zombie: the immediate child is dead (or
        # dying) from the SIGKILL above, so this just collects its exit
        # status -- no pipe-draining needed (nothing more will be written)
        # and no deadlock risk (wait() blocks on process state, not I/O).
        # Bounded exactly like the timeout path's own reap, for the same
        # reason: a caller who keeps this process alive for many calls (an
        # MCP server) must not accumulate zombies across repeated failures.
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except (ProcessLookupError, PermissionError):
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        # Nothing will read these again (the exception is about to
        # propagate past any Result construction), so close them explicitly
        # rather than leave the fds for the garbage collector to find.
        for pipe in (proc.stdout, proc.stderr):
            if pipe is not None:
                pipe.close()
        raise


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
        at_idx = None
        for j in range(i + 1, limit):
            at = _AT.match(lines[j])
            if at:
                entry["file"] = at.group(1)
                entry["line"] = int(at.group(2))
                at_idx = j
                break

        # A backtrace, when present, always immediately follows the `at:`
        # line this diagnostic's own frame was just found on -- never
        # searched for independently of it, and never past `next_header`,
        # for the same reason the `at:` search itself is bounded there: a
        # backtrace's frame lines don't match _HEAD, so they can't be
        # confused for a diagnostic, but bounding by next_header keeps this
        # entirely inside the one diagnostic it belongs to regardless.
        if at_idx is not None:
            backtrace, truncated = _parse_backtrace(lines, at_idx + 1, next_header)
            if backtrace:
                entry["backtrace"] = backtrace
                if truncated:
                    entry["backtrace_truncated"] = truncated

        found.append(entry)
    return found


def _parse_backtrace(lines, start, limit):
    """Parse a `GDScript backtrace (most recent call first):` block that
    begins at `lines[start]`, if it's actually there -- returns `([], 0)`
    immediately otherwise (the ordinary case: most diagnostics, including
    every compile-time one from `check_script`/`check_shader`, have no
    backtrace at all, since nothing has actually run yet).

    Returns `(frames, truncated_count)`. `frames` is capped at
    `MAX_BACKTRACE_FRAMES`; `truncated_count` is how many real frames beyond
    the cap were left out, so a caller can tell "the chain was this deep and
    we stopped" from "that's the whole chain" -- the same distinction
    `check_shader`'s `ShaderCheckTimedOut` exists to preserve for a timeout,
    just for a different kind of truncation.
    """
    if start >= limit or not _BT_HEADER.match(lines[start]):
        return [], 0

    frames = []
    j = start + 1
    while j < limit:
        m = _BT_FRAME.match(lines[j])
        if not m:
            break
        loc = _BT_LOC.match(m.group(3))
        if loc:
            file_, line_ = loc.group(1), int(loc.group(2))
        else:
            # Same rule _AT enforces: a frame whose location isn't a res://
            # path (engine C++, or anything else unrecognised) is not a
            # user file, so it's reported with no file/line rather than a
            # fabricated one -- the frame index and function name are still
            # real and still kept.
            file_, line_ = None, None
        frames.append({
            "frame": int(m.group(1)),
            "function": m.group(2),
            "file": file_,
            "line": line_,
        })
        j += 1

    if len(frames) > MAX_BACKTRACE_FRAMES:
        return frames[:MAX_BACKTRACE_FRAMES], len(frames) - MAX_BACKTRACE_FRAMES
    return frames, 0


def check_script(root: str, rel_path: str, timeout: int = 30) -> list:
    """Raises ScriptCheckTimedOut rather than silently returning `[]` when the
    check itself times out. `result.timed_out` and "no diagnostics" are not the
    same fact: `run()` SIGKILLs a hung engine, which then prints nothing, so a
    timeout produces exactly the empty stderr a clean script produces -- and
    the server renders an empty list as "the script parses and type-checks."
    Falling through to `[]` here would report a script that was never actually
    checked as fine, which is the one thing section 3.1 of the spec exists to
    prevent. Same defect, same fix as render.check_shader; this is its sibling.
    """
    result = run(
        ["--headless", "--path", root, "--check-only", "--script", rel_path],
        timeout=timeout,
    )
    if result.timed_out:
        raise ScriptCheckTimedOut(
            f"check_script timed out after {timeout}s on {rel_path!r}. "
            "This is not a verdict -- it is not the same as a clean parse. "
            "A first-ever --check-only on a large project runs an implicit "
            "import pass, which can exceed the timeout; try again once the "
            "project has been imported."
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
