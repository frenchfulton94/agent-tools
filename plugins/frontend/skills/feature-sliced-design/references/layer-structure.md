# Layer Structure Reference

Detailed folder structures, code examples, and naming conventions for each
FSD layer in this SvelteKit codebase (layers under `src/lib/`). Use this
reference when creating, reviewing, or reorganizing project structure.

## Contents

1. [App Layer](#app-layer)
2. [Pages Layer](#pages-layer)
3. [Widgets Layer](#widgets-layer)
4. [Features Layer](#features-layer)
5. [Entities Layer](#entities-layer)
6. [Shared Layer Structure](#shared-layer-structure)
7. [Segments](#segments)
8. [Naming Conventions](#naming-conventions)
9. [Slice Groups](#slice-groups)
10. [Path Aliases](#path-aliases)

---

## App Layer

App-wide initialization: global styles, hook implementations, root context,
app-wide endpoints. Organized by segments only, no slices.

In SvelteKit the actual entry points are fixed files outside the layer
(`src/routes/+layout.svelte`, `src/hooks.server.ts`, `src/app.html`). Those
files stay thin and import their implementations from `$lib/app/`. The
methodology does not formally standardize App segment names; use names that
describe purpose:

```text
lib/app/
  styles/            ← Global CSS, reset, theme variables
  hooks/             ← handle.server.ts, handle-error.server.ts
  api/               ← App-wide endpoint handlers (*.server.ts)
  config/            ← App-level configuration
  index.ts           ← Universal exports (if any)
  index.server.ts    ← export { handle } from './hooks/handle.server'
```

```typescript
// src/hooks.server.ts (fixed SvelteKit file — thin)
export { handle } from '$lib/app/index.server';
```

```svelte
<!-- src/routes/+layout.svelte (fixed SvelteKit file — thin) -->
<script lang="ts">
	import '$lib/app/styles/global.css';
	let { children } = $props();
</script>

{@render children()}
```

**Belongs in app:** global styles, hook implementations (`handle`,
`handleError`, `reroute`), app-wide context set in the root layout, error
page shell, analytics initialization.

**Does not belong:** feature-specific code, business logic, page-level UI,
routing itself (that is `src/routes/`).

---

## Pages Layer

Route-level composition. In v2.1, pages **own substantial logic**: they are
not thin wrappers. In early project stages, most code lives here — including
each page's `load` and form `actions`.

```text
lib/pages/
  home/
    ui/
      HomePage.svelte
      HeroSection.svelte
      FeaturesGrid.svelte
    index.ts
  profile/
    ui/
      ProfilePage.svelte
      ProfileForm.svelte
      ProfileStats.svelte
    model/
      profile.ts               ← Page-specific state + validation logic
    api/
      profile.server.ts        ← load + actions for this page
    index.ts                   ← export { default as ProfilePage } from './ui/ProfilePage.svelte'
    index.server.ts            ← export { load, actions } from './api/profile.server'
```

The matching route files in `src/routes/` render `ProfilePage` and re-export
`load`/`actions` — see `references/sveltekit-integration.md`.

**Belongs in pages:** page-specific UI, forms, validation, `load` functions,
form actions, state management, business logic, API integrations. Even code
that looks reusable stays here if it is simpler to keep local.

**Does not belong:** code that is currently being reused across multiple
pages with stable boundaries (extract to a lower layer when reuse is
confirmed, not anticipated).

### Page Layout Patterns

A typical page composes widgets, features, and entities from lower layers,
plus its own local UI components:

```svelte
<!-- lib/pages/product-detail/ui/ProductDetailPage.svelte -->
<script lang="ts">
	import { Header } from '$lib/widgets/header';
	import { AddToCart } from '$lib/features/add-to-cart';
	import { ProductCard } from '$lib/entities/product';
	import RelatedProducts from './RelatedProducts.svelte'; // local component

	let { data } = $props(); // from this page's load
</script>

<Header />
<ProductCard product={data.product} />
<AddToCart productId={data.product.id} />
<RelatedProducts products={data.related} />
```

For pages that only need shared + page-local code (no extracted layers):

```svelte
<!-- lib/pages/about/ui/AboutPage.svelte -->
<script lang="ts">
	import Card from '$lib/shared/ui/Card.svelte';
	import TeamSection from './TeamSection.svelte'; // local to this page
	import MissionStatement from './MissionStatement.svelte';
</script>

<main>
	<MissionStatement />
	<Card><TeamSection /></Card>
</main>
```

---

## Widgets Layer

Composite UI blocks with their own logic, **reused across multiple pages**.
Add this layer only when UI blocks actually appear in 2+ pages and sharing
provides clear value.

```text
lib/widgets/
  header/
    ui/
      Header.svelte
      Navigation.svelte
      UserMenu.svelte
    model/
      header.svelte.ts         ← Widget state (runes)
    index.ts
  sidebar/
    ui/
      Sidebar.svelte
    index.ts
```

**Belongs in widgets:** navigation bars, sidebars, dashboards, footers,
complex card layouts that combine data from multiple entities/features.

**Does not belong:** simple UI primitives (→ `shared/ui/`), single-use
page sections (→ keep in the page).

---

## Features Layer

Independent, reusable user interactions. **Create only when used in 2+ places.**

```text
lib/features/
  auth/
    ui/
      LoginForm.svelte
      RegisterForm.svelte
    model/
      auth.ts                  ← Auth form state + logic
    index.ts
  add-to-cart/
    ui/
      AddToCartButton.svelte
    model/
      cart.svelte.ts
    index.ts
  like-post/
    ui/
      LikeButton.svelte
    api/
      toggle-like.ts
    index.ts
```

**Feature composition**: features consume entities and are composed in
higher layers:

```svelte
<!-- lib/widgets/post-card/ui/PostCard.svelte -->
<script lang="ts">
	import { UserAvatar } from '$lib/entities/user';
	import { LikeButton } from '$lib/features/like-post';
	import { CommentButton } from '$lib/features/comment-create';

	let { post } = $props();
</script>

<article>
	<UserAvatar userId={post.authorId} />
	<h2>{post.title}</h2>
	<p>{post.content}</p>
	<div>
		<LikeButton postId={post.id} />
		<CommentButton postId={post.id} />
	</div>
</article>
```

---

## Entities Layer

Reusable business domain models. **Create only when used in 2+ places. Starting
without this layer is completely valid.**

```text
// Minimal entity: model only (most common form)
lib/entities/user/
  model/
    user.ts                    ← Types + domain logic
  index.ts

// Entity with server-side queries
lib/entities/user/
  model/user.ts
  api/user-queries.server.ts   ← Reused db queries
  index.ts
  index.server.ts              ← export { getUserById } from './api/user-queries.server'

// Entity with UI (use with caution)
// ⚠️ Adding UI to entities increases cross-import risk.
// Entity UI should only be imported from higher layers (features, widgets,
// pages), never from other entities.
lib/entities/product/
  model/
    product.ts
  ui/
    ProductCard.svelte
  index.ts
```

---

## Shared Layer Structure

Infrastructure with no business logic. Organized by segments only (no slices).
Segments may import from each other.

```text
lib/shared/
  ui/                ← UI kit: Button, Input, Modal, Card
  lib/               ← Utilities: formatDate, debounce, classnames
  api/               ← API client, route constants, CRUD helpers, base types
  auth/              ← Auth instance (.server.ts), auth client, session utils
  db/                ← Database client (.server.ts) and schema
  config/            ← Environment-derived settings, app settings
  assets/            ← Branding assets shared across the app (use sparingly)
```

```svelte
<!-- lib/shared/ui/Button/Button.svelte -->
<script lang="ts">
	let { variant = 'primary', onclick, children } = $props();
</script>

<button class={`btn btn-${variant}`} {onclick}>
	{@render children()}
</button>
```

```typescript
// lib/shared/ui/Button/index.ts
export { default as Button } from './Button.svelte';
```

Shared **may** contain application-aware code (route constants, API endpoints,
branding assets, common types). It must **never** contain business logic,
feature-specific code, or entity-specific code.

For asset placement specifically (images, icons, fonts, PDFs), see
`references/asset-handling.md`.

---

## Segments

A segment groups related code within a slice (or within App/Shared). The
standard segments cover the most common technical purposes:

- **`ui`**: UI display (Svelte components, date formatters, styles).
- **`api`**: backend interactions (`load`/`actions` implementations as
  `.server.ts` files, request functions, data types, mappers).
- **`model`**: data model (schemas, interfaces, rune state in `.svelte.ts`
  files, business logic).
- **`lib`**: library code that other modules in this slice need.
- **`config`**: configuration files and feature flags.

Custom segments are allowed when needed (for example, `db` and `auth` in the
Shared layer, or `hooks` and `styles` in the App layer).

### Group by what it is _for_, not by what it _is_

Segment names describe **purpose**, not the kind of code they hold. This
is the desegmentation principle:

```text
// ❌ BAD: grouping by technical kind (what the code is)
shared/
  components/         ← What kind of components?
  stores/             ← Which domain do they serve?
  types/              ← Which domain do they describe?
  utils/              ← Utility for what?
  helpers/            ← Same problem

// ✅ GOOD: grouping by purpose (what the code is for)
shared/
  ui/                 ← For displaying UI
  api/                ← For talking to the backend
  lib/                ← For library code that supports the slice
  config/             ← For configuration
```

A segment named `types/` cannot answer "types for what?" without inspecting
the contents. A segment named `model/` says: this is the data model.
Inside `model/`, files are named by domain (`user.ts`, `order.ts`), not by
technical role.

This rule applies everywhere: in `shared/`, in slices, and when designing
new custom segments.

## Naming Conventions

### Domain-based file naming

Within a segment, name files after the business domain, not the technical
role:

```text
// ❌ Technical-role naming: mixes domains
model/types.ts             ← Which types? User? Order?
model/utils.ts
model/store.svelte.ts      ← Store of what?
api/endpoints.ts

// ✅ Domain-based naming: each file owns one domain
model/user.ts              ← User types + logic
model/cart.svelte.ts       ← Cart rune state + logic
api/profile.server.ts      ← Profile load/queries, server-only
```

Two suffixes carry meaning and combine with domain names:

- `.svelte.ts` — the module uses runes (`$state`, `$derived`).
- `.server.ts` — the module is server-only (SvelteKit-enforced).

### Single-concern segments

If a segment contains only one domain concern, the filename may match the
slice name:

```text
lib/features/auth/
  model/
    auth.ts          ← Single concern, matches slice name
```

### Index files as public API

Every slice has an `index.ts` that re-exports its public interface. A slice
with server-only exports has a second file, `index.server.ts` (see SKILL.md
Rule 4-2):

```typescript
// lib/entities/user/index.ts
export { default as UserAvatar } from './ui/UserAvatar.svelte';
export { type User } from './model/user';

// lib/entities/user/index.server.ts
export { getUserById } from './api/user-queries.server';
```

`index.ts` must never re-export from a `.server.ts` module.

---

## Slice Groups

A **slice group** is a folder that contains related slices on the same
layer, used purely to make the structure easier to navigate as the number
of slices grows. A slice group is **not** a slice itself: it has no
segments (`model/`, `ui/`, `api/`), no public API (`index.ts`), and no
shared code. Slice isolation rules apply unchanged inside a group: sibling
slices in the same group cannot import from each other.

Slice groups are optional. Use them only when the layer has grown large
enough that a flat structure becomes hard to scan and there is an obvious
grouping criterion.

### When to use

- Several slices share the same business context and are scattered across
  the layer.
- The slice names clearly suggest they belong to the same topic.
- The layer has grown to the point where it is hard to scan at a glance.

### When NOT to use

- Names alone are enough for quick navigation.
- There is no natural grouping criterion.
- Only two or three slices would end up in the group.

### Example: grouping payment-related entities

```text
lib/entities/
  payment/                  ← Slice group (no public API)
    invoice/                ← Slice
      model/
      ui/
      index.ts
    receipt/                ← Slice (model/, ui/, index.ts)
    transaction/            ← Slice (model/, ui/, index.ts)
  user/                     ← Slice (not in any group)
  product/                  ← Slice
```

Imports go through the full path:

```typescript
import { Invoice } from '$lib/entities/payment/invoice';
import { Receipt } from '$lib/entities/payment/receipt';
```

The same pattern applies to the Pages layer. For example, grouping
`pages/order/{list,detail,create}` when there are multiple pages on the same
topic such as list, detail, create, and edit. This is one possible example
and does not represent the default structure for the Pages layer.

### Features: use with caution

Slice groups can be applied to Features, but features often span multiple
entities and lack a natural grouping criterion. A group like
`features/cart/` tends to attract everything cart-related (DTOs, mappers,
helpers) until it stops being a navigation aid and starts acting as the
home for the entire cart domain, which weakens the principle that
features are split by use case. Before grouping features, check that the
group contains only feature slices and that two or three slices is not the
entire content.

### Anti-patterns

- **Do not put `index.ts` on the group folder.** That promotes the group
  to a slice and breaks the layer's contract.
- **Do not put shared `utils.ts`, `constants.ts`, or `types.ts` files
  inside the group.** A slice group has no shared code. Extract reusable
  code to `shared/` instead. If the layer is `entities` and the shared
  logic is genuinely domain logic, consider whether the boundaries are
  too granular and the slices should be merged into one isolated entity
  (see `references/excessive-entities.md`). The `@x` notation does not
  apply to slice groups. It is a cross-import surface between entity
  slices, not a sharing mechanism for siblings within a group.
- **Do not relax slice isolation inside the group.** If two slices in the
  same group need to share code, extract it one layer down rather than
  adding a `_common/` file.

---

## Path Aliases

Imports follow `$lib/<layer>/<slice>` using SvelteKit's built-in `$lib`
alias — no configuration needed:

```typescript
import { ProfilePage } from '$lib/pages/profile';
import { Header } from '$lib/widgets/header';
import { Button } from '$lib/shared/ui/Button';
```

Do not add per-layer aliases; `$lib` already covers all layers. For route
wiring and server-boundary details, see
`references/sveltekit-integration.md`.
