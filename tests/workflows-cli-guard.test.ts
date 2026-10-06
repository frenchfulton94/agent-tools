import { describe, expect, test } from 'bun:test';
import { mkdirSync, mkdtempSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
// @ts-expect-error untyped .mjs module
import { isMain } from '../plugins/workflows/scripts/lib/cli.mjs';

const SCRIPTS = join(import.meta.dir, '..', 'plugins', 'workflows', 'scripts');
const GUARDED = ['config-facts', 'detect', 'install-plugins', 'plan', 'record', 'verify'];

/**
 * Setup's snippets import these modules through `node -e`, which puts the module's own path
 * at argv[1] — the same slot a direct `node <script>` run fills. The import must hand back
 * the exports without running the script's CLI.
 */
const IMPORT_ONLY = 'import(require("node:url").pathToFileURL(process.argv[1]).href).then(()=>console.log("imported"))';

const NODE = Bun.which('node');

/**
 * A scratch cwd and a PATH holding only `node`, so a CLI block that does run reaches no real
 * `openspec`, `claude`, or `bun`: verify's probe, install-plugins' installs, and detect's
 * version checks all fail fast with ENOENT instead of touching this machine.
 */
function sandbox(): { cwd: string; env: Record<string, string> } {
	const cwd = mkdtempSync(join(tmpdir(), 'wf-cli-guard-'));
	const bin = join(cwd, '.bin');
	mkdirSync(bin);
	symlinkSync(NODE as string, join(bin, 'node'));
	return { cwd, env: { PATH: bin, HOME: cwd } };
}

function node(args: string[]) {
	const { cwd, env } = sandbox();
	return spawnSync(NODE as string, [...args, cwd], { cwd, env, input: '', encoding: 'utf8' });
}

describe('isMain', () => {
	const script = join(SCRIPTS, 'plan.mjs');
	const url = pathToFileURL(script).href;
	const argv = ['/usr/bin/node', script, 'minimal'];

	test.each([
		[['-e', 'code']],
		[['-p', 'code']],
		[['-pe', 'code']],
		[['-ep', 'code']],
		[['--eval', 'code']],
		[['--eval=code']],
		[['--print', 'code']],
		[['--print=code']],
		[['--no-warnings', '--eval=code']],
	])('is false when node was started with %p', (execArgv) => {
		expect(isMain(url, { argv, execArgv })).toBe(false);
	});

	test.each([[[]], [['--no-warnings']], [['--env-file=.env']], [['-r', './hook.cjs']], [['--experimental-vm-modules']]])(
		'is true for node <script> started with %p',
		(execArgv) => {
			expect(isMain(url, { argv, execArgv })).toBe(true);
		},
	);

	test('is false when argv[1] is another module or absent', () => {
		expect(isMain(url, { argv: ['/usr/bin/node', join(SCRIPTS, 'detect.mjs')], execArgv: [] })).toBe(false);
		expect(isMain(url, { argv: ['/usr/bin/node'], execArgv: [] })).toBe(false);
	});
});

describe.each(GUARDED)('%s.mjs', (name) => {
	const script = join(SCRIPTS, `${name}.mjs`);

	test.each([
		['-e', ['-e', IMPORT_ONLY]],
		['--eval=<code>', [`--eval=${IMPORT_ONLY}`]],
		['--eval <code>', ['--eval', IMPORT_ONLY]],
	])('imported through node %s, its CLI does not run', (_form, flags) => {
		const r = node([...flags, script]);
		expect({ status: r.status, stdout: r.stdout.trim(), stderr: r.stderr.trim() }).toEqual({
			status: 0,
			stdout: 'imported',
			stderr: '',
		});
	});

	test('run as node <script>, its CLI still runs', () => {
		const r = node(['--no-warnings', script]);
		expect(`${r.stdout}${r.stderr}`.trim()).not.toBe('');
	});
});
