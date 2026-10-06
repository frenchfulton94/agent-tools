import { describe, expect, test } from 'bun:test';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
// @ts-expect-error untyped .mjs module
import { ownedFromPlan, recordRun } from '../plugins/workflows/scripts/record.mjs';

/** A repo whose record already claims `recorded`, with directories for `onDisk`. */
function repoWithRecord(
	recorded: { schemas?: Record<string, string>; agents?: Record<string, string> },
	onDisk: { schemas?: string[]; agents?: string[] },
): string {
	const root = mkdtempSync(join(tmpdir(), 'wf-record-'));
	mkdirSync(join(root, '.claude'), { recursive: true });
	writeFileSync(
		join(root, '.claude', 'workflows.json'),
		JSON.stringify({
			level: 'minimal',
			version: '0.7.0',
			date: '2026-01-01T00:00:00.000Z',
			installed: { schemas: recorded.schemas ?? {}, agents: recorded.agents ?? {} },
		}),
	);
	for (const name of onDisk.schemas ?? []) {
		mkdirSync(join(root, 'openspec', 'schemas', name), { recursive: true });
		writeFileSync(join(root, 'openspec', 'schemas', name, 'schema.yaml'), `name: ${name}\n`);
	}
	for (const file of onDisk.agents ?? []) {
		mkdirSync(join(root, '.claude', 'agents'), { recursive: true });
		writeFileSync(join(root, '.claude', 'agents', file), `# ${file}\n`);
	}
	return root;
}

const EMPTY_SIDE = { copy: [], update: [], collide: [] };

describe('retirement in the record', () => {
	test('a retired schema setup deleted leaves the record', () => {
		const root = repoWithRecord({ schemas: { 'mattpocock-bridge': 'h1' } }, { schemas: ['feature-flow'] });
		const { record } = recordRun(root, {
			level: 'minimal',
			schemas: ['feature-flow'],
			retired: { schemas: ['mattpocock-bridge'], agents: [] },
			date: '2026-10-06T00:00:00.000Z',
		});
		expect(Object.keys(record.installed.schemas)).toEqual(['feature-flow']);
	});

	test('a retired schema the user kept stays recorded as ours', () => {
		const root = repoWithRecord({ schemas: { 'mattpocock-bridge': 'h1' } }, { schemas: ['mattpocock-bridge'] });
		const { record } = recordRun(root, {
			level: 'minimal',
			schemas: [],
			retired: { schemas: ['mattpocock-bridge'], agents: [] },
			date: '2026-10-06T00:00:00.000Z',
		});
		expect(record.installed.schemas['mattpocock-bridge']).toBe('h1');
	});

	test("ownedFromPlan carries the plan's retire lists", () => {
		const plan = {
			level: 'minimal',
			schemas: EMPTY_SIDE,
			agents: EMPTY_SIDE,
			retire: {
				schemas: { retire: ['mattpocock-bridge'], keep: [] },
				agents: { retire: ['bridge-design-gate.md'], keep: [{ name: 'code-review-spec.md', reason: 'edited since this plugin installed it' }] },
			},
		};
		expect(ownedFromPlan(plan).retired).toEqual({ schemas: ['mattpocock-bridge'], agents: ['bridge-design-gate.md'] });
	});

	test('a plan from before retirement existed retires nothing', () => {
		expect(ownedFromPlan({ level: 'minimal', schemas: EMPTY_SIDE, agents: EMPTY_SIDE }).retired).toEqual({ schemas: [], agents: [] });
	});

	test('a retired agent setup deleted leaves the record', () => {
		const root = repoWithRecord(
			{ agents: { 'bridge-design-gate.md': 'a1', 'code-review-spec.md': 'a2' } },
			{ agents: ['code-review-spec.md'] },
		);
		const { record } = recordRun(root, {
			level: 'minimal',
			agents: [],
			retired: { schemas: [], agents: ['bridge-design-gate.md', 'code-review-spec.md'] },
			date: '2026-10-06T00:00:00.000Z',
		});
		expect(record.installed.agents['bridge-design-gate.md']).toBeUndefined();
		expect(record.installed.agents['code-review-spec.md']).toBe('a2');
	});

	test('the CLI wiring passes retired to recordRun', () => {
		const root = mkdtempSync(join(tmpdir(), 'wf-record-cli-'));
		mkdirSync(join(root, '.claude'), { recursive: true });
		writeFileSync(
			join(root, '.claude', 'workflows.json'),
			JSON.stringify({ level: 'minimal', version: '0.7.0', date: '2026-01-01T00:00:00.000Z', installed: { schemas: { 'mattpocock-bridge': 'h1' }, agents: {} } }),
		);
		// mattpocock-bridge is not on disk, so it should be dropped

		const scriptPath = join(dirname(fileURLToPath(import.meta.url)), '..', 'plugins', 'workflows', 'scripts', 'record.mjs');
		const plan = {
			level: 'minimal',
			schemas: { copy: [], update: [], collide: [] },
			agents: { copy: [], update: [], collide: [] },
			retire: {
				schemas: { retire: ['mattpocock-bridge'], keep: [] },
				agents: { retire: [], keep: [] },
			},
		};

		const result = spawnSync('node', [scriptPath, root], {
			input: JSON.stringify(plan),
			encoding: 'utf8',
		});

		expect(result.status).toBe(0);
		const output = JSON.parse(result.stdout);
		const persisted = JSON.parse(readFileSync(join(root, '.claude', 'workflows.json'), 'utf8'));
		expect(persisted.installed.schemas['mattpocock-bridge']).toBeUndefined();
	});
});
