#!/usr/bin/env bun

/**
 * validate_hooks.ts — validate a hook configuration, and optionally dry-run its handlers.
 *
 * Usage:
 *   bun validate_hooks.ts <hooks.json|settings.json> [--strict]
 *   bun validate_hooks.ts <config> --simulate <Event> [--payload <file.json>]
 *
 * Static checks cover the faults that make a hook look configured and do nothing: miscased
 * event names, matchers in the wrong syntax class, handler types the event does not accept,
 * `if` on a non-tool event, and `once` where it is ignored.
 *
 * --simulate spawns each command handler registered for <Event> with a synthetic payload on
 * stdin, then reports the exit code, whether stdout parsed as valid hook JSON, and what
 * Claude Code would do with the result. This catches the two faults static analysis cannot
 * see: a script that exits 1 expecting to block, and JSON printed alongside exit 2.
 *
 * Exit codes: 0 = clean (warnings allowed unless --strict), 1 = errors found (or warnings
 * found with --strict), 2 = usage error.
 *
 * No dependencies beyond Bun itself.
 */

export {}; // marks this a module, which is what permits the top-level await below

/** Every hook event, exactly as Claude Code matches it. Names are case-sensitive. */
const EVENTS = [
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
] as const;

type EventName = (typeof EVENTS)[number];
const EVENT_SET = new Set<string>(EVENTS);

/** Events that ignore a `matcher` entirely — setting one narrows nothing. */
const NO_MATCHER = new Set<string>([
	'UserPromptSubmit',
	'PostToolBatch',
	'Stop',
	'TeammateIdle',
	'TaskCreated',
	'TaskCompleted',
	'WorktreeCreate',
	'WorktreeRemove',
	'MessageDisplay',
	'CwdChanged',
]);

/** Tool events — the only ones where an `if` condition is evaluated. */
const TOOL_EVENTS = new Set<string>([
	'PreToolUse',
	'PostToolUse',
	'PostToolUseFailure',
	'PermissionRequest',
	'PermissionDenied',
]);

/** Events where exit 2 blocks something. Everything else ignores it. */
const BLOCKING = new Set<string>([
	'PreToolUse',
	'PermissionRequest',
	'UserPromptSubmit',
	'UserPromptExpansion',
	'Stop',
	'SubagentStop',
	'TeammateIdle',
	'TaskCreated',
	'TaskCompleted',
	'ConfigChange',
	'PostToolBatch',
	'PreCompact',
	'Elicitation',
	'ElicitationResult',
	'WorktreeCreate',
]);

const ALL_TYPES = new Set(['command', 'http', 'mcp_tool', 'prompt', 'agent']);
/** Events that reject `prompt` and `agent` handlers. */
const NO_MODEL_HANDLERS = new Set<string>([
	'ConfigChange',
	'CwdChanged',
	'Elicitation',
	'ElicitationResult',
	'FileChanged',
	'InstructionsLoaded',
	'Notification',
	'PreCompact',
	'PostCompact',
	'SessionEnd',
	'StopFailure',
	'SubagentStart',
	'WorktreeCreate',
	'WorktreeRemove',
]);
/** Events that accept only `command` and `mcp_tool`. */
const COMMAND_OR_MCP_ONLY = new Set<string>(['SessionStart', 'Setup']);

/** Matchers compared as exact strings rather than regexes contain only these characters. */
const EXACT_MATCH_RE = /^[A-Za-z0-9_\-, |]+$/;
/** FileChanged and StopFailure use a narrower exact-match set. */
const NARROW_EXACT_RE = /^[A-Za-z0-9_|]+$/;

/** Minimal synthetic payloads for --simulate, keyed by event. */
const PAYLOADS: Partial<Record<EventName, Record<string, unknown>>> = {
	PreToolUse: {
		tool_name: 'Bash',
		tool_input: { command: 'echo hello', description: 'Print a greeting' },
		tool_use_id: 'toolu_simulated',
	},
	PostToolUse: {
		tool_name: 'Write',
		tool_input: { file_path: '/tmp/example.ts', content: 'export const a = 1\n' },
		tool_response: { filePath: '/tmp/example.ts', success: true },
		tool_use_id: 'toolu_simulated',
		duration_ms: 12,
	},
	PostToolUseFailure: {
		tool_name: 'Bash',
		tool_input: { command: 'npm test' },
		tool_use_id: 'toolu_simulated',
		error: 'Command exited with non-zero status code 1',
		is_interrupt: false,
	},
	UserPromptSubmit: { prompt: 'Write a function to calculate a factorial' },
	SessionStart: { source: 'startup' },
	SessionEnd: { reason: 'other' },
	Stop: { stop_hook_active: false, last_assistant_message: 'Done.' },
	SubagentStop: { stop_hook_active: false, agent_type: 'Explore', last_assistant_message: 'Done.' },
	Notification: { message: 'Claude needs your permission', notification_type: 'permission_prompt' },
	FileChanged: { file_path: '/tmp/.env', event: 'change' },
	PreCompact: { trigger: 'manual', custom_instructions: '' },
};

const errors: string[] = [];
const warnings: string[] = [];

function str(v: unknown): string {
	return typeof v === 'string' ? v : v === undefined || v === null ? '' : String(v);
}

type Handler = Record<string, unknown>;
type Group = { matcher?: unknown; hooks?: unknown };

/** Accept settings.json, a plugin hooks.json wrapper, or a bare event map. */
function extractHookMap(root: unknown): Record<string, unknown> | null {
	if (root === null || typeof root !== 'object' || Array.isArray(root)) return null;
	const obj = root as Record<string, unknown>;
	const inner = obj.hooks;
	if (inner !== undefined && typeof inner === 'object' && inner !== null && !Array.isArray(inner)) {
		return inner as Record<string, unknown>;
	}
	// A bare event map: every key is a known event name.
	if (Object.keys(obj).some((k) => EVENT_SET.has(k))) return obj;
	return null;
}

function checkMatcher(event: string, matcher: string): void {
	if (matcher === '' || matcher === '*') return;

	if (NO_MATCHER.has(event)) {
		warnings.push(`${event}: matcher '${matcher}' is ignored — this event has no matcher support`);
		return;
	}

	const narrow = event === 'FileChanged' || event === 'StopFailure';
	const exact = narrow ? NARROW_EXACT_RE.test(matcher) : EXACT_MATCH_RE.test(matcher);

	if (exact) {
		if (matcher.startsWith('mcp__') && !matcher.includes('*')) {
			errors.push(
				`${event}: matcher '${matcher}' has no regex characters, so it is compared as a literal string and matches no MCP tool — use '${matcher}__.*'`,
			);
		}
		if (narrow && /[-, ]/.test(matcher)) {
			warnings.push(
				`${event}: matcher '${matcher}' falls back to regex here — this event's exact-match set is letters, digits, _ and | only`,
			);
		}
		return;
	}

	// Regex path.
	try {
		new RegExp(matcher);
	} catch (e) {
		errors.push(`${event}: matcher '${matcher}' is not a valid regex (${(e as Error).message})`);
		return;
	}
	if (!matcher.startsWith('^') || !matcher.endsWith('$')) {
		if (/^[A-Za-z]+\.\*$/.test(matcher)) {
			warnings.push(
				`${event}: matcher '${matcher}' is an unanchored regex — 'Edit.*' also matches NotebookEdit; use '^Edit$' for a single tool`,
			);
		} else if (!matcher.includes('mcp__')) {
			warnings.push(
				`${event}: matcher '${matcher}' is an unanchored regex and may match more than intended — anchor with ^ and $ if you mean one exact name`,
			);
		}
	}
}

function checkHandler(event: string, handler: Handler, source: string): void {
	const type = str(handler.type);
	if (!ALL_TYPES.has(type)) {
		errors.push(
			`${event}: handler type '${type || '(missing)'}' is not one of ${[...ALL_TYPES].join(', ')}`,
		);
		return;
	}

	if (COMMAND_OR_MCP_ONLY.has(event) && type !== 'command' && type !== 'mcp_tool') {
		errors.push(`${event}: accepts only command and mcp_tool handlers, not '${type}'`);
	} else if (NO_MODEL_HANDLERS.has(event) && (type === 'prompt' || type === 'agent')) {
		errors.push(`${event}: does not accept '${type}' handlers`);
	}

	if (handler.if !== undefined && !TOOL_EVENTS.has(event)) {
		errors.push(
			`${event}: \`if\` is evaluated only on tool events, so this handler never runs — remove it or move the hook to a tool event`,
		);
	}
	if (typeof handler.if === 'string' && /&&|\|\|/.test(handler.if)) {
		errors.push(`${event}: \`if\` takes exactly one permission rule — no && or || syntax`);
	}

	if (handler.once !== undefined && source !== 'skill-frontmatter') {
		warnings.push(`${event}: \`once\` is honored only in skill frontmatter and is ignored here`);
	}

	if (type === 'command') {
		const command = str(handler.command);
		if (!command) {
			errors.push(`${event}: command handler has no \`command\``);
		} else if (command.startsWith('./') || command.startsWith('../')) {
			errors.push(
				`${event}: command '${command}' is a relative path and resolves against an unpredictable cwd — use an absolute path, \${CLAUDE_PROJECT_DIR}, or \${CLAUDE_PLUGIN_ROOT}`,
			);
		}
		if (handler.async === true && BLOCKING.has(event)) {
			warnings.push(
				`${event}: an async handler cannot block or return a decision, so its blocking output is discarded`,
			);
		}
		if (Array.isArray(handler.args) && /\s/.test(command) && !command.includes('/')) {
			warnings.push(
				`${event}: exec form with a bare command containing whitespace ('${command}') — there is no executable by that name`,
			);
		}
	}

	if (type === 'http') {
		if (!str(handler.url)) errors.push(`${event}: http handler has no \`url\``);
		const headers = handler.headers as Record<string, unknown> | undefined;
		const allowed = new Set((handler.allowedEnvVars as string[] | undefined) ?? []);
		if (headers) {
			for (const value of Object.values(headers)) {
				for (const m of str(value).matchAll(/\$\{?([A-Z_][A-Z0-9_]*)\}?/g)) {
					const name = m[1];
					if (name !== undefined && !allowed.has(name)) {
						errors.push(
							`${event}: header references $${name}, which is not in \`allowedEnvVars\` and will resolve to an empty string`,
						);
					}
				}
			}
		}
	}

	if (type === 'mcp_tool') {
		if (!str(handler.server)) errors.push(`${event}: mcp_tool handler has no \`server\``);
		if (!str(handler.tool)) errors.push(`${event}: mcp_tool handler has no \`tool\``);
	}

	if ((type === 'prompt' || type === 'agent') && !str(handler.prompt)) {
		errors.push(`${event}: ${type} handler has no \`prompt\``);
	}

	const timeout = handler.timeout;
	if (timeout !== undefined && (typeof timeout !== 'number' || timeout <= 0)) {
		errors.push(`${event}: \`timeout\` must be a positive number of seconds`);
	}
	if (typeof timeout === 'number') {
		if (event === 'UserPromptSubmit' && timeout > 30) {
			warnings.push(`${event}: timeout ${timeout}s exceeds this event's 30s cap`);
		}
		if (event === 'MessageDisplay' && timeout > 10) {
			warnings.push(`${event}: timeout ${timeout}s exceeds this event's 10s cap`);
		}
	}
}

function checkConfig(map: Record<string, unknown>, source: string): void {
	for (const [event, groups] of Object.entries(map)) {
		if (!EVENT_SET.has(event)) {
			const near = EVENTS.find((e) => e.toLowerCase() === event.toLowerCase());
			errors.push(
				near
					? `'${event}' is miscased — event names are case-sensitive, use '${near}'`
					: `'${event}' is not a hook event`,
			);
		}
		if (!Array.isArray(groups)) {
			errors.push(`${event}: must be an array of matcher groups`);
			continue;
		}
		for (const raw of groups) {
			const group = raw as Group;
			if (group?.matcher !== undefined) checkMatcher(event, str(group.matcher));
			if (!Array.isArray(group?.hooks)) {
				errors.push(`${event}: a matcher group has no \`hooks\` array`);
				continue;
			}
			for (const handler of group.hooks) checkHandler(event, handler as Handler, source);
		}
	}
}

/** Collect the command handlers registered for one event, matcher included for labeling. */
function commandHandlers(
	map: Record<string, unknown>,
	event: string,
): Array<{ matcher: string; handler: Handler }> {
	const out: Array<{ matcher: string; handler: Handler }> = [];
	const groups = map[event];
	if (!Array.isArray(groups)) return out;
	for (const raw of groups) {
		const group = raw as Group;
		if (!Array.isArray(group?.hooks)) continue;
		for (const handler of group.hooks) {
			if (str((handler as Handler).type) === 'command') {
				out.push({ matcher: str(group.matcher) || '*', handler: handler as Handler });
			}
		}
	}
	return out;
}

async function simulate(
	map: Record<string, unknown>,
	event: string,
	payloadPath: string | undefined,
): Promise<string[]> {
	const lines: string[] = [`\n## Simulation: ${event}\n`];

	if (!EVENT_SET.has(event)) {
		lines.push(`- ERROR: '${event}' is not a hook event`);
		errors.push(`--simulate: '${event}' is not a hook event`);
		return lines;
	}

	const handlers = commandHandlers(map, event);
	if (handlers.length === 0) {
		lines.push(`- No command handlers registered for ${event}.`);
		return lines;
	}

	const base = {
		session_id: 'simulated-session',
		transcript_path: '/dev/null',
		cwd: process.cwd(),
		permission_mode: 'default',
		hook_event_name: event,
	};
	const extra = payloadPath
		? (JSON.parse(await Bun.file(payloadPath).text()) as Record<string, unknown>)
		: ((PAYLOADS[event as EventName] ?? {}) as Record<string, unknown>);
	const payload = JSON.stringify({ ...base, ...extra });

	for (const { matcher, handler } of handlers) {
		const command = str(handler.command);
		const args = (handler.args as string[] | undefined) ?? [];
		const label = `${command}${args.length > 0 ? ` ${args.join(' ')}` : ''}`;
		lines.push(`### \`${label}\` (matcher: ${matcher})\n`);

		let proc: Bun.Subprocess<'pipe', 'pipe', 'pipe'>;
		try {
			proc =
				args.length > 0
					? Bun.spawn([command, ...args], { stdin: 'pipe', stdout: 'pipe', stderr: 'pipe' })
					: Bun.spawn(['sh', '-c', command], { stdin: 'pipe', stdout: 'pipe', stderr: 'pipe' });
		} catch (e) {
			lines.push(`- ERROR: could not spawn (${(e as Error).message})`);
			errors.push(`--simulate ${event}: could not spawn '${label}'`);
			continue;
		}

		proc.stdin.write(payload);
		await proc.stdin.end();
		const exitCode = await proc.exited;
		const stdout = (await new Response(proc.stdout).text()).trim();
		const stderr = (await new Response(proc.stderr).text()).trim();

		lines.push(`- exit code: ${exitCode}`);
		if (stdout) lines.push(`- stdout: ${stdout.length > 200 ? `${stdout.slice(0, 200)}…` : stdout}`);
		if (stderr) lines.push(`- stderr: ${stderr.length > 200 ? `${stderr.slice(0, 200)}…` : stderr}`);

		const looksJson = stdout.startsWith('{');
		let parsed: Record<string, unknown> | null = null;
		if (looksJson) {
			try {
				parsed = JSON.parse(stdout) as Record<string, unknown>;
			} catch {
				parsed = null;
			}
		}

		if (exitCode === 0) {
			if (looksJson && parsed === null) {
				errors.push(
					`--simulate ${event}: '${label}' printed something that starts with { but is not valid JSON — check for shell-profile output preceding it`,
				);
				lines.push('- **verdict:** stdout looks like JSON but does not parse; the output is discarded');
			} else if (parsed !== null) {
				const hso = parsed.hookSpecificOutput as Record<string, unknown> | undefined;
				if (parsed.additionalContext !== undefined && hso?.additionalContext === undefined) {
					errors.push(
						`--simulate ${event}: '${label}' places additionalContext at the top level, where it is silently ignored — nest it inside hookSpecificOutput`,
					);
					lines.push('- **verdict:** top-level `additionalContext` is silently ignored');
				} else if (parsed.decision === 'block' && !BLOCKING.has(event)) {
					warnings.push(
						`--simulate ${event}: '${label}' returns decision "block", but ${event} cannot block`,
					);
					lines.push(`- **verdict:** returns a block decision, but ${event} cannot block`);
				} else if (parsed.decision === 'block' || hso?.permissionDecision === 'deny') {
					lines.push('- **verdict:** blocks, via JSON on exit 0');
				} else {
					lines.push('- **verdict:** succeeds; JSON output is applied');
				}
			} else {
				lines.push(
					event === 'SessionStart' || event === 'UserPromptSubmit' || event === 'UserPromptExpansion'
						? '- **verdict:** succeeds; plain stdout is added as context for this event'
						: '- **verdict:** succeeds; stdout goes to the debug log only',
				);
			}
		} else if (exitCode === 2) {
			if (looksJson) {
				warnings.push(
					`--simulate ${event}: '${label}' printed JSON alongside exit 2, where JSON is discarded — stderr is used as the reason`,
				);
				lines.push('- **verdict:** blocks via exit 2; the JSON on stdout is discarded');
			} else if (BLOCKING.has(event)) {
				lines.push('- **verdict:** blocks, with stderr as the reason');
			} else {
				warnings.push(`--simulate ${event}: '${label}' exits 2, but ${event} cannot block`);
				lines.push(`- **verdict:** exits 2, but ${event} cannot block — stderr is shown and nothing stops`);
			}
		} else {
			if (BLOCKING.has(event)) {
				errors.push(
					`--simulate ${event}: '${label}' exits ${exitCode}, which is a non-blocking error — the action proceeds. Use exit 2 to block.`,
				);
				lines.push(
					`- **verdict:** exit ${exitCode} is a NON-BLOCKING error; the action proceeds regardless of intent`,
				);
			} else {
				lines.push(`- **verdict:** exit ${exitCode} is a non-blocking error; execution continues`);
			}
		}
	}

	return lines;
}

async function main(): Promise<number> {
	const argv = Bun.argv.slice(2);
	const strict = argv.includes('--strict');
	const simulateIdx = argv.indexOf('--simulate');
	const payloadIdx = argv.indexOf('--payload');
	const simulateEvent = simulateIdx === -1 ? undefined : argv[simulateIdx + 1];
	const payloadPath = payloadIdx === -1 ? undefined : argv[payloadIdx + 1];
	// Flag values are positional-looking; exclude only the indices a flag actually claimed.
	// Computing these unconditionally would make index 0 (the config path) look consumed
	// whenever the flag is absent and its index is -1.
	const consumed = new Set<number>();
	if (simulateIdx !== -1) consumed.add(simulateIdx + 1);
	if (payloadIdx !== -1) consumed.add(payloadIdx + 1);
	const positional = argv.filter((a, i) => !a.startsWith('--') && !consumed.has(i));
	const target = positional[0];

	if (target === undefined) {
		process.stdout.write(
			'Usage: bun validate_hooks.ts <hooks.json|settings.json> [--strict] [--simulate <Event>] [--payload <file.json>]\n\nValidates a hook configuration and optionally dry-runs its command handlers.\n',
		);
		return 2;
	}
	if (simulateIdx !== -1 && simulateEvent === undefined) {
		process.stdout.write('ERROR: --simulate requires an event name\n');
		return 2;
	}
	if (!(await Bun.file(target).exists())) {
		process.stdout.write(`ERROR: ${target} not found\n`);
		return 1;
	}

	let root: unknown;
	try {
		root = JSON.parse(await Bun.file(target).text());
	} catch (e) {
		process.stdout.write(
			`ERROR: ${target} does not parse as JSON (${(e as Error).message}). Hook config allows no comments and no trailing commas.\n`,
		);
		return 1;
	}

	const map = extractHookMap(root);
	if (map === null) {
		process.stdout.write(`ERROR: ${target} contains no \`hooks\` object and no recognizable events\n`);
		return 1;
	}

	const source = target.endsWith('SKILL.md') ? 'skill-frontmatter' : 'settings';
	checkConfig(map, source);

	const simulationLines =
		simulateEvent === undefined ? [] : await simulate(map, simulateEvent, payloadPath);

	const out: string[] = [`# Hook validation report: ${target}\n`];
	if (errors.length === 0 && warnings.length === 0) {
		out.push('Clean. No errors, no warnings.');
	}
	for (const e of errors) out.push(`- ERROR: ${e}`);
	for (const w of warnings) out.push(`- WARN: ${w}`);
	out.push(`\n${errors.length} error(s), ${warnings.length} warning(s)`);
	out.push(...simulationLines);
	process.stdout.write(`${out.join('\n')}\n`);

	return errors.length > 0 || (strict && warnings.length > 0) ? 1 : 0;
}

process.exit(await main());
