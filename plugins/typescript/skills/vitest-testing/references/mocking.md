# Mocking patterns and pitfalls

Condensed from the official cheat sheet and mocking guides. When a scenario isn't covered here, fetch the matching page from [doc-map.md](doc-map.md) (Mocking section) — the guides at `https://vitest.dev/guide/mocking/*.md` are the source of truth.

## Contents

- Decision guide
- Module mocking (vi.mock)
- Partial module mocks
- Mocking exported variables and classes
- Dates and timers
- Globals and environment variables
- HTTP requests
- Cleanup matrix

## Decision guide

| You need to…                                                              | Reach for                                   |
| ------------------------------------------------------------------------- | ------------------------------------------- |
| Fake a callback/dependency passed as an argument                          | `vi.fn()`                                   |
| Observe (and optionally override) a method on an object you can reference | `vi.spyOn(obj, 'method')`                   |
| Replace what an _imported module_ provides to the file under test         | `vi.mock(import('./mod.js'), factory)`      |
| Fake HTTP responses                                                       | msw (Mock Service Worker)                   |
| Control time                                                              | `vi.useFakeTimers()` / `vi.setSystemTime()` |
| Fake `import.meta.env` / globals                                          | `vi.stubEnv` / `vi.stubGlobal`              |

## Module mocking (vi.mock)

```ts
import { getUser } from './db.js';

vi.mock(import('./db.js'), () => ({
	getUser: vi.fn()
}));

test('uses the mock', () => {
	vi.mocked(getUser).mockReturnValue({ name: 'Alice' });
	// ...
});
```

Why each piece matters:

- `vi.mock` calls are **hoisted above all imports** — they run first no matter where you write them. Consequence: the factory cannot reference variables defined in the test file. If the factory needs shared values, create them with `vi.hoisted`:
  ```ts
  const { mockGetUser } = vi.hoisted(() => ({ mockGetUser: vi.fn() }));
  vi.mock(import('./db.js'), () => ({ getUser: mockGetUser }));
  ```
- Use `import('./db.js')` (not the string form) so TypeScript type-checks the factory and IDE refactors update the path.
- `vi.mocked(x)` is a type-cast helper giving you the mock API on an imported function in TS.
- **External access only**: the mock replaces what _importers_ of the module see. If a function inside `db.js` calls another function from the same file, it calls the real one. If you need to intercept internal calls, refactor the code (dependency injection) rather than fighting the module system.

## Partial module mocks

Keep the real module but replace specific exports:

```ts
vi.mock(import('./some-path.js'), async (importOriginal) => {
	const mod = await importOriginal();
	return { ...mod, mocked: vi.fn() };
});
```

## Mocking exported variables and classes

- Exported getter/variable: `vi.spyOn(exportsNamespace, 'getter', 'get').mockReturnValue('mocked')` (import the module as `import * as exports from './example.js'`). Note: `vi.spyOn` on module namespaces does **not** work in Browser Mode.
- Exported class:
  ```ts
  vi.mock(import('./example.js'), () => {
  	const SomeClass = vi.fn(
  		class FakeClass {
  			someMethod = vi.fn();
  		}
  	);
  	return { SomeClass };
  });
  ```
  For richer class scenarios fetch `https://vitest.dev/guide/mocking/classes.md`.

## Dates and timers

```ts
vi.setSystemTime(new Date(2022, 0, 1)); // freezes Date.now / new Date()
// ... assertions ...
vi.useRealTimers(); // REQUIRED — does not reset on its own
```

- `vi.useFakeTimers()` fakes `setTimeout`/`setInterval`/etc. **and** also affects `Date`. Advance with `vi.advanceTimersByTime(ms)`, `vi.runAllTimers()`, or `await vi.runAllTimersAsync()` when timer callbacks are async.
- Pair every `useFakeTimers` with `useRealTimers` (typically in `afterEach`), or leaked fake timers will hang unrelated tests that await real delays.

## Globals and environment variables

- `vi.stubGlobal('__VERSION__', '1.0.0')` — persists across tests unless `unstubGlobals: true` in config or `vi.unstubAllGlobals()` is called.
- `vi.stubEnv('VITE_ENV', 'staging')` for `import.meta.env` / `process.env` — same persistence rule; enable `unstubEnvs: true` in config to auto-restore.
- Direct assignment (`import.meta.env.X = 'y'`) works but never resets itself; prefer the stub helpers.

## HTTP requests

Prefer msw over stubbing `fetch`: it intercepts at the network level, so the code under test runs unmodified, and handlers are shared between tests and dev. Setup (server, `beforeAll(server.listen)` / `afterEach(server.resetHandlers)` / `afterAll(server.close)`) is version-sensitive — fetch `https://vitest.dev/guide/mocking/requests.md` for the current recipe rather than writing it from memory.

## Cleanup matrix

| Call / option                          | Clears call history | Removes implementation | Restores original (vi.spyOn spies) |
| -------------------------------------- | ------------------- | ---------------------- | ---------------------------------- |
| `mockClear()` / `clearMocks: true`     | ✅                  | ❌                     | ❌                                 |
| `mockReset()` / `mockReset: true`      | ✅                  | ✅                     | ❌                                 |
| `mockRestore()` / `restoreMocks: true` | spies only (v4)     | spies only (v4)        | ✅                                 |

**Vitest 4 change:** `vi.restoreAllMocks()` and the `restoreMocks` option now only act on spies created with `vi.spyOn` — `vi.fn()` mocks and module-factory mocks are untouched. Calling `.mockRestore()` directly on an individual `vi.fn()` still behaves like `mockReset`.

Recommended baseline for any project (Vitest 4):

```ts
test: {
  mockReset: true,    // resets vi.fn/module mocks (history + implementation) each test
  restoreMocks: true, // un-spies vi.spyOn spies back to the original method
}
```

This makes every test start from clean mocks without per-file boilerplate, eliminating the most common class of order-dependent failures. Caveat from the docs: these auto-reset options can misbehave with `test.concurrent` (a reset can land mid-flight in a concurrently running test) — for concurrent suites, manage mock state per-test instead.
