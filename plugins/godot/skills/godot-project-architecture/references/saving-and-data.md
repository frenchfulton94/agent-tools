# Saving and serializing game data

Read this when deciding how to persist player progress or settings, which
path prefix to write to, and which serialization format to reach for.
Distilled from upstream files not vendored in this plugin —
`tutorials/io/saving_games.rst` and `tutorials/io/data_paths.rst` — plus the
vendored `data_preferences.rst` for the data-structure angle. Marked
distilled versus vendored inline.

## Contents

- [res:// versus user://](#res-versus-user)
- [The Persist-group save pattern](#the-persist-group-save-pattern)
- [JSON versus binary serialization](#json-versus-binary-serialization)
- [ConfigFile for settings, not save data](#configfile-for-settings-not-save-data)

## res:// versus user://

*(distilled from `tutorials/io/data_paths.rst`, not vendored)*

- **`res://`** resolves relative to the project root (the folder containing
  `project.godot`). In an exported build this is typically read-only —
  writing here at runtime isn't guaranteed to work and shouldn't be relied
  on for anything the player generates.
- **`user://`** resolves to a per-project, guaranteed-writable directory
  outside the project tree — this is where a save file, player settings, or
  anything else generated at runtime belongs, always. Its actual location
  varies by platform (`%APPDATA%\Godot\app_userdata\<project>` on Windows,
  `~/Library/Application Support/Godot/app_userdata/<project>` on macOS,
  `~/.local/share/godot/app_userdata/<project>` on Linux by default; a
  project setting can move it to a location named directly after the game
  instead of nested under Godot's own data folder). Never hardcode any of
  these — always address it through the `user://` prefix and let the engine
  resolve it.

Use forward slashes in every path you write yourself, even on Windows —
Godot's own path handling is UNIX-style throughout and this works
everywhere; backslashes need doubling to survive as escape sequences and
are best avoided in code entirely.

## The Persist-group save pattern

*(distilled from `tutorials/io/saving_games.rst`, not vendored)*

The standard shape for saving an arbitrary, changing set of objects without
maintaining a manually-updated list of "things to save":

1. Add every node that needs to persist to a group, conventionally named
   `Persist` (editor Groups dock, or `add_to_group("Persist")` at runtime).
   See `references/autoloads-and-signals.md` for why a group — rather than
   an autoload holding references, or hardcoded node paths — is the right
   tool for an open-ended, changing set.
2. Give each persistable node its own `save()` method returning a
   `Dictionary` of exactly the fields that matter (typically including
   `scene_file_path` and the parent's path, so the object can be
   re-instantiated and re-parented on load).
3. To save: `get_tree().get_nodes_in_group("Persist")`, call `save()` on
   each, and append each result — `JSON.stringify()`-encoded, one per
   line — to a file opened at `user://savegame.save`.
4. To load: `queue_free()` every current `Persist` member first (so loading
   doesn't clone objects on top of what's already there), then read the
   save file line by line, `JSON.parse()` each line, `load()` the named
   scene, `instantiate()` and `add_child()` it at the recorded parent, and
   set every remaining field back via `Object.set(key, value)`.

The pattern's known limitation: it assumes no `Persist` object is a child of
another `Persist` object. Nested persistable objects need staged loading —
parents instantiated and added before their children look them up — because
a child's recorded `NodePath` to its parent may otherwise not resolve yet.

## JSON versus binary serialization

*(distilled from `tutorials/io/saving_games.rst`, not vendored)*

| | JSON (`JSON.stringify`/`parse`) | Binary (`FileAccess.store_var`/`get_var`) |
|---|---|---|
| File size | Larger — text format | Smaller |
| Native type support | Limited — no `Vector2`/`Vector3`/`Color`/`Rect2`/`Quaternion` etc. without manual translation to/from JSON-safe types | Handles most built-in Variant types directly |
| Custom classes | Need hand-written encode/decode logic | Still need some custom logic, but less of it |
| Debuggability | Human-readable, easy to inspect and hand-edit | Not human-readable |

Default to JSON for straightforward save state, specifically because it's
inspectable when something goes wrong during development. Move to binary
serialization once save state gets large or complex enough that file size or
manual type translation becomes the actual bottleneck — not before, since
the debuggability cost is real and paid on every future bug.

One binary-serialization caveat worth knowing before relying on it for a
custom `Resource`: only properties whose usage flags include
`PROPERTY_USAGE_STORAGE` are serialized by default. A property added purely
for runtime convenience, without that flag (or without going through
`@export`, which sets it), silently doesn't round-trip through
`store_var`/`get_var` — check `_get_property_list()` if a custom resource's
binary save is missing fields that look like they should be there.

For the *internal* data-structure question this raises — should game state
live in an `Array`, a `Dictionary`, or a custom `Object`/`Resource` before it
ever gets serialized — see the "Before writing a class at all" section of
`references/nodes-scenes-resources.md`; the same tradeoffs (iteration speed,
lookup speed, encapsulation) that decide a node's data shape decide a save
file's in-memory shape before serialization touches it at all.

## ConfigFile for settings, not save data

Player *settings* (audio volume, key bindings, display mode) are a
different problem from save *data* — Godot ships `ConfigFile` specifically
for this case: an INI-like key/value format, sectioned, with built-in
`save()`/`load()` to a `user://` path. Reach for `ConfigFile` for settings
and the Persist-group JSON/binary pattern above for actual game state;
using one pattern for both works but throws away the tool built for the
narrower job.
