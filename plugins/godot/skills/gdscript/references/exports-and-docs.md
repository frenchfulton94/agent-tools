# `@export` and doc comments

Sources: `${CLAUDE_PLUGIN_ROOT}/godot-docs/gdscript/gdscript_exports.rst` for
every `@export` variant. The doc-comment syntax below is not in the vendored
slice — it comes from the upstream `gdscript_documentation_comments.rst` page,
distilled here because a script's exported-property tooltips and its class
help both depend on it.

Contents: [requirements](#requirements) · [export variants and their inspector effect](#export-variants-and-their-inspector-effect)
· [two runtime gotchas](#two-runtime-gotchas) · [doc comments](#doc-comments)

## Requirements

An exported member must have **either** a constant-expression default
(`@export var number = 5`, type inferred) **or** an explicit type
(`@export var number: int`, no default). Neither means a syntax error.

## Export variants and their inspector effect

| Annotation | Inspector effect |
|---|---|
| `@export var x: int` / `@export var x = 5` | Plain field, type inferred from the default or stated explicitly. |
| `@export var r: Resource` / `@export var n: Node` | Drag-and-drop slot. Narrow a `Resource` export to a concrete subclass (`@export var r: AnimationNode`) or the drop-down's "create new" list becomes unusably long. |
| `@export_range(min, max[, step[, hints...]])` | Slider or spin box. Hints: `"or_less"`/`"or_greater"` let typing/dragging past the slider's bound; `"exp"` for an exponential (log-scale) slider; `"hide_slider"` to show only the spin box; `"prefer_slider"` to force a slider on an `int`; `"suffix:m"` appends a unit label; `"radians_as_degrees"` stores radians but displays/edits degrees (with a `°` suffix); `"degrees"` displays the `°` suffix without any unit conversion. |
| `@export_enum("A", "B", "C")` | Drop-down. On an `int` var, stores the selected index; on a `String` var, stores the label text. `"Label:value"` sets an explicit stored value per option. |
| `@export_flags("A", "B", "C")` | Multi-select checkboxes packed into one integer bitmask. Only powers of 2 are valid values (`A=1, B=2, C=4, ...`); `0` means nothing selected. `"Label:value"` sets explicit values, and a combination option (`"Self and Allies:12"`) is allowed. |
| `@export_flags_2d_physics` / `_render` / `_navigation`, and the `3d_` equivalents | Same bitmask UI, pre-populated from the matching project-settings layer names — no manual flag list needed. |
| `@export_file`, `@export_file("*.txt")` | File-picker restricted to `res://`, optionally filtered by extension/pattern. |
| `@export_dir` | Directory-picker restricted to `res://`. |
| `@export_global_file(...)`, `@export_global_dir` | Same, but for paths **outside** the project (global filesystem) — only meaningful in a `@tool` script. |
| `@export_multiline` | Large multi-line text box instead of a single-line field. |
| `@export_node_path("Button", "TouchScreenButton")` | `NodePath` field restricted (in the picker) to the listed node types. |
| `@export_color_no_alpha` | Color picker with the alpha channel forced to 1 and hidden. |
| `@export_exp_easing` | Curve widget that visualizes the value as an `ease()` argument. |
| `@export_group("Name"[, "prefix_"])`, `@export_subgroup(...)`, `@export_category("Name")` | Collapsible headings in the inspector. A prefix hides that substring from each property's displayed name. Groups don't nest — use a subgroup inside a group. `@export_group("")` closes the current group. Pair a boolean toggle named `..._enabled` with `@export_custom(PROPERTY_HINT_GROUP_ENABLE, "")` to move its checkbox onto the group heading itself (Godot's own `refraction_enabled` does this). |
| `@export_storage` | Serialized into the scene/resource file like any export, but **not** shown in the inspector — for state a `@tool` script needs to persist without exposing it to accidental edits. Also copied on `duplicate()`, unlike a plain non-exported `var`. |
| `@export_custom(hint, hint_string[, usage_flags])` | Escape hatch for any `PropertyHint`/usage-flag combination the named annotations don't cover (e.g. a numeric suffix with no range limit). GDScript performs **no validation** on the arguments — a typo produces unexpected inspector behavior, not an error. |
| `@export_tool_button("Label"[, "IconName"])` | A clickable button in the inspector on a `Callable`-typed member; pressing it calls the callable. The icon name must match a built-in editor icon (case-sensitive); custom project icons aren't supported. |
| `@export_custom(PROPERTY_HINT_INPUT_NAME[, "show_builtin,loose_mode"])` | String field scoped to the project's InputMap actions; `show_builtin` adds engine defaults like `ui_accept`, `loose_mode` allows typing an arbitrary value too. |
| `@export_custom(PROPERTY_HINT_LINK, "suffix:px")` | Vector components linked in the inspector — dragging one proportionally adjusts the others (with a per-property unlock toggle). Works on any `Vector2/2i/3/3i/4/4i`. |

Typed arrays combine with most of the above: `@export_range` on
`Array[float]`, `@export_file("*.json")` on `Array[String]`,
`@export_color_no_alpha` on a `PackedColorArray`, and so on. An exported
`Array[Resource-subtype]` (e.g. `Array[Texture]`) accepts multi-file
drag-and-drop from the FileSystem dock. Packed arrays (`PackedVector3Array`,
`PackedStringArray`, …) only work as exports if initialized empty.

## Two runtime gotchas

**Reading an exported value in `_init()` returns the default, not what's set
in the inspector.** Scene/resource values are applied *after* object
construction, so `_init()` only ever sees the export's own default. Read the
real value in `_ready()`, or in a setter defined on the property (useful for
custom `Resource` types, which have no `_ready()`).

**A `@tool` script that changes an exported value from code doesn't refresh
the inspector on its own.** Call `notify_property_list_changed()` after the
assignment, or the panel keeps showing the stale value until something else
forces a redraw.

## Doc comments

A doc comment starts with `##` (not `#`) and must immediately precede what it
documents — a script's own doc comment goes at the very top, before `class_name`/
`extends`. If an exported variable carries one, it becomes its inspector
tooltip; every doc comment together becomes the class's entry in the built-in
help window and can be exported as XML.

Script-level structure: a brief description first, one blank `##` line, then
the fuller description. Tags (each starts a new line, tag flush against the
`##`, no space before the colon):

- `@tutorial: https://...` or `@tutorial(Title): https://...`
- `@deprecated` or `@deprecated: Use [AnotherClass] instead.`
- `@experimental` or `@experimental: This API is unstable.`

Member doc comments precede the signal/enum/constant/variable/function/inner
class they document (before any annotation on that member), or can be written
inline after it on the same line (`var my_var ## My variable.`). A member
whose name starts with `_` is treated as private and stays out of generated
docs — *unless* it has its own doc comment, in which case it's documented
anyway despite the underscore.

A useful subset of the BBCode-like tags available inside a doc comment:
`[ClassName]` links a class, `[method Class.name]`/`[member Class.name]`/
`[signal Class.name]`/`[constant Class.name]`/`[enum Class.name]` link a
specific member, `[param name]` renders a parameter name as code, `[b]`/`[i]`/
`[code]` for inline emphasis, `[codeblock]`/`[/codeblock]` for a multi-line
example (indent with four literal spaces inside it — the parser strips tabs),
and `[br]` for a forced line break (plain blank lines inside a multi-line
description get joined into one paragraph, not preserved).
