#!/usr/bin/env python3
"""Test the glossary compiler against a golden file and its error paths.

Usage:
    python3 scripts/tests/test_glossary_to_vale.py

Exit code 0 = all checks passed.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "glossary-to-vale.py"
SAMPLE = HERE / "sample-glossary.md"
GOLDEN = HERE / "golden-glossary.yml"

FAILURES = []


def run(path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path)],
        capture_output=True,
        text=True,
    )


def normalize(text):
    """Drop the absolute source path so the golden file is machine-independent."""
    return "\n".join(
        "# Source: sample-glossary.md" if line.startswith("# Source:") else line
        for line in text.splitlines()
    )


def check(name, condition, detail=""):
    if condition:
        print(f"  pass  {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        FAILURES.append(name)


def write_temp(body):
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8"
    )
    handle.write(body)
    handle.close()
    return Path(handle.name)


HEADER = (
    "| Term | POS | Meaning | Banned synonyms | Stakeholder gloss |\n"
    "|---|---|---|---|---|\n"
)

print("golden file")
result = run(SAMPLE)
check("compiler exits 0 on the sample", result.returncode == 0, result.stderr)
check(
    "output matches the golden file",
    normalize(result.stdout) == normalize(GOLDEN.read_text(encoding="utf-8")),
    "run: python3 scripts/glossary-to-vale.py scripts/tests/sample-glossary.md "
    "> scripts/tests/golden-glossary.yml",
)
check(
    "gloss-only entry is skipped",
    "Payout" not in result.stdout,
    "a term with no banned synonyms has nothing to enforce",
)

print("error paths — malformed input is named, never silent")

cases = [
    ("short row", HEADER + "| Ledger | noun | The record. | journal |\n", "expected 5"),
    ("empty term", HEADER + "|  | noun | The record. | journal | |\n", "empty Term"),
    ("missing meaning", HEADER + "| Ledger | noun |  | journal | |\n", "no meaning"),
    ("missing pos", HEADER + "| Ledger |  | The record. | journal | |\n", "no part of speech"),
    (
        "duplicate term",
        HEADER
        + "| Ledger | noun | The record. | journal | |\n"
        + "| ledger | noun | Another record. | book | |\n",
        "already defined",
    ),
    (
        "synonym claimed twice",
        HEADER
        + "| Ledger | noun | The record. | journal | |\n"
        + "| Register | noun | Another thing. | journal | |\n",
        "one synonym maps to one term",
    ),
    (
        "term bans itself",
        HEADER + "| Ledger | noun | The record. | ledger | |\n",
        "bans itself",
    ),
    ("no table", "# Glossary\n\nNothing here yet.\n", "no glossary table found"),
    (
        "wrong columns",
        "| Term | Definition |\n|---|---|\n| Ledger | The record. |\n",
        "no glossary table found",
    ),
    (
        "no banned synonyms anywhere",
        HEADER + "| Payout | noun | A transfer. |  | your money |\n",
        "nothing to enforce",
    ),
]

for name, body, expected in cases:
    path = write_temp(body)
    result = run(path)
    check(
        f"{name}: exits 1",
        result.returncode == 1,
        f"got {result.returncode}",
    )
    check(
        f"{name}: names the problem",
        expected in result.stderr,
        f"stderr was {result.stderr.strip()!r}",
    )
    path.unlink()

print()
if FAILURES:
    print(f"{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("all checks passed")
