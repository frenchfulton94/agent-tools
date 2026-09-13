/**
 * vendored-skills.test.ts — the copies this repo uses on itself must equal what it ships.
 *
 * The catalog dogfoods its own skills: `skills-lock.json` names a source under `plugins/*​/skills/`
 * for each one, `.agents/skills/<name>/` holds a copy of it, and `.claude/skills/<name>` symlinks
 * into that copy. So the path an agent is handed when a skill fires — `.claude/skills/<name>/` — is
 * two hops from the file that actually ships, and an edit made there reaches no user.
 *
 * Nothing else catches that. audit_marketplace.ts walks the marketplace, which is `plugins/`; the
 * rest of this suite does too. Until this file existed the copies were in sync only because nobody
 * had edited one, and a one-sided edit would have failed silently in the direction that matters —
 * the maintainer sees their change take effect locally, and users never receive it.
 *
 * `computedHash` in the lock is not checked: the tool that writes it does not live in this repo, so
 * its digest is not ours to reproduce. Comparing the bytes tests the same invariant without
 * pinning someone else's algorithm.
 */

import { describe, expect, test } from 'bun:test';
import { existsSync, lstatSync, readdirSync, readFileSync, readlinkSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const ROOT = join(import.meta.dir, '..');
const VENDORED_DIR = join(ROOT, '.agents', 'skills');
const LINKED_DIR = join(ROOT, '.claude', 'skills');

type Lock = {
	version: number;
	skills: Record<string, { source: string; sourceType: string; computedHash?: string }>;
};

const lock = JSON.parse(readFileSync(join(ROOT, 'skills-lock.json'), 'utf8')) as Lock;
const lockedSkills = Object.keys(lock.skills).sort();

/** Every file under `dir`, as paths relative to it. Ignores the noise macOS leaves behind. */
const walk = (dir: string): string[] => {
	const out: string[] = [];
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		if (entry.name === '.DS_Store') continue;
		if (entry.isDirectory()) out.push(...walk(join(dir, entry.name)).map((p) => join(entry.name, p)));
		else out.push(entry.name);
	}
	return out.sort();
};

/** The shipping directory a vendored skill was copied from. */
const sourceOf = (name: string): string => join(ROOT, lock.skills[name]?.source ?? '', name);

const vendoredDirs = existsSync(VENDORED_DIR)
	? readdirSync(VENDORED_DIR, { withFileTypes: true })
			.filter((e) => e.isDirectory())
			.map((e) => e.name)
			.sort()
	: [];

describe('vendored skills are accounted for', () => {
	test('the lock and .agents/skills/ name the same skills', () => {
		expect(vendoredDirs).toEqual(lockedSkills);
	});

	test.each(lockedSkills)('%s: its locked source directory exists', (name) => {
		expect(lock.skills[name]?.sourceType).toBe('local');
		expect(existsSync(join(sourceOf(name), 'SKILL.md'))).toBe(true);
	});

	test.each(lockedSkills)('%s: the locked source is under plugins/', (name) => {
		expect(lock.skills[name]?.source).toStartWith('./plugins/');
	});
});

describe('vendored copies match their source', () => {
	// A skill edited under .agents/ or .claude/ works locally and ships nothing. Compare both the
	// file list and the bytes: a copy that merely gained a file is as stale as one that changed.
	test.each(lockedSkills)('%s: same files as plugins/', (name) => {
		const source = sourceOf(name);
		expect(walk(join(VENDORED_DIR, name))).toEqual(walk(source));
	});

	test.each(lockedSkills)('%s: same contents as plugins/', (name) => {
		const source = sourceOf(name);
		const differing = walk(source).filter((rel) => {
			const copy = join(VENDORED_DIR, name, rel);
			if (!existsSync(copy)) return true;
			return !readFileSync(join(source, rel)).equals(readFileSync(copy));
		});
		expect(differing).toEqual([]);
	});
});

describe('.claude/skills/ links into .agents/skills/', () => {
	test('every locked skill is linked', () => {
		const linked = readdirSync(LINKED_DIR).filter((n) => n !== '.DS_Store').sort();
		expect(linked).toEqual(lockedSkills);
	});

	test.each(lockedSkills)('%s: is a symlink to its vendored copy', (name) => {
		const link = join(LINKED_DIR, name);
		expect(lstatSync(link).isSymbolicLink()).toBe(true);
		expect(resolve(dirname(link), readlinkSync(link))).toBe(join(VENDORED_DIR, name));
	});
});
