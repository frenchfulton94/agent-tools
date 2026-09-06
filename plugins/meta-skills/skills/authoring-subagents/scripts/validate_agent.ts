#!/usr/bin/env bun

/**
 * validate_agent.ts — validate a Claude Code subagent definition.
 *
 * Usage:
 *   bun validate_agent.ts <agent.md> [--strict] [--plugin]
 *
 * Checks frontmatter against the documented schema, tool names against the canonical list,
 * and the two filters that silently narrow a subagent's tool pool. Pass --plugin when the
 * agent ships inside a plugin, to surface the fields that are dropped on that path.
 *
 * Exit codes: 0 = clean (warnings allowed unless --strict), 1 = errors found (or warnings
 * found with --strict), 2 = usage error.
 *
 * The description checks are heuristics, not spec rules: an agent whose description states
 * what it *is* rather than when to delegate to it is the most common reason a subagent is
 * never invoked, and that failure is invisible from the file alone.
 *
 * No dependencies beyond Bun itself.
 */

export {}; // marks this a module, which is what permits the top-level await below

const NAME_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;

const KNOWN_FIELDS = new Set([
	'name',
	'description',
	'tools',
	'disallowedTools',
	'model',
	'permissionMode',
	'maxTurns',
	'skills',
	'mcpServers',
	'hooks',
	'memory',
	'background',
	'effort',
	'isolation',
	'color',
	'initialPrompt',
]);

/** Fields silently dropped when the agent loads from a plugin. */
const PLUGIN_IGNORED = ['hooks', 'mcpServers', 'permissionMode'];

const MODELS = new Set(['sonnet', 'opus', 'haiku', 'fable', 'inherit']);
const PERMISSION_MODES = new Set([
	'default',
	'acceptEdits',
	'auto',
	'dontAsk',
	'bypassPermissions',
	'plan',
	'manual',
]);
const EFFORTS = new Set(['low', 'medium', 'high', 'xhigh', 'max']);
const MEMORY_SCOPES = new Set(['user', 'project', 'local']);
const COLORS = new Set(['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'cyan']);

/** Canonical tool names, from the tools reference. */
const CANONICAL_TOOLS = new Set([
	'Agent',
	'Artifact',
	'AskUserQuestion',
	'Bash',
	'CronCreate',
	'CronDelete',
	'CronList',
	'Edit',
	'EndConversation',
	'EnterPlanMode',
	'EnterWorktree',
	'ExitPlanMode',
	'ExitWorktree',
	'Glob',
	'Grep',
	'ListMcpResourcesTool',
	'LSP',
	'Monitor',
	'NotebookEdit',
	'PowerShell',
	'PushNotification',
	'Read',
	'ReadMcpResourceTool',
	'RemoteTrigger',
	'ReportFindings',
	'ScheduleWakeup',
	'SendMessage',
	'SendUserFile',
	'ShareOnboardingGuide',
	'Skill',
	'Task', // pre-v2.1.63 alias for Agent
	'TaskCreate',
	'TaskGet',
	'TaskList',
	'TaskOutput',
	'TaskStop',
	'TaskUpdate',
	'TodoWrite',
	'ToolSearch',
	'WaitForMcpServers',
	'WebFetch',
	'WebSearch',
	'Workflow',
	'Write',
]);

/** Removed from every subagent regardless of the tools field. */
const NEVER_AVAILABLE = new Set([
	'AskUserQuestion',
	'EndConversation',
	'EnterPlanMode',
	'ScheduleWakeup',
	'TaskOutput',
	'WaitForMcpServers',
	'Workflow',
]);

/** Built-ins a background subagent keeps. Everything else is dropped there. */
const BACKGROUND_SAFE = new Set([
	'Read',
	'Grep',
	'Glob',
	'Bash',
	'PowerShell',
	'Edit',
	'Write',
	'NotebookEdit',
	'WebFetch',
	'WebSearch',
	'TodoWrite',
	'Skill',
	'ToolSearch',
	'EnterWorktree',
	'ExitWorktree',
	'Monitor',
	'TaskStop',
	'SendMessage',
	'Artifact',
]);

const errors: string[] = [];
const warnings: string[] = [];

function str(v: unknown): string {
	return typeof v === 'string' ? v : v === undefined || v === null ? '' : String(v);
}

/** Split `---` frontmatter from the body, then parse the block as real YAML. */
function parseFrontmatter(text: string): { fields: Record<string, unknown> | null; body: string } {
	if (!text.startsWith('---')) return { body: text, fields: null };
	const end = text.indexOf('\n---', 3);
	if (end === -1) return { body: text, fields: null };
	const block = text.slice(3, end).replace(/^\n+/, '');
	const body = text.slice(end + 4);
	try {
		const parsed = Bun.YAML.parse(block);
		if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
			return { body, fields: null };
		}
		return { body, fields: parsed as Record<string, unknown> };
	} catch {
		return { body, fields: null };
	}
}

/** `tools` is a comma-separated string in YAML and an array in --agents JSON. */
function toolList(value: unknown): string[] {
	if (Array.isArray(value)) return value.map(str).map((t) => t.trim()).filter(Boolean);
	return str(value)
		.split(',')
		.map((t) => t.trim())
		.filter(Boolean);
}

/** Strip an Agent(...) allowlist down to the bare tool name. */
function bareToolName(entry: string): string {
	const paren = entry.indexOf('(');
	return paren === -1 ? entry : entry.slice(0, paren).trim();
}

function checkIdentity(fields: Record<string, unknown>): void {
	const name = str(fields.name);
	if (!name) {
		errors.push('`name` is required');
	} else if (!NAME_RE.test(name)) {
		errors.push(`\`name\` '${name}' must be lowercase letters, digits, and single hyphens`);
	}

	const desc = str(fields.description);
	if (!desc) {
		errors.push('`description` is required — it is what Claude reads to decide whether to delegate');
		return;
	}
	const lower = desc.toLowerCase();
	if (!/\buse\b/.test(lower) && !/\bwhen\b/.test(lower)) {
		warnings.push(
			'`description` states no delegation trigger — add when to hand work to this agent ("Use when...", "Use proactively after..."), or it will rarely be invoked automatically',
		);
	}
	if (/^(a|an|the)\s+\w+\s+(agent|specialist|expert|subagent)\b/i.test(desc.trim())) {
		warnings.push(
			'`description` describes what the agent is rather than when to use it — the description is a routing signal, not a title',
		);
	}
	if (/\bfirst\b[\s\S]*\bthen\b|\bstep\s*[12]\b/i.test(desc)) {
		warnings.push(
			'`description` contains sequenced workflow steps — the caller may follow the summary instead of dispatching the agent',
		);
	}
}

function checkEnums(fields: Record<string, unknown>): void {
	const model = str(fields.model);
	// A full model ID (claude-opus-5, claude-sonnet-5) is also valid.
	if (model && !MODELS.has(model) && !model.startsWith('claude-')) {
		errors.push(
			`\`model\` '${model}' is not an alias (${[...MODELS].join(', ')}) or a full model ID`,
		);
	}

	const mode = str(fields.permissionMode);
	if (mode && !PERMISSION_MODES.has(mode)) {
		errors.push(`\`permissionMode\` '${mode}' is not one of ${[...PERMISSION_MODES].join(', ')}`);
	}

	const effort = str(fields.effort);
	if (effort && !EFFORTS.has(effort)) {
		errors.push(`\`effort\` '${effort}' is not one of ${[...EFFORTS].join(', ')}`);
	}

	const memory = str(fields.memory);
	if (memory && !MEMORY_SCOPES.has(memory)) {
		errors.push(`\`memory\` '${memory}' is not one of ${[...MEMORY_SCOPES].join(', ')}`);
	} else if (memory) {
		warnings.push(
			'`memory` has no effect when auto memory is disabled at the session level — confirm autoMemoryEnabled before relying on it',
		);
	}

	const isolation = str(fields.isolation);
	if (isolation && isolation !== 'worktree') {
		errors.push("`isolation` accepts only 'worktree'");
	}

	const color = str(fields.color);
	if (color && !COLORS.has(color)) {
		errors.push(`\`color\` '${color}' is not one of ${[...COLORS].join(', ')}`);
	}

	if (fields.maxTurns !== undefined && typeof fields.maxTurns !== 'number') {
		errors.push('`maxTurns` must be a number');
	}

	for (const key of Object.keys(fields)) {
		if (!KNOWN_FIELDS.has(key)) {
			warnings.push(`\`${key}\`: not a documented subagent frontmatter field`);
		}
	}
}

function checkTools(fields: Record<string, unknown>): void {
	const tools = toolList(fields.tools);
	const disallowed = toolList(fields.disallowedTools);
	const background = fields.background === true;

	if (fields.tools !== undefined && tools.length === 0) {
		errors.push('`tools` is present but empty — an agent with no resolvable tool refuses to launch');
	}

	let resolvable = 0;
	for (const entry of tools) {
		const bare = bareToolName(entry);
		if (bare.startsWith('mcp__')) {
			resolvable += 1;
			continue;
		}
		if (!CANONICAL_TOOLS.has(bare)) {
			const near = [...CANONICAL_TOOLS].find((t) => t.toLowerCase() === bare.toLowerCase());
			errors.push(
				near
					? `\`tools\`: '${bare}' is miscased — use '${near}'`
					: `\`tools\`: '${bare}' is not a canonical tool name`,
			);
			continue;
		}
		resolvable += 1;

		if (NEVER_AVAILABLE.has(bare)) {
			warnings.push(
				`\`tools\`: '${bare}' is removed from every subagent regardless of this list — listing it has no effect`,
			);
		} else if (bare === 'ExitPlanMode' && str(fields.permissionMode) !== 'plan') {
			warnings.push(
				"`tools`: 'ExitPlanMode' reaches a subagent only under permissionMode: plan",
			);
		} else if (!BACKGROUND_SAFE.has(bare)) {
			warnings.push(
				background
					? `\`tools\`: '${bare}' is dropped from background subagents, and \`background: true\` forces that path`
					: `\`tools\`: '${bare}' is dropped when this agent runs in the background, which is the default since v2.1.198 — the same definition resolves differently in the foreground`,
			);
		}

		if (bare === 'Agent' && entry.includes('(')) {
			warnings.push(
				'`tools`: the type list inside Agent(...) applies only to an agent running as the main thread via --agent, and is ignored in a subagent definition',
			);
		}
	}

	if (tools.length > 0 && resolvable === 0) {
		errors.push(
			'no entry in `tools` resolves to a real tool — the agent will refuse to launch (see errors above)',
		);
	}

	for (const entry of disallowed) {
		const bare = bareToolName(entry);
		if (bare.startsWith('mcp__') || bare === 'mcp__*') continue;
		if (!CANONICAL_TOOLS.has(bare)) {
			warnings.push(`\`disallowedTools\`: '${bare}' is not a canonical tool name`);
			continue;
		}
		if (tools.includes(bare)) {
			warnings.push(
				`'${bare}' appears in both \`tools\` and \`disallowedTools\` — disallowedTools applies first, so the tool is removed`,
			);
		}
	}

	if (fields.skills !== undefined && tools.length > 0 && !tools.includes('Skill')) {
		// Preloading works without the Skill tool; only further discovery needs it.
		warnings.push(
			'`skills` preloads content, but without `Skill` in `tools` the agent cannot invoke any other skill',
		);
	}
}

function checkBody(body: string, name: string): void {
	const text = body.trim();
	if (text.length === 0) {
		errors.push('body is empty — the body is the agent’s entire system prompt');
		return;
	}
	if (text.length < 120) {
		warnings.push(
			`body is ${text.length} characters — a subagent receives no conversation history, so a terse body usually produces thin results`,
		);
	}
	if (
		/\b(as (we|you) discussed|(file|change|issue|approach)s? (we|you) (discussed|mentioned|were looking at)|earlier in this conversation|as mentioned above|like (we|you) did (before|earlier))\b/i.test(
			text,
		)
	) {
		errors.push(
			'body refers to conversation context the subagent never receives — it starts with only this prompt, CLAUDE.md, and a git snapshot',
		);
	}
	if (!/\b(report|return|output|respond|summar)/i.test(text)) {
		warnings.push(
			`body does not say what ${name || 'the agent'} should return — the caller sees only the final message`,
		);
	}
}

async function main(): Promise<number> {
	const argv = Bun.argv.slice(2);
	const positional = argv.filter((a) => !a.startsWith('--'));
	const strict = argv.includes('--strict');
	const isPlugin = argv.includes('--plugin');
	const target = positional[0];

	if (target === undefined) {
		process.stdout.write(
			'Usage: bun validate_agent.ts <agent.md> [--strict] [--plugin]\n\nValidates a Claude Code subagent definition.\n',
		);
		return 2;
	}
	if (!(await Bun.file(target).exists())) {
		process.stdout.write(`ERROR: ${target} not found\n`);
		return 1;
	}

	const { fields, body } = parseFrontmatter(await Bun.file(target).text());
	if (fields === null) {
		process.stdout.write('ERROR: no parseable YAML frontmatter\n');
		return 1;
	}

	checkIdentity(fields);
	checkEnums(fields);
	checkTools(fields);
	checkBody(body, str(fields.name));

	if (isPlugin) {
		for (const field of PLUGIN_IGNORED) {
			if (fields[field] !== undefined) {
				errors.push(
					`\`${field}\` is silently dropped for plugin-shipped agents — move the agent to .claude/agents/ if it needs this`,
				);
			}
		}
	} else {
		const present = PLUGIN_IGNORED.filter((f) => fields[f] !== undefined);
		if (present.length > 0) {
			warnings.push(
				`\`${present.join('`, `')}\` would be silently dropped if this agent ships in a plugin — re-run with --plugin to check`,
			);
		}
	}

	const label = target.split('/').pop() ?? target;
	const out: string[] = [`# Agent validation report: ${label}\n`];
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
