import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { runCommand } from './lib/run.mjs';

/**
 * Default runner: the shared `runCommand` (lib/run.mjs). Injected in tests so no test ever
 * shells out to `claude`.
 *
 * This module used to have its own copy with neither a try/catch nor an `r.error` check,
 * which is exactly the case that matters here: `spawnSync` reports a missing `claude`
 * binary in `r.error` with a `null` status, so the old copy reported `"install failed"` and
 * discarded the ENOENT — the one detail that tells a user why nothing installed.
 */
export function defaultRun(cmd, args) {
	return runCommand(cmd, args);
}

/**
 * `claude plugin marketplace add owner/repo` clones over SSH (`git@github.com:...`), which
 * fails with `Permission denied (publickey)` on any machine without a GitHub SSH key —
 * common on a fresh setup, and unrelated to whether the marketplace is actually blocked.
 * A full `https://` URL clones anonymously instead, so a github-sourced marketplace is
 * added by URL rather than by the `owner/repo` shorthand the settings payload stores it
 * as. Anything else (a bare url, a local path, a plain name) passes through unchanged.
 */
function marketplaceSource(m) {
	if (m.source?.source === 'github' && m.source?.repo) return `https://github.com/${m.source.repo}.git`;
	return m.source?.repo ?? m.source?.url ?? m.name;
}

/**
 * Installs the plan's plugins at project scope.
 *
 * `claude plugin install` writes the enabledPlugins entry as part of installing, which
 * is what keeps I5 true — settings and reality cannot drift apart. The plan has already
 * removed anything the user decided (I3), so everything here is safe to install.
 *
 * A marketplace that will not add is an expected outcome under managed settings, so its
 * plugins are recorded as blocked and the rest of the run continues. The block reason is
 * the CLI's own stderr, not a guess — a managed-settings rejection and an SSH auth failure
 * fail the same `add` call, and only the real message tells them apart.
 */
export function installPlugins(plan, { run = defaultRun } = {}) {
	const installed = [];
	const blocked = [];
	const blockedMarketplaces = new Map();

	for (const m of plan.plugins.marketplaces) {
		const r = run('claude', ['plugin', 'marketplace', 'add', marketplaceSource(m), '--scope', 'project']);
		if (r.status !== 0) {
			blockedMarketplaces.set(m.name, (r.stderr || r.stdout || 'marketplace add failed').trim().split('\n')[0]);
		}
	}

	for (const id of plan.plugins.install) {
		const marketplace = id.split('@')[1];
		if (blockedMarketplaces.has(marketplace)) {
			blocked.push({
				id,
				reason: `marketplace ${marketplace} could not be added: ${blockedMarketplaces.get(marketplace)}`,
			});
			continue;
		}
		const r = run('claude', ['plugin', 'install', id, '--scope', 'project']);
		if (r.status === 0) installed.push(id);
		else blocked.push({ id, reason: (r.stderr || r.stdout || 'install failed').trim().split('\n')[0] });
	}

	for (const id of plan.plugins.disable) {
		run('claude', ['plugin', 'disable', id, '--scope', 'project']);
	}

	return { installed, blocked, skipped: plan.plugins.skip };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
	const plan = JSON.parse(readFileSync(0, 'utf8'));
	console.log(JSON.stringify(installPlugins(plan), null, 2));
}
