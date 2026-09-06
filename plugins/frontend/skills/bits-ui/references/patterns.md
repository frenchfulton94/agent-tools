# Bits UI: cross-cutting patterns

Distilled from `child-snippet`, `ref`, `state-management`, `styling`, and
`transitions` at `https://bits-ui.com/docs/<page>/llms.txt`. Fetch the live
page if you need something beyond what's here.

## Render delegation: the `child` snippet

By default, a part like `Accordion.Trigger` renders a plain element (a
`<button>`) and forwards `props` to it internally. The `child` snippet lets
you take over that element yourself — needed for Svelte transitions/actions,
scoped `<style>`, or swapping in your own component.

```svelte
<Popover.Trigger>
	{#snippet child({ props })}
		<IconButton {...props} icon="filter" label="Filter results" />
	{/snippet}
</Popover.Trigger>
```

Rules:

- `props` carries every attribute and event handler the part needs
  (ARIA attributes, `onclick`, etc.) — spread it onto whichever element you
  choose to render, or the part stops working correctly.
- If you pass a custom `id`, `onclick`, or other prop to the _Bits UI part_
  itself, it gets merged into `props` automatically. Setting it directly
  on your delegated element instead (bypassing the part) breaks the `ref`
  binding described below.
- Using `child` replaces the part's default children entirely — anything
  passed outside the snippet is ignored.

### Floating content needs two levels

Positioned content (tooltips, popovers, dropdowns, comboboxes, selects,
menus, link previews, date pickers) separates positioning from visuals: an
outer wrapper element handles placement, and an inner element holds your
styled content. When delegating with `child` on these components, both
levels are exposed and both need to be rendered:

```svelte
<Tooltip.Content>
	{#snippet child({ wrapperProps, props, open })}
		{#if open}
			<div {...wrapperProps}>
				<div {...props} class="tooltip-panel">Extra context about this control</div>
			</div>
		{/if}
	{/snippet}
</Tooltip.Content>
```

Never put your own styling (padding, background, border, transform) on the
`wrapperProps` element — it exists purely to position `props`. Components
that require this wrapper: `Combobox.Content`, `DatePicker.Content`,
`DateRangePicker.Content`, `DropdownMenu.Content`, `LinkPreview.Content`,
`Menubar.Content`, `Popover.Content`, `Select.Content`, `Tooltip.Content`.

## The `ref` prop

Every part rendering an element exposes a bindable `ref`:

```svelte
<script lang="ts">
	import { Popover } from 'bits-ui';
	let triggerEl = $state<HTMLButtonElement | null>(null);
</script>

<Popover.Trigger bind:ref={triggerEl}>Open</Popover.Trigger>
```

`ref` starts out `null` until the element mounts — treat it the same way
you'd treat the result of `document.getElementById`. It works through
`child` too, matched internally by element ID, which is why a custom `id`
must be passed to the _part_ (`<Popover.Trigger id="my-id">`) rather than
set directly on your delegated element — setting it on the delegated
element breaks the part's ability to find and track it.

To add this same convention to a fully custom (non-Bits-UI) component, use
the `WithElementRef` type helper:

```svelte
<script lang="ts">
	import type { WithElementRef } from 'bits-ui';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	let {
		ref = $bindable(null),
		children,
		...rest
	}: WithElementRef<HTMLButtonAttributes, HTMLButtonElement> = $props();
</script>

<button bind:this={ref} {...rest}>{@render children?.()}</button>
```

## State management

Every stateful prop supports two binding modes:

**Two-way binding** (`bind:`) — the default choice. Zero boilerplate,
works with external programmatic updates automatically:

```svelte
<script lang="ts">
	let open = $state(false);
</script>

<button onclick={() => (open = true)}>Open</button>
<Dialog.Root bind:open>...</Dialog.Root>
```

**Function binding** — pass a getter and setter instead, when you need to
intercept, transform, or conditionally reject an update (debouncing,
validation, syncing to an external store):

```svelte
<script lang="ts">
	let value = $state('');
	let history: string[] = [];

	function getValue() {
		return value;
	}
	function setValue(next: string) {
		history.push(value);
		value = next;
	}
</script>

<Combobox.Root bind:value={getValue, setValue}>...</Combobox.Root>
```

The part calls the setter whenever it wants to change the value internally;
whether that setter actually updates the underlying `$state` is entirely up
to you, which is what makes this useful for validation or "reject this
update" logic that plain `bind:` can't express.

## Styling

Nothing renders styled by default except what accessibility strictly
requires (e.g. focus outlines are left to the browser/your CSS). Three ways
to style, usable together:

**1. `class` / `style` props** — the direct route, works with Tailwind,
utility classes, or scoped styles via `child`:

```svelte
<Switch.Root class="toggle" style="--toggle-size: 1.5rem;">
	<Switch.Thumb class="toggle__thumb" />
</Switch.Root>
```

**2. Data attributes** — every part exposes attributes namespaced to that
part (`[data-switch-root]`, `[data-switch-thumb]`) plus state attributes
like `[data-state="checked"]` and `[data-disabled]`. Useful for global
stylesheets or `:global()` blocks in scoped Svelte `<style>`:

```css
[data-switch-root][data-state='checked'] {
	background-color: var(--color-brand);
}
[data-switch-root][data-disabled] {
	opacity: 0.5;
}
```

Two more attributes appear specifically on components that manage their own
mount/unmount lifecycle for animations (overlays, floating content):
`data-starting-style` (present for the initial open frame) and
`data-ending-style` (present while closing, before unmount) — target these
for enter/exit CSS transitions without losing the close animation.

**3. `--bits-*` CSS variables** — exposed per-component for values that can
only be known at runtime, most often element dimensions used to animate a
collapsing/expanding region:

```css
[data-accordion-content] {
	overflow: hidden;
	transition: height 300ms ease-out;
	height: 0;
}
[data-accordion-content][data-state='open'] {
	height: var(--bits-accordion-content-height);
}
```

Exact variable names are per-component — check the component's API
reference rather than assuming a name.

### Svelte transitions via `forceMount`

CSS transitions driven by data attributes (above) are usually enough. Reach
for this only when the project specifically wants Svelte's `transition:`/
`in:`/`out:` directives or a JS animation library, since `transition:`
doesn't work directly on a component.

Conditionally-rendered parts (`Content`, `Overlay`, etc.) expose a
`forceMount` prop. Combine it with `child` to keep the element permanently
in the DOM and drive its presence yourself:

```svelte
<Dialog.Content forceMount>
	{#snippet child({ props, open })}
		{#if open}
			<div {...props} transition:fade={{ duration: 150 }}>
				<!-- dialog content -->
			</div>
		{/if}
	{/snippet}
</Dialog.Content>
```

For floating content, combine this with the two-level wrapper structure
above — `open` and `props` go on the inner element, `wrapperProps` on the
outer one, unstyled and untransitioned. **Gate both elements with a single
`{#if open}` wrapping the pair, not just the inner one** — a wrapper left
unconditional stays mounted (invisibly) even while closed, instead of being
removed alongside the content it exists to position:

```svelte
<Popover.Content forceMount>
	{#snippet child({ wrapperProps, props, open })}
		{#if open}
			<div {...wrapperProps}>
				<div {...props} transition:fly={{ y: -6, duration: 150 }}>
					<!-- popover content -->
				</div>
			</div>
		{/if}
	{/snippet}
</Popover.Content>
```

If more than one component in the app needs this treatment, extract it
into a reusable wrapper (see SKILL.md's "Wrap primitives into your own
components") rather than repeating the `forceMount` + `child` boilerplate
at each call site.
