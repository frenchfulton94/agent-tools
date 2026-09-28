# Trigger battery — godot-testing-and-debugging

Run each query in a clean session with only the description visible. Record
fired / did not fire. This is the fourth and last skill in the `godot`
plugin's build — `gdscript`, `godot-scene-files`, and
`godot-project-architecture` all already ship, so unlike the trigger
batteries those three recorded for themselves, a full four-way matrix is
actually executable today by a maintainer with a clean-context dispatch; it
just wasn't executable from inside this task (see "Recorded results" below).

## Should trigger

1. "Run my game and tell me if it errors." — the brief's own headline
   example; the plainest positive for the `run_scene` rung.
2. "Show me what this scene looks like." — the brief's own headline example
   for `screenshot_scene`; never says "test" or "debug" at all.
3. "How do I write unit tests in Godot?" — the brief's own headline example
   for `references/test-frameworks.md`, phrased as a how-to with no error
   or symptom in it.
4. "My shader isn't working." — the brief's own headline example; a bare
   symptom report with no mention of compiling, `.gdshader`, or headless.
5. "I ran `--check-only` and it said nothing was wrong, but the game still
   crashes." — a symptom that should route straight to the exit-code trap
   this skill's own opening section exists for, without the query itself
   using the word "exit code."
6. "How do I see a breakdown of where my frame time is going?" — the
   profiler, described entirely by what it's for rather than by name.
7. "Can I get a screenshot of this without opening a window?" — should still
   fire (it's squarely a `screenshot_scene`/display-requirement question)
   even though the literal answer is "no, screenshots need a display."
8. "Set up GUT for this project." — names a specific framework by name, the
   `test-frameworks.md` entry point.

## Should not trigger (near misses — reserved for sibling skills)

1. "Add type hints to this function." → `gdscript` — script-internal
   authoring; this skill's own description and closing section carve this
   out by name ("For what the error means about the code itself, use
   gdscript").
2. "Should this be an autoload?" → `godot-project-architecture` — a
   structural decision, not a run/verify question, even though an autoload
   misbehaving at runtime *would* eventually route here once something
   actually breaks.
3. "Why does my scene fail to load after I renamed a file?" →
   `godot-scene-files` — a `uid://`/sidecar diagnosis on a scene that never
   gets as far as running; this skill's description defers exactly this
   ("for what it means about the scene file, use godot-scene-files").
4. "What does `UNUSED_PARAMETER` mean?" → `gdscript` — a GDScript warning
   name with no run/test/screenshot framing at all.
5. "Convert this script to C#." → `godot-csharp` (not yet shipped in this
   plugin) — a language conversion, untouched by anything here even though
   the source is code that could later be run and verified.

Items 1–3 are the load-bearing near-misses: this skill's own description
names `gdscript` and `godot-scene-files` explicitly as where a diagnostic's
*meaning* belongs, reserving only the *running and interpreting* half for
itself, so a request that only superficially touches "an error" or "a
script" shouldn't pull this skill in over the one that actually owns the
fix. Item 2 is a supplementary check against `godot-project-architecture`,
which this skill's frontmatter doesn't name directly (unlike the other two)
but which `godot-project-architecture`'s own description does name this
skill in return.

## Recorded results

Not run under a clean-context dispatch — this task's own brief directed no
subagent dispatch ("Do not dispatch subagents"), the same constraint
`gdscript`, `godot-scene-files`, and `godot-project-architecture` each
recorded for themselves at Tasks 1, 11, and 12. Unlike those three, though,
every other `godot` skill this battery competes against already exists in
this worktree as of this skill's own shipping — so items 1–5 above are, for
the first time in this plugin's build, actually exercisable as a real
four-way routing contest by whichever maintainer next runs a clean-context
agent with all four skills installed, rather than a designed check against
skills that don't exist yet to compete.
