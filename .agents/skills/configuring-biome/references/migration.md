# Migrating to Biome

## From ESLint and Prettier

```sh
biome migrate eslint --write
biome migrate prettier --write
```

Run them against an existing `biome.json` — both **overwrite** it rather than merging into it, so create the config first (`biome init`) and expect your hand edits to be replaced. Run the migrations before customizing, not after.

### What `migrate eslint` does

Reads the ESLint config and ports what maps. It handles both legacy `.eslintrc.*` and flat `eslint.config.*`, follows `extends` including shared and plugin configs, ports `globals` into `javascript.globals`, ports `overrides`, and migrates `.eslintignore`.

Known-mapped plugins: TypeScript ESLint, jsx-a11y, eslint-plugin-react, eslint-plugin-unicorn.

Three things to expect:

- **It disables `recommended` and enumerates rules explicitly.** That's intended — it reproduces your ESLint rule set rather than Biome's. If you'd rather start from Biome's defaults, discard the enumeration and set `linter.rules.preset: "recommended"`.
- **Inspired rules are skipped by default.** Biome distinguishes rules identical to an ESLint rule from rules merely inspired by one. Add `--include-inspired` to port the second kind too, accepting that behavior will differ.
- **Naming differs.** ESLint uses `kebab-case`, Biome uses `camelCase`, and many rules were deliberately renamed. biomejs.dev/linter/rules-sources maps ESLint rule → Biome rule.

Node.js is required (the subcommand loads and resolves plugins). YAML configs are not supported.

### The cyclic-reference failure

Some plugins and shared configs export objects with cyclic references, and the migration fails to load them. The error points at config loading, not at a specific plugin.

Workaround: comment out plugin entries and shared configs in the ESLint config, run the migration, then re-enable them one at a time to identify the culprit. Configure the surviving rules by hand in `biome.json` afterward.

### What `migrate prettier` does

Ports formatter options directly. `.prettierrc.js` needs Node.js; JSON5, TOML, and YAML configs are unsupported.

Note that Biome's defaults differ from Prettier's — tabs instead of spaces most visibly — so the migrated config will contain explicit values where you may have been relying on Prettier's defaults. That's correct behavior, not noise.

### After migrating

- Enable VCS integration. Both ESLint and Prettier read ignore files by default; Biome doesn't until `vcs.useIgnoreFile` is set, so the migrated config will lint more than the old tools did.
- Remove `eslint`, `prettier`, their plugins, their configs, and their editor extensions. Two active formatters produce a diff war on save.
- Run `biome check --write` once and commit the reformat as its own commit, so the diff stays reviewable.
- Diff a few files against the Prettier output. Biome tracks Prettier closely but not identically; biomejs.dev/formatter/differences-with-prettier lists the deliberate divergences.

**Caution on the docs:** the migrate guide on biomejs.dev still prints v1-shaped output in its worked examples (`"organizeImports": { "enabled": true }`, `overrides[].include`). The command itself emits the correct v2 shape. Verify against `biome.json`'s `$schema`, not against the page.

## From Biome v1

```sh
biome migrate --write
```

Updates the config to the installed version's shape. Run it after every major upgrade, before touching the file by hand.

What changed, if you're reading a v1 config or v1-era examples:

| v1                                           | v2                                                 |
| -------------------------------------------- | -------------------------------------------------- |
| `organizeImports: { enabled: true }`         | `assist.actions.source.organizeImports: "on"`      |
| `files.include` / `files.ignore`             | `files.includes` with `!` negations                |
| `linter.include` / `linter.ignore`           | `linter.includes`                                  |
| `overrides[].include` / `overrides[].ignore` | `overrides[].includes`                             |
| `linter.rules.recommended: true`             | `linter.rules.preset: "recommended"`               |
| `--apply` / `--apply-unsafe`                 | `--write` / `--write --unsafe`                     |
| (nothing)                                    | `root: false` + `extends: "//"` for nested configs |
| (nothing)                                    | `linter.domains`                                   |
| (nothing)                                    | `plugins` (GritQL)                                 |

The v1 field names are not aliased. A config that still uses them parses without erroring on the unknown keys but applies none of their intent — which is why "Biome ignores my settings" is usually a v1/v2 shape problem rather than a glob problem.
