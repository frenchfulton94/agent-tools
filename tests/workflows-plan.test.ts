import { describe, expect, test } from 'bun:test';
// @ts-expect-error untyped .mjs module
import { buildPlan } from '../plugins/workflows/scripts/plan.mjs';

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

const APPLE = { app: true, swift: true, signals: ['app:App.xcodeproj'], xcodeMcpConfigured: false };
const SWIFT_ONLY = { app: false, swift: true, signals: ['swift:Package.swift'], xcodeMcpConfigured: false };

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
