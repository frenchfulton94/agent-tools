#!/usr/bin/env bun

/**
 * audit_marketplace.ts — sweep a plugin marketplace for the faults nothing else reports.
 *
 * Usage:
 *   bun audit_marketplace.ts [marketplace-root] [--strict] [--json] [--since <ref>] [--no-delegate]
 *
 * Exit codes: 0 = clean (warnings allowed unless --strict), 1 = errors found (or warnings
 * found with --strict), 2 = usage error.
 *
 * WHAT THIS DOES NOT DO, DELIBERATELY. It does not re-check registration, name/directory
 * agreement, version agreement, skill-name uniqueness, README links, or description identity
 * across the three files that carry it. A marketplace with a test suite already pins those —
 * in this repository, tests/marketplace-integrity.test.ts — and a second implementation of one
 * invariant disagrees with the first the next time either changes. That disagreement reads to a
 * maintainer as noise from an unreliable tool, which is worse than the coverage is worth. This
 * covers the complement and says so in its output.
 *
 * The complement, and why each item is in it:
 *
 * 1. THE VALIDATOR SWEEP. A marketplace that vendors validate_skill.ts and friends has a Tier 0
 *    lint it never runs. Before this script the four validators appeared only in the prose of
 *    docs/superpowers/plans/ — no test, no workflow, no package.json script — so each ran once,
 *    by hand, during the work that introduced the component it checks, and never again over the
 *    corpus as a whole. Running them is most of this script's value.
 *
 * 2. PLUGIN-LEVEL READMEs. Nothing loads them, so a rename leaves one wrong indefinitely and the
 *    next person to find out is a user running an install command that fails. plugins/marketing
 *    was titled `manhattan-brand-artifacts`, and printed install commands for that name, from the
 *    restructure in ecdd85c until this script found it.
 *
 * 3. THE README'S SKILLS COLUMN. A suite can pin the description cell and still parse past this
 *    one — marketplace-integrity.test.ts matches it with `[^|]*` — so a skill added without a
 *    README entry ships invisible to anyone browsing the repository.
 *
 * 4. VERSION-BUMP DISCIPLINE (--since). Users receive a change only when the version moves;
 *    otherwise `/plugin update` reports "already at the latest version" and serves the cached
 *    copy forever. .github/workflows/owasp-sync.yml states this rule in a PR body and nothing
 *    enforces it.
 *
 * 5. THE MARKETPLACE-LEVEL SCHEMA. Reserved names, `renames` targets and cycles, and `../` in a
 *    source path. `claude plugin validate .` is authoritative and should be preferred when the
 *    CLI is installed; this covers the same ground for environments without it. The reserved-name
 *    check is re-run by Claude Code on every load, not only when a marketplace is added, so a
 *    marketplace that worked yesterday can stop loading with no local change.
 *
 * A plugin that ships no README is not a finding. Plugins here ship them inconsistently, and
 * turning that into a warning would be inventing a rule rather than maintaining one.
 *
 * No dependencies beyond Bun itself.
 */

import { Glob } from 'bun';
import { existsSync, readdirSync, statSync } from 'node:fs';

const NAME_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;

/**
 * Marketplace names reserved for first-party Anthropic use. A third-party marketplace using one
 * is rejected as registered from an untrusted source. Kept as an explicit list rather than a
 * pattern because the reserved set includes vertical names — `healthcare`, `life-sciences` — that
 * no prefix rule would catch.
 */
const RESERVED_MARKETPLACE_NAMES = new Set([
	'claude-code-marketplace',
	'claude-code-plugins',
	'claude-plugins-official',
	'claude-plugins-community',
	'claude-community',
	'anthropic-marketplace',
	'anthropic-plugins',
	'agent-skills',
	'anthropic-agent-skills',
	'knowledge-work-plugins',
	'life-sciences',
	'claude-for-legal',
	'claude-for-financial-services',
	'financial-services-plugins',
	'first-party-plugins',
	'healthcare',
]);

interface MarketplaceEntry {
	name?: string;
	source?: string | Record<string, unknown>;
	version?: string;
}

interface Marketplace {
	name?: string;
	owner?: { name?: string };
	plugins?: MarketplaceEntry[];
	renames?: Record<string, string | null>;
	metadata?: { pluginRoot?: string };
}

/** A plugin resolved from a relative-path entry: the only kind whose files are in this repo. */
interface LocalPlugin {
	name: string;
	/** Absolute path to the plugin directory. */
	dir: string;
	/** Path relative to the marketplace root, for git and for messages. */
	rel: string;
}

type Severity = 'error' | 'warn' | 'note';

/**
 * `source` is what makes this machine-readable output worth having. A gate can require zero
 * `catalog` findings — the drift this script owns, all of it fixable — while leaving findings
 * delegated from `validate_skill.ts` and friends advisory, because those are style judgements
 * about existing content rather than regressions. Collapsing both into one exit code would force
 * a choice between a gate that blocks on a 340-line SKILL.md and no gate at all.
 */
interface Finding {
	message: string;
	severity: Severity;
	/** `catalog` for this script's own checks, otherwise the validator's filename. */
	source: string;
}

const findings: Finding[] = [];
const at = (severity: Severity) => (message: string, source = 'catalog') =>
	void findings.push({ message, severity, source });
const fail = at('error');
const warn = at('warn');
const note = at('note');
const bySeverity = (s: Severity): Finding[] => findings.filter((f) => f.severity === s);

/** Directory entries one level down, sorted. Absent parent reads as empty, not as a fault. */
const dirsIn = (parent: string): string[] =>
	existsSync(parent)
		? readdirSync(parent)
				.filter((d) => statSync(`${parent}/${d}`).isDirectory())
				.sort()
		: [];

/**
 * Resolve the entries whose source is a local relative path. Object sources (github, npm,
 * git-subdir) point outside this repository, so none of the file-level checks below apply to
 * them — they are counted and reported, not inspected.
 */
function localPlugins(root: string, m: Marketplace): { local: LocalPlugin[]; remote: number } {
	const pluginRoot = m.metadata?.pluginRoot?.replace(/^\.\//, '').replace(/\/+$/, '');
	const local: LocalPlugin[] = [];
	let remote = 0;

	for (const entry of m.plugins ?? []) {
		const { name, source } = entry;
		if (typeof source !== 'string') {
			remote++;
			continue;
		}
		if (!name) continue; // reported by the schema check below
		// `metadata.pluginRoot` is prepended only to sources that are not already `./`-relative,
		// which is the form it exists to shorten.
		const rel = source.startsWith('./')
			? source.slice(2)
			: pluginRoot
				? `${pluginRoot}/${source}`
				: source;
		local.push({ dir: `${root}/${rel}`, name, rel });
	}
	return { local, remote };
}

/** Schema faults that stop a marketplace loading, or that `claude plugin validate` would reject. */
function checkSchema(m: Marketplace): void {
	const name = m.name;
	if (!name) {
		fail('marketplace.json has no `name`');
	} else {
		if (!NAME_RE.test(name)) fail(`marketplace name "${name}" is not kebab-case`);
		if (RESERVED_MARKETPLACE_NAMES.has(name)) {
			fail(
				`marketplace name "${name}" is reserved for first-party use, so this marketplace is rejected as an untrusted source — and the check re-runs on every load, not only when it is added`,
			);
		}
	}

	if (!m.owner?.name) fail('marketplace.json has no `owner.name`, which is required');
	if (!Array.isArray(m.plugins)) {
		fail('marketplace.json has no `plugins` array');
		return;
	}

	for (const entry of m.plugins) {
		const label = entry.name ?? '(unnamed entry)';
		if (!entry.name) fail('a plugin entry has no `name`');
		else if (!NAME_RE.test(entry.name)) fail(`plugin name "${entry.name}" is not kebab-case`);

		if (entry.source === undefined) {
			fail(`"${label}" has no \`source\``);
		} else if (typeof entry.source === 'string') {
			// An installed plugin is copied into the plugin cache, so a source that escapes the
			// marketplace directory resolves during development and breaks after install.
			if (entry.source.includes('../')) {
				fail(`"${label}" has source "${entry.source}", which escapes the marketplace`);
			} else if (!entry.source.startsWith('./') && !m.metadata?.pluginRoot) {
				fail(
					`"${label}" has source "${entry.source}", which must start with "./" unless metadata.pluginRoot is set`,
				);
			}
		}
	}

	checkRenames(m);
}

/**
 * `renames` migrates users whose settings still carry a retired plugin name. It is append-only
 * history: a later rename adds an entry rather than editing the first, and Claude Code follows the
 * chain. A chain that loops, or that ends at a name which is neither listed nor `null`, is rejected
 * outright — and until then every affected user sees `plugin-not-found`.
 */
function checkRenames(m: Marketplace): void {
	const renames = m.renames;
	if (!renames) return;
	const listed = new Set((m.plugins ?? []).map((p) => p.name).filter(Boolean) as string[]);

	for (const from of Object.keys(renames)) {
		if (listed.has(from)) {
			fail(`"${from}" is both a live plugin and a \`renames\` key, so its name resolves twice`);
		}

		const seen = new Set<string>([from]);
		let cursor: string | null | undefined = renames[from];
		while (typeof cursor === 'string') {
			if (seen.has(cursor)) {
				fail(`\`renames\` forms a cycle starting at "${from}"`);
				break;
			}
			seen.add(cursor);
			if (listed.has(cursor)) break; // terminates at a live plugin
			if (!(cursor in renames)) {
				fail(
					`\`renames\` maps "${from}" to "${cursor}", which is neither a listed plugin nor another rename`,
				);
				break;
			}
			cursor = renames[cursor];
		}
	}
}

/**
 * A plugin's own README names a different plugin. The H1 check fires only on a bare kebab-case
 * token — `# manhattan-brand-artifacts` — because a prose title like `# Security plugin` is a
 * normal heading and flagging it would train maintainers to ignore this warning.
 */
function checkPluginReadme(p: LocalPlugin, text: string): void {
	const h1 = /^#\s+(.+)$/m.exec(text)?.[1]?.trim();
	if (h1 && NAME_RE.test(h1) && h1 !== p.name) {
		warn(`${p.rel}/README.md is titled "${h1}", but the plugin is named "${p.name}"`);
	}

	for (const [, named] of text.matchAll(/\/plugin\s+install\s+([a-z0-9-]+)@/g)) {
		if (named !== p.name) {
			warn(
				`${p.rel}/README.md tells users to install "${named}", which is not this plugin — the command fails`,
			);
		}
	}

	for (const [, path] of text.matchAll(/--plugin-dir\s+(\S+)/g)) {
		const leaf = path.replace(/\/+$/, '').split('/').pop();
		if (leaf && leaf !== p.name && NAME_RE.test(leaf)) {
			warn(`${p.rel}/README.md points --plugin-dir at "${leaf}", not at "${p.name}"`);
		}
	}
}

/**
 * The marketplace README's skills column, maintained by hand and checked by nothing. The row
 * pattern matches the one marketplace-integrity.test.ts uses, so a table this cannot parse is a
 * table that suite cannot parse either.
 */
function checkSkillsColumn(readme: string, plugins: LocalPlugin[]): void {
	const cells = new Map<string, string>();
	for (const line of readme.split('\n')) {
		const m = line.match(/^\|\s*\[([a-z0-9-]+)\]\(([^)]+)\)\s*\|([^|]*)\|/);
		if (m?.[1]) cells.set(m[1], m[3] ?? '');
	}
	if (cells.size === 0) {
		note('no plugin rows parsed out of the README table — the skills column was not checked');
		return;
	}

	for (const p of plugins) {
		const cell = cells.get(p.name);
		if (cell === undefined) continue; // the suite owns "is every plugin listed"
		const listed = new Set([...cell.matchAll(/`([a-z0-9-]+)`/g)].map((m) => m[1] as string));
		const shipped = new Set(dirsIn(`${p.dir}/skills`));

		for (const s of shipped) {
			if (!listed.has(s)) {
				warn(
					`the README's skills column for "${p.name}" omits \`${s}\`, so nobody browsing the repository learns it ships`,
				);
			}
		}
		for (const s of listed) {
			if (!shipped.has(s)) {
				warn(`the README's skills column for "${p.name}" lists \`${s}\`, which it does not ship`);
			}
		}
	}
}

/** stdout of a command, or null when it fails. Used for git, where failure is a real answer. */
async function run(cmd: string[]): Promise<string | null> {
	const proc = Bun.spawn(cmd, { stderr: 'pipe', stdout: 'pipe' });
	const out = await new Response(proc.stdout).text();
	return (await proc.exited) === 0 ? out : null;
}

/**
 * Plugins with commits since `ref` whose version did not move. Compares the version recorded at
 * `ref` against the version on disk, rather than looking for a changed line in the diff, so a
 * bump-and-revert is reported as the no-op it is.
 */
async function checkVersionBumps(root: string, plugins: LocalPlugin[], ref: string): Promise<number> {
	if ((await run(['git', '-C', root, 'rev-parse', '--git-dir'])) === null) {
		process.stdout.write('Usage: --since needs a git repository\n');
		return 2;
	}
	if ((await run(['git', '-C', root, 'rev-parse', '--verify', `${ref}^{commit}`])) === null) {
		process.stdout.write(`Usage: --since "${ref}" is not a commit this repository knows\n`);
		return 2;
	}

	for (const p of plugins) {
		const log = await run(['git', '-C', root, 'log', '--oneline', `${ref}..HEAD`, '--', p.rel]);
		if (!log?.trim()) continue;

		const manifestRel = `${p.rel}/.claude-plugin/plugin.json`;
		const before = await run(['git', '-C', root, 'show', `${ref}:${manifestRel}`]);
		if (before === null) continue; // the plugin did not exist at `ref`, so nothing to compare

		let past: string | undefined;
		try {
			past = (JSON.parse(before) as { version?: string }).version;
		} catch {
			continue; // an unparseable manifest at `ref` is history, not a finding about today
		}
		const now = (await Bun.file(`${p.dir}/.claude-plugin/plugin.json`).json()) as { version?: string };
		if (past !== undefined && past === now.version) {
			const count = log.trim().split('\n').length;
			warn(
				`"${p.name}" has ${count} commit(s) since ${ref} and is still at ${past} — users receive none of it until the version moves`,
			);
		}
	}
	return 0;
}

/** Locate a vendored validator by filename, anywhere a plugin ships one. */
async function findValidator(plugins: LocalPlugin[], file: string): Promise<string | null> {
	for (const p of plugins) {
		for await (const hit of new Glob(`skills/*/scripts/${file}`).scan({ cwd: p.dir })) {
			return `${p.dir}/${hit}`;
		}
	}
	return null;
}

/**
 * One validator finding split into the file it names and the rule it broke. Validator messages
 * are shaped `<path>: <rule>`, and a message with no path is all rule.
 */
function splitFinding(message: string): { file: string | null; rule: string } {
	const m = /^(\S+?):\s+(.+)$/.exec(message);
	return m?.[1]?.includes('/') ? { file: m[1], rule: m[2] as string } : { file: null, rule: message };
}

/**
 * Collapse one target's findings, so a rule broken by many files reports once.
 *
 * Without this, `manhattan-brand-artifacts` alone emits 50 identical "nested deeper than one level"
 * warnings — one per bundled font, icon, and template — and buries the three findings a maintainer
 * can act on. A sweep nobody reads to the bottom of is a sweep that reports nothing.
 */
function collapse(label: string, found: { rule: string; file: string | null }[]): string[] {
	const byRule = new Map<string, string[]>();
	for (const f of found) {
		const files = byRule.get(f.rule) ?? [];
		if (f.file) files.push(f.file);
		byRule.set(f.rule, files);
	}

	const out: string[] = [];
	for (const [rule, files] of byRule) {
		if (files.length <= 3) {
			for (const f of files) out.push(`${label}: ${f}: ${rule}`);
			if (files.length === 0) out.push(`${label}: ${rule}`);
			continue;
		}
		const shown = files.slice(0, 2).join(', ');
		out.push(`${label}: ${files.length} files — ${rule} (${shown}, and ${files.length - 2} more)`);
	}
	return out;
}

/** The validator's own filename, which becomes the `source` on every finding it produced. */
const sourceOf = (validator: string): string => validator.split('/').pop() ?? validator;

/** Extracts the referenced path from `validate_skill.ts`'s "does not exist" wording, if that is the rule. */
const missingReferencePath = (rule: string): string | null =>
	/^SKILL\.md references ([\w./-]+), which does not exist$/.exec(rule)?.[1] ?? null;

/**
 * Run a validator and fold its report into ours. Classification comes from the report's line
 * prefixes, not the exit code: every validator here exits 1 for warnings under --strict, so the
 * code alone cannot distinguish a warning from an error.
 *
 * `suppressMissing` corrects one specific false positive from `validate_skill.ts`: that validator
 * resolves every `scripts/…` mention against the skill's own directory, with no notion of
 * `${CLAUDE_PLUGIN_ROOT}/`. A skill that references its plugin's top-level `scripts/` (as this
 * repository's docs prescribe, and as `plugins/security/scripts` already does) is flagged as
 * missing every such script even though the file exists — just one level higher. Callers compute
 * the paths that are genuinely present there and pass them here so only those specific "does not
 * exist" findings are dropped; every other error and warning from the validator still counts.
 */
async function delegate(
	validator: string,
	target: string,
	label: string,
	extra: string[],
	suppressMissing: Set<string> = new Set(),
): Promise<void> {
	const proc = Bun.spawn(['bun', validator, target, '--strict', ...extra], {
		stderr: 'pipe',
		stdout: 'pipe',
	});
	const out = await new Response(proc.stdout).text();
	const code = await proc.exited;
	if (code === 0) return;

	const found: Record<'ERROR' | 'WARN', { file: string | null; rule: string }[]> = { ERROR: [], WARN: [] };
	let matched = false;
	for (const line of out.split('\n')) {
		const m = /^-\s+(ERROR|WARN):\s*(.+)$/.exec(line.trim());
		if (!m) continue;
		matched = true;
		found[m[1] as 'ERROR' | 'WARN'].push(splitFinding(m[2] as string));
	}
	const source = sourceOf(validator);
	if (!matched) {
		fail(`${label}: ${source} exited ${code} — ${out.trim() || 'no output'}`, source);
		return;
	}
	const errors = found.ERROR.filter((f) => {
		const rel = missingReferencePath(f.rule);
		return rel === null || !suppressMissing.has(rel);
	});
	for (const m of collapse(label, errors)) fail(m, source);
	for (const m of collapse(label, found.WARN)) warn(m, source);
}

/**
 * The `scripts/…`, `references/…`, `assets/…`, and `evals/…` mentions in a SKILL.md that resolve
 * from the *plugin* root rather than the skill's own directory, and genuinely exist there.
 *
 * Only a path referenced **exclusively** via the `${CLAUDE_PLUGIN_ROOT}/` prefix qualifies — a
 * bare `scripts/X` mention still means skill-relative, which is the form every other SKILL.md in
 * this repository uses and depends on `validate_skill.ts` continuing to check unchanged. A path
 * that appears both ways is left to the existing skill-relative check, rather than guessed at.
 */
async function pluginRootReferencedPaths(skillDir: string, pluginDir: string): Promise<Set<string>> {
	const skillMd = `${skillDir}/SKILL.md`;
	if (!(await Bun.file(skillMd).exists())) return new Set();
	const body = await Bun.file(skillMd).text();

	const bare = new Set<string>();
	const prefixed = new Set<string>();
	for (const m of body.matchAll(/(\$\{CLAUDE_PLUGIN_ROOT\}\/)?((?:references|scripts|assets|evals)\/[\w./-]+)/g)) {
		(m[1] ? prefixed : bare).add(m[2] as string);
	}

	const verified = new Set<string>();
	for (const rel of prefixed) {
		if (bare.has(rel)) continue;
		if (await Bun.file(`${pluginDir}/${rel}`).exists()) verified.add(rel);
	}
	return verified;
}

/** The Tier 0 lint the marketplace vendors and never runs. */
async function sweepValidators(plugins: LocalPlugin[]): Promise<void> {
	const found = {
		agent: await findValidator(plugins, 'validate_agent.ts'),
		hooks: await findValidator(plugins, 'validate_hooks.ts'),
		plugin: await findValidator(plugins, 'validate_plugin.ts'),
		skill: await findValidator(plugins, 'validate_skill.ts'),
	};
	const missing = Object.entries(found)
		.filter(([, v]) => v === null)
		.map(([k]) => k);
	if (missing.length > 0) {
		note(
			`no vendored validator found for: ${missing.join(', ')} — those checks were skipped, which is not a finding about the catalog`,
		);
	}

	for (const p of plugins) {
		if (found.plugin) await delegate(found.plugin, p.dir, p.rel, []);

		if (found.skill) {
			for (const skill of dirsIn(`${p.dir}/skills`)) {
				const skillDir = `${p.dir}/skills/${skill}`;
				const suppress = await pluginRootReferencedPaths(skillDir, p.dir);
				await delegate(found.skill, skillDir, `${p.rel}/skills/${skill}`, [], suppress);
			}
		}

		if (found.agent && existsSync(`${p.dir}/agents`)) {
			for await (const rel of new Glob('*.md').scan({ cwd: `${p.dir}/agents` })) {
				// --plugin reports the fields a plugin-shipped agent silently drops at load, which
				// is the whole reason to check an agent that ships inside a plugin.
				await delegate(found.agent, `${p.dir}/agents/${rel}`, `${p.rel}/agents/${rel}`, ['--plugin']);
			}
		}

		const hooks = `${p.dir}/hooks/hooks.json`;
		if (found.hooks && existsSync(hooks)) await delegate(found.hooks, hooks, `${p.rel}/hooks/hooks.json`, []);
	}
}

async function main(): Promise<number> {
	const argv = Bun.argv.slice(2);
	const strict = argv.includes('--strict');
	const json = argv.includes('--json');
	const delegateSweep = !argv.includes('--no-delegate');

	const sinceAt = argv.indexOf('--since');
	let since = '';
	if (sinceAt !== -1) {
		const value = argv[sinceAt + 1];
		if (value === undefined || value.startsWith('--')) {
			process.stdout.write('Usage: --since needs a git ref\n');
			return 2;
		}
		since = value;
	}

	// `sinceAt + 1` is the ref, which is positional-looking but not a positional. Guarded on
	// sinceAt !== -1: without it the index is 0, and every invocation silently drops its first
	// argument — which made a bad root audit the working directory and report clean.
	const valueAt = sinceAt === -1 ? -1 : sinceAt + 1;
	const positional = argv.filter((a, i) => !a.startsWith('--') && i !== valueAt);
	const root = (positional[0] ?? '.').replace(/\/+$/, '');
	if (positional.length > 1) {
		process.stdout.write(
			'Usage: bun audit_marketplace.ts [marketplace-root] [--strict] [--json] [--since <ref>] [--no-delegate]\n\nSweeps a plugin marketplace for the faults its test suite does not cover.\n',
		);
		return 2;
	}

	const manifestPath = `${root}/.claude-plugin/marketplace.json`;
	if (!existsSync(manifestPath)) {
		process.stdout.write(`ERROR: ${manifestPath} not found — is "${root}" a marketplace?\n`);
		return 1;
	}
	let marketplace: Marketplace;
	try {
		marketplace = (await Bun.file(manifestPath).json()) as Marketplace;
	} catch (e) {
		process.stdout.write(`ERROR: ${manifestPath} is not valid JSON — ${(e as Error).message}\n`);
		return 1;
	}

	checkSchema(marketplace);
	const { local, remote } = localPlugins(root, marketplace);
	if (remote > 0) {
		note(`${remote} entr(y/ies) use a remote source, so their files are not in this repository`);
	}

	for (const p of local) {
		if (!existsSync(p.dir)) continue; // the suite owns "every registration resolves"
		const readme = `${p.dir}/README.md`;
		if (existsSync(readme)) checkPluginReadme(p, await Bun.file(readme).text());
	}

	const rootReadme = `${root}/README.md`;
	if (existsSync(rootReadme)) checkSkillsColumn(await Bun.file(rootReadme).text(), local);
	else note('no README.md at the marketplace root — the skills column was not checked');

	if (since !== '') {
		const code = await checkVersionBumps(root, local, since);
		if (code !== 0) return code;
	}

	if (delegateSweep) await sweepValidators(local);
	else note('--no-delegate: the vendored validators were not run');

	const errors = bySeverity('error');
	const warnings = bySeverity('warn');

	if (json) {
		process.stdout.write(`${JSON.stringify({ findings, marketplace: marketplace.name ?? root }, null, 2)}\n`);
		return errors.length > 0 || (strict && warnings.length > 0) ? 1 : 0;
	}

	const out: string[] = [`# Marketplace audit: ${marketplace.name ?? root}\n`];
	if (errors.length === 0 && warnings.length === 0) out.push('Clean. No errors, no warnings.');
	for (const f of errors) out.push(`- ERROR: ${f.message}`);
	for (const f of warnings) out.push(`- WARN: ${f.message}`);
	for (const f of bySeverity('note')) out.push(`- NOTE: ${f.message}`);
	out.push(`\n${errors.length} error(s), ${warnings.length} warning(s)`);
	// Named explicitly so a reader does not mistake a clean sweep for a fully checked catalog.
	out.push(
		'Registration, name/directory agreement, versions, skill-name uniqueness, and description\nidentity are the test suite\'s to check — run it too.',
	);
	process.stdout.write(`${out.join('\n')}\n`);

	return errors.length > 0 || (strict && warnings.length > 0) ? 1 : 0;
}

process.exit(await main());
