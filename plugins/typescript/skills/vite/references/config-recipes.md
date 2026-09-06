# vite.config recipes

## Contents

- Path aliases
- Dev server proxy
- Using .env values inside the config
- Multi-page app
- Library mode
- Chunk splitting (v8 vs pre-v8)
- Deploying under a sub-path (base)
- Conditional config skeleton

All recipes assume `vite.config.ts` with `import { defineConfig } from 'vite'`.
Verify option details against the live config reference (see `doc-map.md`) when a
project is on an older major.

## Path aliases

Keep the alias and tsconfig `paths` in sync or the editor and the bundler will
disagree:

```ts
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
	resolve: {
		alias: {
			'@': fileURLToPath(new URL('./src', import.meta.url))
		}
	}
});
```

```jsonc
// tsconfig.json
{
	"compilerOptions": {
		"baseUrl": ".",
		"paths": { "@/*": ["./src/*"] }
	}
}
```

Alternative: set `resolve.tsconfigPaths: true` to have Vite read tsconfig `paths`
directly (has a performance cost; explicit aliases are the default recommendation).

## Dev server proxy

For avoiding CORS against a backend during dev. Proxy is dev-server-only — production
routing belongs to your host/reverse proxy.

```ts
export default defineConfig({
	server: {
		proxy: {
			// /api/users -> http://localhost:3000/api/users
			'/api': 'http://localhost:3000',
			// strip the prefix: /v1/users -> http://backend:8080/users
			'/v1': {
				target: 'http://backend:8080',
				changeOrigin: true, // sets Host header to target — needed for most named hosts
				rewrite: (path) => path.replace(/^\/v1/, '')
			},
			// websockets
			'/socket.io': {
				target: 'ws://localhost:3000',
				ws: true,
				rewriteWsOrigin: true
			}
		}
	}
});
```

## Using .env values inside the config

`.env*` files are loaded _after_ the config resolves, so `process.env.VITE_X` is
undefined while the config runs. Load them explicitly:

```ts
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	// third arg '' loads ALL vars, not just VITE_-prefixed
	const env = loadEnv(mode, process.cwd(), '');
	return {
		server: { port: env.APP_PORT ? Number(env.APP_PORT) : 5173 },
		define: { __APP_ENV__: JSON.stringify(env.APP_ENV) }
	};
});
```

## Multi-page app

Each page is an `.html` file; dev needs nothing, build needs the entries listed.

```ts
import { resolve } from 'node:path';

export default defineConfig({
	build: {
		rolldownOptions: {
			// pre-v8: rollupOptions
			input: {
				main: resolve(import.meta.dirname, 'index.html'),
				admin: resolve(import.meta.dirname, 'admin/index.html')
			}
		}
	}
});
```

Output paths mirror the source html locations, not the input keys. If `root` is
changed, include it when resolving these paths (`import.meta.dirname` stays the config
file's folder).

## Library mode

```ts
import { resolve } from 'node:path';

export default defineConfig({
	build: {
		lib: {
			entry: resolve(import.meta.dirname, 'lib/main.ts'),
			name: 'MyLib', // global for UMD
			fileName: 'my-lib'
		},
		rolldownOptions: {
			// pre-v8: rollupOptions
			external: ['vue'], // never bundle peer frameworks
			output: { globals: { vue: 'Vue' } }
		}
	}
});
```

Pair with package.json: `"type": "module"`, `"files": ["dist"]`, and an `exports` map
with `import` → `./dist/my-lib.js` and `require` → `./dist/my-lib.umd.cjs`. Imported
CSS is emitted as one `dist/<fileName>.css` — export it as `"./style.css"`. For
non-browser or advanced library builds, the docs recommend tsdown/Rolldown directly.

## Chunk splitting

**Vite 8+** — `manualChunks` object form is removed and the function form deprecated;
use Rolldown's `codeSplitting`:

```ts
export default defineConfig({
	build: {
		rolldownOptions: {
			output: {
				codeSplitting: {
					groups: [
						{ name: 'vendor-react', test: /node_modules[\\/](react|react-dom)/ },
						{ name: 'vendor', test: /node_modules/ }
					]
				}
			}
		}
	}
});
```

Check https://rolldown.rs/in-depth/manual-code-splitting for current `codeSplitting`
fields before using — the API surface is newer than most references.

**Vite 5–7** — the classic form:

```ts
export default defineConfig({
	build: {
		rollupOptions: {
			output: {
				manualChunks: {
					'vendor-react': ['react', 'react-dom']
				}
			}
		}
	}
});
```

Only split chunks to solve a measured problem (huge vendor chunk, poor caching) —
Vite's defaults plus its preload/import-map optimizations are good.

## Deploying under a sub-path (base)

For GitHub Pages or any `example.com/my-app/` deploy:

```ts
export default defineConfig({
	base: '/my-app/' // or '' / './' for a fully relative build
});
```

In code, build URLs dynamically with `import.meta.env.BASE_URL` (must appear literally
— no bracket access).

## Conditional config skeleton

```ts
export default defineConfig(({ command, mode, isSsrBuild }) => {
	const dev = command === 'serve';
	return {
		base: dev ? '/' : '/my-app/',
		// compare optional flags explicitly — tools may pass undefined
		...(isSsrBuild === true ? { ssr: { noExternal: ['some-pkg'] } } : {})
	};
});
```
