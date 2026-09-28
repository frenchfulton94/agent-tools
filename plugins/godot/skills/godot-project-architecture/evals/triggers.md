# Trigger battery — godot-project-architecture

Run each query in a clean session with only the description visible. Record
fired / did not fire. `godot-testing-and-debugging` does not exist yet as of
this skill shipping (Task 12 of this plan), so the negative cases that name
it check that this skill's own carve-out clause doesn't over-fire in its
absence — the same caveat `godot-scene-files`' own trigger battery recorded
for itself at Task 11.

## Should trigger

1. "Should this be an autoload?" — names the exact decision this skill owns
   and the brief's own headline example.
2. "How should I organize this project?" — folder/file layout, no specific
   symptom, squarely inside `references/project-organization.md`.
3. "How do I save the player's progress?" — the save-game decision, owned by
   `references/saving-and-data.md`.
4. "My player scene keeps reaching into the main scene to spawn bullets, is
   that OK?" — a symptom-shaped question about coupling, without the words
   "signal" or "architecture" anywhere in it; should route to the
   signals-up/calls-down section rather than being missed for lack of
   vocabulary.
5. "Should this enemy's health and stats be a Node or a Resource?" — the
   four-way node/scene/script/resource decision, phrased as a concrete case
   rather than an abstract question.
6. "We're on Godot 4.4, is it safe to move to 4.6?" — the upgrade-path
   material, phrased as a real migration question rather than naming
   "migrating" or "upgrade path" directly.

## Should not trigger (near misses — reserved for sibling skills)

1. "Why is my tscn corrupt?" → `godot-scene-files` — a file-format/parse
   problem on an existing `.tscn`, not a structural decision about what to
   build. This skill explicitly defers file-format diagnosis to
   `godot-scene-files` in its own closing section.
2. "What does this warning mean?" → `gdscript` — a GDScript diagnostic on
   code that already exists, not a decision about where new functionality
   should live.
3. "Add static typing to this function." → `gdscript` — script-internal
   authoring, untouched by this skill even though the file in question may
   live inside a scene this skill would have opinions about structurally.
4. "Run this scene and take a screenshot." → `godot-testing-and-debugging`
   — driving the engine to execute something, not a structural decision;
   this skill's own frontmatter names that skill for exactly this case.
5. "What does uid-not-found mean in reference_graph's output?" →
   `godot-scene-files` — diagnosing a specific broken reference, which is
   the sibling's diagnostic job even though this skill's own version-control
   section mentions `.uid`/`.import` sidecars by name (for what to commit,
   not how they behave under a broken reference).

Item 4 is the load-bearing near-miss even though its target skill doesn't
exist yet in this plugin: this skill's own description and closing section
name `godot-testing-and-debugging` explicitly as the place "running or
screenshotting a scene" belongs, so the carve-out is real from this skill's
side regardless of whether the other skill has shipped yet to compete for
the query. Items 1, 2, 3, and 5 are real adjacent-domain traps against
skills that do already exist (`godot-scene-files`, `gdscript`), each chosen
because it shares surface vocabulary with this skill (file paths, warnings,
UIDs) without being a structural decision.

## Recorded results

Not run under a clean-context dispatch — this task's own brief directed no
subagent dispatch ("Do not dispatch subagents"), so there is no way to
observe an actual fire/no-fire outcome from a fresh session inside this
task. The queries above are written to be exercisable by hand once a
maintainer can run them against a clean session with all four `godot`
skills (`gdscript`, `godot-scene-files`, `godot-project-architecture`,
`godot-testing-and-debugging`) installed side by side; until then, this is a
designed battery, not a measured one — the same honest caveat
`godot-scene-files`' own `evals/triggers.md` recorded for itself.
