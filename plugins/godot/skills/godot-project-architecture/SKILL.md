---
name: godot-project-architecture
description: Decides how a Godot project is structured — when something should be a node, a scene, a script, or a resource, when an autoload is the right answer and when it is a global variable in disguise, signals versus direct calls, how scenes should be composed and organized on disk, saving and serializing game data, version control setup, and upgrading a project between Godot versions. Use when starting a project, deciding where new functionality belongs, reviewing how a project is laid out, or untangling scenes that know too much about each other. For the file format underneath scenes, use godot-scene-files; for the code inside them, use gdscript.
license: MIT
compatibility: Godot 4.x.
---

# Godot Project Architecture

Godot's whole engine reduces to four ideas: a game is a tree of **nodes**,
grouped into **scenes**, wired together with **signals**, all inside one
**scene tree**. Every structural question in this skill — what container to
use, where to put a system, how a scene should talk to its neighbors — is one
of those four ideas applied to a specific decision. The engine's own Getting
Started series teaches this model through step-by-step tutorials; this skill
assumes you already have it and instead answers the decisions that come after
you know what a node and a scene are.

## The four-way decision: node, script alone, scene, or resource

Default to the engine's own node types until something forces you off them.
In order of increasing weight:

1. **A plain node, no script.** The built-in node already does the job
   (a `Timer`, a `Node` used purely as a non-transforming grouping point).
   Nothing to decide.

2. **A script with no scene.** Right when there's no sub-tree worth
   composing: a `class_name` helper library, an autoload's logic, a resource's
   behavior. A script instance is created identically to any other engine
   class (`MyNode.new()`); a scene instance is not (`MyScene.instantiate()`).
   That difference in API is the tell — if you're never going to compose
   children for it in the editor or reuse it as a saved arrangement, a script
   is the whole answer. Registering it with `class_name` gets it a slot (and
   optional icon) in the node/resource creation dialogs, which is worth doing
   for anything reused across scenes or handed to non-programmers.

3. **A scene.** The default the moment more than one node cooperates, or
   editor-visible composition and signal wiring matter, or the same
   arrangement gets reused in more than one place. Rule of thumb from
   upstream: a general-purpose tool used across projects leans script; a
   concept particular to *this* game leans scene, because scenes are easier
   to inspect, edit, and secure against accidental breakage than the
   equivalent built by imperative code. Scenes also process faster than the
   equivalent hand-built node tree — `PackedScene` batches creation, where a
   script rebuilding the same tree in `_init()` pays the scripting API's
   per-call cost for every node.

4. **A `Resource`.** The right container the moment the thing is data with no
   need for a tree position: no `_process`/`_physics_process`/`_input`, no
   transform, nothing that needs `add_child()`. `Resource` sits below `Node`
   on Godot's lightweight-object ladder (`Object` → `RefCounted` → `Resource`
   → `Node`, each one a little heavier and a little more capable) and adds
   exactly one thing `RefCounted` doesn't have: built-in save/load to a
   `.tres`/`.res` file and Inspector-editable properties. If you catch
   yourself building a node purely to hold exported fields that never touch
   the scene tree, that's a `Resource` wearing a `Node` costume. Custom data
   structures (a tree, a graph, a pool) that don't need serialization or
   Inspector visibility can drop a level further, to `RefCounted` or even
   bare `Object` — see `references/nodes-scenes-resources.md` for the full
   ladder, worked examples of each rung, and where a plain `Array` or
   `Dictionary` beats writing a class at all.

## Autoloads: does this need to outlive every scene, and does anything else need to know it exists

Both questions have to be "yes" before an autoload is the right tool.

- **Outlive every scene, but nothing else needs to reach it?** It doesn't
  need to be global — it needs to not get freed. A node parented somewhere
  that survives scene changes (or state written to `user://` and reloaded)
  solves "survive" without also solving "reachable from anywhere," and the
  second half is the part that costs you later.
- **Reachable from anywhere, but doesn't need to outlive the current
  scene?** Pass it down instead — a signal connection, an exported node
  reference, or a `NodePath` set by whichever parent actually owns the
  relationship. Reaching up for a global when a scene only ever runs inside
  one parent context is autoload-shaped code solving a dependency-injection
  problem.
- **Both true — outlives every scene, and several unrelated systems need
  it?** That's the autoload's actual job: a quest log, a dialogue system, an
  input-remapping table. It manages its own state and doesn't reach into
  other objects' data.

The classic failure mode is a "manager" autoload that seems obviously global
because *something* has to coordinate it — a pooled `Sound.play()` for audio
that would otherwise cut itself off mid-clip is the canonical example. It
solves the immediate problem and creates three new ones: one object now owns
every caller's correctness (a bug in the pool breaks sound for the whole
game), any code anywhere can call it so a bad call's origin is unfindable,
and the pool size is a guess — too small stutters, too big wastes memory.
Keeping the same `AudioStreamPlayer` nodes local to whichever scene actually
plays sound sidesteps all three: each scene owns its own failure surface,
bugs are local, and each allocates only what it needs.

Two escape hatches worth knowing before reaching for a full autoload node:
`static func` (with `class_name`) gives you a callable library with no
instance and no autoload registration, and `static var` (Godot 4.1+) gives
you state shared across instances of a class without a separate global node.
Neither one gets you scene-tree membership, groups, or signals — reach for
the autoload once you actually need those.

One ordering fact worth relying on: autoloads are added to the tree, in the
order listed in Project Settings, **before** the main scene loads, and their
`_ready()` fires before the main scene's `_ready()` — verified directly
against Godot 4.7.2 for this skill (two autoloads plus a main scene printed
`_init`/`_enter_tree`/`_ready` in that batch order: both autoloads fully
initialized, then the main scene). Code in a scene's `_ready()` can assume
any autoload is already live. Full callback ordering, including the
`_enter_tree` top-down / `_ready` bottom-up cascade for a scene's own
children, is in `references/autoloads-and-signals.md`.

## Signals up, calls down

A parent may call directly into a child it owns — it created that child (or
instanced that sub-scene) and knows it exists. A child should never reach
back out to its parent or the wider tree by hardcoded reference or
`NodePath` climb (`get_parent()`, `get_node("../../HUD")`). If you're about
to write that, emit a signal instead and let whichever ancestor is currently
listening decide what happens. This is what actually makes a scene reusable:
a `Player` scene that emits `shoot(bullet, direction, location)` instead of
reaching into "the main scene" to spawn a bullet still works when tested
standalone, and still works after the main scene's structure changes,
because the player never named it.

When a child genuinely needs something from outside itself, push it down
rather than letting the child reach up — connect to one of the child's
signals, call a method it exposes, or (least commonly) hand it a `Callable`,
a node reference, or a `NodePath` set by the parent that owns the
relationship. All of these keep the child ignorant of *where* the value
came from, which is what lets it be moved or reused without edits.

## Scene composition and the owner concept

Design every scene to be self-contained first, and only give it external
dependencies when reuse genuinely demands it. The common failure path is
building one large scene, then splitting pieces out once it's unwieldy —
node paths that worked inside the original scene stop resolving, and editor
signal connections silently break, because the sub-scene now runs somewhere
it didn't when those references were authored.

The **owner** property is what actually determines a scene's saved content:
a node saves into a `.tscn` file only if its `owner` is set to that scene's
root (or omitted, for the root itself). A node added at runtime and parented
into an existing tree without an owner assignment exists at runtime but
won't round-trip through a save — verified directly against Godot 4.7.2 for
this skill: a child added with `owner` set was present in the saved scene,
an otherwise-identical child left without `owner` was silently absent. This
is the mechanism, not merely a convention, so "is `owner` set correctly" is
the first thing to check when a runtime-added node mysteriously isn't in the
saved scene.

For overall tree shape: give the game an entry point (commonly a `Main`
node) with a world and a GUI branch beneath it, and put a system under an
autoload only when it truly needs global reach (see above) rather than by
default. The test for whether two nodes belong in a parent-child
relationship rather than as siblings: **would deleting the parent reasonably
mean deleting the child too?** If yes, it's a child. If the child needs to
survive independently of that parent's lifetime, it belongs elsewhere in the
tree — as a sibling, or under whatever node's lifetime it actually tracks.

## Where the rest lives

- `references/nodes-scenes-resources.md` — the full node/script/scene/resource
  ladder, `${CLAUDE_PLUGIN_ROOT}/godot-docs/best_practices/scenes_versus_scripts.rst`
  and `${CLAUDE_PLUGIN_ROOT}/godot-docs/best_practices/node_alternatives.rst`
  distilled, worked examples, and when an `Array`/`Dictionary` beats writing
  a class.
- `references/autoloads-and-signals.md` —
  `${CLAUDE_PLUGIN_ROOT}/godot-docs/best_practices/autoloads_versus_regular_nodes.rst`
  and the shooting-bullets signal example distilled in full, groups as a
  third decoupling tool, and the complete `_init`/`_enter_tree`/`_ready`/
  `_notification` callback order with the property-initialization sequence.
- `references/project-organization.md` — folder layout, the snake_case/
  PascalCase style guide, `.gdignore`, what belongs in `.gitignore` versus
  what must be committed (`.uid` and `.import` sidecars — see the note
  below), and the practical path for upgrading a project between Godot
  versions.
- `references/saving-and-data.md` — save games, `user://` versus `res://`,
  JSON versus binary serialization, `ConfigFile`, and where a project
  setting stops being the right place for a value.

For the `.tscn`/`.tres` grammar, the `uid://` identity system, and exactly
what a `.uid` or `.import` sidecar carries and how it behaves under deletion
or a sidecar-less move, use `godot-scene-files` — this skill only states
what version control needs to track (see `references/project-organization.md`),
not why. For writing the GDScript inside a node or autoload, use `gdscript`.
For running a scene headlessly or screenshotting it to check a layout,
use `godot-testing-and-debugging`.
