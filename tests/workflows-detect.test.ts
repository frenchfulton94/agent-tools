import { describe, expect, test } from 'bun:test';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
// @ts-expect-error untyped .mjs module
import { detect } from '../plugins/workflows/scripts/detect.mjs';

/** Never spawn during tests: openspec/bun version probes return "absent". */
const stubRun = () => null;

function repo(build: (root: string) => void = () => {}): string {
	const root = mkdtempSync(join(tmpdir(), 'wf-apple-'));
	build(root);
	return root;
}

const apple = (root: string) => detect(root, { run: stubRun }).apple;

describe('appleSignals', () => {
	test('empty repo has no apple signals', () => {
		expect(apple(repo())).toEqual({ app: false, swift: false, signals: [], xcodeMcpConfigured: false });
	});

	test('bare Package.swift is tier 1 only', () => {
		const a = apple(repo((r) => writeFileSync(join(r, 'Package.swift'), '// swift-tools-version:6.0')));
		expect(a.swift).toBe(true);
		expect(a.app).toBe(false);
		expect(a.signals).toEqual(['swift:Package.swift']);
	});

	test('a root .xcodeproj bundle is an app signal and implies tier 1', () => {
		const a = apple(repo((r) => mkdirSync(join(r, 'App.xcodeproj'))));
		expect(a.app).toBe(true);
		expect(a.swift).toBe(true);
		expect(a.signals).toEqual(['app:App.xcodeproj']);
	});

	test('an .xcodeproj one directory deep is found; two deep is not', () => {
		const a = apple(repo((r) => {
			mkdirSync(join(r, 'ios', 'App.xcodeproj'), { recursive: true });
			mkdirSync(join(r, 'apps', 'ios2', 'Deep.xcodeproj'), { recursive: true });
		}));
		expect(a.signals).toEqual(['app:ios/App.xcodeproj']);
	});

	test('node_modules and dot-directories are not scanned', () => {
		const a = apple(repo((r) => {
			mkdirSync(join(r, 'node_modules', 'Fake.xcodeproj'), { recursive: true });
			mkdirSync(join(r, '.build', 'Fake.xcodeproj'), { recursive: true });
		}));
		expect(a.signals).toEqual([]);
	});

	test('Tuist, Project.swift, project.yml, and .xcworkspace are app signals', () => {
		expect(apple(repo((r) => mkdirSync(join(r, 'Tuist')))).app).toBe(true);
		expect(apple(repo((r) => writeFileSync(join(r, 'Project.swift'), ''))).app).toBe(true);
		expect(apple(repo((r) => writeFileSync(join(r, 'project.yml'), 'name: App'))).app).toBe(true);
		expect(apple(repo((r) => mkdirSync(join(r, 'App.xcworkspace')))).app).toBe(true);
	});
});

describe('xcodeMcpConfigured', () => {
	test('absent .mcp.json reads as not configured', () => {
		expect(apple(repo()).xcodeMcpConfigured).toBe(false);
	});

	test('an xcode server in .mcp.json reads as configured', () => {
		const a = apple(repo((r) =>
			writeFileSync(join(r, '.mcp.json'), JSON.stringify({ mcpServers: { xcode: { command: 'xcrun' } } })),
		));
		expect(a.xcodeMcpConfigured).toBe(true);
	});

	test('unparseable .mcp.json reads as not configured, never crashes', () => {
		const a = apple(repo((r) => writeFileSync(join(r, '.mcp.json'), '{ nope,')));
		expect(a.xcodeMcpConfigured).toBe(false);
	});
});
