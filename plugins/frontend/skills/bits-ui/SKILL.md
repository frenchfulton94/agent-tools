---
name: bits-ui
description: Build, style, and wrap accessible UI components with Bits UI (bits-ui.com), the headless Svelte 5 component library. Use whenever a user writes Svelte/SvelteKit code involving an accordion, dialog, alert dialog, dropdown/context menu, menubar, navigation menu, command palette, select, combobox, popover, tooltip, calendar, date/time field or picker, slider, switch, toggle, checkbox, radio group, rating group, pin input, tabs, pagination, avatar, or progress/meter — even if they never say "bits-ui" or "headless." Also use for the `child` snippet / render delegation, the `ref` prop, `bind:value` vs function binding, styling via data attributes or CSS variables, `forceMount` + Svelte transitions, wrapping a primitive into a reusable design-system component, or `@internationalized/date`. Not for other libraries (shadcn-svelte, Melt UI, Skeleton) unless Bits UI is also involved, and not needed for plain native form elements with no accessibility/state complexity.
---

# Bits UI (Svelte 5)

Bits UI is a headless, unstyled component library for Svelte 5. It ships the
behavior — state, keyboard navigation, focus management, ARIA wiring — and
almost none of the visual styling, via a set of compound components (`Root`,
`Trigger`, `Content`, etc. under one namespace import). That division of
labor is the whole point: don't reach for custom `role`/`tabindex`/keydown
handling or hand-rolled focus traps on top of it, and don't expect any
visuals until you add `class`/`style` yourself.

This skill covers the patterns that apply across (almost) every component.
Component-specific prop names and data attributes are not duplicated here —
see **"Get the exact API before coding"** below.

## Get the exact API before coding

Bits UI's props, data attributes, and CSS variables evolve between releases,
and a wrong prop name usually fails silently (extra prop ignored) rather
than with a helpful error. Before writing non-trivial code against a
specific component, fetch its live doc:

```
https://bits-ui.com/docs/components/<slug>/llms.txt
```

`references/components.md` lists every component with its slug, grouped by
category, plus a one-line description — check it first to confirm you're
reaching for the right primitive, then fetch that URL for the full prop /
data-attribute / CSS-variable reference before implementing.

For the cross-cutting concepts distilled in this skill's reference files,
the equivalent live pages are `child-snippet`, `ref`, `state-management`,
`styling`, `transitions`, and `dates` under
`https://bits-ui.com/docs/<page>/llms.txt` — fetch one of these instead if
you need the exact current wording or something this skill doesn't cover.

## Installation

```bash
bun add bits-ui        # this project uses Bun workspaces
npm install bits-ui    # or, elsewhere
```

Always import the whole component namespace, never an individual part from
a subpath — the parts share state via Svelte context under `Root`, so they
have to come from the same namespace object:

```svelte
<script lang="ts">
	import { Accordion } from 'bits-ui';
</script>
```

## The patterns you'll use on almost every component

Full detail and examples for all four are in `references/patterns.md`.

1. **Render delegation (`child` snippet)** — swap the element/component a
   part renders, e.g. to use your own `<Button>` instead of `<button>` for
   a `Trigger`. Required whenever you need a Svelte transition, action, or
   custom component in place of the default element.
2. **The `ref` prop** — every part that renders an element exposes a
   bindable `ref` for direct DOM access. Works through `child` too, but
   only if you don't also set a hardcoded `id` on the delegated element.
3. **State management** — every stateful prop (`value`, `open`, `checked`,
   `placeholder`, ...) supports plain `bind:` for the common case, or a
   Svelte [function binding](https://svelte.dev/docs/svelte/bind#Function-bindings)
   (`bind:value={get, set}`) when you need to intercept, transform, debounce,
   or reject an update.
4. **Styling** — components are unstyled but not unstylable: use the
   `class`/`style` props, target the component's `data-*` attributes
   (namespaced per part, e.g. `[data-accordion-trigger]`) for state-based
   CSS (`[data-state="open"]`, `[data-disabled]`), and the component's
   `--bits-*` CSS variables for anything that needs a runtime-computed
   value (e.g. `--bits-accordion-content-height` for animating open/close).

## Wrap primitives into your own components

Sprinkling raw `<Accordion.Root>` / `<Accordion.Item>` / `<Accordion.Trigger>`
composition all over an app duplicates markup and gives every call site a
chance to apply your design tokens slightly differently. Bits UI's own
convention — and the one to default to for design-system work — is to wrap
each primitive once, in your own component, using the `WithoutChildrenOrChild`
type helper to accept all of the primitive's props except the two you're
about to supply yourself (`children`/`child`):

```svelte
<!-- FieldSwitch.svelte -->
<script lang="ts">
	import { Switch, type WithoutChildrenOrChild } from 'bits-ui';

	type Props = WithoutChildrenOrChild<Switch.RootProps> & { label: string };

	let { checked = $bindable(false), ref = $bindable(null), label, ...restProps }: Props = $props();
</script>

<label class="field-switch">
	<span class="field-switch__label">{label}</span>
	<Switch.Root bind:checked bind:ref {...restProps} class="field-switch__control">
		<Switch.Thumb class="field-switch__thumb" />
	</Switch.Root>
</label>
```

Callers then only ever see `<FieldSwitch label="Notifications" bind:checked={notify} />`
— all Bits UI wiring and your styling classes live in one place. Reach for
`WithoutChild` instead when the wrapper doesn't need to expose `children` at
all (e.g. a leaf part), and `WithElementRef` when adding this same
bindable-`ref` convention to a fully custom component that isn't wrapping
Bits UI at all.

## Dates and calendars

`Calendar`, `RangeCalendar`, `DateField`, `DateRangeField`, `DatePicker`,
`DateRangePicker`, `TimeField`, and `TimeRangeField` all take
`@internationalized/date` values, not native `Date` objects, and those
values are immutable. Read `references/dates.md` before touching any of
them — the 1-indexed months and immutability are the two mistakes people
make every time.

## Gotchas

- **Svelte 5 only.** Snippets (`{#snippet}` / `{@render}`), not slots;
  `$props()` / `$bindable()` / `$state()`, not `export let`. If you see
  `<slot>` or `export let` in a Bits UI example, it's stale v1/Svelte-4
  documentation — re-fetch the current doc rather than trust it.
- **Not every `Root` renders a DOM element.** `Accordion.Root`, `AlertDialog.Root`,
  and `Select.Root` are logic-only containers — only `children`, no `ref` or
  `child`. `Switch.Root` and similar toggle-style components do render an
  element and expose both. `WithoutChildrenOrChild` is safe to use either way
  (omitting a prop that doesn't exist is a no-op), but if you want the type
  that matches what the component actually declares, check its `Root` API
  table first — Bits UI's own examples use `WithoutChildren` for the
  logic-only ones.
- **`{...props}` is not optional inside `child`.** Skipping the spread (or
  putting it after your own conflicting props) silently drops the ARIA
  attributes and event handlers the part needs to function.
- **Floating content needs a two-level wrapper.** `Popover.Content`,
  `Select.Content`, `Combobox.Content`, `DropdownMenu.Content`,
  `Menubar.Content`, `Tooltip.Content`, `LinkPreview.Content`,
  `DatePicker.Content`, and `DateRangePicker.Content` position themselves
  via an outer element. When using `child` on these, spread `wrapperProps`
  on an outer (unstyled) element and `props` on an inner (styled) one —
  styling the wrapper breaks positioning. See `references/patterns.md`.
- **`value`'s type can depend on another prop.** `Accordion.Root`'s `value`
  is `string` when `type="single"` and `string[]` when `type="multiple"` —
  match them or TypeScript will (correctly) complain.
- **Data attributes are namespaced per part**, not global — it's
  `[data-accordion-trigger]` and `[data-dialog-trigger]`, never a shared
  `[data-trigger]`. Confirm the exact attribute name in the component's doc
  rather than guessing from another component.
- **Portal-rendered content escapes local CSS/z-index context.** Dialogs,
  popovers, menus, and tooltips render into `document.body` by default
  (via the `Portal` utility), so a parent's `overflow: hidden`, `z-index`,
  or `transform` won't affect them. If content looks visually "wrong,"
  this is the first thing to check.
- **Accessibility is already handled.** ARIA roles, keyboard navigation,
  and focus trapping are built in — adding your own on top usually creates
  conflicts rather than improvements. If default focus/keyboard behavior
  needs to change, look for the component's dedicated prop (e.g.
  `trapFocus`, `loop`, `onOpenAutoFocus`) instead of intercepting the DOM
  event yourself.
- **Styling composes with utility-class and BEM systems fine.** Bits UI
  doesn't inject its own classes, so `class` props and `tailwind-variants`/
  BEM conventions layer on top without fighting the library — target the
  component's `data-state`/`data-disabled` attributes as style variants
  instead of tracking state in your own `$state()` when the component
  already exposes it.

## Where this skill stops

Getting a component's wiring right — state, ARIA, structure, keyboard
behavior — is a different concern from whether the result looks and reads
well once it's on screen. This skill covers the former. For the latter
(typography, color, motion quality, hierarchy, "AI slop" pattern detection,
i18n/edge-case hardening), don't freelance an opinion from here — if the
Impeccable skill is installed in this project, hand off to
`/impeccable polish`, `/impeccable critique`, or `/impeccable audit` once
a component is behaviorally correct. Impeccable reads its own project-level
`PRODUCT.md`/`DESIGN.md` for brand/visual context; that's where design-token
and voice decisions belong, not duplicated here.

## Reference files

- `references/components.md` — every component, grouped by category, with
  a one-line description and its doc slug.
- `references/patterns.md` — render delegation, `ref`, state management,
  and styling (data attributes, CSS variables, `forceMount` + Svelte
  transitions), each with a worked example.
- `references/dates.md` — `@internationalized/date` value types, the
  `placeholder` prop, formatting/parsing, and range handling.
