# GDScript style guide and warning system

Sources: `${CLAUDE_PLUGIN_ROOT}/godot-docs/gdscript/gdscript_styleguide.rst` and
`${CLAUDE_PLUGIN_ROOT}/godot-docs/gdscript/warning_system.rst`. The warning list
below (names, defaults, meaning) comes from the engine's own `ProjectSettings`
class reference, not from the vendored style guide — the style guide only
explains the mechanism, not each warning.

Contents: [formatting](#formatting) · [naming conventions](#naming-conventions)
· [code order](#code-order) · [the warning system](#the-warning-system)
· [full warning reference](#full-warning-reference)

## Formatting

- **Tabs, LF, UTF-8 without BOM** — all editor defaults; don't fight them.
- **Indentation**: one level per nesting depth. Continuation lines (a call or
  condition wrapped across lines) get **two** indent levels, to visually
  distinguish them from a new block — except array/dictionary/enum literals,
  which get **one** extra level, matching their closing bracket.
- **Trailing comma** on the last element of a multi-line array, dictionary, or
  enum (cleaner diffs when adding items) — but never on a single-line literal.
- **Blank lines**: two between top-level function/class definitions, one
  inside a function to separate logical sections.
- **Line length**: keep under 100 characters; prefer under 80.
- **One statement per line** — no `if x: y` on one line — except the ternary
  operator, which is idiomatic on one line: `next_state = "idle" if is_on_floor() else "fall"`.
- **Wrap long expressions with parentheses**, not trailing backslashes —
  backslash continuation breaks if the last line ever gains a trailing
  backslash by accident; parentheses can't. Put `and`/`or` at the **start** of
  the continuation line, not the end of the previous one.
- **Avoid parentheses that don't change evaluation order**: `if is_colliding():`,
  not `if (is_colliding()):`.
- **Boolean operators**: `and`/`or`/`not`, never `&&`/`||`/`!`.
- **Comments**: a space after `#` or `##` for real comments (`# like this`),
  no space when commenting out code (`#print(...)`) — this is what lets a
  reader tell prose from disabled code at a glance. `#region`/`#endregion`
  markers are the one exception and must not have a leading space.
- **Whitespace**: one space around operators and after commas; no space
  before an operator, inside `()`/`[]`, or between a function name and its
  `(`. Single-line dictionary literals get a space just inside `{ }` (`{ key = "value" }`)
  so they don't read as arrays at a glance. Never align values with extra
  spaces.
- **Quotes**: double by default; single only when it avoids escaping — and if
  both styles would need the same number of escapes, prefer double.
- **Numbers**: never omit a leading or trailing zero (`0.234`, `13.0`, not
  `.234`/`13.`); lowercase hex digits (`0xfb8c0b`); use `_` separators in
  numbers at or above 1,000,000 (`1_234_567_890`).

## Naming conventions

| Type | Convention | Example |
|---|---|---|
| File names | snake_case | `yaml_parser.gd` |
| Class names | PascalCase | `class_name YAMLParser` |
| Node names | PascalCase | `Camera3D`, `Player` |
| Functions | snake_case | `func load_level():` |
| Variables | snake_case | `var particle_effect` |
| Signals | snake_case, **past tense** | `signal door_opened` |
| Constants | CONSTANT_CASE | `const MAX_SPEED = 200` |
| Enum names | PascalCase, singular | `enum Element` |
| Enum members | CONSTANT_CASE | `EARTH, WATER, AIR, FIRE` |

A named class's file name is its `class_name` converted to snake_case
(`class_name YAMLParser` lives in `yaml_parser.gd`) — this also sidesteps
case-sensitivity breakage when a project is exported from Windows to a
case-sensitive filesystem. Prepend a single underscore to virtual methods you
override, and to private functions and variables (`_recalculate_path`,
`_counter`) — the same underscore convention that also controls whether a
member appears in generated docs (see `references/exports-and-docs.md`).
Write each enum member on its own line, not `enum Element { EARTH, WATER }` —
one per line makes room for a doc comment above each and produces a clean diff
when a member is added or removed.

## Code order

```
01. @tool, @icon, @static_unload
02. class_name
03. extends
04. ## doc comment

05. signals
06. enums
07. constants
08. static variables
09. @export variables
10. remaining regular variables
11. @onready variables

12. _static_init()
13. remaining static methods
14. overridden built-in virtual methods:
    1. _init()  2. _enter_tree()  3. _ready()
    4. _process()  5. _physics_process()  6. remaining virtual methods
15. overridden custom methods
16. remaining methods
17. inner classes
```

Within properties and within methods, public members come before private
ones. The rationale: properties and signals before methods, public before
private, construction (`_init`/`_ready`) before anything that mutates state at
runtime — so a reader moves top-to-bottom from "what this object is" to "how
it gets built" to "what it does."

## The warning system

Configure warnings in **Project Settings → Debug → GDScript** (enable
**Advanced Settings** to see the section — or just search "GDScript"). Each
warning is a **tri-state**: **Ignore**, **Warn**, or **Error**. Promoting one
to Error means the project won't run until every instance is fixed — a real
gate, not just a status-bar note.

`debug/gdscript/warnings/enable` (bool, default `true`) is the master switch;
`false` silences every warning below regardless of its individual setting.

To suppress a warning locally instead of project-wide, use the
`@warning_ignore("name")` annotation immediately above the offending line
(the name matches the project-setting key's tail, e.g. `unused_variable` for
`debug/gdscript/warnings/unused_variable`). For a whole region, bracket it
with `@warning_ignore_start("name")` and `@warning_ignore_restore("name")` —
omit `_restore` to silence it through the end of the file. `directory_rules`
(default: exclude `res://addons`) lets a whole directory opt out of the
project's warning configuration, which matters for vendored/third-party code
you don't control.

## Full warning reference

Default column: **Ignore** / **Warn** / **Error** as shipped. Most of the
warnings built specifically for typed code ship at **Ignore** —
`untyped_declaration`, `unsafe_cast`, `unsafe_property_access`,
`unsafe_method_access`, and `unsafe_call_argument` all do nothing until you
turn them on. `unsafe_void_return` is the one exception in that group and
ships at **Warn**. Turn the rest on deliberately if you want the compiler to
flag every dynamic-style access in a typed file.

| Warning | Default | Meaning |
|---|---|---|
| `assert_always_false` | Warn | An `assert` call always evaluates to `false`. |
| `assert_always_true` | Warn | An `assert` call always evaluates to `true`. |
| `confusable_capture_reassignment` | Warn | Reassigning a lambda-captured local doesn't modify the outer variable. |
| `confusable_identifier` | Warn | Identifier mixes characters/alphabets that look confusable. |
| `confusable_local_declaration` | Warn | A nested-block identifier shadows one declared later in the parent block. |
| `confusable_local_usage` | Warn | Using an identifier that a later declaration in the same block will shadow. |
| `confusable_temporary_modification` | Warn | Modifying a `Packed*Array` property via a chained call or non-`const` method only touches a temporary — the property itself is unchanged. |
| `deprecated_keyword` | Warn | A deprecated keyword is used (currently never fires — no keywords are deprecated). |
| `directory_rules` | `{"res://addons": Exclude}` | Per-directory Include/Exclude map — a different two-state enum from the rest of this table — controlling which scripts get warnings at all. |
| `empty_file` | Warn | An empty file was parsed. |
| `enum_variable_without_default` | Warn | An enum-typed variable has no explicit default, and `0` isn't a valid member. |
| `get_node_default_without_onready` | Error | `get_node()`/`$Node` used as a class variable's default without `@onready`. |
| `incompatible_ternary` | Warn | A ternary's two branches may produce incompatible types. |
| `inference_on_variant` | Error | An inferred (`:=`) declaration's initial value is `Variant`, so the "inferred" type is just `Variant`. |
| `inferred_declaration` | Ignore | A variable/constant/parameter's type was implicitly inferred via `:=` rather than stated. Pair with `untyped_declaration`, not above it. |
| `int_as_enum_without_cast` | Warn | An integer used as an enum value without an explicit cast. |
| `int_as_enum_without_match` | Warn | An integer used as an enum value that matches no member. |
| `integer_division` | Warn | Dividing an int by an int silently discards the remainder. |
| `missing_await` | Ignore | A coroutine was called without `await`. |
| `missing_tool` | Warn | The base class script has `@tool`, but this script doesn't. |
| `narrowing_conversion` | Warn | A float argument passed where an int is expected, losing precision. |
| `native_method_override` | Error | A script method overrides a native engine method — may not behave as expected. |
| `onready_with_cast` | Warn | An `@onready` initializer casts a `$NodeLiteral` — may unexpectedly assign `null`. |
| `onready_with_export` | Error | `@onready` combined with `@export` on the same variable — the two annotations conflict. |
| `redundant_await` | Warn | `await` used on a call that isn't a coroutine. |
| `redundant_static_unload` | Warn | `@static_unload` used on a script with no static variables. |
| `renamed_in_godot_4_hint` | on (bool) | Hints at the Godot 3 name when a renamed API errors. |
| `return_value_discarded` | Ignore | A function's return value (sometimes an `Error` code) is never used. |
| `shadowed_global_identifier` | Warn | A local/member name shadows a built-in function or global class name. |
| `shadowed_variable` | Warn | A local variable/constant shadows a member of the current class. |
| `shadowed_variable_base_class` | Warn | A local variable/constant shadows a member of a base class. |
| `standalone_expression` | Warn | An expression statement has no effect (e.g. `2 + 2` alone on a line). |
| `standalone_ternary` | Warn | A ternary expression statement has no effect. |
| `static_called_on_instance` | Warn | A static method called through an instance instead of the class. |
| `unassigned_variable` | Warn | A variable is used before it was ever assigned. |
| `unassigned_variable_op_assign` | Warn | A variable is compound-assigned (`+=`) before its first plain assignment. |
| `unreachable_code` | Warn | Code after an always-executed `return` (or similar) can never run. |
| `unreachable_pattern` | Warn | A `match` pattern can never be reached. |
| `unsafe_call_argument` | Ignore | An argument's type may not be compatible with the parameter's declared type. |
| `unsafe_cast` | Ignore | A `Variant` value is cast to a non-`Variant` type. |
| `unsafe_method_access` | Ignore | Calling a method not guaranteed to exist on the static type at compile time. |
| `unsafe_property_access` | Ignore | Accessing a property not guaranteed to exist on the static type at compile time. |
| `unsafe_void_return` | Warn | A `void` function returns the result of a call that isn't guaranteed `void` itself. |
| `untyped_declaration` | Ignore | A variable, parameter, or function return has no static type at all. Pair with the editor's **Text Editor → Completion → Add Type Hints** setting. |
| `unused_local_constant` | Warn | A local constant is declared and never used. |
| `unused_parameter` | Warn | A function parameter is declared and never used. |
| `unused_private_class_variable` | Warn | An underscore-prefixed member variable is never used. |
| `unused_signal` | Warn | A signal is declared but never emitted or connected. |
| `unused_variable` | Warn | A local variable is declared and never used. |

`renamed_in_godot_4_hint` is a plain bool switch (on by default), not a
tri-state — it only adds context to an error that already occurred, so there
is no "Warn" level to set.
