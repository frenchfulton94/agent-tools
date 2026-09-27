# Godot Plugin Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship an installable `godot` plugin containing the vendored documentation slice, a nine-tool MCP server, two hooks, and the four spine skills — verified by `bun test`, `bun run audit`, and `claude plugin validate`.

**Architecture:** A Python package under `plugins/godot/scripts/godot/` holds one module per responsibility (scene parsing, project parsing, reference graphing, engine subprocess handling, API caching, renderer drivers). A thin `godot_mcp_server.py` wires them to JSON-RPC 2.0 over stdio using only the standard library, following `unraid-ops`. Two bash hooks follow `dokploy-guard.sh` and `security/flag-secrets.sh`. Skills are Markdown authored through `meta-skills:authoring-skills`.

**Tech Stack:** Python 3 (standard library only — no pip install step), Bash + `jq` for hooks, Bun for the repository test suite, Godot 4.7.2 for integration tests.

**Spec:** `docs/superpowers/specs/2026-09-26-godot-plugin-design.md`

**Scope:** This plan covers the foundation and the four spine skills. The thirteen subsystem and language skills are a separate plan, per spec §10.

## Global Constraints

- **Never classify a Godot subprocess result by exit code.** `--check-only` exits `0` on scripts with parse errors (spec §3.1). Classify by parsing stderr.
- **The MCP server never mutates project source.** No tool creates, edits, or saves a project file (spec decision 4). `check_shader` and `screenshot_scene` write only to paths outside the project.
- **Python standard library only.** No `mcp` package, no third-party imports (spec decision 17).
- **Python tests use `unittest`**, discovered by `tests/godot-scripts.test.ts` under `bun test` (spec decision 18).
- **Hooks fail open.** Missing `jq` or missing `godot` exits 0 silently rather than erroring on every tool call.
- **No runtime reference to any skill outside this plugin**, and no `dependencies` array in `plugin.json` (spec decision 12).
- **Plugin version `0.1.0`.** Description must be byte-identical in `plugins/godot/.claude-plugin/plugin.json` and the `.claude-plugin/marketplace.json` entry — `bun test` compares them.
- **Vendored docs are verbatim copies.** Never edit a file under `plugins/godot/godot-docs/`.
- Source docs: `/Users/michaelfrenchfultonjr/Downloads/godot-docs-master` (Godot 4.7).
- Both gates must pass before every commit touching `plugins/`: `bun test` and `bun run audit`.

---

## File Structure

| Path | Responsibility |
|---|---|
| `plugins/godot/.claude-plugin/plugin.json` | Manifest: name, version, description, keywords. No dependencies |
| `plugins/godot/.mcp.json` | Points Claude Code at `godot_mcp_server.py` |
| `plugins/godot/README.md` | Components, limits, local run instructions |
| `plugins/godot/godot-docs/` | Verbatim vendored slice + `VERSION` |
| `plugins/godot/hooks/hooks.json` | Hook registration |
| `plugins/godot/hooks/scripts/godot-guard.sh` | PreToolUse Bash guard |
| `plugins/godot/hooks/scripts/check-gdscript.sh` | PostToolUse advisory GDScript check |
| `plugins/godot/scripts/godot_mcp_server.py` | JSON-RPC loop, tool schemas, dispatch. No business logic |
| `plugins/godot/scripts/godot/tscn.py` | `.tscn`/`.tres` parser and scene-tree assembly |
| `plugins/godot/scripts/godot/project.py` | `project.godot` and `export_presets.cfg` parsing |
| `plugins/godot/scripts/godot/refs.py` | UID index, reference graph, broken/orphan detection |
| `plugins/godot/scripts/godot/engine.py` | Binary discovery, subprocess with timeout, stderr diagnostics |
| `plugins/godot/scripts/godot/api.py` | Engine API dump cache, class lookup and search |
| `plugins/godot/scripts/godot/render.py` | Renderer-backed drivers: `check_shader`, `screenshot_scene` |
| `plugins/godot/scripts/godot/drivers/*.gd` | GDScript driver templates run outside the project |
| `plugins/godot/scripts/test/` | `unittest` suites and fixtures |
| `tests/godot-scripts.test.ts` | Bun gate that runs the Python suite |
| `plugins/godot/skills/*/` | Four spine skills |

---

### Task 1: Vendored docs slice, plugin skeleton, and the `gdscript` skill

Registers the plugin so `bun test` passes from the first commit. A plugin directory with no marketplace entry fails `marketplace-integrity.test.ts`, and a README row with no skills fails `bun run audit`, so the manifest, the registration, and one real skill must land together.

**Files:**
- Create: `plugins/godot/.claude-plugin/plugin.json`
- Create: `plugins/godot/godot-docs/VERSION`
- Create: `plugins/godot/godot-docs/` (9 verbatim `.rst` files + `best_practices/`)
- Create: `plugins/godot/skills/gdscript/SKILL.md`
- Create: `plugins/godot/skills/gdscript/references/static-typing.md`
- Create: `plugins/godot/skills/gdscript/references/style-and-warnings.md`
- Create: `plugins/godot/skills/gdscript/references/exports-and-docs.md`
- Create: `plugins/godot/skills/gdscript/evals/triggers.md`
- Create: `plugins/godot/README.md`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `${CLAUDE_PLUGIN_ROOT}/godot-docs/` as the vendored-slice path every later skill references. The plugin `name` is `godot`; the skill name `gdscript` is reserved in the catalog namespace.

- [ ] **Step 1: Copy the vendored slice verbatim**

```bash
cd /Users/michaelfrenchfultonjr/Projects/agent-tools
D=/Users/michaelfrenchfultonjr/Downloads/godot-docs-master
V=plugins/godot/godot-docs
mkdir -p $V/file_formats $V/editor $V/gdscript $V/export $V/best_practices
cp $D/engine_details/file_formats/tscn.rst          $V/file_formats/
cp $D/tutorials/editor/command_line_tutorial.rst    $V/editor/
cp $D/tutorials/scripting/gdscript/gdscript_basics.rst      $V/gdscript/
cp $D/tutorials/scripting/gdscript/gdscript_styleguide.rst  $V/gdscript/
cp $D/tutorials/scripting/gdscript/static_typing.rst        $V/gdscript/
cp $D/tutorials/scripting/gdscript/warning_system.rst       $V/gdscript/
cp $D/tutorials/scripting/gdscript/gdscript_exports.rst     $V/gdscript/
cp $D/tutorials/export/exporting_projects.rst  $V/export/
cp $D/tutorials/export/feature_tags.rst        $V/export/
cp $D/tutorials/best_practices/*.rst           $V/best_practices/
rm -f $V/best_practices/index.rst
du -sh $V && find $V -name '*.rst' | wc -l
```

Expected: roughly 600–800 KB, 21 `.rst` files.

- [ ] **Step 2: Write the VERSION file**

```bash
cat > plugins/godot/godot-docs/VERSION <<'EOF'
Source:  https://github.com/godotengine/godot-docs
Branch:  master
Engine:  4.7 (conf.py godot_version)
Synced:  2026-09-26

These files are VERBATIM copies. Never edit them.

Why these and not others: they carry exact material that paraphrasing
corrupts — the .tscn grammar the parser is written against, the CLI flag
tables, the GDScript style/typing/warning references, and the export and
feature-tag tables. Everything else is distilled into each skill's
references/. The class reference is not vendored at all; it is generated
from the user's own engine binary by the MCP server.
EOF
```

- [ ] **Step 3: Write the plugin manifest**

```bash
mkdir -p plugins/godot/.claude-plugin
cat > plugins/godot/.claude-plugin/plugin.json <<'EOF'
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "godot",
  "displayName": "Godot",
  "version": "0.1.0",
  "description": "Game development with Godot 4 — project and scene architecture, the .tscn and .tres file formats and their uid:// identity rules, GDScript with static typing, and a verify loop built on the engine's own headless tooling. Ships a read-only MCP server that parses a project, checks scripts and shaders, runs scenes, captures screenshots, and serves the class reference generated from the user's own engine binary, plus a guard against the file moves that break uid:// references unrepairably.",
  "author": {
    "name": "Agent Tools",
    "email": "michael@frenchfultonjr.dev"
  },
  "license": "MIT",
  "keywords": ["godot", "gdscript", "gamedev", "game-engine", "tscn", "shaders", "game-development"]
}
EOF
```

- [ ] **Step 4: Register in the marketplace**

Add this object to the `plugins` array in `.claude-plugin/marketplace.json`, after the `para` entry. The `description` must be byte-identical to the manifest's.

```json
    {
      "name": "godot",
      "source": "./plugins/godot",
      "category": "development",
      "description": "Game development with Godot 4 — project and scene architecture, the .tscn and .tres file formats and their uid:// identity rules, GDScript with static typing, and a verify loop built on the engine's own headless tooling. Ships a read-only MCP server that parses a project, checks scripts and shaders, runs scenes, captures screenshots, and serves the class reference generated from the user's own engine binary, plus a guard against the file moves that break uid:// references unrepairably."
    }
```

- [ ] **Step 5: Write the `gdscript` skill**

Invoke `meta-skills:authoring-skills` before writing. Create `plugins/godot/skills/gdscript/SKILL.md` with this exact frontmatter, then a body covering: static typing and why it is worth the keystrokes, the style guide's concrete rules, the warning system and how to configure it, `@export` and its annotations, doc comments, and format strings. Point at `${CLAUDE_PLUGIN_ROOT}/godot-docs/gdscript/` for the verbatim references.

```yaml
---
name: gdscript
description: Writes and reviews GDScript for Godot 4 — static typing and inference, the official style guide, the warning system and its configuration, @export annotations, doc comments, and format strings. Use when writing, reviewing, or fixing a .gd file, when deciding whether to annotate a type, when a GDScript warning or parse error needs interpreting, or when exporting a variable to the inspector. For the scene files a script attaches to, use godot-scene-files; for running or checking the code, use godot-testing-and-debugging; for C# instead of GDScript, use godot-csharp.
license: MIT
compatibility: Godot 4.x. The optional gdformat/gdlint tools ship separately as gdtoolkit and are never assumed present.
---
```

Write these reference files with real content distilled from the vendored `.rst`:
- `references/static-typing.md` — inference rules, when annotation changes behavior, typed arrays and dictionaries, `as` casting.
- `references/style-and-warnings.md` — naming, ordering, line length, plus the full warning list and how to enable, disable, or promote each to an error.
- `references/exports-and-docs.md` — every `@export` variant with its inspector effect, and doc-comment syntax.

- [ ] **Step 6: Write the trigger evals**

Create `plugins/godot/skills/gdscript/evals/triggers.md` following `plugins/dokploy/skills/automating-dokploy/evals/triggers.md`. Include at least three should-fire prompts ("add type hints to this .gd file", "what does UNUSED_PARAMETER mean", "how do I show this variable in the inspector") and three should-not-fire prompts that belong to sibling skills ("why does my scene fail to load" → `godot-scene-files`; "run my game and check for errors" → `godot-testing-and-debugging`; "convert this to C#" → `godot-csharp`).

- [ ] **Step 7: Write the plugin README**

Create `plugins/godot/README.md` following `plugins/dokploy/README.md`. It must state: the skills shipped, that the MCP server is read-only and why (spec decision 4), that `check_shader` and `screenshot_scene` need a display, that running Godot creates `.godot/` and `.uid` artifacts, and that files under `godot-docs/` are verbatim and must not be edited.

- [ ] **Step 8: Add the repository README row**

Add to the `## What ships` table in `README.md`, after the `para` row. The skills column must list every skill the plugin ships — `bun run audit` checks this.

```
| [godot](plugins/godot) | `gdscript` | Game development with Godot 4 — GDScript with static typing, the style guide, and the warning system |
```

- [ ] **Step 9: Run the gates**

Run: `bun test && bun run audit && claude plugin validate plugins/godot --strict`
Expected: all three pass. If `bun run audit` reports the README skills column out of sync, the row in Step 8 does not match the shipped skill directories.

- [ ] **Step 10: Commit**

```bash
git add plugins/godot .claude-plugin/marketplace.json README.md
git commit -m "Add the godot plugin skeleton, its vendored docs slice, and the gdscript skill"
```

---

### Task 2: The `.tscn` parser

The only component that reimplements rather than delegates, and the one that can silently misread a project. It is written strict: unrecognised input raises rather than being skipped.

**Files:**
- Create: `plugins/godot/scripts/godot/__init__.py`
- Create: `plugins/godot/scripts/godot/tscn.py`
- Create: `plugins/godot/scripts/test/__init__.py`
- Create: `plugins/godot/scripts/test/test_tscn.py`
- Create: `plugins/godot/scripts/test/fixtures/scenes/simple.tscn`
- Create: `plugins/godot/scripts/test/fixtures/scenes/nested.tscn`
- Create: `plugins/godot/scripts/test/fixtures/scenes/legacy_load_steps.tscn`
- Create: `plugins/godot/scripts/test/fixtures/scenes/malformed.tscn`
- Create: `tests/godot-scripts.test.ts`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `tscn.parse(text: str) -> list[Block]` where `Block` has `.kind: str`, `.attrs: dict[str,str]`, `.props: dict[str,str]`, `.line_no: int`.
  - `tscn.scene_tree(blocks: list[Block]) -> Node | None` where `Node` has `.name: str`, `.type: str|None`, `.parent: str|None`, `.instance: str|None`, `.props: dict`, `.children: list[Node]`, `.path: str`.
  - `tscn.ext_resources(blocks) -> list[dict]` with keys `type`, `path`, `uid`, `id`.
  - `tscn.TscnParseError(Exception)` with `.line_no`, `.reason`.

- [ ] **Step 1: Write the fixtures**

```bash
mkdir -p plugins/godot/scripts/test/fixtures/scenes
cd plugins/godot/scripts/test/fixtures/scenes

cat > simple.tscn <<'EOF'
[gd_scene format=3 uid="uid://cecaux1sm7mo0"]

; a comment line

[ext_resource type="Script" uid="uid://cnnyipgx21jca" path="res://scripts/player.gd" id="1_abc"]

[node name="Main" type="Node2D"]
script = ExtResource("1_abc")

[node name="Sprite" type="Sprite2D" parent="."]
position = Vector2(10, 20)
EOF

cat > nested.tscn <<'EOF'
[gd_scene format=3 uid="uid://dnested00000"]

[sub_resource type="CircleShape2D" id="CircleShape2D_a1"]
radius = 12.0

[node name="Root" type="Node2D"]

[node name="Body" type="CharacterBody2D" parent="."]

[node name="Shape" type="CollisionShape2D" parent="Body"]
shape = SubResource("CircleShape2D_a1")

[node name="Deep" type="Marker2D" parent="Body/Shape"]
polygon = PackedVector2Array(20, 20,
300, 20,
300, 200)

[connection signal="body_entered" from="Body" to="." method="_on_body_entered"]
EOF

cat > legacy_load_steps.tscn <<'EOF'
[gd_scene load_steps=2 format=3 uid="uid://dlegacy000000"]

[node name="Old" type="Node"]
EOF

cat > malformed.tscn <<'EOF'
[gd_scene format=3]

[node name="Root" type="Node2D"]
this line is not a heading, a property, or a comment
EOF
```

- [ ] **Step 2: Write the failing tests**

Create `plugins/godot/scripts/test/test_tscn.py`:

```python
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import tscn

FIXTURES = Path(__file__).parent / "fixtures" / "scenes"


def load(name):
    return (FIXTURES / name).read_text()


class TestParse(unittest.TestCase):
    def test_heading_kinds_and_attrs(self):
        blocks = tscn.parse(load("simple.tscn"))
        kinds = [b.kind for b in blocks]
        self.assertEqual(kinds, ["gd_scene", "ext_resource", "node", "node"])
        self.assertEqual(blocks[0].attrs["uid"], "uid://cecaux1sm7mo0")
        self.assertEqual(blocks[0].attrs["format"], "3")

    def test_comments_and_blank_lines_ignored(self):
        blocks = tscn.parse(load("simple.tscn"))
        self.assertEqual(len(blocks), 4)

    def test_properties_attach_to_preceding_heading(self):
        blocks = tscn.parse(load("simple.tscn"))
        self.assertEqual(blocks[2].props["script"], 'ExtResource("1_abc")')
        self.assertEqual(blocks[3].props["position"], "Vector2(10, 20)")

    def test_multiline_property_value_is_joined(self):
        blocks = tscn.parse(load("nested.tscn"))
        deep = [b for b in blocks if b.attrs.get("name") == "Deep"][0]
        self.assertIn("300, 200", deep.props["polygon"])
        self.assertTrue(deep.props["polygon"].startswith("PackedVector2Array("))

    def test_deprecated_load_steps_does_not_break_parsing(self):
        blocks = tscn.parse(load("legacy_load_steps.tscn"))
        self.assertEqual(blocks[0].kind, "gd_scene")
        self.assertEqual(blocks[0].attrs["load_steps"], "2")

    def test_malformed_line_raises_with_line_number(self):
        with self.assertRaises(tscn.TscnParseError) as ctx:
            tscn.parse(load("malformed.tscn"))
        self.assertEqual(ctx.exception.line_no, 4)


class TestSceneTree(unittest.TestCase):
    def test_root_and_child_paths(self):
        root = tscn.scene_tree(tscn.parse(load("simple.tscn")))
        self.assertEqual(root.name, "Main")
        self.assertEqual(root.path, ".")
        self.assertEqual([c.name for c in root.children], ["Sprite"])
        self.assertEqual(root.children[0].path, "Sprite")

    def test_nested_parent_paths(self):
        root = tscn.scene_tree(tscn.parse(load("nested.tscn")))
        body = root.children[0]
        shape = body.children[0]
        deep = shape.children[0]
        self.assertEqual(body.path, "Body")
        self.assertEqual(shape.path, "Body/Shape")
        self.assertEqual(deep.path, "Body/Shape/Deep")

    def test_unknown_parent_raises(self):
        text = '[gd_scene format=3]\n\n[node name="A" type="Node"]\n\n[node name="B" type="Node" parent="Ghost"]\n'
        with self.assertRaises(tscn.TscnParseError):
            tscn.scene_tree(tscn.parse(text))


class TestExtResources(unittest.TestCase):
    def test_extracts_path_uid_type_id(self):
        res = tscn.ext_resources(tscn.parse(load("simple.tscn")))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["path"], "res://scripts/player.gd")
        self.assertEqual(res[0]["uid"], "uid://cnnyipgx21jca")
        self.assertEqual(res[0]["type"], "Script")
        self.assertEqual(res[0]["id"], "1_abc")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_tscn -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'godot'`

- [ ] **Step 4: Implement the parser**

Create `plugins/godot/scripts/godot/__init__.py` (empty file) and `plugins/godot/scripts/godot/tscn.py`:

```python
"""Parse Godot .tscn and .tres files.

The grammar is documented in godot-docs/file_formats/tscn.rst, vendored beside
this plugin. Parsing is deliberately strict: an unrecognised construct raises
rather than being skipped, because a partial scene tree presented as complete
is how an agent deletes a node it never saw.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADING = re.compile(r"^\[([A-Za-z_][A-Za-z0-9_]*)(\s[^\]]*)?\]\s*$")
_ATTR = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)=("(?:[^"\\]|\\.)*"|[^\s\]]+)')
_PROP = re.compile(r'^([A-Za-z_][A-Za-z0-9_/.]*(?:\[[^\]]*\])?)\s*=\s*(.*)$')


class TscnParseError(Exception):
    def __init__(self, line_no: int, reason: str, line: str = ""):
        super().__init__(f"line {line_no}: {reason}: {line.strip()}".rstrip(": "))
        self.line_no = line_no
        self.reason = reason
        self.line = line


@dataclass
class Block:
    kind: str
    attrs: dict
    props: dict
    line_no: int


@dataclass
class Node:
    name: str
    type: str | None = None
    parent: str | None = None
    instance: str | None = None
    props: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    path: str = ""


def _parse_attrs(text: str) -> dict:
    out = {}
    for key, value in _ATTR.findall(text or ""):
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        out[key] = value
    return out


def _incomplete(value: str) -> bool:
    """True when a property value continues on the next line."""
    depth = 0
    in_string = False
    escaped = False
    for ch in value:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if in_string:
            if ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
    return depth > 0 or in_string


def parse(text: str) -> list:
    blocks: list = []
    current = None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        stripped = raw.strip()
        if not stripped or stripped.startswith(";"):
            continue

        heading = _HEADING.match(stripped)
        if heading:
            current = Block(
                kind=heading.group(1),
                attrs=_parse_attrs(heading.group(2)),
                props={},
                line_no=i,
            )
            blocks.append(current)
            continue

        prop = _PROP.match(stripped)
        if prop:
            if current is None:
                raise TscnParseError(i, "property before any heading", raw)
            key, value = prop.group(1), prop.group(2)
            while _incomplete(value) and i < len(lines):
                value += "\n" + lines[i]
                i += 1
            current.props[key] = value.strip()
            continue

        raise TscnParseError(i, "not a heading, property, or comment", raw)
    return blocks


def ext_resources(blocks: list) -> list:
    return [
        {
            "type": b.attrs.get("type"),
            "path": b.attrs.get("path"),
            "uid": b.attrs.get("uid"),
            "id": b.attrs.get("id"),
        }
        for b in blocks
        if b.kind == "ext_resource"
    ]


def scene_tree(blocks: list):
    nodes = []
    by_path = {}
    root = None

    for b in blocks:
        if b.kind != "node":
            continue
        name = b.attrs.get("name")
        if not name:
            raise TscnParseError(b.line_no, "node heading has no name")
        node = Node(
            name=name,
            type=b.attrs.get("type"),
            parent=b.attrs.get("parent"),
            instance=b.attrs.get("instance"),
            props=dict(b.props),
        )
        if node.parent is None:
            node.path = "."
            root = node
        elif node.parent == ".":
            node.path = name
        else:
            node.path = f"{node.parent}/{name}"
        if node.path in by_path:
            raise TscnParseError(b.line_no, f"duplicate node path {node.path!r}")
        by_path[node.path] = node
        nodes.append(node)

    for node in nodes:
        if node.parent is None:
            continue
        parent = by_path.get(node.parent)
        if parent is None:
            raise TscnParseError(
                0, f"node {node.path!r} names unknown parent {node.parent!r}"
            )
        parent.children.append(node)

    return root
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_tscn -v`
Expected: PASS, 11 tests.

- [ ] **Step 6: Wire the Python suite into `bun test`**

Create `tests/godot-scripts.test.ts`:

```typescript
/**
 * godot-scripts.test.ts — runs the godot plugin's Python suite as part of `bun test`.
 *
 * The .tscn parser reads a user's scene files, and the guard decides whether a
 * destructive move reaches the shell. Both are gated here rather than run by hand:
 * a red Python suite fails the catalog suite. Skips cleanly when python3 is absent.
 *
 * Tests that need the Godot binary skip themselves from inside Python, so this
 * stays green on a machine with no engine installed.
 */

import { describe, expect, test } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..');
const hasPython = spawnSync('python3', ['--version'], { encoding: 'utf8' }).status === 0;

describe('godot python scripts', () => {
	test.skipIf(!hasPython)('unittest suite passes', () => {
		const result = spawnSync(
			'python3',
			['-m', 'unittest', 'discover', '-s', 'test', '-p', 'test_*.py'],
			{ cwd: join(ROOT, 'plugins/godot/scripts'), encoding: 'utf8' },
		);
		if (result.status !== 0) console.error(result.stderr || result.stdout);
		expect(result.status).toBe(0);
	});
});
```

- [ ] **Step 7: Run the gates**

Run: `bun test && bun run audit`
Expected: both pass; the new Godot suite appears in `bun test` output.

- [ ] **Step 8: Commit**

```bash
git add plugins/godot/scripts tests/godot-scripts.test.ts
git commit -m "Add a strict .tscn parser and gate the godot Python suite in bun test"
```

---

### Task 3: Project and export-preset parsing

**Files:**
- Create: `plugins/godot/scripts/godot/project.py`
- Create: `plugins/godot/scripts/test/test_project.py`
- Create: `plugins/godot/scripts/test/fixtures/sample-project/project.godot`
- Create: `plugins/godot/scripts/test/fixtures/sample-project/export_presets.cfg`
- Create: `plugins/godot/scripts/test/fixtures/sample-project/main.tscn`
- Create: `plugins/godot/scripts/test/fixtures/sample-project/scripts/player.gd`
- Create: `plugins/godot/scripts/test/fixtures/sample-project/scripts/player.gd.uid`
- Create: `plugins/godot/scripts/test/fixtures/sample-project/broken.gd`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `project.find_root(start: str) -> str | None` — walks up for `project.godot`.
  - `project.overview(root: str) -> dict` with keys `name`, `features`, `main_scene`, `autoloads` (dict name→path), `input_actions` (list[str]), `rendering_method`, `export_presets` (list[dict] with `name`, `platform`, `runnable`, `export_path`).
  - `project.parse_cfg(text: str) -> dict[str, dict[str, str]]` — section → key → raw value, for Godot's INI dialect.

- [ ] **Step 1: Write the sample project fixture**

```bash
mkdir -p plugins/godot/scripts/test/fixtures/sample-project/scripts
cd plugins/godot/scripts/test/fixtures/sample-project

cat > project.godot <<'EOF'
config_version=5

[application]

config/name="Sample"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.4", "Forward Plus")

[autoload]

GameState="*res://scripts/game_state.gd"
Audio="res://scripts/audio.gd"

[input]

jump={
"deadzone": 0.5,
"events": []
}
fire={
"deadzone": 0.5,
"events": []
}

[rendering]

renderer/rendering_method="forward_plus"
EOF

cat > export_presets.cfg <<'EOF'
[preset.0]

name="macOS"
platform="macOS"
runnable=true
export_path="builds/sample.dmg"

[preset.0.options]

binary_format/architecture="universal"

[preset.1]

name="Web"
platform="Web"
runnable=false
export_path="builds/web/index.html"
EOF

cat > main.tscn <<'EOF'
[gd_scene format=3 uid="uid://dsample000000"]

[ext_resource type="Script" uid="uid://cnnyipgx21jca" path="res://scripts/player.gd" id="1_abc"]

[node name="Main" type="Node2D"]
script = ExtResource("1_abc")
EOF

cat > scripts/player.gd <<'EOF'
extends Node2D


func _ready() -> void:
	print("player ready")
EOF

printf 'uid://cnnyipgx21jca' > scripts/player.gd.uid

cat > broken.gd <<'EOF'
extends Node


func _ready() -> void:
	var x: int = "not an int"
	undefined_function_call()
EOF
```

- [ ] **Step 2: Write the failing tests**

Create `plugins/godot/scripts/test/test_project.py`:

```python
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import project

SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"


class TestParseCfg(unittest.TestCase):
    def test_sections_and_keys(self):
        cfg = project.parse_cfg((SAMPLE / "project.godot").read_text())
        self.assertEqual(cfg["application"]["config/name"], '"Sample"')
        self.assertEqual(cfg["rendering"]["renderer/rendering_method"], '"forward_plus"')

    def test_multiline_value_is_joined(self):
        cfg = project.parse_cfg((SAMPLE / "project.godot").read_text())
        self.assertIn("deadzone", cfg["input"]["jump"])

    def test_leading_keys_without_section(self):
        cfg = project.parse_cfg((SAMPLE / "project.godot").read_text())
        self.assertEqual(cfg[""]["config_version"], "5")


class TestOverview(unittest.TestCase):
    def setUp(self):
        self.ov = project.overview(str(SAMPLE))

    def test_name_and_main_scene(self):
        self.assertEqual(self.ov["name"], "Sample")
        self.assertEqual(self.ov["main_scene"], "res://main.tscn")

    def test_features(self):
        self.assertIn("4.4", self.ov["features"])

    def test_autoloads_strip_the_singleton_marker(self):
        self.assertEqual(self.ov["autoloads"]["GameState"], "res://scripts/game_state.gd")
        self.assertEqual(self.ov["autoloads"]["Audio"], "res://scripts/audio.gd")

    def test_input_actions(self):
        self.assertEqual(sorted(self.ov["input_actions"]), ["fire", "jump"])

    def test_rendering_method(self):
        self.assertEqual(self.ov["rendering_method"], "forward_plus")

    def test_export_presets(self):
        presets = self.ov["export_presets"]
        self.assertEqual(len(presets), 2)
        self.assertEqual(presets[0]["name"], "macOS")
        self.assertEqual(presets[0]["platform"], "macOS")
        self.assertTrue(presets[0]["runnable"])
        self.assertEqual(presets[1]["export_path"], "builds/web/index.html")
        self.assertFalse(presets[1]["runnable"])


class TestFindRoot(unittest.TestCase):
    def test_finds_root_from_nested_path(self):
        found = project.find_root(str(SAMPLE / "scripts"))
        self.assertEqual(Path(found).resolve(), SAMPLE.resolve())

    def test_returns_none_outside_a_project(self):
        self.assertIsNone(project.find_root("/"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_project -v`
Expected: FAIL with `ImportError: cannot import name 'project'`

- [ ] **Step 4: Implement**

Create `plugins/godot/scripts/godot/project.py`:

```python
"""Read project.godot and export_presets.cfg.

Both use Godot's INI dialect: `[section]` headings, `key=value` pairs, and
values that may span lines when a bracket or brace is left open. Keys contain
slashes (`config/name`), so this is not configparser-compatible.

Nothing here invokes the Godot binary. A project can be described on a machine
with no engine installed, and test_no_binary_needed pins that.
"""

from __future__ import annotations

import os
import re

_SECTION = re.compile(r"^\[([^\]]+)\]\s*$")
_KEY = re.compile(r'^([A-Za-z_][A-Za-z0-9_/.]*)\s*=\s*(.*)$')


def _incomplete(value: str) -> bool:
    depth = 0
    in_string = False
    escaped = False
    for ch in value:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if in_string:
            if ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
    return depth > 0 or in_string


def parse_cfg(text: str) -> dict:
    out: dict = {"": {}}
    section = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        stripped = raw.strip()
        if not stripped or stripped.startswith(";"):
            continue
        heading = _SECTION.match(stripped)
        if heading:
            section = heading.group(1)
            out.setdefault(section, {})
            continue
        kv = _KEY.match(stripped)
        if kv:
            key, value = kv.group(1), kv.group(2)
            while _incomplete(value) and i < len(lines):
                value += "\n" + lines[i]
                i += 1
            out.setdefault(section, {})[key] = value.strip()
    return out


def _unquote(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def _string_list(value: str | None) -> list:
    if not value:
        return []
    return re.findall(r'"([^"]*)"', value)


def find_root(start: str) -> str | None:
    path = os.path.abspath(start)
    if os.path.isfile(path):
        path = os.path.dirname(path)
    while True:
        if os.path.isfile(os.path.join(path, "project.godot")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def overview(root: str) -> dict:
    cfg = parse_cfg(open(os.path.join(root, "project.godot")).read())
    app = cfg.get("application", {})

    autoloads = {}
    for name, value in cfg.get("autoload", {}).items():
        path = _unquote(value) or ""
        # A leading "*" marks the autoload as a singleton; it is not part of the path.
        autoloads[name] = path[1:] if path.startswith("*") else path

    presets = []
    preset_sections = sorted(
        (s for s in cfg if re.fullmatch(r"preset\.\d+", s)),
        key=lambda s: int(s.split(".")[1]),
    )
    for section in preset_sections:
        body = cfg[section]
        presets.append(
            {
                "name": _unquote(body.get("name")),
                "platform": _unquote(body.get("platform")),
                "runnable": body.get("runnable", "false").strip() == "true",
                "export_path": _unquote(body.get("export_path")),
            }
        )

    return {
        "name": _unquote(app.get("config/name")),
        "features": _string_list(app.get("config/features")),
        "main_scene": _unquote(app.get("run/main_scene")),
        "autoloads": autoloads,
        "input_actions": sorted(cfg.get("input", {}).keys()),
        "rendering_method": _unquote(
            cfg.get("rendering", {}).get("renderer/rendering_method")
        ),
        "export_presets": presets,
    }
```

Note: `overview` reads `export_presets.cfg` only if present. Add this before the `return`, and merge its presets in:

```python
    presets_path = os.path.join(root, "export_presets.cfg")
    if os.path.isfile(presets_path):
        cfg.update(parse_cfg(open(presets_path).read()))
```

Place it immediately after the `cfg = parse_cfg(...)` line so the preset sections are in `cfg` before they are read.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_project -v`
Expected: PASS, 11 tests.

- [ ] **Step 6: Commit**

```bash
git add plugins/godot/scripts
git commit -m "Parse project.godot and export_presets.cfg without invoking Godot"
```

---

### Task 4: The reference graph

Detects the failure verified in spec §3.4: a `.gd` moved without its `.uid` sidecar, leaving scenes pointing at a UID nothing owns.

**Files:**
- Create: `plugins/godot/scripts/godot/refs.py`
- Create: `plugins/godot/scripts/test/test_refs.py`

**Interfaces:**
- Consumes: `tscn.parse`, `tscn.ext_resources`, `project.find_root`.
- Produces: `refs.graph(root: str) -> dict` with keys:
  - `uid_index`: dict uid → project-relative path.
  - `broken`: list of `{scene, path, uid, reason}` where reason is `"missing-path"` or `"uid-not-found"`.
  - `orphans`: list of project-relative paths referenced by no scene or resource.
  - `duplicate_uids`: list of `{uid, paths}`.

- [ ] **Step 1: Write the failing tests**

Create `plugins/godot/scripts/test/test_refs.py`:

```python
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import refs

SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"


class TestGraph(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "proj"
        shutil.copytree(SAMPLE, self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_healthy_project_has_no_broken_references(self):
        g = refs.graph(str(self.root))
        self.assertEqual(g["broken"], [])

    def test_uid_index_maps_sidecar_uid_to_its_script(self):
        g = refs.graph(str(self.root))
        self.assertEqual(g["uid_index"]["uid://cnnyipgx21jca"], "scripts/player.gd")

    def test_move_without_sidecar_is_reported_broken(self):
        # Spec 3.4: the script moves, the .uid does not. Unrepairable by --import.
        (self.root / "entities").mkdir()
        shutil.move(str(self.root / "scripts" / "player.gd"),
                    str(self.root / "entities" / "player.gd"))
        (self.root / "scripts" / "player.gd.uid").unlink()
        g = refs.graph(str(self.root))
        self.assertEqual(len(g["broken"]), 1)
        self.assertEqual(g["broken"][0]["uid"], "uid://cnnyipgx21jca")
        self.assertEqual(g["broken"][0]["reason"], "uid-not-found")

    def test_move_with_sidecar_resolves_through_the_uid(self):
        # Spec 3.4: identity survives, so this is NOT reported broken even though
        # the .tscn still names the old path.
        (self.root / "entities").mkdir()
        shutil.move(str(self.root / "scripts" / "player.gd"),
                    str(self.root / "entities" / "player.gd"))
        shutil.move(str(self.root / "scripts" / "player.gd.uid"),
                    str(self.root / "entities" / "player.gd.uid"))
        g = refs.graph(str(self.root))
        self.assertEqual(g["broken"], [])
        self.assertEqual(g["uid_index"]["uid://cnnyipgx21jca"], "entities/player.gd")

    def test_deleted_target_with_no_uid_anywhere_is_missing_path(self):
        (self.root / "scripts" / "player.gd").unlink()
        (self.root / "scripts" / "player.gd.uid").unlink()
        g = refs.graph(str(self.root))
        self.assertEqual(g["broken"][0]["reason"], "uid-not-found")

    def test_orphan_detection(self):
        (self.root / "unused.gd").write_text("extends Node\n")
        g = refs.graph(str(self.root))
        self.assertIn("unused.gd", g["orphans"])

    def test_duplicate_uids_are_reported(self):
        (self.root / "copy.gd").write_text("extends Node\n")
        (self.root / "copy.gd.uid").write_text("uid://cnnyipgx21jca")
        g = refs.graph(str(self.root))
        self.assertEqual(len(g["duplicate_uids"]), 1)
        self.assertEqual(g["duplicate_uids"][0]["uid"], "uid://cnnyipgx21jca")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_refs -v`
Expected: FAIL with `ImportError: cannot import name 'refs'`

- [ ] **Step 3: Implement**

Create `plugins/godot/scripts/godot/refs.py`:

```python
"""Build the uid:// reference graph for a project and report what is broken.

Identity in Godot is carried three different ways, measured in spec 3.7:

  .gd, .gdshader      a .uid sidecar file beside the source
  imported assets     a .import sidecar carrying uid=
  .tscn, .tres        inline, in the [gd_scene]/[gd_resource] heading

A reference resolves if either the path still exists or the uid is still owned
by some file. A move that carries the sidecar keeps the uid and stays healthy
even though the .tscn still names the old path; a move that leaves the sidecar
behind mints a new uid and breaks the reference unrepairably (spec 3.4).
"""

from __future__ import annotations

import os
import re

from . import tscn

SCENE_EXT = (".tscn", ".tres")
SIDECAR_SOURCE_EXT = (".gd", ".gdshader")
SKIP_DIRS = {".godot", ".git", "addons"}
_UID_IN_IMPORT = re.compile(r'^uid="(uid://[^"]+)"', re.MULTILINE)


def _walk(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            full = os.path.join(dirpath, name)
            yield full, os.path.relpath(full, root).replace(os.sep, "/")


def _uid_index(root: str):
    index: dict = {}
    duplicates: dict = {}

    def record(uid, rel):
        if not uid:
            return
        if uid in index and index[uid] != rel:
            duplicates.setdefault(uid, [index[uid]]).append(rel)
        else:
            index[uid] = rel

    for full, rel in _walk(root):
        if rel.endswith(".uid"):
            source = rel[: -len(".uid")]
            record(open(full).read().strip(), source)
        elif rel.endswith(".import"):
            match = _UID_IN_IMPORT.search(open(full, errors="replace").read())
            if match:
                record(match.group(1), rel[: -len(".import")])
        elif rel.endswith(SCENE_EXT):
            try:
                blocks = tscn.parse(open(full, errors="replace").read())
            except tscn.TscnParseError:
                continue
            if blocks and blocks[0].kind in ("gd_scene", "gd_resource"):
                record(blocks[0].attrs.get("uid"), rel)

    return index, [{"uid": u, "paths": p} for u, p in duplicates.items()]


def graph(root: str) -> dict:
    index, duplicates = _uid_index(root)
    broken = []
    referenced = set()

    for full, rel in _walk(root):
        if not rel.endswith(SCENE_EXT):
            continue
        try:
            blocks = tscn.parse(open(full, errors="replace").read())
        except tscn.TscnParseError:
            continue
        for res in tscn.ext_resources(blocks):
            path = (res.get("path") or "")
            uid = res.get("uid")
            target = path[len("res://"):] if path.startswith("res://") else path
            path_exists = bool(target) and os.path.isfile(os.path.join(root, target))
            uid_target = index.get(uid) if uid else None

            if path_exists:
                referenced.add(target)
            elif uid_target:
                referenced.add(uid_target)
            else:
                broken.append(
                    {
                        "scene": rel,
                        "path": path,
                        "uid": uid,
                        "reason": "uid-not-found" if uid else "missing-path",
                    }
                )

    orphans = []
    for _, rel in _walk(root):
        if rel.endswith((".uid", ".import")) or rel.endswith(SCENE_EXT):
            continue
        if not rel.endswith(SIDECAR_SOURCE_EXT):
            continue
        if rel not in referenced:
            orphans.append(rel)

    return {
        "uid_index": index,
        "broken": broken,
        "orphans": sorted(orphans),
        "duplicate_uids": duplicates,
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_refs -v`
Expected: PASS, 7 tests. The two spec-§3.4 tests are the contract; if `test_move_with_sidecar_resolves_through_the_uid` fails, the graph is reporting healthy projects as broken and will be disabled by users.

- [ ] **Step 5: Commit**

```bash
git add plugins/godot/scripts
git commit -m "Detect uid:// reference breakage, including the sidecar-less move"
```

---

### Task 5: The engine wrapper

Where spec §3.1 is encoded. Every Godot subprocess goes through here.

**Files:**
- Create: `plugins/godot/scripts/godot/engine.py`
- Create: `plugins/godot/scripts/test/test_engine.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `engine.find_binary() -> str | None` — `GODOT_BIN`, then `godot`, `godot4` on PATH, then the macOS app bundle path.
  - `engine.run(args: list[str], cwd: str | None = None, timeout: int = 60) -> Result` where `Result` has `.stdout`, `.stderr`, `.returncode`, `.timed_out`.
  - `engine.diagnostics(stderr: str) -> list[dict]` with keys `severity`, `message`, `file`, `line`.
  - `engine.check_script(root: str, rel_path: str, timeout: int = 30) -> list[dict]`.
  - `engine.run_scene(root: str, scene: str | None, frames: int = 120, timeout: int = 60) -> dict` with keys `stdout`, `diagnostics`, `timed_out`.
  - `engine.MissingBinary(Exception)`.

- [ ] **Step 1: Write the failing tests**

Create `plugins/godot/scripts/test/test_engine.py`:

```python
import os
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import engine

SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"
HAS_GODOT = engine.find_binary() is not None

GDSCRIPT_STDERR = """SCRIPT ERROR: Parse Error: Cannot assign a value of type "String" as "int".
          at: GDScript::reload (res://broken.gd:5)
SCRIPT ERROR: Parse Error: Function "undefined_function_call()" not found in base self.
          at: GDScript::reload (res://broken.gd:6)
ERROR: Failed to load script "res://broken.gd" with error "Parse error".
   at: load (modules/gdscript/gdscript_resource_format.cpp:46)
"""

SHADER_STDERR = """SHADER ERROR: Invalid arguments for the built-in function: "vec4(float,float,float)".
          at: (null) (res://bad.gdshader:3)
"""


class TestDiagnostics(unittest.TestCase):
    def test_extracts_script_errors_with_file_and_line(self):
        found = engine.diagnostics(GDSCRIPT_STDERR)
        located = [d for d in found if d["file"]]
        self.assertEqual(len(located), 2)
        self.assertEqual(located[0]["file"], "res://broken.gd")
        self.assertEqual(located[0]["line"], 5)
        self.assertIn("Cannot assign", located[0]["message"])

    def test_engine_internal_cpp_locations_are_not_user_files(self):
        # `modules/gdscript/...cpp:46` is engine source, not the user's project.
        for d in engine.diagnostics(GDSCRIPT_STDERR):
            self.assertFalse((d["file"] or "").endswith(".cpp"))

    def test_extracts_shader_errors(self):
        found = engine.diagnostics(SHADER_STDERR)
        located = [d for d in found if d["file"]]
        self.assertEqual(located[0]["file"], "res://bad.gdshader")
        self.assertEqual(located[0]["line"], 3)
        self.assertEqual(located[0]["severity"], "SHADER ERROR")

    def test_clean_output_yields_nothing(self):
        self.assertEqual(engine.diagnostics("Godot Engine v4.7.2.stable\n"), [])


@unittest.skipUnless(HAS_GODOT, "godot not on PATH")
class TestAgainstRealEngine(unittest.TestCase):
    def test_broken_script_is_reported_broken_despite_exit_zero(self):
        # Spec 3.1: --check-only exits 0 on parse errors. This test is the guard
        # against anyone rewriting check_script to trust returncode.
        found = engine.check_script(str(SAMPLE), "broken.gd")
        self.assertTrue(found, "broken.gd must produce diagnostics")
        self.assertTrue(any(d["line"] == 5 for d in found))

    def test_exit_code_really_is_zero_for_broken_input(self):
        result = engine.run(
            ["--headless", "--path", str(SAMPLE), "--check-only", "--script", "broken.gd"]
        )
        self.assertEqual(result.returncode, 0)

    def test_clean_script_produces_no_diagnostics(self):
        self.assertEqual(engine.check_script(str(SAMPLE), "scripts/player.gd"), [])

    def test_timeout_is_enforced_by_us_not_by_timeout1(self):
        # macOS has no timeout(1); the wrapper owns the deadline.
        result = engine.run(["--headless", "--quit-after", "100000",
                             "--path", str(SAMPLE)], timeout=3)
        self.assertTrue(result.timed_out)


class TestFindBinary(unittest.TestCase):
    def test_env_override_wins(self):
        os.environ["GODOT_BIN"] = "/nonexistent/godot-x"
        try:
            self.assertEqual(engine.find_binary(), "/nonexistent/godot-x")
        finally:
            del os.environ["GODOT_BIN"]


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_engine -v`
Expected: FAIL with `ImportError: cannot import name 'engine'`

- [ ] **Step 3: Implement**

Create `plugins/godot/scripts/godot/engine.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_engine -v`
Expected: PASS. On a machine with Godot installed, 9 tests; without it, 5 tests and 4 skips.

- [ ] **Step 5: Commit**

```bash
git add plugins/godot/scripts
git commit -m "Wrap the Godot binary, classifying results by stderr rather than exit code"
```

---

### Task 6: The engine API cache

**Files:**
- Create: `plugins/godot/scripts/godot/api.py`
- Create: `plugins/godot/scripts/test/test_api.py`

**Interfaces:**
- Consumes: `engine.run`, `engine.find_binary`.
- Produces:
  - `api.engine_version() -> str` — e.g. `"4.7.2.stable.official"`.
  - `api.load_dump(cache_dir: str | None = None) -> dict` — cached parsed JSON, regenerated when the version changes.
  - `api.lookup_class(name: str, member: str | None = None) -> dict | None` with keys `name`, `inherits`, `inheritance_chain`, `brief_description`, `description`, `methods`, `properties`, `signals`; when `member` is given, also `member` holding that one entry.
  - `api.search_classes(query: str, limit: int = 25) -> list[dict]` with keys `name`, `inherits`, `brief_description`.

- [ ] **Step 1: Write the failing tests**

Create `plugins/godot/scripts/test/test_api.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import api, engine

HAS_GODOT = engine.find_binary() is not None

FAKE_DUMP = {
    "header": {"version_full_name": "Godot Engine v4.7.2.stable.official"},
    "classes": [
        {"name": "Object", "inherits": None, "brief_description": "Base class.",
         "description": "", "methods": [], "properties": [], "signals": []},
        {"name": "Node", "inherits": "Object", "brief_description": "Base class for scene objects.",
         "description": "", "methods": [{"name": "add_child", "description": "Adds a child."}],
         "properties": [], "signals": [{"name": "ready", "description": "Emitted when ready."}]},
        {"name": "Node2D", "inherits": "Node", "brief_description": "A 2D game object.",
         "description": "", "methods": [], "properties": [], "signals": []},
        {"name": "CharacterBody2D", "inherits": "PhysicsBody2D",
         "brief_description": "A 2D physics body specialized for characters moved by script.",
         "description": "", "methods": [], "properties": [], "signals": []},
    ],
}


class TestLookupAndSearch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        api._CACHE.clear()
        (Path(self.tmp) / "extension_api.json").write_text(json.dumps(FAKE_DUMP))
        (Path(self.tmp) / "VERSION").write_text("Godot Engine v4.7.2.stable.official")

    def test_lookup_returns_inheritance_chain(self):
        found = api.lookup_class("Node2D", cache_dir=self.tmp)
        self.assertEqual(found["inheritance_chain"], ["Node", "Object"])

    def test_lookup_is_case_insensitive(self):
        self.assertIsNotNone(api.lookup_class("node2d", cache_dir=self.tmp))

    def test_lookup_unknown_class_returns_none(self):
        self.assertIsNone(api.lookup_class("NoSuchClass", cache_dir=self.tmp))

    def test_lookup_single_member(self):
        found = api.lookup_class("Node", member="add_child", cache_dir=self.tmp)
        self.assertEqual(found["member"]["name"], "add_child")

    def test_search_matches_brief_description(self):
        hits = api.search_classes("characters moved by script", cache_dir=self.tmp)
        self.assertEqual(hits[0]["name"], "CharacterBody2D")

    def test_search_matches_name(self):
        names = [h["name"] for h in api.search_classes("node2d", cache_dir=self.tmp)]
        self.assertIn("Node2D", names)


@unittest.skipUnless(HAS_GODOT, "godot not on PATH")
class TestAgainstRealEngine(unittest.TestCase):
    def test_dump_is_generated_and_cached_by_version(self):
        tmp = tempfile.mkdtemp()
        api._CACHE.clear()
        dump = api.load_dump(cache_dir=tmp)
        self.assertGreater(len(dump["classes"]), 500)
        self.assertTrue((Path(tmp) / "extension_api.json").is_file())

    def test_real_class_carries_documentation(self):
        tmp = tempfile.mkdtemp()
        api._CACHE.clear()
        found = api.lookup_class("CharacterBody2D", cache_dir=tmp)
        self.assertIn("character", (found["brief_description"] or "").lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_api -v`
Expected: FAIL with `ImportError: cannot import name 'api'`

- [ ] **Step 3: Implement**

Create `plugins/godot/scripts/godot/api.py`:

```python
"""Serve Godot's class reference from the user's own engine binary.

`--dump-extension-api-with-docs` emits every class with its brief description,
full description, methods, properties and signals — about 12 MB for 4.7.2. It
is generated from whatever engine the user actually has, so answers stay
correct across versions without vendoring 29 MB of class reference that would
go stale (spec decision 7).

The dump is written to the cache directory and reused until the engine version
changes. Generating it costs about two seconds.
"""

from __future__ import annotations

import json
import os

from . import engine

_CACHE: dict = {}


def _default_cache_dir() -> str:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    path = os.path.join(base, "claude-godot-plugin")
    os.makedirs(path, exist_ok=True)
    return path


def engine_version() -> str:
    result = engine.run(["--version"], timeout=15)
    return (result.stdout or result.stderr).strip().splitlines()[0].strip()


def load_dump(cache_dir: str | None = None) -> dict:
    cache_dir = cache_dir or _default_cache_dir()
    if cache_dir in _CACHE:
        return _CACHE[cache_dir]

    dump_path = os.path.join(cache_dir, "extension_api.json")
    version_path = os.path.join(cache_dir, "VERSION")

    current = None
    if os.path.isfile(dump_path) and os.path.isfile(version_path):
        cached_version = open(version_path).read().strip()
        try:
            current = engine_version()
        except engine.MissingBinary:
            current = cached_version  # Serve the cache when the binary is gone.
        if cached_version != current:
            os.remove(dump_path)

    if not os.path.isfile(dump_path):
        os.makedirs(cache_dir, exist_ok=True)
        engine.run(
            ["--headless", "--dump-extension-api-with-docs"],
            cwd=cache_dir,
            timeout=120,
        )
        if not os.path.isfile(dump_path):
            raise RuntimeError("Godot did not produce extension_api.json")
        open(version_path, "w").write(current or engine_version())

    dump = json.load(open(dump_path))
    _CACHE[cache_dir] = dump
    return dump


def _by_name(dump: dict) -> dict:
    return {c["name"].lower(): c for c in dump.get("classes", [])}


def lookup_class(name: str, member: str | None = None, cache_dir: str | None = None):
    dump = load_dump(cache_dir)
    index = _by_name(dump)
    found = index.get((name or "").lower())
    if not found:
        return None

    chain = []
    parent = found.get("inherits")
    while parent:
        chain.append(parent)
        parent = (index.get(parent.lower()) or {}).get("inherits")

    out = {
        "name": found["name"],
        "inherits": found.get("inherits"),
        "inheritance_chain": chain,
        "brief_description": found.get("brief_description"),
        "description": found.get("description"),
        "methods": found.get("methods", []),
        "properties": found.get("properties", []),
        "signals": found.get("signals", []),
    }

    if member:
        needle = member.lower()
        for group in ("methods", "properties", "signals"):
            for entry in out[group]:
                if entry.get("name", "").lower() == needle:
                    out["member"] = entry
                    out["member_kind"] = group
                    return out
        out["member"] = None
    return out


def search_classes(query: str, limit: int = 25, cache_dir: str | None = None) -> list:
    dump = load_dump(cache_dir)
    needle = (query or "").lower()
    scored = []
    for entry in dump.get("classes", []):
        name = entry.get("name", "")
        brief = entry.get("brief_description") or ""
        if needle in name.lower():
            score = 0 if name.lower() == needle else 1
        elif needle in brief.lower():
            score = 2
        else:
            continue
        scored.append((score, name, {
            "name": name,
            "inherits": entry.get("inherits"),
            "brief_description": brief,
        }))
    scored.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in scored[:limit]]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_api -v`
Expected: PASS, 8 tests with Godot installed.

- [ ] **Step 5: Commit**

```bash
git add plugins/godot/scripts
git commit -m "Serve the class reference from the user's own engine binary, cached by version"
```

---

### Task 7: The renderer-backed drivers

Implements spec §3.3 and §3.5. Both driver scripts live outside the project and write nothing into it.

**Files:**
- Create: `plugins/godot/scripts/godot/drivers/screenshot.gd`
- Create: `plugins/godot/scripts/godot/drivers/shadercheck.gd`
- Create: `plugins/godot/scripts/godot/render.py`
- Create: `plugins/godot/scripts/test/test_render.py`
- Create: `plugins/godot/scripts/test/fixtures/sample-project/good.gdshader`
- Create: `plugins/godot/scripts/test/fixtures/sample-project/bad.gdshader`

**Interfaces:**
- Consumes: `engine.run`, `engine.diagnostics`, `engine.find_binary`.
- Produces:
  - `render.screenshot_scene(root, scene, out_path, width=800, height=600, frames=4, timeout=90) -> dict` with keys `path`, `diagnostics`, `timed_out`.
  - `render.check_shader(root, shader_res_path, timeout=60) -> list[dict]` — `engine.diagnostics` entries.
  - `render.NoDisplay(Exception)`.

- [ ] **Step 1: Write the shader fixtures**

```bash
cd plugins/godot/scripts/test/fixtures/sample-project
cat > good.gdshader <<'EOF'
shader_type canvas_item;

void fragment() {
	COLOR = vec4(1.0, 0.0, 0.0, 1.0);
}
EOF
cat > bad.gdshader <<'EOF'
shader_type canvas_item;

void fragment() {
	COLOR = vec4(1.0, 0.0, 0.0);
}
EOF
```

- [ ] **Step 2: Write the driver scripts**

Create `plugins/godot/scripts/godot/drivers/screenshot.gd`:

```gdscript
# Runs as the MainLoop via `--script`, from OUTSIDE the project being captured.
# Nothing is written into the user's project: the scene path and the output path
# both arrive by environment variable, and the PNG is saved to an absolute path.
#
# Headless cannot do this — the dummy renderer returns a null viewport texture
# (spec 3.2), so this driver must run windowed. The caller positions the window
# offscreen.
extends SceneTree

func _initialize() -> void:
	var scene_path := OS.get_environment("GODOT_MCP_SCENE")
	var out_path := OS.get_environment("GODOT_MCP_OUT")
	var frames := int(OS.get_environment("GODOT_MCP_FRAMES"))
	if frames <= 0:
		frames = 4

	var err := change_scene_to_file(scene_path)
	if err != OK:
		printerr("GODOT_MCP_ERROR: could not load scene ", scene_path)
		quit(1)
		return

	for _i in range(frames):
		await process_frame
	await RenderingServer.frame_post_draw

	var image := root.get_texture().get_image()
	if image == null:
		printerr("GODOT_MCP_ERROR: viewport texture was null (headless?)")
		quit(1)
		return

	var save_err := image.save_png(out_path)
	if save_err != OK:
		printerr("GODOT_MCP_ERROR: could not write ", out_path)
		quit(1)
		return

	print("GODOT_MCP_OK ", image.get_size().x, "x", image.get_size().y)
	quit()
```

Create `plugins/godot/scripts/godot/drivers/shadercheck.gd`:

```gdscript
# Compiles one shader under a real renderer and lets Godot print its own errors.
#
# Loading a .gdshader headless reports nothing even when the shader cannot
# compile (spec 3.5), because compilation happens in the rendering server and
# headless installs a dummy one. Assigning the shader to a material on a real
# ColorRect forces the compile, and SHADER ERROR lines reach stderr.
extends SceneTree

func _initialize() -> void:
	var shader_path := OS.get_environment("GODOT_MCP_SHADER")
	var shader := load(shader_path)
	if shader == null:
		printerr("GODOT_MCP_ERROR: could not load ", shader_path)
		quit(1)
		return

	var rect := ColorRect.new()
	rect.size = Vector2(64, 64)
	root.add_child(rect)

	var material := ShaderMaterial.new()
	material.shader = shader
	rect.material = material

	await process_frame
	await RenderingServer.frame_post_draw

	print("GODOT_MCP_OK")
	quit()
```

- [ ] **Step 3: Write the failing tests**

Create `plugins/godot/scripts/test/test_render.py`:

```python
import os
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import engine, render

SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"
HAS_GODOT = engine.find_binary() is not None
HAS_DISPLAY = HAS_GODOT and render.has_display()


class TestDriversExist(unittest.TestCase):
    def test_driver_scripts_are_packaged(self):
        self.assertTrue(render.DRIVER_SCREENSHOT.is_file())
        self.assertTrue(render.DRIVER_SHADER.is_file())


@unittest.skipUnless(HAS_DISPLAY, "needs godot and a display")
class TestShaderCheck(unittest.TestCase):
    def test_good_shader_reports_nothing(self):
        self.assertEqual(render.check_shader(str(SAMPLE), "res://good.gdshader"), [])

    def test_broken_shader_is_reported(self):
        # Spec 3.5: the headless path passes this silently. This test is the
        # guard against anyone "optimising" check_shader to run headless.
        found = render.check_shader(str(SAMPLE), "res://bad.gdshader")
        self.assertTrue(found)
        self.assertTrue(any(d["severity"] == "SHADER ERROR" for d in found))
        self.assertTrue(any(d.get("line") == 4 for d in found))

    def test_headless_really_does_pass_the_broken_shader(self):
        result = engine.run(
            ["--headless", "--path", str(SAMPLE), "--quit-after", "2"], timeout=30
        )
        self.assertFalse(
            [d for d in engine.diagnostics(result.stderr) if d["severity"] == "SHADER ERROR"]
        )


@unittest.skipUnless(HAS_DISPLAY, "needs godot and a display")
class TestScreenshot(unittest.TestCase):
    def test_captures_a_non_empty_png_without_touching_the_project(self):
        before = sorted(p.name for p in SAMPLE.iterdir())
        out = Path(tempfile.mkdtemp()) / "shot.png"
        result = render.screenshot_scene(str(SAMPLE), "res://main.tscn", str(out))
        self.assertTrue(out.is_file())
        self.assertGreater(out.stat().st_size, 100)
        self.assertEqual(result["path"], str(out))
        after = sorted(p.name for p in SAMPLE.iterdir())
        created = set(after) - set(before)
        self.assertTrue(
            created <= {".godot"} or all(c.endswith(".uid") for c in created),
            f"screenshot wrote unexpected files into the project: {created}",
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_render -v`
Expected: FAIL with `ImportError: cannot import name 'render'`

- [ ] **Step 5: Implement**

Create `plugins/godot/scripts/godot/render.py`:

```python
"""Renderer-backed operations: screenshots and shader validation.

Both need a real rendering device. Headless installs a dummy one, which returns
a null viewport texture (spec 3.2) and compiles no shaders (spec 3.5), so both
operations run windowed with the window positioned far offscreen.

Both drive the engine through a GDScript file that lives in this package rather
than in the user's project, so nothing is written into the project being
inspected.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from . import engine

DRIVERS = Path(__file__).parent / "drivers"
DRIVER_SCREENSHOT = DRIVERS / "screenshot.gd"
DRIVER_SHADER = DRIVERS / "shadercheck.gd"

# Far enough offscreen that the window does not appear on any real display.
OFFSCREEN = "5000,5000"


class NoDisplay(Exception):
    pass


def has_display() -> bool:
    if sys.platform == "darwin" or sys.platform.startswith("win"):
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _require_display():
    if not has_display():
        raise NoDisplay(
            "This operation needs a real rendering device and no display is "
            "available. Headless Godot returns a null viewport and compiles no "
            "shaders, so it cannot substitute."
        )


def _drive(driver: Path, root: str, env: dict, width=800, height=600, timeout=90):
    _require_display()
    previous = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        return engine.run(
            [
                "--path", root,
                "--script", str(driver),
                "--resolution", f"{width}x{height}",
                "--position", OFFSCREEN,
            ],
            timeout=timeout,
        )
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def screenshot_scene(root, scene, out_path, width=800, height=600, frames=4, timeout=90):
    result = _drive(
        DRIVER_SCREENSHOT,
        root,
        {
            "GODOT_MCP_SCENE": scene,
            "GODOT_MCP_OUT": os.path.abspath(out_path),
            "GODOT_MCP_FRAMES": str(frames),
        },
        width=width,
        height=height,
        timeout=timeout,
    )
    return {
        "path": os.path.abspath(out_path) if os.path.isfile(out_path) else None,
        "diagnostics": engine.diagnostics(result.stderr),
        "timed_out": result.timed_out,
    }


def check_shader(root, shader_res_path, timeout=60):
    result = _drive(
        DRIVER_SHADER,
        root,
        {"GODOT_MCP_SHADER": shader_res_path},
        width=64,
        height=64,
        timeout=timeout,
    )
    return [
        d
        for d in engine.diagnostics(result.stderr)
        if d["severity"] in ("SHADER ERROR", "ERROR") and (d["file"] or "").endswith(".gdshader")
    ]
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_render -v`
Expected: PASS. If `test_broken_shader_is_reported` fails with an empty list, the driver ran headless — check that `--headless` is absent from the argument list.

- [ ] **Step 7: Commit**

```bash
git add plugins/godot/scripts
git commit -m "Add renderer-backed screenshot and shader validation, driven from outside the project"
```

---

### Task 8: The MCP server

Thin JSON-RPC wiring. No business logic lives here.

**Files:**
- Create: `plugins/godot/scripts/godot_mcp_server.py`
- Create: `plugins/godot/.mcp.json`
- Create: `plugins/godot/scripts/test/test_server.py`

**Interfaces:**
- Consumes: every module from Tasks 2–7.
- Produces: a stdio JSON-RPC 2.0 server exposing nine tools: `project_overview`, `scene_tree`, `reference_graph`, `check_script`, `run_scene`, `check_shader`, `screenshot_scene`, `lookup_class`, `search_classes`.

- [ ] **Step 1: Write the failing tests**

Create `plugins/godot/scripts/test/test_server.py`:

```python
import json
import subprocess
import unittest
from pathlib import Path

SERVER = Path(__file__).resolve().parents[1] / "godot_mcp_server.py"
SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"


def rpc(*messages):
    payload = "".join(json.dumps(m) + "\n" for m in messages)
    proc = subprocess.run(
        ["python3", str(SERVER)], input=payload, capture_output=True, text=True, timeout=180
    )
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def call(name, arguments):
    responses = rpc(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": name, "arguments": arguments}},
    )
    return responses[-1]


class TestProtocol(unittest.TestCase):
    def test_initialize_reports_server_info(self):
        responses = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "godot")

    def test_tools_list_exposes_nine_tools(self):
        responses = rpc(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        names = {t["name"] for t in responses[-1]["result"]["tools"]}
        self.assertEqual(
            names,
            {"project_overview", "scene_tree", "reference_graph", "check_script",
             "run_scene", "check_shader", "screenshot_scene", "lookup_class",
             "search_classes"},
        )

    def test_every_tool_declares_a_description_and_schema(self):
        responses = rpc(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        for tool in responses[-1]["result"]["tools"]:
            self.assertTrue(tool.get("description"), tool["name"])
            self.assertIn("inputSchema", tool)

    def test_unknown_tool_is_an_error_not_a_crash(self):
        response = call("no_such_tool", {})
        self.assertTrue(response["result"].get("isError"))


class TestParserToolsNeedNoBinary(unittest.TestCase):
    """Spec decision 16: these three answer without a Godot install."""

    def test_project_overview(self):
        response = call("project_overview", {"project_path": str(SAMPLE)})
        text = response["result"]["content"][0]["text"]
        self.assertIn("Sample", text)
        self.assertFalse(response["result"].get("isError"))

    def test_scene_tree(self):
        response = call("scene_tree", {"scene_path": str(SAMPLE / "main.tscn")})
        self.assertIn("Main", response["result"]["content"][0]["text"])

    def test_reference_graph(self):
        response = call("reference_graph", {"project_path": str(SAMPLE)})
        self.assertFalse(response["result"].get("isError"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_server -v`
Expected: FAIL — the server file does not exist.

- [ ] **Step 3: Implement the server**

Create `plugins/godot/scripts/godot_mcp_server.py`:

```python
#!/usr/bin/env python3
"""MCP server for Godot 4 projects.

Speaks JSON-RPC 2.0 over stdio using only the standard library, so the plugin
needs no install step.

Design notes:
  - Read-only with respect to project source. No tool creates, edits, or saves
    a project file. Every mutation an agent makes goes through Edit/Write/Bash,
    which is what keeps it visible to the guard hook.
  - project_overview, scene_tree and reference_graph never invoke the Godot
    binary, so a project can still be described on a machine with no engine.
  - check_shader and screenshot_scene need a real rendering device. Headless
    returns a null viewport and compiles no shaders, so it cannot substitute.
  - Running Godot against a project creates .godot/ and .uid artifacts. That is
    normal import behaviour, not something this server writes.
"""

import json
import os
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from godot import api, engine, project, refs, render, tscn

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "godot", "version": "0.1.0"}

_PROJECT = {"type": "string", "description": "Absolute path to the project directory (contains project.godot)."}

TOOLS = [
    {
        "name": "project_overview",
        "description": "Summarise a Godot project: name, engine features, main scene, autoloads, input actions, rendering method, and export presets. Parses project.godot and export_presets.cfg directly and does not need the Godot binary.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT}, "required": ["project_path"]},
    },
    {
        "name": "scene_tree",
        "description": "Show the node hierarchy of a .tscn file with node types, attached scripts, key properties, and the external resources it references. Parses the file directly and does not need the Godot binary or the editor.",
        "inputSchema": {"type": "object", "properties": {"scene_path": {"type": "string", "description": "Absolute path to a .tscn or .tres file."}}, "required": ["scene_path"]},
    },
    {
        "name": "reference_graph",
        "description": "Report broken uid:// and res:// references, orphaned files, and duplicate UIDs across a project. Catches the case where a script was moved without its .uid sidecar, which no reimport can repair. Does not need the Godot binary.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT}, "required": ["project_path"]},
    },
    {
        "name": "check_script",
        "description": "Parse and type-check one GDScript file, returning diagnostics with file and line. Note that Godot's own --check-only exits 0 even when a script has parse errors, so this reads the diagnostics rather than the exit status.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT, "script_path": {"type": "string", "description": "Path to the .gd file, relative to the project root."}}, "required": ["project_path", "script_path"]},
    },
    {
        "name": "run_scene",
        "description": "Run a scene headlessly for a bounded number of frames and return its output together with any runtime errors and their GDScript backtraces. Rendering is disabled in this mode; use screenshot_scene to see what a scene looks like.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT, "scene": {"type": "string", "description": "Scene to run, e.g. res://main.tscn. Defaults to the project's main scene."}, "frames": {"type": "integer", "description": "Frames to run before quitting. Default 120."}}, "required": ["project_path"]},
    },
    {
        "name": "check_shader",
        "description": "Compile a .gdshader under a real renderer and report compilation errors with line numbers. Requires a display: compiling headlessly reports success even for shaders that cannot compile. Compilation stops at the first error, so fixing shaders is iterative.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT, "shader_path": {"type": "string", "description": "Shader to compile, e.g. res://water.gdshader."}}, "required": ["project_path", "shader_path"]},
    },
    {
        "name": "screenshot_scene",
        "description": "Render a scene and save a PNG of it. Runs the game windowed but positioned offscreen, driven by a script outside the project, so nothing is written into the project. Requires a display.",
        "inputSchema": {"type": "object", "properties": {"project_path": _PROJECT, "scene": {"type": "string", "description": "Scene to capture, e.g. res://main.tscn."}, "out_path": {"type": "string", "description": "Absolute path for the PNG. Defaults to a temporary file."}, "width": {"type": "integer"}, "height": {"type": "integer"}, "frames": {"type": "integer", "description": "Frames to advance before capturing. Default 4."}}, "required": ["project_path", "scene"]},
    },
    {
        "name": "lookup_class",
        "description": "Look up a Godot class: its inheritance chain, description, methods, properties, and signals, optionally narrowed to one member. Generated from the user's own engine binary, so it matches their Godot version exactly.",
        "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "description": "Class name, e.g. CharacterBody2D."}, "member": {"type": "string", "description": "Optional method, property, or signal name."}}, "required": ["name"]},
    },
    {
        "name": "search_classes",
        "description": "Find Godot classes by name or by what they do, searching class names and brief descriptions. Use when the right node type for a job is unknown.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]},
    },
]


def _node_lines(node, depth=0):
    if node is None:
        return ["(no root node)"]
    label = f"{'  ' * depth}- {node.name}"
    if node.type:
        label += f" [{node.type}]"
    if node.instance:
        label += f" (instance {node.instance})"
    if "script" in node.props:
        label += f" script={node.props['script']}"
    lines = [label]
    for child in node.children:
        lines.extend(_node_lines(child, depth + 1))
    return lines


def call_tool(name, args):
    if name == "project_overview":
        return True, json.dumps(project.overview(args["project_path"]), indent=2)

    if name == "scene_tree":
        text = open(args["scene_path"], errors="replace").read()
        blocks = tscn.parse(text)
        root = tscn.scene_tree(blocks)
        out = ["# Nodes", *_node_lines(root), "", "# External resources"]
        for res in tscn.ext_resources(blocks) or []:
            out.append(f"- {res['type']} {res['path']} ({res['uid']})")
        return True, "\n".join(out)

    if name == "reference_graph":
        return True, json.dumps(refs.graph(args["project_path"]), indent=2)

    if name == "check_script":
        found = engine.check_script(args["project_path"], args["script_path"])
        if not found:
            return True, "No diagnostics. The script parses and type-checks."
        return True, json.dumps(found, indent=2)

    if name == "run_scene":
        result = engine.run_scene(
            args["project_path"], args.get("scene"), int(args.get("frames", 120))
        )
        return True, json.dumps(result, indent=2)

    if name == "check_shader":
        found = render.check_shader(args["project_path"], args["shader_path"])
        if not found:
            return True, "Shader compiled with no errors."
        return True, json.dumps(found, indent=2)

    if name == "screenshot_scene":
        out_path = args.get("out_path") or os.path.join(
            tempfile.mkdtemp(prefix="godot-shot-"), "scene.png"
        )
        result = render.screenshot_scene(
            args["project_path"],
            args["scene"],
            out_path,
            width=int(args.get("width", 800)),
            height=int(args.get("height", 600)),
            frames=int(args.get("frames", 4)),
        )
        if not result["path"]:
            return False, "No image was produced.\n" + json.dumps(result, indent=2)
        return True, json.dumps(result, indent=2)

    if name == "lookup_class":
        found = api.lookup_class(args["name"], args.get("member"))
        if not found:
            return False, f"No such class: {args['name']}"
        return True, json.dumps(found, indent=2)[:60000]

    if name == "search_classes":
        return True, json.dumps(
            api.search_classes(args["query"], int(args.get("limit", 25))), indent=2
        )

    return False, f"Unknown tool: {name}"


def respond(request_id, result=None, error=None):
    message = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        message["error"] = error
    else:
        message["result"] = result
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = message.get("method")
        request_id = message.get("id")

        if method == "initialize":
            respond(request_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            })
        elif method in ("notifications/initialized", "notifications/cancelled"):
            continue
        elif method == "ping":
            respond(request_id, {})
        elif method == "tools/list":
            respond(request_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = message.get("params") or {}
            try:
                ok, text = call_tool(params.get("name", ""), params.get("arguments") or {})
            except engine.MissingBinary as exc:
                ok, text = False, str(exc)
            except render.NoDisplay as exc:
                ok, text = False, str(exc)
            except tscn.TscnParseError as exc:
                ok, text = False, f"Could not parse the scene file: {exc}"
            except Exception:
                ok, text = False, traceback.format_exc(limit=3)
            result = {"content": [{"type": "text", "text": text}]}
            if not ok:
                result["isError"] = True
            respond(request_id, result)
        elif request_id is not None:
            respond(request_id, error={"code": -32601, "message": f"Method not found: {method}"})


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Write the MCP registration**

```bash
cat > plugins/godot/.mcp.json <<'EOF'
{
  "mcpServers": {
    "godot": {
      "command": "python3",
      "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/godot_mcp_server.py"],
      "env": {
        "GODOT_BIN": "${user_config.godot_bin}"
      }
    }
  }
}
EOF
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_server -v`
Expected: PASS, 7 tests.

- [ ] **Step 6: Verify the server loads in a real session**

Run: `claude --plugin-dir plugins/godot -p "Use the godot MCP server to give me a project overview of plugins/godot/scripts/test/fixtures/sample-project"`
Expected: the response names the project `Sample` and lists its two autoloads.

- [ ] **Step 7: Run the gates and commit**

```bash
bun test && bun run audit
git add plugins/godot
git commit -m "Expose the Godot project tools over stdio JSON-RPC"
```

---

### Task 9: The guard hook

**Files:**
- Create: `plugins/godot/hooks/hooks.json`
- Create: `plugins/godot/hooks/scripts/godot-guard.sh`
- Create: `plugins/godot/scripts/test/test_guard.py`

**Interfaces:**
- Consumes: nothing.
- Produces: a `PreToolUse` handler reading the hook JSON payload on stdin and emitting `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny"|"ask","permissionDecisionReason":"..."}}`, or exiting 0 silently to allow.

- [ ] **Step 1: Write the failing tests**

Create `plugins/godot/scripts/test/test_guard.py`:

```python
import json
import subprocess
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parents[2] / "hooks" / "scripts" / "godot-guard.sh"

CASES = [
    # (command, expected decision)
    # --- deny: unrepairable -------------------------------------------------
    ("mv scripts/player.gd entities/player.gd", "deny"),
    ("git mv src/enemy.gd actors/enemy.gd", "deny"),
    ("mv water.gdshader shaders/water.gdshader", "deny"),
    ("godot --headless --path . --convert-3to4", "deny"),
    # --- allow: the sidecar travels too ------------------------------------
    ("mv scripts/player.gd entities/player.gd && mv scripts/player.gd.uid entities/player.gd.uid", "allow"),
    ("mv scripts/ entities/", "allow"),
    ("git mv scripts entities", "allow"),
    # --- allow: uid lives inside the file -----------------------------------
    ("mv main.tscn scenes/main.tscn", "allow"),
    ("mv theme.tres ui/theme.tres", "allow"),
    # --- allow: regenerable -------------------------------------------------
    ("rm -rf .godot", "allow"),
    ("rm -rf .godot/imported", "allow"),
    # Spec 3.8: UIDs are path-derived, so deleting a sidecar in place
    # regenerates the identical UID. Denying these would be noise.
    ("rm scripts/player.gd.uid", "allow"),
    ("rm -f assets/hero.png.import", "allow"),
    ("rm assets/hero.png.import && godot --headless --import", "allow"),
    # --- ask: recoverable from git -----------------------------------------
    ("rm scripts/player.gd", "ask"),
    ("rm main.tscn", "ask"),
    ("rm project.godot", "ask"),
    ("rm export_presets.cfg", "ask"),
    # --- allow: ordinary work ----------------------------------------------
    ("godot --headless --path . --check-only --script main.gd", "allow"),
    ("ls scripts/", "allow"),
    ("cat scripts/player.gd", "allow"),
    ("grep -rn 'uid://' .", "allow"),
    ("godot --headless --path . --export-release macOS builds/game.dmg", "allow"),
    ("git status", "allow"),
]


def decide(command):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    proc = subprocess.run(
        ["bash", str(GUARD)], input=payload, capture_output=True, text=True, timeout=10
    )
    out = proc.stdout.strip()
    if not out:
        return "allow"
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"]


class TestGuard(unittest.TestCase):
    def test_decision_table(self):
        failures = []
        for command, expected in CASES:
            actual = decide(command)
            if actual != expected:
                failures.append(f"{command!r}: expected {expected}, got {actual}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_permits_godot_cache_removal(self):
        # A guard that fires on harmless operations gets disabled, and then it
        # protects nothing. .godot/ is regenerated by --import.
        self.assertEqual(decide("rm -rf .godot"), "allow")

    def test_deny_message_explains_the_fix(self):
        payload = json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "mv a.gd b/a.gd"}}
        )
        proc = subprocess.run(
            ["bash", str(GUARD)], input=payload, capture_output=True, text=True, timeout=10
        )
        reason = json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn(".uid", reason)

    def test_non_bash_tools_are_ignored(self):
        payload = json.dumps({"tool_name": "Read", "tool_input": {"file_path": "a.gd"}})
        proc = subprocess.run(
            ["bash", str(GUARD)], input=payload, capture_output=True, text=True, timeout=10
        )
        self.assertEqual(proc.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_guard -v`
Expected: FAIL — the guard script does not exist.

- [ ] **Step 3: Implement the guard**

Create `plugins/godot/hooks/scripts/godot-guard.sh`:

```bash
#!/usr/bin/env bash
#
# PreToolUse guard for Bash commands touching a Godot project.
#
#   deny  — breaks uid:// identity with no repair. Godot tracks files by UID, and
#           where the UID lives depends on the file type (measured, spec 3.7):
#             .gd, .gdshader      a .uid sidecar beside the file
#             imported assets     a .import sidecar carrying uid=
#             .tscn, .tres        inline, inside the file
#           Moving a sidecar-bearing file without its sidecar puts it at a new
#           path, so the next import mints a new UID while every existing
#           reference still names the old one. No reimport reconciles that; it is
#           repaired by hand. Measured both ways in spec 3.4 and 3.8.
#   ask   — recoverable from git, but orphans references until it is.
#   allow — everything else, silently. UIDs are derived from the path (measured,
#           spec 3.8), so deleting a .uid or .import IN PLACE regenerates the
#           identical UID and is harmless; only a move changes the path. Directory
#           moves are safe too, because the sidecars travel inside the directory.
#           A guard that fires on safe operations gets turned off, and then it
#           protects nothing — including the one rule that matters.

set -uo pipefail

# Fail open when jq is absent. A guard that errors on every Bash call is worse
# than one that occasionally does not fire.
command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$input" 2>/dev/null) || exit 0
[[ "$tool" != "Bash" ]] && exit 0

cmd=$(jq -r '.tool_input.command // empty' <<<"$input" 2>/dev/null) || exit 0
[[ -z "$cmd" ]] && exit 0

norm=$(printf '%s' "$cmd" | tr '\n\t' '  ' | tr -s ' ')

decide() {
  jq -nc --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:$d,permissionDecisionReason:$r}}'
  exit 0
}

SIDECAR_SRC='\.(gd|gdshader)\b'
ASSET='\.(png|jpg|jpeg|webp|svg|wav|ogg|mp3|glb|gltf|fbx|obj|ttf|otf)\b'

# --- deny: identity loss with no repair --------------------------------------

# A move naming a sidecar-bearing file, where the sidecar is not also named.
if [[ "$norm" =~ (^|[^a-zA-Z])(git[[:space:]]+)?mv[[:space:]] ]] \
   && [[ "$norm" =~ $SIDECAR_SRC ]] \
   && [[ ! "$norm" =~ \.uid ]]; then
  decide deny "This moves a .gd or .gdshader file without its .uid sidecar. Godot keeps that file's identity in the sidecar: move the file alone and the next import mints a new UID, while every scene referencing it still names the old one. No reimport reconciles that — the references are repaired by hand, one at a time. Move both (for example 'mv a.gd b/a.gd && mv a.gd.uid b/a.gd.uid') and then run 'godot --headless --path . --import', or do the move in the Godot editor, which handles the sidecar for you. Moving the whole directory is also safe. If this command was only being quoted or searched for, run that lookup yourself — the guard reads command text and cannot tell a mention from an invocation."
fi

# A move naming an imported asset, where its .import is not also named.
if [[ "$norm" =~ (^|[^a-zA-Z])(git[[:space:]]+)?mv[[:space:]] ]] \
   && [[ "$norm" =~ $ASSET ]] \
   && [[ ! "$norm" =~ \.import ]]; then
  decide deny "This moves an imported asset without its .import sidecar, which is where Godot stores that asset's uid://. Moving the asset alone gives it a new UID on reimport while existing references keep the old one, and no reimport reconciles the two. Move both files, or move the containing directory, or do it in the editor. If you were only quoting this command, run that lookup yourself — the guard matches on text alone."
fi

if [[ "$norm" =~ --convert-3to4 ]]; then
  decide deny "--convert-3to4 rewrites every file in the project in place, and there is no undo. Confirm the project is committed to git or otherwise backed up, then let the user run it themselves. To see what it would change without changing anything, use --validate-conversion-3to4, which is read-only."
fi

# --- ask: recoverable from git, but breaks references until it is ------------

if [[ "$norm" =~ (^|[^a-zA-Z])rm[[:space:]].*\.(tscn|tres|gd|gdshader)([[:space:]]|$) ]]; then
  decide ask "Deleting a scene, resource, or script orphans every uid:// reference pointing at it. Nothing reports the breakage at deletion time — it surfaces later as a scene that will not load. Check what references it first with the reference_graph MCP tool. The file itself is recoverable from git if it was committed."
fi

if [[ "$norm" =~ (^|[^a-zA-Z])rm[[:space:]].*(project\.godot|export_presets\.cfg)([[:space:]]|$) ]]; then
  decide ask "This removes a project-level configuration file. project.godot defines the project itself — autoloads, input map, rendering settings — and export_presets.cfg holds every export configuration including signing settings. Neither is regenerated, and both are recoverable only from git."
fi

exit 0
```

- [ ] **Step 4: Register the hook**

```bash
cat > plugins/godot/hooks/hooks.json <<'EOF'
{
  "description": "Blocks the file operations that break uid:// references unrepairably, asks before deletions that orphan references, and reports GDScript parse errors after an edit",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash",
            "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/scripts/godot-guard.sh"],
            "timeout": 5
          }
        ]
      }
    ]
  }
}
EOF
chmod +x plugins/godot/hooks/scripts/godot-guard.sh
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_guard -v`
Expected: PASS, 4 tests. The decision table reports every mismatch at once, so a failure names each wrong row.

- [ ] **Step 6: Commit**

```bash
bun test && bun run audit
git add plugins/godot
git commit -m "Guard the file operations that break uid:// references unrepairably"
```

---

### Task 10: The advisory GDScript check hook

**Files:**
- Create: `plugins/godot/hooks/scripts/check-gdscript.sh`
- Modify: `plugins/godot/hooks/hooks.json`
- Create: `plugins/godot/scripts/test/test_check_hook.py`

**Interfaces:**
- Consumes: the `godot` binary when present.
- Produces: a `PostToolUse` handler emitting `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"..."}}` and always exiting 0.

- [ ] **Step 1: Write the failing tests**

Create `plugins/godot/scripts/test/test_check_hook.py`:

```python
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godot import engine

HOOK = Path(__file__).resolve().parents[2] / "hooks" / "scripts" / "check-gdscript.sh"
SAMPLE = Path(__file__).parent / "fixtures" / "sample-project"
HAS_GODOT = engine.find_binary() is not None


def run_hook(file_path, env=None):
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}})
    merged = dict(os.environ)
    if env:
        merged.update(env)
    proc = subprocess.run(
        ["bash", str(HOOK)], input=payload, capture_output=True, text=True,
        timeout=60, env=merged,
    )
    return proc


class TestAlwaysAdvisory(unittest.TestCase):
    def test_always_exits_zero(self):
        self.assertEqual(run_hook("/tmp/nowhere.gd").returncode, 0)

    def test_non_gd_files_produce_no_output(self):
        self.assertEqual(run_hook(SAMPLE / "main.tscn").stdout.strip(), "")

    def test_file_outside_a_project_produces_no_output(self):
        tmp = Path(tempfile.mkdtemp()) / "loose.gd"
        tmp.write_text("extends Node\n")
        self.assertEqual(run_hook(tmp).stdout.strip(), "")

    def test_missing_binary_is_silent(self):
        proc = run_hook(SAMPLE / "broken.gd", env={"GODOT_BIN": "/nonexistent/godot-x"})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")


@unittest.skipUnless(HAS_GODOT, "godot not on PATH")
class TestWithEngine(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "proj"
        shutil.copytree(SAMPLE, self.root)
        subprocess.run(
            [engine.find_binary(), "--headless", "--path", str(self.root), "--import"],
            capture_output=True, timeout=180,
        )

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_broken_script_produces_advisory_context(self):
        proc = run_hook(self.root / "broken.gd")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("broken.gd", context)
        self.assertIn("5", context)

    def test_clean_script_produces_no_output(self):
        proc = run_hook(self.root / "scripts" / "player.gd")
        self.assertEqual(proc.stdout.strip(), "")

    def test_unimported_project_stays_silent(self):
        # Without .godot/, a class_name from another file reports a false error.
        shutil.rmtree(self.root / ".godot", ignore_errors=True)
        proc = run_hook(self.root / "broken.gd")
        self.assertEqual(proc.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_check_hook -v`
Expected: FAIL — the hook script does not exist.

- [ ] **Step 3: Implement the hook**

Create `plugins/godot/hooks/scripts/check-gdscript.sh`:

```bash
#!/usr/bin/env bash
#
# PostToolUse handler. Reports GDScript parse and type errors in a .gd file
# Claude just edited.
#
# Advisory by design: always exits 0 and emits additionalContext rather than a
# decision. Game projects sit in deliberately broken intermediate states — a
# script referencing a node that is not in the scene yet is ordinary
# mid-refactor work — so blocking here would fight how the work is done.
#
# The reason this exists at all: `godot --check-only` exits 0 even when the
# script has parse errors, so the obvious safety check passes broken code
# silently. The diagnostics are only on stderr.
#
# Stays quiet in three cases, each of which would otherwise cry wolf:
#   - the edited file is not a .gd
#   - it is not inside a Godot project
#   - the project has no .godot/ cache, because a script referencing a
#     class_name defined elsewhere reports a spurious error before first import

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)
file=$(jq -r '.tool_input.file_path // .tool_input.path // empty' <<<"$input" 2>/dev/null) || exit 0
[[ -z "$file" ]] && exit 0
[[ "$file" != *.gd ]] && exit 0
[[ -f "$file" ]] || exit 0

godot_bin="${GODOT_BIN:-}"
if [[ -z "$godot_bin" ]]; then
  godot_bin=$(command -v godot 2>/dev/null || command -v godot4 2>/dev/null || true)
fi
if [[ -z "$godot_bin" && -x "/Applications/Godot.app/Contents/MacOS/Godot" ]]; then
  godot_bin="/Applications/Godot.app/Contents/MacOS/Godot"
fi
[[ -x "$godot_bin" ]] || exit 0

# Walk up for project.godot.
dir=$(cd "$(dirname "$file")" && pwd)
root=""
while [[ "$dir" != "/" ]]; do
  if [[ -f "$dir/project.godot" ]]; then root="$dir"; break; fi
  dir=$(dirname "$dir")
done
[[ -z "$root" ]] && exit 0

# Before the first import there is no global class cache, so cross-file
# class_name references report errors that are not real.
[[ -d "$root/.godot" ]] || exit 0

rel="${file#"$root"/}"
errors=$("$godot_bin" --headless --path "$root" --check-only --script "$rel" 2>&1 >/dev/null \
  | grep -E '^(SCRIPT ERROR|ERROR):|^\s+at: .*\(res://' || true)

[[ -z "$errors" ]] && exit 0

jq -nc --arg m "godot --check-only reports errors in $rel (note: its exit code is 0 regardless, so these come from stderr):

$errors" \
  '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$m}}'
exit 0
```

- [ ] **Step 4: Register the hook**

Replace `plugins/godot/hooks/hooks.json` with:

```json
{
  "description": "Blocks the file operations that break uid:// references unrepairably, asks before deletions that orphan references, and reports GDScript parse errors after an edit",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash",
            "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/scripts/godot-guard.sh"],
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash",
            "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/scripts/check-gdscript.sh"],
            "timeout": 20
          }
        ]
      }
    ]
  }
}
```

Then: `chmod +x plugins/godot/hooks/scripts/check-gdscript.sh`

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd plugins/godot/scripts && python3 -m unittest test.test_check_hook -v`
Expected: PASS, 7 tests with Godot installed.

- [ ] **Step 6: Commit**

```bash
bun test && bun run audit
git add plugins/godot
git commit -m "Report GDScript errors after an edit, since --check-only's exit code cannot"
```

---

### Task 11: The `godot-scene-files` skill

**Files:**
- Create: `plugins/godot/skills/godot-scene-files/SKILL.md`
- Create: `plugins/godot/skills/godot-scene-files/references/tscn-format.md`
- Create: `plugins/godot/skills/godot-scene-files/references/uid-and-identity.md`
- Create: `plugins/godot/skills/godot-scene-files/references/import-pipeline.md`
- Create: `plugins/godot/skills/godot-scene-files/evals/triggers.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: the MCP tools `scene_tree` and `reference_graph`; the vendored `godot-docs/file_formats/tscn.rst`.
- Produces: the skill every other Godot skill points at for scene-structure questions.

- [ ] **Step 1: Write the skill**

Invoke `meta-skills:authoring-skills` first. Frontmatter, exactly:

```yaml
---
name: godot-scene-files
description: Works with Godot's .tscn and .tres files and the uid:// identity system underneath them — the file grammar and its five sections, what ext_resource and sub_resource mean, when hand-editing a scene is safe and when it corrupts the project, the .uid and .import sidecars, and diagnosing broken or orphaned references. Use when a scene will not load, a resource reference is broken, files need moving or renaming inside a project, a .tscn needs reading or editing directly, or import artifacts need explaining. For writing the GDScript a scene attaches, use gdscript; for running or screenshotting a scene, use godot-testing-and-debugging.
license: MIT
compatibility: Godot 4.x. Reference diagnosis uses the bundled MCP server, which needs no Godot binary for this skill's tools.
---
```

The body must carry these five things, each of which was measured rather than assumed (spec §3.4, §3.7):

1. **Where identity lives, by file type** — the table from spec §3.7: `.gd`/`.gdshader` use a `.uid` sidecar, imported assets use `.import` carrying `uid=`, and `.tscn`/`.tres` carry it inline in the heading.
2. **The move rule.** Moving a sidecar-bearing file *with* its sidecar is recoverable — the `.tscn` keeps naming the old path but resolves through the UID, and `--import` reconciles it. Moving it *without* the sidecar is unrepairable: the file gets a new UID, every reference still names the old one, and no reimport fixes it. Show both commands.
3. **The five sections** of a `.tscn` in order — file descriptor, external resources, internal resources, nodes, connections — and that `load_steps` is deprecated as of 4.6 and should be ignored where present.
4. **When to hand-edit and when not to.** Safe: reading, changing a scalar property, fixing a path. Unsafe: renumbering resource ids, reordering nodes, editing anything binary-ish.
5. **The diagnosis flow**: `reference_graph` first, then `scene_tree` on the scene that failed, and what each `reason` value means.

- [ ] **Step 2: Write the references**

- `references/tscn-format.md` — the full grammar with a worked example of each section, pointing at `${CLAUDE_PLUGIN_ROOT}/godot-docs/file_formats/tscn.rst` for the verbatim source.
- `references/uid-and-identity.md` — sidecars, the move failure with both commands, duplicate UIDs, and what `--import` does and does not repair.
- `references/import-pipeline.md` — `.import` files, the `.godot/imported/` cache, why `.godot/` is safe to delete, and reimport triggers.

- [ ] **Step 3: Write the trigger evals**

Should fire: "my scene won't load after I renamed a file", "what is uid:// in this tscn", "can I move these scripts into a subfolder". Should not fire: "add static types to this script" (`gdscript`), "run the game and show me a screenshot" (`godot-testing-and-debugging`).

- [ ] **Step 4: Update the README row**

The skills column for the `godot` row must now read: `` `gdscript` `godot-scene-files` ``

- [ ] **Step 5: Run the gates and commit**

```bash
bun test && bun run audit && claude plugin validate plugins/godot --strict
git add plugins/godot README.md
git commit -m "Add the godot-scene-files skill covering .tscn structure and uid identity"
```

---

### Task 12: The `godot-project-architecture` skill

**Files:**
- Create: `plugins/godot/skills/godot-project-architecture/SKILL.md`
- Create: `plugins/godot/skills/godot-project-architecture/references/nodes-scenes-resources.md`
- Create: `plugins/godot/skills/godot-project-architecture/references/autoloads-and-signals.md`
- Create: `plugins/godot/skills/godot-project-architecture/references/project-organization.md`
- Create: `plugins/godot/skills/godot-project-architecture/references/saving-and-data.md`
- Create: `plugins/godot/skills/godot-project-architecture/evals/triggers.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: MCP `project_overview`; vendored `godot-docs/best_practices/`.
- Produces: the skill other skills point at for structural decisions.

- [ ] **Step 1: Write the skill**

Invoke `meta-skills:authoring-skills` first. Frontmatter, exactly:

```yaml
---
name: godot-project-architecture
description: Decides how a Godot project is structured — when something should be a node, a scene, a script, or a resource, when an autoload is the right answer and when it is a global variable in disguise, signals versus direct calls, how scenes should be composed and organized on disk, saving and serializing game data, version control setup, and upgrading a project between Godot versions. Use when starting a project, deciding where new functionality belongs, reviewing how a project is laid out, or untangling scenes that know too much about each other. For the file format underneath scenes, use godot-scene-files; for the code inside them, use gdscript.
license: MIT
compatibility: Godot 4.x.
---
```

The body must cover: the four-way node/scene/script/resource decision with a concrete rule for each; the autoload question framed as "does this need to outlive every scene, and does anything else need to know it exists"; signals up, calls down; scene composition and the owner concept; and what `getting_started/` teaches about the node/scene model without reproducing its tutorials.

- [ ] **Step 2: Write the references**

- `references/nodes-scenes-resources.md` — the decision, `scenes_versus_scripts.rst` and `node_alternatives.rst` distilled, with the cases where a `Resource` beats a node.
- `references/autoloads-and-signals.md` — `autoloads_versus_regular_nodes.rst` and `instancing_with_signals.rst`, plus groups and the `godot_notifications.rst` callback order.
- `references/project-organization.md` — folder layout, naming, `version_control_systems.rst` including what belongs in `.gitignore` (`.godot/`, exported builds) and what must be committed (`.uid` sidecars, `.import` files).
- `references/saving-and-data.md` — `io/` distilled: save games, `user://`, serialization choices, and `data_preferences.rst`.

- [ ] **Step 3: Write the trigger evals**

Should fire: "should this be an autoload", "how should I organize this project", "how do I save the player's progress". Should not fire: "why is my tscn corrupt" (`godot-scene-files`), "what does this warning mean" (`gdscript`).

- [ ] **Step 4: Update the README row and run the gates**

Skills column: `` `gdscript` `godot-project-architecture` `godot-scene-files` `` (alphabetical — `bun run audit` compares against sorted directory names).

```bash
bun test && bun run audit
git add plugins/godot README.md
git commit -m "Add the godot-project-architecture skill"
```

---

### Task 13: The `godot-testing-and-debugging` skill

**Files:**
- Create: `plugins/godot/skills/godot-testing-and-debugging/SKILL.md`
- Create: `plugins/godot/skills/godot-testing-and-debugging/references/verify-loop.md`
- Create: `plugins/godot/skills/godot-testing-and-debugging/references/test-frameworks.md`
- Create: `plugins/godot/skills/godot-testing-and-debugging/references/debugging-and-profiling.md`
- Create: `plugins/godot/skills/godot-testing-and-debugging/evals/triggers.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: MCP `check_script`, `run_scene`, `screenshot_scene`, `check_shader`; vendored `godot-docs/editor/command_line_tutorial.rst`.
- Produces: the skill other skills point at for "does it actually work".

- [ ] **Step 1: Write the skill**

Invoke `meta-skills:authoring-skills` first. Frontmatter, exactly:

```yaml
---
name: godot-testing-and-debugging
description: Verifies that a Godot project actually works — checking scripts and shaders for errors, running scenes headlessly, capturing screenshots of what a scene renders, writing unit tests with GUT or gdUnit4, reading the debugger and profiler, and interpreting the engine's own error output. Use when something should be run, tested, or proven to work, when an error message needs interpreting, when a scene behaves wrongly at runtime, or when a change needs visual confirmation. For what the error means about the code itself, use gdscript; for what it means about the scene file, use godot-scene-files.
license: MIT
compatibility: Godot 4.x on PATH or at GODOT_BIN. Screenshots and shader checking need a display. GUT and gdUnit4 are optional project addons and are never assumed installed.
---
```

The body must carry these, all measured (spec §3.1, §3.2, §3.3, §3.5):

1. **Never trust the exit code.** `--check-only` exits `0` on parse errors. State it plainly and early; it is the single most consequential fact in the skill.
2. **Headless renders nothing.** `--headless` installs a dummy rendering server: no screenshots, and shaders silently do not compile. So a headless shader check reports success on code that cannot compile.
3. **The verify ladder**, cheapest first: `check_script` (~130 ms) → `run_scene` headless for logic → `screenshot_scene` for pixels → `check_shader` for shaders.
4. **GUT and gdUnit4 are optional.** The zero-install baseline is `check_script` plus `run_scene`; introduce a framework only when the project already has one or the user asks.
5. **Reading engine output**: `SCRIPT ERROR` versus `ERROR`, GDScript backtraces, and that a `.cpp` location in an `at:` line is engine source, not the user's file.

- [ ] **Step 2: Write the references**

- `references/verify-loop.md` — the ladder with exact MCP calls and the CLI equivalents, plus the exit-code trap with its measured evidence.
- `references/test-frameworks.md` — GUT and gdUnit4: installing, writing a first test, running headless in CI, and choosing between them.
- `references/debugging-and-profiling.md` — the debugger panel, the profiler, custom performance monitors, `logging.rst`, and the `--debug-*` visualisation flags from the vendored CLI reference.

- [ ] **Step 3: Write the trigger evals**

Should fire: "run my game and tell me if it errors", "show me what this scene looks like", "how do I write unit tests in Godot", "my shader isn't working". Should not fire: "add type hints" (`gdscript`), "should this be an autoload" (`godot-project-architecture`).

- [ ] **Step 4: Update the README row and run the gates**

Skills column: `` `gdscript` `godot-project-architecture` `godot-scene-files` `godot-testing-and-debugging` ``

```bash
bun test && bun run audit
git add plugins/godot README.md
git commit -m "Add the godot-testing-and-debugging skill"
```

---

### Task 14: Final verification and documentation

**Files:**
- Modify: `plugins/godot/README.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: everything above.
- Produces: a plugin that passes all three gates and documents its own limits.

- [ ] **Step 1: Complete the plugin README**

`plugins/godot/README.md` must state, each in its own short section:

- The four skills and what each is for.
- The nine MCP tools in a table, with columns for whether each needs the Godot binary and whether each needs a display.
- **Why the server is read-only** (spec decision 4): every mutation goes through `Edit`/`Write`/`Bash` so the guard hook can see it. A future `save_scene` tool would be a mutation path no hook can observe.
- The two hooks, what the guard denies and asks about, and that the check hook is advisory.
- That running Godot creates `.godot/` and `.uid` artifacts, which are normal.
- That `godot-docs/` is verbatim and must never be edited, with a pointer to its `VERSION`.
- Local development: `cd plugins/godot/scripts && python3 -m unittest discover -s test`, and `claude --plugin-dir plugins/godot`.

- [ ] **Step 2: Verify every tool against the real engine**

Run each of these and confirm the described result:

```bash
cd /Users/michaelfrenchfultonjr/Projects/agent-tools/plugins/godot/scripts
S=test/fixtures/sample-project
python3 -c "
import sys; sys.path.insert(0,'.')
from godot import project, refs, engine, api, render, tscn
print('overview:', project.overview('$S')['name'])
print('refs broken:', refs.graph('$S')['broken'])
print('check clean:', engine.check_script('$S','scripts/player.gd'))
print('check broken:', len(engine.check_script('$S','broken.gd')), 'diagnostics')
print('lookup:', api.lookup_class('CharacterBody2D')['inherits'])
print('search:', [c['name'] for c in api.search_classes('tilemap')][:3])
print('shader ok:', render.check_shader('$S','res://good.gdshader'))
print('shader bad:', len(render.check_shader('$S','res://bad.gdshader')), 'errors')
"
```

Expected: `overview: Sample`; `refs broken: []`; `check clean: []`; `check broken: 3 diagnostics`; `lookup: PhysicsBody2D`; a non-empty search list; `shader ok: []`; `shader bad: 1 errors`.

- [ ] **Step 3: Run the full gate set**

```bash
cd /Users/michaelfrenchfultonjr/Projects/agent-tools
bun test
bun run audit
claude plugin validate plugins/godot --strict
claude plugin validate .
```

Expected: all four pass. Record the `bun run audit:strict` warning count for comparison later; it is not a gate.

- [ ] **Step 4: Install and exercise the plugin end to end**

```bash
claude --plugin-dir plugins/godot -p "What does the godot plugin's reference_graph tool report for plugins/godot/scripts/test/fixtures/sample-project, and what would happen if I moved scripts/player.gd without its .uid file?"
```

Expected: the answer reports no broken references and explains the sidecar failure — confirming both the MCP server and the skill content are reachable.

- [ ] **Step 5: Commit**

```bash
git add plugins/godot README.md
git commit -m "Document the godot plugin's tools, limits, and local development loop"
```

---

## Self-Review

**Spec coverage.**

| Spec section | Task |
|---|---|
| §3.1 exit code trap | 5 (implementation), 10 (hook), 13 (skill) |
| §3.2 headless renders nothing | 7, 13 |
| §3.3 windowed capture | 7 |
| §3.4 sidecar-less move | 4, 9, 11 |
| §3.5 shader silence | 7, 13 |
| §3.6 no `timeout(1)` | 5 |
| §3.7 identity by file type | 4, 9, 11 |
| §4 what ships | 1, 8, 9, 10, 14 |
| §5 nine MCP tools | 2–8 |
| §5.2 `.tscn` parser | 2 |
| §6.1 guard | 9 |
| §6.2 check hook | 10 |
| §7.1 four spine skills | 1, 11, 12, 13 |
| §7.4 coverage map (`io/`, `math/`, `migrating/`) | 12 (`io/`, `migrating/`), 1 (`math/` in `gdscript`) |
| §8 portability | 1 (no dependencies), 8 (stdlib only) |
| §9 verification | 2 (bun gate), 14 |

Sections 7.2 and 7.3 — the thirteen subsystem and language skills — are deliberately out of this plan's scope and belong to the follow-up plan.

**Type consistency.** `engine.diagnostics` returns dicts keyed `severity`/`message`/`file`/`line`, consumed unchanged by `check_script`, `run_scene`, `render.check_shader`, and the server. `refs.graph` returns `uid_index`/`broken`/`orphans`/`duplicate_uids`, matching its tests and the server's passthrough. `tscn.Block` exposes `kind`/`attrs`/`props`/`line_no` and `tscn.Node` exposes `name`/`type`/`parent`/`instance`/`props`/`children`/`path`, used by `refs` and by the server's `_node_lines`. `project.overview` keys match Task 3's assertions and the server.

**Known gap, stated rather than hidden.** Task 3 Step 4 instructs adding the `export_presets.cfg` merge immediately after the `cfg = parse_cfg(...)` line rather than showing the final file twice. An implementer reading only that step must place it correctly or `test_export_presets` fails with a `KeyError`; the test failure names the problem directly.
