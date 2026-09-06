# Enforcement

Read this when the user asks to make reading or updating `TOOLS.md` mandatory, or when
they report that the file drifted despite the pointer line being in place.

Contents:
- [The routing decision](#the-routing-decision)
- [Portable: CI drift check](#portable-ci-drift-check)
- [Claude Code: hooks](#claude-code-hooks)
- [What not to enforce](#what-not-to-enforce)

## The routing decision

Two different rules get confused here. Separate them before choosing a mechanism.

| Rule | Mechanism | Why |
|---|---|---|
| "Read `TOOLS.md` before changing deps, scripts, or config" | Advisory pointer in the memory and rules files | Every agent honors a memory file; nothing enforces reading across Claude Code, Codex, and Cursor alike. The failure is missing information, not a skipped rule |
| "`TOOLS.md` must match the repo" | CI check, and optionally a hook | This one competes with task-completion pressure, and unlike reading it is mechanically verifiable after the fact |

So: advisory for reading, enforced for accuracy. That split keeps the portable half
portable and puts the machinery where it can actually decide something.

Escalate the reading rule only on evidence — a landed change that contradicts the file,
or a repeat of the original failure with the pointer already in place. Enforcement added
pre-emptively costs review friction on every unrelated change.

## Portable: CI drift check

`scripts/check_tools_md.py` is stdlib-only and exits 1 on drift, so it runs anywhere
Python 3 does — CI, a pre-commit hook, a Makefile target, a human's terminal. This is
the recommended enforcement because it is agent-independent: it catches drift from
human commits too, which no agent hook can.

GitHub Actions:

```yaml
- name: Check TOOLS.md is current
  run: python3 tools/check_tools_md.py .
```

pre-commit:

```yaml
- repo: local
  hooks:
    - id: tools-md-drift
      name: TOOLS.md drift check
      entry: python3 tools/check_tools_md.py .
      language: system
      pass_filenames: false
      files: '(package\.json|pyproject\.toml|.*lock.*|TOOLS\.md)$'
```

Copy the script into the target repo (`tools/check_tools_md.py` or similar) rather than
referencing a path inside the skill directory, which will not exist on CI.

Scope the CI check to pull requests that touch manifests, lockfiles, or `TOOLS.md`. A
check that fires on every commit trains people to ignore it.

## Claude Code: hooks

Only for repos whose agent work happens in Claude Code, and only in addition to the CI
check, never instead of it. A hook cannot see what a different agent or a human does.

A `PostToolUse` hook matching edits to manifests and lockfiles that runs the drift check
and surfaces its output is the useful shape: it flags the stale lines at the moment the
change is made, while the agent still has the context to fix them.

Avoid a `PreToolUse` hook that blocks dependency edits until `TOOLS.md` is read. It
blocks legitimate work, cannot verify that reading led to understanding, and produces a
bypass habit.

For matcher syntax, the exit-code and JSON output contracts, and where hook config lives,
use the `authoring-hooks` skill rather than reproducing it here.

## What not to enforce

- Reading the file. There is no portable mechanism, and a gate that only some agents honor produces inconsistent behavior that is harder to reason about than a consistent advisory.
- Contents or section order. A validator that rejects a `TOOLS.md` for structure turns a living map into a form to satisfy, which is how these files become perfunctory.
- Freshness by timestamp alone. The drift check compares against evidence in the repo; a rule like "regenerate monthly" produces churn without accuracy.
