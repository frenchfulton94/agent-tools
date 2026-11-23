import { cpSync, mkdirSync as mk, mkdtempSync as mkd, rmSync, writeFileSync as wf } from 'node:fs';
import { tmpdir as tmp } from 'node:os';
import { join as j } from 'node:path';
import { describe, expect, test } from 'bun:test';
// @ts-expect-error untyped .mjs module
import { buildPlan } from '../plugins/workflows/scripts/plan.mjs';
// @ts-expect-error untyped .mjs module
import { detect } from '../plugins/workflows/scripts/detect.mjs';
// @ts-expect-error untyped .mjs module
import { recordRun } from '../plugins/workflows/scripts/record.mjs';

/** Minimal valid detection; override per test. Workflows include new/continue so no profile warning noise. */
export function makeDetection(overrides: Record<string, unknown> = {}) {
	return {
		repoRoot: '/tmp/fake',
		openspec: { present: true, hasSpecs: false, hasChanges: false, schemas: [], schemaHashes: {}, configPath: null },
		agents: { files: [], hashes: {} },
		settings: { present: false, status: 'absent', decided: [] },
		runtime: { node: 'v0.0.0', bun: null },
		openspecCli: { version: null, profile: 'custom', workflows: ['propose', 'explore', 'apply', 'update', 'sync', 'archive', 'new', 'continue'] },
		humanArtifacts: { issueTracker: true, product: true },
		priorRun: false,
		prior: null,
		...overrides,
	};
}

const PAYLOAD = j(import.meta.dir, '..', 'plugins', 'workflows', 'payload');

describe('the one workflow', () => {
	test('a fresh repo copies the seven flows and the design agent', () => {
		const plan = buildPlan(makeDetection());
		expect(plan.level).toBe('minimal');
		expect(plan.schemas.copy).toEqual([
			'bugfix-flow', 'feature-flow', 'rapid-flow', 'refactor-flow', 'setup-flow', 'spike-flow', 'upgrade-flow',
		]);
		expect(plan.agents.copy).toEqual(['flow-design.md']);
	});

	test('installs exactly the plugins the flows call, and only their marketplaces', () => {
		const plan = buildPlan(makeDetection());
		expect(plan.plugins.install).toEqual([
			'agent-skills@addy-agent-skills',
			'impeccable@impeccable',
			'mattpocock-skills@claude-plugins-official',
		]);
		expect(plan.plugins.marketplaces.map((m: { name: string }) => m.name).sort()).toEqual(['addy-agent-skills', 'impeccable']);
	});

	test('a decided plugin is skipped, never overridden (I3)', () => {
		const plan = buildPlan(makeDetection({ settings: { present: true, status: 'ok', decided: ['impeccable@impeccable'] } }));
		expect(plan.plugins.install).not.toContain('impeccable@impeccable');
		expect(plan.plugins.skip.map((s: { id: string }) => s.id)).toEqual(['impeccable@impeccable']);
		expect(plan.plugins.marketplaces.map((m: { name: string }) => m.name)).toEqual(['addy-agent-skills']);
	});

	test('a detection carrying fields from an older build (web, apple) is ignored, not a crash', () => {
		const plan = buildPlan(makeDetection({ web: true, apple: { app: true, swift: true } }));
		expect(plan).not.toHaveProperty('web');
		expect(plan).not.toHaveProperty('apple');
		expect(plan.plugins.install).toHaveLength(3);
	});

	test('a payload with no schemas throws instead of building an empty plan', () => {
		const empty = mkd(j(tmp(), 'wf-payload-'));
		expect(() => buildPlan(makeDetection(), { payloadRoot: empty })).toThrow(/openspec\/schemas/);
	});

	test('a payload missing its agents still plans the schemas', () => {
		const stripped = mkd(j(tmp(), 'wf-payload-'));
		cpSync(PAYLOAD, stripped, { recursive: true });
		rmSync(j(stripped, 'agents'), { recursive: true });
		expect(buildPlan(makeDetection(), { payloadRoot: stripped }).agents.copy).toEqual([]);
	});
});

describe('human steps', () => {
	const steps = (o: Record<string, unknown>) => buildPlan(makeDetection(o)).humanSteps.join('\n');

	test('a repo with the tracker doc and PRODUCT.md gets only the reload', () => {
		expect(buildPlan(makeDetection()).humanSteps).toHaveLength(1);
		expect(steps({})).toContain('/reload-plugins');
	});

	test('a missing tracker doc asks for the Pocock setup interview', () => {
		expect(steps({ humanArtifacts: { issueTracker: false, product: true } })).toContain('setup-matt-pocock-skills');
	});

	test('a missing PRODUCT.md offers impeccable init, for projects with a user interface', () => {
		expect(steps({ humanArtifacts: { issueTracker: true, product: false } })).toContain('/impeccable init');
	});
});

describe('a repository set up at a removed level', () => {
	const at = (level: string | null) =>
		buildPlan(makeDetection({ priorRun: true, prior: { level, schemas: {}, agents: {} } })).warnings.join('\n');

	test.each(['standard', 'advanced'])('%s is named in a warning', (level) => {
		expect(at(level)).toContain(`set up at the \`${level}\` level`);
	});

	test('minimal, and a record with no level, warn about nothing', () => {
		expect(at('minimal')).toBe('');
		expect(at(null)).toBe('');
	});

	test("an advanced schema this plugin installed and nobody edited is offered for retirement, with its agents", () => {
		const plan = buildPlan(
			makeDetection({
				openspec: {
					present: true, hasSpecs: false, hasChanges: false, configPath: null, changeSchemas: {},
					schemas: ['feature', 'hotfix'],
					schemaHashes: { feature: 'f1', hotfix: 'edited' },
				},
				agents: { files: ['design-gate.md'], hashes: { 'design-gate.md': 'g1' } },
				priorRun: true,
				prior: { level: 'advanced', schemas: { feature: 'f1', hotfix: 'h1' }, agents: { 'design-gate.md': 'g1' } },
			}),
		);
		expect(plan.retire.schemas.retire).toEqual(['feature']);
		expect(plan.retire.schemas.keep).toEqual([{ name: 'hotfix', reason: 'edited since this plugin installed it' }]);
		expect(plan.retire.agents.keep).toEqual([{ name: 'design-gate.md', reason: 'a retired schema it serves is being kept' }]);
	});

	test("a user's own schema that shares a removed name is kept", () => {
		const plan = buildPlan(
			makeDetection({
				openspec: { present: true, hasSpecs: false, hasChanges: false, configPath: null, changeSchemas: {}, schemas: ['feature'], schemaHashes: { feature: 'x' } },
			}),
		);
		expect(plan.retire.schemas).toEqual({ retire: [], keep: [{ name: 'feature', reason: 'not installed by this plugin' }] });
	});
});

describe('retirement', () => {
	const RETIRED_AGENTS = ['bridge-design-gate.md', 'code-review-spec.md', 'code-review-standards.md'];
	const ourAgents = Object.fromEntries(RETIRED_AGENTS.map((a) => [a, 'a1']));
	const onDisk = (o: { schemaHash?: string; recorded?: boolean; changes?: Record<string, string | null> | null } = {}) =>
		makeDetection({
			openspec: {
				present: true,
				hasSpecs: false,
				hasChanges: false,
				schemas: ['mattpocock-bridge'],
				schemaHashes: { 'mattpocock-bridge': o.schemaHash ?? 'h1' },
				configPath: null,
				...(o.changes === null ? {} : { changeSchemas: o.changes ?? {} }),
			},
			agents: { files: RETIRED_AGENTS, hashes: ourAgents },
			priorRun: true,
			prior: o.recorded === false ? { schemas: {}, agents: {} } : { schemas: { 'mattpocock-bridge': 'h1' }, agents: ourAgents },
		});
	const keptFor = (reason: string) => RETIRED_AGENTS.map((name) => ({ name, reason }));

	test('recorded, untouched, and unused: the schema and its agents retire', () => {
		const plan = buildPlan(onDisk());
		expect(plan.retire.schemas).toEqual({ retire: ['mattpocock-bridge'], keep: [] });
		expect(plan.retire.agents).toEqual({ retire: RETIRED_AGENTS, keep: [] });
	});

	test('edited since install: kept, and its agents with it', () => {
		const plan = buildPlan(onDisk({ schemaHash: 'h2' }));
		expect(plan.retire.schemas).toEqual({
			retire: [],
			keep: [{ name: 'mattpocock-bridge', reason: 'edited since this plugin installed it' }],
		});
		expect(plan.retire.agents).toEqual({ retire: [], keep: keptFor('a retired schema it serves is being kept') });
	});

	test("never recorded: kept as the user's own", () => {
		const plan = buildPlan(onDisk({ recorded: false }));
		expect(plan.retire.schemas.keep).toEqual([{ name: 'mattpocock-bridge', reason: 'not installed by this plugin' }]);
		expect(plan.retire.agents.keep).toEqual(keptFor('not installed by this plugin'));
	});

	test('an open change uses it: kept', () => {
		const plan = buildPlan(onDisk({ changes: { 'add-x': 'mattpocock-bridge' } }));
		expect(plan.retire.schemas.keep).toEqual([{ name: 'mattpocock-bridge', reason: 'an open change uses it' }]);
	});

	test('an open change naming no schema keeps it', () => {
		const plan = buildPlan(onDisk({ changes: { 'add-x': null } }));
		expect(plan.retire.schemas.keep).toEqual([
			{ name: 'mattpocock-bridge', reason: 'an open change names no schema, so it may use this one' },
		]);
	});

	test('a detection without changeSchemas keeps retired schemas', () => {
		const plan = buildPlan(onDisk({ changes: null }));
		expect(plan.retire.schemas.keep).toEqual([
			{ name: 'mattpocock-bridge', reason: 'open changes were not checked, so one may use it' },
		]);
	});

	test('an open change on another schema does not block', () => {
		const plan = buildPlan(onDisk({ changes: { 'add-x': 'feature-flow' } }));
		expect(plan.retire.schemas.retire).toEqual(['mattpocock-bridge']);
	});

	test('a retired name not on disk is not mentioned', () => {
		const plan = buildPlan(makeDetection());
		expect(plan.retire).toEqual({ schemas: { retire: [], keep: [] }, agents: { retire: [], keep: [] } });
	});

	test('integration: a recorded retired schema an open change uses is kept', () => {
		const root = mkd(j(tmp(), 'wf-retire-'));
		mk(j(root, 'openspec', 'schemas', 'mattpocock-bridge'), { recursive: true });
		wf(j(root, 'openspec', 'schemas', 'mattpocock-bridge', 'schema.yaml'), 'name: mattpocock-bridge\n');
		recordRun(root, { level: 'minimal', schemas: ['mattpocock-bridge'], date: '2026-10-06T00:00:00.000Z' });
		mk(j(root, 'openspec', 'changes', 'add-x'), { recursive: true });
		wf(j(root, 'openspec', 'changes', 'add-x', '.openspec.yaml'), 'schema: mattpocock-bridge\n');
		const plan = buildPlan(detect(root, { run: () => null }));
		expect(plan.retire.schemas).toEqual({ retire: [], keep: [{ name: 'mattpocock-bridge', reason: 'an open change uses it' }] });
	});
});
