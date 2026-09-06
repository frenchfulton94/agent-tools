---
name: vite
description: Professionally configure, use, debug, and upgrade Vite projects. Use this skill whenever a task involves Vite in any way — editing or creating vite.config.ts/js, scaffolding a frontend app (React, Vue, Svelte, Solid, etc. via create-vite), dev server issues (port, HMR, proxy, CORS), path aliases, environment variables (.env files, import.meta.env, VITE_ prefix), production builds (vite build, Rolldown, chunking, browser targets, library mode, multi-page apps), static deployment base paths, Vite plugins, SSR, or migrating between Vite majors. Trigger even when the user doesn't say "Vite" but mentions these files, commands, or errors (e.g. "npm run dev fails", "import.meta.env is undefined", "configure a proxy for my API"). Do NOT rely on training data for Vite specifics — this skill includes a live doc map because Vite changed bundlers (Rollup/esbuild → Rolldown/Oxc in v8).
metadata:
  version: '1.0'
  docs-verified-against: 'vite 8.1.5 (2026)'
---

# Vite

Vite is two things: a dev server that serves your source over native ESM with on-demand
transforms (near-instant startup, fast HMR), and a build command that bundles for
production. `index.html` at the project root is real source code and the entry to the
module graph — not a static file in `public/`.

## Step 0: Establish the project's Vite version, then trust live docs over memory

Vite majors ship yearly with real breaking changes, and **Vite 8 replaced Rollup with
Rolldown and esbuild with Oxc**, invalidating a lot of pre-2026 knowledge (including
model training data and old blog posts). So before giving version-specific advice:

1. Find the installed major: check `devDependencies.vite` in `package.json` (or run
   `bun scripts/audit.ts <project-dir>` — see Scripts below — which reports this and
   more in one shot).
2. Match docs to the major. Current docs live at `https://vite.dev`; older majors keep
   frozen docs at `https://v7.vite.dev`, `https://v6.vite.dev`, `https://v5.vite.dev`,
   etc. (same paths).
3. Fetch the relevant page instead of answering from memory whenever the question
   touches config option names, defaults, CLI flags, plugin hooks, or anything that
   plausibly changed between majors. `references/doc-map.md` maps every topic to its
   URL. Append `.md` to any vite.dev page path (e.g. `https://vite.dev/guide/build.md`)
   to get clean markdown instead of HTML; `https://vite.dev/llms.txt` is the full index.

If you can't fetch the web, say so and qualify advice with the version it applies to.

## Setting up a project

- Scaffold: `npm create vite@latest my-app -- --template react-ts` (templates: vanilla,
  vue, react, preact, lit, svelte, solid, qwik — each with a `-ts` variant). Requires
  Node.js 20.19+ or 22.12+.
- Default scripts: `dev` → `vite` (serves on port 5173), `build` → `vite build` (outputs
  `dist/`), `preview` → `vite preview` (serves the built `dist/` on 4173 — use this to
  verify production builds locally; never deploy the dev server).
- Framework support comes from plugins (`@vitejs/plugin-react`, `@vitejs/plugin-vue`,
  `@vitejs/plugin-react-swc`, community plugins for the rest). Templates preconfigure
  them.

## Configuration essentials

Config lives in `vite.config.ts` (or `.js`) at the project root. Always use
`defineConfig` for IntelliSense:

```ts
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [/* framework plugin here */]
});
```

- **Conditional config**: export a function receiving `{ command, mode, isSsrBuild }`.
  `command` is `'serve'` in dev and `'build'` for builds. Compare optional flags
  explicitly against `true`/`false` — some tools pass `undefined`.
- **Env vars inside the config file are NOT loaded from `.env` files** — Vite loads
  `.env*` only after the config resolves. If config values must depend on them, call
  `loadEnv(mode, process.cwd(), '')` explicitly. This is a top source of "my env var is
  undefined in vite.config" confusion.
- For the full option list and current defaults, fetch the config reference pages in
  `references/doc-map.md`. For working examples of aliases, proxy, multi-page, library
  mode, and chunk splitting, read `references/config-recipes.md`.

## Environment variables and modes

- Only variables prefixed `VITE_` reach client code, as `import.meta.env.VITE_X`
  (always strings — cast booleans/numbers yourself). Everything else stays server-side
  on purpose. **Never put secrets in `VITE_` vars: they are inlined into the shipped
  bundle at build time.**
- File precedence (highest wins): existing shell env > `.env.[mode].local` >
  `.env.[mode]` > `.env.local` > `.env`. Add `*.local` to `.gitignore`. Env files load
  at server start — restart after edits.
- `mode` ≠ `NODE_ENV`. `vite build` runs in mode `production`; `vite build --mode
staging` loads `.env.staging` but still builds with `NODE_ENV=production` (so
  `import.meta.env.PROD` stays `true`). Use custom modes for per-environment config,
  not to switch dev/prod behavior.
- `import.meta.env.*` is statically replaced at build time — dynamic access like
  `import.meta.env[key]` won't be replaced. In HTML, use `%VITE_X%` syntax.
- Built-ins: `MODE`, `DEV`, `PROD`, `BASE_URL`, `SSR`.

## TypeScript

- Vite transpiles TS (via Oxc in v8+) but never type-checks. Run `tsc --noEmit` in CI
  and alongside builds; use `vite-plugin-checker` if you want errors in the browser.
- Set `"isolatedModules": true` in tsconfig — per-file transpilers can't handle const
  enums or implicit type-only imports, and this makes TS warn you.
- Add `"types": ["vite/client"]` in tsconfig (or a `vite-env.d.ts` with
  `/// <reference types="vite/client" />`) for asset-import and `import.meta.env` types.
  Augment `ImportMetaEnv` in `vite-env.d.ts` to type your own `VITE_` vars — that file
  must contain no top-level `import` statements or the augmentation silently breaks.
- Vite ignores tsconfig `target`; dev target comes from `oxc.target` (v8) and build
  target from `build.target`.

## Gotchas: Vite 8 vs. what you may "remember"

These defy pre-Vite-8 knowledge. When working on a v8+ project:

- The bundler is **Rolldown**, not Rollup. Use `build.rolldownOptions` —
  `build.rollupOptions` still works but is deprecated. Rolldown option names mostly
  mirror Rollup's, but check https://rolldown.rs/reference/ when unsure.
- JS transforms and minification use **Oxc**, not esbuild. The `esbuild` config option
  is deprecated in favor of `oxc` (e.g. `oxc.jsx`, `oxc.jsxInject`, `oxc.target`).
  esbuild is no longer a Vite dependency; `build.minify: 'esbuild'` requires installing
  it yourself.
- **`manualChunks` is gone/deprecated.** Chunk splitting is configured with
  `build.rolldownOptions.output.codeSplitting` (see the recipe in
  `references/config-recipes.md`).
- CSS is minified by **Lightning CSS** by default (PostCSS still handles processing).
- Dep pre-bundling uses Rolldown too; `optimizeDeps.esbuildOptions` →
  `optimizeDeps.rolldownOptions`.
- Default build targets are Baseline Widely Available browsers (Chrome/Edge ≥111,
  Firefox ≥114, Safari ≥16.4 as of v8). No polyfills are added — only syntax
  transforms. Legacy browsers need `@vitejs/plugin-legacy`.
- CJS `default`-import interop changed in v8 and can break packages that worked before;
  `legacy.inconsistentCjsInterop: true` is the temporary escape hatch.

On v5–v7 projects the old names (`rollupOptions`, `esbuild`, `manualChunks`) are
correct — another reason Step 0 matters.

## Debugging workflow

1. Reproduce with the exact command and read the full error — Vite errors usually name
   the offending file/import.
2. Classify: dev-only (pre-bundling, HMR, proxy), build-only (Rolldown, targets,
   chunking), or both (resolution, env, plugins).
3. For dep/pre-bundling weirdness (stale imports, "outdated optimize dep"), delete
   `node_modules/.vite` and restart with `vite --force`.
4. Fetch the Troubleshooting page (see doc-map) before inventing fixes — it covers CJS
   interop errors, `Module externalized for browser compatibility`, file-watch limits,
   and other canonical issues with canonical answers.
5. Useful flags: `vite --debug`, `vite --debug transform` (find slow files),
   `vite --profile` (CPU profile), `vite build --debug`.

## Performance defaults for professional setups

- Write explicit import extensions (`./Component.tsx` not `./Component`) and avoid
  barrel `index.ts` re-export files — both multiply resolution/transform work.
- Warm up known-hot files with `server.warmup.clientFiles`.
- Keep `buildStart`/`config` plugin hooks cheap; audit slow community plugins with
  `vite --debug plugin-transform` or `vite-plugin-inspect`.
- Prefer plain modern CSS over Sass/Less when possible.

## Scripts

- **`scripts/audit.ts`** — read-only project audit. Run
  `bun scripts/audit.ts [project-dir]` (defaults to cwd). Prints JSON to stdout:
  installed Vite major + matching docs base URL, config file found, framework plugin,
  env files present, whether `.gitignore` covers `*.local`, tsconfig checks
  (`isolatedModules`, `vite/client` types), and any `VITE_` vars whose names look like
  secrets. Run it at the start of any task on an existing project — it replaces
  four or five manual file inspections and its warnings are your checklist.

## References

- **`references/doc-map.md`** — topic → live vite.dev URL map with fetch guidance.
  Read it whenever you need details not in this file (config option specifics, SSR,
  backend integration, plugin API, deployment guides, migration steps).
- **`references/config-recipes.md`** — copy-adaptable `vite.config.ts` recipes:
  path aliases, dev proxy, multi-page apps, library mode, loadEnv-in-config, chunk
  splitting (v8 and pre-v8 forms), base path for subpath deploys.
