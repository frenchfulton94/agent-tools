# Trigger battery — gdscript

Run each query in a clean session with only the description visible. Record
fired / did not fire. This skill is the first one shipped in the `godot`
plugin — `godot-scene-files`, `godot-testing-and-debugging`, and `godot-csharp`
don't exist yet, so the negatives below check that this skill's own
description doesn't over-fire on requests that belong to a sibling once one
exists, not a real routing contest.

## Should trigger

1. "Add type hints to this .gd file." — the plainest positive; typing is this
   skill's core subject.
2. "What does UNUSED_PARAMETER mean?" — names a specific warning by its
   project-settings identifier, with no other domain word in the query.
3. "How do I show this variable in the inspector?" — never says GDScript,
   `.gd`, or `@export`; the intent (expose a script variable to the editor
   UI) is what should key the match.
4. "Why is my `@onready var enemy := get_node(\"Enemy\")` typed as `Node` and
   not `Enemy`?" — a symptom report, not a feature request; answered by the
   `get_node()` inference trap in `references/static-typing.md`.
5. "Should I turn on unsafe_cast checking?" — a warning-configuration
   question phrased as a yes/no, not "what is."
6. "My script won't compile — Error: onready_with_export." — a raw warning
   name pasted from the editor, no other context.
7. "What's the difference between `%s` and `.format()` in GDScript?" — format
   strings, one of the five topics in this skill's description.

## Should not trigger (near misses — reserved for sibling skills once they exist)

1. "Why does my scene fail to load?" → `godot-scene-files` (the `.tscn` file
   and its `uid://` references, not the script attached to it).
2. "Run my game and check for errors." → `godot-testing-and-debugging` (the
   headless run/verify loop, not the script's own syntax or style).
3. "Convert this script to C#." → `godot-csharp` (a different language
   entirely, even though the source is a `.gd` file).
4. "What Godot version added typed dictionaries?" → release-note trivia, not
   a writing/reviewing/fixing request this skill's description scopes itself
   to.
5. "Format this JSON file with two-space indentation." → a generic
   formatting request with no Godot or GDScript content at all; the trap is
   that this skill's own description contains "the official style guide,"
   which shares vocabulary with "formatting" but not subject matter.

Items 1–3 are the load-bearing ones: this skill's description explicitly
carves out scene files, running/checking code, and C# by name specifically so
a request that only superficially touches "Godot" or "a script" doesn't pull
in the wrong skill once all four ship. Until those three exist, none of these
five queries should fire *this* skill — a false positive on 1–3 today would
mean the description's carve-out clauses aren't doing their job.

## Recorded results

Not run — no clean-context agent dispatch was available for this task (Task 1
of the plugin's build; the brief that produced this skill also directed no
subagent dispatch). The five negatives are exercisable today by hand: this
skill is the only one installed, so 1–3 firing here (there being nothing else
to fire) would still be visible as "fired when it names a sibling skill by
name in its own carve-out clause" and is worth a manual spot check before the
sibling skills land in later tasks. Task 8 of this plan (by analogy with
`dokploy`'s own five-way sibling matrix in
`plugins/dokploy/skills/automating-dokploy/evals/triggers.md`) is the natural
point to run the full battery once `godot-scene-files`,
`godot-testing-and-debugging`, and `godot-csharp` all exist to compete
against.
