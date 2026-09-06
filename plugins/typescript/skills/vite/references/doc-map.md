# Vite live documentation map

## Contents

- How to fetch these docs
- Version-pinned doc sites
- Introduction & guide pages
- Config reference pages
- API pages
- Environment API pages
- Ecosystem pages

## How to fetch these docs

Every page below has two forms:

- HTML: `https://vite.dev/<path>` — what humans browse.
- Markdown: `https://vite.dev/<path>.md` — same content, clean markdown, far fewer
  tokens. **Prefer the `.md` form.** (For `https://vite.dev/guide/` the markdown form
  is `https://vite.dev/guide.md`; for `https://vite.dev/config/` it is
  `https://vite.dev/config.md`.)

The machine-readable index of all pages is `https://vite.dev/llms.txt` — fetch it if
you need a page not listed here (the site may have grown since this map was written;
the llms.txt is always current).

Fetch a page when the user's question depends on exact option names, defaults, CLI
flags, or behavior that varies by version. Don't fetch for conceptual questions this
skill's SKILL.md already answers.

## Version-pinned doc sites

If the project is on an older major (check `package.json`), swap the host — paths are
the same:

| Vite major      | Docs host             |
| --------------- | --------------------- |
| current (8+)    | https://vite.dev      |
| 7               | https://v7.vite.dev   |
| 6               | https://v6.vite.dev   |
| 5               | https://v5.vite.dev   |
| 4               | https://v4.vite.dev   |
| unreleased/next | https://main.vite.dev |

Migration guides chain: the current site's migration page covers the latest major jump
only; for multi-major upgrades, walk each version's migration page in order (e.g.
v6→v8: read `https://v7.vite.dev/guide/migration` then `https://vite.dev/guide/migration`).

## Introduction & guide pages

| Topic — fetch when…                                                                                                                                                                                                             | URL                                           |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| Getting started: scaffolding, templates, Node requirements, CLI basics, index.html-as-entry                                                                                                                                     | https://vite.dev/guide.md                     |
| Features: TS handling, tsconfig interplay, CSS/PostCSS/modules/pre-processors, static assets & import queries (?url ?raw ?worker ?inline), JSON, glob import, dynamic import rules, WASM, web workers, CSP, build optimizations | https://vite.dev/guide/features.md            |
| CLI: every command and flag (`vite`, `vite build`, `vite preview`, `vite optimize`)                                                                                                                                             | https://vite.dev/guide/cli.md                 |
| Using plugins: adding, ordering (`enforce`), conditional application (`apply`), finding plugins                                                                                                                                 | https://vite.dev/guide/using-plugins.md       |
| Dependency pre-bundling: why deps are pre-bundled, cache location, `--force`, monorepo/linked deps                                                                                                                              | https://vite.dev/guide/dep-pre-bundling.md    |
| Static assets: public/ dir semantics, asset inlining, new URL(..., import.meta.url)                                                                                                                                             | https://vite.dev/guide/assets.md              |
| Building for production: browser targets, base path, rolldownOptions, chunking, watch mode, multi-page, library mode, license file                                                                                              | https://vite.dev/guide/build.md               |
| Deploying: platform-specific guides (Netlify, Vercel, GitHub Pages, Cloudflare, …)                                                                                                                                              | https://vite.dev/guide/static-deploy.md       |
| Env variables & modes: full precedence rules, NODE_ENV vs mode tables, HTML replacement, TS IntelliSense for env                                                                                                                | https://vite.dev/guide/env-and-mode.md        |
| SSR: dev middleware setup, build for SSR, externals, ssrLoadModule/ModuleRunner                                                                                                                                                 | https://vite.dev/guide/ssr.md                 |
| Backend integration: using Vite with Rails/Laravel/Django etc., manifest.json                                                                                                                                                   | https://vite.dev/guide/backend-integration.md |
| Troubleshooting: canonical fixes for common errors (CJS/ESM interop, externalized modules, file watch limits, HMR issues) — fetch before improvising a fix                                                                      | https://vite.dev/guide/troubleshooting.md     |
| Performance: profiling, plugin auditing, warmup, resolution costs                                                                                                                                                               | https://vite.dev/guide/performance.md         |
| Migration to current major (breaking changes, deprecations, Rolldown/Oxc mapping tables in v8)                                                                                                                                  | https://vite.dev/guide/migration.md           |
| All historical breaking changes index                                                                                                                                                                                           | https://vite.dev/changes.md                   |

## Config reference pages

| Topic — fetch when…                                                                                                             | URL                                                 |
| ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Config file mechanics: defineConfig, conditional/async config, loadEnv, config loaders                                          | https://vite.dev/config.md                          |
| Shared options: root, base, define, resolve.alias/extensions/conditions, css._, oxc._, envDir/envPrefix, appType, html.cspNonce | https://vite.dev/config/shared-options.md           |
| Server options: port, host, proxy, cors, headers, hmr, watch, warmup, fs.allow                                                  | https://vite.dev/config/server-options.md           |
| Build options: target, outDir, assetsInlineLimit, cssMinify, minify, sourcemap, lib, rolldownOptions, chunkImportMap            | https://vite.dev/config/build-options.md            |
| Preview options                                                                                                                 | https://vite.dev/config/preview-options.md          |
| Dep optimization options: optimizeDeps include/exclude/rolldownOptions                                                          | https://vite.dev/config/dep-optimization-options.md |
| SSR options: ssr.external/noExternal/target                                                                                     | https://vite.dev/config/ssr-options.md              |
| Worker options                                                                                                                  | https://vite.dev/config/worker-options.md           |

## API pages

| Topic — fetch when…                                                                          | URL                                      |
| -------------------------------------------------------------------------------------------- | ---------------------------------------- |
| Writing a Vite plugin: hooks, ordering, virtual modules, transformIndexHtml, handleHotUpdate | https://vite.dev/guide/api-plugin.md     |
| HMR client API: import.meta.hot.accept/dispose/data                                          | https://vite.dev/guide/api-hmr.md        |
| JavaScript API: createServer, build, preview, loadEnv, resolveConfig                         | https://vite.dev/guide/api-javascript.md |

## Environment API pages (advanced: frameworks, custom runtimes)

- https://vite.dev/guide/api-environment.md
- https://vite.dev/guide/api-environment-instances.md
- https://vite.dev/guide/api-environment-plugins.md
- https://vite.dev/guide/api-environment-frameworks.md
- https://vite.dev/guide/api-environment-runtimes.md

## Ecosystem pages

| Topic                                                           | URL                                              |
| --------------------------------------------------------------- | ------------------------------------------------ |
| Official + curated plugins list                                 | https://vite.dev/plugins.md                      |
| Release cadence and support policy                              | https://vite.dev/releases.md                     |
| Rolldown (bundler in v8+): option reference for rolldownOptions | https://rolldown.rs/reference/                   |
| Oxc (transformer/minifier in v8+)                               | https://oxc.rs/docs/guide/usage/transformer.html |
