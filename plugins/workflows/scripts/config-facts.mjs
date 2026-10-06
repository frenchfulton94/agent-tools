import { pathToFileURL } from 'node:url';
import { runCommand } from './lib/run.mjs';

/**
 * The design for `openspec/config.yaml`'s rewrite splits in two: the script supplies
 * facts, the agent supplies judgment (skills/setup/SKILL.md §5). This module is the
 * facts half — the one I4 ("nothing the user wrote is lost silently") needs code and a
 * test behind it, not just prose.
 */

/**
 * The `spec-driven` schema's artifact ids. Forced into the union unconditionally
 * (skills/setup/SKILL.md §5: "plus the built-in spec-driven ids"), since it is the
 * fallback schema for any change that names none, whether or not the CLI's own listing
 * happens to include it for this repo's schema set.
 */
export const BUILTIN_ARTIFACT_IDS = ['proposal', 'specs', 'design', 'tasks'];

/**
 * OpenSpec's real hard cap on the `context:` field, `MAX_CONTEXT_SIZE` in
 * `dist/core/project-config.js` (verified against the installed 1.11.0 CLI): exactly
 * `50 * 1024` bytes, compared with a strict `>` against `Buffer.byteLength(text, 'utf-8')`.
 * A field at exactly this size is kept; one byte over is dropped entirely and silently.
 */
export const CONTEXT_CAP_BYTES = 50 * 1024;

/**
 * The real subprocess runner: `runCommand` (lib/run.mjs) with the `cwd` this module's one
 * `openspec` call needs (the artifact-id union is a property of *that project's* schemas,
 * so the CLI has to run there). This was byte-identical to `verify.mjs`'s copy before the
 * shared runner existed. The contract it inherits — never throwing, surfacing
 * `spawnSync`'s `error`, telemetry opt-outs on every spawn, `WORKFLOWS_OPENSPEC`
 * resolution for the literal `openspec` command — is documented in lib/run.mjs.
 */
export function defaultRun(cmd, args, cwd) {
	return runCommand(cmd, args, { cwd });
}

/** First non-empty line of `stderr`, falling back to `stdout`, for a short failure message. */
function firstLine(result) {
	const text = (result.stderr || result.stdout || '').trim();
	return text.split('\n')[0] || 'no output';
}

/**
 * The authoritative set of artifact ids a project's installed schemas define, straight
 * from `openspec schemas --json` — never parsed out of schema YAML, which is not this
 * plugin's format to interpret and would drift the moment OpenSpec's own schema shape
 * changes. Runs with `repoRoot` as `cwd` so the CLI resolves that project's own
 * `openspec/schemas/` (a user's own schema affects the union, exactly like any shipped
 * one), and unions in `BUILTIN_ARTIFACT_IDS` unconditionally.
 *
 * On any failure to get a trustworthy answer — non-zero exit, unparseable stdout, valid
 * JSON that is not the documented bare array, or a runner that throws — this returns
 * `{ ok: false, ids: null, error }` rather than `{ ok: false, ids: new Set() }`. That
 * distinction is the whole point: a caller that skipped checking `ok` and used the ids
 * anyway gets a `null` it cannot silently treat as "no known ids", where an empty Set is
 * exactly that, and `classifyRules` would turn it into "every rule is unmatched" — the
 * silent-loss failure I4 exists to forbid. Callers MUST check `ok` before calling
 * `classifyRules` with `ids`.
 */
export function artifactIds(repoRoot, { run = defaultRun } = {}) {
	let result;
	try {
		result = run('openspec', ['schemas', '--json'], repoRoot);
	} catch (err) {
		return { ok: false, ids: null, error: `openspec schemas --json threw: ${err instanceof Error ? err.message : String(err)}` };
	}

	if (result.status !== 0) {
		return { ok: false, ids: null, error: `openspec schemas --json exited ${result.status}: ${firstLine(result)}` };
	}

	let schemas;
	try {
		schemas = JSON.parse(result.stdout);
	} catch (err) {
		return {
			ok: false,
			ids: null,
			error: `openspec schemas --json returned unparseable JSON: ${err instanceof Error ? err.message : String(err)}`,
		};
	}

	if (!Array.isArray(schemas)) {
		return { ok: false, ids: null, error: 'openspec schemas --json did not return the documented bare array' };
	}

	const ids = new Set(BUILTIN_ARTIFACT_IDS);
	for (const schema of schemas) {
		if (!schema || !Array.isArray(schema.artifacts)) continue;
		for (const id of schema.artifacts) if (typeof id === 'string') ids.add(id);
	}
	return { ok: true, ids, error: null };
}

/**
 * Per-process monotonic counter, used only to make `backupPath` collision-proof. A plain
 * millisecond timestamp is not enough on its own: two calls inside the same millisecond
 * (a real possibility — JS clock resolution is sometimes coarser than 1ms, and two
 * synchronous calls can land in the same tick regardless) would otherwise produce the
 * identical path, and the second `cpSync` would silently overwrite the first backup —
 * exactly the kind of silent loss I4 exists to forbid, just one step removed from the
 * config file itself. An incrementing integer cannot tie, no matter the clock.
 */
let backupSeq = 0;

/**
 * A timestamped backup path for `configPath`, guaranteed not to collide with a previous
 * call in this process — including two calls made back-to-back within the same
 * millisecond. The timestamp component is still millisecond-resolution and
 * human-sortable; the sequence suffix is what actually makes the guarantee hold.
 */
export function backupPath(configPath) {
	const stamp = new Date().toISOString().replace(/[:.]/g, '-');
	const seq = String(backupSeq++).padStart(6, '0');
	return `${configPath}.backup-${stamp}-${seq}`;
}

/**
 * Splits a project's already-parsed `rules:` map into `carried` (its artifact id is in
 * `knownIds`) and `unmatched` (it is not). `knownIds` must be the union `artifactIds()`
 * reports — every schema the chosen level installs, plus the built-ins — never just the
 * ids of the level's *default* schema. A rule keyed to `diagnose` is valid at `minimal`
 * because `bugfix-flow` defines it, even though that level's default schema is
 * `feature-flow`; testing membership against only the default schema's ids would
 * silently discard that rule as "unmatched".
 *
 * `knownIds` is required to be a real iterable (a `Set` or array of strings) — passing
 * `null`/`undefined` throws rather than being treated as an empty union. This is the
 * guard against the exact failure `artifactIds()` documents: a caller that forwards a
 * failed lookup's `ids: null` straight through here must get a loud crash, not a run
 * that quietly classifies every rule the user wrote as unmatched.
 */
export function classifyRules(userRules, knownIds) {
	if (knownIds == null || typeof knownIds[Symbol.iterator] !== 'function') {
		throw new TypeError(
			'classifyRules requires knownIds as a Set or array of artifact ids (e.g. artifactIds(...).ids on ' +
				'success) — refusing to guess. Passing a failed artifactIds() result through unchecked would ' +
				'silently classify every rule the user wrote as unmatched (I4).',
		);
	}
	const known = knownIds instanceof Set ? knownIds : new Set(knownIds);
	const carried = {};
	const unmatched = {};
	for (const [id, rules] of Object.entries(userRules ?? {})) {
		if (known.has(id)) carried[id] = rules;
		else unmatched[id] = rules;
	}
	return { carried, unmatched };
}

/**
 * Renders `classifyRules`'s `unmatched` map as a trailing YAML comment block, matching
 * the shape skills/setup/SKILL.md §5 documents. Every unmatched rule's original text is
 * preserved verbatim, JSON-encoded so it stays on one line — an unescaped literal newline
 * inside a rule's text would otherwise produce a line that does not start with `#`, which
 * a real YAML parser would then read as actual content instead of a comment, defeating
 * the entire reason this exists: keeping an unmatched id out from under `rules:`, where
 * OpenSpec would warn about it ("Unknown artifact ID in rules: X") on every command.
 * Returns `''` (no block at all) when there is nothing unmatched to carry.
 */
export function commentBlock(unmatched) {
	const ids = Object.keys(unmatched ?? {});
	if (ids.length === 0) return '';

	const lines = [
		'# Unmatched rules carried over from your previous config.yaml.',
		'# No installed schema defines these artifact ids, so they are kept here',
		'# rather than under `rules:`, where they would warn on every command.',
	];
	for (const id of ids) {
		lines.push(`#   ${id}:`);
		const rules = Array.isArray(unmatched[id]) ? unmatched[id] : unmatched[id] == null ? [] : [unmatched[id]];
		for (const rule of rules) lines.push(`#     - ${JSON.stringify(String(rule))}`);
	}
	return `${lines.join('\n')}\n`;
}

/**
 * Reports `text`'s size in bytes against OpenSpec's real `context:` cap. `context` is
 * dropped **entirely and silently** by OpenSpec past `CONTEXT_CAP_BYTES` (a
 * `console.warn` only, never a failure) — the single highest-consequence silent failure
 * this plugin can trigger, so the agent authoring `context:` prose needs this number
 * before it writes the file, not after a user notices the field is empty.
 */
export function contextSize(text) {
	const bytes = Buffer.byteLength(String(text ?? ''), 'utf8');
	return { bytes, capBytes: CONTEXT_CAP_BYTES, overCap: bytes > CONTEXT_CAP_BYTES };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
	const repoRoot = process.argv[2] ?? process.cwd();
	const result = artifactIds(repoRoot);
	console.log(JSON.stringify({ ...result, ids: result.ids ? [...result.ids].sort() : null }, null, 2));
	process.exit(result.ok ? 0 : 1);
}
