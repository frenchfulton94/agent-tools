// Hand-written ambient declarations for install-plugins.mjs, kept in sync manually.
// This file exists only so tsc --noEmit (run in CI via `bun run typecheck`)
// can resolve types for the exported functions.

export interface InstallPluginsMarketplace {
	name: string;
	source?: { repo?: string; url?: string; [key: string]: unknown };
	[key: string]: unknown;
}

export interface InstallPluginsSkip {
	id: string;
	reason: string;
}

export interface InstallPluginsPlan {
	plugins: {
		install: string[];
		disable: string[];
		skip: InstallPluginsSkip[];
		marketplaces: InstallPluginsMarketplace[];
	};
}

export interface RunResult {
	status: number;
	stdout: string;
	stderr: string;
}

export type InstallRunner = (cmd: string, args: string[]) => RunResult;

/**
 * The real runner (the shared `lib/run.mjs` contract). Exported so a test can prove a
 * missing binary comes back as a reported failure carrying the real spawn error, rather
 * than throwing or collapsing into a bare "install failed" — without any test ever
 * spawning the real `claude`.
 */
export function defaultRun(cmd: string, args: string[]): RunResult;

export interface InstallPluginsOptions {
	/** Injectable subprocess runner, for testing without shelling out to `claude`. Defaults to the real one. */
	run?: InstallRunner;
}

export interface InstallPluginsBlocked {
	id: string;
	reason: string;
}

export interface InstallPluginsResult {
	installed: string[];
	blocked: InstallPluginsBlocked[];
	skipped: InstallPluginsSkip[];
}

/**
 * Installs the plan's plugins at project scope. A marketplace or plugin that fails to
 * install is recorded in `blocked` and the run continues rather than throwing.
 */
export function installPlugins(plan: InstallPluginsPlan, options?: InstallPluginsOptions): InstallPluginsResult;
