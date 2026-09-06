import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

/**
 * Distinguishes "no settings file" from "settings file we could not parse". The caller
 * must be able to tell these apart: a corrupted file that still holds real decisions
 * must never be treated as holding none.
 */
export function readSettingsFile(repoRoot) {
	const path = join(repoRoot, '.claude', 'settings.json');
	if (!existsSync(path)) return { settings: {}, status: 'absent' };
	try {
		return { settings: JSON.parse(readFileSync(path, 'utf8')), status: 'ok' };
	} catch {
		return { settings: {}, status: 'unparseable' };
	}
}

/**
 * Every plugin id the user has already made a decision about — true or false alike.
 * `false` matters as much as `true`: `claude plugin install` would flip it.
 */
export function decidedPlugins(settings) {
	return new Set(Object.keys(settings?.enabledPlugins ?? {}));
}

/** Later manifests win per key. Marketplaces union. */
export function mergeManifests(manifests) {
	const enabledPlugins = {};
	const extraKnownMarketplaces = {};
	for (const m of manifests) {
		Object.assign(enabledPlugins, m?.enabledPlugins ?? {});
		Object.assign(extraKnownMarketplaces, m?.extraKnownMarketplaces ?? {});
	}
	return { enabledPlugins, extraKnownMarketplaces };
}

/**
 * Split the merged manifest against what the user already decided.
 * Anything already decided is skipped with a reason — never overwritten (I3).
 * Only marketplaces needed by a plugin we will actually install are returned.
 */
export function planInstalls(merged, decided) {
	const install = [];
	const disable = [];
	const skip = [];

	for (const [id, wanted] of Object.entries(merged.enabledPlugins)) {
		if (decided.has(id)) {
			skip.push({ id, reason: 'already decided in .claude/settings.json' });
			continue;
		}
		(wanted ? install : disable).push(id);
	}

	const needed = new Set(install.map((id) => id.split('@')[1]));
	const marketplaces = Object.entries(merged.extraKnownMarketplaces)
		.filter(([name]) => needed.has(name))
		.map(([name, value]) => ({ name, ...value }));

	return { install, disable, skip, marketplaces };
}
