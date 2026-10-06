import { describe, expect, test } from 'bun:test';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
// @ts-expect-error untyped .mjs module
import { ownedFromPlan, recordRun } from '../plugins/workflows/scripts/record.mjs';

/** A repo whose record already claims `recorded`, with schema directories for `onDisk`. */
function repoWithRecord(recorded: Record<string, string>, onDisk: string[]): string {
	const root = mkdtempSync(join(tmpdir(), 'wf-record-'));
	mkdirSync(join(root, '.claude'), { recursive: true });
	writeFileSync(
		join(root, '.claude', 'workflows.json'),
		JSON.stringify({ level: 'minimal', version: '0.7.0', date: '2026-01-01T00:00:00.000Z', installed: { schemas: recorded, agents: {} } }),
	);
	for (const name of onDisk) {
		mkdirSync(join(root, 'openspec', 'schemas', name), { recursive: true });
		writeFileSync(join(root, 'openspec', 'schemas', name, 'schema.yaml'), `name: ${name}\n`);
	}
	return root;
}

const EMPTY_SIDE = { copy: [], update: [], collide: [] };

describe('retirement in the record', () => {
	test('a retired schema setup deleted leaves the record', () => {
		const root = repoWithRecord({ 'mattpocock-bridge': 'h1' }, ['feature-flow']);
		const { record } = recordRun(root, {
			level: 'minimal',
			schemas: ['feature-flow'],
			retired: { schemas: ['mattpocock-bridge'], agents: [] },
			date: '2026-10-06T00:00:00.000Z',
		});
		expect(Object.keys(record.installed.schemas)).toEqual(['feature-flow']);
	});

	test('a retired schema the user kept stays recorded as ours', () => {
		const root = repoWithRecord({ 'mattpocock-bridge': 'h1' }, ['mattpocock-bridge']);
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
});
