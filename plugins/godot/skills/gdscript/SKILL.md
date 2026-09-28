---
name: gdscript
description: Writes and reviews GDScript for Godot 4 — static typing and inference, the official style guide, the warning system and its configuration, @export annotations, doc comments, and format strings. Use when writing, reviewing, or fixing a .gd file, when deciding whether to annotate a type, when a GDScript warning or parse error needs interpreting, or when exporting a variable to the inspector. For the scene files a script attaches to, use godot-scene-files; for running or checking the code, use godot-testing-and-debugging.
license: MIT
compatibility: Godot 4.x. The optional gdformat/gdlint tools ship separately as gdtoolkit and are never assumed present.
---

# GDScript

GDScript is optionally typed, has its own house style, and ships a
configurable warning system most projects never turn up past the defaults.
Writing or reviewing a `.gd` file means making a call on all three — this
skill covers what each default actually is and where deviating from it costs
you.

## Type it, at least at the boundary where inference gets it wrong

Typing isn't required, but the moment your project has more than one
contributor or you'll reread this script in six months, it pays for itself:
untyped code gives you no autocomplete after a dot, no compile-time catch when
the wrong type flows into a function, and no self-documentation for the next
reader. Godot's editor makes the annotated style pleasant to write —
**Text Editor → Completion → Add Type Hints** fills in the colon for you, and
typed operations also compile to faster opcodes.

The single place this bites hardest is `@onready var x := get_node(...)`:
inference here resolves to the generic `Node`, not the node's real class,
because the scene isn't loaded yet when the compiler looks. State the type
explicitly instead of relying on `:=` for anything fetched through
`get_node()`/`$Node` — see `references/static-typing.md` for exactly why the
explicit-annotation form fails loudly (at scene load) while an `as`-cast form
fails silently (at first use, with a `null`).

Read `references/static-typing.md` before annotating a nontrivial script: it
covers `:=` vs explicit types, `as` vs `is`, the `UNSAFE_*` warnings and how to
clear them, typed arrays/dictionaries and their real limits, and the two
constructs GDScript can never type-hint at all.

## The style guide's rules that survive contact with a real diff

Godot's own script editor already applies most of the mechanical defaults
(tabs, LF, no BOM) — don't fight them. The rules worth enforcing on review are
the ones a formatter won't catch: the property/method **code order**
(`@export` before plain `var`, `_init`/`_ready` before other methods, public
before private), the **naming table** (snake_case files and members,
PascalCase classes/nodes, CONSTANT_CASE constants and enum members, past-tense
signals), and the **trailing-comma-on-multiline** convention that keeps
version-control diffs to one line per array/dict/enum edit. Full rules,
including formatting and whitespace details, are in
`references/style-and-warnings.md`.

## Warnings are mostly on — except the ones typed code needs most

The GDScript warning system lives in **Project Settings → Debug → GDScript**
(enable **Advanced Settings** to see it) and every warning is a tri-state:
Ignore, Warn, or **Error** — promoting one to Error means the project won't
run until every instance is fixed. Most warnings ship at Warn. The exception
that matters for a typed codebase: `untyped_declaration`, `unsafe_cast`,
`unsafe_property_access`, `unsafe_method_access`, and `unsafe_call_argument`
all ship at **Ignore** — if you've committed to static typing, turn these on
deliberately, or the compiler won't tell you where dynamic-style code snuck
back in.

To silence one warning without changing the project setting, use
`@warning_ignore("name")` above the line, or bracket a region with
`@warning_ignore_start("name")` / `@warning_ignore_restore("name")`. The full
warning-by-warning table — every name, its default level, and what triggers
it — is in `references/style-and-warnings.md`.

## `@export` controls the inspector widget, not just the value

An exported member needs a constant-expression default or an explicit type —
without one or the other it's a syntax error, not a warning. Beyond plain
`@export`, Godot has a dozen more specific annotations
(`@export_range`, `@export_enum`, `@export_flags`, `@export_file`,
`@export_group`, `@export_storage`, `@export_custom`, …), each of which
changes what widget the inspector renders — a slider, a drop-down, a
bitmask, a file picker — not just what gets validated. Two runtime gotchas
worth knowing before you rely on an exported value: reading it inside
`_init()` gives you the export's *default*, not what the scene file set,
because scene values apply after construction; and changing an exported value
from a `@tool` script doesn't refresh the inspector unless you call
`notify_property_list_changed()` afterward.

Every variant, its exact inspector effect, and both gotchas are in
`references/exports-and-docs.md`.

## Doc comments feed the inspector tooltip and the help window, not just a reader

A `##` comment (not `#`) immediately preceding a member becomes that member's
entry in Godot's generated class help; on an exported variable, it also
becomes the inspector tooltip. A member named with a leading underscore is
normally excluded from generated docs — unless you give it a doc comment
anyway, which documents it despite the underscore. `@deprecated` and
`@experimental` tags, and a small set of BBCode-like tags (`[method Class.name]`,
`[param name]`, `[codeblock]`, …) for cross-references and formatting, are
covered in `references/exports-and-docs.md`.

## Two ways to build a string, and where each breaks down

`"%s" % value` (a format string) and `"{0}".format([value])` both beat plain
`+` concatenation, which requires wrapping every non-string in `str()` and
gives you no control over how a number renders. Format strings support
padding, precision, and hex/octal/vector placeholders (`%10.3f`, `%x`, `%v`)
the way C's `printf` does — escape a literal `%` by doubling it (`%%`).
`String.format()` trades that numeric control for named or indexed
placeholders (`{name}`, `{0}`), which reorder more safely under translation.
Reach for `%` when you need to control a number's exact representation, and
`.format()` when the string is going to be localized or the placeholders
outnumber what's comfortable to track positionally.

## Where the rest lives

- `references/static-typing.md` — inference rules, the `get_node()` inference
  trap, `as` vs `is`, `UNSAFE_*` warnings, typed arrays/dictionaries, and
  covariance/contravariance on overridden methods.
- `references/style-and-warnings.md` — every formatting and naming rule, the
  17-item code-order list, and the full warning table (name, default, what it
  catches).
- `references/exports-and-docs.md` — every `@export` variant with its exact
  inspector effect, the two runtime-value gotchas, and doc-comment syntax
  including tags and BBCode.
- `${CLAUDE_PLUGIN_ROOT}/godot-docs/gdscript/` — the verbatim upstream source
  for everything above except the full warning table and doc-comment syntax,
  which come from the engine's `ProjectSettings` and documentation-comments
  references respectively (not vendored — see this plugin's `godot-docs/VERSION`).
