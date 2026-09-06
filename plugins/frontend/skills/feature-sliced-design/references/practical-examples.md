# Practical Examples

Concrete code patterns for common scenarios within FSD structure in this
SvelteKit codebase. Covers authentication, type definitions, API request
handling, state management with Svelte runes, and the load/actions data
flow.

## Contents

1. [Authentication](#authentication)
2. [Type Definitions](#type-definitions)
3. [API Request Handling](#api-request-handling)
4. [State Management: Svelte runes](#state-management-svelte-runes)
5. [Data Flow: load and form actions](#data-flow-load-and-form-actions)

## Authentication

Auth is one of the most common sources of confusion in FSD. The key question
is: what goes in `shared/`, what goes in `features/` or `pages/`?

### Auth infrastructure: `shared/auth/`

The auth library instance, its client, and session utilities are
**infrastructure**, not business logic. With BetterAuth, the server instance
is a `.server.ts` module and the browser client is universal:

```text
shared/auth/
  auth.server.ts       ← BetterAuth server instance (Drizzle adapter, plugins)
  client.ts            ← createAuthClient() for the browser
  index.ts             ← export { authClient } from './client'
  index.server.ts      ← export { auth } from './auth.server'
```

```typescript
// shared/auth/auth.server.ts
import { betterAuth } from 'better-auth';
import { drizzleAdapter } from 'better-auth/adapters/drizzle';
import { db } from '$lib/shared/db/index.server';

export const auth = betterAuth({
	database: drizzleAdapter(db, { provider: 'pg' }),
	emailAndPassword: { enabled: true }
});

// shared/auth/client.ts
import { createAuthClient } from 'better-auth/svelte';
export const authClient = createAuthClient();
```

The session is resolved once per request in the app layer's `handle` hook
(which imports `auth` from `$lib/shared/auth/index.server` — `app → shared`
is legal) and placed on `event.locals`. Page `load` functions read
`locals.session`; components receive session data through `load`, not by
importing a global store. This keeps auth state per-request and SSR-safe.

### Auth UI: pages (single use) or features (multi-use)

Place the login form in the slice that consumes it. Single-use (only on the
login page) goes in `pages/login/`; multi-use (dedicated page + modal login)
goes in `features/auth/`:

```text
pages/login/                        ← Single-use
  ui/{LoginPage,LoginForm}.svelte
  model/login.ts                    ← Form state, validation
  api/login.server.ts               ← Form action calling the auth API
  index.ts
  index.server.ts

features/auth/                      ← Multi-use
  ui/{LoginForm,RegisterForm}.svelte
  model/auth.ts
  index.ts
```

### When to use shared/auth vs a user entity

The official Auth guide presents two valid storage locations: **In Shared**
(`shared/auth`) and **In Entities** (a `user` entity). Pages and widgets are
discouraged.

`shared/auth` is the simpler default. Choose it when the project has no
entities layer yet, or when auth state is just a session plus minimal user
info.

A `user` entity is the right call when the project already has an entities
layer **and** auth and profile data are tightly coupled (profile reused for
non-auth purposes like avatars in comments). With cookie-session auth
(BetterAuth), the classic "how does the API client get the token" problem
disappears: the session lives on `locals`, so no token store is needed.

A `user` entity created **only** to wrap a login response is premature.
See `references/excessive-entities.md` for the full decision matrix.

## Type Definitions

### Where to define types

The location of type definitions follows the same rules as any other code:

| Type scope                                        | Location                                                             |
| ------------------------------------------------- | -------------------------------------------------------------------- |
| API response/request shapes shared across the app | Domain-named files in `shared/api/` (e.g., `shared/api/product.ts`)  |
| Types inferred from the database schema           | `shared/db/schema.ts` via Drizzle's `InferSelectModel`               |
| Types for a specific entity's domain model        | `entities/<name>/model/<name>.ts`                                    |
| Types used only within one page                   | `pages/<name>/model/<name>.ts`                                       |
| Types used only within one feature                | `features/<name>/model/<name>.ts`                                    |
| Generic utility types (e.g., `Nullable<T>`)       | Domain-named files in `shared/lib/` (e.g., `shared/lib/nullable.ts`) |

Per Rule 4-4 (domain-based file naming), avoid grouping all types in
`types.ts` or `utils.ts`. A file named `types.ts` cannot answer "types
for what?" without inspection; a file named `product.ts` can.

### Example: API types in shared, domain model in entities

```typescript
// shared/api/product.ts: raw API/DB response shape
export interface ProductDTO {
	id: string;
	name: string;
	price: number;
	createdAt: string;
}

// entities/product/model/product.ts: domain model layered on top
import type { ProductDTO } from '$lib/shared/api';

export interface Product extends ProductDTO {
	formattedPrice: string;
	isOnSale: boolean;
}

export const fromDTO = (dto: ProductDTO): Product => ({
	...dto,
	formattedPrice: `$${dto.price.toFixed(2)}`,
	isOnSale: dto.price < 10
});
```

**Key principle:** Raw shapes go in `shared/api/` (or come from
`shared/db/schema.ts`). Domain models with business logic go in `entities/`.
If you only need the raw shape, do not create an entity just for types.

## API Request Handling

Most data in a SvelteKit app comes from `load` functions querying the
database directly (see [Data Flow](#data-flow-load-and-form-actions) below).
Use an HTTP client only for external/third-party APIs.

### Shared API client

Standardize base URL, headers, and JSON handling in `shared/api/`. Accept a
`fetch` parameter so `load` functions can pass SvelteKit's event `fetch`
(required for SSR-correct requests):

```typescript
// shared/api/client.ts
export const createApiClient = (baseUrl: string, fetchFn: typeof fetch = fetch) => {
	const handle = async <T>(res: Response): Promise<T> => {
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return res.json();
	};
	return {
		get: <T>(path: string) => fetchFn(`${baseUrl}${path}`).then((r) => handle<T>(r)),
		post: <T>(path: string, body: unknown) =>
			fetchFn(`${baseUrl}${path}`, {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify(body)
			}).then((r) => handle<T>(r))
		// put, delete follow the same pattern
	};
};
```

### CRUD helpers in shared

```typescript
// shared/api/create-crud-api.ts
import { createApiClient } from './client';

export const createCrudApi = <T>(resource: string, fetchFn?: typeof fetch) => {
	const api = createApiClient(API_URL, fetchFn);
	return {
		getAll: () => api.get<T[]>(`/${resource}`),
		getById: (id: string) => api.get<T>(`/${resource}/${id}`),
		create: (data: Partial<T>) => api.post<T>(`/${resource}`, data)
	};
};
```

### Request placement rule

Place each request function in the slice that owns the use case:

- **Page-specific data fetching** (e.g., dashboard stats only used on the
  dashboard) → `pages/<name>/api/` (`.server.ts` if it touches the db or
  secrets)
- **Feature-specific actions** (e.g., `toggleLike`) → `features/<name>/api/`
- **Reusable domain queries** (e.g., `getUserById`) → `entities/<name>/api/`
- **CRUD primitives** for a generic resource → `shared/api/create-crud-api.ts`

Do not put domain-specific request functions in `shared/api/`. Shared is
infrastructure; the moment a function knows about a specific resource and
its domain rules, it belongs in `entities/` or higher.

Code generated from an OpenAPI spec, if adopted, goes in `shared/api/`.

## State Management: Svelte runes

Svelte 5 runes are the state layer — no external state library. The same
FSD line applies as with any store technology: **business entities** (the
things the app works with: `todo`, `product`, `user`) go in the Entities
layer; **user actions** (`add-todo`, `toggle-todo`) go in Features. And per
the pages-first rule: state used by a single page stays in that page's
`model/` segment until reuse appears.

### Domain-named rune modules

Rune state outside components lives in `.svelte.ts` files, named by domain
(Rule 4-4 — not `store.ts`):

```typescript
// entities/todo/model/todo.svelte.ts
export interface Todo {
	id: string;
	title: string;
	completed: boolean;
}

export const createTodoState = (initial: Todo[]) => {
	let items = $state(initial);
	return {
		get items() {
			return items;
		},
		setCompleted(id: string, completed: boolean) {
			const todo = items.find((t) => t.id === id);
			if (todo) todo.completed = completed;
		}
	};
};
```

The slice's public API re-exports what consumers need:

```typescript
// entities/todo/index.ts
export { createTodoState, type Todo } from './model/todo.svelte';
```

**Key:** state + mutation logic + types live together in a single
domain-named file, not split across `store.ts`, `actions.ts`, `types.ts`.
That technical-role split reduces cohesion and is an anti-pattern in FSD.

### SSR: no module-level state singletons

Do not export a module-level `$state` singleton
(`export const todos = createTodoState([])` at module scope). On the server,
module state is shared across requests and leaks data between users. Instead,
create the state where it is consumed and share it via context:

```typescript
// entities/todo/model/todo-context.ts
import { getContext, setContext } from 'svelte';
import { createTodoState, type Todo } from './todo.svelte';

const KEY = Symbol('todos');
export const provideTodoState = (initial: Todo[]) => setContext(KEY, createTodoState(initial));
export const useTodoState = () => getContext<ReturnType<typeof createTodoState>>(KEY);
```

The page (or root layout, for app-wide state owned by the `app` layer)
calls `provideTodoState(data.todos)` with data from `load`; features and
widgets call `useTodoState()`. This keeps state per-request on the server
and lets features consume entity state without cross-imports.

### A feature consuming entity state

```svelte
<!-- features/toggle-todo/ui/ToggleTodo.svelte -->
<script lang="ts">
	import { useTodoState } from '$lib/entities/todo';

	let { id, completed }: { id: string; completed: boolean } = $props();
	const todos = useTodoState();
</script>

<input type="checkbox" checked={completed} onchange={() => todos.setCompleted(id, !completed)} />
```

## Data Flow: load and form actions

Server data flows through `load`; mutations flow through form actions. Both
belong to the page slice (`api/*.server.ts`, exported via
`index.server.ts`) — see `references/sveltekit-integration.md` for the
route wiring.

### Reads: load in the page slice, queries in the owning layer

```typescript
// pages/dashboard/api/dashboard.server.ts
import { getUserById } from '$lib/entities/user/index.server'; // reused query
import { db } from '$lib/shared/db/index.server';

export const load = async ({ locals }) => {
	const user = await getUserById(locals.session!.userId);
	// page-specific query stays here (Pages First)
	const stats = await db.query.stats.findMany(/* ... */);
	return { user, stats };
};
```

### Writes: form actions + invalidation

Actions validate input, write, and return; SvelteKit reruns `load`
afterwards, so no client cache management is needed:

```typescript
// pages/profile/api/profile.server.ts
import { fail } from '@sveltejs/kit';

export const actions = {
	update: async ({ request, locals }) => {
		const form = await request.formData();
		const name = String(form.get('name') ?? '');
		if (!name) return fail(400, { name, missing: true });
		await updateProfile(locals.session!.userId, { name });
		return { success: true };
	}
};
```

For finer-grained refresh (e.g., after a client-side fetch), tag the load
with `depends("app:dashboard")` and call `invalidate("app:dashboard")` from
the consuming component. Keep such dependency keys as constants in
`shared/config/` when used from more than one slice.

**Key principle:** the page slice owns its `load` and `actions`. Reusable
queries live in `entities/<name>/api/`; `shared/db/` holds only the client
and schema. Do not put `load` functions in `shared/` — a load is page code.
