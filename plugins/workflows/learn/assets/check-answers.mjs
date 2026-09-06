#!/usr/bin/env node
/* =============================================================================
   check-answers.mjs — authoring check for the quiz component.
   -----------------------------------------------------------------------------
   Every choice in a quiz must be the same number of words, and within four
   characters of every other choice. A longer, hedgier, or more specific option
   is a free clue, and a free clue turns retrieval practice into pattern
   matching. quiz.js warns about this in the browser console; this script finds
   it before the lesson ships.

   Also checks that each quiz has exactly one data-correct choice.

   Run by hand from the workspace root:

       node assets/check-answers.mjs lessons/*.html

   With no arguments it checks every .html file under lessons/ and reference/.
   Exits non-zero when anything fails, so it can be chained into a build later
   if that ever earns its place. It is deliberately NOT a package script: this
   repository's convention is that every CI step is a package script, and this
   check has no business gating the whole marketplace's test run.

   Regex parsing, not a DOM: the input is markup this workspace authors to one
   documented shape, and a dependency for one authoring check is a bad trade.
   ========================================================================== */

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, relative } from 'node:path';

const QUIZ = /<div class="quiz"[^>]*data-quiz[^>]*>([\s\S]*?)<\/div>/g;
const CHOICE = /<button\b([^>]*)>([\s\S]*?)<\/button>/g;
const PROMPT = /<p class="quiz-prompt">([\s\S]*?)<\/p>/;
const TAG = /<[^>]+>/g;
const ENTITY = /&(?:nbsp|amp|lt|gt|quot|#39|mdash|ndash|hellip);/g;
const WS = /\s+/g;

const CHAR_SPREAD = 4;

/** Visible text of a markup fragment, entity-collapsed so counts match what a reader sees. */
function text(fragment) {
	return fragment
		.replace(TAG, '')
		.replace(ENTITY, 'x')
		.replace(WS, ' ')
		.trim();
}

function walk(dir) {
	if (!existsSync(dir)) return [];
	return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
		const path = join(dir, entry.name);
		if (entry.isDirectory()) return walk(path);
		return entry.isFile() && entry.name.endsWith('.html') ? [path] : [];
	});
}

const targets = process.argv.slice(2);
const files = targets.length > 0 ? targets : [...walk('lessons'), ...walk('reference')];

let quizzes = 0;
const problems = [];

for (const file of files) {
	let source;
	try {
		source = readFileSync(file, 'utf8');
	} catch (err) {
		problems.push(`${file}: unreadable — ${err.message}`);
		continue;
	}

	for (const [, body] of source.matchAll(QUIZ)) {
		quizzes += 1;
		const label = text(body.match(PROMPT)?.[1] ?? '').slice(0, 64) || '(no prompt)';
		const where = `${relative(process.cwd(), file)} · "${label}"`;

		const choices = [...body.matchAll(CHOICE)].map(([, attrs, inner]) => ({
			correct: /\bdata-correct\b/.test(attrs),
			hasFeedback: /\bdata-feedback\s*=/.test(attrs),
			label: text(inner),
		}));

		if (choices.length < 2) {
			problems.push(`${where}: ${choices.length} choice(s); need at least 2.`);
			continue;
		}

		const correct = choices.filter((c) => c.correct).length;
		if (correct !== 1) {
			problems.push(`${where}: ${correct} choices marked data-correct; expected exactly 1.`);
		}

		const missing = choices.filter((c) => !c.hasFeedback).length;
		if (missing > 0) {
			problems.push(`${where}: ${missing} choice(s) without data-feedback.`);
		}

		const wordCounts = choices.map((c) => c.label.split(WS).filter(Boolean).length);
		if (new Set(wordCounts).size > 1) {
			problems.push(
				`${where}: word counts differ (${wordCounts.join('/')}) — ` +
					choices.map((c) => `"${c.label}"`).join(' vs '),
			);
		}

		const lengths = choices.map((c) => c.label.length);
		const spread = Math.max(...lengths) - Math.min(...lengths);
		if (spread > CHAR_SPREAD) {
			problems.push(
				`${where}: character spread ${spread} > ${CHAR_SPREAD} (${lengths.join('/')}) — ` +
					choices.map((c) => `"${c.label}"`).join(' vs '),
			);
		}
	}
}

const scope = files.length === 1 ? files[0] : `${files.length} files`;
if (problems.length === 0) {
	console.log(`ok — ${quizzes} quiz${quizzes === 1 ? '' : 'zes'} across ${scope}`);
	process.exit(0);
}

console.error(`${problems.length} problem(s) across ${scope}:\n`);
for (const problem of problems) console.error(`  - ${problem}`);
process.exit(1);
