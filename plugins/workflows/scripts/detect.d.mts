// Hand-written ambient declarations for detect.mjs, kept in sync manually.
// This file exists only so tsc --noEmit (run in CI via `bun run typecheck`)
// can resolve types for the exported functions.
//
// `PriorRun` is imported rather than restated: `detection.prior` is literally
// `readRecord()`'s return value, and two hand-written copies of a shape one module owns
// would drift the first time the record's format changes.

import type { PriorRun } from './record.mjs';

export interface OpenspecDetection {
	present: boolean;
	hasSpecs: boolean;
	hasChanges: boolean;
	schemas: string[];
	/** `{ schemaName: hash }` for every directory in `schemas`, for the ownership check in plan.mjs. */
	schemaHashes: Record<string, string>;
	configPath: string | null;
	/**
	 * `{ changeName: schemaName | null }` for each open change (every directory under
	 * openspec/changes except `archive`), read from its `.openspec.yaml`. `null` means the
	 * change names no schema, so plan.mjs keeps every retired schema it might be using.
	 */
	changeSchemas: Record<string, string | null>;
}

export interface AgentsDetection {
	/** `*.md` files directly under `.claude/agents/`, sorted. */
	files: string[];
	/** `{ fileName: hash }` for every entry in `files`. */
	hashes: Record<string, string>;
}

export interface SettingsDetection {
	present: boolean;
	status: 'absent' | 'ok' | 'unparseable';
	decided: string[];
}

export interface RuntimeDetection {
	node: string;
	bun: string | null;
}

export interface OpenspecCliDetection {
	version: string | null;
	/**
	 * The machine profile as the CLI itself would resolve it (`config.profile || 'core'`),
	 * or `null` when the machine config is absent or unreadable. A malformed config holding
	 * a truthy non-string `profile` is reported verbatim rather than coerced, so this is a
	 * string in every well-formed case but is not guaranteed to be one at runtime.
	 */
	profile: string | null;
	workflows: string[];
}

export interface HumanArtifactsDetection {
	issueTracker: boolean;
	product: boolean;
	design: boolean;
	tools: boolean;
}

export interface Detection {
	repoRoot: string;
	web: boolean;
	webSignals: string[];
	openspec: OpenspecDetection;
	agents: AgentsDetection;
	settings: SettingsDetection;
	runtime: RuntimeDetection;
	openspecCli: OpenspecCliDetection;
	humanArtifacts: HumanArtifactsDetection;
	/** `.claude/workflows.json` exists — this repo has been set up before, whatever the file says. */
	priorRun: boolean;
	/** What that file says a previous run installed, or `null` when it is absent or untrustworthy. */
	prior: PriorRun | null;
}

export type SubprocessRunner = (cmd: string, args: string[]) => string | null;

export interface DetectOptions {
	/** Injectable subprocess runner, for testing the machine-profile branch without shelling out. Defaults to the real one. */
	run?: SubprocessRunner;
}

/**
 * The real subprocess runner. Sets OPENSPEC_TELEMETRY=0 and DO_NOT_TRACK=1 on every
 * spawned child. Exported so tests can prove those env vars reach a spawned process
 * without needing to spawn `openspec` itself.
 */
export function defaultRun(cmd: string, args: string[]): string | null;

/**
 * The OpenSpec CLI's fixed workflow list for its `core` profile (mirrors
 * dist/core/profiles.js at v1.8.0). Exported so tests can assert against it without
 * duplicating the literal.
 */
export const CORE_WORKFLOWS: string[];

/**
 * Absolute path to the machine-level OpenSpec config, mirroring the CLI's
 * `getGlobalConfigDir`. Exported so tests can assert the win32 fallbacks by path.
 */
export function machineConfigPath(): string;

export function detect(repoRoot: string, options?: DetectOptions): Detection;
