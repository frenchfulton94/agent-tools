import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { isMain } from './lib/cli.mjs';
import { runCommand } from './lib/run.mjs';
import { decidedPlugins, readSettingsFile } from './lib/settings.mjs';
import { hashEntry } from './lib/tree.mjs';
import { readRecord } from './record.mjs';

const WEB_DEPS = [
	'react', 'vue', 'svelte', '@sveltejs/kit', 'next', 'nuxt', 'astro',
	'vite', 'tailwindcss', '@angular/core', 'solid-js', 'remix',
];

/**
 * Detection's runner: `runCommand` (lib/run.mjs) narrowed to the only answer detection
 * ever wants — trimmed stdout on success, `null` on any failure, because every caller
 * here is asking "is this binary present, and what does it say its version is?" and has
 * nothing to do with a failure's detail. The shared runner owns the parts that must not
 * differ between scripts: never throwing, surfacing `spawnSync`'s `error`, and setting
 * the telemetry opt-outs on every spawn (see lib/run.mjs).
 *
 * Exported so tests can prove those env vars actually reach a spawned child, without
 * needing to spawn `openspec` itself.
 */
export function defaultRun(cmd, args) {
	const r = runCommand(cmd, args);
	return r.status === 0 ? r.stdout.trim() : null;
}

function webSignals(repoRoot) {
	const signals = [];
	const pkgPath = join(repoRoot, 'package.json');
	if (existsSync(pkgPath)) {
		try {
			const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
			const deps = { ...(pkg.dependencies ?? {}), ...(pkg.devDependencies ?? {}) };
			for (const d of WEB_DEPS) if (d in deps) signals.push(`dependency:${d}`);
		} catch {
			// A malformed package.json is not a web signal; the plan reports the repo as non-web.
		}
	}
	for (const marker of ['index.html', 'public/index.html', 'src/routes', 'app/page.tsx']) {
		if (existsSync(join(repoRoot, marker))) signals.push(`path:${marker}`);
	}
	return signals;
}

/**
 * Two tiers, consumed separately by plan.mjs: app signals gate the advanced-level
 * Apple content; any signal at all gates the apple plugin manifest. The xcodeproj
 * scan goes one directory deep (monorepos put the app in ios/ or apps/) and no
 * deeper — node_modules alone makes a full walk unaffordable, and the skip list
 * below is why a vendored fixture can never masquerade as the user's app.
 */
const APPLE_SCAN_SKIP = new Set(['node_modules']);

function appleSignals(repoRoot) {
	const signals = [];
	const bundles = (dir) =>
		dirNames(dir).filter((n) => n.endsWith('.xcodeproj') || n.endsWith('.xcworkspace'));
	for (const name of bundles(repoRoot)) signals.push(`app:${name}`);
	for (const sub of dirNames(repoRoot)) {
		if (sub.startsWith('.') || APPLE_SCAN_SKIP.has(sub)) continue;
		for (const name of bundles(join(repoRoot, sub))) signals.push(`app:${sub}/${name}`);
	}
	if (existsSync(join(repoRoot, 'Project.swift'))) signals.push('app:Project.swift');
	if (existsSync(join(repoRoot, 'Tuist'))) signals.push('app:Tuist');
	if (existsSync(join(repoRoot, 'project.yml'))) signals.push('app:project.yml');
	if (existsSync(join(repoRoot, 'Package.swift'))) signals.push('swift:Package.swift');
	return signals.sort();
}

/**
 * Read, never spawn: `claude mcp list` would be a subprocess for a question one JSON
 * read answers. An unparseable .mcp.json counts as "not configured" — the human step
 * this feeds errs toward telling the user how to connect Xcode, which costs nothing
 * when it turns out already done.
 */
function xcodeMcpConfigured(repoRoot) {
	const p = join(repoRoot, '.mcp.json');
	if (!existsSync(p)) return false;
	try {
		return Boolean(JSON.parse(readFileSync(p, 'utf8'))?.mcpServers?.xcode);
	} catch {
		return false;
	}
}

/**
 * `existsSync` only needs traversal permission on the parents; `readdirSync` needs read
 * permission on the directory itself. A permission-restricted directory can pass the
 * `existsSync` gate and then throw here — guarded so a locked-down `openspec/schemas`
 * degrades to an empty list instead of crashing a script whose whole job is to never
 * blow up.
 */
function dirNames(dir) {
	if (!existsSync(dir)) return [];
	try {
		return readdirSync(dir, { withFileTypes: true })
			.filter((e) => e.isDirectory())
			.map((e) => e.name)
			.sort();
	} catch {
		return [];
	}
}

/**
 * Fixed workflow list for the CLI's `core` profile. Mirrors the installed CLI's own
 * resolution. Verified against dist/core/global-config.js (DEFAULT_CONFIG) and
 * dist/core/profiles.js (CORE_WORKFLOWS) at v1.8.0. If the CLI changes these, this
 * drifts — which is the price of not shelling out to a command that writes and
 * transmits.
 */
export const CORE_WORKFLOWS = ['propose', 'explore', 'apply', 'update', 'sync', 'archive'];

/**
 * Mirrors the CLI's `getGlobalConfigDir` (dist/core/global-config.js) exactly:
 * `XDG_CONFIG_HOME` wins on every platform when set and non-empty; otherwise win32 uses
 * `%APPDATA%\openspec\config.json`, falling back to `<homedir>\AppData\Roaming\openspec\config.json`
 * when `APPDATA` is unset (the CLI has that same fallback, so a win32 machine without
 * `APPDATA` must not silently drop through to the POSIX path); every other platform uses
 * `~/.config/openspec/config.json`.
 *
 * Exported so a test can assert the win32-without-`APPDATA` fallback by inspecting the
 * resolved path: `homedir()` cannot be stubbed under this runtime (Bun's `os.homedir()`
 * ignores a runtime `HOME` change), so reading through that branch is not testable.
 */
export function machineConfigPath() {
	const xdg = process.env.XDG_CONFIG_HOME;
	if (xdg && xdg.length > 0) return join(xdg, 'openspec', 'config.json');
	if (process.platform === 'win32') {
		const appData = process.env.APPDATA;
		if (appData) return join(appData, 'openspec', 'config.json');
		return join(homedir(), 'AppData', 'Roaming', 'openspec', 'config.json');
	}
	return join(homedir(), '.config', 'openspec', 'config.json');
}

/**
 * The machine-level OpenSpec config, read straight off disk.
 *
 * Deliberately NOT `openspec config list`: every openspec subcommand runs a preAction
 * hook that writes ~/.config/openspec/config.json on first use (`maybeShowTelemetryNotice`)
 * and POSTs to a third-party analytics endpoint on every use (`trackCommand`). Detection
 * must do neither. Reading the file directly is genuinely read-only, and reading the
 * `workflows` array from parsed JSON also means there is no regex left to accidentally
 * scoop up an unrelated indented list from CLI output.
 *
 * Mirrors the CLI's own defaulting, not just its file format:
 *
 * - `profile` follows the CLI's `config.profile || 'core'`: absent, `null` or empty means
 *   `core` (the `DEFAULT_CONFIG` shape the CLI itself writes on a machine's first use,
 *   before the user has run `openspec config set-profile`). A truthy non-string is a
 *   malformed config, and is reported verbatim rather than coerced, because coercing it
 *   to `'core'` would show the user a profile their config does not contain.
 * - `workflows` mirrors `getProfileWorkflows` (dist/core/profiles.js): only `custom` reads
 *   the file's `workflows` array; every other value — `core`, and anything invalid — gets
 *   the fixed `CORE_WORKFLOWS`. This deliberately follows the CLI's *generation* path
 *   (core/update.js, core/init.js, core/shared/tool-detection.js), not its *display* path
 *   (`openspec config list`, which honours an explicit array for any profile). The two
 *   agree for the only valid values, `core` and `custom`, and diverge only for invalid
 *   ones — and this field exists to answer exactly one question, whether `/opsx:new` and
 *   `/opsx:continue` will exist on this machine, which generation decides.
 */
function openspecCli(run) {
	let profile = null;
	let workflows = [];
	try {
		const cfg = JSON.parse(readFileSync(machineConfigPath(), 'utf8'));
		profile = cfg.profile || 'core';
		workflows =
			profile === 'custom'
				? Array.isArray(cfg.workflows)
					? cfg.workflows.filter((w) => typeof w === 'string')
					: []
				: CORE_WORKFLOWS;
	} catch {
		// Absent or unreadable machine config: genuinely unknown, report nothing rather than guessing.
	}
	return { version: run('openspec', ['--version']), profile, workflows };
}

/** File names (not directories) directly under a directory, sorted; `[]` if unreadable. */
function fileNames(dir, suffix) {
	if (!existsSync(dir)) return [];
	try {
		return readdirSync(dir, { withFileTypes: true })
			.filter((e) => e.isFile() && e.name.endsWith(suffix))
			.map((e) => e.name)
			.sort();
	} catch {
		return [];
	}
}

/** `{ name: hash }` over `names`, each resolved to a path by `toPath`. */
function hashesFor(names, toPath) {
	const out = {};
	for (const name of names) out[name] = hashEntry(toPath(name));
	return out;
}

/**
 * `{ changeName: schemaName | null }` for every open change: each directory under
 * openspec/changes except `archive`. Read straight off `.openspec.yaml` rather than through
 * the CLI, for the same reason the machine config is: every subcommand writes and transmits.
 * Retirement (plan.mjs) needs one answer from this — does an open change still resolve
 * against a schema setup is about to offer for deletion — and `null` (no file, or no
 * `schema:` line) is "cannot tell", which plan.mjs treats as "it might".
 */
function openChangeSchemas(openspecDir) {
	const out = {};
	for (const name of dirNames(join(openspecDir, 'changes'))) {
		if (name === 'archive') continue;
		let schema = null;
		try {
			const match = readFileSync(join(openspecDir, 'changes', name, '.openspec.yaml'), 'utf8').match(
				/^schema:[ \t]*['"]?([^'"\s#]+)/m,
			);
			if (match) {
				// YAML null values: ~ and null yield null ('cannot tell').
				const value = match[1];
				schema = value === '~' || value === 'null' ? null : value;
			}
		} catch {
			// No .openspec.yaml: the change names no schema of its own.
		}
		out[name] = schema;
	}
	return out;
}

/**
 * `run` is injectable so tests can exercise the machine-profile branch without
 * shelling out. Every real call site defaults to `defaultRun`, so production
 * behaviour is unchanged; only tests pass a stub.
 */
export function detect(repoRoot, { run = defaultRun } = {}) {
	repoRoot = resolve(repoRoot);
	const settingsState = readSettingsFile(repoRoot);
	const settings = settingsState.settings;
	const openspecDir = join(repoRoot, 'openspec');
	const configYaml = join(openspecDir, 'config.yaml');
	const configYml = join(openspecDir, 'config.yml');
	const signals = webSignals(repoRoot);
	const appleSigs = appleSignals(repoRoot);
	const bun = run('bun', ['--version']);
	const schemas = dirNames(join(openspecDir, 'schemas'));
	const agentFiles = fileNames(join(repoRoot, '.claude', 'agents'), '.md');

	return {
		repoRoot,
		web: signals.length > 0,
		webSignals: signals,
		apple: {
			app: appleSigs.some((s) => s.startsWith('app:')),
			swift: appleSigs.length > 0,
			signals: appleSigs,
			xcodeMcpConfigured: xcodeMcpConfigured(repoRoot),
		},
		openspec: {
			present: existsSync(openspecDir),
			hasSpecs: existsSync(join(openspecDir, 'specs')),
			hasChanges: existsSync(join(openspecDir, 'changes')),
			schemas,
			// Hashed here, not in `plan.mjs`: the plan stays pure, and these are what let it
			// tell a schema this plugin installed and nobody has touched (safe to update on a
			// re-run) from one the user wrote or edited (never replaced without approval).
			schemaHashes: hashesFor(schemas, (name) => join(openspecDir, 'schemas', name)),
			configPath: existsSync(configYaml) ? configYaml : existsSync(configYml) ? configYml : null,
			changeSchemas: openChangeSchemas(openspecDir),
		},
		agents: {
			files: agentFiles,
			hashes: hashesFor(agentFiles, (name) => join(repoRoot, '.claude', 'agents', name)),
		},
		settings: {
			present: existsSync(join(repoRoot, '.claude', 'settings.json')),
			status: settingsState.status,
			decided: [...decidedPlugins(settings)].sort(),
		},
		runtime: {
			node: process.version,
			bun,
		},
		openspecCli: openspecCli(run),
		humanArtifacts: {
			issueTracker: existsSync(join(repoRoot, 'docs', 'agents', 'issue-tracker.md')),
			product: existsSync(join(repoRoot, 'PRODUCT.md')),
			design: existsSync(join(repoRoot, 'DESIGN.md')),
			tools: existsSync(join(repoRoot, 'TOOLS.md')),
		},
		priorRun: existsSync(join(repoRoot, '.claude', 'workflows.json')),
		// The prior run's own account of what it installed, or `null` when there is none we
		// can trust. `priorRun` stays a plain existence check — an unparseable record still
		// means this repo has been set up before (so the mode is `reconcile`), it just means
		// nothing in it can be claimed as ours to update.
		prior: readRecord(repoRoot),
	};
}

if (isMain(import.meta.url)) {
	console.log(JSON.stringify(detect(process.argv[2] ?? process.cwd()), null, 2));
}
