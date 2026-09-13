# Phase 8 design — apple-studio into the agent-tools catalog

> status: approved 2026-09-12
> scope: two repositories — `~/Projects/apple-studio` and `~/Projects/agent-tools`

## Summary

The apple-studio plugin moves into the agent-tools marketplace and ships from
there alone. apple-studio's authoring tools move with it; apple-studio's
verification record stays behind in an archived repository.

The move is not a copy. One skill name collides with the catalog and gets
renamed, four manifest fields and a README have to be written before the plugin
registers cleanly, and the catalog gains its first `CLAUDE.md` and first
`.gitignore` because the Apple authoring rules have to be in scope while the
skills are edited.

Phase 8 ships `apple-studio` at `0.9.0`, tagged `apple-studio-v0.9.0`.

## Terms

| Term | Means |
|---|---|
| the catalog | the `agent-tools` repository and the marketplace it publishes |
| the plugin | the eleven skills and two hooks installed as `apple-studio` |
| the authoring repo | `~/Projects/apple-studio`, which becomes an archive |
| the record | `.superpowers/sdd/` — 391 files of task briefs, reports, and captured logs |

## Decisions

Five settled during design, each with the alternative that lost.

1. **Vendor the built plugin, do not remote-source it.** The catalog's tests and
   audit script both walk `plugins/*` on disk; a marketplace entry pointing at
   another repository would be invisible to every check the catalog has.
2. **`plugin/` leaves the authoring repo entirely.** There is no vendored copy
   to keep in sync, so no sync script and no drift.
3. **agent-tools becomes the only channel.** apple-studio's own
   `.claude-plugin/marketplace.json` is deleted. Two marketplaces publishing a
   plugin of the same name at different versions is a debugging trap, not a
   fallback.
4. **The Svelte `apple-design` is the one that gets renamed.** Its own
   description opens "translated to the web and the Svelte stack"; the literal
   name belongs to the plugin doing native Apple platform work.
5. **apple-studio's eleven skill names are kept.** The catalog already carries
   eleven noun-named skills, so the `swift-` and `apple-` prefixes widen an
   existing exception rather than breaking a rule. `CONVENTIONS.md:32` carries
   across as a documented exception.

Two findings corrected the design mid-flight and are recorded here because both
contradict what the catalog's README says:

- **The catalog records a version in one place, not two.** Every entry in
  `.claude-plugin/marketplace.json` carries `name`, `source`, `category`, and
  `description` and nothing else;
  `tests/marketplace-integrity.test.ts:125-129` asserts only that `plugin.json`
  declares a semver, and the audit's `--since` check reads `plugin.json` alone
  (`audit_marketplace.ts:343-351`). `README.md:39-40` and `README.md:59-63`
  describe machinery that does not exist. apple-studio's own rule —
  `CONVENTIONS.md:157-159`, version in `plugin.json` only — is what the catalog
  actually practices.
- **The plugin version moves to `0.9.0`.** The skills' bodies are unchanged, but
  `apple-animations` gains a routing scope clause in its description. A
  description change is a routing change, and users receive it only when the
  version moves.

## Target layout

```
agent-tools/
  .gitignore                       new — corpus/, *.epub, *.pdf, .DS_Store,
                                   pipeline/tmp/, *.trace/
  CLAUDE.md                        new — thin root memory
  plugins/apple-studio/            1.2M — 11 skills, 2 hooks, plugin.json, README.md
  authoring/apple-studio/
    CONVENTIONS.md                 the Apple authoring rules
    pipeline/                      236K — docc.py, typecheck_snippets.py,
                                   run_evals.py, maps/ (13), fixtures/
    docs/                          440K — specs/ (7), plans/ (7), deferred.md
    records/                       new home for phase briefs and logs
    corpus/                        gitignored, local only

apple-studio/                      archived
  .superpowers/                    32M — the record, kept
  README.md                        rewritten as a pointer
```

`plugins/` stays purely shippable. It is the install unit, and every test and
audit check walks `plugins/*/skills`. Putting 700K of Python and dated specs
inside it would send them to every installer. Naming the authoring tree after
the plugin rather than after the tool leaves room for a second plugin that grows
its own pipeline.

## Step 1 — rename `apple-design` to `fluid-interfaces`

One pull request against the catalog. It lands first: importing the plugin
before the rename creates a duplicate skill name, which
`tests/marketplace-integrity.test.ts:147-158` fails on.

`fluid-interfaces` states what the skill covers and keeps its provenance —
Apple's 2018 WWDC talk *Designing Fluid Interfaces*. Dropping `apple` from a
Svelte skill's name removes the confusion instead of relocating it.

A skill rename needs no `renames` entry. `renames` maps plugin names, which
users carry in `enabledPlugins` and install commands; skill names appear in no
user setting, so no install breaks.

**23 references across four plugins and the root README:**

| File | Lines |
|---|---|
| `plugins/design-engineering/skills/apple-design/` | directory rename |
| `plugins/design-engineering/skills/apple-design/SKILL.md` | 2 (frontmatter `name`) |
| `plugins/design-engineering/README.md` | 33, 47, 113 |
| `plugins/design-engineering/NOTICE.md` | 17, 32 |
| `plugins/design-engineering/skills/design-engineering/SKILL.md` | 3, 118 |
| `plugins/design-engineering/skills/design-engineering/evals/routing.md` | 71 |
| `plugins/design-engineering/skills/design-engineering/evals/cases.md` | 44 |
| `plugins/design-engineering/skills/animating-interfaces/references/recipes.md` | 424 |
| `plugins/workflows/payload/levels/advanced/agents/design-gate.md` | 63 |
| `plugins/workflows/payload/levels/advanced/openspec/README.md` | 78 |
| `plugins/workflows/payload/levels/advanced/openspec/schemas/feature/schema.yaml` | 138 |
| `plugins/workflows/payload/levels/minimal/agents/bridge-design-gate.md` | 50 |
| `plugins/workflows/payload/levels/minimal/openspec/CLAUDE.md.fragment.md` | 67 |
| `plugins/workflows/payload/levels/minimal/openspec/schemas/mattpocock-bridge/schema.yaml` | 346 |
| `plugins/workflows/payload/levels/standard/agents/craft-design-gate.md` | 49 |
| `plugins/workflows/payload/levels/standard/openspec/schemas/craft-driven/schema.yaml` | 272 |
| `plugins/workflows/payload/levels/standard/openspec/schemas/surface-driven/schema.yaml` | 48, 144 |
| `plugins/security/skills/reviewing-code-security/evals/manifest.json` | 22 |
| `README.md` | 22 |

`tests/marketplace-integrity.test.ts:138-143` pins the frontmatter `name`
against the directory name, so both move together or the suite fails.

Three version bumps follow, in `plugin.json` only: `design-engineering`,
`workflows`, `security`.

The two routing scope clauses wait for step 2. Adding them here would ship a
pointer to a skill the catalog does not yet contain.

## Step 2 — import apple-studio

One pull request against the catalog. A plain copy, not a history merge: the
commit history is being archived with the repository, so `git subtree add` would
import eight commits whose value is the record left behind deliberately.

### What lands under `plugins/apple-studio/`

The eleven skills and two hooks as they are, minus `plugin/.DS_Store` and
`plugin/skills/.DS_Store`, which are gitignored in the authoring repo and would
otherwise arrive in a catalog that has no `.gitignore`.

**`plugin.json` gains four fields and changes one.** It carries `name`,
`version`, `description`, `author`; seven of the catalog's nine manifests also
carry `$schema`, `displayName`, `keywords`, and `license`. `author` becomes
`Agent Tools` with the same address, matching every other catalog plugin;
attribution moves to the plugin README. `version` becomes `0.9.0`.

**A plugin README, which apple-studio has never had.** The audit checks three
things nothing else would catch (`audit_marketplace.ts:248-270`): the H1 matches
the plugin name, the install command names `apple-studio` and not another
plugin, and any `--plugin-dir` path points at the right leaf. Shape follows
`plugins/zed/README.md` — install, a Components table, and a "Why this is its
own plugin" section.

**One reference header repoints.**
`apple-frameworks/references/framework-catalog.md:4` reads
`regenerate: pipeline/generate_catalog.sh`, which becomes
`authoring/apple-studio/pipeline/generate_catalog.sh`.

**Five cross-skill citations must be rewritten before the import passes.**
`validate_skill.ts:175-179` resolves every `references/…` mention in a `SKILL.md`
against that skill's own directory, and the audit reports its errors as errors
(`bun run audit` exits non-zero on them). Five citations name a sibling skill in
the prose but write the path as if it were local:

| File | Line | Cites | Which lives in |
|---|---|---|---|
| `apple-animations/SKILL.md` | 9 | `references/animation-taste.md` | `apple-design` |
| `apple-animations/SKILL.md` | 10 | `references/accessibility.md` | `apple-design` |
| `apple-intelligence/SKILL.md` | 10 | `references/primers/foundation-models.md` | `apple-frameworks` |
| `apple-intelligence/SKILL.md` | 11 | `references/primers/app-intents.md` | `apple-frameworks` |
| `apple-intelligence/SKILL.md` | 50 | `references/profiling-workflow.md` | `apple-performance` |

The `${CLAUDE_PLUGIN_ROOT}/` escape hatch at `audit_marketplace.ts:470-487` does
not help: it suppresses the error only when the path resolves from the plugin
root, and these resolve from neither. The fix is to drop the `references/`
prefix and name the file plainly — "apple-design's `animation-taste` reference".
Bodies change, descriptions do not, so this adds no routing risk.

**The hooks ship unchanged.** apple-studio is the catalog's first `Stop` hook
and its second `PostToolUse`. `stop_gate.sh` blocks session end on a failed
`xcodebuild` after Swift edits and fails open at every other branch — no `jq`,
no Xcode project within three parent directories, no scheme, an unavailable
destination. The posture is right; it gets validated before it lands.

### What lands under `authoring/apple-studio/`

`pipeline/` and `docs/` move as they are. `CONVENTIONS.md` moves with five path
references repointed: lines 32, 43, 135, 144, and 158, each `plugin/…` becoming
`plugins/apple-studio/…`. Everything else in it carries over as written — the
stack baseline, the live-docs-first rule, the scope boundary, the four
verification moves ranked by strength, the distillation map rule, and the
kill-switch.

`records/` is created empty for Phase 8's own briefs and logs.

### What lands at the catalog root

**`.gitignore`, the catalog's first.** Carried from the authoring repo:
`corpus/`, `*.epub`, `*.pdf`, `.DS_Store`, `pipeline/tmp/`, `*.trace/`. The
first line matters most — `corpus/` is 5.9M of converted book text that must
never be committed.

**`CLAUDE.md`, the catalog's first.** The Apple authoring rules have to be in
scope while `plugins/apple-studio/skills/` is edited, and a nested `CLAUDE.md`
under `authoring/` would not load in that subtree. Root memory always loads, so
the root is the only place that works.

Four things, kept thin: the `plugins/` versus `authoring/` split, the verify
commands that already exist (`bun test`, `bun run audit`,
`claude plugin validate .`), the version rule, and a pointer to
`authoring/apple-studio/CONVENTIONS.md` for Apple work. A project-memory pass
for the whole catalog is separate work and is not in this phase.

**`marketplace.json`** gains an entry under category `development`, with
`name`, `source: ./plugins/apple-studio`, `category`, and `description` — the
shape every other entry uses.

**`README.md`** gains a row listing all eleven skill names. The audit errors on
a shipped skill missing from that column (`audit_marketplace.ts:293-306`). The
two stale version paragraphs at `README.md:39-40` and `README.md:59-63` are
corrected in the same pass.

**The security eval manifest** gains eleven `acknowledgedOmissions` entries.
`tests/security-evals.test.ts:88-92` asserts every catalog skill appears there
or among the decoys.

### Routing

After the rename, three skills claim Apple motion territory, and the
discriminator is platform rather than topic:

| Skill | Owns |
|---|---|
| `fluid-interfaces` (design-engineering) | Apple's principles on the web and Svelte |
| `apple-animations` (apple-studio) | SwiftUI animation implementation |
| `apple-design` (apple-studio) | HIG conformance and animation taste, native |

`apple-animations` already closes its description by naming `apple-design` and
`xcode-loop`; it gains one clause for `fluid-interfaces`. `fluid-interfaces`
gains the mirror clause. `apple-design` needs no change — "Apple Human Interface
Guidelines conformance for iOS/iPadOS/macOS apps" already fences it to native.

One cosmetic collision survives and is left deliberately:
`apple-animations/references/fluid-interfaces.md` shares a name with the renamed
skill. Same source talk, two platforms.

## Step 3 — archive the authoring repo

Delete `plugin/`, `pipeline/`, `docs/`, `CONVENTIONS.md`, `CLAUDE.md`, and
`.claude-plugin/marketplace.json`. Keep `.superpowers/`. Rewrite `README.md` as
a pointer to the new home, stating that the repository holds the verification
record for Phases 0 through 7 and that the plugin ships from agent-tools.

Existing tags preserve the deleted tree, so nothing becomes unreachable. Every
`verified:` header and spec verification table citing a log under
`.superpowers/` keeps resolving.

Then archive on GitHub, run `claude plugin marketplace remove apple-studio`, and
install from the catalog.

## Phase ritual after the move

Three adjustments, because the catalog holds eleven plugins on independent
versions where the authoring repo held one.

- **Tags are namespaced.** `apple-studio-v0.9.0`, not `v0.9.0`. A bare version
  tag would claim the whole repository for one plugin. The authoring repo's
  rule that the tag runs one ahead of the phase number holds.
- **Phase records go to `authoring/apple-studio/records/<date>-phaseN-<slug>/`**,
  with `*.trace/` gitignored as today. This keeps a tool's directory name out of
  the catalog root and puts the record beside the pipeline that produces it.
- **Commit titles stay `Phase N Task M: <summary>`** for per-task commits, with
  the pull request title written in the catalog's descriptive voice. Mixed
  commit history across a repository with eleven plugins is normal.

Everything else survives: `phase-N` branches off `main`, a design spec approved
before planning, one implementation plan per phase with its Global Constraints
block, and `docs/deferred.md` read before proposing work that looks
already-decided.

## Verification

Every claim in the phase report cites a captured log.

| Check | Catches |
|---|---|
| `bun test` | registration in both directions, `name` against directory, skill-name uniqueness, the README skills column, the security eval roster |
| `bun run audit` | the four vendored validators over every skill, plugin, agent, and hook; plugin READMEs; the marketplace schema |
| `claude plugin validate .` | the authoritative marketplace check |
| `claude plugin validate plugins/apple-studio --strict` | the manifest in isolation |
| `claude --plugin-dir plugins/apple-studio` | that all eleven skills load |
| the authoring-hooks validation script | `hooks.json` and both hook scripts |
| the `apple-animations` trigger evals | the SwiftUI side of the description change |
| design-engineering's `evals/routing.md` and `evals/cases.md` | the Svelte side, where `fluid-interfaces` must now win the cases `apple-design` won |

The last two rows are the ones that must not be skipped. Every other step moves
bytes; those two description edits change which skill fires. They use different
harnesses: `apple-animations` runs through
`authoring/apple-studio/pipeline/run_evals.py`, which guards
`~/Projects/StudioFixture` against writes and leaves its tree clean, while
`fluid-interfaces` is checked against design-engineering's own routing cases.

`bun run audit:strict` is informational, not a gate. It already exits 1 on the
catalog as it stands — 0 errors, 12 warnings — so it cannot
be a pass condition. Run it to record the warning delta instead. Expect roughly
+70 from apple-studio: 16 reference files not linked from their `SKILL.md` and
16 nested a level too deep, all of them `apple-frameworks`' primers, plus around
38 reference files over 100 lines with no table of contents in the first 30.
None are errors. Logged as a deferred item, not fixed in this phase.

Baseline before any change, measured 2026-09-12 on `main` at `cb24f86`:
`bun test` 74 pass, 0 fail; `bun run audit` exit 0; `bun run audit:strict`
0 errors, 12 warnings. The catalog has 9 plugins on this base — the branch
`add-dokploy-plugin` carries an unmerged tenth, outside this phase.

Step 1 is verified green before step 2 starts.

## Non-goals

- **`skills-lock.json` and `.agents/skills/`** mirror only the 14 skills the
  catalog uses on itself. apple-studio's eleven do not belong there.
- **A project-memory pass for the catalog.** The root `CLAUDE.md` written here
  is the minimum that makes the move correct, not a considered memory file for
  eleven plugins.
- **Renaming apple-studio's skills to the catalog's gerund convention.**
  Decided against; see decision 5.
- **Importing apple-studio's commit history.** Decided against; see step 2.
- **The 70 validator warnings apple-studio brings.** Missing tables of contents,
  and `apple-frameworks`' 16 primers sitting a level deeper than the validator
  expects. All advisory, none blocking, and each one a judgement an author may
  have made deliberately. Deferred with an explicit trigger: revisit if
  `audit:strict` is ever made a gate.
- **Cleaning up `~/Projects/StudioFixture` references in
  `xcode-loop/references/headless-commands.md`.** They are provenance citations
  in a verified-against header, shipped as they stand today. Noted for a later
  phase rather than fixed here.

## Risks

- **The `workflows` payload edits are the widest blast radius in step 1.** Ten
  lines across nine files, in schemas and gate agents that other projects
  install. A missed one leaves an OpenSpec schema pointing at a skill name that
  no longer exists, and nothing in the catalog's tests reads schema YAML.
  Mitigation: grep for `apple-design` across the whole catalog after the rename
  and confirm zero hits remain anywhere.
- **The catalog gains a blocking `Stop` hook that its other nine plugins do not
  have.** Anyone installing `apple-studio` for the skills also gets the build
  gate. This is the documented behavior and it fails open everywhere it can, but
  the plugin README states it plainly so the install decision is informed.
- **`authoring/` is a new top-level concept with one occupant.** If no second
  plugin ever grows a pipeline, the directory is one level of nesting that earns
  nothing. The kill-switch rule applies: if Phase 9 has not justified it, flatten
  it.
