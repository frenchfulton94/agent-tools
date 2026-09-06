#!/usr/bin/env bun

/**
 * validate_skill.ts — validate an Agent Skill directory against the skill spec.
 *
 * Usage:
 *   bun validate_skill.ts <skill-dir> [--strict]
 *
 * Checks frontmatter constraints, naming rules, size limits, reference depth, tables of
 * contents, and description anti-patterns. Prints a markdown report.
 *
 * Exit codes: 0 = clean (warnings allowed unless --strict), 1 = errors found (or warnings
 * found with --strict).
 *
 * Frontmatter is parsed with `Bun.YAML`, not a regex. The previous hand-rolled parser
 * folded a YAML comment line into the preceding value, so
 *
 *     name: my-skill
 *     # a comment
 *
 * reported `name` as "my-skill # a comment" and emitted two spurious errors.
 *
 * No dependencies beyond Bun itself.
 */

import { Glob } from 'bun';

const NAME_MAX = 64;
const DESC_MAX = 1024;
const BODY_ERROR_LINES = 500; // spec: keep SKILL.md under 500 lines
const BODY_WARN_LINES = 200; // above this, consider splitting into references/
const TOC_MIN_LINES = 100; // reference files longer than this need a TOC
const TOC_SCAN_LINES = 30; // a TOC must appear within the first 30 lines
const RESERVED_WORDS = ['claude', 'anthropic'];
const NAME_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;
// Sequenced-workflow phrasing inside a description ("first X, then Y") signals the
// description-trap anti-pattern: agents may follow it and skip the body.
const SEQUENCE_RE =
	/\bfirst\b[\s\S]*\bthen\b|\bthen\b[\s\S]*\bfinally\b|\bstep\s*[12]\b|^\s*\d+\.\s/i;

const errors: string[] = [];
const warnings: string[] = [];

/**
 * Split into lines the way Python's `str.splitlines()` does — i.e. a trailing newline does
 * NOT produce a final empty element. Plain `split('\n')` reports one extra line for every
 * file that ends in a newline (which is all of them), shifting every size threshold by one.
 */
function splitLines(text: string): string[] {
	const parts = text.split('\n');
	if (parts.length > 0 && parts[parts.length - 1] === '') parts.pop();
	return parts;
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

function str(v: unknown): string {
	return typeof v === 'string' ? v : v === undefined || v === null ? '' : String(v);
}

function checkFrontmatter(fields: Record<string, unknown>, skillDirName: string): void {
	const name = str(fields.name);
	const desc = str(fields.description);

	if (!name) {
		errors.push('`name` is missing or empty');
	} else {
		if (name.length > NAME_MAX) errors.push(`\`name\` is ${name.length} chars (max ${NAME_MAX})`);
		if (!NAME_RE.test(name)) {
			errors.push(
				`\`name\` '${name}' violates naming rules (lowercase a-z0-9, single hyphens, no edge hyphens)`,
			);
		}
		if (name !== skillDirName) {
			errors.push(`\`name\` '${name}' does not match directory '${skillDirName}'`);
		}
		for (const word of RESERVED_WORDS) {
			if (name.includes(word)) errors.push(`\`name\` contains reserved word '${word}'`);
		}
		if (name.includes('<') || name.includes('>')) {
			errors.push('`name` contains XML-tag characters');
		}
	}

	if (!desc) {
		errors.push('`description` is missing or empty');
	} else {
		if (desc.length > DESC_MAX) {
			errors.push(`\`description\` is ${desc.length} chars (max ${DESC_MAX})`);
		}
		if (desc.includes('<') || desc.includes('>')) {
			errors.push('`description` contains XML-tag characters');
		}
		if (/^(i |you |we )/i.test(desc)) {
			warnings.push('`description` is not third person (starts with I/you/we)');
		}
		if (SEQUENCE_RE.test(desc)) {
			warnings.push(
				'`description` may contain sequenced workflow steps (description-trap risk: agents can follow the description and skip the body)',
			);
		}
		const lower = desc.toLowerCase();
		if (!lower.includes('use when') && !lower.includes('use this')) {
			warnings.push("`description` has no 'Use when...' trigger clause");
		}
	}
}

async function checkBody(body: string, skillDir: string): Promise<void> {
	const lines = splitLines(body);
	const n = lines.length;
	if (n > BODY_ERROR_LINES) {
		errors.push(`SKILL.md body is ${n} lines (spec limit ${BODY_ERROR_LINES})`);
	} else if (n > BODY_WARN_LINES) {
		warnings.push(`SKILL.md body is ${n} lines (consider splitting above ${BODY_WARN_LINES})`);
	}

	// Quoted or code-formatted MUST/CAPS are usually the skill *discussing* the
	// anti-pattern, not committing it — strip those spans before counting.
	let prose = body.replace(/```[\s\S]*?```/g, '');
	prose = prose.replace(/`[^`\n]*`/g, '');
	prose = prose.replace(/"[^"\n]*"/g, '');

	const capsRuns = prose.match(/\b(?:[A-Z]{3,}[ ,:]+){2,}[A-Z]{3,}\b/g) ?? [];
	if (capsRuns.length > 0) {
		warnings.push(`all-caps emphasis runs found (${capsRuns.length}): emphasis inflation`);
	}

	const mustDensity = (prose.match(/\b(MUST|NEVER|CRITICAL|ALWAYS)\b/g) ?? []).length;
	if (mustDensity > 3) {
		warnings.push(`${mustDensity} occurrences of MUST/NEVER/CRITICAL/ALWAYS in body prose`);
	}

	// Referenced-path bookkeeping: every bundled file should be mentioned, and references
	// should be one level deep from the skill root.
	const mentioned = new Set(body.match(/(?:references|scripts|assets|evals)\/[\w./-]+/g) ?? []);
	for (const sub of ['references', 'scripts', 'assets']) {
		const dir = `${skillDir}/${sub}`;
		const found: string[] = [];
		try {
			for await (const entry of new Glob('**/*').scan({ cwd: dir, onlyFiles: true })) {
				found.push(entry);
			}
		} catch {
			continue; // directory absent
		}
		for (const entry of found.sort()) {
			const base = entry.split('/').pop() ?? entry;
			if (base.startsWith('.')) continue;
			const rel = `${sub}/${entry}`;
			if (rel.split('/').length > 2) {
				warnings.push(`${rel}: nested deeper than one level below the skill root`);
			}
			if (!mentioned.has(rel) && sub !== 'assets') {
				warnings.push(`${rel}: not referenced from SKILL.md`);
			}
		}
	}
	for (const rel of [...mentioned].sort()) {
		if (/\.(md|py|sh|js|ts|mjs)$/.test(rel) && !(await Bun.file(`${skillDir}/${rel}`).exists())) {
			errors.push(`SKILL.md references ${rel}, which does not exist`);
		}
	}
}

async function checkReferences(skillDir: string): Promise<void> {
	const dir = `${skillDir}/references`;
	const files: string[] = [];
	try {
		for await (const entry of new Glob('*.md').scan({ cwd: dir, onlyFiles: true })) {
			files.push(entry);
		}
	} catch {
		return;
	}
	for (const name of files.sort()) {
		const lines = splitLines(await Bun.file(`${dir}/${name}`).text());
		if (lines.length <= TOC_MIN_LINES) continue;
		const head = lines.slice(0, TOC_SCAN_LINES).join('\n').toLowerCase();
		const anchorCount = (head.match(/\]\(#/g) ?? []).length;
		if (!head.includes('contents') && anchorCount < 3) {
			warnings.push(
				`references/${name}: ${lines.length} lines with no table of contents in the first ${TOC_SCAN_LINES} lines`,
			);
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
			'Usage: bun validate_skill.ts <skill-dir> [--strict]\n\nValidates an Agent Skill directory against the skill spec.\n',
		);
		return 2;
	}

	const skillDir = target.replace(/\/+$/, '');
	const skillDirName = skillDir.split('/').pop() ?? skillDir;
	const skillMd = `${skillDir}/SKILL.md`;
	if (!(await Bun.file(skillMd).exists())) {
		process.stdout.write(`ERROR: ${skillMd} not found\n`);
		return 1;
	}

	const { fields, body } = parseFrontmatter(await Bun.file(skillMd).text());
	if (fields === null) {
		process.stdout.write('ERROR: SKILL.md has no YAML frontmatter block\n');
		return 1;
	}

	checkFrontmatter(fields, skillDirName);
	await checkBody(body, skillDir);
	await checkReferences(skillDir);

	const out: string[] = [`# Validation report: ${skillDirName}\n`];
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
