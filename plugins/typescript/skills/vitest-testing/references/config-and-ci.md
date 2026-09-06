# Config, coverage, filtering, and CI

Read this when creating or editing `vitest.config.*`, adding coverage, or wiring CI. Option semantics change between majors — verify any option you haven't used against `https://vitest.dev/config/<option>.md` (all lowercase, e.g. `config/restoremocks.md`) or the full reference `https://vitest.dev/config.md`.

## Contents

- Config file basics
- Recommended baseline config
- Environments
- Coverage
- Filtering and selecting tests
- CI recipes
- Performance notes

## Config file basics

- If the project has a `vite.config.*`, add a `test` block there (one file, shared plugins/aliases). Otherwise create `vitest.config.ts` importing `defineConfig` from `'vitest/config'` — **not** from `'vite'`, or the `test` key won't type-check.
- A standalone `vitest.config.ts` has higher priority than and **overrides** `vite.config.ts` (they don't merge). Use `mergeConfig` from `vitest/config` if you need both.
- `tsconfig` path aliases require the `vite-tsconfig-paths` plugin or a manual `test.alias` map with absolute paths.

## Recommended baseline config

```ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
	test: {
		// Reset vi.fn()/module-factory mocks (history + implementation) before
		// each test — prevents order-dependent failures from leaked mock state.
		// (In Vitest 4, restoreMocks alone no longer does this.)
		mockReset: true,
		// Restore vi.spyOn spies to the original method between tests.
		restoreMocks: true,
		// Auto-undo vi.stubEnv / vi.stubGlobal between tests.
		unstubEnvs: true,
		unstubGlobals: true
	}
});
```

Add only what the project needs beyond this (environment, setupFiles, coverage, globals). Avoid copying large option blocks "just in case" — defaults are good (isolated parallel files, `pool: 'forks'`, 5s timeouts).

Common additions:

- `globals: true` — Jest-style no-import `test`/`expect`; pair with `"types": ["vitest/globals"]` in tsconfig. Only enable if the codebase already relies on it (some libs like @testing-library cleanup hooks expect it).
- `setupFiles: ['./test/setup.ts']` — runs before each test file; the place for `expect.extend`, jest-dom matchers, msw server wiring, polyfills.
- `globalSetup` — runs **once per run** in a separate process (start a DB container, seed data). Cannot share in-memory state with tests; communicate via `provide`/`inject` or env vars.

## Environments

Default is `node` — no DOM. For component or DOM-touching tests:

```ts
test: {
	environment: 'jsdom';
} // or 'happy-dom' (faster, less complete)
```

Install the environment package (`npm i -D jsdom`). Mixed suites: annotate individual files with `// @vitest-environment jsdom` at the top, or split into [projects](https://vitest.dev/guide/projects.md) for larger codebases (also the tool for monorepos and unit-vs-integration splits with different configs).

## Coverage

```bash
npm i -D @vitest/coverage-v8   # default provider; use @vitest/coverage-istanbul if v8 output is inaccurate for your transforms
npx vitest run --coverage
```

```ts
test: {
  coverage: {
    provider: 'v8',
    reporter: ['text', 'html', 'lcov'],
    include: ['src/**'],          // measure source, not test/helper files
    thresholds: { lines: 80, functions: 80, branches: 80, statements: 80 },
  },
}
```

- `include` matters: by default coverage may report only files touched by tests; setting `coverage.include` to your source glob surfaces completely untested files as 0%.
- Treat thresholds as a ratchet against regression, not a target to game — a line executed is not a line verified.

## Filtering and selecting tests

```bash
npx vitest run src/utils.test.ts        # by file
npx vitest run -t "handles zero"        # by test name pattern
npx vitest run src/math.test.ts:12      # by line number
npx vitest run --changed                # files affected by git changes
```

- `.only` / `.skip` / `.todo` for local development; never commit `.only` — enable `allowOnly: false` in CI (it's already false by default when `CI=true`).
- Durable subsets (smoke, integration): use [test tags](https://vitest.dev/guide/test-tags.md) or separate projects rather than filename regexes in scripts.

## CI recipes

```bash
npx vitest run --coverage        # never bare `vitest` in CI — watch mode hangs
```

- Vitest auto-detects `CI=true`: disables watch, forbids `.only`.
- GitHub Actions annotations: `reporters: ['default', 'github-actions']` (or `--reporter=github-actions`).
- JUnit for other CI systems: `--reporter=junit --outputFile=test-results.xml`.
- Flaky-test mitigation: `retry: 1` in CI config is acceptable as a tourniquet, but track and fix the root cause — retries hide real race conditions.
- Shard large suites across machines: `vitest run --shard=1/3` etc., then merge coverage via `--merge-reports`. Fetch `guide/cli.md` for current flags.

## Performance notes

If the suite is slow, fetch `https://vitest.dev/guide/improving-performance.md` before changing pools or isolation — the trade-offs matter:

- `isolate: false` is the biggest speed lever but only safe when tests don't rely on module-level state resets.
- `pool: 'threads'` can be faster than the default `forks`, but breaks native modules and Node `fetch` in some versions (segfaults, "Failed to terminate worker") — that's why `forks` is the default.
- Profile first (`--reporter=verbose` durations, or the profiling guide) instead of guessing.
