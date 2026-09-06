---
name: styling-with-tailwind
description: 'Writes and reviews Tailwind CSS v4 markup, themes, and configuration — utility classes, variants, container queries, @theme design tokens, and custom utilities. Use when building, styling, or restyling any component in a codebase that uses utility classes, even when the request never names Tailwind, and when setting up, configuring, or migrating it from v3 to v4. Also use on symptoms where Tailwind is never named as the cause: shadows or corners render smaller than expected, a gradient or focus ring stopped working, borders show up the wrong color, tailwind.config.js appears to be ignored, @apply fails inside a Vue or Svelte style block, or class names built by string interpolation produce no CSS. Not for visual or typographic direction that produces no utility-class markup.'
license: MIT
---

# Styling with Tailwind

Tailwind v4 configures itself in CSS, not JavaScript, and renamed several
scales so that every size has a name. Both changes are quiet: v3 syntax mostly
still compiles, just at a different size or with a different default color. The
overwhelming majority of Tailwind code written before v4 is v3, so the default
habit is v3 and nothing in the build output corrects it.

Assume v4 unless the project pins `tailwindcss` to `^3` in `package.json`. For
a v3 project, use v3 syntax and say so.

## Setup recipe

All configuration lives in the CSS entry file:

```css
@import 'tailwindcss';

@theme {
	--color-brand-500: oklch(0.62 0.19 259);
	--font-display: 'Satoshi', sans-serif;
	--breakpoint-3xl: 120rem;
}
```

Defining `--color-brand-500` is what creates `bg-brand-500`, `text-brand-500`,
`border-brand-500`, and the rest — theme variables generate utilities, they
aren't just values. Namespace determines which utilities appear, so a color must
go under `--color-*` and a breakpoint under `--breakpoint-*`.

Build integration: `@tailwindcss/postcss` for PostCSS, `@tailwindcss/vite` for
Vite, `@tailwindcss/webpack` for webpack, `@tailwindcss/cli` for the CLI. Drop
`autoprefixer` and `postcss-import`; v4 does both itself. A `tailwind.config.js`
is no longer auto-detected — load it with `@config "../tailwind.config.js"` only
when migrating an existing one.

When setting Tailwind up in a repo that also contains documentation, add
`@source not` for those directories at the same time — see `INSTALL.md` for why
and how. This includes the directory holding this skill.

## Renames that change appearance silently

Every bare utility shifted one step down the scale, so v3 code keeps compiling
at the wrong size. Reach for the v4 column:

| Intent            | v3                     | v4                        |
| ----------------- | ---------------------- | ------------------------- |
| Smallest shadow   | `shadow-sm`            | `shadow-xs`               |
| Default shadow    | `shadow`               | `shadow-sm`               |
| Smallest radius   | `rounded-sm`           | `rounded-xs`              |
| Default radius    | `rounded`              | `rounded-sm`              |
| Smallest blur     | `blur-sm`              | `blur-xs`                 |
| Default blur      | `blur`                 | `blur-sm`                 |
| Default ring      | `ring` (3px, blue-500) | `ring-3` + explicit color |
| Invisible outline | `outline-none`         | `outline-hidden`          |

`drop-shadow-*` and `backdrop-blur-*` shifted the same way.

Three defaults also changed with no syntax tell: `border-*` and `divide-*` use
`currentColor` instead of `gray-200`, `ring` is `1px currentColor`, and
placeholders inherit text color at 50% opacity. Set a color explicitly whenever
you add a border, divide, or ring.

## Rules

- **Write complete class names.** Tailwind scans source as plain text, so
  `bg-${color}-500` and `text-{{ error ? 'red' : 'green' }}-600` generate
  nothing. Map props to whole classes: `{ blue: "bg-blue-600 hover:bg-blue-500" }`.
- **Gradients are `bg-linear-*`,** plus `bg-radial` and `bg-conic-*`.
  `bg-gradient-to-r` produces no CSS.
- **Opacity is a modifier:** `bg-black/50`, `text-white/75`. The `*-opacity-*`
  utilities were removed.
- **Important goes last:** `bg-red-500!`, not `!bg-red-500`.
- **CSS variables in arbitrary values use parentheses:** `bg-(--brand)`, which is
  shorthand for `bg-[var(--brand)]`. Square brackets are for literal values, and
  spaces inside them are written as underscores: `grid-cols-[24rem_1fr]`.
- **Variants stack left to right,** matching CSS reading order: `*:first:pt-0`,
  `dark:md:hover:bg-fuchsia-600`.
- **Custom utilities use `@utility`,** not `@layer utilities`, or variants like
  `hover:` won't apply to them.
- **Prefer utilities over `@apply`.** In a Vue, Svelte, Astro, or CSS-module
  `<style>` block, `@apply` needs `@reference "../app.css";` first, or it fails
  on unknown theme values. Plain `var(--color-blue-500)` avoids the problem and
  is faster to build.
- **Logical positioning uses `inset-s-*` / `inset-e-*`.** Bare `start-*` and
  `end-*` are deprecated. `col-start-*` and `row-start-*` are unrelated and fine.
- **Reach for `size-6`** over `h-6 w-6`, and `gap` in a flex or grid container
  over `space-x-*`, whose selector changed and misbehaves with inline elements.

## Design defaults

Unless the project says otherwise: build mobile-first and let unprefixed
utilities cover small screens, since `sm:` means "at the 40rem breakpoint and
up", not "on phones". Pair every `dark:` color with its light counterpart on the
same element. Prefer `focus-visible:` over `focus:` for keyboard rings. Reuse
markup through a component or loop rather than a `.btn` class — one element
repeated five times in a template is not duplication worth abstracting.

## Verify

Run the checker over any file you wrote or edited:

```
python3 scripts/check_tailwind_v4.py path/to/file.tsx path/to/app.css
```

It flags `BROKEN` (generates no CSS), `SILENT` (compiles at a different size or
color), and `CHECK` (a default worth confirming). Stdlib only, no install. If you
cannot execute code, walk the renames table and the Rules list above instead.

## Where to look

- `references/v3-to-v4-migration.md` — full rename, removal, and behavioral-change
  tables. Read when migrating a project, or when existing markup renders wrong.
- `references/variants.md` — all 111 built-in variants, plus `group`/`peer`/
  `has-*`/`not-*`/`in-*` patterns and container queries. Read when a style
  depends on parent, sibling, descendant, or device state.
- `references/theme-and-utilities.md` — theme namespaces, the default scales and
  color palette, `@utility` with `--value()`, `@custom-variant`, and source
  detection. Read when defining design tokens, adding a custom utility, or
  safelisting classes.

## Gotchas

- Every file in the project is scanned, not just components — markdown, MDX, and
  plain text included. A README, Storybook page, or agent-instruction file that
  documents class names contributes all of them to the bundle. Exclude non-source
  directories with `@source not "../docs";`.
- The palette includes `mauve`, `olive`, `mist`, and `taupe` alongside the
  familiar 22 — all 11 shades, 50 through 950.
- `hover:` only applies where the device actually supports hover, so it cannot
  be relied on for tap behavior on touchscreens.
- Buttons get `cursor: default`, not `cursor: pointer` — add `cursor-pointer`
  yourself if you want it.
- Preflight strips heading sizes, list markers, and all margins; `<dialog>`
  margins are reset too, so a native dialog is no longer auto-centered.
- An element with the `hidden` attribute stays hidden even if you add `block` or
  `flex`; remove the attribute instead.
- `transform-none` no longer resets `rotate-*`, `scale-*`, or `translate-*` —
  they are individual CSS properties now, so reset the specific one.
- Sass, Less, and Stylus are not supported; v4 is itself the preprocessor.
- v4 targets Safari 16.4+, Chrome 111+, Firefox 128+. Older support means staying
  on v3.4.
