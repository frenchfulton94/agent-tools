# Workflow router

Read this before creating any OpenSpec change. Classify the work, then create
the change with the schema named in the sentence:

    /openspec-new-change <the work, in a sentence>, using <schema>

Naming the schema is what makes the choice stick: OpenSpec selects nothing on
its own. The terminal form is `openspec new change <slug> --schema <schema>`.
Then run `/openspec-continue-change <change>` once per artifact, naming the change each
time.

## Decision tree (first match wins)

Check "Work that never becomes a change" below first. All surface work goes
through impeccable: work that only changes how a surface looks or reads never
becomes a change, and a change that has a surface builds it through impeccable.

1. **Production is broken now.** Mitigate first: roll back or flip the flag.
   Then open `bugfix-flow` and fill its Incident section.
2. **A new project bootstrap** → `setup-flow`.
3. **Behaviour deviates from spec or intent**, including performance
   regressions → `bugfix-flow`. A raw incoming report goes to `/triage` first.
4. **A dependency, framework, or platform version change** → `upgrade-flow`.
5. **Structure changes and external behaviour must not** → `refactor-flow`.
   Coverage backfill is a refactor with no restructure.
6. **An open question answered by building or reading** → `spike-flow`.
7. **A new capability or intentional behaviour change**, including removals →
   `feature-flow`, the config default.
8. **A small code change, one decision wide, touching no contract** →
   `rapid-flow`. Typos, docs, and lint fixes are a direct commit with no
   change.

## Work that never becomes a change

| Work | Where it goes |
|---|---|
| Surface-only work: look, feel, layout, copy, motion, accessibility, polish | impeccable, directly: `/impeccable <command> <surface>`. See "The surface boundary" |
| An effort too big and foggy for one change | `/wayfinder`. Its cleared map enters `feature-flow` at the proposal |
| A survey for deepening opportunities | `/improve-codebase-architecture`. Each accepted candidate becomes a `refactor-flow` change |
| Raw bug reports and feature requests | `/triage`. Its `ready-for-agent` briefs become changes |
| A decision only someone else can answer | `/to-questionnaire` |
| Which Pocock skill fits | `/ask-matt` |

Tickets a flow published are agent-ready already; never triage them.

## The surface boundary

A surface is anything a person sees or touches: a page, a screen, a component,
its copy, its motion. The surface is an adapter at a presentation seam. A flow
owns everything behind the seam: domain state, data fetching and mutation,
validation, permissions, and the interface the surface consumes. Impeccable
does everything in front of it: components, layout, presentation-only state,
copy, accessibility, and motion.

**No surface file is edited outside an impeccable call.** A flow calls
impeccable at fixed points and writes no surface code itself:

| When | Call |
|---|---|
| A `feature-flow` grill, for a change with a surface | `shape <surface>`: the brief names the states the module must emit |
| A surface slice at apply | build the surface against design.md's Presentation seam block, then `audit`, then `polish` |
| A `bugfix-flow` fix that adds a state | present the state from its fixture, then `audit` |
| A `refactor-flow` slice that restructures surface files | `extract`, with every rendered state unchanged |
| An `upgrade-flow` surface classed rendered | `audit` before the bump and after it |
| A `setup-flow` project with a user interface | `init` |

- A behavioural state, such as "permission denied returns an error", is a spec
  scenario. How that state looks and reads is impeccable's.
- An error kind is behaviour; the message a user reads is presentation. Specs
  assert the kind, never the wording.
- When impeccable needs behaviour the seam does not emit (a retry, a state,
  validation, persistence, analytics), the surface work stops. Add the
  scenario and the state behind the seam first. Impeccable presents only what
  the seam already emits.
- A change a surface consumes carries a Presentation seam block in design.md and
  one fixture per emitted state. The surface slice is blocked by the slice that
  builds the seam.
- Surface-only work needs no change: run the impeccable command. When it
  reveals missing functionality, open a `feature-flow` change; its grill reads
  the brief and asks only behaviour questions.
- Where impeccable is not installed, stop and say so. Never build a surface
  without it.
- Impeccable's design hook also scans `.ts` and `.js` edits. Exclude engineering
  directories with `/impeccable hooks ignore-file <glob>`, with the user's
  agreement.

## Who does what

Pocock's skills run every step. Three other sources each have fixed jobs:

| Job | Skill | Where |
|---|---|---|
| Threat model for a change that crosses a trust boundary | security-and-hardening | `feature-flow` specs |
| Challenge a design before it is approved | doubt-driven-development | `feature-flow` and `refactor-flow` design |
| Hunt for defects and weak tests, once per change | code-review-and-quality | apply, after the last slice |
| Measure a performance fix and keep or revert it | performance-optimization | `bugfix-flow` |
| Write code against a library's current documentation | source-driven-development | `upgrade-flow` and `setup-flow` apply |
| Write and enforce the project's quality bar | constraint-driven-development | `setup-flow` |
| All surface work | impeccable | see above |

code-review asks whether the code follows the standards and matches the spec.
code-review-and-quality asks whether it is correct. They are not substitutes.
Where CONSTRAINTS.md exists it is the bar: never reach green by suppressing a
check, skipping or deleting a test, weakening an assertion, or lowering a
threshold.

## Guardrails

- `rapid-flow` → `feature-flow` when a contract appears or a decision grows real
  alternatives.
- `refactor-flow` → `feature-flow` when a guard assertion has to change.
- `bugfix-flow` → `feature-flow` when the fix changes promised behaviour rather
  than restoring it.
- `upgrade-flow` → `feature-flow` for any deliberate behaviour change.
- De-escalate as readily: a feature grill that shrinks to one decision becomes
  `rapid-flow`, and one that turns into a question becomes `spike-flow`.
- When two schemas fit, ask one question naming both, then route.

## Sessions

- Run the planning artifacts in one unbroken window. Changing model or effort at
  an artifact boundary is free.
- At a phase boundary, prefer in order: continue, `/clear`, `/handoff`, a
  subagent, `/compact`.
- Where tasks.md carries a Session line, it records the session shape.
  Single-session work continues in the same window. Multi-session work runs
  each slice in a fresh session: `/clear`, then `/model` or `/effort`, then
  `/openspec-apply-change <change>`, naming the change because clearing removed it.
- `/handoff` writes to the OS temp directory. Name the change in it, and start
  the next session with `openspec status --change <name> --json`.
- Apply offers `/retro` when a build ends and never runs it. `rapid-flow` offers
  it only when the change went sideways.
- A change ends at archive. Once every box is ticked, the human runs
  `/openspec-verify-change <change>` where it is installed, then
  `/openspec-archive-change <change>`, which merges the delta specs into
  `openspec/specs/`. `openspec validate <change> --strict` runs at the specs
  and tasks artifacts.
