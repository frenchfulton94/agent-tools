---
name: maintaining-plugin-marketplaces
description: Audits, curates, and evolves a Claude Code plugin marketplace as a catalog — marketplace.json, the plugins and skills it registers, the version discipline that makes updates reach users, and the READMEs describing what ships. Use when the user wants to add, move, rename, retire, or release a plugin or skill in a marketplace repository, check whether the catalog has drifted, decide which plugin a new skill belongs in, or find overlapping, stale, or undiscoverable entries. Also use when the working directory is a marketplace repository and the user asks to improve or clean up the plugins, or reports that an install, an update, or the `/plugin` listing does not show what the repository actually ships. For writing one SKILL.md, prefer `authoring-skills`; for one plugin's manifest and layout, prefer `authoring-plugins`.
license: MIT
---

# Maintaining Plugin Marketplaces

A marketplace is a catalog, and catalogs fail quietly. A plugin directory nobody registered is invisible to `/plugin marketplace add` — no error, it simply never appears. A version left unbumped ships nothing while every file on disk looks correct. Neither symptom reaches the maintainer; both reach the user. The unit of maintenance here is the catalog, not any single plugin.

## Route the request

| The request is about... | Use... |
|---|---|
| Writing, fixing, or evaluating one `SKILL.md` | `authoring-skills` |
| One plugin's manifest, layout, or a component that will not load | `authoring-plugins` |
| The contents of `hooks/hooks.json` or `agents/*.md` | `authoring-hooks`, `authoring-subagents` |
| Where a new skill belongs, or whether it belongs at all | Continue below |
| Drift, releases, renames, retirements, catalog cleanup | Continue below |

The split is scope, not difficulty. Those skills each own one artifact; this one owns the relationships between them.

## What the tests already guarantee

In a marketplace with a test suite, read the suite before auditing anything by hand. This repository's `tests/marketplace-integrity.test.ts` pins registration in both directions, `name` matching directory, a semver version in each `plugin.json`, `SKILL.md` presence and frontmatter match, skill-name uniqueness, README rows and their links, and the same description in `plugin.json` and the marketplace entry. `tests/marketplace-audit.test.ts` runs the sweep below and gates on its catalog findings, leaving the delegated validator findings advisory.

So an audit does not re-derive those — it runs `bun test` and reads the failures. Restating a suite's invariants as a manual checklist produces a second, weaker copy that disagrees with the first the next time either changes. Check what the suite cannot see, and treat a warning the gate deliberately lets through as a judgement someone made, not as something nobody noticed.

## Health check

Report findings before editing anything.

```bash
bun scripts/audit_marketplace.ts . --strict     # the sweep: validators plus what no test covers
bun test                                        # the pinned contract
claude plugin validate .                        # authoritative, when the CLI is installed
```

The sweep's own job is small and specific: run the vendored `validate_*.ts` validators over every skill, plugin, agent, and hook file (nothing else does), then check plugin-level READMEs, the README's skills column, the marketplace-level schema, and — with `--since <ref>` — plugin directories that changed without a version bump.

Read `references/health.md` when a finding needs interpreting, or when code execution is unavailable and the checks have to be applied by hand.

## Making a change

Three facts cause most broken releases, and none of them are visible in a diff.

**A version has to move in every place that records it.** `plugin.json`, the marketplace entry, and any README cell quoting it. An unbumped plugin ships nothing: `/plugin update` reports "already at the latest version" and users keep the old copy indefinitely. Behavior changed means the version moves.

**`name` is an install-breaking identifier.** Users carry it in `enabledPlugins`, `pluginConfigs`, and every `/plugin install` line. To change only the label, set `displayName` and leave `name` alone.

**`renames` is append-only history.** When a `name` does have to change, map the old one to the new one, and map a removed plugin to `null`. Existing entries stay put even after everyone has migrated — Claude Code follows chains, so a later rename adds a second entry rather than editing the first.

Read `references/changes.md` for the ordered procedure behind each of these: adding a skill or a plugin, moving a skill between plugins, renaming, retiring, and cutting a release.

## Deciding what belongs

Curation is the half no validator reaches, and the default answer to "should this go in the marketplace" is more often *into an existing plugin* than *into a new one*.

- **Placement.** A skill belongs with the plugins a user installs for the same reason. Someone installing for brand work does not want TypeScript refactoring arriving with it. When no existing plugin shares that reason, that is the case for a new one — not the fact that the skill is new.
- **Overlap.** Two skills whose descriptions would both plausibly fire on the same request is a routing defect, and the fix is usually a scope clause in one description rather than a merge.
- **Belonging.** A one-line convention is a memory file, an always-enforced rule is a hook, and verbose isolated work is a subagent. `authoring-skills` routes these; the catalog-level version of the question is whether the marketplace is the right distribution channel at all, or whether this is project-local and should stay in `.claude/`.

Read `references/curation.md` when weighing a placement or overlap call, or when a plugin has grown enough that splitting it is on the table.

## Auditing a marketplace

Work through in order and report findings before editing. The order matters: the suite and the sweep answer most questions mechanically, so running them first keeps the judgment calls from being made about problems that are already named.

- [ ] `bun test` passes, or every failure is understood and reported
- [ ] The sweep runs clean, including the delegated validators over every skill, plugin, agent, and hook
- [ ] Every plugin's README names that plugin — its title, its install command, its `--plugin-dir` path
- [ ] The README's skills column lists what each plugin actually ships
- [ ] Versions moved wherever behavior did, in all three places that record them
- [ ] `renames` covers every plugin name this marketplace has retired or changed
- [ ] Each plugin's entry still describes what it now contains, and its `category` still fits
- [ ] No two skills would fire on the same request; near-misses route somewhere sensible
- [ ] Deletion pass, last: what does the catalog carry that nobody installs, and what does its documentation still promise that nobody ships?

## Verify

Before reporting done: the sweep and the suite both run, every finding names a file, and any fix has been re-checked rather than assumed. A release additionally means the version moved everywhere and the change is reachable — for a local marketplace, `/plugin marketplace update` followed by the plugin appearing at its new version. Claim only what was observed.

## Output contract

- **Auditing:** findings keyed to the checklist above, each naming the file and the consequence, then proposed diffs with a one-line why. If the catalog is sound, say so and stop — do not invent findings.
- **Changing:** the diff, plus confirmation that every place recording the same fact moved together, plus what a user with the old version installed will experience.

## Related skills

- `authoring-skills` — for the `SKILL.md` files this catalog distributes. This skill is self-contained without it.
- `authoring-plugins` — for one plugin's manifest, layout, and the `marketplace.json` schema in detail. Self-contained without it.
- `authoring-hooks`, `authoring-subagents` — for the other components a plugin ships. Self-contained without them.
