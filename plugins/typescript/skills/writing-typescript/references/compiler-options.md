# Compiler Options Reference

Contents:

- [Module recipes by environment](#module-recipes-by-environment)
- [Strictness flags outside `strict`](#strictness-flags-outside-strict)
- [TypeScript 6.0 default changes](#typescript-60-default-changes)
- [Deprecated and removed in 6.0](#deprecated-and-removed-in-60)
- [Build performance options](#build-performance-options)

## Module recipes by environment

From `modules-reference/guides/Choosing Compiler Options.md`. Each recipe shows only
module-related settings — combine with the baseline in SKILL.md.

### Bundler (Vite, webpack, esbuild, Parcel, tsx)

```json5
{
	compilerOptions: {
		module: 'esnext',
		moduleResolution: 'bundler',
		esModuleInterop: true,
		customConditions: ['module'], // consult your bundler's docs
		noEmit: true, // or "emitDeclarationOnly"
		allowImportingTsExtensions: true,
		allowArbitraryExtensions: true,
		verbatimModuleSyntax: true // or "isolatedModules"
	}
}
```

The docs additionally recommend _not_ setting `{"type": "module"}` in package.json or using
`.mts` files in bundler projects for now — some bundlers change their ESM/CJS interop
behavior under those conditions in ways `moduleResolution: bundler` cannot model.

### Node.js, running the compiled output

```json5
{
	compilerOptions: {
		module: 'nodenext',
		// implied by nodenext: moduleResolution, esModuleInterop, target
		verbatimModuleSyntax: true
	}
}
```

Set `"type": "module"` in package.json or use `.mts` files if emitting ES modules.

### Library published to npm

```json5
{
	compilerOptions: {
		module: 'node18',
		target: 'es2020', // the LOWEST version you support
		strict: true,
		verbatimModuleSyntax: true,
		declaration: true,
		sourceMap: true,
		declarationMap: true,
		rootDir: 'src',
		outDir: 'dist'
	}
}
```

Why each choice matters for libraries specifically:

- **`node18` over `bundler`.** `moduleResolution: bundler` accepts `export * from "./utils"`
  with no extension. That compiles unchanged under `module: esnext` and then throws
  `ERR_MODULE_NOT_FOUND` for consumers running Node. Writing `"./utils.js"` works in both.
  The docs describe `bundler` as infectious for this reason.
- **Lowest `target`.** `target` implies a `lib` value, so a high target also grants access to
  globals that won't exist in older consumer environments.
- **`strict: true`.** Non-strict type-level code leaks into emitted `.d.ts` files and errors
  for consumers who _are_ strict. `interface Sub extends Super { foo: string | undefined }`
  only errors under `strictNullChecks` — the consumer's setting, not yours.
- **`verbatimModuleSyntax`.** Prevents imports whose meaning depends on the consumer's
  `esModuleInterop` value, and blocks `export default` in modules emitted as CommonJS.
- **Separate `rootDir`/`outDir`.** Required if you publish source files: extension
  substitution otherwise makes consumers load your `.ts` files instead of the `.d.ts`.

Bundled libraries carry two caveats: TypeScript cannot model split resolution (bundled
first-party imports vs. externalized dependencies) in one compilation, and unbundled
declaration files can emit extensionless imports that error for `nodenext` consumers and
infect the referencing types with `any`.

## Strictness flags outside `strict`

Defaults confirmed from the table in `project-config/Compiler Options.md`.

| Flag                                    | Default | Effect                                        |
| --------------------------------------- | ------- | --------------------------------------------- |
| `noUncheckedIndexedAccess`              | `false` | Adds `undefined` to indexed access results    |
| `exactOptionalPropertyTypes`            | `false` | `?:` stops implying `\| undefined` as a value |
| `noPropertyAccessFromIndexSignature`    | `false` | Forces `obj["key"]` for index-signature keys  |
| `noImplicitOverride`                    | `false` | Requires `override` on overriding members     |
| `noImplicitReturns`                     | `false` | Flags code paths with no return               |
| `noFallthroughCasesInSwitch`            | `false` | Flags missing `break`                         |
| `noUnusedLocals` / `noUnusedParameters` | `false` | Flags dead bindings                           |

Implied by `strict`: `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`,
`useUnknownInCatchVariables`, `alwaysStrict`, and the other `strict*` family flags.

`noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` are the two the docs' own
`tsc --init` template turns on, and the two most likely to surface real bugs in existing code.

## TypeScript 6.0 default changes

From `release-notes/TypeScript 6.0.md`. These change behavior with no code edit.

| Option                         | Old default                  | 6.0 default                              |
| ------------------------------ | ---------------------------- | ---------------------------------------- |
| `strict`                       | `false`                      | `true`                                   |
| `module`                       | varies by target             | `esnext`                                 |
| `target`                       | `es5`/`es3`                  | current-year ES (`es2025` now, floating) |
| `types`                        | all of `node_modules/@types` | `[]`                                     |
| `rootDir`                      | inferred common source dir   | directory containing tsconfig.json       |
| `noUncheckedSideEffectImports` | `false`                      | `true`                                   |
| `libReplacement`               | `true`                       | `false`                                  |

Two adjustments most projects need on upgrade: set `"types": ["node"]` (or whatever globals
you rely on), and set `"rootDir": "./src"` if sources live below the tsconfig directory.
`"types": ["*"]` restores 5.9 behavior but forfeits the build-time win.

## Deprecated and removed in 6.0

Set `"ignoreDeprecations": "6.0"` to silence these in 6.0 — but 7.0 removes them entirely.

| Deprecated                                                      | Replacement                                                     |
| --------------------------------------------------------------- | --------------------------------------------------------------- |
| `moduleResolution: node` / `node10`                             | `nodenext` (Node) or `bundler` (bundler/Bun)                    |
| `moduleResolution: classic`                                     | `nodenext` or `bundler`                                         |
| `module: amd \| umd \| systemjs \| none`                        | An ESM-emitting target, or a bundler                            |
| `target: es5`                                                   | `es2015` or higher; external compiler if ES5 output is required |
| `downlevelIteration`                                            | Nothing — only affected ES5 emit                                |
| `baseUrl`                                                       | Fold the prefix into each `paths` entry                         |
| `esModuleInterop: false`, `allowSyntheticDefaultImports: false` | Cannot be disabled                                              |
| `alwaysStrict: false`                                           | Cannot be disabled; all code is JS strict mode                  |
| `outFile`                                                       | An external bundler                                             |
| `module Foo {}` namespace syntax                                | `namespace Foo {}`                                              |

The `ts5to6` tool referenced in the release notes can automate the `baseUrl` and `rootDir`
adjustments.

## Build performance options

- `skipLibCheck: true` — skips type checking of `.d.ts` files.
- `incremental: true` — writes `.tsbuildinfo` so rebuilds only recheck what changed.
- `assumeChangesOnlyAffectDirectDependencies` — with `incremental` and watch mode, limits
  recheck propagation to direct dependents.
- `types: []` plus an explicit list — the largest single win the docs quantify (20–50%).
- `libReplacement: false` — avoids failed module resolutions on every run (6.0 default).
- `isolatedDeclarations` (5.5) — allows declaration emit per-file without whole-program
  analysis, enabling parallel builds.
- `noCheck` (5.6) — emit without type checking, for pipelines that check separately.
- Project references — split large programs so each project rebuilds independently.
