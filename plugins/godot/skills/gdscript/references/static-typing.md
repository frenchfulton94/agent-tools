# Static typing in GDScript

GDScript is optionally typed. Typed and untyped code run in the same project, and
the compiler will infer a type the moment you write a colon — `var health: int`
declares it explicitly, `var health := 10` infers it. Everything below assumes
you've chosen to type a file; see `${CLAUDE_PLUGIN_ROOT}/godot-docs/gdscript/static_typing.rst`
for the full source.

Contents: [`:=` versus `: type =`](#-versus--type-) · [`get_node()` inference](#the-one-place-inference-silently-gets-the-wrong-type-get_node)
· [`as` vs `is`](#as-vs-is) · [unsafe accesses](#unsafe-accesses-the-type-checker-cant-verify)
· [typed arrays and dictionaries](#typed-arrays-and-dictionaries) · [what you can't type-hint](#what-you-can-never-type-hint)
· [covariance and contravariance](#covariance-and-contravariance)

## `:=` versus `: type =`

Prefer `:=` when the type is obvious from the right-hand side on the same line,
and write the type explicitly when it isn't:

```gdscript
var direction := Vector3(1, 2, 3)   # Vector3 is unambiguous — infer it.
var health: int = 0                 # Could be int or float — say which.
```

Constants don't need a type hint — Godot sets it from the assigned value — but
add one anyway for a typed array constant, since untyped arrays are the
default: `const A: Array[int] = [1, 2, 3]`.

## The one place inference silently gets the wrong type: `get_node()`

`get_node()` and its `$Node` shorthand cannot infer a specific type unless the
target scene is already loaded in memory. Left to infer, they resolve to the
static type `Node`, not the actual node class, and every specific member access
after that becomes an unsafe or outright broken reference:

```gdscript
# Bad: infers as Node, not ProgressBar. Autocomplete and safety are gone.
@onready var health_bar := get_node("UI/LifeBar")

# Good: state the type explicitly.
@onready var health_bar: ProgressBar = get_node("UI/LifeBar")

# Also fine: cast with `as`, which the inferred var then picks up.
@onready var health_bar := get_node("UI/LifeBar") as ProgressBar
```

The explicit-annotation form and the `as`-cast form are not equivalent in
failure mode, and the difference matters more than which one looks safer in
the editor's gutter. If the node's type in the scene changes and the script
isn't updated, the **annotated** declaration errors immediately when the scene
loads. The **`as`-cast** declaration silently assigns `null` — `as` never
throws on a custom-class mismatch, it just casts to `null` — and the failure
surfaces later, at the first null-dereference, far from its cause. Prefer the
explicit annotation for anything you `@onready`-cache; reach for `as` when you
genuinely want the null-on-mismatch behavior (e.g. an optional child node).

## `as` vs `is`

`as` casts and swallows a type mismatch into `null` with no error or warning.
`is` only tests, so pair it with a typed variable when you need to act on the
result:

```gdscript
func _on_body_entered(body: PhysicsBody2D) -> void:
    if body is not PlayerController:
        push_error("Bug: body is not PlayerController.")
        return
    var player: PlayerController = body
    player.damage()
```

Use `as` when a silent `null` on mismatch is the behavior you want (for
example, an optional cast you immediately null-check). Use `is` plus an
explicit typed variable — or `assert(body is PlayerController, "...")` — when
a mismatch should be loud.

Casting a **built-in** type (not a custom class) that fails throws an error
immediately rather than producing `null` — only custom-class casts are silent.

## Unsafe accesses the type checker can't verify

`UNSAFE_PROPERTY_ACCESS`, `UNSAFE_METHOD_ACCESS`, and `UNSAFE_CAST` fire when
you reach for a member the static type doesn't guarantee exists. The fix is
always the same shape: narrow the type with `is` (or `Object.get()`, which
returns `Variant` or `null` instead of erroring) before touching the member:

```gdscript
func _on_body_entered(body: Node2D) -> void:
    var label_variant: Variant = body.get("label")
    if label_variant is Label:
        var label: Label = label_variant
        label.text = name
```

## Typed arrays and dictionaries

Enclose the element type in `[]`: `var scores: Array[int] = [10, 20, 30]`. The
type constrains `for`-loop iteration, `[]` access, assignment, and `+=`-style
appends — but **not** array/dictionary methods (`push_back`, `keys()`, …) or
`==`, which stay untyped. Dictionaries take two types, key then value:
`Dictionary[String, int]`. Neither collection supports nesting a typed
collection inside another (`Array[Array[int]]` is a syntax error) — only
`Array[Array]`/`Dictionary[String, Dictionary]` with the inner collection left
untyped.

Since Godot 4.2 you can type just the loop variable without typing the
collection: `for name: String in names:` — the array itself stays untyped, but
`name` is `String` inside the loop.

## What you can never type-hint

Two constructs are syntax errors, not warnings:

- Per-element types inside an array or dictionary literal (`[$Goblin: Enemy]`
  or a dict literal with per-key types) — the element type belongs on the
  collection's own declaration, not on the literal.
- Nested typed collections (`Array[Array[Character]]`).

## Covariance and contravariance

An override may narrow its return type (return a subtype the base method
declared as a supertype) and widen a parameter type (accept a supertype the
base method declared as a subtype) — the usual Liskov substitution rule.
Godot's own virtual methods follow this, so overriding `_process(delta: float)`
with a wider or identical parameter type is safe; narrowing a parameter is not.
