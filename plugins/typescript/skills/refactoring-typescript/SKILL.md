---
name: refactoring-typescript
description: Tightens loose TypeScript and migrates JavaScript to TypeScript incrementally — removing `any` and unchecked assertions, staging strictness flags, converting files with JSDoc first, and changing types in code that already ships. Use when the user wants to make an existing codebase stricter or better-typed, convert a JS project or file to TS, remove `any`/`@ts-ignore`/non-null assertions, adopt a new strictness flag without breaking the build, or upgrade a project to a newer TypeScript version. Also use for "clean up these types", "why is this typed as any", and gradual-typing questions, even when the user doesn't mention migration. Scoped to type-level change — not general code restructuring, renaming, or framework migration.
license: MIT
---

# Refactoring TypeScript

Sourced from the TypeScript documentation through **TypeScript 6.0**.

Note on the corpus: `tutorials/Migrating from JavaScript.md` predates the current module
guidance and recommends `target: es5` and `module: amd | system | umd`, all deprecated or
removed in 6.0. Its _sequencing_ advice is still sound; take config values from
`release-notes/TypeScript 6.0.md` and the modules guide instead.

## Separate inputs from outputs before touching anything

TypeScript will overwrite `.js` files that sit alongside their sources. Establish
`src/` → `outDir` separation first, or the first `tsc` run destroys the code being migrated.

## Migrate in stages, not file-by-file rewrites

The order matters because each stage keeps the build green while shrinking the untyped
surface:

1. **Accept JS into the program.** `allowJs: true`, `include: ["./src/**/*"]`, an `outDir`.
   The build now covers every file, and editors give completions immediately.
2. **Turn on checking for JS.** `checkJs: true` project-wide, or `// @ts-check` per file to
   stage it. Errors appear without a single rename.
3. **Type in place with JSDoc.** `@param`, `@returns`, `@type`, `@satisfies` all work in
   `.js` files (`javascript/JSDoc Reference.md`). This decouples "add types" from "rename
   files", so each PR stays reviewable.
4. **Rename to `.ts` / `.tsx`.** Red squiggles here don't block emit — TypeScript still
   compiles. Add `noEmitOnError: true` when you want them to.
5. **Ramp strictness.** Below.

Set `noImplicitAny` _before_ mass file edits rather than after. Turning it on later means
revisiting every file a second time.

## Ramp strictness in dependency order

Enable in this sequence; each stage is smaller than it looks once the previous one lands:

1. `noImplicitAny` — surfaces every location the compiler silently gave up.
2. `strictNullChecks` — the largest single change. `null` and `undefined` become their own
   types, so anything nullable needs a union. Expect dependency `.d.ts` files to need updates
   too.
3. The rest of `strict` — `strictFunctionTypes`, `useUnknownInCatchVariables`, and the
   remaining `strict*` family.
4. The flags `strict` does _not_ include: `noUncheckedIndexedAccess`,
   `exactOptionalPropertyTypes`, `noImplicitOverride`,
   `noPropertyAccessFromIndexSignature`, `noImplicitReturns`,
   `noFallthroughCasesInSwitch`. All default to `false` regardless of `strict`.

A project that sets `strict: true` and stops has adopted roughly half the available checking.
`noUncheckedIndexedAccess` in particular finds real bugs — every `arr[i]` and `map[key]` that
assumed a hit.

## Replacing `any`, not relocating it

The migration-era `any` is meant to be temporary. Replacements in order of preference:

- **`unknown` plus narrowing.** Same permissiveness at the boundary, but the compiler forces
  a check before use. This is the correct type for parse results, `catch` bindings, and
  external input.
- **A discriminated union** when the value is one of several known shapes.
- **`satisfies`** when the value is a literal that should be checked against a constraint but
  keep its specific inferred type — the usual fix for a config object annotated so broadly
  that reads back from it are useless.
- **A type predicate** only when the check genuinely can't be expressed in the type system.
  Since 5.5 the compiler infers predicates for simple functions, so try deleting a
  hand-written one first. A hand-written predicate is an unverified assertion; a wrong one
  silently poisons everything downstream.

Non-null assertions (`!`) and `as` are not replacements — they move the failure to runtime.
When removing them, the question is what the code actually guarantees; if nothing does, the
fix is a check, not a cast.

## Changing types in code that already ships

- Widening a parameter or narrowing a return type is safe for callers. The reverse breaks
  them — narrowing a parameter or widening a return type is a breaking change.
- Adding a member to a union breaks every exhaustive `switch` over it. That's the intended
  behavior if those switches use a `never` check; without one, the new case silently falls
  through. Add the exhaustiveness check _before_ adding the union member.
- Adding a required property to an interface breaks every construction site. Adding it as
  optional doesn't, but under `exactOptionalPropertyTypes` optional no longer implies
  `| undefined` as an assignable value.
- Changing an overload set to a union parameter is usually compatible in the caller direction
  and improves pass-through call sites.
- In libraries, a type-level change with no runtime change is still a breaking change for
  consumers compiling with different strictness than yours. Compile with `strict: true` so
  loose type-level code doesn't reach the emitted `.d.ts`.

## Verify

Re-run `tsc --noEmit` after each stage rather than at the end, and keep the diff for a stage
to one concern — a rename PR and a strictness PR reviewed together are impossible to reason
about. Before declaring a file migrated, confirm no `any`, `!`, or `@ts-ignore` was added to
make it pass; if one was, it isn't migrated, it's deferred.
