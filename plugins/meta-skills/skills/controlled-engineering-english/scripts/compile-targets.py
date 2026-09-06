#!/usr/bin/env python3
"""Compile assets/distillation.md into every harness target.

Usage:
    python3 scripts/compile-targets.py [--check]

The distillation is the single source. Each target is that body, byte for
byte, inside a wrapper the harness understands. `--check` verifies the
targets on disk match the current distillation and exits 1 when they drift,
so a rules change that was not recompiled fails loudly.

Targets:
  assets/controlled-english.output-style.md   Claude Code output style
  assets/agents-fragment.md                   AGENTS.md fragment
  assets/system-prompt-append.md              --append-system-prompt file
  assets/subagent-prompt-block.md             paste-in block for subagents

Stdlib only.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "distillation.md"
BEGIN = "<!-- BEGIN distillation (generated from assets/distillation.md — do not edit here) -->"
END = "<!-- END distillation -->"

# Terminal-only addendum. It is NOT part of the distillation: line width is a
# property of the surface, not of the language. Every compiled target here runs
# in a terminal or an agent CLI, where the renderer will otherwise stretch prose
# to the full window width. The claude.ai path pastes assets/distillation.md
# itself and correctly gets none of this, because a browser reflows text and
# hard wraps would fight it.
#
# It sits after the END marker, so --check still compares bodies byte for byte.
ADDENDUM = """
<!-- BEGIN terminal addendum (target-specific; not part of the distillation) -->

**Wrap prose at about 80 characters.** Break the lines yourself instead of
letting the terminal run them to the full window width. Long lines are hard to
read back: the eye loses its place returning to the left margin.

Wrap paragraphs and list items only. Leave code blocks, shell commands, tables,
file paths, and URLs on their own unwrapped lines — breaking those makes them
wrong rather than merely wide.

<!-- END terminal addendum -->
"""

STYLE_FRONTMATTER = """---
name: Controlled English
description: Answer-first, one term per concept, short sentences. Reads the project glossary before writing.
keep-coding-instructions: true
---

<!--
Compiled from the controlled-engineering-english skill. Edit
assets/distillation.md and rerun scripts/compile-targets.py; edits made here
are overwritten.

keep-coding-instructions is true because this style changes how Claude
communicates while it still does engineering work.

Output styles reach the main conversation only. Subagents do not inherit
them: give a doc-writing subagent the skill, or paste
assets/subagent-prompt-block.md into its prompt.

Install (project): copy to .claude/output-styles/ and select it under /config.
Install (user):    copy to ~/.claude/output-styles/ and select it under /config.
-->

"""

AGENTS_HEADER = """<!--
Compiled from the controlled-engineering-english skill. Edit
assets/distillation.md and rerun scripts/compile-targets.py.

Paste into AGENTS.md (or the harness's memory-file equivalent). Keep project
facts in that file separately: this fragment carries voice only.
-->

"""

APPEND_HEADER = """<!--
Compiled from the controlled-engineering-english skill. Edit
assets/distillation.md and rerun scripts/compile-targets.py.

Use with:  claude --append-system-prompt "$(cat assets/system-prompt-append.md)"
or point --system-prompt-file at this file in SDK, CI, and headless runs.
-->

"""

SUBAGENT_HEADER = """<!--
Compiled from the controlled-engineering-english skill. Edit
assets/distillation.md and rerun scripts/compile-targets.py.

Output styles do not reach subagents. Paste the block below into the prompt of
any subagent that writes documents, or give that subagent the skill instead.
-->

"""

TARGETS = [
    ("controlled-english.output-style.md", STYLE_FRONTMATTER),
    ("agents-fragment.md", AGENTS_HEADER),
    ("system-prompt-append.md", APPEND_HEADER),
    ("subagent-prompt-block.md", SUBAGENT_HEADER),
]


def build(body, header):
    return f"{header}{BEGIN}\n\n{body.rstrip()}\n\n{END}\n{ADDENDUM}"


def extract(text, path):
    """Return the distillation body from a compiled target."""
    if BEGIN not in text or END not in text:
        raise ValueError(f"{path}: missing distillation markers")
    return text.split(BEGIN, 1)[1].split(END, 1)[0].strip()


def main(argv):
    body = SOURCE.read_text(encoding="utf-8")
    check_only = "--check" in argv
    drift = []

    for name, header in TARGETS:
        path = ROOT / "assets" / name
        wanted = build(body, header)

        if check_only:
            if not path.exists():
                drift.append(f"{name}: missing")
                continue
            found = path.read_text(encoding="utf-8")
            if extract(found, name) != body.strip():
                drift.append(f"{name}: body differs from the distillation")
            elif found != wanted:
                drift.append(f"{name}: wrapper differs from the compiler")
        else:
            path.write_text(wanted, encoding="utf-8")
            print(f"wrote assets/{name}")

    if check_only:
        if drift:
            for line in drift:
                print(f"drift: {line}", file=sys.stderr)
            print("rerun: python3 scripts/compile-targets.py", file=sys.stderr)
            return 1
        print(f"all {len(TARGETS)} targets match assets/distillation.md")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
