#!/usr/bin/env bun
/**
 * audit.ts — read-only audit of a Vite project.
 *
 * Usage: bun scripts/audit.ts [project-dir]
 *        bun scripts/audit.ts --help
 *
 * Prints a single JSON object to stdout (diagnostics go to stderr):
 *   viteVersionRange   raw semver range from package.json (or null)
 *   viteMajor          parsed major version number (or null)
 *   docsBaseUrl        the vite docs site matching that major
 *   configFile         detected vite config filename (or null)
 *   frameworkPlugins   known @vitejs/* or framework vite plugins found in deps
 *   envFiles           .env* files present in the project root
 *   gitignoreCoversLocal  true if .gitignore matches *.local env files
 *   tsconfig           { found, isolatedModules, viteClientTypes } (nulls if absent)
 *   suspiciousViteVars VITE_-prefixed var names in .env* files that look like secrets
 *   warnings           human-readable issues worth fixing
 *
 * Exit codes: 0 = audit completed (warnings possible), 1 = bad arguments,
 *             2 = directory unreadable or not a Node project.
 * No network access, no writes, no interactive prompts.
 */
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const args: string[] = Bun.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
	process.stdout.write(
		'Usage: bun scripts/audit.ts [project-dir]\n' +
			'Read-only audit of a Vite project. Prints JSON to stdout.\n' +
			'Exit codes: 0 ok, 1 bad args, 2 unreadable/not a Node project.\n',
	);
	process.exit(0);
}
if (args.length > 1) {
	process.stderr.write('Error: expected at most one argument (project directory).\n');
	process.stderr.write('Usage: bun scripts/audit.ts [project-dir]\n');
	process.exit(1);
}

const dir = resolve(args[0] ?? '.');
const warnings: string[] = [];

type Json = Record<string, unknown>;

/** Narrow an unknown JSON value to an object; anything else becomes {}. */
function obj(v: unknown): Json {
	return v !== null && typeof v === 'object' && !Array.isArray(v) ? (v as Json) : {};
}

function readJson(path: string): Json | null {
	try {
		// Strip // and /* */ comments so tsconfig (JSONC) parses too.
		const raw = readFileSync(path, 'utf8');
		const noComments = raw
			.replace(/\/\*[\s\S]*?\*\//g, '')
			.replace(/^\s*\/\/.*$/gm, '')
			.replace(/,(\s*[}\]])/g, '$1');
		return obj(JSON.parse(noComments));
	} catch {
		return null;
	}
}

// --- package.json -----------------------------------------------------------
const pkgPath = join(dir, 'package.json');
if (!existsSync(pkgPath)) {
	process.stderr.write(`Error: no package.json in ${dir} — not a Node project or wrong path.\n`);
	process.stderr.write('Pass the project root, e.g.: bun scripts/audit.ts ./my-app\n');
	process.exit(2);
}
const pkg = readJson(pkgPath) ?? {};
const allDeps: Json = { ...obj(pkg.dependencies), ...obj(pkg.devDependencies) };

const viteVersionRange = allDeps.vite ?? null;
let viteMajor: number | null = null;
if (viteVersionRange) {
	const m = String(viteVersionRange).match(/(\d+)/);
	if (m?.[1]) viteMajor = Number(m[1]);
} else {
	warnings.push('vite is not in dependencies/devDependencies — is this a Vite project?');
}

// Docs are versioned per major; pointing at the wrong major's docs causes
// wrong option names (e.g. rollupOptions vs rolldownOptions).
const docsBaseUrl =
	viteMajor == null || viteMajor >= 8 ? 'https://vite.dev' : `https://v${viteMajor}.vite.dev`;

// --- config file ------------------------------------------------------------
const configCandidates = [
	'vite.config.ts',
	'vite.config.js',
	'vite.config.mts',
	'vite.config.mjs',
	'vite.config.cts',
	'vite.config.cjs',
];
const configFile = configCandidates.find((f) => existsSync(join(dir, f))) ?? null;
if (!configFile) warnings.push('No vite.config.* found in project root.');

// --- framework plugins ------------------------------------------------------
const knownPlugins = [
	'@vitejs/plugin-react',
	'@vitejs/plugin-react-swc',
	'@vitejs/plugin-rsc',
	'@vitejs/plugin-vue',
	'@vitejs/plugin-vue-jsx',
	'@vitejs/plugin-legacy',
	'@sveltejs/vite-plugin-svelte',
	'vite-plugin-solid',
	'@preact/preset-vite',
];
const frameworkPlugins = knownPlugins.filter((p) => p in allDeps);

// --- env files --------------------------------------------------------------
let entries: string[] = [];
try {
	entries = readdirSync(dir);
} catch {
	process.stderr.write(`Error: cannot read directory ${dir}.\n`);
	process.exit(2);
}
const envFiles = entries.filter((f) => f === '.env' || f.startsWith('.env.')).sort();

let gitignoreCoversLocal = false;
const gitignorePath = join(dir, '.gitignore');
if (existsSync(gitignorePath)) {
	const gi = readFileSync(gitignorePath, 'utf8');
	gitignoreCoversLocal = /^\s*(\*\.local|\.env\*?\.local|\.env\.local)\s*$/m.test(gi);
}
if (envFiles.some((f) => f.endsWith('.local')) && !gitignoreCoversLocal) {
	warnings.push(
		'.env*.local files exist but .gitignore does not cover *.local — risk of committing secrets.',
	);
}

// VITE_ vars are inlined into the client bundle, so secret-looking names are a
// real leak, not a style issue.
const secretPattern = /(secret|password|passwd|private|token|api_?key|credential)/i;
const suspiciousViteVars: string[] = [];
for (const f of envFiles) {
	const content = readFileSync(join(dir, f), 'utf8');
	for (const line of content.split('\n')) {
		const m = line.match(/^\s*(VITE_[A-Z0-9_]+)\s*=/i);
		if (m?.[1] && secretPattern.test(m[1])) suspiciousViteVars.push(`${f}: ${m[1]}`);
	}
}
if (suspiciousViteVars.length) {
	warnings.push(
		'VITE_-prefixed vars with secret-like names found — VITE_ vars are bundled into client code and exposed to every visitor.',
	);
}

// --- tsconfig ---------------------------------------------------------------
const tsconfig: {
	found: boolean;
	isolatedModules: boolean | null;
	viteClientTypes: boolean | null;
} = { found: false, isolatedModules: null, viteClientTypes: null };
// Vite templates commonly split tsconfig.app.json from tsconfig.node.json.
const tsCandidates = ['tsconfig.app.json', 'tsconfig.json'].filter((f) => existsSync(join(dir, f)));
if (tsCandidates.length) {
	tsconfig.found = true;
	const ts = readJson(join(dir, tsCandidates[0] as string));
	const co = obj(ts?.compilerOptions);
	// tsconfig values are booleans in practice; `=== true` preserves the original
	// `co.isolatedModules ?? false` result while satisfying the declared boolean type.
	tsconfig.isolatedModules = co.isolatedModules === true;
	const types = co.types ?? [];
	let hasViteClient = Array.isArray(types) && types.includes('vite/client');
	if (!hasViteClient) {
		// also accept the triple-slash reference convention
		for (const f of entries.filter((e) => e.endsWith('.d.ts'))) {
			if (readFileSync(join(dir, f), 'utf8').includes('vite/client')) hasViteClient = true;
		}
		const srcEnv = join(dir, 'src', 'vite-env.d.ts');
		if (existsSync(srcEnv) && readFileSync(srcEnv, 'utf8').includes('vite/client'))
			hasViteClient = true;
	}
	tsconfig.viteClientTypes = hasViteClient;
	if (tsconfig.isolatedModules !== true)
		warnings.push(
			'tsconfig: isolatedModules is not true — Vite transpiles per-file; TS should warn about incompatible patterns.',
		);
	if (!hasViteClient)
		warnings.push(
			'tsconfig: vite/client types not referenced — asset imports and import.meta.env will be untyped.',
		);
}

process.stdout.write(
	`${JSON.stringify(
		{
			configFile,
			docsBaseUrl,
			envFiles,
			frameworkPlugins,
			gitignoreCoversLocal,
			projectDir: dir,
			suspiciousViteVars,
			tsconfig,
			viteMajor,
			viteVersionRange,
			warnings,
		},
		null,
		2,
	)}\n`,
);
