/**
 * security-evals.test.ts — the drift gate the eval manifest's design assumes exists.
 *
 * `battery.ts` and `evals/README.md` both cite this file as the thing that fails when the lineup
 * stops describing the catalog. It had never been written, which is how the manifest came to name a
 * decoy from a retired plugin — a name that made `loadCandidates` throw, so the battery could not
 * run at all, silently, for as long as nobody ran it.
 *
 * Two asymmetric conditions, per the reasoning in `staleAcknowledgedOmissions`:
 *
 *   MISSING — a shipped skill in none of the manifest's four lists. A correctness problem: nobody
 *   can say what discrimination task the recorded rates describe. The two ways out are re-running
 *   the battery with the skill added to `decoys`, or adding it to `acknowledgedOmissions`.
 *
 *   STALE — a manifest entry naming no shipped skill. Hygiene for an omission, a hard break for a
 *   decoy: an omission merely records an exclusion that no longer exists, while a decoy is loaded
 *   into the lineup and throws when its description cannot be read.
 */

import { describe, expect, test } from 'bun:test';
import { join } from 'node:path';
import {
	loadCandidates,
	loadManifest,
	parseProbes,
	shippedSkills,
	staleAcknowledgedOmissions,
} from '../plugins/security/skills/reviewing-code-security/evals/battery.ts';

const EVALS = join(
	import.meta.dir,
	'..',
	'plugins/security/skills/reviewing-code-security/evals',
);

const manifest = await loadManifest(`${EVALS}/`);
const shipped = shippedSkills();
const probes = parseProbes(await Bun.file(join(EVALS, 'triggers.md')).text());

describe('the manifest describes the catalog', () => {
	test('every shipped skill appears in one of the four lists', () => {
		const listed = new Set([
			manifest.target,
			...manifest.decoys,
			...manifest.synthetic,
			...manifest.acknowledgedOmissions,
		]);
		const missing = shipped.filter((s) => !listed.has(s)).sort();
		expect(missing).toEqual([]);
	});

	test('no acknowledged omission names a skill that is gone', () => {
		expect(staleAcknowledgedOmissions(manifest)).toEqual([]);
	});

	test('every decoy names a skill this repository still ships', () => {
		const have = new Set(shipped);
		expect(manifest.decoys.filter((d) => !have.has(d)).sort()).toEqual([]);
	});

	test('the target is a shipped skill', () => {
		expect(shipped).toContain(manifest.target);
	});

	test('no name appears in two lists', () => {
		const all = [
			manifest.target,
			...manifest.decoys,
			...manifest.synthetic,
			...manifest.acknowledgedOmissions,
		];
		const dupes = all.filter((n, i) => all.indexOf(n) !== i).sort();
		expect(dupes).toEqual([]);
	});
});

describe('the lineup is loadable', () => {
	// The failure that motivated this file: a decoy resolving to no description file makes
	// loadCandidates throw, and nothing else in the repository would have noticed.
	test('every lineup name resolves to a description on disk', async () => {
		const candidates = await loadCandidates(manifest, `${EVALS}/`);
		expect(candidates.length).toBe(1 + manifest.decoys.length + manifest.synthetic.length);
		for (const c of candidates) {
			expect(c.description.length).toBeGreaterThan(0);
		}
	});

	test('acknowledged omissions stay out of the lineup', async () => {
		const candidates = await loadCandidates(manifest, `${EVALS}/`);
		const names = new Set(candidates.map((c) => c.name));
		expect(manifest.acknowledgedOmissions.filter((n) => names.has(n))).toEqual([]);
	});

	// Trial n places the target at index (5·(n−1)) mod lineup size. A size sharing a factor with 5
	// revisits a position inside the five-trial escalation, quietly measuring position bias instead
	// of averaging it out.
	test('the lineup size keeps five trials on five distinct positions', async () => {
		const { length } = await loadCandidates(manifest, `${EVALS}/`);
		const slots = [1, 2, 3, 4, 5].map((t) => (5 * (t - 1)) % length);
		expect(new Set(slots).size).toBe(5);
	});
});

describe('the probe battery', () => {
	// Ids are positional, so inserting or reordering a probe rebinds them and orphans every trial
	// already recorded against the old id. Pinning the counts makes such an edit visible.
	test('20 probes, 10 should-fire and 10 should-not-fire', () => {
		expect(probes.length).toBe(20);
		expect(probes.filter((p) => p.expectation === 'fire').length).toBe(10);
		expect(probes.filter((p) => p.expectation === 'nofire').length).toBe(10);
	});

	test('probe ids are unique and non-empty queries', () => {
		const ids = probes.map((p) => p.id);
		expect(new Set(ids).size).toBe(ids.length);
		for (const p of probes) expect(p.query.trim().length).toBeGreaterThan(0);
	});
});
