---
name: feature-sliced-design
description: >
  Official Feature-Sliced Design (FSD) v2.1 skill adapted for this SvelteKit
  + TypeScript codebase (FSD layers under src/lib, thin src/routes). Use when
  the task involves organizing project structure with FSD layers, deciding
  where code belongs, placing static assets (images, icons, fonts, PDFs),
  grouping closely related slices, defining public APIs and import boundaries
  (index.ts vs index.server.ts), keeping server-only code in .server.ts
  modules, resolving cross-imports or evaluating the @x pattern, deciding
  whether to create or remove an entity, evaluating whether the entities
  layer is needed at all, deciding whether logic should remain local or be
  extracted, wiring SvelteKit routes, load functions, form actions, and hooks
  to FSD slices, migrating from FSD v2.0 or a non-FSD codebase, or
  implementing common patterns such as authentication, API request handling,
  and state management with Svelte runes within FSD.
---

# Feature-Sliced Design (FSD) v2.1 — SvelteKit

> **Source**: [fsd.how](https://fsd.how) | Strictness can be adjusted based on
> project scale and team context.

---

## 1. Core Philosophy & Layer Overview

FSD v2.1 core principle: **"Start simple, extract when needed."**

Place code in the `pages` layer first. Duplication across pages is acceptable
and does not automatically require extraction to a lower layer. Extract only
when the same code is currently being used in multiple places (not
hypothetically), the usages do not always change together, and the boundary
has a focused responsibility.

**Not all layers are required.** Most projects can start with only `shared/`,
`pages/`, and `app/`. Add `widgets/`, `features/`, `entities/` only when they
provide clear value. Do not create empty layer folders "just in case."

FSD uses 6 standardized layers, listed here from highest to lowest:

```text
app/       → App initialization, global styles, hooks implementations
pages/     → Route-level composition, owns its own logic, load/actions
widgets/   → Large composite UI blocks reused across multiple pages
features/  → Reusable user interactions (only when used in 2+ places)
entities/  → Reusable business domain models (only when used in 2+ places)
shared/    → Infrastructure with no business logic (UI kit, utils, API client, db)
```

**Import rule**: A module may only import from layers strictly below it.
Cross-imports between slices on the same layer are forbidden.

```typescript
// ✅ Allowed
import Button from '$lib/shared/ui/Button.svelte'; // features → shared
import { user } from '$lib/entities/user'; // pages → entities

// ❌ Violation
import { login } from '$lib/features/auth'; // entities → features
import { likePost } from '$lib/features/like-post'; // features → features
```

**Note**: The `processes/` layer is **deprecated** in v2.1. For migration
details, read `references/migration-guide.md`.

### SvelteKit project layout (this codebase)

FSD is adapted to standard SvelteKit conventions. Where FSD and SvelteKit
best practices conflict, SvelteKit wins:

- **FSD layers live under `src/lib/`**:
  `src/lib/{app,pages,widgets,features,entities,shared}`. `src/lib/`
  contains only these layer directories.
- **`src/routes/` stays a standard SvelteKit route tree and remains thin.**
  A `+page.svelte` renders the page component from `$lib/pages/<slice>`;
  `+page.server.ts` / `+layout.server.ts` re-export `load` and `actions`
  from the slice's `index.server.ts`. No business logic in `src/routes/`.
- **Server-only modules use the `.server.ts` filename suffix** (enforced by
  SvelteKit), not a `server/` directory and not `$lib/server/`.
- **A slice with server-only exports gets a second public API file,
  `index.server.ts`**, next to its `index.ts` (see Rule 4-2).
- **Imports use the built-in `$lib` alias**: `$lib/<layer>/<slice>`. No
  extra alias configuration is needed.

For route wiring, hooks, form actions, and database placement, read
`references/sveltekit-integration.md`.

---

## 2. Decision Framework

When writing new code, follow this tree:

**Step 1: Where is this code used?**

- Used in only one page → keep it in that `pages/` slice.
- Used in 2+ pages but duplication is manageable → keeping separate copies
  in each page is also valid.
- An entity or feature used in only one page → keep it in that page
  (Steiger: `insignificant-slice`).

**Step 2: Is it reusable infrastructure with no business logic?**

- UI components → `shared/ui/`
- Utility functions → `shared/lib/`
- API client, route constants → `shared/api/` or `shared/config/`
- Auth instance, session utilities → `shared/auth/`
- Database client and schema → `shared/db/` (`.server.ts` modules)
- CRUD operations → `shared/api/`

**Step 3: Is it a complete user action currently used in multiple places,
with stable boundaries?**

- Yes → `features/`
- Uncertain, single use, or speculative reuse → keep in the page.

**Step 4: Is it a business domain model currently used in multiple places,
with stable boundaries?**

- Yes → `entities/`
- Uncertain, single use, or speculative reuse → keep in the page.

**Step 5: Is it app-wide configuration?**

- Global styles, hooks implementations, root providers/context → `app/`

**Golden Rule: When in doubt, keep it in `pages/`. Extract only when the
same code is actively used in multiple places and the boundary is clear.**

---

## 3. Quick Placement Table

Paths below are relative to `src/lib/`.

| Scenario              | Single use                                   | Confirmed multi-use                      |
| --------------------- | -------------------------------------------- | ---------------------------------------- |
| User profile form     | `pages/profile/ui/ProfileForm.svelte`        | `features/profile-form/`                 |
| Product card          | `pages/products/ui/ProductCard.svelte`       | `entities/product/ui/ProductCard.svelte` |
| Product data fetching | `pages/product-detail/api/product.server.ts` | `entities/product/api/`                  |
| Auth instance/session | `shared/auth/` (always)                      | `shared/auth/` (always)                  |
| Auth login form       | `pages/login/ui/LoginForm.svelte`            | `features/auth/`                         |
| CRUD operations       | `shared/api/` (always)                       | `shared/api/` (always)                   |
| Database queries      | page's `api/*.server.ts`                     | `shared/db/` or `entities/<name>/api/`   |
| Generic Card layout   |                                              | `shared/ui/Card/`                        |
| Modal manager         |                                              | `shared/ui/modal-manager/`               |
| Modal content         | `pages/[page]/ui/SomeModal.svelte`           |                                          |
| Date formatting util  |                                              | `shared/lib/format-date.ts`              |

---

## 4. Architectural Rules (MUST)

These rules are the foundation of FSD. Violations weaken the architecture.
If you must break a rule, ensure it is an intentional design decision and
document the reason in code (a comment or ADR).

### 4-1. Import only from lower layers

`app → pages → widgets → features → entities → shared`.
Upward imports and cross-imports between slices on the same layer are
forbidden. Files in `src/routes/` sit above every FSD layer: they may import
from any layer (in practice almost always `$lib/pages/` and `$lib/app/`),
and no FSD layer may import from `src/routes/`.

### 4-2. Public API: every slice exports through index.ts

External consumers may only import from a slice's `index.ts`. Direct imports
of internal files are forbidden.

```typescript
// ✅ Correct
import { LoginForm } from '$lib/features/auth';

// ❌ Violation: bypasses public API
import LoginForm from '$lib/features/auth/ui/LoginForm.svelte';
```

**Shared layer:** Shared has no slices. Define a separate public API per
segment (`shared/ui/index.ts`, `shared/api/index.ts`, etc.) rather than
one top-level `shared/index.ts`. This keeps imports from Shared
organized by intent.

### Server-only public APIs (index.server.ts)

A slice normally exposes its public API through a single `index.ts`. When a
slice contains server-only code (database queries, secrets from
`$env/static/private`, `load` functions, form `actions`), place that code in
`.server.ts` modules and export it through a second public API file,
`index.server.ts`:

- `index.ts` — universal exports, importable everywhere. Must never
  re-export from a `.server.ts` module.
- `index.server.ts` — server-only exports, importable only from other
  server modules and `src/routes/*` server files. SvelteKit fails the build
  if a `.server.ts` module leaks into client code.

Consumers import it by full name: `$lib/pages/profile/index.server`.
See `references/sveltekit-integration.md` for wiring examples.

### 4-3. No cross-imports between slices on the same layer

If two slices on the same layer need to share logic, follow the resolution
order in Section 7. Do not create direct imports.

### 4-4. Domain-based file naming (no desegmentation)

Name files after the business domain they represent, not their technical role.
Technical-role names like `types.ts`, `utils.ts`, `helpers.ts` mix unrelated
domains in a single file and reduce cohesion.

```text
// ❌ Technical-role naming
model/types.ts             ← Which types? User? Order? Mixed?
model/utils.ts

// ✅ Domain-based naming
model/user.ts              ← User types + related logic
model/order.svelte.ts      ← Order rune state + related logic
api/profile.server.ts      ← Clear purpose, server-only
```

### 4-5. No business logic in shared/

Shared contains only infrastructure: UI kit, utilities, API client setup,
database client, route constants, assets. Business calculations, domain
rules, and workflows belong in `entities/` or higher layers (e.g., `calculateUserReputation`
does not belong in `shared/lib/`; it belongs in `entities/user/lib/`).

---

## 5. Recommendations (SHOULD)

### 5-1. Pages First: place code where it is used

Place code in `pages/` first. Extract to lower layers only when truly needed.
Extraction is a design decision that affects the whole project, so the
threshold should be high.

**What stays in pages:**

- Large UI blocks used only in one page
- Page-specific forms, validation, data fetching (`load`), form `actions`,
  and state management
- Page-specific business logic and API integrations
- Code that looks reusable but is simpler to keep local

**Evolution pattern:** Start with everything in `pages/profile/`. When the
same user data is being consumed by another page (not hypothetically),
extract the shared model to `entities/user/`. Keep page-specific `load`
functions, actions, and UI in the page.

### 5-2. Be conservative with entities

The entities layer is highly accessible (almost every other layer can import
from it), so changes propagate widely.

1. **Start without entities.** `shared/` + `pages/` + `app/` is valid FSD.
2. **Do not split slices prematurely.** Extract to entities only when the
   same code is currently used by multiple consumers with a stable boundary.
3. **Business logic does not automatically require an entity.** Types in
   `shared/api` plus logic in the current slice's `model/` may be enough.
4. **Place CRUD in `shared/api/`.** CRUD is infrastructure, not entities.
5. **Place auth data in `shared/auth/` or `shared/api/`.** Sessions and
   login DTOs are rarely reused outside authentication.

For detailed guidance on keeping the entities layer clean (when to skip
it entirely, how to isolate business contexts, why CRUD belongs in
`shared/api`), see `references/excessive-entities.md`.

### 5-3. Start with minimal layers

```text
// ✅ Valid minimal FSD project
src/
  routes/        ← SvelteKit routing (thin entries, not an FSD layer)
  lib/
    app/         ← Global styles, hooks implementations, root context
    pages/       ← All page-level code
    shared/      ← UI kit, utils, API client, db

// Add layers only when an actual use case requires them:
// + widgets/   ← UI blocks currently reused across multiple pages
// + features/  ← User interactions currently reused across multiple pages
// + entities/  ← Domain models currently reused across pages or features
```

### 5-4. Validate with the Steiger linter

[Steiger](https://github.com/feature-sliced/steiger) is the official FSD
linter. Key rules:

- **`insignificant-slice`**: Suggests merging an entity/feature into its page
  if only one page uses it.
- **`excessive-slicing`**: Suggests merging or grouping when a layer has too
  many slices.

```bash
bun add -D @feature-sliced/steiger
bunx steiger ./src/lib
```

Point Steiger at `src/lib`, where the FSD layers live, not at `src`.

---

## 6. Anti-patterns (AVOID)

- **Do not create entities prematurely.** Data structures used in only one
  place belong in that place.
- **Do not put CRUD in entities.** Use `shared/api/`. Consider entities only
  for complex transactional logic.
- **Do not create a `user` entity just for auth data.** Sessions and login
  DTOs belong in `shared/auth/` or `shared/api/`.
- **Do not abuse `@x`.** It is a necessary compromise for the entities
  layer only, used when boundary merge is genuinely impossible. Features
  and widgets use strategies A–D (see Section 7).
- **Do not extract single-use code.** A feature or entity used by only one
  page should stay in that page.
- **Do not use technical-role file names.** Use domain-based names
  (see Rule 4-4).
- **Be cautious adding UI to entities.** Entity UI may only be imported
  from higher layers (features, widgets, pages), never from other entities.
- **Do not create god slices.** Split overly broad slices into focused ones
  (e.g., `user-management/` → `auth/`, `profile-edit/`, `password-reset/`).
- **Do not create a top-level `assets/` segment.** Place static assets next
  to the code that uses them. See `references/asset-handling.md`.
- **Do not put logic in `src/routes/`.** Route files re-export or render
  from `$lib/pages/`; anything more belongs in the page slice.
- **Do not re-export server-only code from `index.ts`.** Server-only exports
  go through `index.server.ts` (Rule 4-2).

---

## 7. Cross-Import Resolution

Cross-imports are a code smell, not an absolute prohibition. The right
strategy depends on the layer and the situation.

### Entities layer: prefer boundary merge, @x is last resort

Cross-imports in `entities` are usually caused by splitting entities too
granularly. Before reaching for `@x`, consider whether the boundaries
should be merged.

`@x` is a **necessary compromise, not a recommended approach**. Use it only
when boundaries genuinely cannot be merged, and document why. Overuse locks
entity boundaries together and increases refactoring cost.

### Features and widgets: four strategies (A, B, C, D)

In `features` and `widgets`, choose based on context:

- **Strategy A: Slice merge.** Two slices always change together → merge.
- **Strategy B: Push to entities.** Shared domain logic → move to
  `entities/`, keep UI in features/widgets.
- **Strategy C: Compose from upper layer (IoC).** The parent (pages or app)
  imports both slices and connects them via props, snippets, or context.
- **Strategy D: Public API access.** When reuse is genuinely unavoidable,
  allow it only through the slice's `index.ts`. Never reach into `model/`,
  `store/`, or internal files.

The `@x` notation is for the entities layer only. Features and widgets use
strategies A–D above.

Strictness varies by project context: early-stage products may accept some
cross-imports as a speed trade-off; long-lived systems benefit from strict
boundaries. Any accepted cross-import is a deliberate choice — document the
reasoning in code.

For detailed code examples of each strategy, read
`references/cross-import-patterns.md`.

---

## 8. Segments & Structure Rules

### Standard segments

Segments group code within a slice by technical purpose:

- **`ui/`**: Svelte components, styles, display-related code
- **`model/`**: Data models, rune state (`.svelte.ts`), business logic,
  validation
- **`api/`**: Backend integration, `load`/`actions` implementations
  (`.server.ts`), request functions, API-specific types
- **`lib/`**: Internal utility functions for this slice
- **`config/`**: Configuration, feature flags

### Layer structure rules

- **App and Shared**: No slices, organized directly by segments. Segments
  within these layers may import from each other.
- **Pages, Widgets, Features, Entities**: Slices first, then segments inside
  each slice.
- **Slice groups (optional)**: A group folder may contain related slices on
  the same layer for navigation purposes only. The group has no segments and
  no public API. See `references/layer-structure.md` for details.

### File naming within segments

Always use domain-based names that describe what the code is about:

```text
model/user.ts               ← User types + logic
model/cart.svelte.ts        ← Cart rune state + logic
api/profile.server.ts       ← Profile load/query, server-only
api/update-settings.server.ts
```

If a segment has only one domain concern, the filename may match the slice
name (e.g., `features/auth/model/auth.ts`).

---

## 9. Shared Layer Guide

Shared contains infrastructure with **no business logic**. It is organized by
segments only (no slices). Segments within shared may import from each other.

**Allowed in shared:**

- `ui/`: UI kit (Button, Input, Modal, Card)
- `lib/`: Utilities (formatDate, debounce, classnames)
- `api/`: API client, route constants, CRUD helpers, base types
- `auth/`: Auth instance (`.server.ts`), auth client, session utilities
- `db/`: Database client and schema (`.server.ts` modules)
- `config/`: Environment-derived settings, app settings
- `assets/`: Branding assets shared across the app (use sparingly; see
  `references/asset-handling.md`)

Shared **may** contain application-aware code (route constants, API endpoints,
branding assets, common types). It must **never** contain business logic,
feature-specific code, or entity-specific code.

---

## 10. Quick Reference

- **Import direction**: `app → pages → widgets → features → entities → shared`
- **Layout**: layers in `src/lib/<layer>`, imported as `$lib/<layer>/<slice>`;
  `src/routes/` is thin and renders/re-exports from `$lib/pages/`
- **Server boundary**: server-only code in `.server.ts` files; server-only
  public API in `index.server.ts`
- **Minimal FSD**: `app/` + `pages/` + `shared/`
- **Create entities/features when**: the same model or interaction is
  currently used in multiple places, with stable boundaries
- **Breaking rules**: only as an intentional, documented design choice
- **Cross-imports**: entities → merge boundaries first, `@x` last resort;
  features/widgets → strategies A–D. `@x` is for entities only
- **File naming**: domain-based (`user.ts`), never technical-role (`types.ts`)
- **Assets**: next to the code that uses them; reuse → `shared/ui/`; global
  styles/fonts → `app/`; fixed-URL files → `static/`
- **Processes layer**: deprecated. See `references/migration-guide.md`.

---

## 11. Conditional References

Read the following reference files **only** when the specific situation applies.
Do **not** preload all references.

- **When creating, reviewing, or reorganizing folder and file structure** for
  FSD layers and slices, including grouping closely related slices into a
  parent folder for navigation (e.g., "set up project structure", "where does
  this folder go", "how do I group these payment entities"):
  → Read `references/layer-structure.md`

- **When resolving cross-import issues** between slices on the same layer,
  evaluating the `@x` pattern, choosing between Strategy A/B/C/D for
  features and widgets, or deciding whether boundaries should be merged:
  → Read `references/cross-import-patterns.md`

- **When deciding whether to create or remove an entity**, dealing with too
  many entities, evaluating whether to skip the entities layer entirely,
  placing CRUD operations, deciding where authentication data belongs, or
  isolating business contexts to avoid `@x` chains:
  → Read `references/excessive-entities.md`

- **When deciding where to place static assets** (images, icons, fonts,
  PDFs, stylesheets) for a single slice, for sharing across slices, or
  globally:
  → Read `references/asset-handling.md`

- **When migrating** from FSD v2.0 to v2.1, converting a non-FSD codebase to
  FSD, or deprecating the processes layer:
  → Read `references/migration-guide.md`

- **When wiring SvelteKit to FSD** — connecting `src/routes/` files
  (`+page.svelte`, `+page.server.ts`, `+layout`, `+server.ts`,
  `hooks.server.ts`) to FSD slices, placing `load` functions and form
  `actions`, enforcing the `.server.ts` / `index.server.ts` boundary, or
  placing database access:
  → Read `references/sveltekit-integration.md`

- **When implementing concrete code patterns** for authentication, API
  request handling, type definitions, or state management (Svelte runes,
  per-request state via context, load/actions data flow) within FSD
  structure:
  → Read `references/practical-examples.md`
  Note: If you already loaded `layer-structure.md` in this conversation,
  avoid loading this file simultaneously. Address structure first, then load
  patterns in a follow-up step if needed.
