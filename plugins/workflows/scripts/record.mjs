import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { hashEntry } from './lib/tree.mjs';

/**
 * `.claude/workflows.json` — what a previous run of this plugin installed into this repo.
 *
 * Without it, "re-running is how you take updates" is false. `copyAdditive` skips anything
 * already present, so on a second run every schema the first run copied looks exactly like
 * a schema the user wrote by hand: both are "a directory that already exists under that
 * name", and setup either has to skip it (never updating) or replace it (destroying the
 * user's work). The record breaks the tie by remembering, per name, the hash of the
 * content *we* wrote. On a re-run:
 *
 * - name recorded, on-disk hash still matches → ours, untouched since we wrote it → safe
 *   to update to the version this plugin now ships;
 * - name recorded, hash differs → the user edited our copy → report it, never replace it;
 * - name not recorded → the user's own file → report it, never replace it.
 *
 * The hash is of what we wrote, not of what we currently ship, which is the whole point:
 * it is what makes "unchanged since the last run" answerable across plugin versions, when
 * the shipped content itself has moved on.
 */

const HERE = dirname(fileURLToPath(import.meta.url));

/** Where a repo's record lives. One place, so detection and recording cannot disagree. */
export function recordPath(repoRoot) {
	return join(repoRoot, '.claude', 'workflows.json');
}

/** Where an installed schema lives, by name. */
export function schemaPath(repoRoot, name) {
	return join(repoRoot, 'openspec', 'schemas', name);
}

/** Where an installed subagent lives, by filename. */
export function agentPath(repoRoot, file) {
	return join(repoRoot, '.claude', 'agents', file);
}

/**
 * This plugin's own version, from its manifest. Recorded alongside the hashes so a reader
 * (or a future migration) can tell which version's content a hash belongs to. Returns
 * `null` rather than throwing if the manifest is somehow unreadable: a missing version is
 * a worse report, not a reason to fail a run that otherwise succeeded.
 */
export function pluginVersion() {
	try {
		return JSON.parse(readFileSync(join(HERE, '..', '.claude-plugin', 'plugin.json'), 'utf8')).version ?? null;
	} catch {
		return null;
	}
}

/** Only string→string entries survive; anything else in a hand-edited file is ignored. */
function stringMap(value) {
	const out = {};
	for (const [k, v] of Object.entries(value ?? {})) if (typeof v === 'string') out[k] = v;
	return out;
}

/**
 * The record, or `null` when there is none we can trust — absent, unparseable, or not an
 * object. `null` is deliberately not "an empty record": it means every existing file is
 * treated as the user's own, which is the conservative answer. A record written by an
 * older version of this plugin (level and version only, no `installed` block) reads back
 * as empty maps and behaves the same way — nothing is claimed as ours that we cannot
 * prove we wrote.
 */
export function readRecord(repoRoot) {
	const path = recordPath(repoRoot);
	if (!existsSync(path)) return null;
	let parsed;
	try {
		parsed = JSON.parse(readFileSync(path, 'utf8'));
	} catch {
		return null;
	}
	if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return null;
	return {
		level: typeof parsed.level === 'string' ? parsed.level : null,
		version: typeof parsed.version === 'string' ? parsed.version : null,
		date: typeof parsed.date === 'string' ? parsed.date : null,
		schemas: stringMap(parsed.installed?.schemas),
		agents: stringMap(parsed.installed?.agents),
	};
}

/**
 * Writes the record for a completed apply. `schemas` and `agents` are the names this run
 * owns — the ones it copied, the ones it updated, and any collision the user explicitly
 * approved replacing — never a name left as the user had it. Each is hashed **from disk**,
 * after the copy, so the record holds exactly the bytes a later run will compare against;
 * a name that is not on disk is dropped from the record rather than recorded with an empty
 * hash, because a hash that matches nothing would claim ownership of whatever appears at
 * that name later.
 */
export function recordRun(repoRoot, { level, schemas = [], agents = [], version = pluginVersion(), date = new Date() } = {}) {
	const prior = readRecord(repoRoot);

	/**
	 * Merged, never replaced. The three levels ship disjoint schema and agent sets, so a
	 * wholesale write meant `minimal` → `advanced` dropped every `minimal` entry, and going
	 * back reported five files this plugin had written as the user's own — a plan that says
	 * "yours, or ours you have edited" about files nobody ever touched. Keeping entries for
	 * levels the user has left is correct rather than a leak: those files are still on disk
	 * and still ours, so returning to that level updates them. An entry whose file has since
	 * been deleted is inert, because `classify` (plan.mjs) requires the name in *detection's*
	 * hashes before it can promote anything — a record alone never claims a file.
	 */
	const merged = (previous, names, toPath) => {
		const out = { ...previous };
		for (const name of [...names].sort()) {
			const hash = hashEntry(toPath(repoRoot, name));
			if (hash) out[name] = hash;
		}
		return Object.fromEntries(Object.entries(out).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)));
	};

	const record = {
		level,
		version,
		date: date instanceof Date ? date.toISOString() : String(date),
		installed: {
			schemas: merged(prior?.schemas, schemas, schemaPath),
			agents: merged(prior?.agents, agents, agentPath),
		},
	};

	const path = recordPath(repoRoot);
	mkdirSync(dirname(path), { recursive: true });
	writeFileSync(path, `${JSON.stringify(record, null, 2)}\n`);
	return { path, record };
}

/**
 * Derives what a run owns **from the approved plan**, not from a caller's list.
 *
 * This is the difference between a record that states a fact and one that grants ownership
 * on request. `recordRun` hashes whatever names it is handed, so a step-9 argument that
 * wrongly included a collision the user *declined* would make that file ours permanently,
 * and the next run would replace it with no gate and no mention — the one thing this model
 * must never do. The plan already knows what was copied and what was updated, and the only
 * thing it cannot know is which collisions the user approved at the gate, because approval
 * happens after the plan is built.
 *
 * So `approved` is the sole caller-supplied input, and it is checked rather than trusted: a
 * name is honoured only if the plan itself listed it as a collision. Anything else comes
 * back in `ignored` — reported, and recorded for nothing. What this cannot detect is a name
 * that really is a collision but which the user declined; that is inherent to approval
 * living outside the plan, and it is why the skill says never to pass one.
 */
export function ownedFromPlan(plan, approved = []) {
	const entries = (side) => {
		const e = plan?.[side];
		if (!e || !Array.isArray(e.copy) || !Array.isArray(e.update) || !Array.isArray(e.collide)) {
			throw new TypeError(
				`plan.${side} must have copy/update/collide arrays — refusing to record against something that is not a plan. ` +
					'Pipe the approved plan JSON (plan.mjs output) on stdin.',
			);
		}
		return e;
	};

	const schemas = entries('schemas');
	const agents = entries('agents');
	const approvedIn = (side) => approved.filter((name) => side.collide.includes(name));
	const schemaApproved = approvedIn(schemas);
	const agentApproved = approvedIn(agents);
	const honoured = new Set([...schemaApproved, ...agentApproved]);

	return {
		level: plan.level,
		schemas: [...schemas.copy, ...schemas.update, ...schemaApproved],
		agents: [...agents.copy, ...agents.update, ...agentApproved],
		ignored: approved.filter((name) => !honoured.has(name)),
	};
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
	// The plan arrives on stdin, exactly as `install-plugins.mjs` takes it. Nothing in argv
	// parses JSON any more: the old two-slot form died on `""` — a legitimately empty shell
	// variable meaning "nothing owned" — because a default only fires on `undefined`, and it
	// died on a space-separated list too. Approved collision names are plain words.
	const repoRoot = process.argv[2] || process.cwd();
	const approved = process.argv.slice(3).filter((a) => a.length > 0);
	try {
		const plan = JSON.parse(readFileSync(0, 'utf8'));
		const owned = ownedFromPlan(plan, approved);
		const { path, record } = recordRun(repoRoot, {
			level: owned.level,
			schemas: owned.schemas,
			agents: owned.agents,
		});
		console.log(JSON.stringify({ path, record, approved, ignored: owned.ignored }, null, 2));
	} catch (err) {
		// Nothing is written on a bad input: a record built from a half-understood plan is
		// worse than no record, because the next run acts on it without asking.
		console.error(err instanceof Error ? err.message : String(err));
		process.exit(1);
	}
}
