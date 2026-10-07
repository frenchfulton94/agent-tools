// Hand-written ambient declarations for cli.mjs, kept in sync manually.
// This file exists only so tsc --noEmit (run in CI via `bun run typecheck`)
// can resolve types for the exported functions.

export interface IsMainOptions {
	/** Defaults to `process.argv`. */
	argv?: string[];
	/** Defaults to `process.execArgv`. */
	execArgv?: string[];
}

/**
 * True only when `argv[1]` is the module at `moduleUrl` and node was not started with
 * `-e`, `-p`, a short group holding either, `--eval`, or `--print` (with or without
 * `=<code>`). Under an eval flag argv[1] is the first argument after the code, so a module
 * imported through `node -e … <module>` would otherwise run its CLI on import.
 */
export function isMain(moduleUrl: string, options?: IsMainOptions): boolean;
