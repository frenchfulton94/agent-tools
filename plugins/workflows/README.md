# workflows

Sets up or reconciles a project's OpenSpec workflow in one command.

## Install

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install workflows@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
setup travels with the repo instead of living on one workstation. `meta-skills` installs
automatically as a declared dependency.

## Use

    /workflows:setup [minimal|standard|advanced] [--check] [--dry-run]

Setup asks one question — which complexity level, and it arrives with a recommendation read
off your own commit history — detects everything else, shows you a plan, and writes nothing
until you approve it. Re-running is safe and is how you take
updates: it records what it installed in `.claude/workflows.json`, so a later run can
refresh its own files while leaving anything you have edited exactly as you left it.
`--check` reports drift read-only and changes nothing.

Once a repo is set up, `choosing-a-workflow` routes a piece of work to the right schema —
it names the schema, the filled-in `/opsx:new` command that creates the change with that
schema, the artifact chain, and the guardrail most likely to force a reclassification, then
stops. `configuring-openspec` covers the configuration surfaces themselves.

## Levels

| Level | Schemas | Longest chain | Router |
|---|---|---|---|
| `minimal` | 2 | 6 artifacts | no |
| `standard` | 2 | 7 artifacts | no |
| `advanced` | 8 | 10 artifacts | yes |

## What setup does

1. Detects repo state, already-decided settings, runtimes, and the machine's OpenSpec profile.
2. Reads the repo's recent commit subjects, sorts them into kinds, and asks one question:
   which level — with a recommendation and the evidence for it. It recommends; you decide.
3. Shows a plan and waits. Nothing is written before you approve it.
4. Applies, in order: `openspec init` (only if absent) → schemas → agents → TOOLS.md →
   `config.yaml` → CLAUDE.md → plugins → verification → records what it
   installed in `.claude/workflows.json`.
5. Reports what happened, what was skipped and why, and which human steps remain.

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
| `/impeccable init` | Interactive design-context gathering |
| `/reload-plugins` | Activates plugins a shell command installed in the running session |
| Select `controlled-english` under `/config` | Choosing an output style is a preference nothing can set for you. **After the reload** — the style ships with the `meta-skills` plugin, so it is not in the list until that plugin is active |

Re-run `/workflows:setup` after the first two and it folds their output into your config.
The last two write nothing, so there is nothing to fold.

## For teammates

A committed `.claude/settings.json` does not install plugins for anyone else. After
cloning a configured repo, install this plugin and run `/workflows:setup` — reconcile
mode installs only what is missing.

## Verification and limits

- Invariants I1 (`openspec/specs/` and `openspec/changes/` are never modified, moved,
  or deleted), I2 (an existing schema is never replaced without being named first), and I6
  (a re-run refreshes setup's own untouched files and reports everything else) are proven
  against real fixtures by the opt-in end-to-end suite (`bun run test:workflows:e2e`).
- **I3 is not proven end to end.** The fixture disables a plugin that the level's manifest
  never mentions, so what that test establishes is narrower than the invariant: nothing in
  the pipeline rewrites `.claude/settings.json` wholesale. The rule that actually enforces
  I3 — a plugin id you have already decided is skipped, never installed over — is covered
  by unit tests (`tests/workflows-plan.test.ts`, `tests/workflows-settings.test.ts`).
- I4's mechanics — the `config.yaml` backup path, the artifact-id union, and unmatched-
  rule preservation as a trailing comment — are covered by `config-facts.mjs`'s unit
  tests (`tests/workflows-config-facts.test.ts`), not by the end-to-end suite.
- **The setup skill's own orchestration is unverified end to end.** `claude -p
  --plugin-dir` cannot drive it: the `meta-skills` dependency this plugin declares does
  not resolve under `--plugin-dir` loading, and the approval gate — nothing is written
  before you approve the plan — cannot complete inside one `-p` turn. The prose in
  `skills/setup/SKILL.md` has been reviewed, not executed.
- The Windows `%APPDATA%` config path is reasoned from the OpenSpec CLI's source and
  this plugin's own docs. It has never been run on Windows.

## Learn

A self-paced learning package ships in [`learn/`](learn): thirteen lessons and six
printable reference cards covering installation, routing, all twelve workflows end to
end, and which model to pair with each phase. Open [`learn/index.html`](learn/index.html)
straight from a checkout, or build and serve it:

    bun run learn:preview        # builds, then serves http://localhost:4173

`learn:preview` runs `learn:build` first, deliberately: the build is what decides the
site's contents, so previewing the workspace instead would preview a directory the deploy
never publishes. `learn:build` alone writes `learn/site/dist/` (gitignored) — it copies
`index.html`, `lessons/`, `reference/`, and `assets/`, writes `.nojekyll`, rewrites the
lessons' relative citations of this plugin's source into blob URLs, and **fails if any
link would 404 on the deployed site**.

`learn/MISSION.md` says who the package is for. `learn/RESOURCES.md` ranks every source by
trust and has an explicit gaps section — read it before trusting a claim. Neither ships to
the site; they are working files.

### Deploying it

The site is live at

    https://frenchfulton94.github.io/agent-tools/

Pages was enabled on 2026-08-28 with **Source: GitHub Actions**. The organisation is on the
Team plan, where a published site has **no access control** — anyone with the URL can read
every lesson. That was the decision behind enabling it, and it is worth keeping in mind when
writing one: the lessons quote this plugin's source and name internal conventions.

`.github/workflows/pages.yml` builds and deploys **on merge to `main`**, path-filtered to
`plugins/workflows/learn/**`, `docs/install.html`, the brand assets it copies, and the
workflow itself — so unrelated merges do not republish. Nothing to run by hand.

`workflow_dispatch` stays alongside it, for a redeploy after changing a Pages setting or for
rolling the site back by dispatching an older ref.

**Merging is publishing.** The gate is pull request review; there is no longer a window in
which a merged mistake is not yet a public one.

**Renaming a lesson breaks its published URL.** A deploy replaces the whole artifact, so the
old path 404s as soon as the workflow runs. Either accept it deliberately or ship a redirect
stub, which means adding it to `build.mjs`'s `PUBLISH` set.

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
