/**
 * Refreshes the vendored OWASP Cheat Sheet Series.
 *
 * Run by a maintainer in this repository; the output is committed. It is never run at plugin
 * install or review time — ${CLAUDE_PLUGIN_ROOT} is replaced on every update so nothing writable
 * belongs there, fetching at review time would make audits non-reproducible, and third-party
 * content entering a security tool needs a human to see the diff.
 *
 * Usage:
 *   bun sync-owasp.ts [--dry-run]
 *
 * Exit codes: 0 = clean, 1 = fetch or extract failed.
 */

import { createHash } from 'node:crypto';
import { existsSync, lstatSync, mkdirSync, readdirSync, rmSync } from 'node:fs';

export const REPO = 'OWASP/CheatSheetSeries';
export const REF = 'master';

export const CORPUS_DIR = new URL('../owasp/', import.meta.url).pathname;

/** True for a regular file. Guards the extraction loop against symlinks in the upstream archive. */
export const isCorpusFile = (path: string): boolean => lstatSync(path).isFile();

export interface SourceManifest {
	repo: string;
	ref: string;
	sha: string;
	syncedAt: string;
	sheetCount: number;
	stubs: string[];
}

/**
 * A redirect stub is a near-empty file whose only content points at another sheet. Length alone is
 * the reliable signal: several live sheets (Kubernetes, Node.js, CSP) contain the word "deprecated"
 * in their body, and a keyword match would wrongly discard ~900 lines of real guidance.
 */
export function isRedirectStub(text: string): boolean {
	const lines = text.trim().split('\n');
	if (lines.length >= 15) return false;
	return /\]\([A-Za-z0-9_-]*Cheat_?Sheet\.md/i.test(text);
}

/** The sheet a stub redirects to, or null when it names none. */
export function redirectTarget(text: string): string | null {
	const m = /\]\(([A-Za-z0-9_-]*Cheat_?Sheet\.md)/i.exec(text);
	return m?.[1] ?? null;
}

export function diffCorpus(
	before: Map<string, string>,
	after: Map<string, string>,
): { added: string[]; changed: string[]; removed: string[] } {
	const added: string[] = [];
	const changed: string[] = [];
	const removed: string[] = [];
	for (const [file, hash] of after) {
		const prior = before.get(file);
		if (prior === undefined) added.push(file);
		else if (prior !== hash) changed.push(file);
	}
	for (const file of before.keys()) if (!after.has(file)) removed.push(file);
	return { added: added.sort(), changed: changed.sort(), removed: removed.sort() };
}

const hash = (text: string): string => createHash('sha256').update(text).digest('hex');

/** Content hashes of the corpus as it stands on disk, for the before/after comparison. */
async function snapshot(dir: string): Promise<Map<string, string>> {
	if (!existsSync(dir)) return new Map();
	const out = new Map<string, string>();
	for (const file of readdirSync(dir).filter((f) => f.endsWith('_Cheat_Sheet.md'))) {
		out.set(file, hash(await Bun.file(`${dir}${file}`).text()));
	}
	return out;
}

/** Resolves the ref to a concrete commit, so the tarball and SOURCE.json cannot disagree. */
async function resolveSha(): Promise<string> {
	const res = await fetch(`https://api.github.com/repos/${REPO}/commits/${REF}`, {
		headers: { Accept: 'application/vnd.github.sha' },
	});
	if (!res.ok) throw new Error(`resolving ${REPO}@${REF} failed: ${res.status} ${res.statusText}`);
	const sha = (await res.text()).trim();
	// The response body is interpolated straight into a tarball URL and a filesystem path below.
	// Validate it here, at the source, rather than trusting an unexpected API response shape.
	if (!/^[0-9a-f]{40}$/.test(sha)) throw new Error(`resolving ${REPO}@${REF} returned a non-SHA value: ${sha}`);
	return sha;
}

async function main(): Promise<number> {
	const dryRun = Bun.argv.includes('--dry-run');
	const before = await snapshot(CORPUS_DIR);

	let sha: string;
	try {
		sha = await resolveSha();
	} catch (e) {
		console.error(`ERROR: ${(e as Error).message}`);
		return 1;
	}
	console.log(`upstream ${REPO}@${REF} is ${sha}`);

	const tmp = `${CORPUS_DIR}../.sync-tmp/`;
	rmSync(tmp, { recursive: true, force: true });
	mkdirSync(tmp, { recursive: true });

	// Everything below touches `tmp`. The `finally` is the one place that removes it, so every exit
	// from here on — a `return 1` on fetch/extract failure, an unanticipated thrown exception, the
	// `--dry-run` return, or the success path — cleans up through the same route.
	try {
		// One tarball request. The Contents API would need 120+ calls against a 60/hour anonymous limit.
		const tarball = `https://github.com/${REPO}/archive/${sha}.tar.gz`;
		const res = await fetch(tarball);
		if (!res.ok) {
			console.error(`ERROR: fetching ${tarball} failed: ${res.status} ${res.statusText}`);
			return 1;
		}
		await Bun.write(`${tmp}archive.tar.gz`, await res.arrayBuffer());

		// Extract to a temp dir, then copy only the sheets. Extracting with a glob directly is not
		// portable — macOS bsdtar and GNU tar disagree on pattern handling.
		const untar = Bun.spawnSync(['tar', '-xzf', 'archive.tar.gz'], { cwd: tmp });
		if (untar.exitCode !== 0) {
			console.error(`ERROR: tar failed: ${new TextDecoder().decode(untar.stderr)}`);
			return 1;
		}

		const srcDir = `${tmp}CheatSheetSeries-${sha}/cheatsheets/`;
		if (!existsSync(srcDir)) {
			console.error(`ERROR: ${srcDir} not found in the archive`);
			return 1;
		}

		const after = new Map<string, string>();
		const stubs: string[] = [];
		const staged = new Map<string, string>();
		for (const file of readdirSync(srcDir).filter((f) => f.endsWith('_Cheat_Sheet.md'))) {
			// tar sanitises member paths but not symlink targets. An upstream sheet that is a symlink
			// would be followed on read and its target's contents vendored into the corpus, then pushed
			// by the sync workflow's PR step. Only regular files are corpus content.
			if (!isCorpusFile(`${srcDir}${file}`)) continue;
			const text = await Bun.file(`${srcDir}${file}`).text();
			staged.set(file, text);
			after.set(file, hash(text));
			if (isRedirectStub(text)) stubs.push(file);
		}

		const delta = diffCorpus(before, after);
		for (const [label, files] of [
			['added', delta.added],
			['changed', delta.changed],
			['removed', delta.removed],
		] as const) {
			if (files.length > 0) console.log(`${label} (${files.length}): ${files.join(', ')}`);
		}
		if (delta.added.length + delta.changed.length + delta.removed.length === 0) {
			console.log('corpus is already current');
		}

		if (dryRun) {
			console.log('--dry-run: nothing written');
			return 0;
		}

		// Remove sheets that disappeared upstream, so the corpus never carries a file the index cannot
		// explain. NOTICE.md and SOURCE.json are not *_Cheat_Sheet.md and so are untouched.
		mkdirSync(CORPUS_DIR, { recursive: true });
		for (const file of delta.removed) rmSync(`${CORPUS_DIR}${file}`, { force: true });
		for (const [file, text] of staged) await Bun.write(`${CORPUS_DIR}${file}`, text);

		const manifest: SourceManifest = {
			repo: REPO,
			ref: REF,
			sha,
			syncedAt: new Date().toISOString(),
			sheetCount: staged.size,
			stubs: stubs.sort(),
		};
		await Bun.write(`${CORPUS_DIR}SOURCE.json`, `${JSON.stringify(manifest, null, 2)}\n`);

		console.log(`wrote ${staged.size} sheets (${stubs.length} redirect stubs) at ${sha.slice(0, 7)}`);
		console.log('next: bun scripts/build-index.ts');
		return 0;
	} finally {
		rmSync(tmp, { recursive: true, force: true });
	}
}

if (import.meta.main) process.exit(await main());
