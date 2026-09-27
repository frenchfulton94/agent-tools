# A Godot game development plugin

Date: 2026-09-26
Status: approved design, awaiting implementation plan

## 1. Goal

A new `godot` plugin giving Claude Code broad, grounded support for developing
games in Godot 4.x: seventeen skills spanning the engine's feature surface and
all three of its languages, a bundled MCP server that reads and verifies a
Godot project without a running editor, and two hooks that close the engine's
silent failure modes.

Coverage is broad but not total. Section 7.4 maps every documentation area to
a skill or records why it is excluded; XR is the one game-facing area
deliberately deferred, and engine-contribution documentation is out of scope.

The plugin is portable. It declares no dependency on any other plugin and
references no skill outside itself.

Grounding is split deliberately: prose guidance is distilled into
`references/*.md`, a narrow slice of Godot's own documentation is vendored
verbatim where paraphrasing would be dangerous, and the class reference is
served live from the user's own engine binary rather than vendored at all.

Authored against Godot 4.7, verified against 4.7.2.stable on macOS.

## 2. Decision log

Each row records a decision made during design. A later change to one of these
reopens the design; it is not an implementation detail.

| # | Decision |
|---|---|
| 1 | Broad coverage of Godot's feature surface, not a narrow spine. The plugin is a catalog plugin in the shape of `apple-studio`, not a project-specific one. |
| 2 | All three languages ship: GDScript as the default idiom, C# and GDExtension/C++ as dedicated skills. YAGNI was raised against GDExtension and overruled; it ships as a full skill. |
| 3 | The MCP server reads and verifies. It never mutates project source. No editor addon, no LSP/DAP proxy. |
| 4 | Every mutation stays on `Edit`/`Write`/`Bash` so the guard hook can see it. An MCP tool that writes project files would be a mutation path no hook in this catalog can observe. This is a safety property, not a convenience choice. |
| 5 | Hooks are a `PreToolUse` guard plus an advisory `PostToolUse` GDScript check. No `Stop` gate: game projects sit in deliberately broken intermediate states far more often than Swift apps, and a gate that fires on intentional states gets disabled. |
| 6 | Subprocess results are classified by parsing stderr, never by exit code. Verified: `--check-only` exits `0` on a script with three parse errors. |
| 7 | The class reference is never vendored. `--dump-extension-api-with-docs` generates it from the user's own binary, keyed by engine version, so it is correct for whatever Godot they run. |
| 8 | A narrow slice of prose documentation is vendored verbatim, limited to exact material that paraphrasing corrupts: the `.tscn` grammar, the CLI flag tables, the GDScript style/typing/warning references, export and feature tags, and best practices. |
| 9 | Skills are decomposed as spine plus consolidated subsystems, preserving subsystem-shaped triggering. Workflow-phase naming was rejected because vague descriptions are the documented cause of skills that never fire. |
| 10 | Seventeen skills, all in v0.1.0. `godot-performance` was added after `tutorials/performance/` proved to fit neither the 3D nor the testing skill. |
| 11 | The Godot editor-tooling skill is named `godot-editor-tooling`, not `godot-editor-plugins`, to avoid a triggering collision with `meta-skills:authoring-plugins`, which ships from the same catalog. |
| 12 | Zero runtime references to skills outside this plugin, and no `dependencies` array in the manifest. |
| 13 | No LSP is written for GDScript or GDShader. GDScript's ships in the editor; an LSP serves a human's editor, and Claude Code has no LSP client. |
| 14 | `check_shader` exists because `--check-only` is GDScript-only and headless shader loading silently passes broken shaders. |
| 15 | The MCP server is Python, following `unraid-ops`, so the plugin does not require Bun on a machine that only wants Godot support. |
| 16 | `project_overview`, `scene_tree`, and `reference_graph` are pure parsers requiring no Godot binary. This is a tested property, not an accident. |
| 17 | The server uses the Python standard library only, speaking JSON-RPC 2.0 over stdio, following `unraid-ops`. No `mcp` package, no pip install step. A plugin that needs a dependency installed before its tools work is not portable. |
| 18 | Python tests use `unittest` and are gated by `bun test` through `tests/godot-scripts.test.ts`, following `para`. The repository has no pytest. |

## 3. Verified engine behavior

Every finding below was measured against Godot 4.7.2.stable on macOS during
design. They are load-bearing: the MCP server and both hooks are built on
them, and each has a corresponding test so a regression is caught rather than
inferred.

### 3.1 `--check-only` exits 0 on broken scripts

A script with three parse errors returned exit code `0`, identical to a clean
script. Errors appear on stderr:

    SCRIPT ERROR: Parse Error: Cannot assign a value of type "String" as "int".
              at: GDScript::reload (res://bad.gd:3)

**Consequence.** The natural safety check — run it, test `$?` — passes broken
code silently. Every subprocess wrapper in the server and in hook 2 classifies
by parsing stderr for `SCRIPT ERROR:`, `ERROR:`, and `Parse Error:` with their
`res://file.gd:LINE` locations. A fixture that is known broken is asserted to
be reported broken, pinning the contract against a later "simplification" to
`returncode`.

### 3.2 Headless mode renders nothing

`--headless` uses a dummy rendering server. `get_viewport().get_texture()`
returns null, and `--write-movie` under `--headless` produced a 44-byte `.wav`
and no frames.

**Consequence.** No visual verification is possible headless.

### 3.3 A windowed run captures real pixels with no addon and no project writes

Running non-headless at `--position 5000,5000` (offscreen), with a driver
script that `extends SceneTree` living **outside the project**, loading the
target scene, awaiting `RenderingServer.frame_post_draw`, and saving through
`get_viewport().get_texture().get_image().save_png()` to an external path,
produced a correct screenshot of the scene.

**Consequence.** The visual feedback loop needs neither a running editor nor an
addon installed into the user's project, and writes nothing into it. This is
what made the editor-bridge MCP option unnecessary.

### 3.4 Moving a file with its `.uid` sidecar is recoverable; without it is not

Moving `player.gd` together with `player.gd.uid` broke the runtime load, but a
subsequent `--import` pass repaired it — the `.tscn` still named the old path,
yet the scene resolved correctly through the UID.

Moving `player.gd` **without** its sidecar was unrepairable: the file received
a new UID (`uid://cbm7rcrqysjkg`), the scene still referenced the old one
(`uid://cnnyipgx21jca`), and no import pass reconciled them.

**Consequence.** This is the precise destructive operation the guard blocks.
Blocking all moves would be wrong and noisy; blocking a move that orphans the
sidecar is exact.

### 3.7 Only some file types have UID sidecars

Measured by importing projects and listing what Godot generated:

| Type | Identity carrier |
|---|---|
| `.gd`, `.gdshader` | A `.uid` sidecar file next to it |
| Imported assets (`.png`, `.wav`, ...) | A `.import` sidecar carrying `uid=` |
| `.tscn`, `.tres` | Inline, in the `[gd_scene ...]` / `[gd_resource ...]` heading |

**Consequence.** The guard's move rule applies only to sidecar-bearing types.
Scenes and resources survive a move because their UID travels inside the file,
and a directory move carries sidecars along with their files. A rule covering
all five extensions would deny safe operations, which is how guards get
disabled.

### 3.8 UIDs are derived from the path, so only the move is destructive

Deleting a sidecar in place and reimporting regenerates the **same** UID:

| Operation | UID before | UID after |
|---|---|---|
| `rm a/s.gd.uid`, reimport | `uid://b24e2fth3n3xk` | `uid://b24e2fth3n3xk` |
| `rm hero.png.import`, reimport | `uid://dka08b7p2ntk2` | `uid://dka08b7p2ntk2` |
| `mv a/s.gd b/s.gd` without the `.uid` | `uid://bwimerv1cyist` | `uid://byx1h08w7qpq8` |
| `mv hero.png art/` without the `.import` | `uid://dka08b7p2ntk2` | `uid://badik1e5sp48k` |

**Consequence.** This narrows the guard considerably, and the narrowing matters.
Deleting a sidecar looks alarming and is harmless; moving a file is routine and
is the operation that destroys identity. A guard that denied sidecar deletion
would fire on safe work often enough to be switched off, taking the rule that
does matter with it.

### 3.5 Headless shader loading silently passes broken shaders

`load()` on a `.gdshader` with an invalid `vec4` arity returned a non-null
Shader under `--headless` and printed nothing. Under a real renderer the same
shader reported:

    E   3->  COLOR = vec4(1.0, 0.0, 0.0);
    SHADER ERROR: Invalid arguments for the built-in function: "vec4(float,float,float)".
              at: (null) (res://bad.gdshader:3)

Only the first error was reported; a second fault on line 4 was not reached.

**Consequence.** Shader validation requires a real renderer, is iterative
rather than batch, and the obvious headless approach reports success on code
that cannot compile.

### 3.6 Timings and environment

| Measurement | Value |
|---|---|
| `--check-only` on one script | 130 ms |
| `--import` on a trivial project | 1.6 s |
| `--dump-extension-api-with-docs` | 11.9 MB, ~2 s, 1,036 classes |
| `--dump-extension-api` (no docs) | 6.9 MB |
| `timeout(1)` on macOS | not present — the server owns its own deadlines |

Running Godot against a project at all creates `.godot/` and per-file `.uid`
artifacts. This is normal import behavior, conventionally gitignored, and is
disclosed in tool descriptions so it does not read as MCP-caused mutation.

## 4. What ships

    plugins/godot/
      .claude-plugin/plugin.json      name "godot", displayName "Godot", 0.1.0, no dependencies
      .mcp.json                       → scripts/godot_mcp_server.py
      README.md
      godot-docs/                     vendored verbatim slice, shared by all skills
        VERSION                       docs commit, engine version, sync date
        file_formats/tscn.rst
        editor/command_line_tutorial.rst
        gdscript/gdscript_basics.rst
        gdscript/gdscript_styleguide.rst
        gdscript/static_typing.rst
        gdscript/warning_system.rst
        gdscript/gdscript_exports.rst
        export/exporting_projects.rst
        export/feature_tags.rst
        best_practices/*.rst
      hooks/
        hooks.json
        scripts/godot-guard.sh        PreToolUse: Bash
        scripts/check-gdscript.sh     PostToolUse: Edit|Write|MultiEdit
      scripts/
        godot_mcp_server.py           thin JSON-RPC wiring over the package below
        godot/                        one module per responsibility
        test/test_*.py                unittest suites
        test/fixtures/sample-project/ a real minimal Godot project
      skills/                         17 skills, each SKILL.md + references/ + evals/triggers.md

Plus, in the repository rather than the plugin:

    tests/godot-scripts.test.ts       guard decision table + .tscn parser fixtures
    .claude-plugin/marketplace.json   new entry, category "development"
    README.md                         new row listing all 17 skills

## 5. The MCP server

Python, following `unraid-ops/scripts/unraid_mcp_server.py`: JSON-RPC 2.0 over
stdio using the standard library only, so the plugin needs no install step.
Nine tools, none of which mutate project source.

| Tool | Returns | Mechanism | Needs `godot` | Needs a display |
|---|---|---|---|---|
| `project_overview` | Engine version, main scene, autoloads, input actions, rendering method, export presets | Parses `project.godot`, `export_presets.cfg` | no | no |
| `scene_tree` | Node hierarchy with types, scripts, key properties, signal connections, external resources | Parses `.tscn` | no | no |
| `reference_graph` | Broken `uid://`/`res://` references, orphaned files, duplicate UIDs | Walks project, cross-references | no | no |
| `check_script` | `{severity, file, line, message}` diagnostics | `--headless --check-only --script`, stderr parsed | yes | no |
| `run_scene` | stdout plus runtime errors with GDScript backtraces | `--headless --quit-after N` | yes | no |
| `check_shader` | `{file, line, message}` plus marked source excerpt | External `SceneTree` driver, real renderer, offscreen | yes | **yes** |
| `screenshot_scene` | PNG path | External `SceneTree` driver, windowed offscreen | yes | **yes** |
| `lookup_class` | Inheritance chain, brief, methods, properties, signals, per-member docs | Cached `--dump-extension-api-with-docs` | yes (once) | no |
| `search_classes` | Matching classes by name and brief description | Same cache | yes (once) | no |

### 5.1 Rules the implementation holds to

1. **Never trust an exit code.** Per finding 3.1. Classification is by stderr
   parsing throughout.
2. **The server owns its timeouts.** Per finding 3.6, `timeout(1)` does not
   exist on macOS. Every subprocess gets a Python-side deadline and a kill.
   `run_scene` additionally passes `--quit-after` as a second bound, because a
   scene with no quit condition runs forever and would hang the connection.
3. **The API cache is keyed by engine version.** `lookup_class` and
   `search_classes` shell out once to `--dump-extension-api-with-docs` and
   cache the result against `godot --version`. An engine upgrade invalidates
   it automatically.
4. **Disclose real side effects.** Tool descriptions state that running Godot
   creates `.godot/` and `.uid` artifacts.
5. **Degrade with a clear message.** Missing binary yields "Godot not found,
   set `GODOT_BIN`". Missing display yields "requires a display" for the two
   renderer-dependent tools, not a raw renderer error.
6. **The first three tools never invoke Godot.** Tested, so the property
   survives someone adding a convenient version check at startup.

### 5.2 The `.tscn` parser

The only component that reimplements rather than delegates, and the only one
that can silently misread a user's project.

- Written against the vendored `tscn.rst` grammar in the same repository.
- Handles the five documented sections: file descriptor, external resources,
  internal resources, nodes, connections.
- Ignores the `load_steps` attribute, which `tscn.rst` records as deprecated
  on scenes saved before Godot 4.6.
- Handles single-line `;` comments.
- **Fails loudly rather than guessing.** An unrecognized construct returns an
  explicit parse error naming the line. A partial tree presented as complete
  is how an agent deletes a node it never saw.
- Tested against fixture scenes covering all five sections plus the
  deprecated-attribute case.

### 5.3 Explicitly out of scope for the server

Creating or modifying nodes, saving scenes, writing project files. Recorded in
the plugin README with decision 4's reasoning, so a future contributor does
not add a convenient `save_scene` without understanding its cost.

## 6. The hooks

Both authored through `meta-skills:authoring-hooks`. Both tested under
`scripts/test/`.

### 6.1 `godot-guard.sh` — `PreToolUse`, matcher `Bash`

| Pattern | Action | Grounding |
|---|---|---|
| `mv`/`git mv` of a `.gd` or `.gdshader` without its `.uid`, or of an imported asset without its `.import` | Block | Finding 3.4 — unrepairable |
| `mv` of `.tscn`/`.tres`, or of a whole directory | Allow | Scenes and resources carry their UID inline (3.7); a directory move carries sidecars with it |
| `--convert-3to4` | Block | Rewrites every file in the project in place |
| `rm` of `.tscn`/`.tres`/`.gd`/`project.godot`/`export_presets.cfg` | Ask | Recoverable from git, but orphans references |
| `rm` of a `*.uid` or `*.import` **in place** | Allow | Regenerates identically (3.8) — the file's path has not changed |
| `rm -rf .godot/` | Allow | Rebuilt by `--import` |

The permit rows matter as much as the block rows. A guard that fires on
harmless operations gets disabled, and then it protects nothing. The
`rm -rf .godot` permit is asserted in `tests/godot-scripts.test.ts`.

Block messages carry the fix, not just the refusal: move the `.uid` alongside
the file and run `--import`, or perform the move in the editor, which handles
both.

### 6.2 `check-gdscript.sh` — `PostToolUse`, matcher `Edit|Write|MultiEdit`

Fires only on `.gd` paths. Runs `--check-only` against the owning project,
parses stderr, reports diagnostics as advisory context. Never blocks:
mid-refactor breakage is normal in game work.

Required behaviors:

- Parse stderr, never the exit code (finding 3.1).
- No-op silently when `godot` is absent from `PATH`.
- Distinguish "not yet imported" from "broken": a script referencing a
  `class_name` defined elsewhere reports an error when no `.godot/` cache
  exists. The hook checks for that cache and stays silent if it is missing,
  rather than crying wolf.
- Locate the project by walking up for `project.godot`; no-op if absent.

Budget: 130 ms per finding 3.6.

## 7. The skills

Seventeen, each with `SKILL.md`, `references/*.md`, and `evals/triggers.md`.
All authored through `meta-skills:authoring-skills`.

### 7.1 Spine — always relevant, and where agents fail

| Skill | Covers | Vendored |
|---|---|---|
| `godot-project-architecture` | Node vs scene vs script vs resource; when an autoload is right and when it is a global variable in disguise; signals vs direct calls; scene and project organization; version control | `best_practices/*` |
| `godot-scene-files` | The `.tscn`/`.tres` grammar and its five sections; `uid://` and the `.uid` sidecar; the move-without-sidecar failure (3.4); the import pipeline; when to hand-edit and when not to; driving `scene_tree` and `reference_graph` | `tscn.rst` |
| `gdscript` | Language, static typing, style guide, warning system, `@export`, doc comments, format strings | `gdscript/*` |
| `godot-testing-and-debugging` | The verify loop (`check_script`, `run_scene`, `screenshot_scene`); GUT and gdUnit4 as optional additions; debugger panel; logging; custom performance monitors | `command_line_tutorial.rst` |

### 7.2 Subsystems

| Skill | Covers | Source |
|---|---|---|
| `godot-2d` | 2D nodes, sprites, tilemaps, 2D lights and shadows, particles, cameras, custom drawing | `2d/` |
| `godot-3d-and-rendering` | 3D nodes, meshes, materials, lighting, global illumination, environment and sky, the three renderers, occlusion, LOD | `3d/`, `rendering/` |
| `godot-physics-and-navigation` | Static/Rigid/Character/Area bodies, collision layers and masks, shapes, joints, casts, character controllers, physics interpolation, navmesh, agents, avoidance | `physics/`, `navigation/` |
| `godot-animation` | AnimationPlayer, AnimationTree, state machines and blend spaces, tweens, skeletons and IK, vertex animation | `animation/` |
| `godot-ui` | Control nodes, anchors and containers, themes and fonts, custom controls, localization, accessibility | `ui/`, `i18n/` |
| `godot-shaders` | Shading language, canvas_item/spatial/particle/sky shaders, visual shaders, compute shaders, screen-reading; the headless-passes-broken-shaders hazard (3.5) | `shaders/` |
| `godot-audio-and-input` | Buses and effects, 2D/3D audio players, interactive music; InputEvent, input map, actions, gamepads, haptics | `audio/`, `inputs/` |
| `godot-multiplayer` | High-level multiplayer, RPCs, spawners and synchronizers, authority, ENet/WebSocket/WebRTC, dedicated servers | `networking/` |
| `godot-performance` | Profiling-led optimization, CPU and GPU work, threading and thread-safe APIs, servers, MultiMesh | `performance/` |
| `godot-export-and-platforms` | Export presets and templates, all seven platforms, feature tags, PCK and patches, signing and notarization, CLI export | `export/`, `platform/` |

### 7.3 Extension and languages

| Skill | Covers | Source |
|---|---|---|
| `godot-csharp` | .NET setup, the documented divergences from GDScript, Variant marshalling, collections, `[Signal]`/`[Export]`, global classes, analyzer diagnostics, `--build-solutions`, export caveats | `c_sharp/` |
| `godot-gdextension` | `godot-cpp`, the SCons build system, core types, the docs system, ABI compatibility across engine versions, and when leaving GDScript is warranted | `cpp/` |
| `godot-editor-tooling` | `EditorPlugin`, `@tool` scripts, inspector and import plugins, 3D gizmos, main-screen plugins | `plugins/` |

### 7.4 Coverage map

"Broad coverage" is only checkable if every documentation area has a home.
This table accounts for all of them. Areas assigned above are omitted; these
are the ones the subsystem tables do not name directly.

| Docs area | Files | Home |
|---|---|---|
| `getting_started/` | 4 dirs | `godot-project-architecture` — the concepts; the two tutorial games are narrative and are not reproduced |
| `io/` | 6 | `godot-project-architecture` — saving games, serialization, encryption, user data paths |
| `math/` | 7 | `gdscript` — vectors, transforms, interpolation, random number generation as used from code |
| `migrating/` | 9 | `godot-project-architecture` for the general upgrade path; the 4.4 UID changes go to `godot-scene-files`, which owns UID semantics |
| `assets_pipeline/` | 14 | `godot-scene-files` — the import pipeline, `.import` files, reimporting |
| `tutorials/editor/` | 14 | `command_line_tutorial.rst` to `godot-testing-and-debugging`; `project_settings.rst` to `godot-project-architecture`. The remaining GUI-workflow files are out of scope: an agent does not drive the editor's interface |
| `tutorials/troubleshooting.rst` | 1 | `godot-testing-and-debugging` |
| `tutorials/scripting/` | ~40 | Distributed across the spine: language files to `gdscript`, `debug/` to `godot-testing-and-debugging`, `c_sharp/` and `cpp/` to their skills, the rest (scene tree, autoloads, groups, signals, resources) to `godot-project-architecture` |
| `engine_details/file_formats/` | 2 | `godot-scene-files`, vendored |
| `engine_details/` (architecture, development, engine_api) | — | **Out of scope.** These document contributing to the Godot engine itself, not building games with it |
| `tutorials/xr/` | 24 | **Deferred.** See section 11 |
| `classes/` | 1,113 | Not vendored. Served live by `lookup_class` and `search_classes` per decision 7 |

### 7.5 Cross-cutting conventions

**Triggering is the main risk at seventeen skills.** `godot-2d` and
`godot-shaders` both plausibly answer "why is my sprite the wrong color", so
`evals/triggers.md` is written deliberately for every skill rather than
discovered in use.

**Explicit hand-offs between siblings**, following
`deploying-apps-to-dokploy`. `godot-physics-and-navigation` points at
`godot-animation` for the animation half of a character controller;
`godot-3d-and-rendering` points at `godot-performance` for optimization;
everything touching `.tscn` structure points at `godot-scene-files`.

**`compatibility:` frontmatter** declares external tool requirements, using
the field established by `frontend:layerchart` and
`workflows:choosing-a-workflow`. `godot-shaders` declares the display
requirement; `godot-csharp` the .NET SDK; `godot-gdextension` SCons and a C++
toolchain.

## 8. Portability

The plugin installs and works alone.

**No runtime references to external skills.** These were considered and
rejected:

| Rejected reference | Reason |
|---|---|
| `godot-export-and-platforms` → `docker-workbench:containerizing-apps` | Containerizing a dedicated-server export is generic Docker work; the reference would make a Godot user's experience depend on an unrelated plugin |
| `godot-testing-and-debugging` → `superpowers:test-driven-development` | A different marketplace — strictly worse than an intra-catalog dependency |
| `godot-animation` → `design-engineering:animating-interfaces` | Wrong stack; Svelte/CSS motion principles do not transfer to `AnimationTree` |
| `godot-ui` → `frontend:*` | Entirely different UI system |

**No `dependencies` array** in `plugin.json`, unlike `workflows`, which
declares `meta-skills`.

**Non-skill dependencies and their degradation:**

| Dependency | Needed by | Without it |
|---|---|---|
| `godot` on `PATH` | Six MCP tools, hook 2 | Clear "not found, set `GODOT_BIN`" error; hook 2 no-ops silently; the three parser tools still work |
| A display | `check_shader`, `screenshot_scene` | Explicit "requires a display" message |
| Python 3 (stdlib only) | The server | No pip install step; `python3` alone is enough |
| GUT / gdUnit4 | `godot-testing-and-debugging` | `check_script`/`run_scene` are the zero-install baseline; the frameworks are presented as optional |
| gdtoolkit (`gdformat`/`gdlint`) | `gdscript` | Optional throughout; never assumed |
| .NET SDK | `godot-csharp` | The skill covers installing it |
| SCons + C++ toolchain | `godot-gdextension` | The skill covers the toolchain setup |

**No LSP is written.** GDScript's ships in the Godot editor on port 6005.
GDShader has none, and writing one is a compiler project serving human
editors, which is the `zed` plugin's territory. Claude Code has no LSP client,
so an LSP would not improve agent behavior. `check_shader` gives the agent
something an LSP would not: validation against the actual GPU backend rather
than a static parse.

## 9. Verification

Both gates must pass before any commit touching `plugins/`:

- **`bun test`** — registration both ways, `name` matching directory, semver
  version, identical descriptions in `plugin.json` and the marketplace entry,
  `SKILL.md` presence and frontmatter match, catalog-wide uniqueness of all 17
  new skill names, and a README row linking to a real directory.
- **`bun run audit`** — the vendored validators over every skill, plugin, and
  hook, plus the README skills column listing all 17.
- **`claude plugin validate plugins/godot --strict`** — authoritative.

**`tests/godot-scripts.test.ts`**, following `tests/para-scripts.test.ts`,
covers what is assertable without a Godot binary: the guard's full decision
table including the `rm -rf .godot` permit, and the `.tscn` parser against
fixture scenes.

**`scripts/test/*.py`** are `unittest` suites covering Godot-dependent
behavior, skipping when `godot` is absent from `PATH`, so CI without Godot stays green while a
developer with it gets full coverage. It pins findings 3.1, 3.4, and 3.5
directly: a known-broken script is asserted reported broken, a sidecar-less
move is asserted blocked, and a known-broken shader is asserted reported
broken.

Registration in `.claude-plugin/marketplace.json` and the repository README
goes through `meta-skills:maintaining-plugin-marketplaces`. Version `0.1.0`;
no `renames` entry, this being a new name.

## 10. Sequencing note for the implementation plan

Seventeen skills, nine MCP tools, two hooks, a `.tscn` parser, and a vendored
doc slice is the largest single addition this catalog has taken. The plan
should land and verify the four spine skills and the MCP server before the
thirteen remaining skills, so a defect in the parser or the stderr-parsing
contract surfaces early rather than after most of the prose is written. This
is sequencing within v0.1.0, not a scope reduction — all seventeen ship.

## 11. Deferred

Named here so later work knows they were considered, not overlooked:

- **An editor-bridge MCP addon** for editor-only state: which scene is open,
  current selection, `@tool` behavior, import dialogs. Rejected for v0.1.0 on
  distribution cost and decision 4. Revisit only if editor-state gaps show up
  in practice.
- **An LSP/DAP proxy** for breakpoint debugging with variable inspection.
  Rejected on the running-editor requirement and LSP's poor fit with MCP's
  request/response shape.
- **XR** (`tutorials/xr/`, 24 files). Not assigned to any of the seventeen
  skills. A future `godot-xr` skill.
