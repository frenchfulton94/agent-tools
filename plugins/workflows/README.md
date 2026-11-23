# workflows

Sets up one OpenSpec workflow in a project, in one command: seven change-type schemas with
a router between them, and the three plugins their steps call.

## Install

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install workflows@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
setup travels with the repo instead of living on one workstation.

## Use

    /workflows:setup [--check] [--dry-run]

Setup asks no questions about what to install: there is one workflow. It detects the
repository's state, shows you a plan, and writes nothing until you approve it. Re-running
is safe and is how you take updates: it records what it installed in
`.claude/workflows.json`, so a later run can refresh its own files while leaving anything
you have edited exactly as you left it. `--check` reports drift read-only and changes
nothing.

Once a repo is set up, `choosing-a-workflow` routes a piece of work to the right schema,
or to impeccable when the work is only about how a surface looks or reads — it names the
schema, the filled-in `/openspec-new-change` command that creates the change with that
schema, the artifact chain, and the guardrail most likely to force a reclassification, then
stops. `configuring-openspec` covers the configuration surfaces themselves.

## OpenSpec version

Written against OpenSpec 2.x (checked on 2.1.0). 2.0 replaced the `/opsx:*` command files with skills:
the guidance names `/openspec-new-change`, `/openspec-continue-change`, and
`/openspec-apply-change`, not `/opsx:new` and the rest. A project that still carries 1.x
files needs `openspec update` (preview it with `--dry-run`) to get those skills. That
command also migrates the machine-global `config.json` the first time it runs, which is
the one machine-wide change a project command can make; setup itself never runs it.
The routed flows use `new` and `continue`, which sit outside the `core` profile — setup
warns when the machine profile lacks them.

## What it installs

| Piece | What |
|---|---|
| Schemas | `feature-flow`, `bugfix-flow`, `refactor-flow`, `spike-flow`, `upgrade-flow`, `setup-flow`, `rapid-flow` |
| Router | `openspec/ROUTING.md`, and one line in `CLAUDE.md` pointing at it |
| Agent | `flow-design`, which drafts `design.md` on the top model |
| Config | `openspec/config.yaml`, rewritten from the shipped example with your project-specific text carried forward |
| Plugins | `mattpocock-skills`, `agent-skills`, and `impeccable` — the three the flows call, and nothing else |

Each job goes to the source that does it best:

- **OpenSpec** owns which documents a change has, validates them, and merges behaviour into
  `openspec/specs/` at archive.
- **Matt Pocock's skills** drive every step: the interview, the glossary and ADRs, module
  design, slicing, TDD, diagnosis, the standards-and-spec review, and the PR body.
- **Six of Addy Osmani's agent-skills** do what Pocock's set has no skill for: a threat
  model, a fresh-context challenge to the design, one defect-hunting review per change,
  keep-or-revert performance work, code written from current documentation, and a written
  quality bar.
- **Impeccable** does all surface work. A flow builds up to a presentation seam and calls
  impeccable for everything a person sees or touches.

`payload/openspec/README.md` and `ROUTING.md` say which skill runs at which step.

## Coming from 0.9.x

0.10.0 removed the `standard` and `advanced` levels, the general-purpose and
stack-specific plugin layers setup used to install (including the Apple-native layer),
the `TOOLS.md` step, and the dependency on `meta-skills`. On a repository set up at a
removed level, a re-run:

- installs the seven flows beside what is there and makes `feature-flow` the default
  schema for new changes — open changes keep the schema they were created with;
- lists that level's schemas and agents for retirement, and deletes only the ones you
  approve, one by one; a file you edited, or one an open change still uses, is never
  offered;
- leaves every plugin that level enabled exactly as it is.

## What setup does

1. Detects repo state, already-decided settings, and the machine's OpenSpec profile.
2. Shows a plan and waits. Nothing is written before you approve it.
3. Applies, in order: `openspec init` (only if absent) → schemas → agents → retired names,
   each approved → `config.yaml` → router and the `CLAUDE.md` line → plugins → records what
   it installed in `.claude/workflows.json` → verification.
4. Reports what happened, what was skipped and why, and which human steps remain.

## What it will not do

- **Overwrite a value already in `.claude/settings.json`.** A plugin you disabled on
  purpose is left exactly as you set it — setup only fills in keys you have not decided
  yet.
- **Touch `openspec/specs/` or `openspec/changes/`.** Those are your work product;
  setup manages the schema and configuration layer around them, never their contents.
- **Replace one of your schemas or subagents without naming it in the plan first.** A
  same-name collision is shown before you approve, never applied silently. That includes a
  file setup itself installed and you have since edited: the plan records the content it
  wrote, so your change makes the file yours, and a re-run reports it instead of reverting
  it. Only a file still byte-identical to what setup wrote is refreshed automatically.
- **Run `openspec init` over an existing `openspec/` directory.** Only a repo with no
  `openspec/` at all gets initialized.
- **Install OpenSpec's skills machine-wide.** On a repository with no `openspec/`, setup
  runs `openspec init --scope project`, so the skills land in the repository. OpenSpec's
  own default would put them in your home directory for every project.
- **Write `openspec config profile`.** That value is machine-global — shared by every
  project you run OpenSpec in on this machine, not scoped to this repo — so setup
  reports its current value and leaves the decision to you.
- **Transmit anything.** Every `openspec` invocation this plugin makes sets
  `OPENSPEC_TELEMETRY=0` and `DO_NOT_TRACK=1` — the scripts on every spawn they make, and
  the setup procedure on every command it tells the agent to run. Both halves are pinned by
  tests, because it only takes one call site to make this claim false.

## Human steps setup cannot do

| Step | Why |
|---|---|
| `/mattpocock-skills:setup-matt-pocock-skills` | An interview whose value is your answers; marked human-only upstream |
| `/impeccable init` | An interview that writes `PRODUCT.md`; only for a project with a user interface |
| `/reload-plugins` | Activates plugins a shell command installed in the running session |

Re-run `/workflows:setup` after the first and it folds the tracker doc into your config.

## For teammates

A committed `.claude/settings.json` does not install plugins for anyone else. After
cloning a configured repo, install this plugin and run `/workflows:setup` — reconcile
mode installs only what is missing.

## Verification and limits

- Invariants I1 (`openspec/specs/` and `openspec/changes/` are never modified, moved,
  or deleted), I2 (an existing schema is never replaced without being named first), and I6
  (a re-run refreshes setup's own untouched files and reports everything else) are proven
  against real fixtures by the opt-in end-to-end suite (`bun run test:workflows:e2e`).
- **I3 is not proven end to end.** The fixture disables a plugin that the manifest
  never mentions, so what that test establishes is narrower than the invariant: nothing in
  the pipeline rewrites `.claude/settings.json` wholesale. The rule that actually enforces
  I3 — a plugin id you have already decided is skipped, never installed over — is covered
  by unit tests (`tests/workflows-plan.test.ts`, `tests/workflows-settings.test.ts`).
- I4's mechanics — the `config.yaml` backup path, the artifact-id union, and unmatched-
  rule preservation as a trailing comment — are covered by `config-facts.mjs`'s unit
  tests (`tests/workflows-config-facts.test.ts`), not by the end-to-end suite.
- **The setup skill's own orchestration is unverified end to end.** `claude -p
  --plugin-dir` cannot drive it: the approval gate — nothing is written before you approve
  the plan — cannot complete inside one `-p` turn. The prose in `skills/setup/SKILL.md`
  has been reviewed, not executed, and 0.10.0 rewrote it.
- The Windows `%APPDATA%` config path is reasoned from the OpenSpec CLI's source and
  this plugin's own docs. It has never been run on Windows.

## Development

    bun test                      # unit suite
    bun run audit                 # marketplace/skill-shape audit
    claude plugin validate plugins/workflows --strict
    bun run test:workflows:e2e    # end-to-end against real fixtures (slow, shells out)

The first three run in CI — the validate step there loops over every plugin the
marketplace ships, this one included, and `tests/ci-workflows.test.ts` pins that it covers
all of them. The end-to-end suite does not run in CI: it reaches the network (`npx --yes
@fission-ai/openspec@1.11.0`) and shells out to `claude`, so it stays opt-in and is run by
hand before a release.
