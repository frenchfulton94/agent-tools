---
name: vitest-testing
description: Write, run, debug, and maintain professional JavaScript/TypeScript tests with Vitest — unit tests, mocking (vi.fn, vi.spyOn, vi.mock), async tests, snapshots, fixtures, coverage, and vitest.config setup. Use this skill whenever the user wants tests written for JS/TS code, mentions Vitest, vitest.config, "unit tests" in a Vite/Node/React/Vue project, needs failing Vitest tests fixed or flaky tests debugged, wants a test suite reviewed or migrated from Jest, or asks to set up test coverage — even if they don't name Vitest explicitly but the project uses it (vitest in package.json).
metadata:
  version: '1.0'
  docs-source: https://vitest.dev
---

# Vitest Testing

Guidance for writing professional, maintainable tests with Vitest. The core concepts are below; for anything deeper or newer, fetch the **live official docs** — see [Staying current with the docs](#staying-current-with-the-docs). Vitest evolves quickly (v4 changed defaults and recommendations), so prefer the live docs over memory whenever an API detail matters.

## Workflow

1. **Inspect the project first.** Check `package.json` for the `vitest` version and test script, and look for `vitest.config.{ts,js}` or a `test` block in `vite.config.*`. The installed major version determines which APIs to use — if unsure how a feature works in that version, fetch the doc page for it (see doc map).
2. **Write or fix the tests** following the principles below.
3. **Verify by running them.** Use `npx vitest run` (single pass, no watch — watch mode hangs non-interactive shells). Narrow the run while iterating: `npx vitest run path/to/file.test.ts` or `npx vitest run -t "test name pattern"`.
4. **Iterate until green**, reading Vitest's failure output — it includes a diff, the failing line, and a code frame, which usually pinpoints the problem without extra logging.

If Vitest isn't installed yet: `npm install -D vitest`, add `"test": "vitest"` to package.json scripts. TypeScript works out of the box — no ts-jest, no build step. (With Bun, use `bun run test`, not `bun test`, which runs Bun's own runner.)

## Test fundamentals

Tests live in files matching `**/*.{test,spec}.{ts,js,mjs,cjs,tsx,jsx}` anywhere in the project. Co-locate them next to source (`utils.ts` + `utils.test.ts`) unless the project already uses a `__tests__/` or `test/` directory — follow the existing convention.

```ts
import { describe, expect, test } from 'vitest';
import { formatPrice } from './formatPrice.js';

describe('formatPrice', () => {
	test('formats USD prices', () => {
		expect(formatPrice(10, 'USD')).toBe('$10.00');
	});

	test('handles negative amounts', () => {
		expect(formatPrice(-5.5, 'USD')).toBe('-$5.50');
	});
});
```

- `test` and `it` are identical aliases — match whichever the codebase already uses.
- Import from `'vitest'` unless the project has `globals: true` in its config (check before assuming either way; with globals + TS, `tsconfig.json` needs `"types": ["vitest/globals"]`).
- Use `describe` to group tests per exported function/method. Keep nesting to one or two levels — deep trees are a smell.

### What to test

Test the **contract** — inputs, return values, errors, observable side effects — not internals. Litmus test: _if someone refactored the internals and the output stayed the same, would this test break?_ If yes, it's testing implementation details; rewrite it against behavior.

- One behavior per test. An "and" in the test name means it should be split.
- Names describe behavior, not mechanics: `"returns 0 for an empty cart"`, not `"works correctly"` or `"calls Intl.NumberFormat with correct options"`. Failing test names should read like a spec of what broke.
- After the happy path, cover boundaries and error paths: zero, empty string, limits and limit+1, invalid input, the error message text. Only test edges a real caller could actually hit.
- Structure each test as Arrange → Act → Assert (no section comments needed).
- Keep tests independent: create fresh state inside each test (or in `beforeEach`) so tests pass in any order. Never let one test depend on values produced by another (e.g., auto-increment IDs from shared module state — assert relative properties, not absolute values).
- When fixing a bug: write the failing test that reproduces it _first_, then fix the code, then watch it go green. Never "fix" a bug by changing the test to match broken behavior.

### Choosing matchers

| Situation                                             | Use                                                                                                                             |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Primitives (numbers, strings, booleans)               | `toBe`                                                                                                                          |
| Object/array structure                                | `toEqual`                                                                                                                       |
| Also care about `undefined` props and class types     | `toStrictEqual`                                                                                                                 |
| Floating point (`0.1 + 0.2`)                          | `toBeCloseTo` — never `toBe`                                                                                                    |
| Subset of object fields                               | `toMatchObject` or `toHaveProperty('a.b', v)`                                                                                   |
| Item in array/Set                                     | `toContain` (primitives) / `toContainEqual` (objects)                                                                           |
| Unknown exact value, known shape                      | asymmetric: `expect.any(Number)`, `expect.stringContaining`, `expect.arrayContaining`, `expect.objectContaining`                |
| Function throws                                       | `expect(() => fn()).toThrow('message')` — **must wrap in an arrow function**, or the error escapes before `expect` can catch it |
| Check several independent fields, report all failures | `expect.soft(...)`                                                                                                              |

Prefer the most precise matcher: `toBeTruthy` where you mean `toBeDefined` hides bugs (`0` and `''` are defined but falsy).

## Async tests

Make the test function `async` and `await` everything — Vitest waits for the returned promise; rejections fail the test.

```ts
test('fetches user', async () => {
	const user = await fetchUser(1);
	expect(user.name).toBe('Alice');
});

test('rejects for missing user', async () => {
	await expect(fetchUser(999)).rejects.toThrow('User not found');
});
```

- **Always `await` `.resolves` / `.rejects` assertions** — without the `await`, the test can finish before the assertion runs.
- A promise that rejects with no handler fails the whole run ("Unhandled Rejection") even if all assertions passed — this almost always means a missing `await`.
- Assertions inside callbacks/loops can silently never execute; guard with `expect.hasAssertions()` or `expect.assertions(n)` when assertions are conditional.
- Default per-test timeout is 5s; pass a third argument for legitimately slow tests: `test('slow', async () => {...}, 10_000)`.

## Setup, teardown, and fixtures

- `beforeEach`/`afterEach` run around every test (afterEach even on failure) — use them to guarantee clean state. `beforeAll`/`afterAll` run once per file for expensive resources (DB connections, servers).
- Hooks inside a `describe` scope only to that block; outer hooks wrap inner ones.
- `beforeEach` can return a cleanup function; `onTestFinished(() => ...)` registers cleanup right where a resource is created inside a test.
- For reusable typed setup, prefer **fixtures** via `test.extend` — lazily initialized only when a test destructures them, composable, with built-in cleanup. Fetch `guide/test-context.md` when using these.
- Project-wide setup (custom matchers via `expect.extend`, polyfills) belongs in a file listed under `setupFiles` in the config, not copy-pasted `beforeAll`s.

## Mocking

Rules of thumb (from the official guidance):

- **Mock only what's slow, flaky, or side-effectful**: network, filesystem, DB, time/randomness. Don't mock pure functions or cheap in-memory dependencies — real implementations give more confidence.
- **Never mock the unit under test** — mock its dependencies.
- For HTTP, prefer **Mock Service Worker (msw)** over stubbing `fetch` directly.
- Non-determinism: `vi.useFakeTimers()` / `vi.setSystemTime(date)` for time (remember `vi.useRealTimers()` after — system time does **not** auto-reset between tests).

The three tools:

```ts
const fn = vi.fn((a, b) => a + b); // brand-new tracked function
const spy = vi.spyOn(obj, 'method'); // wraps existing method; original still runs unless .mockReturnValue/.mockImplementation
vi.mock(import('./db.js'), () => ({
	// replaces a whole module — HOISTED above all imports
	getUser: vi.fn()
}));
```

- Control outputs: `mockReturnValue`, `mockReturnValueOnce`, `mockResolvedValue`, `mockRejectedValue`, `mockImplementation`.
- Inspect: `toHaveBeenCalledWith`, `toHaveBeenCalledTimes`, `toHaveBeenNthCalledWith`, or raw `fn.mock.calls` / `fn.mock.results`.
- Use `vi.mocked(getUser)` to get typed access to a mocked import in TS.
- Pass `import('./mod.js')` (not the string `'./mod.js'`) to `vi.mock` for type-checked factories and refactor-safe paths.

**Mock hygiene — the #1 source of flaky suites**: mocks accumulate call history and implementations across tests. Set `mockReset: true` + `restoreMocks: true` (and consider `unstubEnvs: true`, `unstubGlobals: true`) in the config rather than sprinkling cleanup in `afterEach` everywhere. Ladder: `mockClear` (history only) < `mockReset` (+ implementation) < `mockRestore` (+ un-spies the original). **Vitest 4 change**: `restoreMocks`/`vi.restoreAllMocks` now only affects `vi.spyOn` spies — it no longer resets `vi.fn()` or module-factory mocks, so a `mockRejectedValue` set in one test _will_ leak into the next unless `mockReset: true` is on. (Caveat: auto-reset options can interfere with `test.concurrent`.)

For partial module mocks, mocking dates/timers/globals/env/classes/fs, and the pitfalls of each, read [references/mocking.md](references/mocking.md) before writing the mock.

## Parameterized tests

Prefer `test.for` (`test.each` exists mainly for Jest compatibility):

```ts
test.for([
	{ input: '25', expected: 25 },
	{ input: '25.9', expected: 25 }
])('parseAge($input) -> $expected', ({ input, expected }) => {
	expect(parseAge(input)).toBe(expected);
});
```

With `test.concurrent`, take `expect` from the test context (second argument) — the global `expect` can't associate snapshots with the right concurrent test.

## Snapshots

Use `toMatchInlineSnapshot()` for small serializable values (self-updating, reviewable in-place) and `toMatchSnapshot()` for larger output. Snapshots complement, not replace, explicit assertions — don't snapshot objects full of volatile data (dates, IDs). Update intentionally with `npx vitest run -u` and review the diff. Details: fetch `guide/snapshot.md`.

## Config, coverage, filtering, CI

Read [references/config-and-ci.md](references/config-and-ci.md) when you need to create or modify `vitest.config.*`, set up coverage (`@vitest/coverage-v8`), configure environments (node vs jsdom/happy-dom), filter/tag tests, or wire Vitest into CI. Don't guess config options — that file plus the live `config.md` doc are the source of truth.

## Gotchas

Environment-specific facts that defy reasonable assumptions — read before debugging weird failures:

- **`vi.mock` is hoisted** to the top of the file and runs before all imports. Variables declared in the test file aren't available inside the factory unless created with `vi.hoisted(() => ...)`.
- **Module mocks only intercept external access.** If `original()` calls `mocked()` internally within the same module, the real function runs — the mock only replaces the export seen by _importers_.
- **`.mock.calls` stores references, not copies.** Mutating an object after passing it to a mock changes the recorded call; assert before mutating or clone in a `mockImplementation`.
- **`vi.setSystemTime` and `vi.stubGlobal`/`vi.stubEnv` don't reset between tests** unless you restore manually or enable `unstubGlobals`/`unstubEnvs` in config.
- **Vitest transforms TS but does not type-check it.** Run `tsc --noEmit` separately; a passing suite can still have type errors.
- **`tsconfig.json` `baseUrl`/`paths` are ignored** — install `vite-tsconfig-paths` and add it to `plugins`, or use relative imports.
- **Watch mode is the default** for the bare `vitest` command. In scripts, CI, or agent shells always use `vitest run`.
- **Test files run in parallel in isolated processes** (default pool: `forks`); tests within a file run sequentially. Cross-file shared state (a dev server port, a temp dir) needs `globalSetup`, not `beforeAll`.
- **Segfaults / "Failed to terminate worker"** usually mean a native module or Node `fetch` under `pool: 'threads'` — switch (back) to `pool: 'forks'`.
- **DOM APIs are undefined by default** — the default environment is `node`. Component/DOM tests need `environment: 'jsdom'` (or `happy-dom`), set globally or per-file via `// @vitest-environment jsdom`.

## Staying current with the docs

Every Vitest doc page is available as clean markdown by appending `.md` to its path. When a question goes beyond this skill — an unfamiliar option, browser mode, a version-specific behavior, migration — **fetch the live page instead of relying on memory**:

- Full index of all pages: `https://vitest.dev/llms.txt`
- Any page as markdown: `https://vitest.dev/<path>.md` (e.g. `https://vitest.dev/guide/mocking/timers.md`, `https://vitest.dev/config/coverage.md`, `https://vitest.dev/api/expect.md`)

[references/doc-map.md](references/doc-map.md) maps common tasks to the exact URLs. Fetch the doc when: the user's Vitest major version differs from what you expect, you're about to use a config option or API you haven't verified, the user asks about browser mode / type testing / advanced APIs, or an error message doesn't match a known gotcha (then fetch `guide/common-errors.md` first).
