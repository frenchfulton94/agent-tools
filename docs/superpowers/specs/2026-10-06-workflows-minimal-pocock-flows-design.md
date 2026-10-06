# Pocock-driven SDLC flows for the workflows plugin's minimal level

Date: 2026-10-06
Status: approved design, awaiting implementation plan

## 1. Goal

The `workflows` plugin's `minimal` level ships two OpenSpec schemas today:
`mattpocock-bridge` for features and `bugfix-flow` for defects. Both were
written against an older release of Matt Pocock's skills, and both have
drifted from it.

This design replaces them with seven change-type schemas, modelled on the
`advanced` level's set. Each artifact is driven by a skill from
mattpocock-skills 1.3.1, or offers the human one of its user-invoked commands.
Impeccable owns user interface design and user interface code; the flows own
functionality.

The design also fixes the defects listed in section 4.

## 2. Decision log

Each row records a decision the user made during design. A later change to one
of these reopens the design; it is not an implementation detail.

| # | Decision |
|---|---|
| 1 | Schema instructions call only Pocock skills and OpenSpec. No artifact depends on another skill. |
| 2 | Impeccable owns UI/UX: look, feel, layout, copy, accessibility, and the surface code. OpenSpec changes own functionality. Flows never call impeccable; they name it as the owner and track a hand-off. |
| 3 | Seven schemas ship. Hotfix folds into `bugfix-flow` as an optional Incident section, preceded by a mitigate-first routing rule. |
| 4 | Schema names take a `-flow` suffix: `feature-flow`, `bugfix-flow`, `refactor-flow`, `spike-flow`, `upgrade-flow`, `setup-flow`, `rapid-flow`. |
| 5 | Setup gains a guarded retirement step for `mattpocock-bridge` and the three old agents. |
| 6 | One custom agent ships: `flow-design`, pinned to the top model. The two review agents retire; review calls `code-review` directly. |
| 7 | Schema instructions are thin glue. They call model-invoked skills, carry only OpenSpec mechanics, and restate a user-invoked skill's discipline in a few lines. A roster test pins every skill name. |
| 8 | Each schema description stamps the upstream version it was written against. |
| 9 | The `learn/` curriculum refresh is a separate sub-project. |

## 3. Upstream baseline

### 3.1 mattpocock-skills 1.3.1

Source: `github.com/mattpocock/skills` at the 2026-10-06 head, plus its
`docs/` pages, `CHANGELOG.md`, and the v1.1 to v1.3 release posts.

| Invocation | Skills |
|---|---|
| Model-invoked (11) | `tdd`, `diagnosing-bugs`, `domain-modeling`, `codebase-design`, `code-review`, `prototype`, `research`, `pr`, `wizard`, `grilling`, `writing-for-agents` |
| User-invoked (16) | `ask-matt`, `grill-with-docs`, `grill-me`, `implement`, `implement-spec`, `improve-codebase-architecture`, `retro`, `setup-matt-pocock-skills`, `to-spec`, `to-tickets`, `triage`, `wayfinder`, `handoff`, `to-questionnaire`, `teach`, `wait-what` |

No skill can call a user-invoked skill. A schema instruction therefore calls
model-invoked skills through the Skill tool, and offers user-invoked commands
to the human.

Facts from upstream that bind this design:

- `CONTEXT.md` and `CONTEXT-MAP.md` became `GLOSSARY.md` and `GLOSSARY-MAP.md`
  in 1.3.0.
- `tdd` is red then green only. Refactoring belongs to the review stage.
- `code-review` diffs `<fixed-point>...HEAD`, so it sees committed work only.
  It runs its Standards and Spec axes as its own parallel sub-agents.
- The `grill-with-docs` docs page reports a filed, unfixed bug. Inside a
  wrapper pipeline, the glossary-writing half "silently does not happen".
- Upstream rejects routing grilling through a harness question tool. A user
  can opt in through their own `CLAUDE.md`.
- The v1.3 main flow ends `code-review → pr → retro`. The author says not to
  automate `/retro`.
- `/implement-spec` resolves tickets but never edits a local checklist. The
  author recommends a deterministic per-ticket loop over it for most AFK work.

### 3.2 impeccable 4.5.0

Source: the installed skill and its `reference/` files, plus
`impeccable.style`. 4.5.0 is the current release.

- One model-invoked skill with 24 commands, passed as arguments.
- Stores: `PRODUCT.md`, `DESIGN.md` with the `.impeccable/design.json` sidecar,
  surface briefs under `.impeccable/surfaces/`, and `.impeccable/config.json`.
- `shape` runs a discovery interview and returns a brief. It never writes code.
- It has no notion of a seam. `harden`, `onboard`, `optimize`, and `extract`
  edit state, error handling, and data fetching unless told otherwise.
- It has no input slot for an engineering contract and no fixture harness.
- Its design hook scans `.ts` and `.js` edits as well as markup.

## 4. Defects fixed

| # | Defect in the current minimal level | Fixed in |
|---|---|---|
| D1 | Instructions name `CONTEXT.md`. On 1.3.1 an agent starts an empty `GLOSSARY.md` beside it. | 5.1, 13 |
| D2 | The skill roster omits `pr`, `wizard`, `writing-for-agents`, `/implement-spec`, `/retro`, and `/ask-matt`. | 5.5, 8 |
| D3 | The `code-review → pr → retro` close of the main flow is missing. | 5.5 |
| D4 | Apply reviews before it commits, so both reviewers diff an empty range. | 5.4 |
| D5 | Two review agents each call `code-review`, which fans out again. The Standards agent carries a second smell list. | 5.4, 11 |
| D6 | Glossary writes inside OpenSpec can silently drop, and nothing checks them. | 5.2 |
| D7 | `bridge-design-gate` demands a long ADR form that contradicts `domain-modeling`'s ADR format. | 10 |
| D8 | `bugfix-flow` omits the feedback loop, hypotheses, minimisation, the no-seam finding, and cleanup. | 7.2 |
| D9 | Grilling rounds route through AskUserQuestion. | 5.2 |
| D10 | Apply always starts with `/clear`, even for single-session work. | 5.3 |
| D11 | Design is optional, yet apply requires seams agreed in `design.md`. | 7.1 |
| D12 | Nothing installs `CLAUDE.md.fragment.md`. | 8 |
| D13 | `choosing-a-workflow` infers the level by counting schemas. | 12 |
| D14 | Nothing validates payload schemas or payload agents. | 13 |

## 5. Shared conventions

These bind all seven schemas.

### 5.1 Standing stores

Each fact goes to the store that owns it.

| Store | Holds | Owner |
|---|---|---|
| `openspec/specs/` | Behaviour | OpenSpec archive |
| `GLOSSARY.md`, or `GLOSSARY-MAP.md` | Domain vocabulary | `domain-modeling` |
| `docs/adr/` | Decisions that still bind the next change | `domain-modeling` |
| `CODING_STANDARDS.md` | Judgement-call standards read by `code-review` | `/retro` |
| `docs/agents/*.md` | Tracker, labels, domain-doc layout | `/setup-matt-pocock-skills` |
| `PRODUCT.md`, `DESIGN.md`, `.impeccable/` | Product context, visual system, surface briefs | impeccable |

A flow MAY read impeccable's stores. A flow MUST NOT write them. Commands come
from the repository's own manifests and scripts.

### 5.2 Interviews and domain-model writes

- A grilling step calls the Skill tool twice, for `grilling` and
  `domain-modeling`.
- Rounds use `grilling`'s text format: numbered questions, each with a
  recommended answer.
- AskUserQuestion MAY carry approve-or-adjust sign-offs only: seams, the
  ticket breakdown, and an ADR yes or no.
- Every artifact that grills ends with a **Domain terms settled** section. It
  lists the glossary terms added or changed and the ADRs written, or says
  "none".
- That artifact MUST NOT be marked done until the list matches `git diff` on
  `GLOSSARY.md` and `docs/adr/`.

### 5.3 Session shape

Planning artifacts run in one unbroken context window. The tasks artifact then
records one of two shapes:

- **Single-session.** Apply continues in the same window. Tasks live in
  `tasks.md` only.
- **Multi-session.** Tasks publish to the tracker as tickets with blocking
  edges. Each slice runs in a fresh session through `/opsx:apply <change>`.
  The human MAY instead run `/implement-spec` over the whole ticket graph.

Phase boundaries follow upstream's order: continue, `/clear`, `/handoff`,
subagent, `/compact`.

### 5.4 Slice close-out order

Every apply step except `spike-flow`'s closes a slice in this order:

1. Write tests at the agreed seams with `tdd`.
2. Typecheck and run the affected tests as the work proceeds.
3. Run the full suite.
4. Commit.
5. Call `code-review` with the slice's start commit as the fixed point. Pass
   the change's planning artifacts as the spec source.
6. Fix the findings in a follow-up commit. Do not loop the review until it
   comes back clean.
7. Tick `tasks.md` and update the issue.

The apply instruction SHOULD tell the human that `code-review` judges best from
a fresh session on a strong model.

### 5.5 Shipping

- `tasks.md` ends with a **Ship** group. Its boxes MUST be ticked before
  archive. Archive's unchecked-box warning is the gate.
- Where work goes up as a pull request, the agent calls `pr` and gives it the
  change's specs as well as the diff.
- After the final slice, apply offers `/retro`. It MUST NOT run `/retro`
  itself.
- After `/implement-spec` returns, apply ticks `tasks.md` from the closed
  tickets.

### 5.6 Escape hatches

The CLI reads two change flags: `skip_specs` and `retire_capabilities`. Any
other skip, such as skipping the interview, MUST write a one-line stub file
holding the reason and the date.

## 6. The UI boundary

The UI is an adapter at a presentation seam.

- **A flow owns everything behind the seam:** domain state, data fetching and
  mutation, validation, permissions, and the interface the surface consumes.
  Its specs and `tdd` tests sit at that seam.
- **Impeccable owns the surface:** components, layout, presentation-only state,
  copy, accessibility, and motion.

Rules that follow from the split:

1. A behavioural state, such as "permission denied returns an error", is a
   spec scenario. How that state looks and reads belongs to impeccable.
2. An error kind is behaviour. The message a user reads is presentation. Specs
   assert the kind, never the wording.
3. When an impeccable command finds a behaviour gap, it names the gap. The
   human opens or extends a flow change. Impeccable builds only the
   presentation of what the seam already emits.
4. When a surface consumes a seam, `design.md` carries a **Presentation seam**
   block. The block names the interface, every emitted state, the error kinds,
   the fixtures, and the consumer surface's brief path.
5. That seam ships one fixture per emitted state, so impeccable can render
   every state for critique and review.
6. A change whose surface must ship with it carries one Ship box: "Surface
   hand-off: impeccable builds `<surface>` against `<seam>`."

Which side starts:

- **UI/UX-led requests** start in impeccable. When `shape`'s brief needs
  functionality that does not exist, the human opens a `feature-flow` change
  for it. Grill reads the brief and asks only behaviour questions.
- **Functionality-led requests** start in `feature-flow`. Grill hands
  look-and-feel to impeccable and records it under Handed downstream.

Rules 3 to 6 reach impeccable through `ROUTING.md` (section 8), because
impeccable's own prompts are read-only plugin files.

## 7. The seven flows

### 7.1 feature-flow

Chain: `grill → proposal → specs → design → tasks → apply`.

**grill**

- Classify the change first. Reroute a defect to `bugfix-flow`. Reroute
  one-decision work to `rapid-flow` and a question in disguise to
  `spike-flow`.
- Fog too big for one change stops the flow. Offer `/wayfinder`, whose cleared
  map re-enters at the proposal.
- Read any source first: a `/triage` agent brief, a wayfinder map, or an
  impeccable brief.
- Interview with `grilling` and `domain-modeling`.
- A logic question detours to `prototype`, kept on a `prototype/<name>`
  branch. A facts question detours to `research`, written to
  `openspec/changes/<name>/research/<topic>.md`.
- Done when the user confirms shared understanding and section 5.2's list
  matches the diff.
- Template: Question, Decisions, Domain terms settled, Detours, Handed
  downstream, Still open.

**proposal**

- The `/to-spec` shape, kept in the change folder.
- Template: Problem, Solution, User Stories, Capabilities, Out of Scope,
  Impact.
- Synthesise from `grill.md` without a new interview.
- Done when every statement traces to `grill.md`.
- The instruction MUST NOT offer `/to-spec`. It publishes a `ready-for-agent`
  issue, which AFK pollers would build.

**specs**

- ADDED requirements trace both ways to the user stories.
- MODIFIED and REMOVED requirements start from the main spec. A MODIFIED block
  copies the whole requirement.
- Scenarios take exactly four hashtags and WHEN/THEN bullets.
- A new capability opens with `## Purpose`.
- Set `retire_capabilities` when the last requirement of a capability goes.

**design**

- Run the `flow-design` agent (section 10).
- Put each ADR candidate to the user as a yes or no.
- Resolve every question that would change the specs or the tasks.
- Get the Seams table approved or adjusted.
- Design MUST NOT be skipped. A one-module change shrinks `design.md` to the
  Seams table.

**tasks**

- Record the session shape (section 5.3).
- Slice tracer bullets. Prefactoring goes first. Each slice names its blocking
  edges.
- A wide refactor runs expand, migrate, contract. Batches that cannot stay
  green alone share an integration branch.
- Get the breakdown approved or adjusted.
- Multi-session: publish to the tracker, labelled `ready-for-agent`, with
  native blocking edges. Tickets become sub-issues of the source issue, where
  one exists. The human MAY run
  `/to-tickets` instead.
- `tasks.md` mirrors published tickets with their tracker references.
  Checkboxes use the exact `- [ ] X.Y` form.
- End with the Ship group.

**apply**

- Follow section 5.4.
- A wrong seam stops the slice. Agree a new seam and update `design.md`.

### 7.2 bugfix-flow

Chain: `diagnose → specs → tasks → apply`. The `diagnose` id is unchanged, so
in-flight changes still resolve.

**diagnose**

- Call `diagnosing-bugs`. Stop when Phase 4 confirms a cause.
- Reroute a raw incoming report to `/triage` first.
- Reroute a fix that changes promised behaviour to `feature-flow`.
- Redact output per the skill's Redact rule.
- Call `domain-modeling` only when a term the diagnosis depends on is fuzzy.
- Template:
  - **Incident** (optional): timeline, mitigation taken, approver.
  - **Feedback loop:** one command, already run, with redacted red output. It
    meets the skill's four bars: red-capable, deterministic, fast,
    agent-runnable.
  - **Minimised reproduction:** observed versus expected. Every remaining
    element is load-bearing.
  - **Hypotheses:** three to five ranked, falsifiable predictions, shown to the
    user before testing. Which one survived, with its evidence.
  - **Debug tag:** the `[DEBUG-xxxx]` prefix, so cleanup is one grep after a
    `/clear`.
  - **Fix layer:** symptom or cause, with reasoning. A symptom fix states what
    the cause fix needs.
  - **Seam:** a correct seam that exercises the real bug pattern, agreed with
    the user. Or "No correct seam", which is a finding.
  - **Also found:** same-cause faults become task groups. Unrelated faults are
    filed separately.

**specs**

- The spec covered the case: set `skip_specs: true`.
- The spec was silent: add an ADDED requirement.
- The spec was wrong: add a MODIFIED requirement, copying the whole block.
- In every case, the scenario is the minimised reproduction made permanent.

**tasks**

- Usually one group: a failing test at the seam, the fix, same-cause extras,
  and cleanup.
- A symptom fix shipped now gives its cause fix a separate group and tracker
  issue.
- The Ship group adds: the commit or PR names the confirmed hypothesis.

**apply**

1. Write the failing test at the seam with `tdd`.
2. Watch it fail for the diagnosed reason.
3. Make the smallest fix at the agreed layer.
4. Watch it pass.
5. Re-run the Phase 1 loop against the original scenario.
6. Run Phase 6 cleanup, then section 5.4 from step 3.

When the fix does not hold, update `diagnose.md`, not the code.

Apply ends by offering `/retro`. Where the seam finding was "No correct seam",
it also offers `/improve-codebase-architecture`.

**Scope:** a deviation from specified behaviour belongs here wherever the code
sits. Layout, contrast, copy, and polish problems go to impeccable. A
behaviour fix that needs a new presentation state lists it under Also found
and adds the surface hand-off box.

### 7.3 refactor-flow

Chain: `grill → design → tasks → apply`. No `specs` artifact, so changes
archive without a spec merge.

**Entry points:** a candidate from `/improve-codebase-architecture`, a bugfix
that found no correct seam, or a user request.

**Guard:** if behaviour observable at the external seam must change, reroute
to `feature-flow`.

**grill**

- Call `grilling` and `domain-modeling`, using `codebase-design`'s vocabulary.
- Settle the module being deepened, what moves behind the seam, the dependency
  category, and the external behaviour that must not change.
- When `/improve-codebase-architecture` already grilled the candidate in this
  window, record its decisions without a new interview.

**design**

- Run the `flow-design` agent.
- Cover the target interface, seam placement, and adapters.
- Name the guard tests: tests at the external seam that stay green unchanged.
  If none exist, the first task writes them.
- Apply "replace, don't layer": new tests at the deepened interface, and a list
  of shallow tests to delete once those cover them.
- When the user wants alternative interfaces, the main session runs
  `codebase-design`'s design-it-twice before running the agent. It fans out its own
  sub-agents, so it cannot run inside `flow-design`.

**tasks:** `to-tickets` discipline. A wide refactor runs expand, migrate,
contract.

**apply:** follow section 5.4. A changed guard assertion means behaviour moved:
stop and reroute to `feature-flow`. `code-review`'s spec source is `grill.md`
and `design.md`.

### 7.4 spike-flow

Chain: `question → findings`. Apply tracks `question.md`.

**Scope:** logic, state, feasibility, library choice, and outside facts. A
"what should it look like" question goes to impeccable's `generate` or `live`.

**question**

- Template: Question, Decision it informs, Timebox, Answer criteria,
  Experiments.
- Each experiment is a checkbox tagged prototype, research, or measurement.
- The last checkbox is "write findings.md".
- `grilling` MAY sharpen the question. If it runs, section 5.2 applies.

**apply**

- `prototype` builds a logic prototype or feasibility code on a
  `prototype/<name>` branch.
- `research` runs as a background agent into the change's `research/` folder.
- Hard-stop at the timebox.

**findings**

- Template: Answer, Evidence, Recommendation, Disposition.
- The prototype stays on its branch as a primary source and never merges.
- Name any validated pure module for lifting into a follow-up change.
- Name the follow-up change, or record a decision not to proceed.

### 7.5 upgrade-flow

Chain: `inventory → surfaces → tasks → apply`. No `specs` artifact.

**inventory**

- Call `research` against official release notes, changelogs, migration
  guides, and source.
- Wait for the research file. Facts are never guessed.
- Template: Current to target, Motivation, Stepping stones, Breaking changes.
- Each breaking change carries an applies-to-us verdict and a link to the
  cited research.

**surfaces**

- Find call sites for each applicable break by search, with paths and counts.
- Classify each surface:
  - **mechanical:** a codemod handles it;
  - **behavioural:** it needs an equivalence check at a named seam, usually
    `diagnosing-bugs`' differential loop;
  - **unknown:** spike first.
- List steps only a human can take, for `wizard`.

**tasks**

- Expand, migrate, contract: bump or dual-run, codemods, mechanical batches,
  behavioural surfaces with checks first, then delete shims.
- Name the rollback and any point of no return.

**apply**

- Follow section 5.4.
- Call `wizard` when a human must act.
- Commit the lockfile with the code.
- An unexplained behavioural diff stops the change: fix forward or roll back.
- A deliberate behaviour change is a `feature-flow` change.
- The PR evidence is the differential loop's before and after output.

### 7.6 setup-flow

Chain: `decisions → tasks → apply`. No `specs` artifact.

**decisions**

- Call `grilling` and `domain-modeling`.
- Template:
  - **Stack:** each choice links its ADR.
  - **Glossary seed:** written to `GLOSSARY.md`.
  - **Standards:** judgement calls for `CODING_STANDARDS.md`.
  - **Guardrails:** lint, typecheck, and test wired into pre-commit or CI.
  - **Human-only steps:** these become `wizard` stages.
  - **Deferred decisions.**

**tasks and apply**

- The first task asks the human to run `/setup-matt-pocock-skills`. Tracker
  publishing waits for it.
- Then: scaffold, a walking skeleton with one real `tdd` test green in CI, and
  the guardrail.
- `wizard` handles infrastructure set-up and secrets.
- `CLAUDE.md` gets navigation pointers only.
- A project with UI adds a hand-off box: the human runs `/impeccable init` and
  `/impeccable document`.

### 7.7 rapid-flow

Chain: `proposal → tasks → apply`, in one context window. No `specs`
artifact.

- **proposal:** one or two paragraphs of what and why.
- **Guard:** a decision with real alternatives, or a touched contract, means
  recreate under `feature-flow`. A contract is specified behaviour, a public
  API, a data schema, or a config key.
- **apply:** `tdd` where behaviour is testable, then commit, `code-review`,
  and `pr` when the change goes up as a pull request. Offer `/retro` only when
  the change went sideways.

### 7.8 Artifact ids shared across schemas

A config rule keyed to an artifact id fires in every schema that uses the id.
Each shared rule MUST read correctly in all of them.

| Id | Schemas |
|---|---|
| `grill` | feature-flow, refactor-flow |
| `proposal` | feature-flow, rapid-flow |
| `specs` | feature-flow, bugfix-flow |
| `design` | feature-flow, refactor-flow |
| `tasks` | every schema except spike-flow |

## 8. Routing

`openspec/ROUTING.md` replaces `CLAUDE.md.fragment.md`.

- Setup's step 6 names `ROUTING.md` at every level.
- `CLAUDE.md` gets one pointer line.
- Config `context:` repeats "read the router before creating a change".

**Decision tree, first match wins:**

1. Production broken now: mitigate first, then `bugfix-flow` with the Incident
   section.
2. A new project bootstrap: `setup-flow`.
3. Behaviour deviates from spec or intent, including performance:
   `bugfix-flow`. A raw report goes to `/triage` first.
4. A dependency, framework, or platform version change: `upgrade-flow`.
5. Structure changes and external behaviour must not: `refactor-flow`.
   Coverage backfill is a refactor with no restructure.
6. An open question answered by building or reading: `spike-flow`.
7. A new capability or intentional behaviour change, including removals:
   `feature-flow`.
8. A small code change, one decision wide, with no contract: `rapid-flow`.
   Typos, docs, and lint fixes are a direct commit.

**Work that never becomes a change:**

- UI/UX-led work goes to impeccable, under section 6's rules.
- `/wayfinder` maps fog too big for one change.
- `/to-questionnaire` serves an answer held by someone else.
- `/ask-matt` picks a Pocock skill.

**Guardrails:**

- Escalate rapid to feature when a contract appears.
- Escalate refactor to feature when a guard assertion changes.
- Escalate bugfix to feature when the fix changes promised behaviour.
- Escalate upgrade to feature when a behaviour change is deliberate.
- De-escalate a feature grill to rapid or spike when it shrinks.
- When two schemas fit, ask one question.

**Operational notes for impeccable:**

- Exclude engineering directories from its design hook with
  `/impeccable hooks ignore-file <glob>`.
- During a flow's apply, surface work goes through the hand-off, not
  mid-slice.

`ROUTING.md` SHOULD stay under about 120 lines.

## 9. Config

`config.yaml.example`:

- `schema: feature-flow`. It defines `proposal`, which `verify.mjs` probes.
- `context:` stays short, because it loads on every artifact. It carries:
  - read the router;
  - read `GLOSSARY.md` and relevant ADRs before exploring, silently if absent;
  - section 5.1's store ownership;
  - the tracker config lives in `docs/agents/issue-tracker.md`;
  - grilling uses text rounds, and AskUserQuestion carries sign-offs only.
- `rules:` ships one `proposal` rule: "Name domain concepts with
  `GLOSSARY.md` terms." Every gate and completion criterion lives in the
  schema instructions, so a schema upgrade never strands a config rule.

## 10. The flow-design agent

`payload/levels/minimal/agents/flow-design.md`:

- **Frontmatter:** model `opus`, effort `xhigh`, tools Read, Grep, Glob, Skill,
  Bash.
- **Run by** the `feature-flow` and `refactor-flow` design artifacts, which
  pass the change directory path.
- **Reads:** `grill.md`, `proposal.md` and the specs for features,
  `GLOSSARY.md`, `docs/adr/`, and the touched code.
- **Calls:** `codebase-design`, and `domain-modeling` for ADR candidates.
- **Returns three things:**
  1. A `design.md` draft. Its sections are Context, Goals and Non-Goals,
     Decisions, Seams, Risks, Migration, and Open Questions. Seams carries a
     regression row per REMOVED requirement. A consumed module adds the
     Presentation seam block. A refactor adds the guard tests and the shallow tests to
     replace.
  2. ADR candidates in `domain-modeling`'s format, each with its three-part
     test spelled out.
  3. Caller actions: questions that change specs or tasks, the seam sign-off,
     and confirmation of any consumer surface.
- **Partial chain:** a missing input returns only the caller actions.

## 11. Installer: retirement

- The level ships `payload/levels/minimal/retired.json`, listing `mattpocock-bridge` and the agents
  `bridge-design-gate`, `code-review-spec`, and `code-review-standards`.
- `plan.mjs` classifies a retired name on disk as **retire** only when all
  three hold:
  - the install record lists it;
  - its hash matches the record;
  - no open change's `.openspec.yaml` names it.
- Every other retired name is **kept**, and the plan reports the reason.
- Setup shows the retire list and deletes entries only after the user
  confirms.
- `record.mjs` drops deleted entries from `.claude/workflows.json`.

## 12. Skill and documentation prose

**`choosing-a-workflow`**

- Detect the level by schema names. The `-flow` set means minimal.
- Walk a level's `ROUTING.md` whenever one exists.
- `references/chains.md`: one section per flow.
- `references/model-effort.md`: drop the two review-agent rows and rename the
  design row.
- `evals/cases.md`: update Case 3.
- The description MUST keep schema names un-backticked. The marketplace
  integrity test treats a backticked hyphenated name as a skill pointer.

**`setup/SKILL.md`**

- Rewrite the minimal row of the level table.
- Name `ROUTING.md` in step 6 for every level.
- Replace the rule-sorting example, which names `mattpocock-bridge`.
- Add the retirement step.

**Elsewhere**

- `scripts/config-facts.mjs`: update the comment naming the old schemas.
- Plugin `README.md`: update the levels table counts.
- `plugin.json` and `marketplace.json`: update the schema count in the
  description. The two MUST stay byte-identical.

## 13. Tests

New file: `tests/workflows-minimal-flows.test.ts`.

1. **Roster.** A fixture holds the 1.3.1 roster from section 3.1.
   - Every `Call the Skill tool with "X"` names a model-invoked skill.
   - Every offered `/command` is one of: a Pocock user-invoked skill, an
     `/opsx:*` command, a harness built-in, or `/impeccable …` offered to the
     human.
   - `Call the Skill tool with "impeccable"` never appears.
   - Every schema description's version stamp matches the fixture.
2. **Retired terms.** `CONTEXT.md`, `CONTEXT-MAP.md`, `to-prd`, `to-issues`,
   `/diagnose`, and `mattpocock-bridge` appear nowhere in the minimal payload
   except `retired.json`.
3. **Structure.**
   - Every `schema.yaml` parses.
   - Artifact ids are unique. Every `requires` target exists, and the graph is
     acyclic.
   - Every referenced template exists.
   - Task templates use the exact `- [ ] ` checkbox form.
   - The config's default schema exists and defines `proposal`.
4. **Disjoint names.** Minimal's schema and agent names collide with no other
   level's. This pins the assumption in `record.mjs`.
5. **Agent.** `flow-design.md` frontmatter carries name, description, tools,
   model, and effort. `bun run audit` does not cover payload agents.

`tests/workflows-plan.test.ts` gains cases for retirement: retire, kept
because the user changed it, and kept because an open change uses it.

`openspec schema validate` stays a setup-time check. The plan runs it by hand
against a scratch project.

## 14. Versioning and catalog

- `workflows`: minor bump, 0.7.0 to 0.8.0.
- `bun run audit --since <ref>` confirms nothing else changed without a bump.

## 15. Process requirements

Section 14 of `2026-09-13-workflows-apple-native-design.md` binds this change.
Every implementation task MUST load the skills its surface requires before
editing.

| Work surface | Required skill(s) |
|---|---|
| Schemas, templates, `ROUTING.md`, `config.yaml.example` | `configuring-openspec` |
| Schema `instruction:` blocks, the agent prompt, template wording | `improving-prompts` |
| `flow-design.md` | `authoring-subagents` |
| `SKILL.md` edits | `authoring-skills` |
| Payload layout, version bump, plugin README | `authoring-plugins` |
| Marketplace entry | `maintaining-plugin-marketplaces` |

## 16. Verification before commit

- `bun test` passes.
- `bun run audit` passes.
- `claude plugin validate .` passes.
- A scratch-repo dry run:
  - setup runs at `minimal`;
  - `verify.mjs` reports green;
  - `openspec schema validate` passes for all seven flows;
  - `openspec validate` accepts a change under a schema with no `specs`
    artifact, on OpenSpec 1.14.0.

## 17. Deferred

Recorded as decisions, not omissions:

- **`learn/` curriculum.** About 30 files cite the old names or the "two
  schemas" count. Sub-project 2 rewrites them. Until then they are known
  drift.
- **A hotfix schema.** Revisit if a Pocock incident skill ships.
- **A presentation-seam fixture harness.** Section 6 requires fixtures per
  state. A shared harness to render them is a later change.

## 18. Invariants kept

- The minimal level's `settings.json` enables only `mattpocock-skills`.
- Setup deletes nothing without the user's confirmation.
- `bugfix-flow` keeps its name and its `diagnose` id.
- No minimal schema calls a skill outside mattpocock-skills 1.3.1.
