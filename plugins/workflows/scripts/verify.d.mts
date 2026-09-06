// Hand-written ambient declarations for verify.mjs, kept in sync manually.
// This file exists only so tsc --noEmit (run in CI via `bun run typecheck`)
// can resolve types for the exported functions.

export interface RunResult {
	status: number;
	stdout: string;
	stderr: string;
}

export type VerifyRunner = (cmd: string, args: string[], cwd?: string) => RunResult;

/**
 * The real subprocess runner. Resolves the `openspec` binary from `WORKFLOWS_OPENSPEC`
 * (falling back to `openspec` on PATH) and sets `OPENSPEC_TELEMETRY=0` and
 * `DO_NOT_TRACK=1` on every spawn.
 */
export function defaultRun(cmd: string, args: string[], cwd?: string): RunResult;

export interface VerifyBeforeHashes {
	specs: string;
	changes: string;
}

export interface VerifyOptions {
	/** Tree hashes captured before apply, from `hashTree`. */
	before: VerifyBeforeHashes;
	/** Rule text expected to appear in the probe's `openspec instructions --json` payload. */
	expectRules?: string[];
	/**
	 * Plugin ids (e.g. `"a@marketplace"`) expected to appear installed in
	 * `claude plugin list --json`. This is the **planned** set — `plan.plugins.install` — not
	 * what the install step reported installing: a blocked plugin never enters that second
	 * list, so the check could not fail for the case it exists to catch.
	 */
	expectPlugins?: string[];
	/** Injectable subprocess runner, for testing without shelling out to `openspec` or `claude`. */
	run?: VerifyRunner;
}

export interface VerifyCheck {
	name: string;
	ok: boolean;
	detail: string;
}

export interface VerifyResult {
	checks: VerifyCheck[];
	ok: boolean;
}

/**
 * Post-apply behavioural verification. Confirms `openspec/specs` and `openspec/changes`
 * are byte-for-byte unchanged (I1), that a throwaway probe change's
 * `openspec instructions --json` payload actually contains `context` and every rule in
 * `expectRules`, and that every id in `expectPlugins` appears installed in
 * `claude plugin list --json` (I5). The probe is created and removed by deleting its
 * directory directly — never via `openspec archive`, which would merge delta specs into
 * `openspec/specs/` and violate I1 — at both its active path and any archived path found
 * by suffix match; a survivor at either, or any thrown error along the way, is reported
 * as a failed check rather than allowed to propagate.
 */
export function verify(repoRoot: string, options: VerifyOptions): VerifyResult;
