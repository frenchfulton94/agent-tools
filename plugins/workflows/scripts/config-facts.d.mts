// Hand-written ambient declarations for config-facts.mjs, kept in sync manually.
// This file exists only so tsc --noEmit (run in CI via `bun run typecheck`)
// can resolve types for the exported functions.

/** The `spec-driven` schema's artifact ids, unioned in unconditionally. */
export const BUILTIN_ARTIFACT_IDS: string[];

/** OpenSpec's real `context:` cap in bytes: `50 * 1024` (dist/core/project-config.js `MAX_CONTEXT_SIZE`). */
export const CONTEXT_CAP_BYTES: number;

export interface RunResult {
	status: number;
	stdout: string;
	stderr: string;
}

export type ConfigFactsRunner = (cmd: string, args: string[], cwd?: string) => RunResult;

/**
 * The real subprocess runner. Resolves the `openspec` binary from `WORKFLOWS_OPENSPEC`
 * (falling back to `openspec` on PATH) and sets `OPENSPEC_TELEMETRY=0` and
 * `DO_NOT_TRACK=1` on every spawn. Never throws.
 */
export function defaultRun(cmd: string, args: string[], cwd?: string): RunResult;

export interface ArtifactIdsOptions {
	/** Injectable subprocess runner, for testing without shelling out to `openspec`. */
	run?: ConfigFactsRunner;
}

export interface ArtifactIdsResult {
	ok: boolean;
	/** The artifact-id union on success; `null` on any failure — never a plausible empty Set. */
	ids: Set<string> | null;
	/** A short, human-readable reason on failure; `null` on success. */
	error: string | null;
}

/**
 * The authoritative artifact-id union for `repoRoot`, from `openspec schemas --json`
 * only, plus `BUILTIN_ARTIFACT_IDS`. Returns `{ ok: false, ids: null, error }` — never an
 * empty Set — when the CLI fails, returns unparseable output, or returns JSON that is not
 * the documented bare array.
 */
export function artifactIds(repoRoot: string, options?: ArtifactIdsOptions): ArtifactIdsResult;

/**
 * A timestamped backup path for `configPath`, guaranteed unique across repeated calls in
 * this process — including two calls within the same millisecond.
 */
export function backupPath(configPath: string): string;

export type RulesMap = Record<string, string[]>;

export interface ClassifiedRules {
	carried: RulesMap;
	unmatched: RulesMap;
}

/**
 * Splits `userRules` into `carried` (artifact id is in `knownIds`) and `unmatched` (it is
 * not). `knownIds` must be a real `Set` or array of strings — passing `null`/`undefined`
 * throws rather than being treated as an empty union.
 */
export function classifyRules(userRules: RulesMap | null | undefined, knownIds: Set<string> | string[]): ClassifiedRules;

/** The config text a level's previous release shipped: `retired.json`'s `config`. */
export interface RetiredConfig {
	/** Artifact id → rule strings. */
	rules?: RulesMap;
	/** Operation → `operations.<op>.guidance` strings. */
	guidance?: RulesMap;
}

export interface KeptAndDropped {
	kept: RulesMap;
	dropped: RulesMap;
}

export interface SplitRetiredConfigResult {
	rules: KeptAndDropped;
	guidance: KeptAndDropped;
}

/**
 * Splits a parsed `rules:` map and `operations.*.guidance` map into `kept` and `dropped`
 * against `retired`. A line is dropped only when it equals shipped text under the same key
 * after trimming; a missing `retired` drops nothing. A key whose lines are all dropped is
 * absent from `kept`.
 */
export function splitRetiredConfig(
	config: { rules?: RulesMap | null; guidance?: RulesMap | null } | undefined,
	retired: RetiredConfig | null | undefined,
): SplitRetiredConfigResult;

/**
 * Renders `unmatched` as a trailing YAML comment block (every rule's text JSON-encoded
 * onto one line, so an embedded newline cannot break a line out of the comment). Returns
 * `''` when `unmatched` has no keys.
 */
export function commentBlock(unmatched: RulesMap | null | undefined): string;

export interface ContextSizeResult {
	bytes: number;
	capBytes: number;
	overCap: boolean;
}

/** `text`'s UTF-8 byte length against `CONTEXT_CAP_BYTES`. */
export function contextSize(text: string | null | undefined): ContextSizeResult;
