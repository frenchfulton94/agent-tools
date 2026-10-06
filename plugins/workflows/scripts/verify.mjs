import { existsSync, readdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { isMain } from './lib/cli.mjs';
import { runCommand } from './lib/run.mjs';
import { hashTree } from './lib/tree.mjs';

const PROBE = 'zz-workflows-setup-probe';

/**
 * The real subprocess runner: `runCommand` (lib/run.mjs) with this module's `cwd`
 * argument, which every call here needs — an `openspec` command's answer depends on the
 * project it runs in. Everything else this module used to spell out for itself (never
 * throwing, surfacing `spawnSync`'s `error`, the telemetry opt-outs on every spawn, and
 * resolving `openspec` through `WORKFLOWS_OPENSPEC` so a fixture suite can pin a version)
 * is the shared runner's contract now — see lib/run.mjs for why each part is there.
 */
export function defaultRun(cmd, args, cwd) {
	return runCommand(cmd, args, { cwd });
}

/**
 * Never lets `run` — the injected one from a test, or `defaultRun` itself — throw out
 * of `verify()`. A throw here is a genuine defect in the runner, not evidence about the
 * consumer's repo, but if it escaped uncaught it would discard every check already
 * computed (including I1, which runs first) along with whatever check the throw
 * interrupted. Converting it to a normal failing result keeps that from happening: the
 * error message survives as the check's `detail` instead of being lost.
 */
function safeRun(run, cmd, args, cwd) {
	try {
		return run(cmd, args, cwd);
	} catch (err) {
		return { status: 1, stdout: '', stderr: err instanceof Error ? err.message : String(err) };
	}
}

/** First non-empty line of `stderr`, falling back to `stdout`, for a short failure message. */
function firstLine(result) {
	const text = (result.stderr || result.stdout || '').trim();
	return text.split('\n')[0] || 'no output';
}

/**
 * `openspec archive` prefixes the destination folder with the archive date
 * (`YYYY-MM-DD-<name>`), so a probe that ended up archived — by a stale build of this
 * module, or by hand mid-verification — is found by suffix match, not exact name.
 */
function archivedProbePaths(repoRoot) {
	const archiveDir = join(repoRoot, 'openspec', 'changes', 'archive');
	if (!existsSync(archiveDir)) return [];
	try {
		return readdirSync(archiveDir)
			.filter((name) => name.endsWith(PROBE))
			.map((name) => join(archiveDir, name));
	} catch {
		return [];
	}
}

/**
 * Post-apply assertions. Everything here checks behaviour or evidence, never mere
 * file presence — the failures this plugin can cause do not raise errors. A written
 * config proves nothing: OpenSpec `safeParse`s each field, silently drops what fails
 * validation while keeping the rest, and warns only to stderr, which an agent reading
 * piped output never sees. The only way to see what the model actually receives is to
 * ask OpenSpec itself, via a throwaway probe change and `openspec instructions --json`.
 */
export function verify(repoRoot, { before, expectRules = [], expectPlugins = [], run = defaultRun } = {}) {
	const checks = [];
	const add = (name, ok, detail = '') => checks.push({ name, ok, detail });

	// I1 — the two trees setup must never touch. Hashed before the probe below ever
	// touches disk, so the probe's own create/remove cycle can never register here even
	// if its cleanup were imperfect — this check is about what *apply* did, not verify.
	for (const [label, dir] of [['specs', 'specs'], ['changes', 'changes']]) {
		const after = hashTree(join(repoRoot, 'openspec', dir));
		add(`openspec/${label} unchanged (I1)`, after === before[label],
			after === before[label] ? '' : `hash changed: ${before[label]} -> ${after}`);
	}

	// The decisive check: does the config actually reach the model?
	try {
		const created = safeRun(run, 'openspec', ['new', 'change', PROBE], repoRoot);
		if (created.status !== 0) {
			// Reported here rather than falling through to the `instructions` call, whose
			// failure would then be blamed on the config: with no probe change to read, that
			// call cannot succeed, and its message describes the missing change rather than
			// the real cause. The previous version recorded this status in a variable nothing
			// read, and reported the generic `"instructions failed"` instead.
			add('config reaches the model', false, `openspec new change failed: ${firstLine(created)}`);
		} else {
			const out = safeRun(run, 'openspec', ['instructions', 'proposal', '--change', PROBE, '--json'], repoRoot);
			if (out.status !== 0) {
				add('config reaches the model', false, firstLine(out));
			} else {
				let payload = {};
				try {
					payload = JSON.parse(out.stdout);
				} catch {
					payload = {};
				}
				const hasContext = typeof payload.context === 'string' && payload.context.length > 0;
				const injected = JSON.stringify(payload.rules ?? []);
				const missing = expectRules.filter((r) => !injected.includes(r));
				add('config reaches the model', hasContext && missing.length === 0,
					!hasContext ? 'context absent from the instructions payload — OpenSpec dropped it'
						: missing.length ? `rules not injected: ${missing.join('; ')}` : '');
			}
		}
	} finally {
		// The probe must never be cleaned up with `openspec archive`: archive validates
		// and merges active delta specs into openspec/specs/ before moving the change
		// folder — exactly the mutation I1 exists to forbid, done by the module whose job
		// is to police I1. Deleting a directory this module created itself is not an
		// OpenSpec operation and touches nothing else, so that is all cleanup ever does —
		// at the probe's active path, and at any archived path a suffix match finds,
		// in case one is left over from a stale build or a hand-run archive.
		//
		// The probe must never outlive verification, however verification ended: this
		// runs in `finally` and, unlike the try block above, its own failure is always
		// captured as a check rather than allowed to throw — an exception here would
		// mask the error handled above and discard every check already computed.
		let removed = true;
		let detail = '';
		for (const dir of [join(repoRoot, 'openspec', 'changes', PROBE), ...archivedProbePaths(repoRoot)]) {
			if (!existsSync(dir)) continue;
			try {
				rmSync(dir, { recursive: true, force: true });
			} catch (err) {
				removed = false;
				detail = `LEFT BEHIND at ${dir} — remove it by hand (${err instanceof Error ? err.message : String(err)})`;
				continue;
			}
			if (existsSync(dir)) {
				removed = false;
				detail = detail || `LEFT BEHIND at ${dir} — remove it by hand`;
			}
		}
		add('probe change removed', removed, detail);
	}

	// I5 — everything the plan enables is actually installed. `expectPlugins` must be the
	// **planned** set (`plan.plugins.install`), never the set the install step reported as
	// installed: a plugin a managed marketplace blocked never enters that second list, so
	// feeding it here would reduce this to "what install said it installed is installed" —
	// a check that cannot fail for the one case it exists to catch. Exiting 0 only proves
	// the CLI ran, so this checks each expected id shows up installed in the parsed listing
	// and names the gaps. A blocked plugin failing here is the correct, reportable outcome.
	const listed = safeRun(run, 'claude', ['plugin', 'list', '--json'], repoRoot);
	if (listed.status !== 0) {
		add('plugins installed (I5)', false, 'could not read `claude plugin list --json`');
	} else {
		let entries = [];
		try {
			const parsed = JSON.parse(listed.stdout);
			entries = Array.isArray(parsed) ? parsed : [];
		} catch {
			entries = [];
		}
		const installed = new Set(entries.filter((p) => p && p.installed).map((p) => p.name));
		const missing = expectPlugins.filter((id) => !installed.has(id));
		add('plugins installed (I5)', missing.length === 0,
			missing.length === 0 ? '' : `not installed: ${missing.join(', ')}`);
	}

	return { checks, ok: checks.every((c) => c.ok) };
}

if (isMain(import.meta.url)) {
	const repoRoot = process.argv[2] ?? process.cwd();
	const result = verify(repoRoot, { before: { specs: '', changes: '' } });
	console.log(JSON.stringify(result, null, 2));
	process.exit(result.ok ? 0 : 1);
}
