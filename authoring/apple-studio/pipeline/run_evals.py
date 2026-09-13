#!/usr/bin/env python3
"""Trigger-eval sweep for apple-studio skills, with a fixture write guard.

Promoted to git on 2026-09-12 from the Phase 6 session scratchpad, where the
driver was re-invented each phase and produced three defects that each looked
like a skill misfire. All three fixes are behavior here, not memory:

1. **stdin leak.** Phase 6 round 1 ran `claude` inside a `while read` loop, so
   the child inherited the loop's stdin and swallowed the remaining prompt file
   into its own prompt. One eval then "failed" on a prompt that was never sent.
   Every child is launched with stdin at /dev/null.

2. **Turn exhaustion read as a misfire.** At `--max-turns 2` a session can burn
   both turns on denied Bash exploration and hit the cap before invoking any
   skill. That is a harness defect, not a routing defect. The default is 6, and
   a run that ends in `error_max_turns` is reported as `max_turns` in its own
   column rather than silently scored as a miss.

3. **The fixture gets written to despite `--allowedTools`.** The Phase 6 sweep
   left nine source files and a build directory in StudioFixture. The guard
   below checks the fixture's git status before the sweep, after every single
   prompt, and once at the end; it attributes writes to the prompt that made
   them, restores the tree, and exits non-zero.

Python 3 standard library only, per the pipeline rule. No jq dependency: the
stream-json parsing that needed it is done here.

Usage:
    python3 pipeline/run_evals.py PROMPTS.tsv OUTDIR [options]

PROMPTS.tsv is tab-separated, `#` comments and blank lines ignored:
    id <TAB> skill <TAB> FIRE|NOFIRE <TAB> prompt

Exit codes: 0 all passed and the fixture stayed clean; 1 a verdict failed or
the fixture was written to; 2 setup refused the run.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_FIXTURE = Path.home() / "Projects" / "StudioFixture"
DEFAULT_ALLOWED_TOOLS = "Skill Read"
DEFAULT_MAX_TURNS = 6
DEFAULT_TIMEOUT = 300


class Refused(Exception):
    """Setup problem that must stop the sweep before any session runs."""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def fixture_status(fixture: Path) -> list[str]:
    """Porcelain status lines for the fixture, or raise if it isn't a repo."""
    probe = git(fixture, "rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0:
        raise Refused(
            f"{fixture} is not a git work tree, so nothing can attribute or "
            f"undo writes made during the sweep."
        )
    result = git(fixture, "status", "--porcelain")
    if result.returncode != 0:
        raise Refused(f"git status failed in {fixture}: {result.stderr.strip()}")
    return [line for line in result.stdout.splitlines() if line.strip()]


def restore_fixture(fixture: Path) -> None:
    git(fixture, "restore", ".")
    git(fixture, "clean", "-fd")


def read_prompts(path: Path, only: set[str] | None) -> list[dict]:
    rows = []
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 4:
            raise Refused(
                f"{path}:{lineno} has {len(parts)} tab-separated fields, "
                f"expected 4 (id, skill, FIRE|NOFIRE, prompt)."
            )
        row = {
            "id": parts[0].strip(),
            "skill": parts[1].strip(),
            "expect": parts[2].strip().upper(),
            "prompt": "\t".join(parts[3:]).strip(),
        }
        if row["expect"] not in {"FIRE", "NOFIRE"}:
            raise Refused(
                f"{path}:{lineno} expectation is {row['expect']!r}, "
                f"expected FIRE or NOFIRE."
            )
        if only is None or row["id"] in only:
            rows.append(row)
    if not rows:
        raise Refused(f"No prompts selected from {path}.")
    return rows


def parse_stream(log_text: str) -> tuple[list[str], str]:
    """Return (skills invoked, in order) and a note: '', 'max_turns', 'error'."""
    skills: list[str] = []
    note = ""
    for line in log_text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            content = event.get("message", {}).get("content") or []
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "tool_use":
                    continue
                if block.get("name") != "Skill":
                    continue
                name = (block.get("input") or {}).get("skill")
                if isinstance(name, str) and name:
                    skills.append(name.split(":")[-1])
        elif event.get("type") == "result":
            subtype = event.get("subtype", "")
            if subtype == "error_max_turns":
                note = "max_turns"
            elif event.get("is_error") or subtype.startswith("error"):
                note = "error"
    return skills, note


def verdict_for(row: dict, fired: str) -> str:
    """Phase 3-6 scoring, carried forward unchanged.

    A NOFIRE prompt passes when the named skill stays silent, including when a
    different skill answers instead — routing to the right neighbour is stronger
    evidence of a clean boundary than silence.
    """
    if row["expect"] == "FIRE":
        return "PASS" if fired == row["skill"] else "FAIL"
    return "PASS" if fired != row["skill"] else "FAIL"


def run_one(row: dict, args, out_dir: Path) -> dict:
    log_path = out_dir / f"{row['id']}.log"
    cmd = [
        args.claude_bin,
        "--plugin-dir",
        str(args.plugin_dir),
        "-p",
        row["prompt"],
        "--output-format",
        "stream-json",
        "--verbose",
        "--max-turns",
        str(args.max_turns),
        "--allowedTools",
        args.allowed_tools,
    ]
    note = ""
    try:
        with open(os.devnull, "rb") as devnull:  # the stdin-leak fix
            completed = subprocess.run(
                cmd,
                cwd=str(args.fixture),
                stdin=devnull,
                capture_output=True,
                text=True,
                timeout=args.timeout,
                check=False,
            )
        log_text = completed.stdout
        if completed.stderr:
            log_text += "\n--- stderr ---\n" + completed.stderr
    except subprocess.TimeoutExpired:
        log_text = f"--- timed out after {args.timeout}s ---\n"
        note = "timeout"
    log_path.write_text(log_text)

    skills, stream_note = parse_stream(log_text)
    note = note or stream_note
    fired = skills[0] if skills else "(none)"
    return {
        **row,
        "fired": fired,
        "all_fired": ",".join(skills),
        "verdict": verdict_for(row, fired),
        "note": note,
        "log": log_path.name,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("prompts", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument(
        "--plugin-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent.parent / "plugins" / "apple-studio",
    )
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--allowed-tools", default=DEFAULT_ALLOWED_TOOLS)
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--only", default=None, help="comma-separated prompt ids")
    args = parser.parse_args()

    args.fixture = args.fixture.expanduser().resolve()
    args.plugin_dir = args.plugin_dir.expanduser().resolve()

    try:
        if not args.plugin_dir.is_dir():
            raise Refused(f"--plugin-dir {args.plugin_dir} does not exist.")
        only = set(args.only.split(",")) if args.only else None
        rows = read_prompts(args.prompts, only)

        dirty = fixture_status(args.fixture)
        if dirty:
            raise Refused(
                f"{args.fixture} is dirty before the sweep, so writes made "
                f"during it could not be attributed:\n  "
                + "\n  ".join(dirty)
            )
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    dirtied_by = []

    for index, row in enumerate(rows, start=1):
        print(f"[{index}/{len(rows)}] {row['id']} ", end="", flush=True)
        result = run_one(row, args, args.out_dir)

        wrote = fixture_status(args.fixture)  # the guard, per prompt
        result["wrote"] = ";".join(line[3:] for line in wrote)
        if wrote:
            dirtied_by.append((row["id"], list(wrote)))
            restore_fixture(args.fixture)

        results.append(result)
        flag = f"  WROTE {len(wrote)} path(s)" if wrote else ""
        note = f" ({result['note']})" if result["note"] else ""
        print(f"-> {result['fired']}  {result['verdict']}{note}{flag}")

    header = ["id", "skill", "expect", "fired", "verdict", "note", "wrote", "log"]
    tsv = args.out_dir / "results.tsv"
    with tsv.open("w") as handle:
        handle.write("\t".join(header) + "\n")
        for result in results:
            handle.write("\t".join(str(result.get(key, "")) for key in header) + "\n")

    passed = sum(1 for r in results if r["verdict"] == "PASS")
    print(f"\n{passed}/{len(results)} PASS   results: {tsv}")

    leftover = fixture_status(args.fixture)  # the closing check
    if leftover:
        print(f"fixture still dirty at close: {leftover}", file=sys.stderr)
        restore_fixture(args.fixture)

    if dirtied_by:
        print(
            f"\nfixture written to by {len(dirtied_by)} prompt(s) despite "
            f"--allowedTools {args.allowed_tools!r}:",
            file=sys.stderr,
        )
        for prompt_id, paths in dirtied_by:
            print(f"  {prompt_id}: {', '.join(p[3:] for p in paths)}", file=sys.stderr)
        print("fixture restored; treat any prompt that reads the project as contaminated.",
              file=sys.stderr)

    if passed != len(results) or dirtied_by or leftover:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
