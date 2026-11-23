# The seven chains

Everything needed to fill in the chain, gate, and hatch lines of a routing answer, and to
drive the chain afterwards. Read only the section for the schema you routed to.

Contents:

- [How to read these](#how-to-read-these)
- [The seven flows](#the-seven-flows)
- [Rules that apply to every chain](#rules-that-apply-to-every-chain)

## How to read these

**Arrows are not the graph.** The real dependency graph is each artifact's `requires`, and
it forks — several artifacts can become ready together, and declaration order breaks the
tie. Status is pure filesystem existence:

```
BLOCKED ──────────► READY ──────────► DONE
missing deps      all deps done     file exists
```

So an artifact can read `done` while its dependencies were never written. Build the
required set by walking `requires` transitively, not by trusting status.

**`apply` is an operation, not an artifact.** It has its own `requires` and a `tracks`
file, which is why it never appears as an artifact id.

**The flows call only skills setup installs** — mattpocock-skills, six from agent-skills,
and impeccable — so they carry no fallback chain beyond the `flow-design` agent's inline
one. Where impeccable is absent, a flow stops rather than build the surface.

## The seven flows

Seven flows, each job given to the skill that does it best. mattpocock-skills 1.3.2 drives
every step. Six skills from agent-skills 0.6.17 do what Pocock's set has no skill for:
`security-and-hardening` (threat model at specs), `doubt-driven-development` (design
challenge), `code-review-and-quality` (one defect-hunting review per change),
`performance-optimization` (keep or revert), `source-driven-development` (code from current
docs), and `constraint-driven-development` (the quality bar). Impeccable 4.10.0 does all
surface work: the flows own functionality up to a presentation seam and call impeccable for
everything in front of it. `openspec/ROUTING.md` routes between them.

Every flow with a `specs` or `tasks` artifact runs `openspec validate <change> --strict`
there, and every apply ends by offering `/openspec-archive-change`.

### `feature-flow` — 5 artifacts, the config default

`grill → proposal → specs → design → tasks`, then `apply`.

| Artifact | `requires` | Carries |
|---|---|---|
| `grill` | — | `impeccable shape` first when the change has a surface; interview in grilling's rounds; `GLOSSARY.md` and ADRs written inline; a six-line Intent the user confirms with an explicit yes |
| `proposal` | `grill` | Problem / Solution / User Stories / Capabilities, every statement traceable to the grill |
| `specs` | `proposal` | Delta specs: `ADDED` from the stories, `MODIFIED`/`REMOVED` from the main spec; a `security-and-hardening` threat model when a trust boundary is crossed; strict validation |
| `design` | `proposal`, `specs` | The Seams table, every scenario covered; a `doubt-driven-development` challenge for a multi-module design; a Presentation seam block when a surface consumes the change |
| `tasks` | `specs`, `design` | Session shape, tracer-bullet slices (published when multi-session), one surface slice per consumer surface, and the Ship group |

- **Gate:** the grill. Facts are the agent's job; decisions are the user's.
- **Hatch:** a one-line `grill.md` stub when the user waives the interview.
- **Dispatches:** `flow-design` at `design`.
- **Apply:** `tdd` at agreed seams → full suite → **commit** → `code-review` from the
  slice's start commit → one follow-up commit for findings. `tasks.md`'s Session line sets
  the window: single-session apply continues in the planning window, with no `/clear`;
  multi-session runs each slice in a fresh session, or the human runs `/implement-spec`
  instead. A surface slice is impeccable's: build against the Presentation seam, `audit`,
  `polish`. After the last slice, `code-review-and-quality` reviews the whole change from
  `tasks.md`'s Base commit.
- **Reroute:** a defect → `bugfix-flow`; one decision wide → `rapid-flow`; a question →
  `spike-flow`; fog → `/wayfinder`.

### `bugfix-flow` — 3 artifacts

`diagnose → specs → tasks`, then `apply`.

| Artifact | `requires` | Carries |
|---|---|---|
| `diagnose` | — | diagnosing-bugs phases 1–4: the red feedback loop, minimised reproduction, ranked hypotheses, debug tag, fix layer, and seam; an optional Incident section |
| `specs` | `diagnose` | The case the spec missed or got wrong; the scenario is the reproduction made permanent |
| `tasks` | `specs` | Failing test, fix, cleanup, Ship |

- **Gate:** a red feedback loop. No red command, no hypotheses.
- **Hatch:** `skip_specs` when the spec already covered the case.
- **Apply:** phases 5–6. Watch the test fail *for the diagnosed reason*, fix at the agreed
  layer, re-run the loop on the original scenario, and grep the debug tag away.
  `code-review-and-quality` then flips a condition in the fix to prove the suite notices. A
  performance fix is kept only when its gain clears the measured noise. Offers
  `/retro`, and `/improve-codebase-architecture` when there was no correct seam.
- **Reroute:** a fix that changes promised behaviour → `feature-flow`; a fault in how a
  surface looks or reads → impeccable, with no change. If the fix does not hold, update
  `diagnose.md`, not the code.

### `refactor-flow` — 3 artifacts

`grill → design → tasks`, then `apply`. No `specs` artifact.

| Artifact | `requires` | Carries |
|---|---|---|
| `grill` | — | The module being deepened, its dependency category, and the external behaviour that must not change |
| `design` | `grill` | Target interface, seam and adapters, guard tests, and tests to replace |
| `tasks` | `design` | Guard tests first, then slices, or expand → migrate → contract |

- **Gate:** agreed guard tests at the external seam.
- **Dispatches:** `flow-design` at `design`; design-it-twice runs in the main session first
  when the user wants alternatives.
- **Apply:** replace, don't layer. A shallow test goes only once its replacement passes.
  Surface files are restructured through `impeccable extract` with every rendered state
  unchanged; `code-review-and-quality` closes the change.
- **Reroute:** a guard assertion that has to change → `feature-flow`.

### `spike-flow` — 2 artifacts

`question → findings`; `apply` tracks `question.md`.

- **Gate:** a hard timebox and answer criteria.
- **Apply:** `prototype` and `research` experiments. The prototype stays on its branch and
  never merges.
- **Post-apply:** `findings.md`, gated by `question.md`'s last checkbox.
- **Scope:** "what should it look like" goes to impeccable (`generate` or `shape`), not here.

### `upgrade-flow` — 3 artifacts

`inventory → surfaces → tasks`, then `apply`. No `specs` artifact.

| Artifact | `requires` | Carries |
|---|---|---|
| `inventory` | — | Breaking changes from `research` over primary sources, each with an applies-to-us verdict |
| `surfaces` | `inventory` | Search-verified call sites, classed mechanical / behavioural / rendered / unknown |
| `tasks` | `surfaces` | Bump → codemods → batches → behavioural surfaces with equivalence checks → shims deleted |

- **Gate:** the research file. Verdicts wait for it.
- **Apply:** rewritten call sites come from the target version's docs through
  `source-driven-development`; a rendered surface gets `impeccable audit` before and after;
  the lockfile commits with its code; `wizard` scripts the human-only steps.
- **Reroute:** an unknown surface → `spike-flow`; a deliberate behaviour change →
  `feature-flow`.

### `setup-flow` — 2 artifacts

`decisions → tasks`, then `apply`. No `specs` artifact.

- **Gate:** the stack decisions, each with its ADR.
- **Apply:** the human runs `/setup-matt-pocock-skills` first; a walking skeleton with one
  real `tdd` test green in CI; every `CONSTRAINTS.md` row (written by
  `constraint-driven-development`) wired and proven to fail on a violation; `impeccable init`
  on a UI project; `wizard` for secrets and provisioning.

### `rapid-flow` — 2 artifacts

`proposal → tasks`, then `apply`, in one window. No `specs` artifact.

- **Gate:** the contract check in `proposal.md`.
- **Reroute:** a contract or a real decision → `feature-flow`.

## Rules that apply to every chain

- **Driving a chain is `/openspec-continue-change <change>`, once per artifact.** Name the change every
  time. Both `continue` and `apply` infer it from the conversation when the name is omitted
  and have to ask when they cannot, and `continue` is also how a change is resumed in a
  brand-new session — it reads the filesystem, not the history.
- **`tasks.md`'s Session line decides whether to clear before implementing.**
  Single-session apply continues in the planning window. Multi-session runs each slice in
  a fresh session: `/clear`, then `/model` (model up/down, its effort left/right) or
  `/effort`, then `/openspec-apply-change <change>` — clearing **first**, because a switch
  made inside a full window still drags that window along, and with the name, because
  clearing is exactly what removes what `apply` would have inferred it from. Nothing is
  lost: status is filesystem existence.
- **Do not clear between planning artifacts.** Re-picking model and effort at an artifact
  boundary is always free. Clearing there is not: the flows want their planning artifacts
  in one unbroken window and, at a phase boundary, prefer continuing, then `/clear`,
  `/handoff`, a subagent, and `/compact` last.
- **Delta spec format.** Scenarios need exactly four hashes (`#### Scenario:`) — three, or
  a bullet, does not parse. A `MODIFIED` requirement replaces the whole block, so it must
  carry every surviving scenario.
- **Post-apply artifacts are gated by checkboxes, not files.** `spike-flow`'s `findings`
  is written after the work, and the archive warning counts *tracked checkboxes*. Ticking
  the last box before writing the artifact is how one quietly never happens.
- **Escape hatches live in the change's `.openspec.yaml`.** The CLI reads `skip_specs` and
  `retire_capabilities`; it reads no other skip key, so a waived interview needs a one-line
  stub file to unblock the graph.
- **Archiving non-interactively** needs the change name and `--yes`, or it exits 1.
- **A subagent inherits nothing** — no conversation, no files read, no skills invoked, and
  no `AskUserQuestion`. Its prompt names every input, and a gate that needs a human answer
  drafts and returns the question for the caller to ask.

Sources: the seven `schema.yaml` files under `payload/openspec/schemas/*/`,
`payload/openspec/ROUTING.md`, `payload/agents/flow-design.md`, and
`skills/configuring-openspec/references/`.
