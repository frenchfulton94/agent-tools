/**
 * para-scripts.test.ts — runs the para plugin's Python suite as part of `bun test`.
 *
 * The para scripts move the user's files. Unlike the other plugin scripts in this
 * repo, whose tests are run by hand, these are gated: a red Python suite fails the
 * catalog suite. Skips cleanly when python3 is unavailable.
 */

import { describe, expect, test } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..');
const hasPython = spawnSync('python3', ['--version'], { encoding: 'utf8' }).status === 0;

describe('para python scripts', () => {
	test.skipIf(!hasPython)('unittest suite passes', () => {
		const result = spawnSync(
			'python3',
			['-m', 'unittest', 'discover', '-s', 'plugins/para/scripts/test', '-p', 'test_*.py'],
			{ cwd: ROOT, encoding: 'utf8' },
		);
		if (result.status !== 0) console.error(result.stderr || result.stdout);
		expect(result.status).toBe(0);
	});
});
