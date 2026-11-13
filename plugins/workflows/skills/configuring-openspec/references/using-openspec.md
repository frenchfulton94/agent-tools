# Using OpenSpec Day to Day

Contents:
- [The loop](#the-loop)
- [Profiles: which skills exist](#profiles-which-skills-exist)
- [Skill spelling by tool](#skill-spelling-by-tool)
- [Skill reference](#skill-reference)
- [The change folder](#the-change-folder)
- [Writing delta specs](#writing-delta-specs)
- [Reviewing a drafted plan](#reviewing-a-drafted-plan)
- [Sync and archive](#sync-and-archive)
- [Editing a change in flight](#editing-a-change-in-flight)
- [Adopting on an existing codebase](#adopting-on-an-existing-codebase)
- [Teams](#teams)

## The loop

```
TERMINAL   npm install -g @fission-ai/openspec@latest
TERMINAL   cd your-project && openspec init
CHAT       /openspec-explore                    (optional: think it through first)
CHAT       /openspec-new-change add dark mode          (scaffolds; shows the first template)
CHAT       /openspec-continue-change add-dark-mode     (one artifact per call; repeat)
CHAT       /clear  +  /model or /effort     (before implementing — see below)
CHAT       /openspec-apply-change add-dark-mode        (builds it, checking off tasks)
CHAT       /openspec-archive-change add-dark-mode      (merges specs, files the change away)
```

On the `core` profile, `/openspec-propose add-dark-mode` replaces the `new` + `continue` pair and drafts every planning artifact in one step.

Two terminal steps to set up; the rest lives in chat. There is no "interactive mode" to enter — typing the slash command *is* how you enter OpenSpec. The one genuinely interactive terminal feature is `openspec view`, a browsing dashboard.

Guidance from the project itself: OpenSpec works best with high-reasoning models, and benefits from a clean context window — clear context before implementation.

In Claude Code that is three commands, in this order, once the planning artifacts are all written:

1. `/clear` — the artifacts are files; apply reads them off disk and needs the window for code, test output, and shell noise. A model switch made *inside* a full window still drags that window along, so clearing comes first, not after.
2. `/model` — model with up/down, that model's effort with left/right, one dialog. `/effort` alone when only the depth is wrong.
3. `/openspec-apply-change <change>` — **with the name.** `apply` and `continue` both infer the change from the conversation when the name is omitted; clearing is exactly what removes the thing they infer from.

Run the same three between planning artifacts whenever the next one wants a different depth, ending in `/openspec-continue-change <change>`. Nothing is lost: artifact status is pure filesystem existence, so a cleared window costs a chain nothing.

## Profiles: which skills exist

| Profile | Workflows |
|---|---|
| `core` (default) | `propose`, `explore`, `apply`, `update`, `sync`, `archive` |
| expanded (custom selection) | adds `new`, `continue`, `ff`, `verify`, `bulk-archive`, `onboard` |

```bash
openspec config profile     # interactive picker; `core` is the only preset
openspec update             # apply the selection to this project
```

Each workflow is one skill under `.agents/skills/openspec-*/SKILL.md`, linked from the tool's own folder (`.claude/skills/` for Claude Code). OpenSpec 2.0 installs skills only: the `delivery` key (`both` | `skills` | `commands`) is still accepted in `config.json` but ignored, and the per-tool command files (`/opsx:*`) are gone.

## Skill spelling by tool

The intent is identical everywhere; the spelling follows how the tool invokes a skill.

| Tool | You type | Notes |
|---|---|---|
| Claude Code and most tools | `/openspec-propose` | The skill name behind a slash |
| Codex CLI | `$openspec-propose` | Codex does not recognize `/<name>` |
| Kimi Code | `/skill:openspec-propose` | |
| GSD, Rovo Dev, SourceCraft Code Assistant | say it in prose: "use the openspec-propose skill" | No slash surface for skills |

Amazon Q Developer is retired in 2.0: it cannot load skills, `openspec update` removes its OpenSpec files, and Kiro replaces it. The authoritative answer for any project is the "Getting started" line `openspec init` printed, which already uses the right form.

Skill names are not the old command ids. `/opsx:` users translate like this:

| 1.x command | 2.0 skill |
|---|---|
| `/opsx:propose` | `openspec-propose` |
| `/opsx:explore` | `openspec-explore` |
| `/opsx:apply` | `openspec-apply-change` |
| `/opsx:update` | `openspec-update-change` |
| `/opsx:sync` | `openspec-sync-specs` |
| `/opsx:archive` | `openspec-archive-change` |
| `/opsx:new` | `openspec-new-change` |
| `/opsx:continue` | `openspec-continue-change` |
| `/opsx:ff` | `openspec-ff-change` |
| `/opsx:verify` | `openspec-verify-change` |
| `/opsx:bulk-archive` | `openspec-bulk-archive-change` |
| `/opsx:onboard` | `openspec-onboard` |

## Skill reference

| Skill | What it does |
|---|---|
| `/openspec-explore` | Thinking partner. Reads the codebase, compares options, creates no artifacts and writes no code |
| `/openspec-propose [name-or-description]` | Creates the change and drafts every planning artifact the schema requires |
| `/openspec-apply-change [name]` | Works through `tasks.md`, writing code and checking items off |
| `/openspec-update-change [name]` | Revises existing planning artifacts and keeps them coherent. Planning only — never edits code, never creates missing artifacts |
| `/openspec-sync-specs [name]` | Merges delta specs into main specs without archiving |
| `/openspec-archive-change [name]` | Offers to sync, then moves the change to `changes/archive/YYYY-MM-DD-<name>/` |
| `/openspec-new-change [name-or-description]` | Expanded: scaffolds a change and shows the first artifact's template, writing no artifacts. The argument is a kebab-case name **or** a description it derives one from; mention a schema and it passes `--schema` through |
| `/openspec-continue-change [name]` | Expanded: creates the next ready artifact, one at a time. Also how you resume a change in a fresh session — it reads the filesystem, not the conversation |
| `/openspec-ff-change [name]` | Expanded: creates all planning artifacts at once |
| `/openspec-verify-change [name]` | Expanded: checks completeness, correctness, coherence against the code. Does not block archive |
| `/openspec-bulk-archive-change` | Expanded: archives several changes, resolving spec conflicts by inspecting what shipped |
| `/openspec-onboard` | Expanded: narrated end-to-end tutorial on the user's real codebase |

`/openspec-ff-change` when the scope is clear; `/openspec-continue-change` when you want to review each artifact.

## The change folder

```
openspec/changes/add-dark-mode/
├── proposal.md          why and what
├── design.md            how (optional for simple changes)
├── tasks.md             implementation checklist
├── .openspec.yaml       schema, skip_specs, retire_capabilities
└── specs/
    └── ui/spec.md       delta spec
```

Artifacts build on each other (`proposal → specs → design → tasks`) but the order is an enabler, not a gate — any artifact can be revisited at any time.

`tasks.md` must use `- [ ] X.Y Description` checkboxes under `## N.` headings; the apply phase parses that format to track progress, and tasks written any other way are not tracked.

## Writing delta specs

A delta describes what changes relative to current behavior, which is what makes OpenSpec work on existing systems.

```markdown
## Purpose

Lets users take their data out of the product in a portable format.

## ADDED Requirements

### Requirement: User can export data
The system SHALL allow users to export their data in CSV format.

#### Scenario: Successful export
- **WHEN** the user clicks "Export"
- **THEN** the system downloads a CSV file with all user data

## REMOVED Requirements

### Requirement: Legacy export
**Reason**: Replaced by the new export system
**Migration**: Use the new endpoint at /api/v2/export
```

| Section | On archive |
|---|---|
| `## ADDED Requirements` | Appended to the main spec |
| `## MODIFIED Requirements` | Replaces the existing requirement — must include the full updated block |
| `## REMOVED Requirements` | Deleted from the main spec; needs `**Reason**` and `**Migration**` |
| `## RENAMED Requirements` | Retitled in place; uses `FROM:`/`TO:` |
| `## Purpose` | Seeds a brand-new capability's spec; ignored when the spec already exists |

Format rules that fail silently when broken:

- `### Requirement: <name>` for requirements, `#### Scenario: <name>` for scenarios. Scenarios need **exactly four hashes** — three hashes or a bullet is not parsed.
- Every requirement needs at least one scenario.
- Use SHALL/MUST for normative statements; avoid should/may unless you mean the RFC 2119 sense.
- `## Purpose` on a new capability wants 50+ characters, or `--strict` flags it as too brief. Without it, the created main spec carries a `TBD … Update Purpose after archive` placeholder. Do not add `## Purpose` to a delta for an existing capability — it is ignored; edit the main spec directly.
- `MODIFIED` carries every surviving scenario, not only the edited ones. Partial content loses detail at archive time and validation now rejects it up front.

What belongs in a spec: observable behavior, inputs, outputs, error conditions, external constraints, testable scenarios. What does not: internal class or function names, library choices, step-by-step implementation. The test — if the implementation could change without changing externally visible behavior, it does not belong in the spec.

Good requirements are one observable behavior each with one SHALL. Good scenarios name the case in the title and cover the edges, not just the happy path.

## Reviewing a drafted plan

The two-minute pass, in the order that lets you quit earliest:

1. `proposal.md` — is this the right problem, and has anything crept into scope?
2. the delta specs — is "done" defined correctly, and is the case you care about most actually covered? The most valuable catch is what is *missing*, since the AI faithfully writes down what was said.
3. `tasks.md` — does every task map to a requirement?

Pushing back is cheap: edit the Markdown, or tell the assistant what is wrong. Nothing is locked.

## Sync and archive

Sync merges a change's deltas into `openspec/specs/` while leaving the change active. Archive prompts to sync if needed, so most users never run sync directly. Reach for it when a long-running change should land specs early, when a parallel change needs the updated base, or to review the merged result before archiving.

Archive then moves the folder to `openspec/changes/archive/YYYY-MM-DD-<name>/`, preserving every artifact as the audit trail. It warns about incomplete tasks but does not block.

## Editing a change in flight

Every artifact is plain Markdown; edit it by hand or ask the assistant to revise it, then continue. The assistant always works from current file contents, so editing steers the work. There is no separate "update proposal" command because none is needed — though `/openspec-update-change` exists to revise artifacts *and keep them coherent with each other*, confirming each edit.

Reconciling hand-edited code with the spec: whichever is correct wins. If the code is right, update the delta to describe what shipped; if the spec is right, keep building. Do it before archiving, because archiving makes the specs the record of truth. `/openspec-verify-change` surfaces the mismatches.

**Update vs. start fresh:** update when it is the same work refined — scope narrowing, learning-driven corrections, a better approach to the same goal. Start a new change when the intent fundamentally changed, the scope exploded into different work, or the original could be marked done on its own. Update preserves context; a new change provides clarity.

## Adopting on an existing codebase

You do not document the whole system first. Specs grow one change at a time, and deltas are what make that possible.

Practical guidance: pick a small, real change you needed anyway; use `/openspec-explore` first so the AI reads the area before proposing; create domain folders under `openspec/specs/` when a change first needs one (by feature area, by component, or by bounded context — whatever a newcomer would nod at). Resist back-filling specs for code you are not changing; they go stale because nothing forces them to track reality.

Existing PRDs and SRS documents are source material for exploration, not specs to bulk-convert. Point the assistant at the relevant section when starting a change.

For a monorepo, one `openspec/` at the root with domains mapping to packages covers most teams. Work genuinely spanning repos is what the beta stores feature addresses.

A pure refactor with no behavior change has nothing to add to specs — declare `skip_specs: true` in `.openspec.yaml` rather than inventing a requirement to satisfy validation.

## Teams

OpenSpec never touches git. Commit `openspec/` like any source.

The convention that works: one change per branch, per pull request. The PR then carries both the delta spec and the code, so a reviewer reads the proposal, then the delta, then the diff — and can disagree with the *approach* cheaply instead of relitigating it across 300 lines.

Archive after the PR merges (keeps shared `specs/` moving forward only with work that shipped), or inside the PR for small teams (simpler, noisier diff). Pick one and be consistent.

Changes are separate folders, so parallel work does not collide. Keep one change to one author. The one place conflicts surface is `specs/`, when two changes modify the same requirement — resolve it like any merge conflict, keeping the requirement that reflects reality.
