#!/usr/bin/env bun

/**
 * validate_plugin.ts — validate a Claude Code plugin directory.
 *
 * Usage:
 *   bun validate_plugin.ts <plugin-dir> [--strict]
 *
 * Checks the layout traps that make a plugin load with missing components, the manifest
 * schema, component path rules, and the parseability of hooks/hooks.json and agent
 * frontmatter. Prints a markdown report.
 *
 * Exit codes: 0 = clean (warnings allowed unless --strict), 1 = errors found (or warnings
 * found with --strict), 2 = usage error.
 *
 * This complements `claude plugin validate`, which is authoritative when available. It
 * exists for environments without the CLI, and it checks two things the CLI does not
 * report as errors: component directories misplaced inside .claude-plugin/, and paths
 * that escape the plugin directory and therefore break after install.
 *
 * No dependencies beyond Bun itself.
 */

import { Glob } from 'bun';

const NAME_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;

/** Directories that must sit at the plugin root, never inside .claude-plugin/. */
const COMPONENT_DIRS = [
	'skills',
	'agents',
	'commands',
	'hooks',
	'workflows',
	'output-styles',
	'monitors',
	'themes',
	'scripts',
	'bin',
];

/** Root files that are components rather than metadata. */
const COMPONENT_FILES = ['.mcp.json', '.lsp.json', 'settings.json'];

/** Manifest keys whose values are plugin-relative paths. */
const PATH_FIELDS = [
	'skills',
	'commands',
	'agents',
	'workflows',
	'hooks',
	'mcpServers',
	'outputStyles',
	'lspServers',
];

/** Path fields that REPLACE their default directory rather than adding to it. */
const REPLACING_FIELDS = new Set(['commands', 'agents', 'workflows', 'outputStyles']);

const KNOWN_MANIFEST_KEYS = new Set([
	'$schema',
	'name',
	'displayName',
	'version',
	'description',
	'author',
	'homepage',
	'repository',
	'license',
	'keywords',
	'defaultEnabled',
	'userConfig',
	'channels',
	'dependencies',
	'experimental',
	'settings',
	...PATH_FIELDS,
]);

/** Hook events, exactly as Claude Code matches them (case-sensitive). */
const HOOK_EVENTS = new Set([
	'SessionStart',
	'Setup',
	'InstructionsLoaded',
	'UserPromptSubmit',
	'UserPromptExpansion',
	'MessageDisplay',
	'PreToolUse',
	'PermissionRequest',
	'PermissionDenied',
	'PostToolUse',
	'PostToolUseFailure',
	'PostToolBatch',
	'Stop',
	'StopFailure',
	'SubagentStart',
	'SubagentStop',
	'TaskCreated',
	'TaskCompleted',
	'TeammateIdle',
	'Notification',
	'ConfigChange',
	'CwdChanged',
	'FileChanged',
	'WorktreeCreate',
	'WorktreeRemove',
	'PreCompact',
	'PostCompact',
	'SessionEnd',
	'Elicitation',
	'ElicitationResult',
]);

const HANDLER_TYPES = new Set(['command', 'http', 'mcp_tool', 'prompt', 'agent']);

/** Agent frontmatter fields that are silently dropped when the agent ships in a plugin. */
const PLUGIN_IGNORED_AGENT_FIELDS = ['hooks', 'mcpServers', 'permissionMode'];

const errors: string[] = [];
const warnings: string[] = [];

function str(v: unknown): string {
	return typeof v === 'string' ? v : v === undefined || v === null ? '' : String(v);
}

/** Split `---` frontmatter from the body, then parse the block as real YAML. */
function parseFrontmatter(text: string): Record<string, unknown> | null {
	if (!text.startsWith('---')) return null;
	const end = text.indexOf('\n---', 3);
	if (end === -1) return null;
	const block = text.slice(3, end).replace(/^\n+/, '');
	try {
		const parsed = Bun.YAML.parse(block);
		if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) return null;
		return parsed as Record<string, unknown>;
	} catch {
		return null;
	}
}

async function isDir(path: string): Promise<boolean> {
	try {
		const { stat } = await import('node:fs/promises');
		return (await stat(path)).isDirectory();
	} catch {
		return false;
	}
}

/**
 * The highest-value check in this script. A plugin whose skills/ or hooks/ lives inside
 * .claude-plugin/ installs cleanly and shows zero components, with no error anywhere.
 */
async function checkLayout(dir: string): Promise<void> {
	const metaDir = `${dir}/.claude-plugin`;
	if (!(await isDir(metaDir))) {
		if (!(await Bun.file(`${dir}/SKILL.md`).exists())) {
			warnings.push(
				'no .claude-plugin/plugin.json: components will auto-discover and the plugin name will come from the directory name',
			);
		}
		return;
	}

	for await (const entry of new Glob('*').scan({ cwd: metaDir, onlyFiles: false })) {
		if (entry === 'plugin.json') continue;
		if (entry.startsWith('.')) continue;
		if (COMPONENT_DIRS.includes(entry) || COMPONENT_FILES.includes(entry)) {
			errors.push(
				`.claude-plugin/${entry}: component lives inside .claude-plugin/ and will never load — move it to the plugin root`,
			);
		} else {
			warnings.push(`.claude-plugin/${entry}: only plugin.json belongs in this directory`);
		}
	}
}

function checkManifestFields(manifest: Record<string, unknown>, dirName: string): void {
	const name = str(manifest.name);
	if (!name) {
		errors.push('`name` is missing — it is the only required manifest field');
	} else if (!NAME_RE.test(name)) {
		errors.push(
			`\`name\` '${name}' is not kebab-case (Claude Code tolerates this; claude.ai marketplace sync rejects it)`,
		);
	}
	if (name && name !== dirName) {
		warnings.push(`\`name\` '${name}' does not match directory '${dirName}'`);
	}

	if (manifest.keywords !== undefined && !Array.isArray(manifest.keywords)) {
		errors.push('`keywords` must be an array — a wrong type on a known field is a load error');
	}
	if (manifest.author !== undefined && typeof manifest.author !== 'object') {
		errors.push('`author` must be an object of the form {name, email?, url?}');
	}
	if (manifest.version === undefined) {
		warnings.push(
			'no `version`: the plugin falls back to the git commit SHA, so every new commit ships to users',
		);
	}
	if (str(manifest.description).length === 0) {
		warnings.push('no `description`: users see nothing in `/plugin` or `claude plugin list`');
	}

	for (const key of Object.keys(manifest)) {
		if (!KNOWN_MANIFEST_KEYS.has(key)) {
			warnings.push(`\`${key}\`: unrecognized manifest key (ignored at load time)`);
		}
	}
}

async function checkPathFields(manifest: Record<string, unknown>, dir: string): Promise<void> {
	for (const field of PATH_FIELDS) {
		const value = manifest[field];
		if (value === undefined) continue;

		const paths: string[] =
			typeof value === 'string' ? [value] : Array.isArray(value) ? value.map(str) : [];
		if (paths.length === 0) continue; // object form (inline hooks/mcpServers) — nothing to resolve

		for (const p of paths) {
			if (!p.startsWith('./')) {
				errors.push(`\`${field}\`: '${p}' must be relative and start with ./`);
				continue;
			}
			if (p.includes('../')) {
				errors.push(
					`\`${field}\`: '${p}' escapes the plugin directory and will break once installed`,
				);
				continue;
			}
			const resolved = `${dir}/${p.replace(/^\.\//, '').replace(/\/+$/, '')}`;
			const exists = (await Bun.file(resolved).exists()) || (await isDir(resolved));
			if (!exists) errors.push(`\`${field}\`: '${p}' does not resolve to a file or directory`);
		}

		if (REPLACING_FIELDS.has(field)) {
			const defaultDir = field === 'outputStyles' ? 'output-styles' : field;
			const pointsAtDefault = paths.some((p) => p.replace(/^\.\//, '').startsWith(defaultDir));
			if ((await isDir(`${dir}/${defaultDir}`)) && !pointsAtDefault) {
				warnings.push(
					`\`${field}\` replaces the default ${defaultDir}/ directory rather than adding to it — list both if you want to keep it`,
				);
			}
		}
	}
}

async function checkHooksConfig(dir: string): Promise<void> {
	const path = `${dir}/hooks/hooks.json`;
	if (!(await Bun.file(path).exists())) return;

	let parsed: unknown;
	try {
		parsed = JSON.parse(await Bun.file(path).text());
	} catch (e) {
		errors.push(
			`hooks/hooks.json does not parse (${(e as Error).message}) — a malformed hooks file stops the entire plugin loading`,
		);
		return;
	}

	const root = parsed as Record<string, unknown>;
	const hooks = (root.hooks ?? root) as Record<string, unknown>;
	if (typeof hooks !== 'object' || hooks === null) {
		errors.push('hooks/hooks.json has no `hooks` object');
		return;
	}

	for (const [event, groups] of Object.entries(hooks)) {
		// A bad event name does not stop handler checking — a config usually has more than
		// one fault, and reporting only the first sends the reader back for another round.
		if (!HOOK_EVENTS.has(event)) {
			const near = [...HOOK_EVENTS].find((e) => e.toLowerCase() === event.toLowerCase());
			errors.push(
				near
					? `hooks/hooks.json: event '${event}' is miscased — event names are case-sensitive, use '${near}'`
					: `hooks/hooks.json: '${event}' is not a hook event`,
			);
		}
		if (!Array.isArray(groups)) {
			errors.push(`hooks/hooks.json: ${event} must be an array of matcher groups`);
			continue;
		}
		for (const group of groups) {
			const handlers = (group as Record<string, unknown>)?.hooks;
			if (!Array.isArray(handlers)) {
				errors.push(`hooks/hooks.json: a ${event} group has no \`hooks\` array`);
				continue;
			}
			for (const handler of handlers) {
				const h = handler as Record<string, unknown>;
				const type = str(h.type);
				if (!HANDLER_TYPES.has(type)) {
					errors.push(
						`hooks/hooks.json: ${event} handler type '${type || '(missing)'}' is not one of ${[...HANDLER_TYPES].join(', ')}`,
					);
				}
				const command = str(h.command);
				if (type === 'command' && command && !command.includes('${CLAUDE_PLUGIN_ROOT}')) {
					if (command.startsWith('./') || command.startsWith('../')) {
						errors.push(
							`hooks/hooks.json: ${event} command '${command}' is a relative path — use \${CLAUDE_PLUGIN_ROOT} so it resolves after install`,
						);
					}
				}
			}
		}
	}
}

async function checkAgents(dir: string): Promise<void> {
	const agentsDir = `${dir}/agents`;
	if (!(await isDir(agentsDir))) return;

	for await (const entry of new Glob('**/*.md').scan({ cwd: agentsDir, onlyFiles: true })) {
		const fields = parseFrontmatter(await Bun.file(`${agentsDir}/${entry}`).text());
		if (fields === null) {
			errors.push(`agents/${entry}: no parseable YAML frontmatter`);
			continue;
		}
		if (!str(fields.name)) errors.push(`agents/${entry}: \`name\` is required`);
		if (!str(fields.description)) errors.push(`agents/${entry}: \`description\` is required`);
		for (const field of PLUGIN_IGNORED_AGENT_FIELDS) {
			if (fields[field] !== undefined) {
				warnings.push(
					`agents/${entry}: \`${field}\` is ignored for plugin-shipped agents — copy the agent into .claude/agents/ if you need it`,
				);
			}
		}
	}
}

async function checkSkills(dir: string): Promise<void> {
	const skillsDir = `${dir}/skills`;
	if (!(await isDir(skillsDir))) return;

	for await (const entry of new Glob('*').scan({ cwd: skillsDir, onlyFiles: false })) {
		if (entry.startsWith('.')) continue;
		if (!(await isDir(`${skillsDir}/${entry}`))) continue;
		if (!(await Bun.file(`${skillsDir}/${entry}/SKILL.md`).exists())) {
			errors.push(`skills/${entry}: no SKILL.md`);
		}
	}
}

async function main(): Promise<number> {
	const argv = Bun.argv.slice(2);
	const positional = argv.filter((a) => !a.startsWith('--'));
	const strict = argv.includes('--strict');
	const target = positional[0];
	if (target === undefined) {
		process.stdout.write(
			'Usage: bun validate_plugin.ts <plugin-dir> [--strict]\n\nValidates a Claude Code plugin directory: layout, manifest, component paths, hooks config, agents.\n',
		);
		return 2;
	}

	const dir = target.replace(/\/+$/, '');
	const dirName = dir.split('/').pop() ?? dir;
	if (!(await isDir(dir))) {
		process.stdout.write(`ERROR: ${dir} is not a directory\n`);
		return 1;
	}

	await checkLayout(dir);

	const manifestPath = `${dir}/.claude-plugin/plugin.json`;
	if (await Bun.file(manifestPath).exists()) {
		let manifest: Record<string, unknown> | null = null;
		try {
			manifest = JSON.parse(await Bun.file(manifestPath).text()) as Record<string, unknown>;
		} catch (e) {
			errors.push(`.claude-plugin/plugin.json does not parse: ${(e as Error).message}`);
		}
		if (manifest !== null) {
			checkManifestFields(manifest, dirName);
			await checkPathFields(manifest, dir);
		}
	}

	await checkHooksConfig(dir);
	await checkAgents(dir);
	await checkSkills(dir);

	const out: string[] = [`# Plugin validation report: ${dirName}\n`];
	if (errors.length === 0 && warnings.length === 0) {
		out.push('Clean. No errors, no warnings.');
	}
	for (const e of errors) out.push(`- ERROR: ${e}`);
	for (const w of warnings) out.push(`- WARN: ${w}`);
	out.push(`\n${errors.length} error(s), ${warnings.length} warning(s)`);
	process.stdout.write(`${out.join('\n')}\n`);

	return errors.length > 0 || (strict && warnings.length > 0) ? 1 : 0;
}

process.exit(await main());
