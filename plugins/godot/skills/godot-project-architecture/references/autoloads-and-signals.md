# Autoloads, signals, groups, and callback order

Read this for the full reasoning behind the autoload decision in SKILL.md,
the mechanics of decoupling a scene from its environment, and exactly when
each Godot lifecycle callback fires. Distilled from the vendored
`autoloads_versus_regular_nodes.rst` and `godot_notifications.rst`, plus two
files not vendored in this plugin — `tutorials/scripting/instancing_with_signals.rst`
and `tutorials/scripting/groups.rst` — marked as distilled rather than
citable against the vendored slice.

## Contents

- [The cutting-audio example in full](#the-cutting-audio-example-in-full)
- [Static alternatives to a full autoload](#static-alternatives-to-a-full-autoload)
- [Signals up: the bullet-spawning example](#signals-up-the-bullet-spawning-example)
- [Groups: a third decoupling tool](#groups-a-third-decoupling-tool)
- [Full callback order](#full-callback-order)

## The cutting-audio example in full

*(distilled from `autoloads_versus_regular_nodes.rst`, vendored)*

The scenario: a platformer plays a sound effect on coin pickup. A single
`AudioStreamPlayer` cuts its own sound off if two pickups happen close
together, so the instinctive fix is a global `Sound` autoload holding a pool
of `AudioStreamPlayer` nodes that cycle through requests — call it from
anywhere with `Sound.play("coin_pickup.ogg")`.

This works immediately and creates three specific problems:

1. **Global state.** One object now answers for every caller. If `Sound` has
   a bug, or runs out of available players, every node that plays a sound
   breaks — not just the one that triggered the failure.
2. **Global access.** Because anything can call `Sound.play(...)` from
   anywhere, a bad call's origin stops being traceable from the call site
   alone; the search space for "who caused this" is the entire project.
3. **Global resource allocation.** The pool size is a guess made once, up
   front. Too small and legitimate calls get dropped or queued; too large
   and memory is wasted on players that mostly sit idle.

Contrast with each scene keeping its own `AudioStreamPlayer` nodes: each
scene's failure surface is its own (a bug in one scene's audio can't break
another's), each bug is traceable to one or two scripts instead of the whole
project, and each scene allocates only what it actually uses. The general
form: **global access is the problem, not "needing a sound player."** Prefer
solving "needs to be reachable" by scoping it correctly (usually: keep it
inside the scene that uses it) before reaching for something globally
callable.

## Static alternatives to a full autoload

Two GDScript features solve part of what an autoload is often used for,
without registering a node:

- **`static func` with `class_name`** gives you a library of helper
  functions callable without an instance (`MyHelpers.some_func()`), but a
  static function can't reference member variables, non-static functions,
  or `self` — it's stateless by construction.
- **`static var`** (Godot 4.1+) gives you a variable shared across every
  instance of a class, without needing a separate autoload node to hold it.

Neither gives you scene-tree membership, so neither can hold `_process`
logic, participate in groups, or be found via `get_node("/root/Name")`.
Reach for a real autoload once you need those; reach for `static`
func/var when all you need is "shared code" or "shared state," not "a node
that lives in the tree."

An autoload is also, explicitly, *not* a true singleton in the design-pattern
sense: nothing stops you from instantiating additional copies of the same
scene or script elsewhere. What the Autoload mechanism actually guarantees is
narrower — the named node is added under `/root` (reachable via
`get_node("/root/Sound")`) before any other scene runs, and it survives scene
changes because `SceneTree.change_scene_to_file()` never frees the root's
other children.

## Signals up: the bullet-spawning example

*(distilled from `tutorials/scripting/instancing_with_signals.rst`, not
vendored)*

A player that shoots is the canonical case for why a child shouldn't reach
into its environment. Three approaches, in order of increasing coupling:

1. **Bullet as a child of the player.** Simplest to write
   (`add_child(bullet)`), but wrong: the bullet inherits the player's
   transform, so it visibly rotates and moves with the player instead of
   traveling in a straight line once fired.
2. **Player reaches up:** `get_parent().add_child(bullet_instance)`. Fixes
   the transform problem, but couples the player scene to whatever happens
   to be its parent at the moment. Test the `Player` scene standalone (no
   parent) and it crashes on the first shot. Change the main scene's
   structure later, and the player's assumption about "my parent is the
   right place for bullets" silently stops being true.
3. **Player emits a signal, something else decides.** The player declares
   `signal shoot(bullet, direction, location)` and emits it on input; it
   never learns what happens to the bullet afterward. Whatever scene is
   currently listening (typically the main scene) connects to `shoot` and
   does the actual `add_child()`, positioning, and velocity setup. The
   player scene now runs standalone without crashing, and the main scene's
   structure can change freely without the player needing to know.

The generalizable rule this example is standing in for: **a node should
never assume the shape of what's above it in the tree.** `get_parent()`,
`get_node("../../HUD")`, or any other upward/lateral hardcoded path is the
signal that a scene has taken on a dependency it doesn't own. Emitting a
signal and letting an ancestor connect to it inverts the dependency: the
child stays ignorant of its context, and whatever *does* know the context
(because it owns the relationship) wires the connection.

When the child genuinely needs a piece of external data rather than merely
needing to notify something, the parent should push it down instead of the
child pulling it up — in decreasing order of how loosely coupled each
technique is: connecting to one of the child's own signals to react (safest,
but only for *reacting*, not initiating); calling a method the child
exposes; assigning a `Callable` property the child then invokes (safe
because ownership of the method is never required); assigning a direct node
or `Object` reference; or assigning a `NodePath` the child resolves itself.
All five let the parent — which owns the relationship — decide what the
child depends on, rather than the child assuming it.

## Groups: a third decoupling tool

*(distilled from `tutorials/scripting/groups.rst`, not vendored)*

Groups are tags, not a hierarchy: any node can belong to any number of them,
assigned either in the editor's Groups dock or at runtime with
`add_to_group("name")`. Once tagged, `SceneTree` gives you three operations
that don't require holding a reference to the members at all:

- `get_tree().get_nodes_in_group("guards")` — the full member list, as an
  `Array`.
- `get_tree().call_group("guards", "enter_alert_mode")` — call a method on
  every member.
- Sending a notification to every member (the same mechanism `call_group`
  uses under the hood).

Groups earn their place as a distinct third tool from autoloads and signals:
they're the right answer when an unbounded, dynamic *set* of nodes needs to
be reached as a set ("every enemy currently alive," "every persistable
object") — something neither a single global reference (autoload) nor a
one-to-one signal connection expresses cleanly. The save-game pattern in
`references/saving-and-data.md` uses a `Persist` group for exactly this
reason: the set of things to save changes as the game runs, and nothing
should have to maintain a manually updated list of "things to save" in
parallel.

A group can be marked **Global** in the editor (visible and reusable across
every scene in the project) or left scoped to the current scene; both use
identical underlying logic; a name collision between a Global and a Scene
group is the same group, not two.

## Full callback order

*(the notification/callback material here is vendored in
`godot_notifications.rst`; the `_ready`-before-main-scene autoload ordering
below was verified directly against Godot 4.7.2 for this skill, not merely
read off the docs)*

**Property initialization**, in order, for one node:

1. Initial value assignment (the declared/default value; no setter runs).
2. `_init()`'s own assignments (setter runs).
3. Exported value assignment, if the node is inside a scene and the
   Inspector holds a different value (setter runs again, overwriting #2).

Instantiating a script directly (`.new()`, no scene) stops after step 2 —
there's no Inspector-driven step 3 to run.

**Tree entry**, for a scene being instantiated as part of loading the active
scene tree:

1. `_init()` cascades down the tree as each node is constructed.
2. `_enter_tree()` cascades **down**, root to leaves, once the whole
   subtree is built.
3. `_ready()` cascades **up**, leaves to root — a node's `_ready()` doesn't
   run until every one of its children has already called theirs.

Verified directly (Godot 4.7.2, a `Main` node with one `Child`):
`_init` order was Main, Child; `_enter_tree` order was Main, Child (down);
`_ready` order was Child, Main (up) — matching the vendored doc exactly.

Instantiating a *standalone* scene or a bare script (not yet added to the
running tree) only runs `_init()` — `_enter_tree()`/`_ready()` wait until
`add_child()` actually places it in the live tree.

**Autoloads relative to the main scene** — verified directly, not merely
read off the docs: autoloads are added to `/root`, in the order listed under
Project Settings → Autoload, **before** the main scene is instantiated. A
project with autoloads `AutoA`, `AutoB` and a main scene `Main` printed:

```
AutoA _init      AutoB _init      Main _init
AutoA _enter_tree  AutoB _enter_tree  Main _enter_tree
AutoA _ready       AutoB _ready       Main _ready
```

Both autoloads fully entered and became ready before `Main` did. Practical
consequence: code in any scene's `_ready()` can assume every autoload is
already live — no defensive null-checking an autoload's readiness is needed
from ordinary scene code.

**Two callbacks with no dedicated method**, useful when you need to react to
re-parenting regardless of whether it happens as part of normal scene
loading:

- `NOTIFICATION_PARENTED` — fires whenever this node is added as a child of
  another node, whether or not that's happening as part of the main scene
  loading.
- `NOTIFICATION_UNPARENTED` — fires whenever this node is removed from a
  parent.

Both come through the universal `_notification(what)` method, not a
dedicated virtual — useful for a data-centric node created and re-parented
at runtime, where you can't rely on `_enter_tree()`/`_ready()` having fired
in the usual scene-load order.

**Per-frame callbacks:** `_process(delta)` fires every frame regardless of
input, with a framerate-*dependent* `delta`; `_physics_process(delta)` fires
on a fixed step with a framerate-*independent* `delta` and is the right
place for kinematics and transforms specifically because of that fixed
step. Avoid checking input inside either — `_process`/`_physics_process`
fire every opportunity with no "rest," where `_unhandled_input(event)`
(or `_input`) fires only on frames where input actually occurred, which is
cheaper when all you need is to react to input rather than poll for it.
