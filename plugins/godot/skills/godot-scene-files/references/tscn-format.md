# The `.tscn`/`.tres` grammar

Read this when you need to write or review a `.tscn`/`.tres` edit by hand, or
when a scene's structure needs to be reasoned about line by line rather than
through `scene_tree`'s summary. The verbatim upstream source is vendored at
`${CLAUDE_PLUGIN_ROOT}/godot-docs/file_formats/tscn.rst` — this file is a
working guide to it, with the sections re-ordered around what you'll actually
need and worked examples pulled from real fixtures rather than the doc's own
(fine, but sparser) ones.

## Contents

- [File descriptor](#file-descriptor)
- [External resources](#external-resources)
- [Internal resources](#internal-resources)
- [Nodes](#nodes)
- [Connections](#connections)
- [NodePath](#nodepath)

## File descriptor

Always the first line in the file:

```
[gd_scene format=3 uid="uid://cecaux1sm7mo0"]
```

or, for a `.tres`:

```
[gd_resource type="ArrayMesh" format=3 uid="uid://dww8o7hsqrhx5"]
```

`format=3` is what Godot 4.x writes (Godot 3.x wrote `format=2`). `uid=` is
this file's own inline identity — see `uid-and-identity.md` for how that's
derived and what breaks it.

Scenes saved before Godot 4.6 also carry `load_steps=<int>` here, e.g.
`[gd_scene load_steps=2 format=3 uid="uid://dlegacy000000"]`. It's a stale
step-count the loader no longer needs. Deprecated as of 4.6 — ignore it
wherever you see it; do not try to keep it in sync with the file's actual
resource count.

## External resources

A link to a resource that lives in its own file, not inside this one:

```
[ext_resource type="Texture2D" uid="uid://ccbm14ebjmpy1" path="res://gradient.tres" id="2_eorut"]
[ext_resource type="Material" uid="uid://c4cp0al3ljsjv" path="material.tres" id="1_7bt6s"]
```

Four fields: `type` (the resource class), `path` (usually `res://`-prefixed,
though a path relative to the `.tscn` file's own location is also valid),
`uid` (this external file's own identity — see `uid-and-identity.md`), and
`id` (a label scoped to *this file*, used to refer to the resource from
elsewhere in it).

Referenced from a node or another resource with `ExtResource("id")`:

```
script = ExtResource("1_cvyw8")
```

`id` and `uid` are unrelated: `id` only has to be unique within this one
`.tscn`/`.tres` file, so an external and an internal resource in the same
file can legally share the same `id` string — they're disambiguated by which
constructor refers to them (`ExtResource` vs. `SubResource`), not by the id
value itself.

## Internal resources

A resource that lives inside this file rather than as a separate one — no
`path`, because there's nowhere else for it to live:

```
[sub_resource type="CapsuleShape3D" id="CapsuleShape3D_fdxgg"]
radius = 1.0
height = 3.0
```

Referenced the same way as an external resource, but with `SubResource`
instead of `ExtResource`:

```
shape = SubResource("CapsuleShape3D_fdxgg")
```

**Order matters here in a way it doesn't elsewhere in the file:** if one
internal resource refers to another (a mesh naming its material, say), the
resource being referred to must appear *earlier* in the file than the
resource referring to it. This is the concrete reason "reorder the internal
resources section" is unsafe to do casually — see the main `SKILL.md`.

## Nodes

The scene tree itself. Each node is one `[node …]` heading followed by its
`key = value` properties:

```
[node name="Root" type="Node2D" unique_id=1875567328]
script = ExtResource("1_cvyw8")

[node name="Enemy" type="Sprite2D" parent="." unique_id=1372617621 groups=["damageable", "enemies"]]

[node name="Holder" type="Node2D" parent="." unique_id=2015271264 node_paths=PackedStringArray("target_a", "target_b")]
script = ExtResource("2_4efwe")
target_a = NodePath("../TargetA")
target_b = NodePath("../TargetB")

[node name="TargetA" type="Node2D" parent="." unique_id=981781774]

[node name="TargetB" type="Node2D" parent="." unique_id=1926719150]
```

Heading fields worth knowing beyond `name`/`type`/`parent`:

- **`unique_id`** — present only in scenes saved with Godot 4.6+; do not
  assume it's there.
- **`groups=[...]`** — the node's group memberships, an inline string array.
- **`node_paths=PackedStringArray(...)`** — names which of this node's own
  properties are exported as a `Node` type but stored as a `NodePath` in this
  file (`target_a`/`target_b` above); the property values themselves still
  appear as ordinary `key = NodePath(...)` lines below the heading.
- **`instance=`** / **`instance_placeholder=`** — this node is an instanced
  sub-scene, not a plain node.
- **`index=`** — explicit ordering among siblings; when absent, appearance
  order in the file is what decides precedence between inherited and plain
  nodes.
- **`owner=`** — which node "owns" this one for scene-saving purposes,
  relevant to instanced sub-scenes.

The scene root is the first `[node …]` block and must **not** have a
`parent=` attribute; every other node's `parent=` is an absolute path from
the root, using `"."` for a direct child of the root and never repeating the
root's own name:

```
[node name="Player" type="Node3D" unique_id=1155673912]                    ; the root
[node name="Arm" type="Node3D" parent="." unique_id=1010797352]            ; direct child
[node name="Hand" type="Node3D" parent="Arm" unique_id=536436825]          ; child of Arm
```

A scene with no root, or more than one, fails to import. A `.tscn` may
contain single-line `;` comments — Godot itself discards them the next time
it saves the file through the editor.

## Connections

Signal wiring, always after the nodes section:

```
[connection signal="tree_exiting" from="Enemy" to="." method="_on_enemy_exit" binds= ["extra", 42]]
```

`signal`, `from`, `to`, and `method` are self-explanatory node-path/name
references. `binds=` carries the extra arguments bound to the connection as
an inline array — and the engine's own writer emits a **literal space**
after the `=` on this one attribute specifically (`binds= [...]`, not
`binds=[...]`). A parser or hand-edit that assumes every `key=value` pair is
tight against the `=` will trip on this one.

## NodePath

`NodePath(...)` is how one node's property refers to another node, or to a
component of another node's property, relative to the node whose property
holds it:

```
target_a = NodePath("../TargetA")
skeleton = NodePath("..")
```

`NodePath(".")` means the current node; `NodePath("")` means no node at all.
A `NodePath` can also address a specific property with a `:` suffix, down to
a single vector/transform/color component:
`NodePath("MeshInstance3D:scale.x")` names the `x` component of that node's
`scale` property — the mechanism Animation tracks use to target exactly what
they animate.
