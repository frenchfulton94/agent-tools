import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { backupPath } from './config-facts.mjs';
import { isMain } from './lib/cli.mjs';
import { mergeManifests, planInstalls } from './lib/settings.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const PAYLOAD = join(HERE, '..', 'payload');

/** The name of the throwaway change verification creates and removes, so this is never a surprise. */
export const PROBE_CHANGE = 'zz-workflows-setup-probe';

/**
 * The one workflow this plugin ships. It was once the `minimal` level of three; the name
 * stays in the plan and in `.claude/workflows.json` so a record written by any release
 * reads the same way.
 */
export const LEVEL = 'minimal';

/** The levels 0.10.0 removed. A repository recorded at one of them gets told, in the plan. */
const REMOVED_LEVELS = new Set(['standard', 'advanced']);

/**
 * Thrown for a level argument. There are no levels to choose between any more, and a stale
 * `plan.mjs advanced` must fail loudly rather than quietly plan the one workflow under a
 * name the caller did not ask for. The CLI entry point prints just the message.
 */
export class UnknownLevelError extends Error {}
/**
 * Workflows only a `custom` profile provides; the flows' documented path needs these.
 * The CLI ships exactly one preset, `core`, whose fixed six workflows (`CORE_WORKFLOWS` in
 * detect.mjs) do not include them — there is no "expanded" preset to pick, which is why the
 * warning below names the custom selection specifically rather than a preset that does not
 * exist.
 */
const NEEDED_WORKFLOWS = ['new', 'continue'];

const readJson = (p) => (existsSync(p) ? JSON.parse(readFileSync(p, 'utf8')) : {});
const subdirs = (d) =>
	existsSync(d)
		? readdirSync(d, { withFileTypes: true }).filter((e) => e.isDirectory()).map((e) => e.name).sort()
		: [];

/**
 * Renders the machine's OpenSpec profile for a human-readable warning. `detection.openspecCli.profile`
 * is typed `string | null`, but Task 7 deliberately mirrors the CLI's own `config.profile || 'core'`
 * defaulting without validating the type it read off disk — a hand-edited machine config with
 * `"profile": 42` surfaces here as the *number* 42, not a string. `String()` guards this file's own
 * display of that value rather than assuming the type holds at runtime; it does not change what
 * detect.mjs reports. `null` specifically means "no machine config found" (not the same as an
 * explicit `core`), so it gets its own label instead of the misleading literal `"null"`.
 */
function profileLabel(profile) {
	return profile == null ? 'unset (no machine config found)' : String(profile);
}

/**
 * Splits the names the payload ships into what to copy, what this plugin may update, and what
 * belongs to the user.
 *
 * The ownership question — "is this ours?" — is answered only by `.claude/workflows.json`
 * (`scripts/record.mjs`): a name a previous run recorded, whose content on disk still hashes
 * to what that run wrote. That is the one claim that survives a version bump, because the
 * shipped content moves and the recorded hash does not. Two deliberate consequences:
 *
 * - A repo with no record — a first run, or one whose record is unreadable — owns nothing, so
 *   every existing name collides. That is the old behaviour, and it is the safe direction to
 *   fail in.
 * - A file of ours the user has edited hashes differently, so it collides. Setup reports it
 *   instead of quietly reverting their change, which is what "never lost silently" means here.
 *
 * `existingNames`/`hashes`/`recorded` are read defensively: a detection object from an older
 * build carries no hashes, and the answer that produces — everything collides — is the
 * conservative one, not a crash and not a silent overwrite.
 */
function classify(shipped, existingNames, hashes, recorded) {
	const existing = new Set(existingNames ?? []);
	const copy = [];
	const update = [];
	const collide = [];
	for (const name of shipped) {
		if (!existing.has(name)) copy.push(name);
		else if (recorded?.[name] && hashes?.[name] && recorded[name] === hashes[name]) update.push(name);
		else collide.push(name);
	}
	return { copy, update, collide };
}

/**
 * Names this plugin used to ship and no longer does, from the payload's `retired.json`:
 * the pre-0.8.0 bridge schema and every schema and agent of the `standard` and `advanced`
 * levels 0.10.0 removed.
 * Setup deletes nothing on its own, so without this a renamed schema or a dropped agent
 * stays on disk indefinitely — and a dropped agent keeps loading, its description still
 * telling the model to reach for it. A retired name is offered for deletion only when the
 * record says this plugin wrote it, its bytes still match what was written, and nothing
 * still needs it. Everything else is kept with its reason, because a file the user edited,
 * or one an in-flight change resolves against, is theirs to delete.
 *
 * An open change whose schema detection could not read (`null`) might be any of them, and
 * a detection with no `changeSchemas` at all never looked; both keep every retired schema.
 * Retired agents stay while any retired schema stays, because the old schemas dispatch them.
 */
function planRetirement(payloadRoot, detection) {
	const retired = readJson(join(payloadRoot, 'retired.json'));
	const changes = detection.openspec?.changeSchemas;

	const sweep = (names, onDisk, hashes, recorded, blocker) => {
		const out = { retire: [], keep: [] };
		for (const name of names ?? []) {
			if (!(onDisk ?? []).includes(name)) continue;
			let reason;
			if (!recorded?.[name]) reason = 'not installed by this plugin';
			else if (!hashes?.[name] || hashes[name] !== recorded[name]) reason = 'edited since this plugin installed it';
			else reason = blocker(name);
			if (reason) out.keep.push({ name, reason });
			else out.retire.push(name);
		}
		return out;
	};

	const schemas = sweep(
		retired.schemas,
		detection.openspec?.schemas,
		detection.openspec?.schemaHashes,
		detection.prior?.schemas,
		(name) => {
			if (!changes) return 'open changes were not checked, so one may use it';
			const open = Object.values(changes);
			if (open.includes(name)) return 'an open change uses it';
			if (open.includes(null)) return 'an open change names no schema, so it may use this one';
			return null;
		},
	);
	const agents = sweep(retired.agents, detection.agents?.files, detection.agents?.hashes, detection.prior?.agents, () =>
		schemas.keep.length > 0 ? 'a retired schema it serves is being kept' : null,
	);
	return { schemas, agents };
}

/**
 * Consumes `Detection` (Task 7) and produces the single artifact a user approves before setup
 * writes anything. Computes schema collisions from `detection.openspec.schemas` directly, never
 * touching the filesystem itself, so this stays pure and testable.
 *
 * `payloadRoot` (default: this plugin's real shipped payload) is a TEST-ONLY seam. A
 * `payloadRoot` with no schemas directory throws (see the guard in the body): it used to
 * degrade through the `existsSync` guards below into empty manifests, schemas, and agents — a
 * plan that looks successful (0 schemas, 0 agents, 0 warnings, plugins still installing) while
 * delivering none of the workflow, which is worse than a crash. No user-facing caller (the CLI
 * entry point, the setup skill, or anything else that runs against a real repo) may ever pass
 * this option.
 */
export function buildPlan(detection, { payloadRoot = PAYLOAD } = {}) {
	// Ruling 48: `payloadRoot` was documented-but-unvalidated, so a wrong path degraded into an
	// empty-but-plausible plan. Prose cannot close a vector; this can.
	const shippedSchemasDir = join(payloadRoot, 'openspec', 'schemas');
	if (!existsSync(shippedSchemasDir)) {
		throw new Error(`payloadRoot ${JSON.stringify(payloadRoot)} has no openspec/schemas directory — refusing to build an empty-but-plausible plan.`);
	}

	const warnings = [];

	// I3, and Ruling 47: a settings file we could not parse is not a settings file with no
	// decisions in it, but `decidedPlugins` cannot tell them apart — both come back empty. Left
	// unsaid, that silently queues every plugin for install, with nothing in the plan hinting
	// why. It leads the warnings because it invalidates the plugin section the user is about
	// to approve.
	if (detection.settings?.status === 'unparseable') {
		warnings.push(
			'Could not read `.claude/settings.json` — it exists but is not valid JSON (a trailing comma is the ' +
				'usual cause). Choices already recorded in it CANNOT be honoured by this plan: every plugin below ' +
				'is listed as an install because none could be read as already decided. Fix the file and ' +
				're-run setup before approving this.',
		);
	}

	// A repository a removed level set up keeps everything that level installed. Its own
	// files are offered for deletion one by one below (`retire`); nothing goes without a yes.
	const priorLevel = detection.prior?.level;
	if (REMOVED_LEVELS.has(priorLevel)) {
		warnings.push(
			`This repository was set up at the \`${priorLevel}\` level, which this plugin no longer ships. ` +
				'Setup now installs one workflow: the seven `-flow` schemas. The schemas and agents that level ' +
				'installed stay on disk and are no longer updated; the ones nobody has edited and no open change ' +
				'uses are listed under retire, each deleted only if you approve it. Plugins that level enabled are ' +
				"left as they are. `openspec/config.yaml`'s default schema becomes `feature-flow`; open changes " +
				'keep the schema they were created with.',
		);
	}

	// One manifest: the plugins the flows call. Nothing else is installed.
	const merged = mergeManifests([readJson(join(payloadRoot, 'settings.json'))]);
	const plugins = planInstalls(merged, new Set(detection.settings.decided));

	// I2 and I6, together. `copy` is what is not there yet. Of the names that ARE there, the
	// ones a previous run of this plugin installed and nobody has edited since are `update` —
	// re-running is the documented way to take updates, and without this split it never was:
	// every shipped name looked like a user's own file on the second run. Everything else is
	// `collide`: a file the user wrote, or one of ours they have since changed, and neither is
	// ever replaced without being named in the plan and approved individually.
	const shippedSchemas = subdirs(shippedSchemasDir);
	const schemas = classify(shippedSchemas, detection.openspec.schemas, detection.openspec.schemaHashes, detection.prior?.schemas);

	const agentFilesIn = (dir) =>
		existsSync(dir) ? readdirSync(dir).filter((f) => f.endsWith('.md')) : [];
	const shippedAgents = agentFilesIn(join(payloadRoot, 'agents')).sort();
	const agents = classify(shippedAgents, detection.agents?.files, detection.agents?.hashes, detection.prior?.agents);

	const configExists = Boolean(detection.openspec.configPath);

	const missing = NEEDED_WORKFLOWS.filter((w) => !detection.openspecCli.workflows.includes(w));
	if (missing.length > 0) {
		warnings.push(
			`This machine's OpenSpec profile ("${profileLabel(detection.openspecCli.profile)}") does not include ` +
				`the ${missing.join(', ')} workflow(s) the flows use. Fix it by running ` +
				'`openspec config profile`, choosing the custom option, and selecting those workflows ' +
				'individually — the CLI has one preset, `core`, and it does not include them — then ' +
				'`openspec update` in this project. `openspec config profile` is machine-wide: it changes the ' +
				"profile for every project on this machine, not just this one, so setup never runs it for you — " +
				"you'll need to run it yourself.",
		);
	}

	const humanSteps = [];
	if (!detection.humanArtifacts.issueTracker) {
		humanSteps.push(
			'Run `/mattpocock-skills:setup-matt-pocock-skills` — an interview only you can answer. It writes docs/agents/issue-tracker.md.',
		);
	}
	if (!detection.humanArtifacts.product) {
		humanSteps.push(
			'If this project has a user interface, run `/impeccable init` — an interview that writes PRODUCT.md. ' +
				'The flows send all surface work through impeccable, and it asks for this first. Skip it otherwise.',
		);
	}
	if (plugins.install.length > 0) {
		humanSteps.push('Run `/reload-plugins` to activate the newly installed plugins in this session.');
	}

	return {
		mode: detection.priorRun ? 'reconcile' : 'fresh',
		level: LEVEL,
		// I1/legacy-cleanup: `openspec init` over an existing directory has a legacy-cleanup path,
		// so this is true only when openspec/ is genuinely absent — never inferred any other way.
		openspecInit: !detection.openspec.present,
		schemas,
		agents,
		retire: planRetirement(payloadRoot, detection),
		config: {
			action: configExists ? 'replace' : 'create',
			// `backupPath` (config-facts.mjs) owns the collision-resistance guarantee — a
			// timestamp plus a per-process monotonic counter, so a re-run can never overwrite
			// a prior backup even within the same millisecond. Computed here, not re-derived
			// by hand, so this plan and the one function that guards the invariant agree.
			backupTo: configExists ? backupPath(detection.openspec.configPath) : null,
		},
		plugins,
		humanSteps,
		probeChange: PROBE_CHANGE,
		warnings,
	};
}

if (isMain(import.meta.url)) {
	// A pipeline consumer must never receive JSON it could mistake for a real plan, so nothing
	// is written to stdout unless buildPlan actually succeeds — every failure goes to stderr
	// only, with a non-zero exit. But a user typo and a genuine defect are not the same problem:
	// an UnknownLevelError is fully explained by its message, while any other error is a bug in
	// this module that someone will need to localise, so it gets its full stack instead.
	try {
		const stdinDetection = JSON.parse(readFileSync(0, 'utf8'));
		const arg = process.argv[2];
		if (arg !== undefined && arg !== LEVEL) {
			throw new UnknownLevelError(
				`Unknown level ${JSON.stringify(arg)}. This plugin ships one workflow and takes no level; run plan.mjs with no argument.`,
			);
		}
		const plan = buildPlan(stdinDetection);
		console.log(JSON.stringify(plan, null, 2));
	} catch (err) {
		if (err instanceof UnknownLevelError) {
			console.error(err.message);
		} else {
			console.error(err instanceof Error ? (err.stack ?? err.message) : String(err));
		}
		process.exit(1);
	}
}
