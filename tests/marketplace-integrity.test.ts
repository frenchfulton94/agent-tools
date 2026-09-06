/**
 * marketplace-integrity.test.ts — the pinned contract for the catalog.
 *
 * These are the invariants that must never drift, and that no validator checks because each one
 * spans two or more files. The complement — the single-file lints, the plugin-level READMEs, the
 * marketplace-level schema — is covered by scripts/audit_marketplace.ts, which this suite does not
 * duplicate. Two implementations of one invariant disagree the next time either changes, and that
 * disagreement reads to a maintainer as noise from an unreliable tool.
 *
 * The one this suite exists for, above all: registration in both directions. A plugin directory
 * nobody registered is invisible to `/plugin marketplace add` — no error, it simply never appears.
 */

import { describe, expect, test } from 'bun:test';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..');
const PLUGINS_DIR = join(ROOT, 'plugins');

type MarketplaceEntry = {
	name: string;
	source: string;
	description?: string;
	category?: string;
};

type Marketplace = {
	name: string;
	owner?: { name?: string };
	plugins: MarketplaceEntry[];
	renames?: Record<string, string | null>;
};

type Manifest = {
	name: string;
	version: string;
	description?: string;
	displayName?: string;
};

const read = (path: string): string => readFileSync(path, 'utf8');
const readJson = <T>(path: string): T => JSON.parse(read(path)) as T;

const marketplace = readJson<Marketplace>(join(ROOT, '.claude-plugin', 'marketplace.json'));

/** Every directory under plugins/ that carries a manifest — the ground truth for what exists. */
const pluginDirs = readdirSync(PLUGINS_DIR, { withFileTypes: true })
	.filter((e) => e.isDirectory())
	.map((e) => e.name)
	.filter((name) => existsSync(join(PLUGINS_DIR, name, '.claude-plugin', 'plugin.json')))
	.sort();

const manifestOf = (dir: string): Manifest =>
	readJson<Manifest>(join(PLUGINS_DIR, dir, '.claude-plugin', 'plugin.json'));

/** Skill directories a plugin ships, by directory name. */
const skillsOf = (dir: string): string[] => {
	const skillsDir = join(PLUGINS_DIR, dir, 'skills');
	if (!existsSync(skillsDir)) return [];
	return readdirSync(skillsDir, { withFileTypes: true })
		.filter((e) => e.isDirectory())
		.map((e) => e.name)
		.sort();
};

/** Parse a SKILL.md's frontmatter `name`, tolerating folded (`>`) description blocks above it. */
const skillFrontmatter = (path: string): { name?: string; description?: string } => {
	const text = read(path);
	const match = text.match(/^---\n([\s\S]*?)\n---/);
	if (!match) return {};
	const body = match[1] as string;
	const name = body.match(/^name:\s*(.+)$/m)?.[1]?.trim();
	const description = body.match(/^description:\s*(.+)$/m)?.[1]?.trim();
	return { name, description };
};

describe('registration', () => {
	test('every plugin directory is registered in marketplace.json', () => {
		const registered = new Set(marketplace.plugins.map((p) => p.name));
		const unregistered = pluginDirs.filter((d) => !registered.has(d));
		expect(unregistered).toEqual([]);
	});

	test('every marketplace entry points at a directory that exists', () => {
		for (const entry of marketplace.plugins) {
			expect(entry.source).toStartWith('./');
			expect(entry.source).not.toInclude('../');
			const dir = join(ROOT, entry.source);
			expect(existsSync(join(dir, '.claude-plugin', 'plugin.json'))).toBe(true);
		}
	});

	test('marketplace.json has an owner', () => {
		expect(marketplace.owner?.name).toBeTruthy();
	});
});

describe('identity', () => {
	test.each(pluginDirs)('%s: manifest name matches its directory', (dir) => {
		expect(manifestOf(dir).name).toBe(dir);
	});

	test.each(pluginDirs)('%s: entry source matches its directory', (dir) => {
		const entry = marketplace.plugins.find((p) => p.name === dir);
		expect(entry?.source).toBe(`./plugins/${dir}`);
	});

	test('plugin names are unique across the catalog', () => {
		const names = marketplace.plugins.map((p) => p.name);
		expect(names.length).toBe(new Set(names).size);
	});
});

describe('descriptions agree', () => {
	// plugin.json and marketplace.json are both machine-read — the manifest describes the plugin
	// once installed, the entry describes it in the `/plugin` list before installing. A user who
	// reads one and gets the other is being told two different things about the same plugin.
	test.each(pluginDirs)('%s: manifest and marketplace entry carry the same description', (dir) => {
		const entry = marketplace.plugins.find((p) => p.name === dir);
		expect(entry?.description).toBe(manifestOf(dir).description);
	});
});

describe('versions', () => {
	test.each(pluginDirs)('%s: manifest declares a semver version', (dir) => {
		expect(manifestOf(dir).version).toMatch(/^\d+\.\d+\.\d+(-[\w.]+)?$/);
	});
});

describe('skills', () => {
	test.each(pluginDirs)('%s: every skill directory has a SKILL.md', (dir) => {
		for (const skill of skillsOf(dir)) {
			expect(existsSync(join(PLUGINS_DIR, dir, 'skills', skill, 'SKILL.md'))).toBe(true);
		}
	});

	test.each(pluginDirs)('%s: SKILL.md frontmatter name matches its directory', (dir) => {
		for (const skill of skillsOf(dir)) {
			const fm = skillFrontmatter(join(PLUGINS_DIR, dir, 'skills', skill, 'SKILL.md'));
			expect(fm.name).toBe(skill);
		}
	});

	// Two skills sharing a name is a routing defect the model resolves arbitrarily: the same
	// request fires a different body depending on load order, and the loser is undiagnosable.
	test('skill names are unique across every plugin', () => {
		const seen = new Map<string, string>();
		const collisions: string[] = [];
		for (const dir of pluginDirs) {
			for (const skill of skillsOf(dir)) {
				const prior = seen.get(skill);
				if (prior) collisions.push(`${skill}: ${prior} and ${dir}`);
				else seen.set(skill, dir);
			}
		}
		expect(collisions).toEqual([]);
	});
});

describe('README', () => {
	const readme = read(join(ROOT, 'README.md'));

	// The row shape the sweep's skills-column check parses. A table it cannot parse is a table
	// nothing checks, so the shape itself is pinned here.
	const rows = readme
		.split('\n')
		.map((line) => line.match(/^\|\s*\[([a-z0-9-]+)\]\(([^)]+)\)\s*\|([^|]*)\|/))
		.filter((m): m is RegExpMatchArray => m !== null);

	test('every plugin has a README row', () => {
		const listed = new Set(rows.map((m) => m[1] as string));
		expect(pluginDirs.filter((d) => !listed.has(d))).toEqual([]);
	});

	test('every README row links to a directory that exists', () => {
		for (const m of rows) {
			expect(existsSync(join(ROOT, m[2] as string))).toBe(true);
		}
	});
});

describe('renames', () => {
	const renames = marketplace.renames ?? {};

	test('no rename key collides with a live plugin name', () => {
		const live = new Set(marketplace.plugins.map((p) => p.name));
		expect(Object.keys(renames).filter((from) => live.has(from))).toEqual([]);
	});

	test('every rename resolves to a live plugin or to null', () => {
		const live = new Set(marketplace.plugins.map((p) => p.name));
		const unresolved: string[] = [];
		for (const from of Object.keys(renames)) {
			let cursor = renames[from];
			const seen = new Set<string>([from]);
			while (typeof cursor === 'string') {
				if (seen.has(cursor)) {
					unresolved.push(`${from} -> cycle at ${cursor}`);
					break;
				}
				seen.add(cursor);
				if (live.has(cursor)) break;
				if (!(cursor in renames)) {
					unresolved.push(`${from} -> ${cursor}, which is neither a plugin nor a rename`);
					break;
				}
				cursor = renames[cursor];
			}
		}
		expect(unresolved).toEqual([]);
	});
});
