# v3 → v4 Migration Reference

Contents:

- [Automated upgrade](#automated-upgrade)
- [Build setup](#build-setup)
- [Renamed utilities](#renamed-utilities)
- [Removed utilities](#removed-utilities)
- [Syntax changes](#syntax-changes)
- [Changed defaults with no syntax tell](#changed-defaults-with-no-syntax-tell)
- [Preflight changes](#preflight-changes)
- [Configuration and JavaScript API](#configuration-and-javascript-api)
- [Framework style blocks](#framework-style-blocks)

## Automated upgrade

`npx @tailwindcss/upgrade` handles most of this mechanically: dependencies, the
config-to-CSS migration, and template updates. It needs Node 20+. Run it on a
branch and review the diff — it does not catch everything, and the silent
appearance changes below are the ones it can miss.

Browser floor: Safari 16.4, Chrome 111, Firefox 128. v4 depends on `@property`
and `color-mix()`. Projects needing older browsers stay on v3.4.

## Build setup

| v3                                     | v4                                           |
| -------------------------------------- | -------------------------------------------- |
| `tailwindcss` as a PostCSS plugin      | `@tailwindcss/postcss`                       |
| `npx tailwindcss -i in.css -o out.css` | `npx @tailwindcss/cli -i in.css -o out.css`  |
| PostCSS plugin under Vite              | `@tailwindcss/vite` (preferred, faster)      |
| PostCSS plugin under webpack           | `@tailwindcss/webpack`                       |
| `postcss-import`, `autoprefixer`       | Remove both; v4 bundles imports and prefixes |

```css
/* v3 */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* v4 */
@import 'tailwindcss';
```

What that import expands to, useful when you need to disable a piece:

```css
@layer theme, base, components, utilities;
@import 'tailwindcss/theme.css' layer(theme);
@import 'tailwindcss/preflight.css' layer(base); /* omit to drop Preflight */
@import 'tailwindcss/utilities.css' layer(utilities);
```

Options attach to the import they affect: `source(…)` and `important` on
`utilities.css`, `theme(static)` or `theme(inline)` on `theme.css`, and
`prefix(tw)` on both.

## Renamed utilities

Every scale gained a named smallest step, pushing the old names down one slot.
The old names still compile, at the wrong size.

| v3                  | v4                                            |
| ------------------- | --------------------------------------------- |
| `shadow-sm`         | `shadow-xs`                                   |
| `shadow`            | `shadow-sm`                                   |
| `drop-shadow-sm`    | `drop-shadow-xs`                              |
| `drop-shadow`       | `drop-shadow-sm`                              |
| `blur-sm`           | `blur-xs`                                     |
| `blur`              | `blur-sm`                                     |
| `backdrop-blur-sm`  | `backdrop-blur-xs`                            |
| `backdrop-blur`     | `backdrop-blur-sm`                            |
| `rounded-sm`        | `rounded-xs`                                  |
| `rounded`           | `rounded-sm`                                  |
| `outline-none`      | `outline-hidden`                              |
| `ring`              | `ring-3`                                      |
| `start-*` / `end-*` | `inset-s-*` / `inset-e-*` (deprecated in 4.2) |

`outline-none` still exists in v4 but now genuinely sets `outline-style: none`.
The v3 behavior — a transparent outline that stays visible in forced-colors mode
for accessibility — is `outline-hidden`. Keep using it for focus styles that
need a custom ring.

`outline-<number>` now implies `outline-style: solid`, so `outline outline-2`
collapses to `outline-2`. Bare `outline` is `outline-width: 1px`.

## Removed utilities

| Removed                 | Replacement            |
| ----------------------- | ---------------------- |
| `bg-opacity-*`          | `bg-black/50`          |
| `text-opacity-*`        | `text-black/50`        |
| `border-opacity-*`      | `border-black/50`      |
| `divide-opacity-*`      | `divide-black/50`      |
| `ring-opacity-*`        | `ring-black/50`        |
| `placeholder-opacity-*` | `placeholder-black/50` |
| `flex-shrink-*`         | `shrink-*`             |
| `flex-grow-*`           | `grow-*`               |
| `overflow-ellipsis`     | `text-ellipsis`        |
| `decoration-slice`      | `box-decoration-slice` |
| `decoration-clone`      | `box-decoration-clone` |
| `bg-gradient-to-*`      | `bg-linear-to-*`       |

Gradients gained `bg-radial`, `bg-radial-[…]`, and `bg-conic-<angle>` at the
same time. Gradient interpolation defaults to oklab.

## Syntax changes

**CSS variables in arbitrary values** moved from square brackets to parentheses,
because `[--var]` became ambiguous under newer CSS:

```html
<div class="bg-[--brand-color]"></div>
<!-- v3 -->
<div class="bg-(--brand-color)"></div>
<!-- v4 -->
```

**The important modifier** moved to the end of the class:

```html
<div class="!flex !bg-red-500"></div>
<!-- v3, deprecated -->
<div class="flex! bg-red-500!"></div>
<!-- v4 -->
```

**Variant stacking order** flipped from right-to-left to left-to-right, to read
like CSS. Only order-sensitive stacks are affected — in practice `*` and
typography plugin variants:

```html
<ul class="first:*:pt-0 last:*:pb-0">
	<!-- v3 -->
	<ul class="*:first:pt-0 *:last:pb-0">
		<!-- v4 -->
	</ul>
</ul>
```

**Commas in `grid-cols-*`, `grid-rows-*`, and `object-*` arbitrary values** are
no longer converted to spaces. Use underscores:
`grid-cols-[max-content_auto]`.

**Prefixes** are now written as a leading variant, and theme variables are still
declared unprefixed even though the generated CSS variables carry the prefix:

```css
@import 'tailwindcss' prefix(tw);
```

```html
<div class="tw:flex tw:bg-red-500 tw:hover:bg-red-600"></div>
```

**Custom utilities** use `@utility` instead of `@layer utilities`. v4 uses real
cascade layers and no longer repurposes `@layer`, so a class defined in
`@layer utilities` is not a utility and gets no variant support:

```css
@utility tab-4 {
	tab-size: 4;
}
```

Custom utilities sort by how many properties they declare, so a multi-property
`@utility btn` can be overridden by a single-property utility like `rounded-none`
without extra configuration.

**The `container` utility** lost its `center` and `padding` options. Extend it:

```css
@utility container {
	margin-inline: auto;
	padding-inline: 2rem;
}
```

## Changed defaults with no syntax tell

These are the changes most likely to be mistaken for a bug elsewhere.

- **Border and divide color** is `currentColor`, not `gray-200`. Specify a color
  on every `border-*` and `divide-*`.
- **Ring width and color** are `1px` and `currentColor`, previously `3px` and
  `blue-500`. `ring-3 ring-blue-500` restores the old look.
- **`space-x-*` / `space-y-*`** changed selector from
  `> :not([hidden]) ~ :not([hidden])` to `> :not(:last-child)` for performance.
  Spacing shifts when children are inline elements or carry their own margins.
  Prefer flex or grid with `gap`.
- **`divide-x-*` / `divide-y-*`** changed the same way.
- **Gradient variants preserve other stops.** In v3, `dark:from-blue-500` reset
  the whole gradient; in v4 the `via` and `to` stops survive. Use `via-none` to
  drop a three-stop gradient back to two in a given state.
- **`hover:`** is wrapped in `@media (hover: hover)`, so it no longer fires on
  tap. Treat hover as an enhancement. To opt out:
  `@custom-variant hover (&:hover);`
- **`transition` and `transition-colors` include `outline-color`.** Set the
  outline color unconditionally, or it animates from the default on focus.
- **`rotate-*`, `scale-*`, `translate-*`** map to the individual CSS properties.
  `transform-none` no longer resets them — use `scale-none` and friends. A custom
  `transition-[opacity,transform]` no longer covers them either; write
  `transition-[opacity,scale]`.

## Preflight changes

- Placeholder text uses the current text color at 50% opacity, not `gray-400`.
- Buttons use `cursor: default`, matching the browser. Restore with:
  ```css
  @layer base {
  	button:not(:disabled),
  	[role='button']:not(:disabled) {
  		cursor: pointer;
  	}
  }
  ```
- `<dialog>` margins are reset, so dialogs are no longer centered by default.
- The `hidden` attribute beats display utilities. `block` will not reveal an
  element with `hidden`; remove the attribute. `hidden="until-found"` is exempt.

## Configuration and JavaScript API

- JS config files are supported but no longer auto-detected. Load explicitly:
  `@config "../../tailwind.config.js";`
- `corePlugins`, `safelist`, and `separator` are unsupported. Safelist with
  `@source inline("…")` instead.
- `resolveConfig` was removed. Read the generated CSS variables:
  ```js
  getComputedStyle(document.documentElement).getPropertyValue('--shadow-xl');
  ```
  Libraries that accept CSS values can take `var(--color-blue-500)` directly.
- `theme()` is deprecated in favor of CSS variables. Where it is still needed —
  media queries, where variables don't work — it takes the variable name:
  `@media (width >= theme(--breakpoint-xl))`, not `theme(screens.xl)`.

## Framework style blocks

Stylesheets bundled separately from the main CSS file — CSS modules, and
`<style>` blocks in Vue, Svelte, and Astro — have no access to theme variables,
custom utilities, or custom variants. `@apply` there fails on unknown values.

```html
<style>
	@reference "../../app.css";
	h1 {
		@apply text-2xl font-bold text-red-500;
	}
</style>
```

`@reference` imports definitions without emitting duplicate CSS. If the project
uses the stock theme with no customization, `@reference "tailwindcss"` works.

Referencing the variable directly is better where it fits — Tailwind skips
processing the file entirely, which speeds up builds:

```html
<style>
	h1 {
		color: var(--color-red-500);
	}
</style>
```

Sass, Less, and Stylus are not supported at all. v4 handles imports, nesting
(via Lightning CSS), and prefixing itself.
