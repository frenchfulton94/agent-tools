// Hand-written ambient declarations for record.mjs, kept in sync manually.
// This file exists only so tsc --noEmit (run in CI via `bun run typecheck`)
// can resolve types for the exported functions.

/** What a previous run installed: name -> hash of the content this plugin wrote. */
export interface PriorRun {
	level: string | null;
	version: string | null;
	date: string | null;
	schemas: Record<string, string>;
	agents: Record<string, string>;
}

export interface RecordRunOptions {
	level: string;
	/** Schema names this run owns: copied, updated, or an approved overwrite. */
	schemas?: string[];
	/** Subagent filenames this run owns, same rule. */
	agents?: string[];
	/**
	 * Names the plan offered for retirement. Each one that is gone from disk leaves the record;
	 * one the user kept is still on disk and stays recorded.
	 */
	retired?: { schemas?: string[]; agents?: string[] };
	/** Prefer `ownedFromPlan` to derive both from the approved plan rather than passing lists. */
	/** Defaults to this plugin's manifest version. */
	version?: string | null;
	/** Defaults to now. Injectable so a test can pin the timestamp. */
	date?: Date | string;
}

export interface RecordedRun {
	level: string;
	version: string | null;
	date: string;
	installed: { schemas: Record<string, string>; agents: Record<string, string> };
}

export function recordPath(repoRoot: string): string;
export function schemaPath(repoRoot: string, name: string): string;
export function agentPath(repoRoot: string, file: string): string;
export function pluginVersion(): string | null;

/** The record, or `null` when absent, unparseable, or not an object — never a partial guess. */
export function readRecord(repoRoot: string): PriorRun | null;

/**
 * Hashes each owned name from disk and merges it into `.claude/workflows.json`. Merged, not
 * replaced: the levels ship disjoint sets, so replacing orphans the previous level's files
 * and reports them as the user's on a later run.
 */
export function recordRun(repoRoot: string, options: RecordRunOptions): { path: string; record: RecordedRun };

export interface OwnedFromPlan {
	level: string;
	schemas: string[];
	agents: string[];
	/** `plan.retire.*.retire`, or empty lists for a plan built before retirement existed. */
	retired: { schemas: string[]; agents: string[] };
	/** Approved names the plan never listed as collisions — reported, and recorded for nothing. */
	ignored: string[];
}

/**
 * What a run owns, derived from the approved plan (`copy` + `update`) plus only those
 * `approved` names the plan itself lists as collisions. Throws a TypeError when `plan` is not
 * a plan, rather than recording an empty set. The CLI entry point reads the plan on stdin and
 * calls this, so no caller hands `recordRun` a list of its own devising.
 */
export function ownedFromPlan(plan: unknown, approved?: string[]): OwnedFromPlan;
