/**
 * Assembles and tallies the trigger battery for `reviewing-code-security`.
 *
 * The skill's frontmatter `description` is the only thing a model sees when deciding whether to load
 * it. Too narrow and a pre-merge check never fires, and the cost is an unreviewed vulnerability; too
 * broad and it fires on a rename. `triggers.md` holds 20 probes written to measure that, and the
 * battery had never really been run: 5 of the 20, one malformed answer caught by eye, and a single
 * recorded failure resting on five trials of one query.
 *
 * This script owns the two parts of that run which a script fixes cheaply — assembling prompts from
 * the descriptions actually on disk, and validating answers. It deliberately does NOT dispatch.
 * Every trial costs money and needs a model, so a harness shelling out to `claude -p` would be the
 * least-tested code in this repository guarding its most expensive claim. Dispatch stays human-run
 * via the `dispatch.sh` this script writes.
 *
 * Usage:
 *   bun battery.ts prompts --model <id> --scratch <dir> [--probe <id> ...] [--trials <n>]
 *   bun battery.ts tally --scratch <dir>
 *
 * Exit codes: 0 = success, 1 = at least one trial malformed or missing, 2 = usage error, 3 = the
 * results file this run would write already exists and belongs to a different model (or to nobody
 * this script can identify), so nothing was written.
 */

/** One query from `triggers.md`, with the outcome the battery expects of it. */
export interface Probe {
	id: string;
	query: string;
	expectation: 'fire' | 'nofire';
}

const FIRE_HEADING = /^##\s+Should fire/i;
const NOFIRE_HEADING = /^##\s+Should not fire/i;
/**
 * A probe is a numbered item whose query is the first double-quoted span on its line. Requiring the
 * quote is what lets the recorded rate lines and the trailing commentary in `triggers.md` sit in the
 * same file without being mistaken for probes.
 */
const ITEM_RE = /^\s*\d+\.\s+"(.+?)"/;

/**
 * Ids are positional (`fire-1`, `nofire-3`) rather than derived from the query text, so that fixing
 * a typo in a probe does not orphan the trials already recorded against it. Reordering or inserting
 * a probe DOES rebind ids — which is correct, because it changes the battery, and `tests/
 * security-evals.test.ts` pins the 10/10 counts so such an edit cannot pass unnoticed.
 */
export function parseProbes(text: string): Probe[] {
	const probes: Probe[] = [];
	let section: 'fire' | 'nofire' | null = null;
	let n = 0;

	for (const line of text.split('\n')) {
		if (FIRE_HEADING.test(line)) {
			section = 'fire';
			n = 0;
			continue;
		}
		if (NOFIRE_HEADING.test(line)) {
			section = 'nofire';
			n = 0;
			continue;
		}
		if (section === null) continue;

		const match = ITEM_RE.exec(line);
		if (match?.[1] === undefined) continue;
		n++;
		probes.push({ id: `${section}-${n}`, query: match[1], expectation: section });
	}

	return probes;
}

import { existsSync, readdirSync, statSync } from 'node:fs';

/**
 * The recorded competitor lineup. Changing it invalidates every previously recorded rate.
 *
 * `acknowledgedOmissions` names shipped skills the recorded rates never competed against. It is not
 * a lineup: nothing in it is loaded, shown to a probe, or counted. It exists so that adding an
 * unrelated skill to this marketplace costs one line of JSON instead of ~60 paid dispatches, while
 * still leaving a machine-readable record of exactly which skills the numbers did not face.
 */
export interface Manifest {
	target: string;
	decoys: string[];
	synthetic: string[];
	acknowledgedOmissions: string[];
}

/** The on-disk shape, before defaulting. A manifest written before `acknowledgedOmissions` existed still reads. */
type RawManifest = Omit<Manifest, 'acknowledgedOmissions'> & { acknowledgedOmissions?: string[] };

/** A skill name paired with the description a probe is shown. */
export interface Candidate {
	name: string;
	description: string;
}

// `fileURLToPath`, not `.pathname`: `pathname` is percent-encoded, so a checkout under a path
// containing a space would give directories spelled with `%20` and every read from them would fail.
const EVALS_DIR = fileURLToPath(new URL('./', import.meta.url));
const REPO_PLUGINS = fileURLToPath(new URL('../../../../../plugins/', import.meta.url));

/**
 * Reads one scalar field out of YAML frontmatter. Handles the plain `field: value` form and the
 * folded `field: >` block form, because shipped skills use both and a parser that only understood
 * the former would silently hand a probe an empty description — a competitor that cannot compete,
 * inflating the target's apparent hit rate.
 *
 * `feature-sliced-design` and `internationalized-date-time` are the folded ones at present. They
 * are named as examples, not as the reason: the form is legal YAML that any skill may adopt, so
 * this stays whether or not those two keep using it. It previously cited `manhattan-brand-artifacts`,
 * whose plugin has since been retired — which is exactly why the reason is stated structurally now.
 */
export function frontmatterField(text: string, field: string): string | null {
	if (!text.startsWith('---')) return null;
	const end = text.indexOf('\n---', 3);
	if (end === -1) return null;
	const block = text.slice(3, end);

	const lineMatch = new RegExp(`^${field}:[ \\t]*(.*)$`, 'm').exec(block);
	if (lineMatch === null) return null;
	const value = lineMatch[1] ?? '';

	if (!/^[>|][-+]?[ \t]*$/.test(value)) {
		const trimmed = value.trim();
		return trimmed.length > 0 ? trimmed.replace(/^["']|["']$/g, '') : null;
	}

	const rest = block.slice(lineMatch.index + lineMatch[0].length).split('\n').slice(1);
	const lines: string[] = [];
	for (const line of rest) {
		if (line.trim() === '') break;
		if (!/^\s/.test(line)) break;
		lines.push(line.trim());
	}
	const joined = lines.join(' ').trim();
	return joined.length > 0 ? joined : null;
}

/**
 * Reads the recorded competitor lineup from `manifest.json` in `dir` (defaults to this file's own
 * directory). A manifest with no `acknowledgedOmissions` field reads as an empty one rather than
 * `undefined`, so a manifest written before the field existed does not crash its readers.
 */
export async function loadManifest(dir: string = EVALS_DIR): Promise<Manifest> {
	const raw = (await Bun.file(`${dir}manifest.json`).json()) as RawManifest;
	return { ...raw, acknowledgedOmissions: raw.acknowledgedOmissions ?? [] };
}

/**
 * Every skill directory this marketplace ships, across every plugin. Walks the same
 * `plugins/<plugin>/skills/<skill>/` layout `describePath` resolves shipped descriptions from, so
 * the set of skills the manifest is checked against cannot drift from the set it reads.
 */
export function shippedSkills(pluginsDir: string = REPO_PLUGINS): string[] {
	if (!existsSync(pluginsDir)) return [];
	const out: string[] = [];
	for (const plugin of readdirSync(pluginsDir).filter((d) => statSync(join(pluginsDir, d)).isDirectory())) {
		const base = join(pluginsDir, plugin, 'skills');
		if (!existsSync(base)) continue;
		for (const skill of readdirSync(base).filter((d) => statSync(join(base, d)).isDirectory())) out.push(skill);
	}
	return out;
}

/**
 * The entries of `m.acknowledgedOmissions` that no longer name a shipped skill directory, sorted.
 *
 * The asymmetry with the drift gate in `tests/security-evals.test.ts` is deliberate. A *missing*
 * entry — a shipped skill in none of the manifest's four lists — is a correctness problem: nobody
 * can say what discrimination task the recorded rates describe, so that gate fails and offers the
 * two ways out. A *stale* entry cannot hide a shipped skill, because that same gate still catches
 * every one of those; all it does is leave the manifest claiming the rates deliberately excluded
 * something that no longer exists. That is hygiene, so it fails for a different reason and its only
 * remedy is deleting the line.
 */
export function staleAcknowledgedOmissions(m: Manifest, pluginsDir: string = REPO_PLUGINS): string[] {
	const shipped = new Set(shippedSkills(pluginsDir));
	return m.acknowledgedOmissions.filter((name) => !shipped.has(name)).sort();
}

/** Where a name's description lives: a shipped SKILL.md, or a synthetic file under `decoys/`. */
function describePath(name: string, synthetic: Set<string>, evalsDir: string): string | null {
	if (synthetic.has(name)) {
		const p = `${evalsDir}decoys/${name}.md`;
		return existsSync(p) ? p : null;
	}
	if (!existsSync(REPO_PLUGINS)) return null;
	for (const plugin of readdirSync(REPO_PLUGINS).filter((d) => statSync(`${REPO_PLUGINS}${d}`).isDirectory())) {
		const p = `${REPO_PLUGINS}${plugin}/skills/${name}/SKILL.md`;
		if (existsSync(p)) return p;
	}
	return null;
}

/**
 * Descriptions are read from disk every run, never transcribed. The point is to measure the string
 * that ships, and a pasted copy goes stale the moment someone edits the description — which is
 * exactly the moment the battery is due to be re-run.
 *
 * Throws rather than skipping on an unresolvable name: a lineup missing a competitor is a different
 * experiment from the one recorded, and silently running the easier version is the defect this
 * whole branch exists to fix.
 *
 * `m.acknowledgedOmissions` is deliberately absent from `names`. An acknowledged omission is an
 * omission: if such a name entered the lineup, the record of what the rates never competed against
 * would be a lie. `tests/security-evals.test.ts` asserts that it stays out.
 */
export async function loadCandidates(m: Manifest, dir: string = EVALS_DIR): Promise<Candidate[]> {
	const synthetic = new Set(m.synthetic);
	const names = [m.target, ...m.decoys, ...m.synthetic];
	const out: Candidate[] = [];

	for (const name of names) {
		const path = describePath(name, synthetic, dir);
		if (path === null) throw new Error(`lineup names "${name}", which resolves to no description file`);
		const description = frontmatterField(await Bun.file(path).text(), 'description');
		if (description === null) throw new Error(`${path} has no frontmatter description`);
		out.push({ name, description });
	}

	return out;
}

import { mkdirSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { basename, dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

/** Builds the trial id shown to a human alongside its recorded answer: `<probe-id>.t<trial>`. */
export function trialId(probeId: string, trial: number): string {
	return `${probeId}.t${trial}`;
}

/**
 * A lineup has position bias, and three trials of one ordering would measure that bias three times
 * instead of averaging it out. Trial n places the target at index (5·(n−1)) mod `candidates.length`
 * — the modulus is the live lineup size, not a constant, so this stays correct when the lineup
 * changes. At the current 13 that is 0, 5, 10, 2, 7 for the first five trials: five distinct
 * indices, because 5 is coprime with 13. Deterministic, so there is no seed to record and the
 * ordering of any trial is reconstructible from its number.
 *
 * A lineup size sharing a factor with 5 — 15, say — would revisit indices within the first five
 * trials. Check that before changing the lineup, or the escalation to five trials stops sampling
 * five distinct positions.
 */
export function orderFor(trial: number, candidates: Candidate[]): Candidate[] {
	const [target, ...rest] = candidates;
	if (target === undefined) return [];
	const slot = (5 * (trial - 1)) % candidates.length;
	const ordered = [...rest];
	ordered.splice(slot, 0, target);
	return ordered;
}

/**
 * The version of the instrument. `buildPrompt`'s text *is* the instrument: a rate is a measurement
 * of how a model routes when asked in one particular way, so two rates gathered under two different
 * wordings are two different measurements wearing the same units.
 *
 * **Increment this whenever `buildPrompt`'s text changes.** Results carrying different
 * `promptVersion` values must not be compared, averaged, pooled, or plotted against each other — for
 * the same reason a rate measured against a different lineup may not be. The only way to compare a
 * description against a number taken under an older version is to re-dispatch every probe under the
 * current one.
 *
 * The versions so far:
 *
 * - **1** — required `skill_named` to be one of the listed names whenever `would_load` was true.
 *   The 60 trials in `results/2026-07-30-claude-opus-5.json` were dispatched under it. That file
 *   predates this field, so a results file with no `promptVersion` is version 1; `evals/README.md`
 *   records the convention.
 * - **2** — `would_load` means "would you load a skill at all", and `skill_named` always names the
 *   skill. Version 1 had no legal way to say "yes, a skill — just not one of yours", and on
 *   `nofire-2` three correct answers came back unrepresentable because of it.
 */
export const PROMPT_VERSION = 2;

/**
 * Asks which skill the model would load, and nothing else. This measures *stated* routing rather
 * than observed routing — a script cannot watch a real session load a skill — which is the proxy
 * `evals/README.md` records beside the numbers so nobody quotes a rate as a field measurement.
 *
 * The prompt never names the battery or the expected answer. The first partial run used a
 * meta-prompt and returned one answer nobody could interpret; a probe that knows it is being tested
 * is answering a different question.
 *
 * `would_load` asks whether a skill would be loaded at all, not whether one of the lineup would be, and
 * `skill_named` carries the name either way. Under version 1 it asked the narrower question and
 * required the name to come from the list, which left a probe that wanted a skill we had not offered
 * with no legal way to say so: on `nofire-2` all three trials wanted `superpowers:systematic-
 * debugging`, one named it in defiance of the instruction and two left `skill_named` empty in
 * obedience to it, and all three were thrown away as malformed. Changing this text changes the
 * instrument, which is what `PROMPT_VERSION` exists to record.
 */
export function buildPrompt(probe: Probe, trial: number, candidates: Candidate[]): string {
	const listed = orderFor(trial, candidates)
		.map((c, i) => `${i + 1}. ${c.name}\n   ${c.description}`)
		.join('\n\n');

	return [
		'You are about to answer a user. Before replying, you choose whether to load one of the',
		'skills below. Loading a skill costs context, so you load one only when it fits the task.',
		'',
		'Available skills:',
		'',
		listed,
		'',
		"The user's first message is:",
		'',
		`"${probe.query}"`,
		'',
		'Reply with exactly one JSON object and no other text, no code fence:',
		'{"would_load": true or false, "skill_named": "<skill name, or empty string>", "reason": "<one line>"}',
		'',
		'Set would_load to true if you would load a skill at all — one of the ones listed above,',
		'or a skill that is not listed. When it is true, skill_named must name the skill you would',
		"load: the exact name from the list when it is one of those, and the skill's own name when",
		'it is not. When it is false, skill_named must be "".',
	].join('\n');
}

const SUBCOMMANDS = new Set(['prompts', 'tally']);

function flag(name: string): string | undefined {
	const i = Bun.argv.indexOf(`--${name}`);
	return i === -1 ? undefined : Bun.argv[i + 1];
}

function flagAll(name: string): string[] {
	const out: string[] = [];
	for (let i = 0; i < Bun.argv.length; i++) {
		if (Bun.argv[i] === `--${name}` && Bun.argv[i + 1] !== undefined) out.push(Bun.argv[i + 1] as string);
	}
	return out;
}

/**
 * Wraps a value so bash reads it as one literal word. Single quotes are the only bash quoting that
 * suppresses everything, and the `'\''` dance is how a literal single quote gets through them.
 *
 * `dispatch.sh` is generated once and then read, pasted from, and re-run by hand, so a scratch path
 * with a space in it has to survive all three. It previously did not: the closing line interpolated
 * the path bare, producing a tally command that could be copied but not pasted.
 */
export function shellQuote(value: string): string {
	return `'${value.replaceAll("'", `'\\''`)}'`;
}

/**
 * `dispatch.sh` runs from the scratch directory, outside this repository, so no project memory or
 * repo-local plugin config is in scope. User-level memory and installed plugins still load — "clean"
 * here means no repository-specific context, not a vacuum — and `evals/README.md` records which were
 * active, since a reader comparing two runs needs to know whether that changed.
 *
 * Every trial is a real `claude -p` call and real money, so the script never reaches one by accident:
 *
 * - `--help` and an unknown flag both exit before the `cd` into scratch — no directory is touched,
 *   nothing is created — because `--help` used as a probe for usage text is the exact input that
 *   previously ran ~17 paid trials before a timeout stopped it.
 * - `--dry-run` lists every trial id, marks which already have a non-empty response and would be
 *   skipped, and exits before `mkdir -p responses` ever runs, so a dry run leaves no trace on disk.
 * - Before the first real call, the script prints how many trials would actually fire (already-
 *   answered ones excluded) and requires typing `yes`. `--yes` skips that prompt for non-interactive
 *   runs. Piped stdin without `--yes` refuses outright rather than blocking forever on a `read` no one
 *   can answer — that refusal only fires when there is something to dispatch, so a resumed run with
 *   nothing left to do never needs `--yes` either.
 * - That gate is documented as an exact `yes`, and `IFS= read -r REPLY` is what makes it one. With the
 *   default IFS, `read` strips leading and trailing whitespace before the comparison ever runs, so
 *   `yes ` and ` yes` proceeded through a gate whose contract says they should not.
 */
export function dispatchScript(model: string, scratch: string, ids: string[]): string {
	const lines = [
		'#!/usr/bin/env bash',
		'# Generated by evals/battery.ts. Runs from anywhere; it cds to its own scratch directory.',
		'set -u',
		'',
		'usage() {',
		'\techo "Usage: dispatch.sh [--dry-run] [--yes] [--help]"',
		'\techo',
		'\techo "  --dry-run  Print what would be dispatched, then exit 0 without calling claude."',
		'\techo "  --yes      Skip the confirmation prompt (required when stdin is not a TTY)."',
		'\techo "  --help     Print this usage and exit 0."',
		'}',
		'',
		'DRY_RUN=0',
		'ASSUME_YES=0',
		'for arg in "$@"; do',
		'\tcase "$arg" in',
		'\t\t--dry-run)',
		'\t\t\tDRY_RUN=1',
		'\t\t\t;;',
		'\t\t--yes)',
		'\t\t\tASSUME_YES=1',
		'\t\t\t;;',
		'\t\t--help)',
		'\t\t\tusage',
		'\t\t\texit 0',
		'\t\t\t;;',
		'\t\t*)',
		'\t\t\techo "Unknown argument: $arg" >&2',
		'\t\t\tusage >&2',
		'\t\t\texit 2',
		'\t\t\t;;',
		'\tesac',
		'done',
		'',
		`cd ${shellQuote(scratch)} || exit 1`,
		`MODEL=${shellQuote(model)}`,
		'',
		'ids=(',
		...ids.map((id) => `\t${id}`),
		')',
		'',
		'pending=()',
		'for id in "${ids[@]}"; do',
		'\tif [ -s "responses/$id.json" ]; then continue; fi',
		'\tpending+=("$id")',
		'done',
		'',
		'if [ "$DRY_RUN" -eq 1 ]; then',
		'\techo "DRY RUN: ${#ids[@]} trial(s) total, ${#pending[@]} would be dispatched."',
		'\techo "  model:   $MODEL"',
		'\techo "  scratch: $(pwd)"',
		'\tfor id in "${ids[@]}"; do',
		'\t\tif [ -s "responses/$id.json" ]; then',
		'\t\t\techo "  skip  $id (already answered)"',
		'\t\telse',
		'\t\t\techo "  run   $id"',
		'\t\tfi',
		'\tdone',
		'\texit 0',
		'fi',
		'',
		'if [ "${#pending[@]}" -gt 0 ] && [ "$ASSUME_YES" -ne 1 ]; then',
		'\tif [ ! -t 0 ]; then',
		'\t\techo "ERROR: stdin is not a TTY and --yes was not given; refusing to dispatch ${#pending[@]}" \\',
		'\t\t\t"trial(s) rather than block on a confirmation nothing can answer. Re-run with --yes." >&2',
		'\t\texit 1',
		'\tfi',
		'\techo "About to dispatch ${#pending[@]} of ${#ids[@]} trial(s) with model $MODEL from $(pwd)."',
		'\techo "This calls \\`claude -p\\` once per trial and costs real money."',
		'\tprintf \'Type "yes" to proceed: \'',
		// `IFS=` for this one command: with the default IFS, `read` strips the surrounding whitespace
		// and `yes ` passes a gate documented as an exact `yes`.
		'\tIFS= read -r REPLY',
		'\tif [ "$REPLY" != "yes" ]; then',
		'\t\techo "Aborted; nothing dispatched."',
		'\t\texit 0',
		'\tfi',
		'fi',
		'',
		'mkdir -p responses',
		'for id in "${ids[@]}"; do',
		'\tif [ -s "responses/$id.json" ]; then echo "skip  $id (already answered)"; continue; fi',
		'\techo "run   $id"',
		'\tclaude -p "$(cat "prompts/$id.txt")" --model "$MODEL" --output-format json > "responses/$id.json"',
		'done',
		'',
		`echo "done. Tally with: bun run battery:tally --scratch ${shellQuote(scratch)}"`,
	];
	return `${lines.join('\n')}\n`;
}

/**
 * The one form of a path that can be compared to another: symlinks followed, and — on a
 * case-insensitive filesystem — the casing the disk actually holds rather than the casing that was
 * typed. `resolve()` alone gives neither, because it is purely lexical and never touches the disk.
 *
 * The complication `realpathSync` brings is that `--scratch` normally names a directory that does
 * not exist yet, and `realpathSync` throws on a missing path. So: walk up to the nearest ancestor
 * that does exist, canonicalise that, and re-append the components walked past. The remainder stays
 * lexical, which is correct — a path component that is not on disk has no symlink to follow and no
 * on-disk casing to recover. If nothing on the way up exists (or every attempt throws, e.g. a
 * symlink loop), the lexical resolution is returned unchanged; that is the old behaviour, so the
 * guard degrades to its previous strength rather than to none.
 */
function canonicalPath(path: string): string {
	let head = resolve(path);
	const tail: string[] = [];

	for (;;) {
		try {
			const real = realpathSync(head);
			return tail.length === 0 ? real : join(real, ...tail);
		} catch {
			const parent = dirname(head);
			if (parent === head) return resolve(path);
			tail.unshift(basename(head));
			head = parent;
		}
	}
}

/**
 * True when `path` is `root` itself or lies beneath it. The prefix test requires a following
 * separator, so `<root>-sibling` — which shares `root` as a bare string prefix but is genuinely
 * beside it, not inside it — is not inside. Extracted because it is applied to more than one
 * spelling of each side and the two comparisons must not drift apart.
 */
function pathInside(path: string, root: string): boolean {
	return path === root || path.startsWith(root + sep);
}

/**
 * True when `scratch` falls inside this repository. This guard has now been wrong seven times, and
 * every one of those was the comparison being weaker than the paths it compared. Assume an eighth.
 *
 * The seven, and what closes each:
 *
 * 1. A bare relative `--scratch` (e.g. `scratch-run`) never looks in-repo by `startsWith`, but
 *    resolves under `process.cwd()` and lands inside the repo anyway. `resolve()` closes it.
 * 2. `--scratch .` from the repository root IS the repository. `new URL(...)` carries a trailing
 *    separator and `resolve()` never produces one, so `startsWith` alone never matched the root
 *    itself. Testing equality as well as the prefix closes it.
 * 3. A symlink that lives outside the repository and points inside it. `resolve()` is lexical and
 *    never sees the target; `realpathSync`, via `canonicalPath`, does.
 * 4. A case-variant of the root (`/users/...` where the disk holds `/Users/...`). On a
 *    case-insensitive filesystem that path IS the repository, but the string comparison said
 *    otherwise. `realpathSync` returns the disk's casing, so both sides normalise to it. This is
 *    the likeliest to happen by accident — a human can type it.
 * 5. The root was resolved four levels up from `evals/` where five are needed: `../../../../` is
 *    `plugins/`, so a scratch directory at the repository root sailed through the guard that exists
 *    to catch exactly that.
 * 6. `.pathname` rather than `fileURLToPath`: `pathname` is percent-encoded, so a checkout under a
 *    path containing a space gave a root spelled with `%20`, matching nothing — the guard was
 *    disabled entirely, and silently.
 * 7. A symlink that lives INSIDE the repository and points outside it. Canonicalising alone accepts
 *    it, because the canonical path really is outside. But `dispatch.sh` runs `cd '<repo>/link'`,
 *    and bash's `cd` is logical: `$PWD` stays a repo-internal path, so repo-local context discovery
 *    can still walk repository directories. The fix is to reject when EITHER the canonical path or
 *    the purely lexical `resolve()` lands inside — canonicalising can only move a path out of the
 *    repository, so an OR of the two is the only form that catches both directions of symlink.
 *
 * Both spellings of the root are compared against, for the same reason. The canonical root is what
 * makes cases 3 and 4 work — a repository reached through a symlinked ancestor (on macOS `/tmp` is
 * a symlink to `/private/tmp`) would otherwise fail to compare equal to itself. The lexical root is
 * what makes case 7 work when the repository itself is reached through such an ancestor.
 *
 * OR-ing only ever adds rejections, so the standing regression risk is over-rejection, not under-.
 * What must still be ACCEPTED, and is asserted in `tests/security-evals.test.ts`: `<repo-root>-
 * sibling`, and any genuinely-outside absolute path. Neither is inside either root under either
 * spelling, because a path outside the repository resolves lexically to itself.
 */
export function scratchInsideRepo(scratch: string): boolean {
	const rawRoot = fileURLToPath(new URL('../../../../../', import.meta.url));
	// `resolve()` strips the trailing separator `new URL(...)` leaves on a directory; without that,
	// nothing would ever compare equal to the root itself.
	const roots = [canonicalPath(rawRoot), resolve(rawRoot)];
	const spellings = [canonicalPath(scratch), resolve(scratch)];
	return spellings.some((s) => roots.some((r) => pathInside(s, r)));
}

async function cmdPrompts(): Promise<number> {
	const model = flag('model');
	const rawScratch = flag('scratch');
	if (model === undefined || rawScratch === undefined) {
		console.error('Usage: bun battery.ts prompts --model <id> --scratch <dir> [--probe <id> ...] [--trials <n>]\n');
		return 2;
	}
	if (scratchInsideRepo(rawScratch)) {
		console.error('ERROR: --scratch must be outside this repository, or the run is not clean.');
		return 2;
	}
	// Resolved once here, then carried through meta.json, dispatch.sh's `cd`, and the printed
	// instructions, so a dispatch.sh generated from a relative --scratch still works from any
	// directory it is later run from — not only the one this command happened to run from.
	const scratch = resolve(rawScratch);

	const trials = Number(flag('trials') ?? 3);
	if (!Number.isInteger(trials) || trials < 1) {
		console.error('ERROR: --trials must be a positive integer');
		return 2;
	}

	const only = new Set(flagAll('probe'));
	const manifest = await loadManifest();
	const candidates = await loadCandidates(manifest);
	const all = parseProbes(await Bun.file(`${EVALS_DIR}triggers.md`).text());
	const probes = only.size > 0 ? all.filter((p) => only.has(p.id)) : all;
	if (probes.length === 0) {
		console.error(`ERROR: --probe matched nothing. Known ids: ${all.map((p) => p.id).join(', ')}`);
		return 2;
	}

	// Escalation reuses this subcommand rather than a second mechanism: `--probe nofire-1 --trials 5`
	// re-emits t1..t5 for that probe alone, and dispatch.sh skips the trials already answered, so the
	// rotation continues at index 4 instead of restarting.
	mkdirSync(`${scratch}/prompts`, { recursive: true });
	const ids: string[] = [];
	for (const probe of probes) {
		for (let t = 1; t <= trials; t++) {
			const id = trialId(probe.id, t);
			ids.push(id);
			writeFileSync(`${scratch}/prompts/${id}.txt`, buildPrompt(probe, t, candidates));
		}
	}

	// The model is written here and read back by `tally`, so the id beside the numbers cannot
	// disagree with the id that was dispatched. `promptVersion` travels the same way and for the same
	// reason: these prompts were built by the version of `buildPrompt` running *now*, and a tally may
	// happen days and one prompt edit later.
	writeFileSync(
		`${scratch}/meta.json`,
		`${JSON.stringify(
			{
				model,
				promptVersion: PROMPT_VERSION,
				scratch,
				trials,
				probes: probes.map((p) => p.id),
				lineup: candidates.map((c) => c.name),
			},
			null,
			'\t',
		)}\n`,
	);
	writeFileSync(`${scratch}/dispatch.sh`, dispatchScript(model, scratch, ids));

	console.log(`Wrote ${ids.length} prompt(s) for ${probes.length} probe(s) to ${scratch}/prompts/`);
	console.log(`Dispatch with: bash ${scratch}/dispatch.sh`);
	return 0;
}

/** The forced schema. Prose is not an acceptable answer, and neither is a schema-consistent lie. */
export interface Answer {
	would_load: boolean;
	skill_named: string;
	reason: string;
}

/**
 * What an accepted answer did about the lineup descriptions it was shown. Four distinct things a probe
 * can do, only one of which can fire, and they are not interchangeable evidence:
 *
 * - `in-lineup` — named one of the lineup. If it is the target, the trial fired; if it is a competitor,
 *   the target lost a discrimination it was offered, which is what this battery exists to measure.
 * - `out-of-lineup` — named a skill that was not on offer. `nofire-2` did this on its first real
 *   run, naming `superpowers:systematic-debugging`, a user-level installed skill rather than a
 *   hallucination. That is evidence about the *trial environment*, not about the target's
 *   description, and it has to stay distinguishable from losing to a competitor we offered.
 * - `unnamed` — would load something, but named nothing. Under prompt version 1 this was produced by
 *   a probe that obeyed the instruction to name only listed skills while wanting to reach outside
 *   the list; version 2 removed that instruction, so an `unnamed` answer under it is a probe that
 *   would not or could not name what it reached for. It is not the same observation as `declined`
 *   under either version, and reading it as one would convert "I'd load something else" into "I'd
 *   load nothing".
 * - `declined` — would load none of the lineup, and said so cleanly.
 *
 * Prompt version 1 offered no way to say "yes, a skill — just not one of yours", so the middle two
 * are how that answer arrived. Widening the validator to accept them was a change to how existing
 * answers are read, which is why it could be made without touching `buildPrompt` and without
 * invalidating the 60 trials paid for under version 1. Version 2 then changed the prompt itself so
 * the answer has a home in the schema, and `PROMPT_VERSION` is what keeps the two sets of numbers
 * from being read as one.
 */
export type Outcome = 'in-lineup' | 'out-of-lineup' | 'unnamed' | 'declined';

export type Malformed = { ok: false; why: string };
export type Parsed = { ok: true; answer: Answer; outcome: Outcome } | Malformed;

const FENCE_RE = /```(?:json)?\s*([\s\S]*?)```/;

function firstObject(text: string): unknown {
	const fenced = FENCE_RE.exec(text);
	const body = fenced?.[1] ?? text;
	const start = body.indexOf('{');
	const end = body.lastIndexOf('}');
	if (start === -1 || end <= start) return undefined;
	try {
		return JSON.parse(body.slice(start, end + 1)) as unknown;
	} catch {
		return undefined;
	}
}

/**
 * A malformed answer is a first-class outcome, not a zero. It is never dropped, never averaged
 * around, and never read as `would_load: false` — the last of those would quietly convert an
 * uninterpretable trial into evidence that the skill did not fire.
 *
 * What is rejected is what is genuinely broken: a `would_load` that is not a boolean, a
 * `skill_named` that is not a string, a missing or empty `reason`, no JSON object at all, and
 * `would_load: false` alongside a non-empty `skill_named` — that last one is a real contradiction,
 * declining to load while naming what was loaded, and stays rejected.
 *
 * What is no longer rejected is either half of the answer the schema has no words for. This
 * validator used to require that a `true` `would_load` be paired with a name drawn from the lineup, and
 * on `nofire-2` all three trials agreed that the right skill was `superpowers:systematic-debugging`
 * — one naming it, two leaving `skill_named` empty because the prompt said the name must come from
 * the list. Three consistent, correct, mutually-reinforcing answers were all called malformed, and
 * for this battery's purpose the only fact that mattered was that the security skill did not fire in
 * any of them. Both shapes are now accepted and recorded as their own `Outcome`; neither can fire,
 * because firing still requires `skill_named` to be the target exactly.
 */
export function parseAnswer(raw: string, names: Set<string>): Parsed {
	let obj = firstObject(raw);

	// `claude -p --output-format json` wraps the reply in an envelope whose `result` is the text.
	if (typeof obj === 'object' && obj !== null && typeof (obj as { result?: unknown }).result === 'string') {
		obj = firstObject((obj as { result: string }).result);
	}
	if (typeof obj !== 'object' || obj === null) return { ok: false, why: 'no JSON object found' };

	const o = obj as Record<string, unknown>;
	if (typeof o.would_load !== 'boolean') return { ok: false, why: 'would_load is not a boolean' };
	if (typeof o.skill_named !== 'string') return { ok: false, why: 'skill_named is not a string' };
	if (typeof o.reason !== 'string' || o.reason.trim() === '') return { ok: false, why: 'reason is missing or empty' };

	// The one surviving consistency check. Unlike the two that were removed, no reading of this makes
	// it a coherent answer: it declines to load anything and then names the thing it loaded.
	if (!o.would_load && o.skill_named !== '') {
		return { ok: false, why: `would_load is false but skill_named is "${o.skill_named}"` };
	}

	const answer: Answer = { would_load: o.would_load, skill_named: o.skill_named, reason: o.reason };
	if (!o.would_load) return { ok: true, answer, outcome: 'declined' };
	if (o.skill_named === '') return { ok: true, answer, outcome: 'unnamed' };
	return { ok: true, answer, outcome: names.has(o.skill_named) ? 'in-lineup' : 'out-of-lineup' };
}

/** Fixed order and wording for the four outcomes, so two tallies of one run read identically. */
const OUTCOME_ORDER: readonly Outcome[] = ['in-lineup', 'out-of-lineup', 'unnamed', 'declined'];
const OUTCOME_PHRASE: Record<Outcome, string> = {
	'in-lineup': 'named a listed skill',
	'out-of-lineup': 'named a skill outside the lineup',
	unnamed: 'would load, but named nothing',
	declined: 'declined to load anything',
};

/**
 * One line saying what a probe's trials actually reached for. The rate line beside it counts only
 * fires, so on its own it cannot distinguish a probe that preferred a competitor we offered from one
 * that reached outside the offered set entirely — and the second is evidence about the trial
 * environment rather than about the target's description.
 *
 * Names are listed for both kinds of naming outcome, deduplicated and sorted, because "3 named a
 * skill outside the lineup" prompts the exact question the name answers.
 */
export function outcomeBreakdown(trials: readonly { outcome: Outcome; answer: Answer }[]): string {
	const parts: string[] = [];
	for (const outcome of OUTCOME_ORDER) {
		const mine = trials.filter((t) => t.outcome === outcome);
		if (mine.length === 0) continue;
		const named = [...new Set(mine.map((t) => t.answer.skill_named))].sort();
		const suffix = outcome === 'in-lineup' || outcome === 'out-of-lineup' ? ` (${named.join(', ')})` : '';
		parts.push(`${mine.length} ${OUTCOME_PHRASE[outcome]}${suffix}`);
	}
	return parts.length === 0 ? 'no interpretable trials' : `${parts.join('; ')}.`;
}

/**
 * The verdict follows the rule set in the v0.3.0 design and carried into this one unchanged. A
 * should-fire miss is a defect, investigated in every case and forcing a description change below
 * 3/5. A should-not-fire probe that fires is recorded with its rate and judged separately, because
 * the cost is a heavier review rather than a wrong answer — so this function states the number and
 * leaves the acceptance sentence to a human.
 */
export function rateLine(probe: Probe, fired: number, total: number): string {
	const rate = `fires ${fired}/${total}`;
	if (probe.expectation === 'fire') {
		return fired === total
			? `   Measured: ${rate}.`
			: `   Measured: ${rate}. DEFECT — a should-fire probe missed; investigate${fired * 5 < total * 3 ? ', and below 3/5 this forces a description change' : ''}.`;
	}
	return fired === 0 ? `   Measured: ${rate}.` : `   Measured: ${rate}. Record the rate and judge acceptance.`;
}

/**
 * Maps a value to one safe filename component: every character outside `[A-Za-z0-9._-]` becomes
 * `-`, and any run of dots collapses to a single one, so neither a `/` nor a `..` can survive to
 * steer a write out of `results/`. A provider-prefixed model id such as `anthropic/claude-opus-5`
 * is legitimate on some providers, so it is sanitised rather than rejected.
 *
 * Used ONLY for building a filename. The model id recorded *inside* `meta.json` and inside the
 * results JSON body stays the exact string that was dispatched: the filename is a label a human
 * scans, while the body is the evidence, and a mangled id in the body would misattribute which
 * model produced the numbers.
 *
 * This mapping is not injective: two ids differing only outside `[A-Za-z0-9._-]` — say
 * `anthropic/claude-opus-5` and `anthropic-claude-opus-5` — produce the same filename stem. The
 * verbatim `model` inside the JSON body, never the filename, is therefore the authoritative record
 * of which model produced a set of numbers, and `tally` reads that field rather than trusting the
 * stem before it removes anything: a colliding file belonging to a different model is kept, with
 * both ids named on stdout.
 *
 * A collision therefore costs a re-run, never a record. Two colliding ids that also share an outcome
 * would land on the same filename, and rather than overwrite, `tally` refuses and exits 3 with both
 * ids named. The one write that still overwrites is the one where the existing file records the same
 * model id, which is a re-tally of the same thing.
 */
export function safeFilenameSegment(value: string): string {
	return value.replace(/[^A-Za-z0-9._-]/g, '-').replace(/\.{2,}/g, '.');
}

/**
 * `fired` and `outcome` are both recorded, and neither replaces the other. `fired` is the number
 * every downstream rate is computed from and its meaning is unchanged; `outcome` says which of the
 * four non-firing (or, for `in-lineup`, possibly-firing) things the trial did, so a reader of a
 * results file can tell a competitor we offered from a skill we did not from a blank, without going
 * back to the raw responses.
 */
interface TrialRecord {
	trial: string;
	probe: string;
	expectation: 'fire' | 'nofire';
	trialNumber: number;
	fired: boolean;
	outcome: Outcome;
	answer: Answer;
}

/** Where committed evidence lives. The CLI never writes anywhere else. */
export const DEFAULT_RESULTS_DIR = `${EVALS_DIR}results`;

/**
 * Who an existing results file says produced it. `known: false` is a refusal rather than a default:
 * both callers use this to decide whether to destroy a file, and "I could not tell whose run this
 * is" must never be actioned as "it is not yours".
 *
 * The two unknown cases behave identically — keep the file, refuse — but they are distinguished
 * because a reader chasing the message needs to know which happened: a file that will not parse is
 * a truncated write, a bad merge, or a permissions problem, while a file that parses without a
 * `model` was written by something other than this script.
 */
type ResultsOwner = { known: true; model: string } | { known: false; why: 'unreadable' | 'no-model-field' };

async function recordedModel(path: string): Promise<ResultsOwner> {
	let body: unknown;
	try {
		body = await Bun.file(path).json();
	} catch {
		return { known: false, why: 'unreadable' };
	}
	const model = (body as { model?: unknown } | null)?.model;
	return typeof model === 'string' ? { known: true, model } : { known: false, why: 'no-model-field' };
}

/** Why an existing file's provenance could not be established, phrased for the person reading stdout. */
function unknownOwnerReason(why: 'unreadable' | 'no-model-field'): string {
	return why === 'unreadable'
		? 'it could not be read as JSON, so nothing here can say whose run it holds'
		: 'it parses as JSON but records no "model", so nothing here can say whose run it holds';
}

async function cmdTally(): Promise<number> {
	const scratch = flag('scratch');
	if (scratch === undefined) {
		console.error('Usage: bun battery.ts tally --scratch <dir>\n');
		return 2;
	}
	return await tally(scratch);
}

/**
 * Reads a dispatched scratch directory and files the run under `resultsDir`.
 *
 * `resultsDir` is a parameter rather than a constant so that a test can point a real tally at a
 * temporary directory. `results/` is documented as committed evidence of real, paid battery runs; a
 * test writing there — even one that cleans up in a `finally` — puts fabricated records in the one
 * place a reader is told to trust, and a hard-killed run would leave them. The CLI never passes this
 * argument, so its behaviour is exactly what it was.
 */
export async function tally(scratch: string, resultsDir: string = DEFAULT_RESULTS_DIR): Promise<number> {
	// Nothing paid is at stake here — tally only reads responses and writes into `results/` — so this
	// is symmetry with `cmdPrompts` rather than a live hazard. It is worth having anyway: a guard that
	// holds on one subcommand and not the other invites the reader to assume it is global, and the
	// same scratch directory is passed to both.
	if (scratchInsideRepo(scratch)) {
		console.error('ERROR: --scratch must be outside this repository, or the run is not clean.');
		return 2;
	}
	if (!existsSync(`${scratch}/meta.json`)) {
		console.error(`ERROR: ${scratch}/meta.json not found — run \`battery:prompts\` first.`);
		return 2;
	}

	const meta = (await Bun.file(`${scratch}/meta.json`).json()) as {
		model: string;
		promptVersion?: number;
		trials: number;
		probes: string[];
		lineup: string[];
	};
	// The version that BUILT these prompts, not the version this process happens to hold. A tally can
	// run after the prompt has been edited — that is the whole scenario `PROMPT_VERSION` exists for —
	// and stamping the current constant onto responses dispatched under an older one would mislabel
	// the instrument in exactly the way this field is meant to prevent. A `meta.json` with no such
	// field was written by `prompts` before the field existed, which makes it version 1; `evals/
	// README.md` records that convention for results files too.
	const promptVersion = meta.promptVersion ?? 1;
	const manifest = await loadManifest();
	const candidates = await loadCandidates(manifest);
	const names = new Set(candidates.map((c) => c.name));
	const byId = new Map(parseProbes(await Bun.file(`${EVALS_DIR}triggers.md`).text()).map((p) => [p.id, p]));

	const records: TrialRecord[] = [];
	const problems: string[] = [];

	for (const probeId of meta.probes) {
		const probe = byId.get(probeId);
		if (probe === undefined) {
			problems.push(`${probeId}: dispatched, but no longer in triggers.md`);
			continue;
		}
		for (let t = 1; t <= meta.trials; t++) {
			const id = trialId(probeId, t);
			const path = `${scratch}/responses/${id}.json`;
			if (!existsSync(path)) {
				problems.push(`${id}: no response file — re-dispatch it`);
				continue;
			}
			const parsed = parseAnswer(await Bun.file(path).text(), names);
			if (!parsed.ok) {
				problems.push(`${id}: MALFORMED (${parsed.why}) — re-dispatch it`);
				continue;
			}
			records.push({
				trial: id,
				probe: probeId,
				expectation: probe.expectation,
				trialNumber: t,
				fired: parsed.answer.would_load && parsed.answer.skill_named === manifest.target,
				outcome: parsed.outcome,
				answer: parsed.answer,
			});
		}
	}

	// Refuse to produce a rate for any probe with a malformed or missing trial. A rate computed over
	// the trials that happened to parse is the same defect as the hand-filtered first run.
	const broken = new Set(problems.map((p) => (p.split(':')[0] ?? '').split('.')[0]));
	console.log('\n--- paste into evals/triggers.md, under the matching probe ---\n');
	for (const probeId of meta.probes) {
		const probe = byId.get(probeId);
		if (probe === undefined) continue;
		if (broken.has(probeId)) {
			console.log(`${probeId}: NO RATE — a trial is malformed or missing.`);
			continue;
		}
		const mine = records.filter((r) => r.probe === probeId);
		console.log(`${probeId}: ${rateLine(probe, mine.filter((r) => r.fired).length, mine.length).trim()}`);
	}

	// Deliberately outside the paste block above, which is copied verbatim into `triggers.md` and
	// records rates. This says what the trials reached for instead, which a rate cannot: a probe that
	// preferred a competitor we offered and one that named a skill we never showed it both read as
	// `fires 0/3`, and only the second is evidence about the environment the run happened in.
	console.log('\n--- what each probe reached for ---\n');
	for (const probeId of meta.probes) {
		const mine = records.filter((r) => r.probe === probeId);
		if (mine.length === 0) continue;
		console.log(`${probeId}: ${outcomeBreakdown(mine)}`);
	}

	if (problems.length > 0) {
		console.error(`\n${problems.length} problem(s):`);
		for (const p of problems) console.error(`  ${p}`);
	}

	// A run with problems still writes its records — the `problems` array is the useful part of it —
	// but never under the name a clean run would take. `results/` is committed evidence, and a
	// partial run filed as `<date>-<model>.json` is indistinguishable from a complete one until
	// somebody opens it. The `-rejected` suffix carries the warning in the filename itself.
	const date = new Date().toISOString().slice(0, 10);
	const rejected = problems.length > 0;
	// `safeFilenameSegment` on the filename only: a provider-prefixed id like `anthropic/claude-opus-5`
	// would otherwise write outside `results/`. The body below records `meta.model` verbatim.
	const stem = `${resultsDir}/${date}-${safeFilenameSegment(meta.model)}`;
	const out = `${stem}${rejected ? '-rejected' : ''}.json`;
	// The two names describe one run and are mutually exclusive for a given (date, model). Re-tallying
	// after fixing a malformed trial would otherwise leave both on disk, and a committer would have two
	// files describing the same run with no way to tell which is current.
	const superseded = `${stem}${rejected ? '' : '-rejected'}.json`;

	// The same collision, on the write path. Two ids that sanitise to one stem AND share an outcome
	// produce the same filename, so this write would silently erase another model's committed run —
	// the identical defect the removal below guards, and worse for being silent. An existing file
	// recording *this* run's model is a genuine re-tally and is overwritten as before; anything else
	// stops the run. Nothing is written and nothing is removed, so the refusal costs only a re-run.
	if (existsSync(out)) {
		const owner = await recordedModel(out);
		if (!owner.known) {
			console.error(
				`ERROR: refusing to overwrite ${out} — ${unknownOwnerReason(owner.why)}, and destroying evidence needs a positive reason. Nothing was written; check that file by hand.`,
			);
			return 3;
		}
		if (owner.model !== meta.model) {
			console.error(
				`ERROR: refusing to overwrite ${out} — this run dispatched "${meta.model}" but that file records "${owner.model}". Their filenames collide only because characters outside [A-Za-z0-9._-] are replaced. Nothing was written; move that file aside, or dispatch under a model id that does not collide with it.`,
			);
			return 3;
		}
	}

	mkdirSync(resultsDir, { recursive: true });
	writeFileSync(
		out,
		`${JSON.stringify(
			{
				date,
				model: meta.model,
				// The instrument travels with the numbers, like the lineup below. A reader holding two
				// results files must be able to see that they are not comparable without having to know
				// what this script's source looked like on either day.
				promptVersion,
				trialsPerProbe: meta.trials,
				// The lineup travels with the numbers, so a reader of the results never has to trust
				// that manifest.json is unchanged since the run.
				lineup: candidates.map((c) => ({ name: c.name, description: c.description })),
				problems,
				records,
			},
			null,
			'\t',
		)}\n`,
	);
	console.log(
		rejected
			? `\nWrote ${out} — REJECTED, ${problems.length} unresolved trial(s); do not commit it. Fix them and tally again.`
			: `\nWrote ${out}`,
	);
	// Removing a results file needs a positive reason, because `results/` is committed evidence and a
	// deleted run is not recoverable from anything else here. The filename alone is not that reason:
	// `safeFilenameSegment` is not injective, so `anthropic/claude-opus-5` and `anthropic-claude-opus-5`
	// share a stem while being two different models. Only the `model` recorded inside the file says
	// whose run it was, so that is what is compared — and a file that cannot be read as a results file
	// is kept, since unknown provenance is a reason to leave evidence alone, not to remove it.
	//
	// Every branch is said out loud: a file vanishing from committed evidence, or surviving where a
	// reader expected one file, must never be something they have to notice for themselves.
	if (existsSync(superseded)) {
		const owner = await recordedModel(superseded);
		if (owner.known && owner.model === meta.model) {
			rmSync(superseded);
			console.log(
				`Removed ${superseded} — it records model "${owner.model}", so it was this (date, model) under the other name.`,
			);
		} else if (!owner.known) {
			console.log(
				`Left ${superseded} in place — ${unknownOwnerReason(owner.why)}. Removing evidence needs a positive reason; check it by hand.`,
			);
		} else {
			console.log(
				`Left ${superseded} in place — this run dispatched "${meta.model}" but that file records "${owner.model}". Their filenames collide only because characters outside [A-Za-z0-9._-] are replaced, so these are two different runs and neither is stale.`,
			);
		}
	}

	return rejected ? 1 : 0;
}

async function main(): Promise<number> {
	const sub = Bun.argv[2];
	if (sub === undefined || !SUBCOMMANDS.has(sub)) {
		console.error('Usage: bun battery.ts <prompts|tally> [flags]\n');
		return 2;
	}
	return sub === 'prompts' ? await cmdPrompts() : await cmdTally();
}

if (import.meta.main) process.exit(await main());
