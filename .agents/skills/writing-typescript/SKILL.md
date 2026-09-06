---
name: writing-typescript
description: Chooses TypeScript compiler settings and type-level designs for new code — tsconfig and module resolution, strictness flags, API surface shape, and `satisfies` over annotations to preserve literal inference. Use when starting a TypeScript file, package, or project, when writing or reviewing a tsconfig.json, when choosing between interface/type/enum/union or between overloads and unions, when picking module and target settings, and when a config object, route table, or lookup map must be checked against a constraint without losing its specific types. Also use when the user asks for "a TypeScript setup", a starter config, or best practices for a new TS codebase, even if they don't name a compiler option. Not for routine authoring of a single function where no config or design decision is at stake.
license: MIT
---

# Writing TypeScript

Sourced from the TypeScript documentation through **TypeScript 6.0**. Where the docs contain
advice from different eras, 6.0 release notes supersede older tutorials — several tutorial
pages still recommend options that 6.0 deprecates.

## Start from the prescriptive baseline, not a minimal config

The docs ship an opinionated default config (`release-notes/TypeScript 5.9.md`, "Minimal and
Updated `tsc --init`"). Write this, adjusting the module block per environment below:

```json5
{
	compilerOptions: {
		module: 'nodenext',
		target: 'esnext',
		types: [], // add "node", "jest" etc. explicitly

		sourceMap: true,
		declaration: true,
		declarationMap: true,

		noUncheckedIndexedAccess: true, // NOT implied by strict
		exactOptionalPropertyTypes: true, // NOT implied by strict

		strict: true,
		verbatimModuleSyntax: true,
		isolatedModules: true,
		noUncheckedSideEffectImports: true,
		moduleDetection: 'force',
		skipLibCheck: true
	}
}
```

`strict: true` is not the maximum strictness setting. `noUncheckedIndexedAccess`,
`exactOptionalPropertyTypes`, `noImplicitOverride`, `noPropertyAccessFromIndexSignature`,
`noUnusedLocals`, and `noImplicitReturns` all default to `false` and are unaffected by
`strict` (`project-config/Compiler Options.md`). Turning on `strict` alone and calling the
project strict is the most common config error.

`"types": []` matters for build speed, not just correctness: the docs report 20–50% build
time improvements from setting it, because the old default enumerated every package in
`node_modules/@types` (`release-notes/TypeScript 6.0.md`).

## Module settings depend on the environment

There is no portable module config. Pick by where the code runs — full recipes and reasoning
in `references/compiler-options.md`:

| Environment                           | `module`   | `moduleResolution`  |
| ------------------------------------- | ---------- | ------------------- |
| Bundler (Vite, webpack, esbuild, tsx) | `esnext`   | `bundler`           |
| Node.js, running tsc output           | `nodenext` | implied by `module` |
| Library published to npm              | `node18`   | implied by `module` |

Do not write `"moduleResolution": "node"` — deprecated in 6.0 and removed in 7.0. It encodes
Node 10's algorithm. Likewise `baseUrl` (deprecated; fold the prefix into `paths` entries),
`target: "es5"` (deprecated), and `module: "amd" | "umd" | "systemjs" | "none"` (removed).

For libraries, set `target` to the _lowest_ ECMAScript version you support, and prefer
`nodenext`-style resolution over `bundler`: `bundler` is infectious, accepting extensionless
relative imports that break at runtime under Node
(`modules-reference/guides/Choosing Compiler Options.md`).

A single tsconfig describes a single environment. Server, DOM, worker, and test code each
need their own tsconfig connected by project references — not one config with a union of
their settings.

## `satisfies` instead of a type annotation on config objects

Annotating a value with its constraint discards the specific literal types. `satisfies`
checks the constraint and keeps inference (`release-notes/TypeScript 4.9.md`):

```ts
// Loses per-key types: palette.green is string | RGB, so .toUpperCase() errors
const palette: Record<Colors, string | RGB> = { red: [255, 0, 0], green: '#00ff00' };

// Checks keys and values, keeps green as string
const palette = { red: [255, 0, 0], green: '#00ff00' } satisfies Record<Colors, string | RGB>;
```

Reach for `satisfies` whenever the value is a literal you also want to read back precisely:
config objects, route tables, lookup maps, const-like exports.

## Designing the API surface

Four rules from `declaration-files/Do's and Don'ts.md` that contradict common defaults:

- **Order overloads specific-to-general.** TypeScript picks the _first_ matching overload, so
  a general signature placed first permanently hides the specific ones below it.
- **Prefer a union parameter over overloads that differ in one argument position.** Callers
  passing a `string | number` through cannot satisfy any single overload, but can satisfy the
  union.
- **Prefer optional parameters over overloads that differ only in trailing arguments** — but
  only when the return type is identical.
- **Type ignored callback returns as `void`, never `any`.** `void` stops callers from
  consuming a value that isn't meant to exist; `any` lets the mistake through silently.

Never use the boxed types `Number`, `String`, `Boolean`, `Symbol`, or `Object`. When a value
is genuinely unconstrained use `unknown`, not `any` — `any` disables checking for everything
downstream of it.

Read `references/api-design.md` when writing a `.d.ts`, a public API, or any signature with
overloads or callbacks — it has the worked failure cases for each rule above.

## Make unions exhaustive at compile time

Discriminated union plus a `never` assignment in the default branch turns "someone added a
variant and forgot a case" into a compile error (`handbook-v2/Narrowing.md`):

```ts
function area(shape: Shape) {
	switch (shape.kind) {
		case 'circle':
			return Math.PI * shape.radius ** 2;
		case 'square':
			return shape.sideLength ** 2;
		default:
			const _exhaustive: never = shape;
			return _exhaustive;
	}
}
```

Prefer this over an optional-property object with a `kind` field — optional properties don't
narrow, so every access needs a non-null assertion.

## Verify

Before finishing, confirm the config actually type-checks the code you wrote: run `tsc
--noEmit` and check that no option you used appears in the 6.0 deprecation list above. If the
project targets TypeScript 5.x, `strict` still defaults to `false` — set it explicitly rather
than relying on the version's default.
