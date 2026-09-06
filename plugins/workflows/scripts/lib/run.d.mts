// Hand-written ambient declarations for run.mjs, kept in sync manually.
// This file exists only so tsc --noEmit (run in CI via `bun run typecheck`)
// can resolve types for the exported functions.

export interface RunResult {
	status: number;
	stdout: string;
	stderr: string;
}

export interface RunOptions {
	/** Working directory for the child. `undefined` inherits this process's, as `spawnSync` does. */
	cwd?: string;
}

/**
 * The single subprocess contract for this plugin: never throws, surfaces `spawnSync`'s
 * `error` (ENOENT and friends) as `stderr` with a non-zero status, sets
 * `OPENSPEC_TELEMETRY=0`/`DO_NOT_TRACK=1` on every spawn, and resolves the literal command
 * name `openspec` through `WORKFLOWS_OPENSPEC` when it is set.
 */
export function runCommand(cmd: string, args: string[], options?: RunOptions): RunResult;
