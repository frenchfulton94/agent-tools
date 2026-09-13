import { expect, test } from 'bun:test';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..', 'plugins', 'apple-studio');
const URL_RE = /https:\/\/developer\.apple\.com\/documentation\/[^\s"'<>\]]+/g;

/** Trim characters that belong to the prose, not the URL: trailing .,;: and
 *  unbalanced closing parens (symbol URLs contain balanced ones). */
function trimUrl(raw: string): string {
	let url = raw;
	for (;;) {
		if (/[.,;:]$/.test(url) && !url.endsWith('.md')) { url = url.slice(0, -1); continue; }
		if (url.endsWith(')')) {
			const open = (url.match(/\(/g) ?? []).length;
			const close = (url.match(/\)/g) ?? []).length;
			if (close > open) { url = url.slice(0, -1); continue; }
		}
		return url;
	}
}

function* walk(dir: string): Generator<string> {
	for (const name of readdirSync(dir)) {
		const p = join(dir, name);
		if (statSync(p).isDirectory()) yield* walk(p);
		else if (/\.(md|json|html)$/.test(name)) yield p;
	}
}

/**
 * Total curl verification (2026-09-13, every rewritten URL fetched, none
 * sampled) found 11 page-form links that genuinely have no `.md` form —
 * confirmed via `curl -w '%{content_type}'`, 404 in both cases below:
 *   - Legacy, pre-DocC framework index pages: ApplicationServices,
 *     CoreServices, Installer JS, IOKit, Kernel, PlaygroundBluetooth,
 *     PlaygroundSupport, TVMLKit JS, WebKit JS. Their symbol/article pages
 *     under the same framework DO have `.md` forms (e.g. `appkit.md` is
 *     `200 text/markdown`) — only these bare, non-DocC framework roots 404.
 *   - Two symbols whose bare name requires a disambiguation redirect
 *     (CKSyncEngine, CLBackgroundActivitySession): the bare URL redirects
 *     fine as text/html, and the *redirected*, hash-suffixed URL does have
 *     an `.md` form, but requesting `<bare-url>.md` directly 404s because
 *     the extension is matched before the redirect resolves. The hash
 *     suffix (e.g. `-5sie5`) isn't a stable identifier to hardcode, so
 *     these stay in page-form rather than pinning a fragile URL.
 * These are pinned exceptions, not a loophole: any new page-form link this
 * test flags outside this list is a real regression.
 */
const KNOWN_PAGE_FORM_EXCEPTIONS = new Set([
	'https://developer.apple.com/documentation/applicationservices',
	'https://developer.apple.com/documentation/cloudkit/cksyncengine',
	'https://developer.apple.com/documentation/corelocation/clbackgroundactivitysession',
	'https://developer.apple.com/documentation/coreservices',
	'https://developer.apple.com/documentation/installer_js',
	'https://developer.apple.com/documentation/iokit',
	'https://developer.apple.com/documentation/kernel',
	'https://developer.apple.com/documentation/playgroundbluetooth',
	'https://developer.apple.com/documentation/playgroundsupport',
	'https://developer.apple.com/documentation/tvmljs',
	'https://developer.apple.com/documentation/webkitjs',
]);

test('every page-form Apple documentation link in apple-studio ends in .md', () => {
	const offenders: string[] = [];
	for (const file of walk(ROOT)) {
		for (const m of readFileSync(file, 'utf8').matchAll(URL_RE)) {
			const url = trimUrl(m[0]);
			if (url.includes('#')) continue;
			if (url.endsWith('.md') || url.endsWith('.json')) continue;
			if (KNOWN_PAGE_FORM_EXCEPTIONS.has(url)) continue;
			offenders.push(`${file}: ${url}`);
		}
	}
	expect(offenders).toEqual([]);
});
