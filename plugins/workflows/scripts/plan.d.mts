// Hand-written ambient declarations for plan.mjs, kept in sync manually.
// This file exists only so tsc --noEmit (run in CI via `bun run typecheck`)
// can resolve types for the exported functions.
//
// The detection shapes below are intentionally local to this file rather than imported
// from detect.d.mts (which follows the same standalone convention for settings.d.mts).
// They cover exactly the fields buildPlan reads, so a caller can pass either the full
// `Detection` from detect.mjs, or the smaller literal test fixtures in
// tests/workflows-plan.test.ts, without either side needing to import the other's types.

export interface PlanDetectionOpenspec {
	present: boolean;
	hasSpecs: boolean;
	hasChanges: boolean;
	schemas: string[];
	/**
	 * Optional so a caller (or a test fixture) built before the ownership model existed still
	 * type-checks. Absent hashes mean nothing can be proven to be ours, so every existing name
	 * is reported as a collision — the conservative answer, never a silent overwrite.
	 */
	schemaHashes?: Record<string, string>;
	configPath: string | null;
	/**
	 * `{ changeName: schemaName | null }` for each open change. Optional so an older detection
	 * still type-checks; absent is treated as "not checked", which keeps every retired schema.
	 */
	changeSchemas?: Record<string, string | null>;
}

export interface PlanDetectionAgents {
	files: string[];
	hashes?: Record<string, string>;
}

export interface PlanDetectionSettings {
	present: boolean;
	/** `unparseable` raises a leading plan warning: recorded choices cannot be honoured. */
	status?: 'absent' | 'ok' | 'unparseable';
	decided: string[];
}

/**
 * What a previous run recorded in `.claude/workflows.json`; see record.d.mts. Only the two
 * maps buildPlan reads are named — a full `PriorRun` (which also carries the level, version,
 * and date) satisfies this, matching this file's convention of describing exactly what
 * buildPlan consumes rather than importing the producer's type.
 */
export interface PlanDetectionPrior {
	schemas?: Record<string, string>;
	agents?: Record<string, string>;
}

export interface PlanDetectionRuntime {
	node: string;
	bun: string | null;
}

export interface PlanDetectionOpenspecCli {
	version: string | null;
	/**
	 * Declared `string | null` to match detect.d.mts's `Detection`, even though a
	 * hand-edited machine config can make the real runtime value a non-string (e.g. the
	 * number `42`). plan.mjs coerces with `String()` at the one place it renders this
	 * value, rather than trusting the type.
	 */
	profile: string | null;
	workflows: string[];
}

export interface PlanDetectionHumanArtifacts {
	issueTracker: boolean;
	product: boolean;
	design: boolean;
	tools: boolean;
}

export interface PlanDetection {
	repoRoot: string;
	web: boolean;
	webSignals: string[];
	openspec: PlanDetectionOpenspec;
	agents?: PlanDetectionAgents;
	settings: PlanDetectionSettings;
	runtime: PlanDetectionRuntime;
	openspecCli: PlanDetectionOpenspecCli;
	humanArtifacts: PlanDetectionHumanArtifacts;
	priorRun: boolean;
	prior?: PlanDetectionPrior | null;
}

export interface BuildPlanOptions {
	level: 'minimal' | 'standard' | 'advanced';
	/**
	 * TEST-ONLY seam for pinning buildPlan's own base->web->level composition order (not a
	 * general merge-semantics test hook -- mergeManifests is already pure and exported for
	 * that). A path with no levels/<level> directory THROWS: it used to degrade silently to an
	 * empty-but-plausible plan. No user-facing caller may ever pass this.
	 */
	payloadRoot?: string;
}

/** The only valid levels. Exported so callers share one source of truth instead of re-listing the names. */
export const LEVELS: string[];

/**
 * One shape for both schemas and agents: `copy` is new, `update` is ours to refresh (recorded
 * by a previous run and unmodified since), `collide` is the user's — reported, never replaced
 * without an individually approved overwrite.
 */
export interface PlanEntries {
	copy: string[];
	update: string[];
	collide: string[];
}

export interface PlanRetireKeep {
	name: string;
	reason: string;
}

/** `retire`: safe to offer for deletion at the gate. `keep`: left on disk, each with its reason. */
export interface PlanRetireSide {
	retire: string[];
	keep: PlanRetireKeep[];
}

/** Names this level no longer ships (`levels/<level>/retired.json`), split for the gate. */
export interface PlanRetirement {
	schemas: PlanRetireSide;
	agents: PlanRetireSide;
}

export interface PlanConfig {
	action: 'create' | 'replace';
	backupTo: string | null;
}

export interface PlanPluginsSkip {
	id: string;
	reason: string;
}

/**
 * Shape-compatible with `InstallPluginsMarketplace` (install-plugins.d.mts) — a `name`
 * required, everything else optional under an index signature — so a `Plan` type-checks
 * straight into `installPlugins(plan, ...)` with no cast at the call site. Declared
 * locally rather than imported, matching this file's convention for the detection shapes
 * above: a `Plan` is a data shape any caller can produce or consume, and neither script
 * needs to import the other's ambient types to agree on it. `object[]` previously stood
 * in here and was never checked against a real consumer until the two modules were
 * actually composed (tests/workflows-e2e.test.ts), which is exactly how the two
 * declarations drifted apart unnoticed.
 */
export interface PlanPluginsMarketplace {
	name: string;
	source?: { repo?: string; url?: string; [key: string]: unknown };
	[key: string]: unknown;
}

export interface PlanPlugins {
	install: string[];
	disable: string[];
	skip: PlanPluginsSkip[];
	marketplaces: PlanPluginsMarketplace[];
}

export interface Plan {
	mode: 'fresh' | 'reconcile';
	level: 'minimal' | 'standard' | 'advanced';
	web: boolean;
	openspecInit: boolean;
	schemas: PlanEntries;
	agents: PlanEntries;
	retire: PlanRetirement;
	config: PlanConfig;
	plugins: PlanPlugins;
	humanSteps: string[];
	probeChange: string;
	warnings: string[];
}

/** The name of the throwaway change verification creates and removes. */
export const PROBE_CHANGE: string;

/**
 * Thrown only for a bad `level` argument (a user typo), distinct from any other error
 * `buildPlan` might throw (a genuine defect). The CLI entry point catches this specifically
 * to print just its message, rather than a full stack.
 */
export class UnknownLevelError extends Error {}

/** Throws an UnknownLevelError when `options.level` is not one of `LEVELS`, before any disk read. */
export function buildPlan(detection: PlanDetection, options: BuildPlanOptions): Plan;
