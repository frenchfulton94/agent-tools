# Vitest live-docs map

Every page on vitest.dev serves clean markdown when you append `.md` to the path. Fetch these instead of trusting memory whenever an API or config detail matters — this keeps the skill accurate as Vitest releases new versions.

**Master index (all pages):** https://vitest.dev/llms.txt
**Versioned docs** if the project pins an old major: replace the host, e.g. `https://v3.vitest.dev/guide/` (v0–v3 available). The `.md` trick works on the current site; for old versions fetch the HTML page.

## Contents

- Getting started & fundamentals
- API reference
- Mocking
- Config & environments
- Running, filtering, debugging
- Coverage & reporting
- Snapshots
- Browser mode & component testing
- Performance & advanced
- Migration

## Getting started & fundamentals

| Task                                          | URL                                                   |
| --------------------------------------------- | ----------------------------------------------------- |
| Install / first test / requirements           | https://vitest.dev/guide.md                           |
| Feature overview                              | https://vitest.dev/guide/features.md                  |
| Writing & organizing tests, test.for, globals | https://vitest.dev/guide/learn/writing-tests.md       |
| Matchers tutorial                             | https://vitest.dev/guide/learn/matchers.md            |
| Async testing patterns                        | https://vitest.dev/guide/learn/async.md               |
| Hooks & fixtures tutorial                     | https://vitest.dev/guide/learn/setup-teardown.md      |
| What to test / structuring suites             | https://vitest.dev/guide/learn/testing-in-practice.md |
| Debugging failing tests                       | https://vitest.dev/guide/learn/debugging-tests.md     |

## API reference

| Task                                                              | URL                                |
| ----------------------------------------------------------------- | ---------------------------------- |
| `test` / `it` modifiers (only, skip, todo, for, each, concurrent) | https://vitest.dev/api/test.md     |
| `describe`                                                        | https://vitest.dev/api/describe.md |
| Hooks (beforeEach, aroundEach, onTestFinished…)                   | https://vitest.dev/api/hooks.md    |
| Full `expect` matcher list                                        | https://vitest.dev/api/expect.md   |
| `vi` utility (all mock/timer/stub helpers)                        | https://vitest.dev/api/vi.md       |
| Mock instance API (mockReset, mock.calls…)                        | https://vitest.dev/api/mock.md     |

## Mocking

| Task                                                  | URL                                              |
| ----------------------------------------------------- | ------------------------------------------------ |
| Cheat sheet (start here)                              | https://vitest.dev/guide/mocking.md              |
| Mock functions tutorial                               | https://vitest.dev/guide/learn/mock-functions.md |
| Modules (vi.mock pitfalls, **mocks**, importOriginal) | https://vitest.dev/guide/mocking/modules.md      |
| Timers                                                | https://vitest.dev/guide/mocking/timers.md       |
| Dates                                                 | https://vitest.dev/guide/mocking/dates.md        |
| HTTP requests (msw setup)                             | https://vitest.dev/guide/mocking/requests.md     |
| File system                                           | https://vitest.dev/guide/mocking/file-system.md  |
| Globals / env                                         | https://vitest.dev/guide/mocking/globals.md      |
| Classes                                               | https://vitest.dev/guide/mocking/classes.md      |

## Config & environments

| Task                                            | URL                                                                                                                                      |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Full config reference                           | https://vitest.dev/config.md                                                                                                             |
| Single option (pattern)                         | https://vitest.dev/config/&lt;option&gt;.md — e.g. coverage, environment, setupfiles, globals, pool, restoremocks, testtimeout, projects |
| Test environments (node/jsdom/happy-dom)        | https://vitest.dev/guide/environment.md                                                                                                  |
| Monorepos / multiple configs                    | https://vitest.dev/guide/projects.md                                                                                                     |
| Test context & fixtures (test.extend)           | https://vitest.dev/guide/test-context.md                                                                                                 |
| Run lifecycle (setupFiles vs globalSetup order) | https://vitest.dev/guide/lifecycle.md                                                                                                    |

## Running, filtering, debugging

| Task                                          | URL                                       |
| --------------------------------------------- | ----------------------------------------- |
| CLI flags                                     | https://vitest.dev/guide/cli.md           |
| Filtering by name/file/line                   | https://vitest.dev/guide/filtering.md     |
| Test tags                                     | https://vitest.dev/guide/test-tags.md     |
| Parallelism / concurrency                     | https://vitest.dev/guide/parallelism.md   |
| Debugger / IDE                                | https://vitest.dev/guide/debugging.md     |
| Common errors (fetch on unexplained failures) | https://vitest.dev/guide/common-errors.md |

## Coverage & reporting

| Task                                    | URL                                   |
| --------------------------------------- | ------------------------------------- |
| Coverage setup, providers, thresholds   | https://vitest.dev/guide/coverage.md  |
| Coverage config options                 | https://vitest.dev/config/coverage.md |
| Reporters (junit, json, github-actions) | https://vitest.dev/guide/reporters.md |

## Snapshots

| Task                                       | URL                                         |
| ------------------------------------------ | ------------------------------------------- |
| Snapshot guide (file, inline, serializers) | https://vitest.dev/guide/snapshot.md        |
| Snapshot tutorial                          | https://vitest.dev/guide/learn/snapshots.md |

## Browser mode & component testing

| Task                                  | URL                                                                                                                                         |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Browser mode overview                 | https://vitest.dev/guide/browser.md                                                                                                         |
| Component testing (React/Vue/Svelte)  | https://vitest.dev/guide/browser/component-testing.md                                                                                       |
| Locators / interactivity / assertions | https://vitest.dev/api/browser/locators.md , https://vitest.dev/api/browser/interactivity.md , https://vitest.dev/api/browser/assertions.md |
| Visual regression                     | https://vitest.dev/guide/browser/visual-regression-testing.md                                                                               |

## Performance & advanced

| Task                                       | URL                                                    |
| ------------------------------------------ | ------------------------------------------------------ |
| Speeding up slow suites                    | https://vitest.dev/guide/improving-performance.md      |
| Profiling                                  | https://vitest.dev/guide/profiling-test-performance.md |
| Type testing (expectTypeOf)                | https://vitest.dev/guide/testing-types.md              |
| In-source testing                          | https://vitest.dev/guide/in-source.md                  |
| Custom matchers                            | https://vitest.dev/guide/extending-matchers.md         |
| Node API (running Vitest programmatically) | https://vitest.dev/guide/advanced.md                   |

## Migration

| Task                                       | URL                                   |
| ------------------------------------------ | ------------------------------------- |
| Jest → Vitest, and upgrading Vitest majors | https://vitest.dev/guide/migration.md |
