// Hand-written ambient declarations for settings.mjs, kept in sync manually.
// This file exists only so tsc --noEmit (run in CI via `bun run typecheck`)
// can resolve types for the exported functions.

export interface SettingsManifest {
	enabledPlugins?: Record<string, boolean>;
	extraKnownMarketplaces?: Record<string, object>;
}

export interface MergedManifest {
	enabledPlugins: Record<string, boolean>;
	extraKnownMarketplaces: Record<string, object>;
}

export interface PlanInstallsResult {
	install: string[];
	disable: string[];
	skip: Array<{ id: string; reason: string }>;
	marketplaces: Array<{ name: string; source?: object; [key: string]: any }>;
}

export interface ReadSettingsFileResult {
	settings: object;
	status: 'absent' | 'ok' | 'unparseable';
}

export function readSettingsFile(repoRoot: string): ReadSettingsFileResult;
export function decidedPlugins(settings: object): Set<string>;
export function mergeManifests(manifests: SettingsManifest[]): MergedManifest;
export function planInstalls(merged: MergedManifest, decided: Set<string>): PlanInstallsResult;
