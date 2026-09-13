import { cpSync, mkdirSync as mk, mkdtempSync as mkd, rmSync, writeFileSync as wf } from 'node:fs';
import { tmpdir as tmp } from 'node:os';
import { join as j } from 'node:path';
import { describe, expect, test } from 'bun:test';
// @ts-expect-error untyped .mjs module
import { buildPlan } from '../plugins/workflows/scripts/plan.mjs';
// @ts-expect-error untyped .mjs module
import { detect } from '../plugins/workflows/scripts/detect.mjs';

/** Minimal valid detection; override per test. Workflows include new/continue so no profile warning noise. */
export function makeDetection(overrides: Record<string, unknown> = {}) {
	return {
		repoRoot: '/tmp/fake',
		web: false,
		webSignals: [],
		apple: { app: false, swift: false, signals: [], xcodeMcpConfigured: false },
		openspec: { present: true, hasSpecs: false, hasChanges: false, schemas: [], schemaHashes: {}, configPath: null },
		agents: { files: [], hashes: {} },
		settings: { present: false, status: 'absent', decided: [] },
		runtime: { node: 'v0.0.0', bun: null },
		openspecCli: { version: null, profile: 'custom', workflows: ['propose', 'explore', 'apply', 'update', 'sync', 'archive', 'new', 'continue'] },
		humanArtifacts: { issueTracker: true, product: true, design: true, tools: false },
		priorRun: false,
		prior: null,
		...overrides,
	};
}

export const APPLE = { app: true, swift: true, signals: ['app:App.xcodeproj'], xcodeMcpConfigured: false };
export const SWIFT_ONLY = { app: false, swift: true, signals: ['swift:Package.swift'], xcodeMcpConfigured: false };

const PAYLOAD = j(import.meta.dir, '..', 'plugins', 'workflows', 'payload');

describe('tier-1 apple manifest', () => {
	test('a Swift signal installs apple-studio', () => {
		const plan = buildPlan(makeDetection({ apple: SWIFT_ONLY }), { level: 'minimal' });
		expect(plan.plugins.install).toContain('apple-studio@agent-tools');
		expect(plan.plugins.marketplaces.map((m: { name: string }) => m.name)).toContain('agent-tools');
	});

	test('no Swift signal, no apple-studio', () => {
		const plan = buildPlan(makeDetection(), { level: 'minimal' });
		expect(plan.plugins.install).not.toContain('apple-studio@agent-tools');
	});

	test('a decided apple-studio is skipped, never overridden (I3)', () => {
		const plan = buildPlan(
			makeDetection({ apple: SWIFT_ONLY, settings: { present: true, status: 'ok', decided: ['apple-studio@agent-tools'] } }),
			{ level: 'minimal' },
		);
		expect(plan.plugins.install).not.toContain('apple-studio@agent-tools');
		expect(plan.plugins.skip.map((s: { id: string }) => s.id)).toContain('apple-studio@agent-tools');
	});

	test('the plan carries the apple field', () => {
		const plan = buildPlan(makeDetection({ apple: APPLE }), { level: 'standard' });
		expect(plan.apple).toEqual({ app: true, swift: true });
	});

	test('a detection with no apple field (older build) degrades to false, not a crash', () => {
		const d = makeDetection();
		delete (d as Record<string, unknown>).apple;
		const plan = buildPlan(d, { level: 'minimal' });
		expect(plan.apple).toEqual({ app: false, swift: false });
	});
});

describe('advanced apple content composition', () => {
	test('advanced + app ships app-release and apple-design-gate', () => {
		const plan = buildPlan(makeDetection({ apple: APPLE }), { level: 'advanced' });
		expect(plan.schemas.copy).toContain('app-release');
		expect(plan.agents.copy).toContain('apple-design-gate.md');
	});

	test('advanced without app signal ships neither', () => {
		const plan = buildPlan(makeDetection({ apple: SWIFT_ONLY }), { level: 'advanced' });
		expect(plan.schemas.copy).not.toContain('app-release');
		expect(plan.agents.copy).not.toContain('apple-design-gate.md');
	});

	test('standard + app ships neither (advanced only)', () => {
		const plan = buildPlan(makeDetection({ apple: APPLE }), { level: 'standard' });
		expect(plan.schemas.copy).not.toContain('app-release');
	});

	test('a user-owned app-release schema collides, never silently replaced (I2)', () => {
		const plan = buildPlan(
			makeDetection({
				apple: APPLE,
				openspec: { present: true, hasSpecs: false, hasChanges: false, schemas: ['app-release'], schemaHashes: { 'app-release': 'abc' }, configPath: null },
			}),
			{ level: 'advanced' },
		);
		expect(plan.schemas.collide).toContain('app-release');
		expect(plan.schemas.copy).not.toContain('app-release');
	});

	test('missing apple subtree throws instead of shipping a silently thinner plan', () => {
		const stripped = mkd(j(tmp(), 'wf-payload-'));
		cpSync(PAYLOAD, stripped, { recursive: true });
		rmSync(j(stripped, 'levels', 'advanced', 'apple'), { recursive: true });
		expect(() => buildPlan(makeDetection({ apple: APPLE }), { level: 'advanced', payloadRoot: stripped })).toThrow(/apple/);
	});
});

describe('mcpbridge human step', () => {
	const stepText = (plan: { humanSteps: string[] }) => plan.humanSteps.join('\n');

	test('app repo without an xcode MCP server gets the step', () => {
		const plan = buildPlan(makeDetection({ apple: APPLE }), { level: 'minimal' });
		expect(stepText(plan)).toContain('xcrun mcpbridge');
	});

	test('already-configured xcode server suppresses it', () => {
		const plan = buildPlan(makeDetection({ apple: { ...APPLE, xcodeMcpConfigured: true } }), { level: 'minimal' });
		expect(stepText(plan)).not.toContain('mcpbridge');
	});

	test('tier-1-only repos do not get it', () => {
		const plan = buildPlan(makeDetection({ apple: SWIFT_ONLY }), { level: 'minimal' });
		expect(stepText(plan)).not.toContain('mcpbridge');
	});
});

describe('integration: detect → buildPlan on a real fixture (spec §12 e2e stand-in)', () => {
	test('an Apple app monorepo plans the full apple surface', () => {
		const root = mkd(j(tmp(), 'wf-fixture-'));
		mk(j(root, 'ios', 'App.xcodeproj'), { recursive: true });
		wf(j(root, 'Package.swift'), '// swift-tools-version:6.0');
		const d = detect(root, { run: () => null });
		const plan = buildPlan(d, { level: 'advanced' });
		expect(plan.apple).toEqual({ app: true, swift: true });
		expect(plan.plugins.install).toContain('apple-studio@agent-tools');
		expect(plan.schemas.copy).toContain('app-release');
		expect(plan.agents.copy).toContain('apple-design-gate.md');
		expect(plan.humanSteps.join('\n')).toContain('xcrun mcpbridge');
	});
});
