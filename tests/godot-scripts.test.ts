/**
 * godot-scripts.test.ts — runs the godot plugin's Python suite as part of `bun test`.
 *
 * The .tscn parser reads a user's scene files, and the guard decides whether a
 * destructive move reaches the shell. Both are gated here rather than run by hand:
 * a red Python suite fails the catalog suite. Skips cleanly when python3 is absent.
 *
 * Tests that need the Godot binary skip themselves from inside Python, so this
 * stays green on a machine with no engine installed.
 */

import { describe, expect, test } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..');
const hasPython = spawnSync('python3', ['--version'], { encoding: 'utf8' }).status === 0;

describe('godot python scripts', () => {
	// The engine wrapper's own tests spawn real subprocesses (including two
	// that enforce a Python-side timeout against a hung fake binary), so the
	// full suite runs well past bun's 5s default per-test timeout even
	// though nothing is actually stuck. Generous ceiling, not a real budget --
	// bumped from 30000 to 90000 when the GDScript check hook's suite grew
	// past 30s (measured at ~35.5s) after adding several tests that each run
	// a real `godot --check-only`/`--import` invocation; raise it again
	// rather than trim test coverage if a future round pushes past this.
	test.skipIf(!hasPython)(
		'unittest suite passes',
		() => {
			const result = spawnSync(
				'python3',
				['-m', 'unittest', 'discover', '-s', 'test', '-p', 'test_*.py'],
				{ cwd: join(ROOT, 'plugins/godot/scripts'), encoding: 'utf8' },
			);
			if (result.status !== 0) console.error(result.stderr || result.stdout);
			expect(result.status).toBe(0);
		},
		90000,
	);
});
