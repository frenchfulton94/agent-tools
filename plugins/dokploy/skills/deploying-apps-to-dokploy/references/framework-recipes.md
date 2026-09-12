# Framework recipes

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [How to read this table](#how-to-read-this-table)
- [The table](#the-table)
- [The three shapes behind it](#the-three-shapes-behind-it)
- [Ports the docs name elsewhere](#ports-the-docs-name-elsewhere)

## How to read this table

Dokploy publishes one short guide per framework — seventeen of them as of the retrieval
date above. They are near-identical Nixpacks configurations, so they are collapsed here
into one table rather than restated one section at a time.

Every guide deploys from the same example repository, `https://github.com/Dokploy/examples.git`
on branch `main`, and differs only in the build path. Read the row for the framework at
hand, then treat the build path as the directory inside your own repository.

"Domain port" is the `Container Port` on the domain, not the port the framework's dev
server uses. Where a guide does not state one, the cell says so rather than guessing:
use the port the process actually listens on.

## The table

| Framework | Build path | Build type and settings | Publish Directory | Domain port |
|---|---|---|---|---|
| 11ty | `/11ty` | Nixpacks | `./_site` | 80 |
| Astro | `/astro` | Nixpacks | `./dist` | 80 |
| Astro SSR | `/astro-ssr` | Nixpacks, `NIXPACKS_START_CMD="pnpm run preview"` | — | Not stated in the guide |
| Deno | `/deno` | Dockerfile, `Dockerfile Path` = `Dockerfile` | — | 8080 |
| HTML | `/html` | Static | — | 80 |
| Lit | `/lit` | Nixpacks | `./dist` | 80 |
| Nest.js | `/nestjs` | Nixpacks | — | Not stated in the guide |
| Next.js | `/nextjs` | Nixpacks | — | Not stated in the guide; 3000 elsewhere in the docs |
| Preact | `/preact` | Nixpacks | `./dist` | 80 |
| Qwik | `/qwik` | Nixpacks, `NIXPACKS_START_CMD="pnpm run preview"` | — | Not stated in the guide |
| Remix | `/remix` | Nixpacks | — | Not stated in the guide |
| Solid.js | `/solidjs` | Nixpacks | `./dist` | 80 |
| Svelte | `/svelte` | Nixpacks | `./dist` | 80 |
| Tanstack | `/tanstack` | Nixpacks | — | 3000 |
| Turborepo | `/turborepo` | Nixpacks, plus the three variables below | — | 3000 |
| Vite React | `/vite` | Nixpacks | `./dist` | 80 |
| Vue.js | `/vuejs` | Nixpacks | `./dist` | 80 |

Turborepo's three variables select one workspace out of the monorepo:

```bash
NIXPACKS_TURBO_APP_NAME="web"
NIXPACKS_BUILD_CMD="turbo run build --filter=web"
NIXPACKS_START_CMD="turbo run start --filter=web"
```

## The three shapes behind it

All seventeen rows are one of three configurations — nine, seven, and one — and
recognising which one a framework needs matters more than the row itself. Each shape
carries its own gotcha, which is why they are grouped here rather than repeated
seventeen times in a table column.

**Static files served by NGINX** — nine rows. 11ty, Astro, Lit, Preact, Solid.js,
Svelte, Vite React, and Vue.js name a `Publish Directory` on a Nixpacks build; HTML uses
the `Static` build type instead. Either way Dokploy copies files and NGINX serves them.
The gotcha is the same for all nine: the domain port is **80**, not 3000 and not 4321.
Pointing the domain at the framework's dev-server port is one of the ways a deployment
that reports success serves nothing. HTML's own variation is that `Static` copies the
`Root` directory as it stands and builds nothing, so a project with a build step belongs
on Nixpacks with a `Publish Directory` rather than on `Static`.

**A long-running server** — seven rows. Nest.js, Next.js, Remix, Tanstack, Turborepo,
Astro SSR, and Qwik. Nixpacks builds and starts the application, and the domain
port is whatever the process listens on. Astro SSR and Qwik need `NIXPACKS_START_CMD`
set to the preview command, because the default start command does not serve the built
output. Turborepo needs all three of the variables above, which are what select one
workspace out of the monorepo for the build and the start command.

**A Dockerfile** — one row. Deno. Set the build type to Dockerfile and the path to `Dockerfile`.
Any framework whose build needs system packages or a runtime Nixpacks does not detect
belongs here too; see `build-types.md`.

Anything in the second or third group has to bind `0.0.0.0`. Vite-based frameworks
default to `127.0.0.1` and return Bad Gateway until `host: true` is set in both
`server` and `preview`.

## Ports the docs name elsewhere

The troubleshooting and generated-domain pages name three defaults the framework guides
leave out:

| Framework | Port |
|---|---|
| Next.js | 3000 |
| Astro (dev server) | 4321 |
| Laravel | 8000 |

Changing the application's port means updating the domain's `Container Port` to match.
