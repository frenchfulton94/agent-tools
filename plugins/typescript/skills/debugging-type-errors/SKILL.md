---
name: debugging-type-errors
description: Diagnoses TypeScript compiler errors and build-shape problems by reading error elaborations bottom-up, isolating narrowing and inference failures, and tracing why tsc included a file or resolved an import a given way. Use when tsc reports an error the user wants explained or fixed, when an error message seems wrong or unrelated to the code, when narrowing "stops working" inside callbacks or after assignments, when a project errors or emits to unexpected output paths after a TypeScript upgrade, when an import type-checks but fails at runtime, or when the user pastes a compiler error. Also use for "cannot find name", "not assignable to", "possibly undefined", and excessively-deep instantiation errors, even when the user only pastes code and says it doesn't compile. Not for runtime exceptions or test-runner configuration that tsc never reported.
license: MIT
---

# Debugging Type Errors

Sourced from the TypeScript documentation through **TypeScript 6.0**.

The default failure mode is silencing rather than diagnosing: reaching for `as`, `!`,
`@ts-ignore`, or a widened parameter type before knowing what the compiler objected to. Each
of those converts a compile error into a runtime bug. Diagnose first.

## Read the elaboration bottom-up

A TypeScript error is a chain, not a sentence. The leading message states the assignment that
failed; each sub-message answers "why?" about the line above it
(`handbook-v2/Understanding Errors.md`). **The last sub-message is the root cause** — it names
the two concrete types that are actually incompatible.

```ts
let a: { m: number[] };
let b = { m: [''] };
a = b;
```

The chain reads: `b` isn't assignable to `a` → because property `m` is incompatible → because
`string[]` isn't assignable to `number[]` → because `string` isn't assignable to `number`.
Only the final link tells you the fix is at the array literal, not the assignment.

"Assignable to" is directional. `S` assignable to `T` does not imply the reverse, so read the
direction in the message before concluding which side is wrong.

## Match the symptom to the cause

| Symptom                                                             | Likely cause                                                                     |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Object literal errors on a property the target type doesn't declare | Excess property check — only fires on fresh object literals, not on variables    |
| Error names a union member you didn't intend to use                 | The literal matched neither member; TS reports against the closest one           |
| `possibly undefined` on an array element or index access            | `noUncheckedIndexedAccess` is on — the index genuinely may miss                  |
| Narrowing lost inside a callback or after `await`                   | Narrowing doesn't survive function boundaries or assignments                     |
| Property access errors after a `typeof x === "object"` check        | `null` is `"object"`; narrow it out separately                                   |
| `Type instantiation is excessively deep and possibly infinite`      | A recursive conditional or mapped type; reduce depth or add a base case          |
| Everything in the file errors at once                               | Usually a config or resolution failure, not a type failure — see the flags below |

Narrowing rules worth checking explicitly (`handbook-v2/Narrowing.md`): assignments reset a
narrowed type to its declared type; `in`, `instanceof`, `typeof`, and truthiness each narrow
differently; and truthiness narrowing silently keeps `0` and `""` in the falsy branch, which
is the standard source of "the empty-string case disappeared".

Since TypeScript 5.5 the compiler infers type predicates for simple functions, so a
hand-written predicate may now be unnecessary — and a _wrong_ hand-written predicate is
invisible, because `x is T` is an assertion the compiler trusts rather than verifies. When
narrowing behaves impossibly, check whether a predicate in the chain is lying.

## Errors that are really config errors

After a TypeScript upgrade — especially to 6.0 — several errors point nowhere near their
cause. The release notes state directly that some deprecations have no error message
identifying the underlying issue.

| Error                                                               | Cause                                                              | Fix                                       |
| ------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------- |
| `Cannot find name 'process'` / `'describe'` / `'Bun'`, many at once | 6.0 changed `types` to default to `[]`                             | Add `"types": ["node"]`, `["jest"]`, etc. |
| Output lands in `dist/src/` instead of `dist/`                      | 6.0 changed `rootDir` to default to the tsconfig's directory       | Set `"rootDir": "./src"`                  |
| Import resolves in the editor but fails at runtime                  | `moduleResolution: bundler` accepts extensionless relative imports | Use `nodenext`, add the `.js` extension   |
| `import * as x` suddenly wrong                                      | `esModuleInterop` can no longer be `false` in 6.0                  | Change to a default import                |
| Reserved-word identifier errors (`await`, `static`, `private`)      | `alwaysStrict: false` is gone; all code is JS strict mode          | Rename the identifiers                    |

A large, sudden error count almost always means the program changed shape, not that the code
changed meaning.

## Diagnostic flags

Use these before hypothesizing:

- `tsc --showConfig` — prints the fully resolved config, including everything inherited from
  `extends`. Confirms which options are actually in effect.
- `tsc --explainFiles` — prints why each file entered the program. This is the tool for "why
  is this `.d.ts` here", "why is the wrong `lib` loaded", and "why didn't `exclude` work".
  Verbose; pipe it to a file or a pager.
- `tsc --traceResolution` — step-by-step module resolution, for imports that resolve to the
  wrong file or not at all.
- `tsc --noEmit` — check without writing output while iterating.
- `tsc --generateTrace <dir>` — event trace and type list, for compilations that are slow
  rather than wrong.
- `tsc --extendedDiagnostics` — where compile time went.

## Verify the fix

State which of the two types in the final elaboration link you changed and why that was the
wrong one. If the fix was a type assertion, say what runtime guarantee justifies it — if
there isn't one, the assertion is deferring the error to runtime rather than fixing it.
