import { describe, expect, test } from 'bun:test';
import { mkdirSync, mkdtempSync, realpathSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
// @ts-expect-error untyped .mjs module
import { verify } from '../plugins/workflows/scripts/verify.mjs';
// @ts-expect-error untyped .mjs module
import { hashTree } from '../plugins/workflows/scripts/lib/tree.mjs';

type Run = (cmd: string, args: string[], cwd?: string) => { status: number; stdout: string; stderr: string };
type Check = { name: string; ok: boolean; detail: string };

const ok = (stdout = '') => ({ status: 0, stdout, stderr: '' });
const PLUGIN = 'impeccable@impeccable';

/** A runner that answers the two openspec probe calls and returns `listing` for `claude plugin list --json`. */
const runner = (listing: unknown): Run => (cmd, args) => {
	if (cmd === 'claude') return ok(JSON.stringify(listing));
	if (args[0] === 'instructions') return ok(JSON.stringify({ context: 'ctx', rules: [] }));
	return ok();
};

const repo = () => mkdtempSync(join(tmpdir(), 'wf-verify-'));
const check = (r: { checks: Check[] }, name: string) => r.checks.find((c) => c.name.startsWith(name)) as Check;

/** The shape `claude plugin list --json` prints on Claude Code 2.1.311: machine-wide, one entry per installation. */
const entry = (o: Record<string, unknown>) => ({ id: PLUGIN, version: '4.10.0', scope: 'project', enabled: true, ...o });

describe('plugins installed (I5)', () => {
	const plugins = (root: string, listing: unknown) =>
		check(verify(root, { before: { specs: '', changes: '' }, expectPlugins: [PLUGIN], run: runner(listing) }), 'plugins installed');

	test('a project-scope entry for this repository passes', () => {
		const root = repo();
		expect(plugins(root, [entry({ projectPath: root })]).ok).toBe(true);
	});

	test("the same plugin installed in another repository does not satisfy this one", () => {
		const root = repo();
		const r = plugins(root, [entry({ projectPath: repo() })]);
		expect(r).toMatchObject({ ok: false, detail: `not installed: ${PLUGIN}` });
	});

	test('a symlinked spelling of the repository path still matches', () => {
		const root = repo();
		expect(plugins(root, [entry({ projectPath: realpathSync(root) })]).ok).toBe(true);
	});

	test('a user-scope entry applies everywhere', () => {
		expect(plugins(repo(), [entry({ scope: 'user' })]).ok).toBe(true);
	});

	test('a disabled entry is not installed', () => {
		const root = repo();
		expect(plugins(root, [entry({ projectPath: root, enabled: false })]).ok).toBe(false);
	});

	test('a listing that is not an array of entries fails rather than passing empty-handed', () => {
		expect(plugins(repo(), { plugins: [] }).ok).toBe(false);
	});
});

describe('openspec trees unchanged (I1)', () => {
	const trees = (root: string, before: { specs: string; changes: string }) =>
		verify(root, { before, run: runner([]) }).checks.filter((c: Check) => c.name.includes('(I1)'));

	test('a tree that did not exist before the run passes, and says init created it', () => {
		const root = repo();
		mkdirSync(join(root, 'openspec', 'specs'), { recursive: true });
		writeFileSync(join(root, 'openspec', 'specs', '.gitkeep'), '');
		const [specs, changes] = trees(root, { specs: '', changes: '' });
		expect(specs).toMatchObject({ ok: true, detail: 'did not exist before this run; created by openspec init' });
		expect(changes).toMatchObject({ ok: true, detail: '' });
	});

	test('a tree that existed and was modified fails', () => {
		const root = repo();
		mkdirSync(join(root, 'openspec', 'specs', 'auth'), { recursive: true });
		writeFileSync(join(root, 'openspec', 'specs', 'auth', 'spec.md'), 'before');
		const before = { specs: hashTree(join(root, 'openspec', 'specs')), changes: '' };
		writeFileSync(join(root, 'openspec', 'specs', 'auth', 'spec.md'), 'after');
		expect(trees(root, before)[0].ok).toBe(false);
	});

	test('a tree that existed and was left alone passes', () => {
		const root = repo();
		mkdirSync(join(root, 'openspec', 'specs', 'auth'), { recursive: true });
		writeFileSync(join(root, 'openspec', 'specs', 'auth', 'spec.md'), 'same');
		const before = { specs: hashTree(join(root, 'openspec', 'specs')), changes: '' };
		expect(trees(root, before)[0]).toMatchObject({ ok: true, detail: '' });
	});
});
