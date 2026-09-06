/**
 * Verifies the citations in a security review report against the vendored OWASP corpus.
 *
 * The plugin's claim is that findings are grounded in a real, pinned source. Nothing enforced that
 * — a grep of the generated index alone yields a filename and a plausible section heading without
 * opening a sheet, so a fabricated citation looked identical to a real one. This closes that: a
 * quote that cannot be found in the cited section is reported, and a review that never opened the
 * section cannot produce one.
 *
 * Usage:
 *   bun verify-citations.ts <report.md>
 *
 * Exit codes: 0 = every citation verified, 1 = at least one failed, 2 = usage error.
 */

import { existsSync } from 'node:fs';

export interface Citation {
	severity: string;
	file: string;
	section: string;
	quote?: string;
	/**
	 * True when a `**Quote:**` line was present but did not match the strict `"..."` shape (a
	 * typographic quote, a trailing period outside the closing quote, or similar). Distinguished
	 * from an honest omission so the parser cannot silently turn an unparseable quote into UNQUOTED.
	 */
	quoteMalformed?: true;
}

/** Why a quote failed to verify, distinct from "no quote was given at all". */
export type QuoteProblem = 'malformed' | 'too-short' | 'not-found';

export interface CitationResult {
	citation: Citation;
	fileOk: boolean;
	sectionOk: boolean;
	/** null when the finding carries no quote — unverified, which is not the same as failed. */
	quoteOk: boolean | null;
	/** Set only when quoteOk is false — which of the distinct ways verification failed. */
	quoteProblem?: QuoteProblem;
}

/** Collapses whitespace so a re-wrapped quote still matches the sheet it came from. */
export function normalize(text: string): string {
	return text.replace(/\s+/g, ' ').trim();
}

const SOURCE_RE = /^\*\*Source:\*\*\s*`([^`]+)`\s*§\s*(.+)$/;
const QUOTE_RE = /^\*\*Quote:\*\*\s*"(.+)"\s*$/;
// Any line that opens the Quote field at all, whether or not it goes on to match QUOTE_RE. Used to
// tell an honest omission (no such line) apart from a line the strict pattern couldn't parse.
const QUOTE_LINE_RE = /^\*\*Quote:\*\*/;
const HEADING_RE = /^###\s*\[([A-Z]+)\]/;

/**
 * Findings are `### [SEVERITY] ...` blocks. Source and Quote are read per block rather than
 * globally, so a quote can never be paired with a different finding's source.
 */
export function parseCitations(report: string): Citation[] {
	const out: Citation[] = [];
	let severity = '';
	let file: string | null = null;
	let section = '';
	let quote: string | undefined;
	let quoteMalformed = false;

	const flush = (): void => {
		if (file !== null) {
			out.push({
				severity,
				file,
				section,
				...(quote === undefined ? {} : { quote }),
				...(quoteMalformed ? { quoteMalformed: true as const } : {}),
			});
		}
		file = null;
		quote = undefined;
		quoteMalformed = false;
	};

	for (const line of report.split('\n')) {
		const h = HEADING_RE.exec(line);
		if (h) {
			flush();
			severity = h[1] ?? '';
			continue;
		}
		const s = SOURCE_RE.exec(line);
		if (s) {
			file = s[1] ?? '';
			section = (s[2] ?? '').trim();
			continue;
		}
		const q = QUOTE_RE.exec(line);
		if (q) {
			quote = q[1];
			continue;
		}
		// A line that opens the Quote field but doesn't match the strict pattern (typographic
		// quotes, trailing text after the closing quote, etc.) is a malformed quote, not a missing
		// one — flag it rather than silently leaving `quote` unset.
		if (QUOTE_LINE_RE.test(line)) quoteMalformed = true;
	}
	flush();
	return out;
}

/** A quote of fewer than this many words identifies no passage — see references/findings.md. */
const MIN_QUOTE_WORDS = 5;

export async function verifyCitation(c: Citation, corpusDir: string): Promise<CitationResult> {
	const path = `${corpusDir}${c.file}`;
	if (!existsSync(path)) {
		const quoteFails = c.quoteMalformed === true || c.quote !== undefined;
		return {
			citation: c,
			fileOk: false,
			sectionOk: false,
			quoteOk: quoteFails ? false : null,
			...(c.quoteMalformed === true
				? { quoteProblem: 'malformed' as const }
				: c.quote !== undefined
					? { quoteProblem: 'not-found' as const }
					: {}),
		};
	}
	const text = await Bun.file(path).text();

	// Headings carry inline markdown in this corpus — `#### Use `innerHTML` with extreme caution`
	// and `### GUIDELINE \#8 ... object\[x\] accessors` are both real. A reviewer transcribing a
	// heading as it reads should not fail for omitting backticks, so strip them before comparing.
	const headingText = (raw: string): string => normalize(raw.replace(/[`*]/g, '').replace(/\\/g, '')).toLowerCase();
	const wanted = headingText(c.section);

	// Any heading depth: sections cited from a sheet may be ## or deeper.
	const headings = [...text.matchAll(/^(#{2,6})\s+(.+)$/gm)];

	// Heading text is not unique — 20 sheets repeat one, and JSON_Web_Token_Cheat_Sheet.md has six
	// `#### How to Prevent`. Taking only the first match failed correct citations of every later
	// one, and the cheapest way to satisfy "fix the citation" is to delete the quote. Search them
	// all; the quote need only be in one.
	const matches = headings.filter((m) => headingText(m[2] ?? '') === wanted);
	const sectionOk = matches.length > 0;

	// The quote must appear inside the CITED SECTION, not merely somewhere in the file. Searching
	// the whole file let a quote lifted from one section verify under a different one, so a
	// reviewer who grepped without opening the cited section passed — which defeats the point.
	// The body runs to the next heading of the same or shallower level, so subsections count.
	let quoteOk: boolean | null = null;
	let quoteProblem: QuoteProblem | undefined;
	if (c.quoteMalformed === true) {
		quoteOk = false;
		quoteProblem = 'malformed';
	} else if (c.quote !== undefined) {
		// A quote below the floor identifies no passage — "the" verifies against nearly any
		// section, which defeats the point of requiring a quote at all. Checked before the section
		// search so a short quote is never reported as merely "not found".
		const wordCount = normalize(c.quote).split(' ').filter(Boolean).length;
		if (wordCount < MIN_QUOTE_WORDS) {
			quoteOk = false;
			quoteProblem = 'too-short';
		} else if (!sectionOk) {
			quoteOk = false;
			quoteProblem = 'not-found';
		} else {
			const needle = normalize(c.quote);
			quoteOk = matches.some((hit) => {
				const start = hit.index + hit[0].length;
				const depth = (hit[1] ?? '#').length;
				const after = text.slice(start);
				const next = new RegExp(`^#{2,${depth}}\\s+`, 'm').exec(after);
				const body = next === null ? after : after.slice(0, next.index);
				return normalize(body).includes(needle);
			});
			if (!quoteOk) quoteProblem = 'not-found';
		}
	}
	return { citation: c, fileOk: true, sectionOk, quoteOk, ...(quoteProblem ? { quoteProblem } : {}) };
}

const CORPUS_DIR = new URL('../owasp/', import.meta.url).pathname;

async function main(): Promise<number> {
	const path = Bun.argv.slice(2).find((a) => !a.startsWith('--'));
	if (path === undefined) {
		console.error('Usage: bun verify-citations.ts <report.md>\n');
		return 2;
	}
	if (!existsSync(path)) {
		console.error(`ERROR: ${path} not found`);
		return 2;
	}

	const citations = parseCitations(await Bun.file(path).text());
	if (citations.length === 0) {
		// Exit 0, not 1. The "Nothing found" report format is a legitimate clean result with zero
		// findings and therefore zero Source lines, and this script is the gate a baseline audit
		// runs against its own output — failing here would reject every clean review.
		console.log('No citations to check. Expected for a report with no findings.');
		return 0;
	}

	let failed = 0;
	let unverified = 0;
	for (const c of citations) {
		const r = await verifyCitation(c, CORPUS_DIR);
		const problems: string[] = [];
		if (!r.fileOk) problems.push('sheet not in corpus');
		else if (!r.sectionOk) problems.push(`no section "${c.section}"`);
		// Distinct reasons: quotes are scoped to the cited section, so "not found" here means the
		// quote is not in THAT section (it may well be elsewhere in the sheet — the misattribution
		// case this scoping exists to catch), which reads very differently from "too short to
		// identify a passage" or "the Quote line itself didn't parse".
		if (r.quoteOk === false) {
			problems.push(
				r.quoteProblem === 'too-short'
					? 'quote too short'
					: r.quoteProblem === 'malformed'
						? 'quote line malformed'
						: 'quote not found in cited section',
			);
		}

		if (problems.length > 0) {
			failed++;
			console.log(`FAIL  [${c.severity}] ${c.file} § ${c.section} — ${problems.join('; ')}`);
		} else if (r.quoteOk === null) {
			unverified++;
			console.log(`UNQUOTED  [${c.severity}] ${c.file} § ${c.section} — section verified, no quote to check`);
		} else {
			console.log(`ok    [${c.severity}] ${c.file} § ${c.section}`);
		}
	}

	console.log(
		`\n${citations.length} citation(s): ${citations.length - failed - unverified} verified, ${unverified} unquoted, ${failed} failed`,
	);
	return failed > 0 ? 1 : 0;
}

if (import.meta.main) process.exit(await main());
