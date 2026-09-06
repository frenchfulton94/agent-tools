# The twelve chains

Everything needed to fill in the chain, gate, and hatch lines of a routing answer, and to
drive the chain afterwards. Read only the section for the schema you routed to.

Contents:

- [How to read these](#how-to-read-these)
- [`minimal` — mattpocock-bridge, bugfix-flow](#minimal)
- [`standard` — craft-driven, surface-driven](#standard)
- [`advanced` — the everyday four](#advanced--the-everyday-four)
- [`advanced` — the situational four](#advanced--the-situational-four)
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

**Every skill invocation carries a fallback chain** ending in "follow the template
manually". A schema that names a skill the session does not have degrades; it does not
fail. Skill names are written `pack:skill`, and installation prefixes vary — confirm the
exact name in the agent's skill list.

## `minimal`

### `mattpocock-bridge` — 6 artifacts, the config default

`grill → proposal → surface → specs → design → tasks`, then `apply`.

| Artifact | `requires` | Carries |
|---|---|---|
| `grill` | — | Interview in rounds; `CONTEXT.md` and ADRs written inline |
| `proposal` | `grill` | Problem / Solution / User Stories, plus the Capabilities contract |
| `surface` | `proposal` | Design brief: visitor mode, states and ranges, direction, boundaries |
| `specs` | `proposal`, `surface` | Delta specs. `ADDED` from the user stories; `MODIFIED`/`REMOVED` from the existing main spec |
| `design` | `proposal`, `specs` | Deep-module vocabulary and the **Seams** table, every scenario covered by name |
| `tasks` | `specs`, `design` | Tracer-bullet slices published to the tracker, mirrored as checkboxes |

- **Gate:** the grill. Facts are the agent's job; decisions are the user's.
- **Hatches:** `skip_grill` and `skip_surface` (stub file required — the CLI does not read
  either key), `skip_specs` (the CLI does read this), and `design` skipped deliberately
  when the change is one module with no new dependency and no security, performance, or
  migration question.
- **Config rule:** confirm the Seams table with the user before marking `design` done.
- **Dispatches:** `bridge-design-gate` at `design`; `code-review-standards` and
  `code-review-spec` in parallel at each slice's review.
- **Apply:** one slice per session. Failing test at an agreed seam → smallest code to pass
  → affected tests as you go, full suite at the end → the design pass on visible surfaces →
  the two-axis review → tick and commit. Then stop; a session degrades past roughly 150k
  tokens and each slice is self-contained by construction.
- **Reopen:** if the grill realises this is a defect, offer
  `/opsx:new <what the fix really is>, using bugfix-flow` — or the terminal form,
  `openspec new change <name> --schema bugfix-flow`.

### `bugfix-flow` — 3 artifacts, selected per change

`diagnose → specs → tasks`, then `apply`.

| Artifact | `requires` | Carries |
|---|---|---|
| `diagnose` | — | Reproduction, root cause, fix layer with reasoning, and the seam the regression test sits at |
| `specs` | `diagnose` | The case the spec was silent about, as an `ADDED` requirement whose scenario is the reproduction made permanent |
| `tasks` | `specs` | Failing test first, then the fix |

- **Gate:** a written root cause. Nothing is written until it is.
- **Hatch:** `skip_specs` where the spec already covered the case and the code simply
  disagreed — the regression test holds the line.
- **Apply:** watch the test fail *for the reason the diagnosis gave*, not an unrelated one.
- **Reopen:** a fault whose fix is a redesign is a change, not a bugfix — reopen under
  `mattpocock-bridge`. If the reproduction still triggers after the fix, the artifact to
  update is `diagnose.md`, not the code.

## `standard`

### `craft-driven` — 7 artifacts, the config default

`brainstorm → proposal → specs + design-brief + design → tasks → apply → verification`.

| Artifact | `requires` | Notes |
|---|---|---|
| `brainstorm` | — | Record the exact message in which the user approved the intent |
| `proposal` | `brainstorm` | Its **Surfaces** line is the switch for the whole UI path |
| `specs` | `proposal` | |
| `design-brief` | `proposal` | **Only if** Surfaces names at least one user-facing surface. "None — no UI impact" means skip it and say why |
| `design` | `proposal` | **Only if** cross-cutting, new pattern, new dependency, significant data-model change, security/performance/migration complexity, or genuine ambiguity |
| `tasks` | `specs`, `design-brief`, `design` | |
| `verification` | `tasks` | The archive gate |

- **Gate:** `verification`. Archive warns until it exists.
- **Dispatches:** `craft-design-gate` at `design`; `verification-reviewer` at
  `verification` step 3, prompted with the change directory path, the base SHA, and the
  head SHA.
- **Evidence rule:** every claim backed by a command run *while writing that file*. A run
  from earlier in the session is not evidence, and a subagent's success report is a lead.
  Ready-to-archive with a Critical finding unresolved contradicts itself.

### `surface-driven` — 5 artifacts, selected per change

`design-brief → proposal → specs → tasks → apply → quality`. Strictly linear.

| Artifact | `requires` | Notes |
|---|---|---|
| `design-brief` | — | Leads. Visitor mode, visual authority, direction, states and ranges, anti-goals |
| `proposal` | `design-brief` | Deliberately short — the brief already carries the decisions |
| `specs` | `proposal` | Largely a translation of States-and-Ranges into scenarios |
| `tasks` | `specs` | Design tasks with inspection steps, behaviour tasks with TDD |
| `quality` | `tasks` | The archive gate: critique → audit → behaviour evidence → brief fidelity → verdict |

- **Visual authority:** the surface either inherits the incumbent visual world (refinement
  preserves) or a replacement world was chosen and approved (redesign replaces). Never
  split the difference.
- **Dispatches:** none pinned — the quality pass runs in the main session.

## `advanced` — the everyday four

### `feature` — 10 artifacts, the config default

`brainstorm → constraints → proposal → specs → design → migration → review → tasks → plan
→ verification`. Strictly linear.

- **Gate:** `review` must **PASS** before `tasks`. On BLOCK, surface the `[Critical]`
  findings, fix the *upstream artifacts*, and re-dispatch. Do not soften or re-adjudicate
  the findings — the gate runs on a stronger model than the session.
- **Dispatches:** `design-gate` at `design`. At `review`, `taste-preflight` first when the
  proposal's Surfaces line names any surface, then `review-gate` with the pre-flight
  findings carried verbatim; write its returned content as `review.md` verbatim.
- **Two files, two jobs:** `tasks.md` is the coarse tracked checklist, with checkboxes in
  exactly the `- [ ] ` form — any other shape is invisible to progress tracking, not an
  error. `plan.md` is the micro-step, two-to-five-minute decomposition with the real
  failing-test code in a fenced block above each checkbox. Placeholders in `plan.md` are
  plan failures.
- **Scales down:** `constraints` and `migration` can be three lines for net-new flag-gated
  work.

### `bugfix` — 4 artifacts

`reproduction → rootcause → fix → tasks`.

- **Gate:** no fix proposed before `rootcause` completes. Trace to the faulty assumption,
  not the faulty line.
- **Also does:** a same-class scan elsewhere in the codebase, recording hits or "none
  found"; each hit becomes a task, addressed or explicitly ticketed.
- **Spec classification** in `fix`, with its common answer named: spec covered the case and
  the code disagreed → no delta; **spec was silent → an `ADDED` requirement, and expect
  this to be the common outcome**; spec said something the fault proves wrong → `MODIFIED`,
  copying the entire requirement block header included, since archive matches on that
  header.
- **Performance:** the measured target from `reproduction` *is* the regression guard.
- **Symptom fixes are legitimate when written down** — state what a proper cause fix would
  require, so the next person inherits the choice rather than the surprise.

### `refactor` — 3 artifacts

`characterization → strategy → tasks`.

- **Gate:** behaviour pinned by tests and coverage gaps closed before any code moves.
- **Per task:** one mechanical step — extract, rename, move, inline — with the acceptance
  criterion "suite green, no assertion changed".
- **Degenerate case:** coverage-only work. State "no restructure" and let `tasks` be the
  test list.

### `rapid` — 2 artifacts

`proposal → tasks`.

- **Gate:** the contract check, inside the proposal. Discipline rides in config rules
  rather than extra artifacts.
- **Still does:** TDD, full suite and lint, and an evidence-before-completion pass. Cheap
  is not unverified.

## `advanced` — the situational four

### `setup` — 3 artifacts

`decisions → conventions → tasks`.

- **Inverts:** no `specs` artifact — no behaviour exists yet to spec.
- `decisions` is a one-question-at-a-time stack interview; at bootstrap nearly every choice
  passes the ADR three-gate test.
- `conventions` is written **to be copied, not summarized** — it is materialized during
  apply into `CONTEXT.md`, `AGENTS.md`, the OpenSpec config context, and a `DESIGN.md` stub.
- **Exit criterion:** a walking skeleton — the thinnest end-to-end slice building, testing,
  and deploying green in CI.
- `TOOLS.md` is generated *after* the skeleton, never at scaffold time: the owning skill
  forbids writing it before evidence exists on disk.

### `spike` — 2 artifacts

`question → apply → findings`. Apply tracks `question.md`, whose experiment checkboxes are
the task list.

- **Gate:** a hard timebox. When it expires, findings get written with whatever evidence
  exists — an unbounded spike is unplanned development.
- Apply runs in an isolated worktree that never merges, with quality bars relaxed by design.
- **Mandatory disposition:** code discarded, plus either a follow-up `feature` change for
  the learnings or an explicit decision not to proceed.

### `upgrade` — 5 artifacts

`inventory → surfaces → migration → tasks → verification`.

- **Inverts:** the constraints come from someone else's release notes, and success means
  behaviour is *unchanged*.
- `inventory` cites official release notes and changelogs **by URL** — memory of an API is
  not evidence of its current shape — and gives each breaking change an applies-to-us
  verdict.
- **Gate:** `surfaces`. Real call sites by search (grep or AST) with paths and counts.
  Start from `TOOLS.md`'s dependency map where it exists, then grep-verify: the map
  narrows, the search proves. Classify each surface mechanical (codemod), behavioral (needs
  an equivalence test), or unknown (spike first).
- **Never** ship a changed behaviour as an upgrade. On an unexplained behavioural diff,
  stop and fix forward or roll back. Commit the lockfile with the code and refresh
  `TOOLS.md`.

### `hotfix` — 3 artifacts

`triage → tasks → apply → postmortem`.

- **Inverts:** depth comes after shipping. `triage` takes minutes, not hours.
- First diagnostic is **what changed recently** — deploys, flags, config. Decide rollback
  versus forward-fix explicitly and name the approver.
- **Rollback beats forward-fix when both are viable** — faster and better understood.
- Every task names the observable signal proving it worked.
- **Mandatory:** `postmortem` is blameless, applies the full investigation rigour triage
  skipped, and **creates the linked follow-up change** for the durable fix.

## Rules that apply to every chain

- **Driving a chain is `/opsx:continue <change>`, once per artifact.** Name the change every
  time. Both `continue` and `apply` infer it from the conversation when the name is omitted
  and have to ask when they cannot, and `continue` is also how a change is resumed in a
  brand-new session — it reads the filesystem, not the history.
- **Clear the window before implementing.** Once the planning artifacts exist they are
  files; apply reads them off disk and needs the room, and OpenSpec's own guidance is to
  clear context before implementation. The order is `/clear`, then `/model` (model up/down,
  its effort left/right) or `/effort`, then `/opsx:apply <change>` — clearing **first**,
  because a switch made inside a full window still drags that window along, and with the
  name, because clearing is exactly what removes what `apply` would have inferred it from.
  Nothing is lost: status is filesystem existence.
- **Whether to clear *between planning artifacts* is per chain, not general.** Re-picking
  model and effort at an artifact boundary is always free. Clearing there is not:
  `mattpocock-bridge` wants `grill` through `tasks` in one unbroken window and says to
  compact at the nearest boundary instead, while `feature`'s own session discipline is to
  compact at artifact boundaries. Follow the chain, and default to not clearing when the
  chain is silent.
- **Delta spec format.** Scenarios need exactly four hashes (`#### Scenario:`) — three, or
  a bullet, does not parse. A `MODIFIED` requirement replaces the whole block, so it must
  carry every surviving scenario.
- **Post-apply artifacts are gated by checkboxes, not files.** `spike`'s `findings` and
  `hotfix`'s `postmortem` are written after the work, and the archive warning counts
  *tracked checkboxes*. Ticking the last box before writing the artifact is how one
  quietly never happens.
- **Escape hatches live in the change's `.openspec.yaml`.** The CLI reads `skip_specs` and
  `retire_capabilities`; it does not read `skip_grill` or `skip_surface`, so those need a
  one-line stub file to unblock the graph.
- **Archiving non-interactively** needs the change name and `--yes`, or it exits 1.
- **A subagent inherits nothing** — no conversation, no files read, no skills invoked, and
  no `AskUserQuestion`. Its prompt names every input, and a gate that needs a human answer
  drafts and returns the question for the caller to ask.

Sources: the twelve `schema.yaml` files under
`payload/levels/*/openspec/schemas/*/`, `payload/levels/advanced/openspec/ROUTING.md`, the
eight agent files under `payload/levels/*/agents/`, and
`skills/configuring-openspec/references/`.
