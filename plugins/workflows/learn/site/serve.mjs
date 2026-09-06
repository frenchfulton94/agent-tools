#!/usr/bin/env node
/* =============================================================================
   serve.mjs — serve site/dist/ locally, so the preview is the built artifact
   rather than the workspace.
   -----------------------------------------------------------------------------
   Serving the workspace directly would preview a directory the deploy never
   publishes, which is how "it looked fine locally" happens. Build first; this
   refuses to start without a build.

   Zero dependencies, node:http only.

   Run:  bun run learn:preview        → http://localhost:4173
   Port: PORT=5000 bun run learn:preview
   ========================================================================== */

import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { dirname, extname, join, normalize, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), 'dist');
const port = Number(process.env.PORT ?? 4173);

if (!existsSync(join(root, 'index.html'))) {
	console.error('serve: no build found. Run `bun run learn:build` first.');
	console.error(`serve: expected ${join(root, 'index.html')}`);
	process.exit(1);
}

const TYPES = {
	'.html': 'text/html; charset=utf-8',
	'.css': 'text/css; charset=utf-8',
	'.js': 'text/javascript; charset=utf-8',
	'.mjs': 'text/javascript; charset=utf-8',
	'.json': 'application/json; charset=utf-8',
	'.svg': 'image/svg+xml',
	'.woff2': 'font/woff2',
	'.png': 'image/png',
	'.md': 'text/markdown; charset=utf-8',
	'.txt': 'text/plain; charset=utf-8',
};

const server = createServer((req, res) => {
	const url = new URL(req.url ?? '/', `http://localhost:${port}`);
	let pathname;
	try {
		pathname = decodeURIComponent(url.pathname);
	} catch {
		res.writeHead(400).end('Bad request');
		return;
	}

	// Resolve inside root, then prove it stayed there. `..` in a request path is
	// the one thing a static server must not get wrong.
	const target = resolve(root, `.${normalize(pathname)}`);
	if (target !== root && !target.startsWith(root + sep)) {
		res.writeHead(403).end('Forbidden');
		return;
	}

	let file = target;
	if (existsSync(file) && statSync(file).isDirectory()) file = join(file, 'index.html');

	if (!existsSync(file) || !statSync(file).isFile()) {
		res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
		res.end(`404 — ${pathname}\n`);
		return;
	}

	res.writeHead(200, {
		'content-type': TYPES[extname(file).toLowerCase()] ?? 'application/octet-stream',
		'cache-control': 'no-store',
	});
	createReadStream(file).pipe(res);
});

server.on('error', (err) => {
	if (err.code === 'EADDRINUSE') {
		console.error(`serve: port ${port} is in use. Try PORT=4174 bun run learn:preview`);
		process.exit(1);
	}
	throw err;
});

server.listen(port, '127.0.0.1', () => {
	console.log(`serve: http://localhost:${port}`);
	console.log('serve: Ctrl-C to stop');
});
