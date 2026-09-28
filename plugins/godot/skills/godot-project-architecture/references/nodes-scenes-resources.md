# Nodes, scenes, scripts, and resources

Read this when deciding what container a new piece of functionality or data
should live in. Distilled from the vendored `scenes_versus_scripts.rst` and
`node_alternatives.rst`, with one addition (`data_preferences.rst`'s
Array/Dictionary/Object comparison) for the case where the answer is "none
of the above — a plain collection is enough."

## Contents

- [Script versus scene](#script-versus-scene)
- [The lightweight-object ladder](#the-lightweight-object-ladder)
- [Before writing a class at all: Array or Dictionary](#before-writing-a-class-at-all-array-or-dictionary)

## Script versus scene

Both can define a reusable "class" of object in Godot, but they're not
interchangeable, and the difference is more than style:

- **API shape.** `MyNode.new()` (a plain script) is identical to
  instantiating any built-in engine class. `MyScene.instantiate()` (a scene)
  is a different call, backed by `PackedScene`. This isn't cosmetic —
  `PackedScene` stores serialized data the engine can construct in batches,
  where a script rebuilding an equivalent tree in `_init()` pays the
  scripting API's per-call overhead for every node it creates. The more
  nodes and the more complex their configuration, the more that gap costs.
- **What each can express.** A scene can define how an extended class
  initializes — its children, their properties, their signal wiring — but
  not what its behavior actually *is*. Behavior needs a script. The common
  shape is a scene providing composition and a script (attached to its root)
  providing behavior; anonymous "scene defined entirely by a script" is
  possible (it's what the editor itself does, in C++) but rare in project
  code, since it throws away the composition/behavior split that makes both
  halves easier to read.
- **Registering a type.** A script can register a name via `class_name`,
  which puts it in the node/resource creation dialogs (optionally with an
  icon) and makes its typename and static members accessible without
  loading the resource first — `MyType.SOME_CONST` works from anywhere. This
  is worth doing for anything reused across scenes, and closer to required
  for anything a designer or non-programmer will need to create without
  knowing the underlying base type.
- **Naming a scene.** You can still give a scene an effective name without
  turning it into a full type: a `RefCounted`-extending script with
  `class_name` and a `const MyScene = preload("my_scene.tscn")` acts as a
  namespace (`Game.MyScene.instantiate()`), without the scene itself
  becoming a registered type.

**Decision:** if it's a general-purpose tool meant to be reused across
projects and used by people who don't think of themselves as programmers,
lean script (with a registered name). If it's a concept particular to this
game — a level, a character, a weapon, a menu — lean scene: scenes are
easier to inspect and edit safely, and they're faster to instantiate at any
nontrivial size.

## The lightweight-object ladder

Godot gives you four base weights, each one a strict superset of the one
before, each one heavier:

| Class | Adds over the previous rung | Use when |
|---|---|---|
| `Object` | Nothing below it — the base. Manual memory management. | You're building a genuinely custom, high-volume data structure and even `RefCounted`'s bookkeeping is overhead you don't want. Rare. Example: `Tree`'s internal `TreeItem` objects. |
| `RefCounted` | Automatic memory management (frees itself once nothing references it). | The common case for a custom data class with no need to save/load or show in the Inspector. Example: `FileAccess`. |
| `Resource` | Serialization (save/load to `.tres`/`.res`) and Inspector-editable/exportable properties. | The data needs to persist to disk, be assigned in the Inspector, or be shared by reference across multiple nodes/scenes. Examples: scripts and `PackedScene` themselves, `AudioEffect` subclasses, any custom `@export`-able data bundle. |
| `Node` | Scene-tree membership: `_process`/`_physics_process`/`_input`, a transform (for `Node2D`/`Node3D`/`Control`), parenting, groups. | The thing actually needs a position in the tree, needs per-frame callbacks, or needs to be added/removed as the game runs. |

Read the table top-to-bottom as "how much am I actually going to use": a
`Node` built only to hold a few exported fields that never call
`add_child()`, never override `_process`, and never move in the tree is a
`Resource` wearing a `Node` costume — heavier for nothing. Conversely, don't
under-reach: if you do need per-frame updates or tree position, a `Resource`
can't give you that and a `Node` is correct.

`Object`'s big caveat: references to a plain `Object` can go invalid without
warning if whatever created it frees it — there's no automatic reference
counting to protect you, unlike every rung above it. Only reach this low
when you specifically want to avoid `RefCounted`'s bookkeeping cost at scale.

## Before writing a class at all: Array or Dictionary

Not every "should this be an Object" question needs an answer above the
ladder at all. Godot's `Array` (contiguous, `Vector<Variant>`-backed) and
`Dictionary` (hash-map-backed) cover most ad hoc data needs without a custom
type:

- **Array:** fastest iteration and fastest get/set *by position*; slow
  insert/erase/move except at the end; slowest at finding a value by content
  (linear scan unless you maintain sort order yourself).
- **Dictionary:** fast iteration, fast insert/erase/get/set *by key*
  (amortized constant time via hashing); still slow to find a value's key
  (no reverse index — Godot doesn't provide one).
- **Object (or above):** reach for this over a raw collection when you need
  encapsulation (the external shape shouldn't change when internals do),
  signals, or a data source callers can query without worrying whether a
  given property exists (a script or engine class's declared properties are
  a reliable contract in a way a `Dictionary` key never is).

The rule of thumb: default to `Dictionary`/`Array` for a value that's
genuinely just data passed around inline; move up to a class once callers
need behavior, guaranteed shape, or signals attached to the data itself.
