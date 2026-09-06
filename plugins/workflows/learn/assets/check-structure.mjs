#!/usr/bin/env node
/* =============================================================================
   check-structure.mjs — proves every lesson's element nesting is well-formed.
   -----------------------------------------------------------------------------
   This exists because of a real bug. A scripted edit meant to add a class to a
   `<th>` used the pattern /<th([^>]*)>/, which also matches `<thead>` — `<th`
   followed by `ead` — and so replaced five `<thead>` opening tags with
   `<th class="...">`. Every page still rendered, every link still resolved, the
   brand linter still passed, and the tables quietly lost their header rows.

   A tag-counting check would not have caught it either: closing tags here are
   often split across lines (`</strong\n>`), so counting `</strong>` literals
   reports imbalances that do not exist. This walks a stack instead, which is
   the only version that is actually right.

   Run from the workspace root:

       node assets/check-structure.mjs

   Exits non-zero on any unclosed, misnested, or stray closing tag.
   ========================================================================== */

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, relative } from 'node:path';

/** Elements with no closing tag. */
const VOID = new Set([
	'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
	'link', 'meta', 'param', 'source', 'track', 'wbr',
]);

/** Elements whose closing tag HTML lets you omit. None are omitted here, but a
 *  parser that assumed otherwise would produce confusing errors. */
const OPTIONAL_CLOSE = new Set(['li', 'p', 'td', 'th', 'tr', 'thead', 'tbody', 'dt', 'dd', 'option']);

const TAG = /<(\/?)([a-zA-Z][a-zA-Z0-9-]*)((?:[^>"']|"[^"]*"|'[^']*')*)>/g;

function lineOf(text, index) {
	return text.slice(0, index).split('\n').length;
}

function check(file) {
	const text = readFileSync(file, 'utf8');
	// Comments and raw-text elements must not be tokenized as markup.
	const scannable = text
		.replace(/<!--[\s\S]*?-->/g, (m) => ' '.repeat(m.length))
		.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, (m) => ' '.repeat(m.length));

	const stack = [];
	const problems = [];

	for (const m of scannable.matchAll(TAG)) {
		const [whole, slash, rawName, attrs] = m;
		const name = rawName.toLowerCase();
		if (VOID.has(name)) continue;
		if (attrs.trimEnd().endsWith('/')) continue; // self-closed

		if (!slash) {
			stack.push({ name, line: lineOf(text, m.index) });
			continue;
		}

		if (stack.length === 0) {
			problems.push(`line ${lineOf(text, m.index)}: stray </${name}>`);
			continue;
		}

		const top = stack[stack.length - 1];
		if (top.name === name) {
			stack.pop();
			continue;
		}

		// A mismatch. If the expected element allows an omitted close, unwind
		// through those; otherwise it is a genuine nesting error.
		let depth = stack.length - 1;
		while (depth >= 0 && stack[depth].name !== name) depth -= 1;
		if (depth < 0) {
			problems.push(`line ${lineOf(text, m.index)}: </${name}> with no matching open (innermost open is <${top.name}> from line ${top.line})`);
			continue;
		}
		const skipped = stack.slice(depth + 1).filter((e) => !OPTIONAL_CLOSE.has(e.name));
		if (skipped.length > 0) {
			problems.push(
				`line ${lineOf(text, m.index)}: </${name}> closes across unclosed ` +
					skipped.map((e) => `<${e.name}> (line ${e.line})`).join(', '),
			);
		}
		stack.length = depth;
	}

	for (const open of stack) {
		if (OPTIONAL_CLOSE.has(open.name)) continue;
		problems.push(`line ${open.line}: <${open.name}> is never closed`);
	}

	return problems;
}

function walk(dir) {
	if (!existsSync(dir)) return [];
	return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
		const path = join(dir, e.name);
		if (e.isDirectory()) return walk(path);
		return e.isFile() && e.name.endsWith('.html') ? [path] : [];
	});
}

const args = process.argv.slice(2);
const files = args.length > 0 ? args : ['index.html', ...walk('lessons'), ...walk('reference')].filter(existsSync);

let failed = 0;
for (const file of files) {
	const problems = check(file);
	if (problems.length === 0) continue;
	failed += 1;
	console.error(`${relative(process.cwd(), file)}:`);
	for (const p of problems) console.error(`  - ${p}`);
}

if (failed > 0) {
	console.error(`\n${failed} of ${files.length} file(s) have malformed nesting`);
	process.exit(1);
}
console.log(`ok — nesting well-formed in ${files.length} file(s)`);
