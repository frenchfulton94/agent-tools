# Catalog health reference

Contents:
- [What the sweep reports](#what-the-sweep-reports)
- [Finding classes](#finding-classes)
- [Delegated validator findings](#delegated-validator-findings)
- [Manual checklist](#manual-checklist)

## What the sweep reports

```bash
bun scripts/audit_marketplace.ts [marketplace-root] [--strict] [--json] [--since <ref>] [--no-delegate]
```

Exit `0` clean, `1` errors — or warnings under `--strict` — and `2` for a usage error. The root
defaults to the working directory and is discovered from `marketplace.json`'s relative sources, so
the sweep is correct for any marketplace whose entries use `./` paths. In this repository
`bun run audit` is the same command against the repository root.

`--json` emits every finding with a `severity` and a `source` — `catalog` for the sweep's own
checks, or the validator's filename for a delegated one. That split is what lets a gate block on
catalog drift, which is always fixable in one edit, while leaving standing style advisories about
existing content out of the build. `tests/marketplace-audit.test.ts` is that gate here.

Two things it deliberately does not do. It does not re-check what a test suite already pins, because
two implementations of one invariant eventually disagree and the disagreement reads as noise. And it
does not require a plugin to have a README — plugins here ship them inconsistently, and turning that
into a finding would be inventing a rule rather than maintaining one.

`--no-delegate` skips the validator sweep, which is most of the runtime. Useful when iterating on the
catalog checks alone.

## Finding classes

**Stale plugin README** *(warning)*. A plugin's own README names a different plugin — in its title,
its `/plugin install <name>@<marketplace>` line, or a `--plugin-dir` path. This is what a rename
leaves behind. Nothing loads these files, so they are wrong for as long as nobody happens to read
them, and the person who does read one is a user about to run a command that fails.

**Skills column disagrees with the tree** *(warning)*. The marketplace README lists skills per plugin
by hand. A test can pin the description cell and still parse past this one, so a skill added without
a README entry ships invisible to anyone browsing the repository. Fix by editing the cell, not by
relaxing the check.

**Unbumped plugin** *(warning, `--since <ref>` only)*. A plugin directory has commits since `<ref>`
and its version did not move. Users receive nothing: `/plugin update` reports "already at the latest
version" and keeps serving the cached copy. Bump the version in `plugin.json`, the marketplace entry,
and any README cell quoting it. Pick `<ref>` to match the question — the last release tag when
preparing one, `origin/main` when reviewing a branch.

**Marketplace schema fault** *(error)*. The marketplace `name` is not kebab-case, or collides with a
reserved first-party name; a `renames` entry points at a plugin that is neither listed nor `null`, or
forms a cycle; a plugin `source` contains `../`. `claude plugin validate .` is authoritative for these
and should be preferred when the CLI is installed — the sweep covers them for environments without
it. A reserved-name collision is re-checked on every load, not only when a marketplace is added, so a
marketplace that worked yesterday can stop loading with no local change.

## Delegated validator findings

The sweep runs the vendored validators and reports their output unchanged:

| Validator | Target |
|---|---|
| `validate_skill.ts --strict` | every `skills/<name>/` in every plugin |
| `validate_plugin.ts --strict` | every plugin directory |
| `validate_agent.ts --strict --plugin` | every `agents/*.md` |
| `validate_hooks.ts --strict` | every `hooks/hooks.json` |

`--plugin` on the agent check is not optional detail: plugin-shipped agents silently drop `hooks`,
`mcpServers`, and `permissionMode`, and only that flag reports fields that will be ignored at load.

These findings belong to the component, so route them to the skill that owns it —
`authoring-skills` for a `SKILL.md` warning, `authoring-plugins` for a manifest or layout one. The
sweep's contribution is that they run at all, over the whole corpus, rather than once during the work
that introduced each component.

When the validators are absent — a marketplace that does not vendor them — the sweep prints a note
and continues. Their absence is not a finding about the catalog.

## Manual checklist

Where code execution is unavailable, apply in this order. It covers the sweep's own checks; the
delegated validators have manual equivalents in their own skills.

- [ ] Every directory under the plugin root appears in `marketplace.json`'s `plugins` array
- [ ] Every entry's `source` starts with `./`, contains no `../`, and resolves to a real directory
- [ ] Every entry's `name` matches the `name` in that plugin's `plugin.json`, and both are kebab-case
- [ ] Every entry's `version` matches its `plugin.json` version
- [ ] The same description text appears in `plugin.json`, the marketplace entry, and the README row
- [ ] Every plugin's README names that plugin in its title and in every command it prints
- [ ] The README's skills column matches the skill directories each plugin actually contains
- [ ] Every `skills/<name>/SKILL.md` exists and its frontmatter `name` matches the directory
- [ ] No skill name appears in two plugins
- [ ] `renames` maps each retired or changed name to a listed plugin or to `null`, with no cycles
- [ ] The marketplace `name` is kebab-case and is not a reserved first-party name
