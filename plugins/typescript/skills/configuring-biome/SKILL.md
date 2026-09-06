---
name: configuring-biome
description: Sets up and configures Biome — installation, biome.json/biome.jsonc, formatter, linter, and assist options, file globs, monorepo and nested configs, editor and CI wiring, and migration from ESLint and Prettier. Use when a project needs formatting or linting set up or replaced with a single toolchain, when the user mentions Biome, biome.json, `biome check`, or `biome ci`, when a Biome config is being tuned or reviewed, and when Biome silently ignores files, ignores settings, or breaks after a version upgrade.
license: MIT
---

# Configuring Biome

Produce a working Biome setup: a valid `biome.json` matched to the installed version, wired into package scripts, the editor, and CI, and verified by an actual run. Biome v2 renamed or moved most of the fields that v1 used, so the most common failure is writing a config that parses partially and silently does nothing.

## Before starting

Establish the version first — it determines the entire config shape:

```sh
npx --no-install @biomejs/biome --version
```

If Biome isn't installed yet, you're on v2 (start at Stage 1). If the project has an existing config written for v1, run `biome migrate --write` before hand-editing anything; it rewrites the config to the installed version's shape.

This skill covers configuration and setup. For writing custom lint rules, see Biome's GritQL plugin docs instead. If the user just wants files formatted once, run `biome format --write` and skip the rest.

## Fields that changed in v2

Model training data is full of v1 configs, and biomejs.dev's own migration guide still prints v1-shaped output in its examples. Trust the configuration reference and the JSON schema over any example, including those. The renames that matter:

| v1 (silently ignored or deprecated in v2)   | v2                                                                   |
| ------------------------------------------- | -------------------------------------------------------------------- |
| `"organizeImports": { "enabled": true }`    | `"assist": { "actions": { "source": { "organizeImports": "on" } } }` |
| `files.include`, `files.ignore`             | `files.includes`, with `!` negations in the same list                |
| `overrides[].include`, `overrides[].ignore` | `overrides[].includes`                                               |
| `linter.rules.recommended: true`            | `linter.rules.preset: "recommended"`                                 |
| `biome check --apply`, `--apply-unsafe`     | `biome check --write`, `--write --unsafe`                            |

New in v2 and worth reaching for: `root`/`extends: "//"` for monorepos, `linter.domains` for framework rule bundles, and `assist` as a third tool alongside the formatter and linter.

## Stage 1: Install and pin

```sh
npm i -D -E @biomejs/biome
npx @biomejs/biome init
```

`-E` pins the exact version. Biome ships lint rules and formatter changes in minor releases, so an unpinned range means CI and local machines disagree about what "formatted" means.

Then set `$schema` in the generated config to the version you actually installed — a mismatched schema makes editor validation confidently wrong about which fields exist:

```json
{ "$schema": "https://biomejs.dev/schemas/<installed-version>/schema.json" }
```

Use `./node_modules/@biomejs/biome/configuration_schema.json` instead if the project works offline. Rename to `biome.jsonc` if you want comments; Biome resolves `biome.json`, `biome.jsonc`, `.biome.json`, `.biome.jsonc` in that order, searching the working directory and then upward.

## Stage 2: Write the config

Start from this, swapping in the version you actually installed, and delete what the project doesn't need:

```json
{
	"$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",
	"vcs": { "enabled": true, "clientKind": "git", "useIgnoreFile": true },
	"files": { "includes": ["**", "!!**/dist", "!!**/build"] },
	"formatter": { "indentStyle": "tab", "lineWidth": 80 },
	"linter": { "rules": { "preset": "recommended" } },
	"assist": { "actions": { "source": { "organizeImports": "on" } } }
}
```

Four decisions carry most of the weight:

- **VCS integration.** Without `vcs.useIgnoreFile`, Biome lints everything `.gitignore` excludes. Turn it on unless there's a reason not to. If the config lives below the repo root, also set `vcs.root` to the relative path up to it.
- **Formatter defaults.** Biome defaults to tabs at width 80; Prettier defaults to spaces at 80. Teams coming from Prettier want `"indentStyle": "space"`. Don't change defaults the user didn't ask about.
- **Ignoring output directories.** `!` excludes a path from formatting and linting but still indexes it; `!!` (force-ignore) excludes it from indexing too. Use `!!` for `dist/` and `build/`, plain `!` for generated source you still want type information from. Negated patterns must follow a `**` entry, or they match nothing.
- **Framework rules.** `linter.domains` bundles rules per ecosystem — `react`, `next`, `vue`, `solid`, `svelte`, `test`, `tailwind`, `turborepo`, plus `project` and `types` for cross-file analysis. Set `{ "domains": { "react": "recommended" } }` rather than enabling rules one at a time.

Read `references/config-reference.md` when tuning specific options, choosing between tool-level and language-level settings, writing `overrides`, or reasoning about glob precedence. Read `references/monorepo.md` if the repo has multiple packages or more than one config file.

## Stage 3: Wire it up

Add scripts, then the two surfaces that make the config actually bind:

```json
{
	"scripts": {
		"check": "biome check",
		"check:fix": "biome check --write",
		"ci": "biome ci"
	}
}
```

`biome ci` is the CI command, not `biome check` — it refuses `--write`, emits GitHub annotations, and uses `--changed` semantics where `check` uses `--staged`.

Read `references/integrations.md` for editor settings (format-on-save, fix-on-save, import sorting), the GitHub Actions and GitLab workflows, and git hook configurations for lefthook, husky, and pre-commit.

## Stage 4: Verify

Never report the setup as done without running it. If you can execute commands:

```sh
sh scripts/verify_setup.sh
```

The script locates the config, compares its `$schema` version against the installed binary, and runs `biome check` to confirm the config parses and matches files. Otherwise check by hand:

- [ ] `biome check` runs without a configuration-parse diagnostic
- [ ] It reports a nonzero number of files checked — zero means the globs match nothing
- [ ] `$schema` version equals the installed version
- [ ] No field from the v2 rename table above appears in its v1 form
- [ ] If the project had ESLint or Prettier, their configs and dependencies are removed so two formatters can't fight

## Migrating from ESLint or Prettier

`biome migrate eslint --write` and `biome migrate prettier --write` read the existing configs and port what they can. Both need Node.js to load JS-based configs, neither handles YAML, and the ESLint one disables `recommended` and enumerates rules explicitly. Read `references/migration.md` before running them — it covers the `--include-inspired` flag, the cyclic-reference failure and its workaround, and what to check afterward.

## Output contract

Report: the config file (full content), which decisions were defaults versus chosen, the commands run and their actual output, and anything that couldn't be verified. If ESLint or Prettier remain installed, say so explicitly rather than leaving it implied.
