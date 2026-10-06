# Workflow router

Read this before creating any OpenSpec change. Classify the work, then create
the change with the schema named in the sentence:

    /opsx:new <the work, in a sentence>, using <schema>

Naming the schema is what makes the choice stick: OpenSpec selects nothing on
its own. The terminal form is `openspec new change <slug> --schema <schema>`.
Then run `/opsx:continue <change>` once per artifact, naming the change each
time.

## Decision tree (first match wins)

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
| UI/UX: look, feel, layout, copy, accessibility, polish | impeccable. See "The UI boundary" |
| An effort too big and foggy for one change | `/wayfinder`. Its cleared map enters `feature-flow` at the proposal |
| A survey for deepening opportunities | `/improve-codebase-architecture`. Each accepted candidate becomes a `refactor-flow` change |
| Raw bug reports and feature requests | `/triage`. Its `ready-for-agent` briefs become changes |
| A decision only someone else can answer | `/to-questionnaire` |
| Which Pocock skill fits | `/ask-matt` |

Tickets a flow published are agent-ready already; never triage them.

## The UI boundary

The UI is an adapter at a presentation seam. A flow owns everything behind the
seam: domain state, data fetching and mutation, validation, permissions, and
the interface the surface consumes. Impeccable owns the surface: components,
layout, presentation-only state, copy, accessibility, and motion.

- A behavioural state, such as "permission denied returns an error", is a spec
  scenario. How that state looks and reads is impeccable's.
- An error kind is behaviour; the message a user reads is presentation. Specs
  assert the kind, never the wording.
- When an impeccable command finds a behaviour gap (a retry policy, a state the
  module does not emit, validation, persistence, analytics), name the gap and
  open or extend a flow change. Impeccable presents only what the seam already
  emits.
- A change a surface consumes carries a Presentation seam block in design.md and
  one fixture per emitted state. Build the surface against that block.
- UI/UX-led work starts in impeccable. When `/impeccable shape` reveals missing
  functionality, open a `feature-flow` change for it; its grill reads the brief
  and asks only behaviour questions.
- During a flow's apply, surface work waits for the hand-off item; it never
  happens mid-slice.
- Impeccable's design hook also scans `.ts` and `.js` edits. Exclude engineering
  directories with `/impeccable hooks ignore-file <glob>`.

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
  `/opsx:apply <change>`, naming the change because clearing removed it.
- `/handoff` writes to the OS temp directory. Name the change in it, and start
  the next session with `openspec status --change <name> --json`.
- Apply offers `/retro` when a build ends and never runs it. `rapid-flow` offers
  it only when the change went sideways.
