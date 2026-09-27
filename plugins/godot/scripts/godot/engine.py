"""Run the Godot binary and interpret what it says.

Two things make this less obvious than it looks.

First, exit codes are useless. `--check-only` returns 0 for a script with
parse errors (spec 3.1), so a wrapper that tests returncode reports broken code
as fine. Everything here classifies by reading stderr.

Second, macOS has no timeout(1) (spec 3.6), and a Godot scene with no quit
condition runs forever. Every call carries its own deadline and kill.
"""

from __future__ import annotations

import os
import re
import shutil
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
    proc = subprocess.Popen(
        [binary, *args],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return Result(stdout, stderr, proc.returncode, False)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        return Result(stdout, stderr, proc.returncode or -1, True)


def diagnostics(stderr: str) -> list:
    found = []
    lines = stderr.splitlines()
    for i, line in enumerate(lines):
        head = _HEAD.match(line)
        if not head:
            continue
        entry = {
            "severity": head.group(1),
            "message": head.group(2).strip(),
            "file": None,
            "line": None,
        }
        for follow in lines[i + 1 : i + 4]:
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
