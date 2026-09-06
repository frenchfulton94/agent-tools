# Monorepos and Multiple Configs

## How Biome finds a config

From the working directory, then upward through parent folders, then the OS config directory (`$XDG_CONFIG_HOME`/`~/.config/biome`, `~/Library/Application Support/biome`, `%APPDATA%\biome\config`). First hit wins; no config means Biome's defaults.

For the CLI the working directory is wherever the command ran. For the language server it's the project root.

## Monorepo setup

Supported natively since v2. Three steps.

**1. Root config** — a normal `biome.json` at the repository root. This is the base every package inherits.

```json
{
	"$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",
	"vcs": { "enabled": true, "clientKind": "git", "useIgnoreFile": true },
	"linter": { "rules": { "preset": "recommended" } },
	"formatter": { "indentStyle": "space", "lineWidth": 100 }
}
```

**2. Nested configs that inherit** — `extends: "//"` points at the root config regardless of nesting depth. It implies `"root": false`, so you can omit that.

```json
{
	"extends": "//",
	"linter": { "rules": { "suspicious": { "noConsole": "off" } } }
}
```

**3. Nested configs that don't inherit** — a package with genuinely different standards omits `extends` and declares `"root": false` explicitly.

```json
{
	"root": false,
	"formatter": { "lineWidth": 100 }
}
```

Every nested config must be non-root, either explicitly or via `extends: "//"`. A nested config left as root throws an error. Once set up, `biome check` works from the repo root or from any single package.

**Vendored projects.** A `biome.json` inside a git submodule or vendored dependency won't have `"root": false` and will break the run. Force-ignore the folder from the root config: `"files": { "includes": ["**", "!!vendor"] }`.

## Sharing config without nesting

`extends` also takes an array of paths, applied in order with later entries overriding earlier ones:

```json
{ "extends": ["./common.json"] }
```

The path-resolution rule is the one people get wrong: paths inside an extended file resolve relative to the folder of the config that is **extending**, not the folder the extended file lives in. So a `common.json` at the repo root containing `"includes": ["src/**/*.js"]`, extended by both `frontend/biome.json` and `backend/biome.json`, matches `frontend/src` in one and `backend/src` in the other.

Note that in that arrangement both configs are still roots, so `biome` can't run from the repo root — you'd need `--config-path` pointed at one of them. Use `extends: "//"` with `root: false` instead if you want repo-wide runs.

Extended files cannot themselves extend.

## Sharing config via an npm package

Export the config from the package:

```json
{
	"name": "@org/shared-configs",
	"type": "module",
	"exports": { "./biome": "./biome.json" }
}
```

Consume it by specifier:

```json
{ "extends": ["@org/shared-configs/biome"] }
```

Resolution happens from the working directory (CLI) or project root (LSP). Anything starting with `.` or ending in `.json`/`.jsonc` is treated as a relative path and will never resolve from `node_modules/`, so the specifier must be extensionless.

If CI uses this, the workflow has to install dependencies before running Biome — the first-party GitHub Action alone won't resolve the package. See `integrations.md`.
