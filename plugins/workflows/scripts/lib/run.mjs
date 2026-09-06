import { spawnSync } from 'node:child_process';

/**
 * The one subprocess runner every script in this plugin spawns through.
 *
 * There were four of these before this module existed — `detect.mjs`, `verify.mjs`,
 * `config-facts.mjs`, and `install-plugins.mjs` — with three different error policies
 * between them, two of them byte-identical, and `install-plugins.mjs` as the outlier that
 * had neither a try/catch nor an `r.error` check: a missing `claude` binary surfaced there
 * as the string `"install failed"` with the real ENOENT discarded, which is the least
 * useful thing this plugin can tell a user whose install did not happen. One contract:
 *
 * - **Never throws.** `spawnSync` can throw synchronously (a bad `cwd`, an unspawnable
 *   binary), and every call site in this plugin treats the result as data. A throw here
 *   would blow past checks already computed — in `verify()` that means discarding I1.
 * - **`r.error` is surfaced, not discarded.** `spawnSync` reports ENOENT in `r.error` with
 *   a `null` status, so a runner that only looks at `status` reports "the command failed"
 *   and loses the one detail that explains why.
 * - **Telemetry opt-out on every spawn.** Every `openspec` subcommand runs a preAction
 *   hook that writes `~/.config/openspec/config.json` on first use and POSTs to a
 *   third-party analytics endpoint on every use; `OPENSPEC_TELEMETRY=0` and
 *   `DO_NOT_TRACK=1` are the CLI's documented opt-outs. They are set on *every* spawn,
 *   not just the ones that happen to invoke `openspec`, so the plugin's own claim
 *   (README: "Every `openspec` invocation this plugin makes sets ...") cannot be made
 *   false by a call site forgetting them.
 * - **`WORKFLOWS_OPENSPEC` resolves the `openspec` binary**, so a fixture suite can pin an
 *   exact CLI version instead of silently exercising whatever is on the machine running
 *   the test. Scoped to the literal command name `openspec`: a call to `claude`, `bun`, or
 *   anything else is never redirected through it.
 * - **`cwd` is optional.** `undefined` means "inherit this process's" — the same thing
 *   passing no `cwd` to `spawnSync` has always meant.
 */
export function runCommand(cmd, args, { cwd } = {}) {
	const resolved = cmd === 'openspec' ? process.env.WORKFLOWS_OPENSPEC || 'openspec' : cmd;
	try {
		const r = spawnSync(resolved, args, {
			cwd,
			encoding: 'utf8',
			stdio: ['ignore', 'pipe', 'pipe'],
			env: { ...process.env, OPENSPEC_TELEMETRY: '0', DO_NOT_TRACK: '1' },
		});
		if (r.error) throw r.error;
		return { status: r.status ?? 1, stdout: r.stdout ?? '', stderr: r.stderr ?? '' };
	} catch (err) {
		return { status: 1, stdout: '', stderr: err instanceof Error ? err.message : String(err) };
	}
}
