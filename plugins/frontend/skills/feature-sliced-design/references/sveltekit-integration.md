# SvelteKit Integration

How FSD maps onto SvelteKit in this codebase. Covers directory placement,
route wiring, `load`/`actions` placement, the server-only boundary, hooks,
API endpoints, and database access.

## Contents

1. [General principle](#general-principle)
2. [Directory structure](#directory-structure)
3. [Wiring routes to FSD pages](#wiring-routes-to-fsd-pages)
4. [Load functions and form actions](#load-functions-and-form-actions)
5. [The server-only boundary](#the-server-only-boundary)
6. [Root layout and hooks](#root-layout-and-hooks)
7. [API endpoints (+server.ts)](#api-endpoints-serverts)
8. [Database access](#database-access)
9. [Path aliases](#path-aliases)
10. [Key reminders](#key-reminders)

## General principle

Keep the standard SvelteKit project structure. FSD layers live inside
`src/lib/` — and `src/lib/` contains **only** the six layer directories.
`src/routes/` is SvelteKit's file-based routing and is **not** an FSD layer:
it is a thin adapter above the FSD `pages` layer. There is no naming
collision (SvelteKit has no `src/pages/` or `src/app/` directories), so FSD
layer names are used without prefixes.

## Directory structure

```text
my-sveltekit-project/
  src/
    routes/                        ← SvelteKit routing (thin entries only)
      +layout.svelte
      +layout.server.ts
      +page.svelte
      profile/
        +page.svelte
        +page.server.ts
      api/
        webhook/
          +server.ts               ← re-exports handlers from a slice
    lib/
      app/                         ← FSD app layer
        styles/global.css
        hooks/handle.server.ts     ← handle() implementation
        index.ts
        index.server.ts
      pages/                       ← FSD pages layer
        home/
          ui/HomePage.svelte
          index.ts
        profile/
          ui/ProfilePage.svelte
          model/profile.ts
          api/profile.server.ts    ← load + actions implementations
          index.ts                 ← universal exports (the component)
          index.server.ts          ← server exports (load, actions)
      widgets/                     ← when needed
      features/                    ← when needed
      entities/                    ← when needed
      shared/                      ← FSD shared layer
        ui/
        lib/
        api/
        db/                        ← database (.server.ts modules)
    hooks.server.ts                ← fixed location, thin re-export
    app.html
    app.d.ts
  static/                          ← served as-is (favicon, robots.txt)
  svelte.config.js
  vite.config.ts
```

`app.html`, `app.d.ts`, `hooks.server.ts`, `service-worker.ts`, and
`+page`/`+layout`/`+server` files are SvelteKit's fixed entry points. They
stay where SvelteKit expects them and stay thin.

## Wiring routes to FSD pages

`+page.svelte` renders the page component; `+page.server.ts` re-exports the
page's server code. Nothing else goes in route files.

```svelte
<!-- src/routes/profile/+page.svelte -->
<script lang="ts">
	import { ProfilePage } from '$lib/pages/profile';

	let { data, form } = $props();
</script>

<ProfilePage {data} {form} />
```

```typescript
// src/routes/profile/+page.server.ts
export { load, actions } from '$lib/pages/profile/index.server';
```

The page slice owns everything:

```typescript
// src/lib/pages/profile/index.ts (universal public API)
export { default as ProfilePage } from './ui/ProfilePage.svelte';

// src/lib/pages/profile/index.server.ts (server public API)
export { load, actions } from './api/profile.server';
```

The same pattern applies to layouts: a nested `+layout.svelte` renders a
layout component from the owning slice (a widget or the app layer), and
`+layout.server.ts` re-exports its `load`.

A route that needs no server code (a purely static page) is just a
`+page.svelte` rendering the component from `$lib/pages/<slice>`.

## Load functions and form actions

`load` and `actions` are page-level code: implement them in the page slice's
`api/` segment as `.server.ts` files, exported through `index.server.ts`.

```typescript
// src/lib/pages/profile/api/profile.server.ts
import type { ServerLoad, Actions } from '@sveltejs/kit';
import { db } from '$lib/shared/db/client.server';

export const load: ServerLoad = async ({ locals }) => {
	const profile = await db.query.profiles.findFirst({
		where: (p, { eq }) => eq(p.userId, locals.session!.userId)
	});
	return { profile };
};

export const actions: Actions = {
	update: async ({ request, locals }) => {
		const data = await request.formData();
		// validate, write, return
	}
};
```

Note: SvelteKit's generated `./$types` only exists for files inside
`src/routes/`. Inside `src/lib/`, use the generic `ServerLoad`/`Actions`
types from `@sveltejs/kit` (as above), or import the route's generated
types by full path. Either is acceptable; be consistent.

Placement rules:

- **Page-specific `load`/`actions`** → the page slice's `api/` segment
  (the default; keep them here per Pages First).
- **Reusable domain queries** used by multiple pages → `entities/<name>/api/`
  as `.server.ts` files, called from each page's `load`.
- **Universal `load`** (`+page.ts`, runs on client too): implement in the
  page slice's `api/` as a regular `.ts` file, export via `index.ts`, and
  re-export from `+page.ts`. Use only when the data must be fetchable from
  the client; server `load` is the default.
- Form actions are bound to routes. A feature form reused across pages
  posts to a fixed route (`action="/profile?/update"`); keep such route
  paths as constants in `shared/config/`.

## The server-only boundary

Server-only code uses the `.server.ts` filename suffix. SvelteKit enforces
this: importing a `.server.ts` module into client-reachable code fails the
build. This codebase does **not** use the `$lib/server/` directory
convention — the suffix replaces it, so server code stays inside its slice
next to the code it belongs with.

- Anything touching the database, private env vars
  (`$env/static/private`, `$env/dynamic/private`), or secrets → `.server.ts`.
- A slice's server-only exports go through `index.server.ts`, never through
  `index.ts` (see SKILL.md Rule 4-2). Import it by full name:
  `$lib/pages/profile/index.server`.
- A slice with no server code has no `index.server.ts`.

## Root layout and hooks

Global styles, root context, and hook implementations belong to the FSD
`app` layer. The fixed SvelteKit files import from it:

```svelte
<!-- src/routes/+layout.svelte -->
<script lang="ts">
	import '$lib/app/styles/global.css';

	let { children } = $props();
</script>

{@render children()}
```

```typescript
// src/hooks.server.ts (fixed location — thin)
export { handle } from '$lib/app/index.server';

// src/lib/app/index.server.ts
export { handle } from './hooks/handle.server';
```

The `handle` implementation in `$lib/app/hooks/handle.server.ts` may import
from `shared` (e.g., the auth instance) — `app → shared` is a legal import
direction. `handleError` and `reroute` follow the same thin-re-export
pattern.

## API endpoints (+server.ts)

Most data flows through `load` and form actions; `+server.ts` endpoints are
for webhooks, external consumers, and mounted handlers (e.g., an auth
library's catch-all route). Implement the handler in the slice that owns the
domain — `$lib/app/api/` for app-wide endpoints, or a page slice for
page-scoped ones — as a `.server.ts` file, and re-export:

```typescript
// src/lib/app/api/stripe-webhook.server.ts
import type { RequestHandler } from '@sveltejs/kit';
export const handleStripeWebhook: RequestHandler = async ({ request }) => {
	// verify signature, process event
	return new Response(null, { status: 200 });
};

// src/routes/api/webhook/+server.ts
export { handleStripeWebhook as POST } from '$lib/app/api/stripe-webhook.server';
```

FSD is primarily a frontend methodology. If the endpoint surface grows
large, consider moving the backend to a separate package.

## Database access

Place the database client and schema in a `db` segment in shared
(`src/lib/shared/db/`). The connection is server-only; the schema file
carries no secrets and its inferred types are reused across the app:

```text
shared/db/
  client.server.ts     ← Drizzle client + connection (server-only)
  schema.ts            ← Table definitions; types via InferSelectModel
  index.server.ts      ← export { db } from './client.server'; re-export schema
```

Queries used by a single page stay in that page's `api/*.server.ts` files
(Pages First). Reusable domain queries move to `entities/<name>/api/` as
`.server.ts` files. Do not put domain-specific queries in `shared/db/` —
shared holds the client and schema, not business queries.

## Path aliases

`$lib` is built in — no configuration needed. Imports follow
`$lib/<layer>/<slice>`:

```typescript
import { ProfilePage } from '$lib/pages/profile';
import { load } from '$lib/pages/profile/index.server'; // server files only
import Button from '$lib/shared/ui/Button.svelte';
```

Do not add per-layer aliases (`@/pages`, etc.) — they duplicate what `$lib`
already provides. If an alias is ever needed outside `src/lib`, define it in
`svelte.config.js` under `kit.alias`.

## Key reminders

1. **FSD lives in `src/lib/`**; `src/routes/` belongs to SvelteKit routing,
   not FSD, and stays thin.
2. **Route files re-export or render** — page components from `index.ts`,
   `load`/`actions` from `index.server.ts`. Business logic stays in slices.
3. **`.server.ts` is the server boundary**; `index.server.ts` is the
   server-side public API. No `$lib/server/` directory.
4. **Pages First still applies**: start with code in `$lib/pages/` and
   extract only when reuse is real.
