import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { backupPath } from './config-facts.mjs';
import { mergeManifests, planInstalls } from './lib/settings.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const PAYLOAD = join(HERE, '..', 'payload');

/** The name of the throwaway change verification creates and removes, so this is never a surprise. */
export const PROBE_CHANGE = 'zz-workflows-setup-probe';

/**
 * The only valid levels. Exported so later tasks and the setup skill share one source of
 * truth instead of re-listing the names. An unrecognized level must never fall through to
 * produce a plausible-looking plan — see the guard at the top of `buildPlan` — because an
 * empty plan that looks successful (0 schemas, 0 agents, 0 warnings, but plugins still
 * installing) is worse than a crash: it mutates the user's environment while delivering
 * none of the workflow they asked for, and nothing in its shape signals that anything went
 * wrong.
 */
export const LEVELS = ['minimal', 'standard', 'advanced'];

/**
 * Thrown only for a bad `level` argument — a user typo, not a defect in this module. The
 * CLI entry point catches this specifically so it can print just the message (the failure
 * is fully explained by it); any other error is a genuine bug and gets its full stack
 * instead, since that is what someone will need to localise and fix it.
 */
export class UnknownLevelError extends Error {}

/** Levels that lean on the mattpocock pack, whose setup skill is human-only (§9). */
const MATTPOCOCK_LEVELS = new Set(['minimal', 'advanced']);
/**
 * Workflows only a `custom` profile provides; this level's documented flow needs these.
 * The CLI ships exactly one preset, `core`, whose fixed six workflows (`CORE_WORKFLOWS` in
 * detect.mjs) do not include them — there is no "expanded" preset to pick, which is why the
 * warning below names the custom selection specifically rather than a preset that does not
 * exist.
 */
const NEEDED_WORKFLOWS = ['new', 'continue'];
/**
 * The plugin that carries the `controlled-english` output style
 * (`plugins/meta-skills/output-styles/`). An output style ships with its plugin, so the
 * style only appears in `/config` once this plugin is active — and selecting one is a user
 * act nothing can automate. Hence a human step, ordered after the reload rather than
 * standing alone.
 */
const OUTPUT_STYLE_PLUGIN = 'meta-skills@agent-tools';

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
 * Splits the names this level ships into what to copy, what this plugin may update, and what
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
 * Consumes `Detection` (Task 7) and produces the single artifact a user approves before setup
 * writes anything. Computes schema collisions from `detection.openspec.schemas` directly, never
 * touching the filesystem itself, so this stays pure and testable.
 *
 * `payloadRoot` (default: this plugin's real shipped payload) is a TEST-ONLY seam for pinning
 * buildPlan's own base→web→level *composition order* — not a general escape hatch for testing
 * merge semantics. `mergeManifests` is already pure and exported, so the generic "a later
 * manifest's value wins per key" rule belongs in a direct unit test of that function, not here;
 * reading a payload directory is not impure the way spawning a subprocess is, so this is a
 * narrower seam than `detect.mjs`'s injectable `run`, not an equivalent of it. It exists only
 * because the real payload has no naturally-occurring value conflict across manifests to observe
 * order-sensitivity against. A `payloadRoot` with no `levels/<level>` directory now throws (see
 * the guard in the body): it used to degrade through the `existsSync` guards below into empty
 * manifests/schemas/agents, reproducing the round-1 "plausible-but-empty-plan" failure by a
 * different vector. No user-facing caller (the CLI entry point, the setup skill, or anything
 * else that runs against a real repo) may ever pass this option.
 */
export function buildPlan(detection, { level, payloadRoot = PAYLOAD }) {
	// An unrecognized level must fail loudly before anything else runs — including before the
	// first disk read — rather than silently falling through to an empty-but-plausible plan.
	if (!LEVELS.includes(level)) {
		throw new UnknownLevelError(`Unknown level ${JSON.stringify(level)}. Valid levels are: ${LEVELS.join(', ')}.`);
	}

	const levelDir = join(payloadRoot, 'levels', level);
	// Ruling 48, reversing Ruling 30: `payloadRoot` was documented-but-unvalidated, so a wrong
	// path degraded through the `existsSync` guards below into an empty-but-plausible plan —
	// 0 schemas, 0 agents, 0 warnings, plugins still installing — which is the exact failure
	// Ruling 27's level check exists to prevent, reached by a different door. Prose cannot
	// close a vector; this can.
	if (!existsSync(levelDir)) {
		throw new Error(`payloadRoot ${JSON.stringify(payloadRoot)} has no levels/${level} directory — refusing to build an empty-but-plausible plan.`);
	}

	// Ruling 48's lesson applies here too: a payload missing content the detection says
	// this plan must ship is a defect, and the empty-but-plausible plan it would produce
	// is the exact failure the level guard above exists to prevent.
	const appleActive = level === 'advanced' && Boolean(detection.apple?.app);
	const appleDir = join(levelDir, 'apple');
	if (appleActive && !existsSync(appleDir)) {
		throw new Error(
			`payloadRoot ${JSON.stringify(payloadRoot)} has no levels/advanced/apple directory — refusing to build a plan that omits the Apple content it claims to ship.`,
		);
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

	const manifests = [readJson(join(payloadRoot, 'base', 'settings.base.json'))];
	if (detection.web) manifests.push(readJson(join(payloadRoot, 'base', 'settings.base.web.json')));
	if (detection.apple?.swift) manifests.push(readJson(join(payloadRoot, 'base', 'settings.base.apple.json')));
	manifests.push(readJson(join(levelDir, 'settings.json')));

	const merged = mergeManifests(manifests);
	const plugins = planInstalls(merged, new Set(detection.settings.decided));

	// I2 and I6, together. `copy` is what is not there yet. Of the names that ARE there, the
	// ones a previous run of this plugin installed and nobody has edited since are `update` —
	// re-running is the documented way to take updates, and without this split it never was:
	// every shipped name looked like a user's own file on the second run. Everything else is
	// `collide`: a file the user wrote, or one of ours they have since changed, and neither is
	// ever replaced without being named in the plan and approved individually.
	const shippedSchemas = [
		...subdirs(join(levelDir, 'openspec', 'schemas')),
		...(appleActive ? subdirs(join(appleDir, 'openspec', 'schemas')) : []),
	].sort();
	const schemas = classify(shippedSchemas, detection.openspec.schemas, detection.openspec.schemaHashes, detection.prior?.schemas);

	const agentFilesIn = (dir) =>
		existsSync(dir) ? readdirSync(dir).filter((f) => f.endsWith('.md')) : [];
	const shippedAgents = [
		...agentFilesIn(join(levelDir, 'agents')),
		...(appleActive ? agentFilesIn(join(appleDir, 'agents')) : []),
	].sort();
	const agents = classify(shippedAgents, detection.agents?.files, detection.agents?.hashes, detection.prior?.agents);

	const configExists = Boolean(detection.openspec.configPath);

	const missing = NEEDED_WORKFLOWS.filter((w) => !detection.openspecCli.workflows.includes(w));
	if (missing.length > 0) {
		warnings.push(
			`This machine's OpenSpec profile ("${profileLabel(detection.openspecCli.profile)}") does not include ` +
				`the ${missing.join(', ')} workflow(s) this level's flow uses. Fix it by running ` +
				'`openspec config profile`, choosing the custom option, and selecting those workflows ' +
				'individually — the CLI has one preset, `core`, and it does not include them — then ' +
				'`openspec update` in this project. `openspec config profile` is machine-wide: it changes the ' +
				"profile for every project on this machine, not just this one, so setup never runs it for you — " +
				"you'll need to run it yourself.",
		);
	}

	const humanSteps = [];
	if (MATTPOCOCK_LEVELS.has(level) && !detection.humanArtifacts.issueTracker) {
		humanSteps.push(
			'Run `/mattpocock-skills:setup-matt-pocock-skills` — an interview only you can answer. It writes docs/agents/issue-tracker.md.',
		);
	}
	if (detection.web && !detection.humanArtifacts.product) {
		humanSteps.push('Run `/impeccable init` — gathers design context and writes PRODUCT.md and DESIGN.md.');
	}
	if (detection.apple?.app && !detection.apple.xcodeMcpConfigured) {
		humanSteps.push(
			'Enable "Allow external agents to use Xcode tools" in Xcode → Settings → Intelligence, then run ' +
				'`claude mcp add --transport stdio xcode -- xcrun mcpbridge`. Verification then drives Xcode ' +
				'directly; without it, xcode-loop falls back to headless xcodebuild.',
		);
	}
	if (plugins.install.length > 0) {
		humanSteps.push('Run `/reload-plugins` to activate the newly installed plugins in this session.');
	}
	if (plugins.install.includes(OUTPUT_STYLE_PLUGIN)) {
		humanSteps.push(
			'Switch your output style: after the reload, select `controlled-english` under `/config`. It ships ' +
				'with the meta-skills plugin, so it only appears once that plugin is active, and nothing selects ' +
				'it for you — it changes the register of every reply in this repository.',
		);
	}

	return {
		mode: detection.priorRun ? 'reconcile' : 'fresh',
		level,
		web: detection.web,
		apple: { app: Boolean(detection.apple?.app), swift: Boolean(detection.apple?.swift) },
		// I1/legacy-cleanup: `openspec init` over an existing directory has a legacy-cleanup path,
		// so this is true only when openspec/ is genuinely absent — never inferred any other way.
		openspecInit: !detection.openspec.present,
		schemas,
		agents,
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

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
	// A pipeline consumer must never receive JSON it could mistake for a real plan, so nothing
	// is written to stdout unless buildPlan actually succeeds — every failure goes to stderr
	// only, with a non-zero exit. But a user typo and a genuine defect are not the same problem:
	// an UnknownLevelError is fully explained by its message, while any other error is a bug in
	// this module that someone will need to localise, so it gets its full stack instead.
	try {
		const stdinDetection = JSON.parse(readFileSync(0, 'utf8'));
		const level = process.argv[2] ?? 'minimal';
		const plan = buildPlan(stdinDetection, { level });
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
