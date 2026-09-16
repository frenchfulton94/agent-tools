# PARA File-Organizing Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a `para` plugin in the agent-tools marketplace that organizes a named directory into Tiago Forte's PARA structure through an approve-before-move workflow.

**Architecture:** Deterministic work lives in tested Python scripts (`scan`, `apply`, `undo`, plus shared `para_paths` and `para_index` modules); judgement lives in two skills. `scan.py` emits aggregated clusters rather than file rows, which keeps the inventory decisions-sized in context and is why no classifier subagent is needed. A `PreToolUse` guard hook makes the safety rules binding rather than aspirational.

**Tech Stack:** Python 3 (stdlib only — no third-party dependencies), Bun + `bun:test` for the catalog contract, Claude Code plugin manifest/skills/commands/hooks.

**Spec:** `docs/superpowers/specs/2026-09-15-para-file-organizing-plugin-design.md`

## Global Constraints

Every task's requirements implicitly include these. Values are copied verbatim from the spec.

- **Plugin identity.** `name` is `para` (install-breaking, never change), `displayName` is `PARA`, version starts at `0.1.0`. The version lives only in `plugins/para/.claude-plugin/plugin.json`; the marketplace entry carries no version field.
- **Description parity.** The `description` string must be byte-identical in `plugins/para/.claude-plugin/plugin.json` and in the `marketplace.json` entry. `bun test` gates this.
- **Python stdlib only.** No pip installs, no third-party imports. The plugin must work on a stock macOS `python3`.
- **No book content.** No chapter summaries, no glossary of the book's terms, no extended quotes. All skill prose written fresh. Forte attributed with a link, plus an explicit "independent implementation, not affiliated with or endorsed by the author" line.
- **No deletion, ever.** No script in this plugin calls `rm`, `os.remove`, `shutil.rmtree`, or `Path.unlink` on user data. Archiving is a move.
- **Never `$HOME`.** `validate_root` refuses `$HOME`, `/`, and any path at or above the user's home directory.
- **Same volume only.** Plan destinations must share `st_dev` with the root.
- **Tunable defaults.** Archive after 12 months since last use (`--archive-after`), peek budget 200 files (`--peek-files`) at 8192 bytes each (`--peek-bytes`), `--metadata-only` disables tier two.
- **Archive destination.** Age-clustered files go to `4-Archives/<year-of-last-use>`. Everything else archived goes directly to `4-Archives`. No other subfoldering is invented.
- **Skeleton rule.** Only `0-Inbox`, `1-Projects`, `2-Areas`, `3-Resources`, `4-Archives` are created up front. No subfolder is created unless files land in it.
- **Guard hook contract.** Read a `PreToolUse` payload on stdin, write a JSON `hookSpecificOutput.permissionDecision` of `allow`/`ask`/`deny` on stdout, and **always `sys.exit(0)`**. Empty stdout means allow. This matches `plugins/unraid-ops/scripts/guard_destructive_storage.py`.

### Two refinements to the spec

Both were discovered while reading the repo's actual conventions. Neither changes a decision-log row.

1. **Tests use `unittest`, not `pytest`.** Spec §10 said pytest. The repo has no pytest dependency, and the existing `plugins/unraid-ops/scripts/test/test_guard.py` is a plain script that prints a failure count and exits 0 — meaning a failure cannot gate anything. `unittest` is stdlib (so it honours the no-dependencies constraint), gives real assertions and `tmp_path`-style helpers, and returns a correct exit code so the `bun test` wrapper can actually gate it.
2. **A shared foundations module.** The spec implies path-safety logic in every script. This plan concentrates it in `plugins/para/scripts/para_paths.py`, with `PARA.md` parsing beside it in `para_index.py`, so the safety rules have one home and one test file.

---

## File Structure

    plugins/para/
      .claude-plugin/plugin.json      # manifest: name, version, description, keywords
      README.md                       # components, limits, local run, attribution
      commands/organize.md            # /para:organize entry point
      hooks/hooks.json                # PreToolUse → guard_para_moves.py
      scripts/
        para_paths.py                 # root validation, volumes, packages, globs, collisions
        para_index.py                 # PARA.md parse/render
        scan.py                       # walk → signals → peek → clusters
        apply.py                      # validate plan → skeleton → move → manifest
        undo.py                       # reverse a manifest, change-detected, idempotent
        guard_para_moves.py           # PreToolUse guard
        test/
          test_paths.py  test_index.py  test_scan.py
          test_apply.py  test_undo.py   test_guard.py
      skills/
        organizing-files-with-para/
          SKILL.md
          references/{classification-tests,macos-signals,plan-format}.md
          evals/triggers.md
        maintaining-para-systems/
          SKILL.md
          references/{upkeep,starting-over}.md
          evals/triggers.md

    tests/para-scripts.test.ts        # bun gate that runs the Python suite

Responsibilities are split so that files changing together live together: everything that decides *whether a path may be touched* is in `para_paths.py`; everything that decides *what the user's commitments are* is in `para_index.py`; the three verbs get one file each.

---

### Task 1: Registered plugin shell

Registration must come first. `tests/marketplace-integrity.test.ts` asserts that every directory under `plugins/` carrying a manifest is registered in `marketplace.json` — so creating the directory in any later task would turn the suite red until this task lands.

**Files:**
- Create: `plugins/para/.claude-plugin/plugin.json`
- Create: `plugins/para/README.md`
- Create: `plugins/para/skills/organizing-files-with-para/SKILL.md`
- Create: `plugins/para/skills/maintaining-para-systems/SKILL.md`
- Modify: `.claude-plugin/marketplace.json` (append one entry)
- Modify: `README.md` (append one table row)

**Interfaces:**
- Consumes: nothing.
- Produces: the plugin directory and both skill directory names (`organizing-files-with-para`, `maintaining-para-systems`) that every later task writes into.

- [ ] **Step 1: Run the catalog suite to confirm a green baseline**

Run: `bun test`
Expected: PASS. If it is already red, stop and fix that first — you will not be able to tell your own breakage from pre-existing breakage.

- [ ] **Step 2: Create the manifest**

Create `plugins/para/.claude-plugin/plugin.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "para",
  "displayName": "PARA",
  "version": "0.1.0",
  "description": "Organizes a directory into Tiago Forte's PARA structure — Projects, Areas, Resources, Archives — through an approve-before-move workflow: a plan grouped by decision rather than by file, classification from metadata and macOS Spotlight signals with a bounded content peek, a project list you own and correct, and an undo manifest for every move. Ships /para:organize and a guard hook that blocks deletion and unplanned moves inside a managed root.",
  "author": {
    "name": "Agent Tools",
    "email": "michael@frenchfultonjr.dev"
  },
  "license": "MIT",
  "keywords": [
    "para",
    "files",
    "organizing",
    "macos",
    "spotlight",
    "productivity",
    "second-brain"
  ]
}
```

- [ ] **Step 3: Register it in the marketplace**

Append to the `plugins` array in `.claude-plugin/marketplace.json`, after the `apple-studio` entry. The `description` must be byte-identical to the manifest's:

```json
{
  "name": "para",
  "source": "./plugins/para",
  "category": "productivity",
  "description": "Organizes a directory into Tiago Forte's PARA structure — Projects, Areas, Resources, Archives — through an approve-before-move workflow: a plan grouped by decision rather than by file, classification from metadata and macOS Spotlight signals with a bounded content peek, a project list you own and correct, and an undo manifest for every move. Ships /para:organize and a guard hook that blocks deletion and unplanned moves inside a managed root."
}
```

- [ ] **Step 4: Write both SKILL.md files**

These are brief now and expanded in Tasks 8 and 9. The frontmatter `name` must equal the directory name — `bun test` gates that.

`plugins/para/skills/organizing-files-with-para/SKILL.md`:

```markdown
---
name: organizing-files-with-para
description: Organizes a directory on disk into the PARA structure — Projects, Areas, Resources, Archives — by scanning it, proposing a project list the user corrects, and producing an approve-before-move plan grouped by decision. Use when the user wants to organize, sort, clean up, or tidy a folder, a Downloads or Documents directory, or a drive full of loose files; when they mention PARA, Tiago Forte, or applying a second brain to files; or when they describe the symptom without naming a method — "my Downloads folder is a disaster", "I can't find anything", "help me file all this". For a PARA tree that already exists and has drifted, prefer maintaining-para-systems.
license: MIT
---

# Organizing files with PARA

PARA sorts files by **how actionable they are**, not by subject: Projects (a goal
with a deadline), Areas (a standard with no end date), Resources (topics of
interest), Archives (anything from the first three that is no longer active).

This skill drives `/para:organize`. Nothing moves without an approved plan.

PARA is Tiago Forte's method, from *The PARA Method: Simplify, Organize, and
Master Your Digital Life*. This plugin is an independent implementation, not
affiliated with or endorsed by the author.
```

`plugins/para/skills/maintaining-para-systems/SKILL.md`:

```markdown
---
name: maintaining-para-systems
description: Maintains a PARA tree that already exists — sweeping 0-Inbox, archiving completed projects, detecting drift between the project list and the folders on disk, and declaring digital bankruptcy when a tree is past repair. Use when a PARA root already exists and the user asks for a weekly review, an inbox sweep, an archive pass, or says their system has gone stale, messy, or out of sync with what they are actually working on. For a directory that has not been organized yet, prefer organizing-files-with-para.
license: MIT
---

# Maintaining PARA systems

An organized tree drifts: projects finish without being archived, the inbox
fills, and `PARA.md` stops describing what you are actually working on. This
skill is the recurring pass over a root that `organizing-files-with-para`
already set up.

PARA is Tiago Forte's method, from *The PARA Method: Simplify, Organize, and
Master Your Digital Life*. This plugin is an independent implementation, not
affiliated with or endorsed by the author.
```

- [ ] **Step 5: Write the plugin README**

`bun run audit` checks plugin-level READMEs. Create `plugins/para/README.md`:

```markdown
# PARA

Organizes a directory into Tiago Forte's PARA structure — Projects, Areas,
Resources, Archives — through an approve-before-move workflow.

## What it ships

| Component | Name | Does |
|---|---|---|
| Skill | `organizing-files-with-para` | The run: scan, project list, plan, approve, apply |
| Skill | `maintaining-para-systems` | The recurring pass: inbox, archiving, drift |
| Command | `/para:organize <dir>` | Entry point for a run |
| Hook | `PreToolUse` on Bash | Blocks deletion and unplanned moves in a managed root |
| Scripts | `scan.py` `apply.py` `undo.py` | The deterministic core |

## Safety model

- Nothing moves without an approved plan.
- `$HOME` and `/` are refused as roots.
- Every move is recorded in an undo manifest before it happens.
- Deletion is not in this plugin's vocabulary. Archiving is a move.
- A never-read denylist is enforced regardless of any budget.

## Limits

- macOS signals (Spotlight, Finder tags, download provenance) are best-effort.
  Unindexed volumes fall back to portable metadata, and the scan reports how
  many files came back unindexed.
- Cross-volume destinations are rejected rather than handled.
- No deduplication, no renaming, no content edits.

## Local development

    claude --plugin-dir plugins/para
    python3 -m unittest discover -s plugins/para/scripts/test -p 'test_*.py'

## Attribution

PARA is the method of Tiago Forte, from
[*The PARA Method: Simplify, Organize, and Master Your Digital Life*](https://www.buildingasecondbrain.com/para).
This plugin is an independent implementation. It is not affiliated with or
endorsed by the author, and it ships no text from the book.
```

- [ ] **Step 6: Add the catalog README row**

Append to the "What ships" table in the repo-root `README.md`, after the `apple-studio` row. Skills are listed alphabetically, matching the other rows:

```markdown
| [para](plugins/para) | `maintaining-para-systems` `organizing-files-with-para` | Organizing a directory into PARA — Projects, Areas, Resources, Archives — with an approve-before-move plan. Ships `/para:organize`, an undo trail, and a guard hook against deletion and unplanned moves |
```

- [ ] **Step 7: Verify the catalog contract**

Run: `bun test`
Expected: PASS — registration both ways, name against directory, description parity, skill-name uniqueness, README row.

Run: `bun run audit`
Expected: exit 0.

Run: `claude plugin validate plugins/para --strict`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add plugins/para .claude-plugin/marketplace.json README.md
git commit -m "Register a para plugin shell with two skills"
```

---

### Task 2: Shared foundations — `para_paths.py` and `para_index.py`

The safety rules concentrate here, so this is the most test-worthy code in the plugin. This task also wires the Python suite into `bun test`, so every later task is gated from the moment it has tests.

**Files:**
- Create: `plugins/para/scripts/para_paths.py`
- Create: `plugins/para/scripts/para_index.py`
- Create: `plugins/para/scripts/test/test_paths.py`
- Create: `plugins/para/scripts/test/test_index.py`
- Create: `tests/para-scripts.test.ts`

**Interfaces:**
- Consumes: nothing.
- Produces, from `para_paths`:
  - `class UnsafeRoot(Exception)`
  - `validate_root(raw: str) -> pathlib.Path`
  - `volume_of(p: pathlib.Path) -> int`
  - `is_package(p: pathlib.Path) -> bool`
  - `matches_any(p: pathlib.Path, root: pathlib.Path, patterns: Sequence[str]) -> bool`
  - `safe_destination(dest: pathlib.Path) -> pathlib.Path`
  - `DEFAULT_NEVER_READ: tuple[str, ...]`, `DEFAULT_NEVER_MOVE: tuple[str, ...]`
- Produces, from `para_index`:
  - `class Index` with `.projects`, `.areas`, `.resources`, `.never_read`, `.never_move` (each `list[str]`) and `.classify(name) -> str | None` returning `"1-Projects"`, `"2-Areas"`, `"3-Resources"`, or `None`
  - `parse_index(text: str) -> Index`
  - `render_index(index: Index, root: str, updated: str) -> str`

- [ ] **Step 1: Write the failing tests for `para_paths`**

Create `plugins/para/scripts/test/test_paths.py`:

```python
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import para_paths as pp


class ValidateRoot(unittest.TestCase):
    def test_refuses_home(self):
        with self.assertRaises(pp.UnsafeRoot):
            pp.validate_root(os.path.expanduser("~"))

    def test_refuses_filesystem_root(self):
        with self.assertRaises(pp.UnsafeRoot):
            pp.validate_root("/")

    def test_refuses_a_file(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "a.txt"
            f.write_text("x")
            with self.assertRaises(pp.UnsafeRoot):
                pp.validate_root(str(f))

    def test_accepts_an_ordinary_directory(self):
        with tempfile.TemporaryDirectory() as d:
            sub = pathlib.Path(d) / "Documents"
            sub.mkdir()
            self.assertEqual(pp.validate_root(str(sub)), sub.resolve())


class Globs(unittest.TestCase):
    def test_matches_dotfile_pattern(self):
        root = pathlib.Path("/r")
        self.assertTrue(pp.matches_any(root / "x" / ".env.local", root, ["**/.env*"]))

    def test_does_not_match_unrelated(self):
        root = pathlib.Path("/r")
        self.assertFalse(pp.matches_any(root / "notes.md", root, ["**/.env*"]))


class SafeDestination(unittest.TestCase):
    def test_returns_original_when_free(self):
        with tempfile.TemporaryDirectory() as d:
            dest = pathlib.Path(d) / "a.pdf"
            self.assertEqual(pp.safe_destination(dest), dest)

    def test_appends_counter_on_collision(self):
        with tempfile.TemporaryDirectory() as d:
            dest = pathlib.Path(d) / "a.pdf"
            dest.write_text("x")
            self.assertEqual(pp.safe_destination(dest).name, "a (2).pdf")

    def test_counts_past_an_existing_counter(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "a.pdf").write_text("x")
            (pathlib.Path(d) / "a (2).pdf").write_text("x")
            self.assertEqual(
                pp.safe_destination(pathlib.Path(d) / "a.pdf").name, "a (3).pdf"
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_paths.py'`
Expected: FAIL with `ModuleNotFoundError: No module named 'para_paths'`

- [ ] **Step 3: Implement `para_paths.py`**

Create `plugins/para/scripts/para_paths.py`:

```python
#!/usr/bin/env python3
"""Path safety for the para plugin.

Everything that decides whether a path may be touched lives here, so the
rules have one home and one test file. Nothing in this module deletes.
"""

import fnmatch
import os
import pathlib

# Bundles macOS presents as single items, plus dependency trees that are one
# item by their parent. Descending into any of these would scatter them.
PACKAGE_SUFFIXES = (
    ".app", ".rtfd", ".photoslibrary", ".musiclibrary", ".bundle",
    ".framework", ".pkg", ".xcodeproj", ".xcworkspace", ".playground",
)
PACKAGE_DIRS = (".git", "node_modules", ".venv", "venv", ".tox")

DEFAULT_NEVER_READ = (
    "**/.ssh/**", "**/.gnupg/**", "**/*.pem", "**/*.key", "**/*.kdbx",
    "**/.env*", "**/Keychains/**", "**/*.keychain*",
)

DEFAULT_NEVER_MOVE = (
    "**/*.app", "**/node_modules/**", "**/.git/**", "**/Library/**",
)

SKELETON = ("0-Inbox", "1-Projects", "2-Areas", "3-Resources", "4-Archives")


class UnsafeRoot(Exception):
    """The requested root is one this plugin refuses to organize."""


def validate_root(raw):
    """Resolve a user-supplied root, refusing the ones that are never safe."""
    path = pathlib.Path(raw).expanduser().resolve()
    home = pathlib.Path.home().resolve()

    if not path.is_dir():
        raise UnsafeRoot(f"{path} is not a directory.")
    if path == pathlib.Path("/"):
        raise UnsafeRoot("Refusing to organize the filesystem root.")
    if path == home:
        raise UnsafeRoot(
            "Refusing to organize your home directory. Name a subdirectory "
            "such as ~/Documents or ~/Downloads instead."
        )
    if path in home.parents:
        raise UnsafeRoot(f"Refusing to organize {path}: it is above your home directory.")
    return path


def volume_of(path):
    """Device id, for same-volume checks. A cross-volume mv is copy+delete."""
    return os.stat(path).st_dev


def is_package(path):
    """True when the path is one item, not a directory to descend into."""
    if path.name in PACKAGE_DIRS:
        return True
    return path.is_dir() and path.suffix.lower() in PACKAGE_SUFFIXES


def matches_any(path, root, patterns):
    """Glob-match a path against patterns, testing both absolute and relative."""
    absolute = str(path)
    try:
        relative = str(path.relative_to(root))
    except ValueError:
        relative = absolute
    for pattern in patterns:
        expanded = os.path.expanduser(pattern)
        for candidate in (absolute, relative, f"/{relative}"):
            if fnmatch.fnmatch(candidate, expanded):
                return True
    return False


def safe_destination(dest):
    """Return dest, or dest with ' (n)' appended until it is free.

    APFS is case-insensitive by default, so a case-only difference is a
    collision. exists() already reflects that, which is why this is a plain
    loop rather than a directory listing comparison.
    """
    if not dest.exists():
        return dest
    stem, suffix, parent = dest.stem, dest.suffix, dest.parent
    counter = 2
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_paths.py'`
Expected: PASS, 9 tests.

- [ ] **Step 5: Write the failing tests for `para_index`**

Create `plugins/para/scripts/test/test_index.py`:

```python
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import para_index as pi

SAMPLE = """# PARA index

Root: /Users/me/Documents
Updated: 2026-09-15

## Projects
- client-redesign — ship the new marketing site — due 2026-10-15
- taxes-2025

## Areas
- finances — accounts reconciled monthly

## Resources
- photography

## Never read
- ~/.ssh
- **/*.kdbx

## Never move
- **/*.app
"""


class Parse(unittest.TestCase):
    def setUp(self):
        self.index = pi.parse_index(SAMPLE)

    def test_reads_each_section(self):
        self.assertEqual(self.index.projects, ["client-redesign", "taxes-2025"])
        self.assertEqual(self.index.areas, ["finances"])
        self.assertEqual(self.index.resources, ["photography"])

    def test_strips_description_after_em_dash(self):
        self.assertIn("client-redesign", self.index.projects)
        self.assertNotIn("ship the new marketing site", " ".join(self.index.projects))

    def test_reads_policy_sections(self):
        self.assertEqual(self.index.never_read, ["~/.ssh", "**/*.kdbx"])
        self.assertEqual(self.index.never_move, ["**/*.app"])

    def test_classify_maps_to_destinations(self):
        self.assertEqual(self.index.classify("client-redesign"), "1-Projects")
        self.assertEqual(self.index.classify("finances"), "2-Areas")
        self.assertEqual(self.index.classify("photography"), "3-Resources")
        self.assertIsNone(self.index.classify("nothing-here"))

    def test_classify_is_case_insensitive(self):
        self.assertEqual(self.index.classify("Client-Redesign"), "1-Projects")

    def test_empty_text_yields_empty_index(self):
        empty = pi.parse_index("")
        self.assertEqual(empty.projects, [])
        self.assertIsNone(empty.classify("anything"))


class Render(unittest.TestCase):
    def test_round_trips(self):
        text = pi.render_index(pi.parse_index(SAMPLE), "/Users/me/Documents", "2026-09-15")
        self.assertEqual(pi.parse_index(text).projects, ["client-redesign", "taxes-2025"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Run it to verify it fails**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_index.py'`
Expected: FAIL with `ModuleNotFoundError: No module named 'para_index'`

- [ ] **Step 7: Implement `para_index.py`**

Create `plugins/para/scripts/para_index.py`:

```python
#!/usr/bin/env python3
"""Parse and render PARA.md — the user's project list.

Parsing is deliberately forgiving: a heading plus a dash list. Text after the
first em-dash is a human description and is never parsed for meaning. An
entry's section IS its P/A/R classification, which is why the user edits
sections rather than a separate field.
"""

import re

SECTIONS = {
    "projects": "1-Projects",
    "areas": "2-Areas",
    "resources": "3-Resources",
}
POLICY = ("never read", "never move")


class Index:
    def __init__(self, projects=None, areas=None, resources=None,
                 never_read=None, never_move=None):
        self.projects = projects or []
        self.areas = areas or []
        self.resources = resources or []
        self.never_read = never_read or []
        self.never_move = never_move or []

    def classify(self, name):
        """Return the destination folder for a name, or None if unlisted."""
        needle = name.strip().casefold()
        for entries, destination in (
            (self.projects, "1-Projects"),
            (self.areas, "2-Areas"),
            (self.resources, "3-Resources"),
        ):
            for entry in entries:
                if entry.casefold() == needle:
                    return destination
        return None

    def all_names(self):
        return list(self.projects) + list(self.areas) + list(self.resources)


def _entry_name(line):
    """'- client-redesign — ship the site — due X' -> 'client-redesign'."""
    body = line.lstrip().lstrip("-").strip()
    return re.split(r"\s+—\s+", body, maxsplit=1)[0].strip()


def parse_index(text):
    buckets = {key: [] for key in list(SECTIONS) + list(POLICY)}
    current = None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip().casefold()
            continue
        if current in buckets and line.lstrip().startswith("-"):
            name = _entry_name(line)
            if name:
                buckets[current].append(name)
    return Index(
        projects=buckets["projects"],
        areas=buckets["areas"],
        resources=buckets["resources"],
        never_read=buckets["never read"],
        never_move=buckets["never move"],
    )


def render_index(index, root, updated):
    lines = ["# PARA index", "", f"Root: {root}", f"Updated: {updated}", ""]
    for title, entries in (
        ("Projects", index.projects),
        ("Areas", index.areas),
        ("Resources", index.resources),
        ("Never read", index.never_read),
        ("Never move", index.never_move),
    ):
        lines.append(f"## {title}")
        lines.extend(f"- {entry}" for entry in entries)
        lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 8: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_index.py'`
Expected: PASS, 7 tests.

- [ ] **Step 9: Gate the Python suite from `bun test`**

Create `tests/para-scripts.test.ts`. The skip path keeps the suite green where Python is absent; the exit code is what makes this a real gate, which the existing `unraid-ops` scripts do not have.

```typescript
/**
 * para-scripts.test.ts — runs the para plugin's Python suite as part of `bun test`.
 *
 * The para scripts move the user's files. Unlike the other plugin scripts in this
 * repo, whose tests are run by hand, these are gated: a red Python suite fails the
 * catalog suite. Skips cleanly when python3 is unavailable.
 */

import { describe, expect, test } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..');
const hasPython = spawnSync('python3', ['--version'], { encoding: 'utf8' }).status === 0;

describe('para python scripts', () => {
	test.skipIf(!hasPython)('unittest suite passes', () => {
		const result = spawnSync(
			'python3',
			['-m', 'unittest', 'discover', '-s', 'plugins/para/scripts/test', '-p', 'test_*.py'],
			{ cwd: ROOT, encoding: 'utf8' },
		);
		if (result.status !== 0) console.error(result.stderr || result.stdout);
		expect(result.status).toBe(0);
	});
});
```

- [ ] **Step 10: Run the full suite**

Run: `bun test`
Expected: PASS, including the new `para python scripts` case.

- [ ] **Step 11: Commit**

```bash
git add plugins/para/scripts tests/para-scripts.test.ts
git commit -m "Add para path-safety and project-list modules with a gated test suite"
```

---

### Task 3: `scan.py` tier one — walk, portable metadata, clusters

Tier one uses only portable metadata, so it is testable on any platform and is the fallback when Spotlight has nothing. Tier two lands in Task 4.

**Files:**
- Create: `plugins/para/scripts/scan.py`
- Create: `plugins/para/scripts/test/test_scan.py`

**Interfaces:**
- Consumes: `para_paths.validate_root`, `volume_of`, `is_package`, `matches_any`, `DEFAULT_NEVER_MOVE`; `para_index.Index`, `parse_index`.
- Produces:
  - `Entry` — a `dict` with keys `rel` (str), `last_used` (float, epoch seconds), `size` (int), `indexed` (bool).
  - `walk(root, index) -> tuple[list[Entry], dict]` — entries plus `{"unreadable": int, "skipped_never_move": int}`.
  - `cluster(entries, index, *, archive_after_months=12, now=None) -> list[dict]` — each cluster is `{"kind", "rule", "reason", "destination", "count", "samples", "files"}`.
  - `scan(root, **opts) -> dict` — the full document written to stdout as JSON.

- [ ] **Step 1: Write the failing tests**

Create `plugins/para/scripts/test/test_scan.py`:

```python
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import para_index as pi
import scan

DAY = 86400


def touch(path, age_days=0, content="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    when = time.time() - age_days * DAY
    os.utime(path, (when, when))
    return path


class Walk(unittest.TestCase):
    def test_treats_a_package_as_one_item(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "Thing.app" / "Contents" / "Info.plist")
            entries, _ = scan.walk(root, pi.Index())
            rels = [e["rel"] for e in entries]
            self.assertIn("Thing.app", rels)
            self.assertNotIn("Thing.app/Contents/Info.plist", rels)

    def test_skips_never_move_entries(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "keep.txt")
            touch(root / "node_modules" / "dep" / "index.js")
            entries, stats = scan.walk(root, pi.Index())
            self.assertEqual([e["rel"] for e in entries], ["keep.txt"])
            self.assertEqual(stats["skipped_never_move"], 1)

    def test_does_not_descend_into_the_skeleton(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "4-Archives" / "old.pdf")
            touch(root / "loose.pdf")
            entries, _ = scan.walk(root, pi.Index())
            self.assertEqual([e["rel"] for e in entries], ["loose.pdf"])


class Cluster(unittest.TestCase):
    def test_groups_old_files_by_year_of_last_use(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "old.pdf", age_days=800)
            touch(root / "fresh.pdf", age_days=3)
            entries, _ = scan.walk(root, pi.Index())
            clusters = scan.cluster(entries, pi.Index(), archive_after_months=12)
            age = [c for c in clusters if c["kind"] == "age"]
            self.assertEqual(len(age), 1)
            self.assertEqual(age[0]["files"], ["old.pdf"])
            self.assertTrue(age[0]["destination"].startswith("4-Archives/"))

    def test_matches_a_project_by_name(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "client-redesign-brief.docx", age_days=2)
            index = pi.Index(projects=["client-redesign"])
            entries, _ = scan.walk(root, index)
            clusters = scan.cluster(entries, index)
            match = [c for c in clusters if c["kind"] == "project-match"]
            self.assertEqual(match[0]["destination"], "1-Projects/client-redesign")

    def test_project_match_beats_age(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "client-redesign-old.docx", age_days=800)
            index = pi.Index(projects=["client-redesign"])
            entries, _ = scan.walk(root, index)
            clusters = scan.cluster(entries, index, archive_after_months=12)
            kinds = {c["kind"] for c in clusters}
            self.assertIn("project-match", kinds)
            self.assertNotIn("age", kinds)

    def test_unmatched_recent_files_go_to_inbox(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "mystery.bin", age_days=1)
            entries, _ = scan.walk(root, pi.Index())
            clusters = scan.cluster(entries, pi.Index())
            unresolved = [c for c in clusters if c["kind"] == "unresolved"]
            self.assertEqual(unresolved[0]["destination"], "0-Inbox")

    def test_every_file_lands_in_exactly_one_cluster(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "client-redesign.docx", age_days=2)
            touch(root / "old.pdf", age_days=900)
            touch(root / "mystery.bin", age_days=1)
            index = pi.Index(projects=["client-redesign"])
            entries, _ = scan.walk(root, index)
            clusters = scan.cluster(entries, index)
            placed = [f for c in clusters for f in c["files"]]
            self.assertEqual(sorted(placed), sorted(e["rel"] for e in entries))
            self.assertEqual(len(placed), len(set(placed)))

    def test_samples_are_capped_but_counts_are_not(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            for i in range(30):
                touch(root / f"old{i}.pdf", age_days=900)
            entries, _ = scan.walk(root, pi.Index())
            age = [c for c in scan.cluster(entries, pi.Index()) if c["kind"] == "age"][0]
            self.assertEqual(age["count"], 30)
            self.assertLessEqual(len(age["samples"]), 5)


class Cli(unittest.TestCase):
    def test_emits_json_and_refuses_home(self):
        script = str(pathlib.Path(__file__).resolve().parents[1] / "scan.py")
        with tempfile.TemporaryDirectory() as d:
            touch(pathlib.Path(d) / "a.txt")
            ok = subprocess.run([sys.executable, script, d], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0)
            self.assertEqual(json.loads(ok.stdout)["version"], 1)

        refused = subprocess.run(
            [sys.executable, script, os.path.expanduser("~")],
            capture_output=True, text=True,
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("home directory", refused.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_scan.py'`
Expected: FAIL with `ModuleNotFoundError: No module named 'scan'`

- [ ] **Step 3: Implement `scan.py` tier one**

Create `plugins/para/scripts/scan.py`:

```python
#!/usr/bin/env python3
"""Scan a directory and emit aggregated clusters.

Clusters, not rows: counts and samples are what reach the agent's context, so
review cost scales with decisions rather than file count. That is also why the
plugin needs no classifier subagent.

Tier one (this module's walk and cluster) uses portable metadata only. Tier two
adds macOS signals and a bounded content peek.
"""

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

import para_paths as pp
from para_index import Index, parse_index

SAMPLE_CAP = 5
MONTH_SECONDS = 30.44 * 86400


def _tokens(rel):
    """Lowercase word-ish tokens from a relative path, for name matching."""
    return set(re.split(r"[^a-z0-9]+", rel.casefold())) - {""}


def walk(root, index):
    """Collect entries beneath root. Packages are single items."""
    entries = []
    stats = {"unreadable": 0, "skipped_never_move": 0}
    never_move = tuple(pp.DEFAULT_NEVER_MOVE) + tuple(index.never_move)

    def visit(directory):
        try:
            children = sorted(directory.iterdir())
        except (PermissionError, OSError):
            stats["unreadable"] += 1
            return
        for child in children:
            if child.is_symlink():
                record(child)
                continue
            if pp.is_package(child):
                record(child)
                continue
            if child.is_dir():
                visit(child)
            else:
                record(child)

    def record(path):
        if pp.matches_any(path, root, never_move):
            stats["skipped_never_move"] += 1
            return
        try:
            info = path.lstat()
        except OSError:
            stats["unreadable"] += 1
            return
        entries.append({
            "rel": str(path.relative_to(root)),
            "last_used": info.st_mtime,
            "size": info.st_size,
            "indexed": False,
        })

    for child in sorted(root.iterdir()):
        # The skeleton is output, not input. A re-run works 0-Inbox only, which
        # the maintaining-para-systems skill drives.
        if child.name in pp.SKELETON:
            continue
        if child.is_symlink() or pp.is_package(child) or not child.is_dir():
            record(child)
        else:
            visit(child)
    return entries, stats


def _make(kind, rule, reason, destination, files):
    return {
        "kind": kind,
        "rule": rule,
        "reason": reason,
        "destination": destination,
        "count": len(files),
        "samples": files[:SAMPLE_CAP],
        "files": files,
    }


def cluster(entries, index, *, archive_after_months=12, now=None):
    """Assign every entry to exactly one cluster, highest precedence first."""
    now = now if now is not None else dt.datetime.now().timestamp()
    cutoff = now - archive_after_months * MONTH_SECONDS
    remaining = {e["rel"]: e for e in entries}
    clusters = []

    # 1. Name matches against the user's confirmed commitments.
    for name in index.all_names():
        destination = index.classify(name)
        wanted = set(re.split(r"[^a-z0-9]+", name.casefold())) - {""}
        if not wanted:
            continue
        hits = sorted(
            rel for rel in remaining if wanted <= _tokens(rel)
        )
        if hits:
            kind = {"1-Projects": "project-match", "2-Areas": "area-match"}.get(
                destination, "resource-match"
            )
            clusters.append(_make(
                kind,
                f'path mentions "{name}"',
                f'matches "{name}" in PARA.md',
                f"{destination}/{name}",
                hits,
            ))
            for rel in hits:
                del remaining[rel]

    # 2. Age, bucketed by year of last use.
    by_year = {}
    for rel, entry in list(remaining.items()):
        if entry["last_used"] < cutoff:
            year = dt.datetime.fromtimestamp(entry["last_used"]).year
            by_year.setdefault(year, []).append(rel)
            del remaining[rel]
    for year, files in sorted(by_year.items()):
        clusters.append(_make(
            "age",
            f"last used before {archive_after_months} months ago",
            f"{len(files)} files last used in {year}",
            f"4-Archives/{year}",
            sorted(files),
        ))

    # 3. Whatever is left. 0-Inbox is a correct answer, not a failure.
    if remaining:
        clusters.append(_make(
            "unresolved",
            "no match in PARA.md and recently used",
            "needs a human decision",
            "0-Inbox",
            sorted(remaining),
        ))
    return clusters


def scan(root, *, archive_after_months=12, metadata_only=False, para=None):
    index = parse_index(para) if para else Index()
    entries, stats = walk(root, index)
    clusters = cluster(entries, index, archive_after_months=archive_after_months)
    return {
        "version": 1,
        "root": str(root),
        "volume": pp.volume_of(root),
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "metadata_only": metadata_only,
        "peeked": [],
        "unindexed": sum(1 for e in entries if not e["indexed"]),
        "unreadable": stats["unreadable"],
        "skipped_never_move": stats["skipped_never_move"],
        "clusters": clusters,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan a directory into PARA clusters.")
    parser.add_argument("root")
    parser.add_argument("--archive-after", type=int, default=12, metavar="MONTHS")
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()

    try:
        root = pp.validate_root(args.root)
    except pp.UnsafeRoot as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)

    index_file = root / "PARA.md"
    para = index_file.read_text(encoding="utf-8") if index_file.exists() else None
    json.dump(
        scan(root, archive_after_months=args.archive_after,
             metadata_only=args.metadata_only, para=para),
        sys.stdout, indent=2,
    )
    print()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_scan.py'`
Expected: PASS, 10 tests.

- [ ] **Step 5: Run the whole suite and commit**

Run: `bun test`
Expected: PASS.

```bash
git add plugins/para/scripts/scan.py plugins/para/scripts/test/test_scan.py
git commit -m "Add para scan tier one: walk, portable metadata, clustering"
```

---

### Task 4: `scan.py` tier two — macOS signals and the budgeted peek

A reviewer could accept tier one and reject this layer, which is why it is its own task. Everything here is best-effort and degrades to tier one.

**Files:**
- Modify: `plugins/para/scripts/scan.py`
- Modify: `plugins/para/scripts/test/test_scan.py`

**Interfaces:**
- Consumes: everything from Task 3.
- Produces:
  - `spotlight(path) -> dict` — `{"last_used": float|None, "tags": list[str], "where_from": list[str], "indexed": bool}`
  - `peek(path, limit_bytes) -> str` — decoded prefix, `""` when unreadable or binary.
  - `walk` gains a `metadata_only` keyword; `scan` gains `peek_files` and `peek_bytes`.

- [ ] **Step 1: Write the failing tests**

Append to `plugins/para/scripts/test/test_scan.py`, above the `if __name__` block:

```python
class TierTwo(unittest.TestCase):
    def test_peek_reads_a_bounded_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            f = touch(pathlib.Path(d) / "notes.txt", content="client-redesign " * 500)
            self.assertLessEqual(len(scan.peek(f, 64).encode("utf-8")), 64)

    def test_peek_returns_empty_on_binary(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "blob.bin"
            f.write_bytes(b"\x00\x01\x02\xff" * 64)
            self.assertEqual(scan.peek(f, 128), "")

    def test_denylist_is_enforced_regardless_of_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            secret = touch(root / ".env.local", content="TOKEN=abc")
            index = pi.Index(never_read=["**/.env*"])
            opened = scan.peek_candidates([{"rel": ".env.local"}], root, index,
                                          peek_files=100)
            self.assertEqual(opened, [])
            self.assertTrue(secret.exists())

    def test_peek_budget_caps_file_count(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            entries = []
            for i in range(10):
                touch(root / f"f{i}.txt")
                entries.append({"rel": f"f{i}.txt"})
            opened = scan.peek_candidates(entries, root, pi.Index(), peek_files=3)
            self.assertEqual(len(opened), 3)

    def test_metadata_only_peeks_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            touch(root / "mystery.txt", content="client-redesign notes")
            result = scan.scan(root, metadata_only=True)
            self.assertEqual(result["peeked"], [])

    def test_spotlight_degrades_without_raising(self):
        with tempfile.TemporaryDirectory() as d:
            f = touch(pathlib.Path(d) / "a.txt")
            signals = scan.spotlight(f)
            self.assertIn("indexed", signals)
            self.assertIsInstance(signals["tags"], list)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_scan.py' -k TierTwo`
Expected: FAIL with `AttributeError: module 'scan' has no attribute 'peek'`

- [ ] **Step 3: Add the signal and peek layer**

Add to `plugins/para/scripts/scan.py`, after the `_tokens` helper:

```python
import plistlib
import subprocess

MDLS_KEYS = (
    "kMDItemLastUsedDate", "kMDItemUserTags",
    "kMDItemWhereFroms", "kMDItemContentTypeTree",
)


def spotlight(path):
    """Best-effort macOS metadata. Every field may be absent.

    Spotlight indexing is off on many external and network volumes, so this
    reports `indexed` and the caller falls back to portable metadata.
    """
    blank = {"last_used": None, "tags": [], "where_from": [], "indexed": False}
    try:
        result = subprocess.run(
            ["mdls", "-plist", "-", str(path)],
            capture_output=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return blank
    if result.returncode != 0 or not result.stdout:
        return blank
    try:
        data = plistlib.loads(result.stdout)
    except Exception:
        return blank
    if not isinstance(data, dict):
        return blank

    used = data.get("kMDItemLastUsedDate")
    return {
        "last_used": used.timestamp() if hasattr(used, "timestamp") else None,
        "tags": [str(t) for t in (data.get("kMDItemUserTags") or [])],
        "where_from": [str(w) for w in (data.get("kMDItemWhereFroms") or [])],
        "indexed": any(data.get(key) is not None for key in MDLS_KEYS),
    }


def peek(path, limit_bytes):
    """Decode a bounded prefix. Returns '' for binary or unreadable files."""
    try:
        with open(path, "rb") as handle:
            chunk = handle.read(limit_bytes)
    except OSError:
        return ""
    if b"\x00" in chunk:
        return ""
    return chunk.decode("utf-8", errors="replace")


def peek_candidates(entries, root, index, *, peek_files=200):
    """Relative paths eligible for a content read, denylist first, then budget.

    The denylist is checked before the budget, so a never-read path can never
    be opened by raising the budget.
    """
    never_read = tuple(pp.DEFAULT_NEVER_READ) + tuple(index.never_read)
    eligible = []
    for entry in entries:
        candidate = root / entry["rel"]
        if pp.matches_any(candidate, root, never_read):
            continue
        eligible.append(entry["rel"])
        if len(eligible) >= peek_files:
            break
    return eligible
```

- [ ] **Step 4: Wire the signals into `walk` and the peek into `scan`**

In `walk`, replace the `entries.append({...})` block inside `record` with:

```python
        signals = {"last_used": None, "tags": [], "where_from": [], "indexed": False}
        if not metadata_only:
            signals = spotlight(path)
        entries.append({
            "rel": str(path.relative_to(root)),
            # Last-used beats mtime: mtime churns on sync, copy, and restore.
            "last_used": signals["last_used"] or info.st_mtime,
            "size": info.st_size,
            "indexed": signals["indexed"],
            "tags": signals["tags"],
            "where_from": signals["where_from"],
        })
```

Change the `walk` signature to `def walk(root, index, *, metadata_only=False):`, and in `scan` replace the body with:

```python
def scan(root, *, archive_after_months=12, metadata_only=False,
         peek_files=200, peek_bytes=8192, para=None):
    index = parse_index(para) if para else Index()
    entries, stats = walk(root, index, metadata_only=metadata_only)
    clusters = cluster(entries, index, archive_after_months=archive_after_months)

    peeked = []
    if not metadata_only:
        unresolved = [c for c in clusters if c["kind"] == "unresolved"]
        if unresolved:
            pending = [{"rel": rel} for rel in unresolved[0]["files"]]
            for rel in peek_candidates(pending, root, index, peek_files=peek_files):
                text = peek(root / rel, peek_bytes)
                if not text:
                    continue
                peeked.append(rel)
                for name in index.all_names():
                    if name.casefold() in text.casefold():
                        unresolved[0].setdefault("peek_hints", {})[rel] = name
                        break

    return {
        "version": 1,
        "root": str(root),
        "volume": pp.volume_of(root),
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "metadata_only": metadata_only,
        "peeked": peeked,
        "unindexed": sum(1 for e in entries if not e["indexed"]),
        "unreadable": stats["unreadable"],
        "skipped_never_move": stats["skipped_never_move"],
        "clusters": clusters,
    }
```

Add the two flags to `main`'s parser and pass them through:

```python
    parser.add_argument("--peek-files", type=int, default=200)
    parser.add_argument("--peek-bytes", type=int, default=8192)
```

```python
        scan(root, archive_after_months=args.archive_after,
             metadata_only=args.metadata_only, peek_files=args.peek_files,
             peek_bytes=args.peek_bytes, para=para),
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_scan.py'`
Expected: PASS, 16 tests.

- [ ] **Step 6: Commit**

```bash
git add plugins/para/scripts/scan.py plugins/para/scripts/test/test_scan.py
git commit -m "Add para scan tier two: Spotlight signals and a budgeted peek"
```

---

### Task 5: `apply.py` — validate, skeleton, move, manifest

**Files:**
- Create: `plugins/para/scripts/apply.py`
- Create: `plugins/para/scripts/test/test_apply.py`

**Interfaces:**
- Consumes: `para_paths.validate_root`, `volume_of`, `safe_destination`, `SKELETON`.
- Produces:
  - `validate_plan(plan, root) -> list[str]` — error strings; empty means valid.
  - `apply_plan(plan, root) -> dict` — `{"moved": int, "skipped": list, "manifest": str}`.
  - Manifest at `.para/undo-<ts>.jsonl`, one object per line: `{"from","to","size","mtime_ns","inode"}`.

- [ ] **Step 1: Write the failing tests**

Create `plugins/para/scripts/test/test_apply.py`:

```python
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import apply as ap


def plan_with(groups, root):
    return {"version": 1, "root": str(root), "groups": groups}


def group(files, destination, gid="g1"):
    return {
        "id": gid, "rule": "r", "reason": "why", "destination": destination,
        "count": len(files), "samples": files[:5], "files": files,
    }


class Validate(unittest.TestCase):
    def test_rejects_a_missing_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            errors = ap.validate_plan(plan_with([group(["ghost.pdf"], "0-Inbox")], root), root)
            self.assertTrue(any("ghost.pdf" in e for e in errors))

    def test_rejects_a_file_claimed_by_two_groups(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("x")
            plan = plan_with(
                [group(["a.pdf"], "0-Inbox", "g1"), group(["a.pdf"], "4-Archives", "g2")],
                root,
            )
            self.assertTrue(any("claimed by two" in e for e in ap.validate_plan(plan, root)))

    def test_rejects_an_escaping_destination(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("x")
            plan = plan_with([group(["a.pdf"], "../outside")], root)
            self.assertTrue(any("outside the root" in e for e in ap.validate_plan(plan, root)))

    def test_accepts_a_sound_plan(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("x")
            self.assertEqual(ap.validate_plan(plan_with([group(["a.pdf"], "0-Inbox")], root), root), [])


class Apply(unittest.TestCase):
    def test_moves_files_and_writes_a_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("hello")
            result = ap.apply_plan(plan_with([group(["a.pdf"], "4-Archives/2024")], root), root)
            self.assertEqual(result["moved"], 1)
            self.assertFalse((root / "a.pdf").exists())
            self.assertEqual((root / "4-Archives" / "2024" / "a.pdf").read_text(), "hello")
            lines = pathlib.Path(result["manifest"]).read_text().strip().splitlines()
            self.assertEqual(json.loads(lines[0])["to"], "4-Archives/2024/a.pdf")

    def test_creates_the_skeleton_but_no_empty_subfolders(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("x")
            ap.apply_plan(plan_with([group(["a.pdf"], "0-Inbox")], root), root)
            for name in ("0-Inbox", "1-Projects", "2-Areas", "3-Resources", "4-Archives"):
                self.assertTrue((root / name).is_dir())
            self.assertEqual(list((root / "1-Projects").iterdir()), [])

    def test_renames_on_collision_and_records_the_real_destination(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("new")
            (root / "4-Archives").mkdir()
            (root / "4-Archives" / "a.pdf").write_text("existing")
            result = ap.apply_plan(plan_with([group(["a.pdf"], "4-Archives")], root), root)
            self.assertEqual((root / "4-Archives" / "a.pdf").read_text(), "existing")
            self.assertEqual((root / "4-Archives" / "a (2).pdf").read_text(), "new")
            entry = json.loads(pathlib.Path(result["manifest"]).read_text().strip())
            self.assertEqual(entry["to"], "4-Archives/a (2).pdf")

    def test_refuses_an_invalid_plan_whole(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("x")
            plan = plan_with([group(["a.pdf", "ghost.pdf"], "0-Inbox")], root)
            with self.assertRaises(ap.InvalidPlan):
                ap.apply_plan(plan, root)
            self.assertTrue((root / "a.pdf").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_apply.py'`
Expected: FAIL with `ModuleNotFoundError: No module named 'apply'`

- [ ] **Step 3: Implement `apply.py`**

Create `plugins/para/scripts/apply.py`:

```python
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
import pathlib
import shutil
import sys

import para_paths as pp


class InvalidPlan(Exception):
    """The plan failed validation and was not applied."""


def _resolve_destination(root, destination, name):
    target = (root / destination / name).resolve()
    if root not in target.parents and target != root:
        return None
    return target


def validate_plan(plan, root):
    """Return a list of error strings. Empty means the plan is sound."""
    errors = []
    seen = {}
    root_volume = pp.volume_of(root)

    for group in plan.get("groups", []):
        destination = group.get("destination", "")
        for rel in group.get("files", []):
            source = root / rel
            if not source.exists() and not source.is_symlink():
                errors.append(f"{rel}: source no longer exists")
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

    moved, skipped = 0, []
    with open(manifest, "a", encoding="utf-8") as log:
        for group in plan.get("groups", []):
            for rel in group.get("files", []):
                source = root / rel
                target_dir = root / group["destination"]
                target_dir.mkdir(parents=True, exist_ok=True)
                target = pp.safe_destination(target_dir / source.name)
                try:
                    info = source.lstat()
                except OSError:
                    skipped.append({"file": rel, "reason": "unreadable"})
                    continue

                # Written before the move: an interrupted run stays reversible.
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
    print(f"\nReverse this run with:\n  python3 undo.py {result['manifest']}", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_apply.py'`
Expected: PASS, 9 tests.

- [ ] **Step 5: Commit**

```bash
git add plugins/para/scripts/apply.py plugins/para/scripts/test/test_apply.py
git commit -m "Add para apply: whole-plan validation, skeleton, moves, manifest"
```

---

### Task 6: `undo.py` — reverse a manifest, change-detected and idempotent

**Files:**
- Create: `plugins/para/scripts/undo.py`
- Create: `plugins/para/scripts/test/test_undo.py`

**Interfaces:**
- Consumes: `para_paths.validate_root`, `safe_destination`.
- Produces: `undo(manifest_path, root) -> dict` — `{"restored": int, "skipped": list[dict]}`, each skip carrying `{"file", "reason"}`.

- [ ] **Step 1: Write the failing tests**

Create `plugins/para/scripts/test/test_undo.py`:

```python
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import apply as ap
import undo as un


def moved_fixture(root, content="hello"):
    (root / "a.pdf").write_text(content)
    plan = {
        "version": 1, "root": str(root),
        "groups": [{
            "id": "g1", "rule": "r", "reason": "why",
            "destination": "4-Archives/2024", "count": 1,
            "samples": ["a.pdf"], "files": ["a.pdf"],
        }],
    }
    return ap.apply_plan(plan, root)["manifest"]


class Undo(unittest.TestCase):
    def test_restores_a_moved_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            manifest = moved_fixture(root)
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 1)
            self.assertEqual((root / "a.pdf").read_text(), "hello")

    def test_refuses_a_file_modified_since_the_move(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            manifest = moved_fixture(root)
            (root / "4-Archives" / "2024" / "a.pdf").write_text("edited since")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 0)
            self.assertEqual(result["skipped"][0]["reason"], "modified since the move")
            self.assertFalse((root / "a.pdf").exists())

    def test_continues_past_a_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "a.pdf").write_text("one")
            (root / "b.pdf").write_text("two")
            plan = {
                "version": 1, "root": str(root),
                "groups": [{
                    "id": "g1", "rule": "r", "reason": "w",
                    "destination": "4-Archives", "count": 2,
                    "samples": [], "files": ["a.pdf", "b.pdf"],
                }],
            }
            manifest = ap.apply_plan(plan, root)["manifest"]
            (root / "4-Archives" / "a.pdf").write_text("changed")
            result = un.undo(manifest, root)
            self.assertEqual(result["restored"], 1)
            self.assertEqual(len(result["skipped"]), 1)
            self.assertEqual((root / "b.pdf").read_text(), "two")

    def test_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            manifest = moved_fixture(root)
            un.undo(manifest, root)
            second = un.undo(manifest, root)
            self.assertEqual(second["restored"], 0)
            self.assertEqual(second["skipped"][0]["reason"], "already restored")
            self.assertEqual((root / "a.pdf").read_text(), "hello")

    def test_restores_under_a_new_name_when_the_origin_is_occupied(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            manifest = moved_fixture(root)
            (root / "a.pdf").write_text("something new here")
            un.undo(manifest, root)
            self.assertEqual((root / "a.pdf").read_text(), "something new here")
            self.assertEqual((root / "a (2).pdf").read_text(), "hello")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_undo.py'`
Expected: FAIL with `ModuleNotFoundError: No module named 'undo'`

- [ ] **Step 3: Implement `undo.py`**

Create `plugins/para/scripts/undo.py`:

```python
#!/usr/bin/env python3
"""Reverse an apply run from its manifest.

Per-file refusal, never whole-run abort: a file edited since the move is
reported and skipped while the rest proceed. Re-running a reversed manifest is
a no-op, not an error.

The change detector is size + mtime_ns + inode. A content hash would cost a
full read of every large file and adds nothing over the triple for spotting a
post-move edit.
"""

import argparse
import json
import pathlib
import shutil
import sys

import para_paths as pp


def undo(manifest_path, root):
    restored, skipped = 0, []
    lines = pathlib.Path(manifest_path).read_text(encoding="utf-8").splitlines()

    # Reverse order, so nested destinations unwind before their parents.
    for line in reversed(lines):
        if not line.strip():
            continue
        record = json.loads(line)
        current = root / record["to"]
        origin = root / record["from"]

        if not current.exists() and not current.is_symlink():
            skipped.append({"file": record["to"], "reason": "already restored"})
            continue

        info = current.lstat()
        unchanged = (
            info.st_size == record["size"]
            and info.st_mtime_ns == record["mtime_ns"]
            and info.st_ino == record["inode"]
        )
        if not unchanged:
            skipped.append({"file": record["to"], "reason": "modified since the move"})
            continue

        origin.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(current), str(pp.safe_destination(origin)))
        restored += 1

    return {"restored": restored, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(description="Reverse a PARA apply run.")
    parser.add_argument("manifest")
    parser.add_argument("--root", default=None,
                        help="Defaults to the grandparent of the manifest (<root>/.para/).")
    args = parser.parse_args()

    manifest = pathlib.Path(args.manifest).resolve()
    raw_root = args.root or str(manifest.parent.parent)
    try:
        root = pp.validate_root(raw_root)
    except pp.UnsafeRoot as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)

    result = undo(manifest, root)
    print(json.dumps(result, indent=2))
    for entry in result["skipped"]:
        print(f"skipped {entry['file']}: {entry['reason']}", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_undo.py'`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add plugins/para/scripts/undo.py plugins/para/scripts/test/test_undo.py
git commit -m "Add para undo: change-detected, per-file refusal, idempotent"
```

---

### Task 7: The guard hook

This is the component that makes the safety model binding rather than aspirational. The registry scoping is a deliberate trade — see spec §8.

**Files:**
- Create: `plugins/para/scripts/guard_para_moves.py`
- Create: `plugins/para/scripts/test/test_guard.py`
- Create: `plugins/para/hooks/hooks.json`
- Modify: `plugins/para/scripts/apply.py` (register the root on success)

**Interfaces:**
- Consumes: nothing from earlier tasks (the guard must stay dependency-free so it cannot fail to load).
- Produces: `registered_roots(path=None) -> list[str]`, `evaluate(command, roots) -> tuple[str, str] | None`, and the registry file at `~/.config/para/roots`.

- [ ] **Step 1: Write the failing tests**

Create `plugins/para/scripts/test/test_guard.py`:

```python
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import guard_para_moves as guard

SCRIPT = str(pathlib.Path(__file__).resolve().parents[1] / "guard_para_moves.py")
ROOTS = ["/Users/me/Documents"]


class Evaluate(unittest.TestCase):
    def test_denies_rm_inside_a_registered_root(self):
        verdict = guard.evaluate("rm -rf /Users/me/Documents/4-Archives/old", ROOTS)
        self.assertEqual(verdict[0], "deny")

    def test_denies_bare_mv_inside_a_registered_root(self):
        verdict = guard.evaluate("mv /Users/me/Documents/a.pdf /Users/me/Documents/b.pdf", ROOTS)
        self.assertEqual(verdict[0], "deny")

    def test_allows_mv_through_apply(self):
        self.assertIsNone(guard.evaluate("python3 apply.py /Users/me/Documents/.para/plan.json", ROOTS))

    def test_allows_rm_outside_every_registered_root(self):
        self.assertIsNone(guard.evaluate("rm -rf /tmp/scratch/build", ROOTS))

    def test_allows_reads_inside_a_registered_root(self):
        self.assertIsNone(guard.evaluate("ls -la /Users/me/Documents", ROOTS))
        self.assertIsNone(guard.evaluate("grep -r todo /Users/me/Documents", ROOTS))

    def test_judges_each_segment_independently(self):
        verdict = guard.evaluate("ls /tmp && rm -rf /Users/me/Documents/x", ROOTS)
        self.assertEqual(verdict[0], "deny")

    def test_no_registry_means_no_opinion(self):
        self.assertIsNone(guard.evaluate("rm -rf /Users/me/Documents/x", []))


class Cli(unittest.TestCase):
    def _run(self, payload, roots_file):
        return subprocess.run(
            [sys.executable, SCRIPT],
            input=json.dumps(payload), capture_output=True, text=True,
            env={"PARA_ROOTS_FILE": roots_file, "PATH": "/usr/bin:/bin"},
        )

    def test_exits_zero_and_denies_via_json(self):
        with tempfile.TemporaryDirectory() as d:
            roots_file = str(pathlib.Path(d) / "roots")
            pathlib.Path(roots_file).write_text("/Users/me/Documents\n")
            result = self._run(
                {"tool_name": "Bash", "tool_input": {"command": "rm -rf /Users/me/Documents/x"}},
                roots_file,
            )
            self.assertEqual(result.returncode, 0)
            decision = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]
            self.assertEqual(decision, "deny")

    def test_stays_silent_for_non_bash_tools(self):
        with tempfile.TemporaryDirectory() as d:
            roots_file = str(pathlib.Path(d) / "roots")
            pathlib.Path(roots_file).write_text("/Users/me/Documents\n")
            result = self._run({"tool_name": "Read", "tool_input": {}}, roots_file)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_survives_a_malformed_payload(self):
        with tempfile.TemporaryDirectory() as d:
            roots_file = str(pathlib.Path(d) / "roots")
            result = subprocess.run(
                [sys.executable, SCRIPT], input="not json",
                capture_output=True, text=True,
                env={"PARA_ROOTS_FILE": roots_file, "PATH": "/usr/bin:/bin"},
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_guard.py'`
Expected: FAIL with `ModuleNotFoundError: No module named 'guard_para_moves'`

- [ ] **Step 3: Implement the guard**

Create `plugins/para/scripts/guard_para_moves.py`:

```python
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
"""

import json
import os
import pathlib
import re
import sys

DESTRUCTIVE = ("rm", "rmdir", "unlink", "shred", "trash")
RELOCATING = ("mv", "rename")
APPLY_MARKER = "apply.py"


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
    stripped = segment.strip()
    while re.match(r"^\w+=\S*\s+", stripped):
        stripped = re.sub(r"^\w+=\S*\s+", "", stripped)
    match = re.match(r"^([\w./-]+)", stripped)
    return match.group(1).split("/")[-1] if match else ""


def touches_root(segment, roots):
    for root in roots:
        if root in segment:
            return root
    return None


def evaluate(command, roots):
    """Return (decision, reason), or None when the guard has no opinion."""
    if not roots:
        return None

    for segment in segments(command):
        if APPLY_MARKER in segment:
            continue
        root = touches_root(segment, roots)
        if not root:
            continue
        lead = leading_word(segment)

        if lead in DESTRUCTIVE:
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_guard.py'`
Expected: PASS, 10 tests.

- [ ] **Step 5: Register the hook**

Create `plugins/para/hooks/hooks.json`:

```json
{
  "description": "Blocks deletion and unplanned moves inside a PARA root that apply.py has registered.",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3",
            "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/guard_para_moves.py"],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Have `apply.py` register the root**

Add to `plugins/para/scripts/apply.py`, after the imports:

```python
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
        registry.write_text("\n".join(existing) + "\n", encoding="utf-8")
```

Add `import os` to the imports, and call `register_root(root)` in `apply_plan` immediately after the skeleton-creation loop.

- [ ] **Step 7: Run the whole suite**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_*.py'`
Expected: PASS, all tests.

Run: `bun test && bun run audit`
Expected: PASS, exit 0.

- [ ] **Step 8: Commit**

```bash
git add plugins/para/scripts plugins/para/hooks
git commit -m "Add the para guard hook and register roots on apply"
```

---

### Task 8: The command and the organizing skill

With the scripts' real interfaces settled, the orchestration prose can name exact commands and exact file paths.

**Files:**
- Create: `plugins/para/commands/organize.md`
- Modify: `plugins/para/skills/organizing-files-with-para/SKILL.md`
- Create: `plugins/para/skills/organizing-files-with-para/references/classification-tests.md`
- Create: `plugins/para/skills/organizing-files-with-para/references/macos-signals.md`
- Create: `plugins/para/skills/organizing-files-with-para/references/plan-format.md`
- Create: `plugins/para/skills/organizing-files-with-para/evals/triggers.md`

**Interfaces:**
- Consumes: the CLI surface of `scan.py`, `apply.py`, `undo.py` as defined in Tasks 3–6.
- Produces: the seven-step run contract the maintaining skill defers to.

- [ ] **Step 1: Write the command**

Create `plugins/para/commands/organize.md`:

```markdown
---
description: Organize a directory into the PARA structure, with an approve-before-move plan
argument-hint: [directory, e.g. ~/Downloads]
---

Organize this directory into PARA: **$ARGUMENTS**

Use the `organizing-files-with-para` skill and follow its seven-step run. The
ordering matters: steps 1 and 2 are read-only, and step 6 is the only one that
moves anything.

Do not move a single file before the user has approved the rendered plan. If
the user asks you to "just do it", still render the plan first — it is the
artifact the approval is about, and producing it costs one scan.

If no directory was given, ask for one. Never default to the home directory:
`$HOME` is refused by design.
```

- [ ] **Step 2: Expand the skill**

Replace the body of `plugins/para/skills/organizing-files-with-para/SKILL.md` below the frontmatter (keep the frontmatter from Task 1 exactly as written):

```markdown
# Organizing files with PARA

PARA sorts files by **how actionable they are**, not by subject:

| Folder | Holds | Test |
|---|---|---|
| `0-Inbox` | Undecided | Anything you could not place confidently |
| `1-Projects` | A goal with a deadline | Can you mark it done? |
| `2-Areas` | A standard with no end date | Would you be embarrassed if it slipped? |
| `3-Resources` | Topics of interest | Useful, but nobody is relying on you |
| `4-Archives` | Anything above, now inactive | No longer live |

## The run

`/para:organize <dir>` drives seven steps. Never skip step 5.

1. **Validate the root.** `scan.py` refuses `$HOME`, `/`, and anything above
   home. If the user names one, ask for a subdirectory instead.
2. **Scan.** `python3 scripts/scan.py <dir>` emits clusters as JSON. Add
   `--metadata-only` when the user does not want anything read.
3. **Propose the project list.** From the clusters, draft `PARA.md` at the
   root. Propose, never assume — you are guessing at commitments.
4. **Have the user correct it, both ways.** They delete what is wrong *and add
   commitments the scan could not see*. A project with no files yet will never
   appear in a scan, and that is exactly the entry that matters most.
5. **Render the plan.** Write `.para/plan-<ts>.json` and `.para/plan-<ts>.md`.
   Group by decision — one block per rule, never one line per file. See
   `references/plan-format.md`.
6. **Apply on approval.** `python3 scripts/apply.py .para/plan-<ts>.json`.
7. **Report.** Counts moved and skipped, collisions renamed, and the exact
   `undo.py` command.

## What you decide, and what you must not

Decide alone:
- Age-based archiving. High confidence, no list needed, usually the largest group.
- Membership in a project, area, or resource the user has already confirmed.

Never decide alone — these are not visible in a filesystem at any read depth:
- Whether something is a **Project or an Area**. Projects end; areas do not.
- Whether something is an **Area or a Resource**. Responsibility versus interest.

When a file matches two `PARA.md` entries in different sections, or matches
nothing, it goes to `0-Inbox`. That is a correct answer, not a failure — a
confident wrong move costs the user far more than an undecided file.

## Rules that are not negotiable

- **Never create an empty folder.** Only `0`–`4` are made up front. A
  subfolder appears only when files land in it.
- **Never delete.** Archiving is a move. The guard hook enforces this.
- **Never move without a manifest.** Always go through `apply.py`.
- **One named directory per run.**

## Depth

For the method beyond what this skill covers, check whether a
`forte-para-method` skill is installed on this machine and use it. Do not
assume it is there; everything above works without it.

PARA is Tiago Forte's method, from *The PARA Method: Simplify, Organize, and
Master Your Digital Life*. This plugin is an independent implementation, not
affiliated with or endorsed by the author.
```

- [ ] **Step 3: Write `references/plan-format.md`**

```markdown
# Plan format

Two files, same timestamp: `.para/plan-<ts>.json` drives execution,
`.para/plan-<ts>.md` is what the user reads.

## The rule that makes the gate real

Group by **decision**, never by file. A 4,000-item directory must produce a
plan with dozens of blocks, not 4,000 lines. A plan nobody reads is a
rubber stamp, and a rubber stamp is not an approval.

Never render the full `files` array. Render `count` and up to five `samples`.

## JSON

    {
      "version": 1,
      "root": "/Users/me/Documents",
      "volume": 16777220,
      "generated": "2026-09-15T18:00:00+00:00",
      "metadata_only": false,
      "peeked": ["Scan 2024-03-11.pdf"],
      "groups": [
        {
          "id": "g1",
          "rule": "last used before 12 months ago",
          "reason": "412 files last used in 2024",
          "destination": "4-Archives/2024",
          "count": 412,
          "samples": ["a.pdf", "b.docx"],
          "files": ["a.pdf", "b.docx"]
        }
      ]
    }

All paths are relative to `root`.

## Markdown

    ## g1 — 412 files → 4-Archives/2024
    Rule: last used before 12 months ago
    Why: 412 files last used in 2024
    Examples: a.pdf, b.docx, c.png

Close with a section naming every file opened during the peek, so the privacy
cost is visible rather than implicit. If `metadata_only` is true, say so
explicitly instead.
```

- [ ] **Step 4: Write `references/classification-tests.md`**

```markdown
# Classification tests

## Project or Area

A **project** has a completion condition and a deadline. A **area** has a
standard to maintain and no end date.

- "Ship the marketing site by 15 October" — project.
- "The website stays up and current" — area.

Getting this wrong is not cosmetic. A project treated as an area feels
directionless because nothing can be finished. An area treated as a project
reverts, because no habit was built to sustain it.

Neither property is on disk. Ask.

## Area or Resource

**Responsibility** versus **interest**. The same topic lands differently for
different people: nutrition research is an area for a dietitian and a resource
for a curious reader.

A usable prompt for the user — never an automatic rule: *areas are private by
default, resources are shareable by default.* If they would have to scrub the
folder before handing it over, it is an area.

## The save filter

Ask "is this useful?", never "is this interesting?" Interesting overcollects.

## The one question

For any single item: **when will this be relevant next?** Not where does it
belong, not how important is it. One question, answerable in seconds, which is
why it survives low energy.
```

- [ ] **Step 5: Write `references/macos-signals.md`**

```markdown
# macOS signals

`scan.py` reads these via `mdls`. Every one can be absent — Spotlight indexing
is off on many external and network volumes — so each falls back to portable
metadata and the scan reports an `unindexed` count.

| Key | Use |
|---|---|
| `kMDItemLastUsedDate` | Age decisions. Preferred over mtime. |
| `kMDItemUserTags` | Finder tags — judgement the user already recorded. |
| `kMDItemWhereFroms` | Download provenance; the host often names the project. |
| `kMDItemFinderComment` | Rare, free when present. |
| `kMDItemContentTypeTree` | Package detection. |

## Why last-used beats mtime

mtime changes on sync, copy, restore, and cloud re-download. A folder restored
from backup has a uniformly recent mtime and a correct last-used date. Since
age-based archiving is the highest-volume rule in a typical run, the difference
decides the largest group in the plan.

## Packages are single items

`.app`, `.rtfd`, `.photoslibrary`, `.xcodeproj` and anything whose
`kMDItemContentTypeTree` contains `com.apple.package` is **one item**, never a
directory to walk into. Descending into a package scatters it and breaks it.
The same applies to `.git`, `node_modules`, and `.venv`.

## A degraded scan must be visible

When `unindexed` is high, say so in the plan. A silently degraded scan that
reports confident groupings from mtime alone is worse than one that admits
Spotlight had nothing.
```

- [ ] **Step 6: Write the trigger evals**

Create `plugins/para/skills/organizing-files-with-para/evals/triggers.md`:

```markdown
# Trigger cases

Should fire:
- "My Downloads folder is a disaster, help me sort it out"
- "Organize ~/Documents"
- "Can you set up PARA for my files?"
- "I have 4,000 files on my desktop and I can't find anything"
- "Apply Tiago Forte's method to this directory"
- "Tidy up this folder for me"

Should not fire:
- "What does PARA stand for?" — a question about the method, not a run.
- "Reorganize these React components" — source code, not documents.
- "My PARA inbox has filled up again" — prefer `maintaining-para-systems`.
- "Delete everything in Downloads older than a year" — this plugin never deletes.
```

- [ ] **Step 7: Verify and commit**

Run: `bun test && bun run audit`
Expected: PASS, exit 0.

Run: `claude plugin validate plugins/para --strict`
Expected: no errors.

```bash
git add plugins/para/commands plugins/para/skills/organizing-files-with-para
git commit -m "Add the para organize command and the organizing skill"
```

---

### Task 9: The maintaining skill and final verification

**Files:**
- Modify: `plugins/para/skills/maintaining-para-systems/SKILL.md`
- Create: `plugins/para/skills/maintaining-para-systems/references/upkeep.md`
- Create: `plugins/para/skills/maintaining-para-systems/references/starting-over.md`
- Create: `plugins/para/skills/maintaining-para-systems/evals/triggers.md`

**Interfaces:**
- Consumes: the run contract from Task 8; the CLI of `scan.py` and `apply.py`.
- Produces: nothing later tasks depend on. This is the last task.

- [ ] **Step 1: Expand the skill**

Replace the body below the frontmatter (keep the Task 1 frontmatter exactly):

```markdown
# Maintaining PARA systems

An organized tree drifts. Projects finish without being archived, `0-Inbox`
fills, and `PARA.md` stops describing what the user is actually working on.

This skill assumes a root that already has `PARA.md` and the `0`–`4` skeleton.
If it does not, use `organizing-files-with-para` instead.

## The upkeep pass

1. **Reconcile `PARA.md` against reality.** Ask which projects have finished.
   A finished project moves to `4-Archives` whole — folder and all.
2. **Sweep `0-Inbox`.** Re-scan it as a root of its own; everything there was
   previously undecidable, and the project list may have grown since.
3. **Report drift, do not fix it silently.** A folder under `1-Projects` with
   no `PARA.md` entry, or an entry with no folder, is a question for the user.
4. **Mine before archiving.** Ask whether anything in a finishing project is
   reusable elsewhere before it goes cold.

Every move still goes through an approved plan and `apply.py`. Maintenance is
not a licence to skip the gate.

## When the tree is past repair

Digital bankruptcy is a supported outcome, not a failure: move everything into
`4-Archives/<today>` and re-run the setup. Nothing is deleted and everything
stays searchable. Offer it when the inbox has grown faster than the sweep for
several passes running.

See `references/upkeep.md` and `references/starting-over.md`.

PARA is Tiago Forte's method, from *The PARA Method: Simplify, Organize, and
Master Your Digital Life*. This plugin is an independent implementation, not
affiliated with or endorsed by the author.
```

- [ ] **Step 2: Write `references/upkeep.md`**

```markdown
# The upkeep pass

Keep it short enough to actually happen. A maintenance routine that takes an
hour gets skipped, and a skipped routine is worth nothing.

## Order

1. **Archives first.** Finished projects are the highest-volume, lowest-risk
   move, and clearing them shrinks everything downstream.
2. **Then the inbox.** Re-scan `0-Inbox` as its own root.
3. **Then drift.** Report mismatches between `PARA.md` and the folders.

## Drift worth reporting

| Symptom | Likely meaning |
|---|---|
| Folder under `1-Projects`, no `PARA.md` entry | A project started outside the system |
| `PARA.md` entry, no folder | Finished, or never started |
| Project untouched for months | Probably finished, or was an area all along |
| `0-Inbox` growing every pass | The project list is too thin to match against |

That last row is the important one. A growing inbox is usually not a sorting
failure — it means the vocabulary is missing entries, and the fix is in
`PARA.md`, not in more aggressive classification.

## Skipped weeks cost nothing

The system is designed to fail gracefully. A month of skipped upkeep produces a
bigger pass, not a broken tree. Never imply the user has fallen behind.
```

- [ ] **Step 3: Write `references/starting-over.md`**

```markdown
# Digital bankruptcy

When a tree has drifted past the point where sorting it is worth the effort,
the supported move is to declare bankruptcy: move everything into
`4-Archives/<today's date>` and re-run the sixty-second setup.

## Why this is safe

Nothing is deleted. Everything stays exactly where search can find it. The
archive is a resting place, not a wastebasket — which is the whole reason the
plugin has no delete verb.

## When to offer it

- `0-Inbox` has grown for several upkeep passes running.
- `PARA.md` no longer resembles what the user is working on.
- The user says some version of "I've lost track of this".

Offer it. Do not perform it unprompted — it is still a plan, it still needs
approval, and it still writes a manifest.

## After

Re-run `organizing-files-with-para` against the same root. The archived tree is
untouched input for the next scan if it is ever needed.
```

- [ ] **Step 4: Write the trigger evals**

Create `plugins/para/skills/maintaining-para-systems/evals/triggers.md`:

```markdown
# Trigger cases

Should fire:
- "Time for my weekly review"
- "My PARA inbox has filled up again"
- "Archive the projects I've finished"
- "My folders don't match my project list any more"
- "This system has gotten away from me — should I start over?"

Should not fire:
- "Organize my Downloads folder" — no PARA tree yet; prefer `organizing-files-with-para`.
- "What's the difference between a project and an area?" — a method question.
- "Delete my old archives" — this plugin never deletes.
```

- [ ] **Step 5: Final verification across the whole catalog**

Run: `python3 -m unittest discover -s plugins/para/scripts/test -p 'test_*.py' -v`
Expected: PASS, all tests.

Run: `bun test`
Expected: PASS.

Run: `bun run audit`
Expected: exit 0, and the README skills column lists both skills.

Run: `claude plugin validate . --strict`
Expected: no errors.

- [ ] **Step 6: Confirm no delete verb reached the shipped code**

Run: `grep -rnE "shutil\.rmtree|os\.remove|\.unlink\(|subprocess.*\brm\b" plugins/para/scripts --include=*.py | grep -v "/test/"`
Expected: no output. Any hit is a constraint violation and must be removed before commit.

- [ ] **Step 7: Commit**

```bash
git add plugins/para/skills/maintaining-para-systems
git commit -m "Add the para maintaining skill and its references"
```

---

## Self-Review

**Spec coverage.** Every section of the spec maps to a task:

| Spec section | Task |
|---|---|
| §3 What ships (manifest, registration, README) | 1 |
| §5.1 `PARA.md` | 2 (`para_index`), 8 (step 3 of the run) |
| §5.2/5.3 plan JSON and Markdown | 8 (`references/plan-format.md`), 5 (consumed by `apply`) |
| §5.4 scan clusters | 3, 4 |
| §5.5 undo manifest | 5 (written), 6 (read) |
| §4 the seven-step run | 8 |
| §6 classification rules | 3 (`cluster` precedence), 8 (`classification-tests.md`) |
| §6.1 tunable defaults | 3, 4 (flags), Global Constraints |
| §7 macOS signals | 4, 8 (`macos-signals.md`) |
| §8 safety model | 2 (`para_paths`), 5 (validation), 7 (guard) |
| §9 error handling | 3 (unreadable counted), 5 (whole-plan refusal), 6 (per-file refusal) |
| §10 testing | every task; gate in 2 |
| §11 attribution | 1 (README, both SKILL.md), 8, 9 |
| §12 non-goals | Global Constraints (no delete), verified in 9 step 6 |

**Placeholder scan.** No "TBD", no "add error handling", no "similar to Task N". Every code step carries the actual code. Every test step carries the actual test and the exact command with its expected result.

**Type consistency.** Checked across tasks: `validate_root`, `volume_of`, `is_package`, `matches_any`, `safe_destination`, `SKELETON`, `DEFAULT_NEVER_READ`, `DEFAULT_NEVER_MOVE` are defined in Task 2 and used under those exact names in Tasks 3–7. `Index.classify` returns the folder strings `"1-Projects"`/`"2-Areas"`/`"3-Resources"` in Task 2 and is consumed as such in Task 3. The manifest keys `from`/`to`/`size`/`mtime_ns`/`inode` are written in Task 5 and read under the same names in Task 6. `walk` gains its `metadata_only` keyword in Task 4 with the signature change stated explicitly.

**One gap found and closed during review.** Task 3's `walk` originally had no way to skip the `0`–`4` skeleton, which would have made a second run re-sort its own output. `test_does_not_descend_into_the_skeleton` and the `pp.SKELETON` check in the top-level loop close it.
