# Biome Configuration Reference

Biome v2. Options confirmed against biomejs.dev/reference/configuration.

Contents:

- [Shape of the file](#shape-of-the-file)
- [Top-level fields](#top-level-fields)
- [files](#files)
- [vcs](#vcs)
- [formatter](#formatter)
- [linter](#linter)
- [linter domains](#linter-domains)
- [assist](#assist)
- [Language sections](#language-sections)
- [overrides](#overrides)
- [Glob syntax](#glob-syntax)
- [Well-known files](#well-known-files)

## Shape of the file

Biome is a toolchain, so the config is organized by tool: `formatter`, `linter`, `assist`. All three are enabled by default. Options that apply across languages live on the tool (`formatter.lineWidth`). Language-specific options live under `<language>.<tool>` (`javascript.formatter.quoteStyle`) and override the general value for that language.

```jsonc
{
	"formatter": { "indentStyle": "space", "lineWidth": 100 },
	"javascript": { "formatter": { "quoteStyle": "single", "lineWidth": 120 } },
	"json": { "formatter": { "enabled": false } }
}
```

Biome calls every JavaScript variant `javascript` — that includes TypeScript, JSX, and TSX. There is no `typescript` section.

## Top-level fields

| Field     | Notes                                                                                                                                                                             |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `$schema` | URL `https://biomejs.dev/schemas/<version>/schema.json`, or the local `./node_modules/@biomejs/biome/configuration_schema.json`. Must match the installed version.                |
| `extends` | Array of paths, resolved from this file's folder, applied least-relevant first. Or the string `"//"` to extend the monorepo root config. Extended files cannot themselves extend. |
| `root`    | Default `true`. Nested configs must set `"root": false` or Biome errors. Implied `false` when `extends: "//"`.                                                                    |
| `plugins` | GritQL plugin paths, or `{ "path", "includes" }` objects to scope a plugin to certain files.                                                                                      |

## files

- `files.includes` — glob list controlling every tool. Anything not matched here can't be matched by a tool-level `includes` later.
- `files.ignoreUnknown` — default `false`. When `true`, Biome stays quiet about file types it can't handle.
- `files.maxSize` — default `1048576` (1 MB). Larger files are skipped.

Two levels of exclusion:

- `!pattern` — not formatted or linted, but still **indexed** (kept in the module graph, types still inferred from it). Use for generated source you still import from.
- `!!pattern` — force-ignore, not even indexed. Use for `dist/`, `build/`, vendored folders, and nested `biome.json` or `.gitignore` files you want Biome to skip entirely.

Negated patterns must come after a `**` entry. Exceptions apply in order, so you can except an exception:

```json
{ "files": { "includes": ["**", "!**/*.test.js", "**/special.test.js", "!test"] } }
```

`node_modules/` is always ignored regardless of `files.includes`. So are the protected files `package-lock.json`, `npm-shrinkwrap.json`, `yarn.lock`, and `composer.lock` — Biome never emits diagnostics for them.

Caveat on the scanner: if any `project`-domain rule is enabled, Biome indexes imported files even when `files.includes` excludes them, including `.d.ts` and `package.json` inside `node_modules/`. Force-ignore is the only way to stop that.

## vcs

```json
{
	"vcs": {
		"enabled": true,
		"clientKind": "git",
		"useIgnoreFile": true,
		"root": "../",
		"defaultBranch": "main"
	}
}
```

`useIgnoreFile` honors `.gitignore`, git's local exclude file, and `.ignore`, including nested ones. `root` is only needed when the config sits below the repository root. `defaultBranch` is what `--changed` compares against.

## formatter

Defaults: `indentStyle: "tab"`, `indentWidth: 2` (ignored when indenting with tabs), `lineWidth: 80`, `lineEnding: "lf"`, `bracketSpacing: true`, `delimiterSpacing: false`, `expand: "auto"`, `attributePosition: "auto"`, `formatWithErrors: false`, `useEditorconfig: false`, `trailingNewline: true`.

- `expand` — `"auto"` keeps objects multi-line if the first property has a newline; `"always"`/`"never"` force it. `package.json` gets `"always"` unless configured otherwise.
- `useEditorconfig` — when on, `.editorconfig` supplies formatting options, but `biome.json` always wins. Files above the `biome.json` are ignored, and nested `.editorconfig` files aren't supported.
- `trailingNewline` — leave at `true`. Disabling it breaks other tools.

## linter

- `linter.enabled` — default `true`.
- `linter.rules.preset` — `"recommended"` (default), `"all"` (everything except nursery), `"none"`. Replaces the deprecated `linter.rules.recommended`.
- `linter.includes` — applied _after_ `files.includes`, so it can only narrow. Unlike `files.includes`, it cannot match a bare folder name — use `!/test/**`, not `!test`.

Rule groups: `a11y`, `complexity`, `correctness`, `nursery`, `performance`, `security`, `style`, `suspicious`.

A group takes either a severity string or an object of rules:

```json
{
	"linter": {
		"rules": {
			"a11y": "info",
			"suspicious": { "noConsole": "error", "noDebugger": "off" }
		}
	}
}
```

Severities: `"on"` (the rule's own default severity), `"off"`, `"info"`, `"warn"`, `"error"`. `biome explain <ruleName>` prints a rule's default severity and docs.

Nursery rules need explicit opt-in on stable releases and are exempt from semver.

## linter domains

`linter.domains` enables rule bundles per ecosystem, each accepting `"recommended"`, `"all"`, or `"none"`. Domains auto-activate when the matching dependency is declared.

| Domain        | Triggering dependency                        |
| ------------- | -------------------------------------------- |
| `react`       | `react >=16`                                 |
| `next`        | `next >=14`                                  |
| `vue`         | `vue >=3`                                    |
| `solid`       | `solid >=1`                                  |
| `svelte`      | `svelte >=3`                                 |
| `qwik`        | `@builder.io/qwik >=1`, `@qwik.dev/core >=2` |
| `reactnative` | `react-native >=0.60`                        |
| `test`        | `jest`, `mocha`, `ava`, `vitest`             |
| `playwright`  | `@playwright/test >=1`                       |
| `tailwind`    | `tailwindcss >=3`                            |
| `drizzle`     | `drizzle-orm >=0.9`                          |
| `turborepo`   | `turbo >=1`                                  |
| `project`     | — cross-file analysis                        |
| `types`       | — type inference                             |

`react` and `solid` conflict; enable one. Several domains (`drizzle`, `playwright`, `svelte`, `tailwind`, `reactnative`) currently contain only nursery rules, so `"recommended"` activates nothing there — enable individual rules instead.

`project` and `types` turn on the whole-project scanner and cost real time on large repos. `project` covers `noPrivateImports`, `noUndeclaredDependencies`, `noUnresolvedImports`, `noImportCycles`, `useImportExtensions`. `types` covers type-aware rules like `noFloatingPromises`, `useAwaitThenable`, `noUnnecessaryConditions`.

## assist

The third tool — source actions that are safe to apply on save. Only one group exists, `source`:

```json
{ "assist": { "enabled": true, "actions": { "source": { "organizeImports": "on" } } } }
```

This is where v1's top-level `organizeImports` went. `assist.includes` behaves like `linter.includes`.

## Language sections

`javascript`, `json`, `css`, `graphql`, `grit`, `html`. Each supports `<lang>.formatter`, `<lang>.linter.enabled`, `<lang>.assist.enabled`, and most a `<lang>.parser`.

**javascript.formatter** — `quoteStyle: "double"`, `jsxQuoteStyle: "double"`, `quoteProperties: "asNeeded"`, `trailingCommas: "all"`, `semicolons: "always"`, `arrowParentheses: "always"`, `bracketSameLine: false`, `operatorLinebreak: "after"`.

**javascript** other — `globals: []` for names the analyzer should accept; `jsxRuntime: "transparent"` (set `"reactClassic"` when the `React` import is required); `parser.jsxEverywhere: true` allows JSX in `.js`; `parser.unsafeParameterDecoratorsEnabled: false`; `resolver.experimentalPnpmCatalogs: false`.

**json** — `parser.allowComments`, `parser.allowTrailingCommas`, `formatter.trailingCommas: "none"`.

**css** — `parser.cssModules: false`, `parser.tailwindDirectives: false` (enable for `@theme`, `@utility`, `@apply`), `formatter.quoteStyle: "double"`. Note `css.formatter.enabled` defaults to `false`.

**html** — experimental. `html.formatter.enabled` and `graphql.formatter.enabled` and `grit.formatter.enabled` all default to `false`. `html.experimentalFullSupportEnabled` extends parsing, formatting, and linting into Vue, Svelte, and Astro files rather than extracting only their script blocks. `html.formatter.whitespaceSensitivity` defaults to `"css"`.

## overrides

An ordered list of `{ includes, ...settings }`. The **first** matching pattern wins; later ones are not merged in.

```json
{
	"overrides": [
		{ "includes": ["generated/**"], "formatter": { "lineWidth": 160 } },
		{ "includes": ["shims/**"], "linter": { "enabled": false } },
		{ "includes": [".vscode/**"], "json": { "parser": { "allowComments": true } } }
	]
}
```

Each entry accepts the tool sections (`formatter`, `linter`, `assist`) and the language sections, minus their own `includes`/`ignore`.

## Glob syntax

- `*` matches within one path segment; `**` recurses and must be a whole segment (`**a` is an error).
- `[abc]` and `[!abc]` for character classes and their negation.
- A leading `!` makes a negated pattern, only valid as an exception to a preceding regular pattern.
- Include a folder's contents with `dir/**`; exclude a folder with bare `!dir` (avoids traversing it at all, and avoids Biome picking up a `biome.json` or `.gitignore` inside).
- Globs written on the command line are expanded by the shell, not by Biome.

Paths in a config resolve relative to that config's folder — except in an extended file, where they resolve relative to the folder of the config doing the extending.

## Well-known files

Biome parses certain filenames as JSON with parser options preset, regardless of extension. Comments and trailing commas allowed: `tsconfig.json`, `jsconfig.json`, `.babelrc`, `.swcrc`, `deno.json`, `nx.json`, `project.json`, `typedoc.json`, `devcontainer.json`, and everything under `.vscode/`, `.zed/`, `.cursor/`. Comments only: `.eslintrc.json`, `.jshintrc`, `tslint.json`, `turbo.json`. Neither: `.bowerrc`, `.nycrc`, `.watchmanconfig`, and similar.
