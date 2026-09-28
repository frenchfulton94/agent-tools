# Trigger battery — godot-scene-files

Run each query in a clean session with only the description visible. Record
fired / did not fire. `godot-testing-and-debugging` and
`godot-project-architecture` don't exist yet as of this skill shipping, so
the negatives that name them check that this skill's own carve-out clauses
don't over-fire in their absence, the same caveat `gdscript`'s own trigger
battery records for itself.

## Should trigger

1. "My scene won't load after I renamed a file." — the brief's own headline
   symptom: a scene-load failure traced to a rename, which is exactly the
   sidecar-less-move failure this skill exists to diagnose.
2. "What is `uid://` in this `.tscn`?" — names the file format and the
   identity syntax directly, no symptom framing needed.
3. "Can I move these scripts into a subfolder?" — a forward-looking question
   about whether an operation is safe, not a report of something already
   broken; answered by the move rule (with-sidecar vs. without) in
   `uid-and-identity.md`.
4. "reference_graph says this is broken but the file is right there." — a
   symptom that should route straight to the `parse_errors`/overcount caveat:
   `broken` can be wrong when a referenced scene fails to parse.
5. "What does `ext_resource` mean in this scene file?" — vocabulary from the
   grammar itself, no symptom or file-operation framing at all.
6. "I deleted a .uid file by accident, is my project broken?" — tests that
   the skill fires on the safe case too, not only the destructive one; the
   correct answer (delete-in-place is recoverable) lives here, not in a
   panic response.

## Should not trigger (near misses — reserved for sibling skills)

1. "Add static types to this script." → `gdscript` — a `.gd` file's own
   content (typing), not the scene or sidecar it's attached through.
2. "Run the game and show me a screenshot." → `godot-testing-and-debugging`
   — driving the engine to execute a scene, not reading or diagnosing its
   file structure.
3. "Where should I put my enemy scenes relative to their scripts?" →
   `godot-project-architecture` — folder-level project organization, which
   this skill explicitly defers rather than covering itself (see the last
   paragraph of `SKILL.md`'s diagnosis section).
4. "Convert this script to C#." → `godot-csharp` — a language conversion,
   untouched by anything here even though the source is a project file.
5. "What does UNUSED_PARAMETER mean?" → `gdscript` — a GDScript warning
   name, no scene/resource/UID vocabulary in the query at all.

Items 1–2 are the load-bearing ones: this skill's description carves out
GDScript authorship and running/screenshotting a scene by pointing at
`gdscript` and `godot-testing-and-debugging` by name specifically, so a
request that only superficially touches "a Godot file" doesn't pull this
skill in over the one the description itself names as the correct owner.
Items 3–4 are supplementary near-miss checks against `godot-project-architecture`
and `godot-csharp` — real adjacent-domain traps worth having in the battery,
but neither is named in this skill's description, so they test general
non-overreach rather than a carve-out clause doing its job.

## Recorded results

Not run under a clean-context dispatch — the task that produced this skill
directed no subagent dispatch, the same constraint `gdscript`'s own trigger
battery recorded for itself at Task 1. The queries above are exercisable by
hand once `godot-testing-and-debugging`, `godot-project-architecture`, and
`godot-csharp` exist to compete against; until then, items 1–2 in the
negative list "firing" would only be observable as this skill answering a
question its own description says belongs elsewhere, since there is nothing
else installed yet to fire instead. Items 3–4 "firing" would only be
observable as this skill answering a question that belongs to a sibling its
description never names in the first place — a real over-reach if it
happened, but not one the description's own wording would have predicted.
