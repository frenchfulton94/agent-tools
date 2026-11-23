import { describe, expect, test } from 'bun:test';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
// @ts-expect-error untyped .mjs module
import { detect } from '../plugins/workflows/scripts/detect.mjs';

/** Never spawn during tests: openspec/bun version probes return "absent". */
const stubRun = () => null;

function repo(build: (root: string) => void = () => {}): string {
	const root = mkdtempSync(join(tmpdir(), 'wf-detect-'));
	build(root);
	return root;
}

describe('what detection no longer reports', () => {
	test('no web or apple fields, whatever the repository holds', () => {
		const root = repo((r) => {
			mkdirSync(join(r, 'App.xcodeproj'));
			writeFileSync(join(r, 'package.json'), JSON.stringify({ dependencies: { react: '19.0.0' } }));
		});
		const d = detect(root, { run: stubRun });
		expect(d).not.toHaveProperty('web');
		expect(d).not.toHaveProperty('apple');
	});

	test('human artifacts are the tracker doc and PRODUCT.md', () => {
		const root = repo((r) => writeFileSync(join(r, 'PRODUCT.md'), '# Product'));
		expect(detect(root, { run: stubRun }).humanArtifacts).toEqual({ issueTracker: false, product: true });
	});
});

describe('open change schemas', () => {
	const changeSchemas = (root: string) => detect(root, { run: stubRun }).openspec.changeSchemas;
	const change = (root: string, name: string, body?: string) => {
		mkdirSync(join(root, 'openspec', 'changes', name), { recursive: true });
		if (body !== undefined) writeFileSync(join(root, 'openspec', 'changes', name, '.openspec.yaml'), body);
	};

	test('no changes directory means no entries', () => {
		expect(changeSchemas(repo())).toEqual({});
	});

	test("reads each open change's schema, quoted or not", () => {
		const root = repo((r) => {
			change(r, 'add-a', 'schema: feature-flow\ncreated: 2026-10-06\n');
			change(r, 'fix-b', "schema: 'bugfix-flow' # chosen by the router\n");
			change(r, 'old-c', 'created: 2026-09-01\nschema: "mattpocock-bridge"\n');
		});
		expect(changeSchemas(root)).toEqual({ 'add-a': 'feature-flow', 'fix-b': 'bugfix-flow', 'old-c': 'mattpocock-bridge' });
	});

	test('a change with no .openspec.yaml, or no schema line, names null', () => {
		const root = repo((r) => {
			change(r, 'bare');
			change(r, 'no-line', 'created: 2026-10-06\n');
		});
		expect(changeSchemas(root)).toEqual({ bare: null, 'no-line': null });
	});

	test('a valueless schema: line names null', () => {
		const root = repo((r) => {
			change(r, 'schema-newline', 'schema:\ncreated: 2026-10-06\n');
			change(r, 'schema-tilde', 'schema: ~\n');
			change(r, 'schema-null', 'schema: null\n');
		});
		expect(changeSchemas(root)).toEqual({ 'schema-newline': null, 'schema-tilde': null, 'schema-null': null });
	});

	test('archived changes are not open', () => {
		const root = repo((r) => {
			change(r, join('archive', '2026-01-01-old'), 'schema: mattpocock-bridge\n');
			change(r, 'add-a', 'schema: feature-flow\n');
		});
		expect(changeSchemas(root)).toEqual({ 'add-a': 'feature-flow' });
	});
});
