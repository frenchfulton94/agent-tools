# Cross-skill trigger matrix

Each of this plugin's four skills was checked against its own siblings in
isolation, at the point it shipped — see each skill's own
`evals/triggers.md`. Three of those four batteries recorded the same honest
caveat: the siblings they were checking against didn't exist yet, so their
"should not trigger" cases were a designed prediction, not a measured
four-way contest. `godot-testing-and-debugging`'s battery, shipping last,
noted this explicitly: a real four-way matrix was "actually executable
today," just not from inside that task, because its own brief also forbade
subagent dispatch.

This document is that four-way matrix. It reasons from the four shipped
`description` fields, read together, rather than dispatching a clean-context
agent per prompt (this task's own brief forbids that too). Where the
descriptions genuinely disagree about who owns a prompt, that is recorded as
a finding — not resolved with an invented tie-break the descriptions
themselves don't support.

## The four descriptions, for reference

- **`gdscript`** — writing/reviewing GDScript: typing, style, warnings,
  `@export`, doc comments, format strings. Names `godot-scene-files` (scene
  files), `godot-testing-and-debugging` (running/checking code), and
  `godot-csharp` (a different language) as the sibling that owns each
  adjacent case.
- **`godot-project-architecture`** — structural decisions: node/scene/
  script/resource, autoload vs. global, signals vs. direct calls, scene/
  project organization, save data, version control, engine upgrades. Names
  `godot-scene-files` (file format) and `gdscript` (code inside a scene) as
  carve-outs.
- **`godot-scene-files`** — the `.tscn`/`.tres` grammar and `uid://`
  identity: `ext_resource`/`sub_resource`, hand-editing safety, `.uid`/
  `.import` sidecars, diagnosing broken/orphaned references. Names
  `gdscript` (the script a scene attaches) and `godot-testing-and-debugging`
  (running/screenshotting a scene) as carve-outs.
- **`godot-testing-and-debugging`** — proving a project works: checking
  scripts/shaders, running scenes headlessly, screenshots, unit test
  frameworks, debugger/profiler. Names `gdscript` (what an error means about
  the code) and `godot-scene-files` (what it means about the scene file) as
  carve-outs.

## Matrix

| # | Prompt | Fires | Why the other three don't |
|---|---|---|---|
| 1 | "My scene won't load after I renamed a script file." | `godot-scene-files` | `gdscript`: the script's own content isn't in question. `godot-project-architecture`: not a structural decision. `godot-testing-and-debugging`: the scene never gets as far as running. |
| 2 | "Add type hints to this function in player.gd." | `gdscript` | `godot-scene-files`: no scene or sidecar involved. `godot-project-architecture`: not a where-does-this-belong question. `godot-testing-and-debugging`: nothing is being run or checked. |
| 3 | "Should this enemy's health system be an autoload or a regular node?" | `godot-project-architecture` | `gdscript`: no code being written yet. `godot-scene-files`: no file-format question. `godot-testing-and-debugging`: nothing runtime-broken to diagnose — this is a design choice before any code exists. |
| 4 | "Run my game headlessly and tell me if anything errors." | `godot-testing-and-debugging` | `gdscript`: no specific diagnostic to interpret yet. `godot-scene-files`: not a file-format question. `godot-project-architecture`: not a structural question. |
| 5 | "What does the UNUSED_PARAMETER warning mean?" | `gdscript` | `godot-scene-files`/`godot-project-architecture`: no scene or structural content at all. `godot-testing-and-debugging`: its own `evals/triggers.md` records this exact prompt as a negative case for itself — "a GDScript warning name with no run/test/screenshot framing at all." |
| 6 | "My shader won't compile, what's wrong with it?" | `godot-testing-and-debugging` | `gdscript`: scoped to `.gd`, never shaders. `godot-scene-files`/`godot-project-architecture`: neither's description mentions shader compilation at all. |
| 7 | "What's the difference between ext_resource and sub_resource in a .tscn?" | `godot-scene-files` | The other three: none names scene-file grammar in its description. |
| 8 | "How should I organize my scenes and folders for a new project?" | `godot-project-architecture` | `godot-scene-files`: this is exactly the carve-out its own description draws — file *format*, not folder layout; its own `evals/triggers.md` records "Where should I put my enemy scenes relative to their scripts?" as a negative case pointing here. `gdscript`/`godot-testing-and-debugging`: neither covers project layout. |
| 9 | "I deleted a .uid file by accident — is my project broken?" | `godot-scene-files` | Its description explicitly names ".uid and .import sidecars" and "diagnosing broken or orphaned references" — the only one of the four whose description surfaces sidecars at all. **Worth flagging, not a tie**: `godot-project-architecture`'s *reference material* (`references/project-organization.md`) independently states this exact same measured fact under "what to commit," but that fact never surfaces in *its description* — so on description text alone (what actually drives triggering) this is a clean single fire, even though the underlying content is duplicated across two skills' reference files. |
| 10 | "check_script reported an error on line 12 of player.gd — what does it mean and how do I fix it?" | **Genuine overlap — no clean single fire** | See below. |
| 11 | "My autoload's signal handler throws a null reference error when the game runs — what's wrong?" | **Genuine overlap — no clean single fire** | See below. |
| 12 | "How do I write a unit test for this class using GUT?" | `godot-testing-and-debugging` | `gdscript`: not about the code's own typing/style/warnings. `godot-scene-files`/`godot-project-architecture`: neither covers test frameworks. |

## The two prompts that don't resolve cleanly

**#10 — interpreting a `check_script`/`--check-only` diagnostic.**
`gdscript`'s description explicitly claims "when a GDScript warning or parse
error needs interpreting." `godot-testing-and-debugging`'s description
explicitly claims "checking scripts and shaders for errors" and "an error
message needs interpreting." Each skill's own text *also* tries to hand this
exact case to the other — `gdscript` says "for running or checking the
code, use godot-testing-and-debugging"; `godot-testing-and-debugging` says
"for what the error means about the code itself, use gdscript." A prompt
phrased as one sentence that both runs the check *and* asks what the result
means (the way a real user actually asks it, per prompt #10) sits exactly on
that mutual carve-out and both descriptions claim it. The individual
`evals/triggers.md` files avoid this collision by only ever testing the two
halves separately — "What does UNUSED_PARAMETER mean?" (no run framing,
correctly `gdscript` alone) and "I ran `--check-only` and it said nothing
was wrong, but the game still crashes" (a verify-loop symptom, correctly
`godot-testing-and-debugging` alone) — neither battery tests the combined
phrasing that #10 uses. In practice this is a soft landing (whichever skill
fires cross-references the other one by name in its own text, so an agent
that reads either skill knows where to look next), but the description text
alone does not name one clean winner.

**#11 — a runtime error inside an autoload's signal handler.**
`godot-project-architecture`'s description claims "when an autoload is the
right answer and when it is a global variable in disguise" and "signals
versus direct calls" — this prompt names both. `godot-testing-and-debugging`'s
description claims "a scene behaves wrongly at runtime" and "an error message
needs interpreting" — this prompt is exactly that, too. `godot-testing-and-
debugging`'s own `evals/triggers.md` already flags this exact tension against
itself, as a *forward-looking* design question ("Should this be an autoload?"
→ `godot-project-architecture`), noting "an autoload misbehaving at runtime
*would* eventually route here once something actually breaks" — but that
note only covers the design-time phrasing, not a live crash report. Prompt
#11 is the live-crash phrasing that note anticipated but never actually
tested. A real answer to #11 plausibly needs both: `godot-testing-and-
debugging` to read the backtrace and confirm what's actually null, and
`godot-project-architecture` to judge whether the autoload/signal design is
the root cause or just where the symptom surfaced. Neither description
subordinates itself to the other here the way `gdscript` and `godot-scene-
files` do for each other elsewhere, so this is a real, undecided overlap,
not a missing carve-out clause that could be patched in with one more
sentence.

## Reading this matrix

Ten of twelve prompts resolve to exactly one skill, using only the
description text every skill already ships — no changes were needed to any
`SKILL.md` to produce this result. The two that don't (#10, #11) are
reported as-is rather than patched with a tie-break invented for this
document: fixing them for real would mean editing two skills' `description`
fields against each other, which is a design change to skills that already
shipped and passed their own review, not something this verification task
is scoped to do unilaterally.
