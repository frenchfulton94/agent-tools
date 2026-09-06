#!/usr/bin/env node
/* =============================================================================
   build.mjs — assemble the publishable half of the learn workspace into
   site/dist/, which is what the Pages workflow uploads.
   -----------------------------------------------------------------------------
   The workspace root is not the site root, and that is the whole point of this
   script. `MISSION.md`, `RESOURCES.md`, `NOTES.md` and `learning-records/` are
   working files for whoever maintains the package; publishing the directory
   wholesale would put them on the site as a side effect of a deploy rather
   than as a decision. This copies exactly the four publishable things and
   nothing else.

   Zero dependencies, node builtins only — this repository's convention is that
   every CI step is a package script, and a copy does not earn a bundler.

   Run:  bun run learn:build      (or: node plugins/workflows/learn/site/build.mjs)
   ========================================================================== */

import {
	cpSync,
	existsSync,
	mkdirSync,
	readFileSync,
	readdirSync,
	rmSync,
	statSync,
	writeFileSync,
} from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const siteDir = dirname(fileURLToPath(import.meta.url));
const workspace = resolve(siteDir, '..');
const dist = join(siteDir, 'dist');

/** Exactly what ships. Anything not named here stays a working file. */
const PUBLISH = ['index.html', 'lessons', 'reference', 'assets'];

/**
 * Lessons cite the plugin source by relative path, which is correct when the
 * workspace is read from a checkout and broken once `learn/` is the site root —
 * every `../` escapes the published tree. The build rewrites those to blob URLs
 * so the local copy keeps working relative links and the published copy gets
 * working absolute ones. Change this if the repository moves.
 */
const BLOB = 'https://github.com/YOUR-GITHUB-OWNER/agent-tools/blob/main/plugins/workflows';

const missing = PUBLISH.filter((entry) => !existsSync(join(workspace, entry)));
if (missing.length > 0) {
	console.error(`build: missing from the workspace: ${missing.join(', ')}`);
	console.error(`build: expected them under ${workspace}`);
	process.exit(1);
}

rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });

for (const entry of PUBLISH) {
	cpSync(join(workspace, entry), join(dist, entry), { recursive: true });
}

// GitHub Pages runs Jekyll unless told not to, and Jekyll silently drops any
// path segment beginning with an underscore. Nothing here starts with one
// today; this keeps that from becoming a trap for whoever adds the first file
// that does.
writeFileSync(join(dist, '.nojekyll'), '');

const walk = (dir) =>
	readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
		const path = join(dir, e.name);
		return e.isDirectory() ? walk(path) : [path];
	});

// Rewrite every href that resolves outside the site root. Anything left
// pointing outward after this is a link that would 404 on the deployed site,
// so it fails the build rather than shipping quietly.
let rewritten = 0;
const stillEscaping = [];

const pluginRoot = resolve(workspace, '..');

for (const file of walk(dist).filter((f) => f.endsWith('.html'))) {
	// Hrefs were authored relative to the workspace, so resolve them from the
	// file's WORKSPACE location. Resolving from its dist location would fold
	// `site/dist` into every rewritten path.
	const authoredDir = dirname(join(workspace, relative(dist, file)));
	const original = readFileSync(file, 'utf8');
	const updated = original.replace(/href="([^":#]+?)((?:#[^"]*)?)"/g, (whole, href, hash) => {
		if (/^(?:https?:|mailto:|data:|\/)/.test(href)) return whole;
		const target = resolve(authoredDir, href);
		if (target === workspace || target.startsWith(workspace + '/')) return whole;
		// Outside the workspace: express it relative to the plugin root, and
		// point at the blob so the deployed page has a link that works.
		const fromPlugin = relative(pluginRoot, target);
		if (fromPlugin.startsWith('..')) {
			stillEscaping.push(`${relative(dist, file)} -> ${href}`);
			return whole;
		}
		rewritten += 1;
		return `href="${BLOB}/${fromPlugin.split('\\').join('/')}${hash}"`;
	});
	if (updated !== original) writeFileSync(file, updated);
}

if (stillEscaping.length > 0) {
	console.error('build: links that would 404 on the deployed site:');
	for (const link of stillEscaping) console.error(`  - ${link}`);
	process.exit(1);
}

const files = walk(dist);
const bytes = files.reduce((sum, f) => sum + statSync(f).size, 0);
const pages = files.filter((f) => f.endsWith('.html')).length;

console.log(`build: ${pages} pages, ${files.length} files, ${(bytes / 1024).toFixed(0)}KB`);
console.log(`build: ${rewritten} source link(s) rewritten to blob URLs`);
console.log(`build: ${relative(process.cwd(), dist) || dist}`);
