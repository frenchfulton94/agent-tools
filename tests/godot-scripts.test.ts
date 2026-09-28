/**
 * godot-scripts.test.ts — runs the godot plugin's FAST Python subset as part of `bun test`.
 *
 * The suite is split. This gate runs the parsers, the guard, the server's wiring and the
 * hook's logic — plus one real `--check-only` as a smoke check — and finishes in ~6s. The
 * tests that actually drive Godot run separately, via `bun run test:engine` (~23s).
 *
 * Why split: before this, the wrapped Python suite was ~38s of the catalog's ~40s `bun test`,
 * having grown from ~3s. A gate slow enough to avoid is a gate that gets avoided.
 *
 * What keeps the split honest, because moving 94% of a gate's runtime out of it is exactly
 * how a fast gate becomes no gate:
 *
 *   1. `bun test` still makes one real engine invocation (test_engine.TestEngineSmoke), so it
 *      cannot go green on a server that can no longer talk to Godot at all.
 *   2. The second test below asserts the gate is REAL — that engine tests are actually being
 *      skipped. Delete the decorators and the fast subset silently becomes the slow one; this
 *      notices.
 *   3. CLAUDE.md names `bun run test:engine` as required for commits touching plugins/godot.
 *
 * Skips cleanly when python3 is absent. The engine-gated tests skip themselves from inside
 * Python, so this stays green on a machine with no engine installed.
 */

import { describe, expect, test } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..');
const SCRIPTS = join(ROOT, 'plugins/godot/scripts');
const hasPython = spawnSync('python3', ['--version'], { encoding: 'utf8' }).status === 0;

/**
 * `-t .` matters: without an explicit top-level directory, discovery imports the suites as
 * top-level modules and every relative import of test/engine_gate.py fails with "attempted
 * relative import with no known parent package". Measured — it collected 76 of 205 and
 * reported 5 import errors.
 */
const DISCOVER = ['-m', 'unittest', 'discover', '-s', 'test', '-t', '.', '-p', 'test_*.py'];

/**
 * Memoized: both assertions below read the same run. Running it per test doubled the gate
 * (measured: 15.1s vs 8.9s) for two assertions about one piece of evidence.
 */
let cached: ReturnType<typeof spawnSync<string>> | undefined;
const runFast = () => {
	cached ??= spawnSync('python3', DISCOVER, {
		cwd: SCRIPTS,
		encoding: 'utf8',
		env: { ...process.env, GODOT_SKIP_ENGINE_TESTS: '1' },
	});
	return cached;
};

describe('godot python scripts (fast subset)', () => {
	// Generous ceiling, not a budget: the fast subset measures ~6s, of which ~3.5s is the
	// guard's per-case bash spawns and ~1.5s is engine.run's deliberate timeout tests against
	// a hung fake binary. Raise this rather than trim coverage.
	test.skipIf(!hasPython)(
		'fast suite passes',
		() => {
			const result = runFast();
			if (result.status !== 0) console.error(result.stderr || result.stdout);
			expect(result.status).toBe(0);
		},
		30000,
	);

	test.skipIf(!hasPython)(
		'the engine gate actually skips engine tests',
		() => {
			const out = runFast().stderr ?? '';
			// unittest prints "OK (skipped=N)" to stderr. A plain "OK" means nothing was
			// gated, so either the decorators are gone or GODOT_SKIP_ENGINE_TESTS stopped
			// being read — and this gate would be quietly running the full engine suite
			// while claiming to be the fast one.
			const skipped = Number(out.match(/OK \(skipped=(\d+)\)/)?.[1] ?? 0);
			// The threshold detects "nothing is gated at all", not a specific count —
			// pinning the exact number (33 today) would fail every time an engine test is
			// legitimately added or removed. test_invariants.py unit-tests the gate's own
			// logic; what THIS asserts is that the env var set above actually reaches
			// Python, which no Python-side test can check.
			expect(skipped).toBeGreaterThan(10);
		},
		30000,
	);
});
