#!/usr/bin/env bun

/**
 * lint_prompt.ts — advisory linter for prompt text: flags patterns that are deprecated or
 * counterproductive on current Claude models.
 *
 * Usage:
 *   bun lint_prompt.ts <prompt-file>
 *   cat prompt.txt | bun lint_prompt.ts -
 *
 * Prints markdown findings with line numbers. Advisory only: always exits 0 (findings are
 * signals for a human/agent rewrite pass, not build failures).
 *
 * No dependencies beyond Bun itself.
 */

interface Rule {
	id: string;
	re: RegExp;
	message: string;
}

// Heuristics tuned for low false-positive rates on prose prompts.
const RULES: Rule[] = [
	{
		id: 'prefill',
		message:
			'Prefill-style instruction — assistant prefill is rejected by current models; use structured outputs or "Return only ..." instead.',
		re: /begin your (response|answer|output) with|start your (response|answer) with|prefill/i,
	},
	{
		id: 'thinking-budget',
		message:
			'Manual thinking scaffold — use adaptive thinking + effort settings; keep at most a brief targeted "consider X" nudge.',
		re: /budget_tokens|<thinking>|think step[- ]by[- ]step/i,
	},
	{
		id: 'reasoning-echo',
		message:
			'Reasoning-echo instruction — can trigger refusals on newest models; ask for the result plus a brief stated rationale.',
		re: /(show|reveal|output|transcribe|explain)\s+(me\s+)?your\s+(internal\s+)?(thinking|thought process|chain of thought|reasoning)/i,
	},
	{
		id: 'sampling-params',
		message: 'Sampling parameter — rejected on newest models; steer tone/variety via instructions.',
		re: /\b(temperature|top_p|top_k)\s*[:=]/i,
	},
	{
		id: 'emphasis-caps',
		// three or more consecutive ALL-CAPS words of length >= 3
		message:
			'All-caps emphasis run — current models over-trigger on shouted rules; rephrase normally.',
		re: /\b[A-Z]{3,}(?:[ ,:]+[A-Z]{3,}){2,}\b/,
	},
];

// Density rules evaluated over the whole text rather than per line.
const MUST_WORDS = /\b(MUST|NEVER|ALWAYS|CRITICAL)\b/g;
const NEGATION = /\b(do not|don't|never)\b/i;
const INSTEAD = /\binstead\b|\brather\b|\buse\b/i;
const MUST_DENSITY_PER_WORDS = 40; // flag when more than 1 MUST-word per 40 words

interface Finding {
	line: number;
	id: string;
	message: string;
	excerpt: string;
}

async function readInput(arg: string): Promise<string> {
	if (arg === '-') return await Bun.stdin.text();
	return await Bun.file(arg).text();
}

async function main(): Promise<number> {
	const arg = Bun.argv[2];
	if (arg === undefined || arg === '--help' || arg === '-h') {
		process.stdout.write(
			[
				'Usage: bun lint_prompt.ts <prompt-file>',
				'       cat prompt.txt | bun lint_prompt.ts -',
				'',
				'Advisory linter for prompt text. Always exits 0.',
				'',
			].join('\n'),
		);
		return 0;
	}

	let text: string;
	try {
		text = await readInput(arg);
	} catch (err) {
		process.stdout.write(`Error: could not read ${arg}: ${(err as Error).message}\n`);
		process.stdout.write("Expected: a readable file path, or '-' for stdin.\n");
		return 0;
	}

	const lines = text.split('\n');
	const findings: Finding[] = [];

	for (const [i, line] of lines.entries()) {
		for (const rule of RULES) {
			if (rule.re.test(line)) {
				findings.push({
					excerpt: line.trim().slice(0, 100),
					id: rule.id,
					line: i + 1,
					message: rule.message,
				});
			}
		}
	}

	const words = text.split(/\s+/).filter(Boolean).length;
	const musts = text.match(MUST_WORDS)?.length ?? 0;
	if (words > 0 && musts > Math.max(1, Math.floor(words / MUST_DENSITY_PER_WORDS))) {
		findings.push({
			excerpt: '',
			id: 'emphasis-density',
			line: 0,
			message: `${musts} MUST/NEVER/ALWAYS/CRITICAL in ${words} words — emphasis inflation; state rules once, normally.`,
		});
	}

	// Negative instructions with no nearby positive alternative.
	for (const [i, line] of lines.entries()) {
		if (!NEGATION.test(line)) continue;
		// Python's lines[max(0, i-2) : i+1] with 1-based i == 0-based slice [i-2, i+1).
		const window = lines.slice(Math.max(0, i - 1), i + 2).join(' ');
		if (!INSTEAD.test(window)) {
			findings.push({
				excerpt: line.trim().slice(0, 100),
				id: 'negative-only',
				line: i + 1,
				message: 'Prohibition with no positive alternative nearby — state what TO do instead.',
			});
		}
	}

	const out: string[] = [`# Prompt lint: ${arg}\n`];
	if (findings.length === 0) {
		out.push('No modern-model anti-patterns found.');
	} else {
		for (const f of findings) {
			out.push(`- [${f.id}] ${f.line ? `line ${f.line}` : 'whole text'}: ${f.message}`);
			if (f.excerpt) out.push(`  > ${f.excerpt}`);
		}
	}
	out.push(`\n${findings.length} finding(s). Advisory only — verify each in context.`);
	process.stdout.write(`${out.join('\n')}\n`);
	return 0;
}

process.exit(await main());
