# Theme and Custom Utilities Reference

Contents:

- [Theme namespaces](#theme-namespaces)
- [Default scales](#default-scales)
- [Color palette](#color-palette)
- [Customizing the theme](#customizing-the-theme)
- [Arbitrary values](#arbitrary-values)
- [Logical property utilities](#logical-property-utilities)
- [Custom utilities](#custom-utilities)
- [Source detection and safelisting](#source-detection-and-safelisting)

## Theme namespaces

A theme variable's namespace decides which utilities it creates. Put a value in
the wrong namespace and no utility appears.

| Namespace          | Creates                                                                                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--color-*`        | `bg-*`, `text-*`, `border-*`, `fill-*`, `stroke-*`, `ring-*`, `accent-*`, `caret-*`, `decoration-*`, `outline-*`, `shadow-*`, `scrollbar-thumb-*`, … |
| `--font-*`         | `font-sans` and other font-family utilities                                                                                                          |
| `--text-*`         | `text-xl` and other font sizes                                                                                                                       |
| `--font-weight-*`  | `font-bold` and other weights                                                                                                                        |
| `--tracking-*`     | `tracking-wide` letter spacing                                                                                                                       |
| `--leading-*`      | `leading-tight` line height                                                                                                                          |
| `--tab-size-*`     | `tab-github` and other tab sizes                                                                                                                     |
| `--breakpoint-*`   | `sm:*` responsive variants                                                                                                                           |
| `--container-*`    | `@sm:*` container variants, and `max-w-md` / `w-md` sizes                                                                                            |
| `--spacing-*`      | `px-4`, `max-h-16`, and the rest of the spacing scale                                                                                                |
| `--radius-*`       | `rounded-sm` and other radii                                                                                                                         |
| `--shadow-*`       | `shadow-md` box shadows                                                                                                                              |
| `--inset-shadow-*` | `inset-shadow-xs`                                                                                                                                    |
| `--drop-shadow-*`  | `drop-shadow-md`                                                                                                                                     |
| `--text-shadow-*`  | `text-shadow-sm`                                                                                                                                     |
| `--blur-*`         | `blur-md`                                                                                                                                            |
| `--perspective-*`  | `perspective-near`                                                                                                                                   |
| `--zoom-*`         | `zoom-compact`                                                                                                                                       |
| `--aspect-*`       | `aspect-video`                                                                                                                                       |
| `--ease-*`         | `ease-out` timing functions                                                                                                                          |
| `--animate-*`      | `animate-spin`                                                                                                                                       |

`@theme` is not interchangeable with `:root`. Theme variables generate utilities
and must be declared at the top level, unnested. Use `:root` for CSS variables
that should _not_ produce a utility.

## Default scales

Spacing is a single multiplier — `--spacing: 0.25rem` — and every numeric
spacing utility is `calc(var(--spacing) * n)`. So `p-4` is `1rem`, `p-6` is
`1.5rem`. Change one variable and the whole scale moves.

| Scale        | Values                                                                                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Breakpoints  | `sm` 40rem, `md` 48rem, `lg` 64rem, `xl` 80rem, `2xl` 96rem                                                                                                        |
| Containers   | `3xs` 16rem, `2xs` 18rem, `xs` 20rem, `sm` 24rem, `md` 28rem, `lg` 32rem, `xl` 36rem, `2xl` 42rem, `3xl` 48rem, `4xl` 56rem, `5xl` 64rem, `6xl` 72rem, `7xl` 80rem |
| Font size    | `xs` .75rem, `sm` .875rem, `base` 1rem, `lg` 1.125rem, `xl` 1.25rem, then `2xl`–`9xl` (1.5, 1.875, 2.25, 3, 3.75, 4.5, 6, 8rem)                                    |
| Font weight  | `thin` 100 → `black` 900 in hundreds                                                                                                                               |
| Tracking     | `tighter` −.05em, `tight` −.025em, `normal` 0, `wide` .025em, `wider` .05em, `widest` .1em                                                                         |
| Leading      | `tight` 1.25, `snug` 1.375, `normal` 1.5, `relaxed` 1.625, `loose` 2                                                                                               |
| Radius       | `xs` 2px, `sm` 4px, `md` 6px, `lg` 8px, `xl` 12px, `2xl` 16px, `3xl` 24px, `4xl` 32px                                                                              |
| Shadow       | `2xs`, `xs`, `sm`, `md`, `lg`, `xl`, `2xl`                                                                                                                         |
| Inset shadow | `2xs`, `xs`, `sm`                                                                                                                                                  |
| Drop shadow  | `xs`, `sm`, `md`, `lg`, `xl`, `2xl`                                                                                                                                |
| Text shadow  | `2xs`, `xs`, `sm`, `md`, `lg`                                                                                                                                      |
| Blur         | `xs` 4px, `sm` 8px, `md` 12px, `lg` 16px, `xl` 24px, `2xl` 40px, `3xl` 64px                                                                                        |
| Perspective  | `dramatic` 100px, `near` 300px, `normal` 500px, `midrange` 800px, `distant` 1200px                                                                                 |
| Ease         | `in`, `out`, `in-out`                                                                                                                                              |
| Animate      | `spin`, `ping`, `pulse`, `bounce`                                                                                                                                  |

Font sizes carry a paired default line height (`--text-xl--line-height`).
Override per-utility with a slash: `text-sm/6`, `text-xl/[1.4]`.

Width and max-width both accept the container scale (`w-md`, `max-w-3xl`) as
well as the spacing scale (`w-64`), fractions (`w-1/2`), and viewport units
(`w-dvw`, `h-dvh`, `h-lh`). `size-*` sets width and height together.

## Color palette

26 palettes, 11 shades each (50, 100–900 by hundreds, 950), plus `black` and
`white`. Values are oklch.

`red` `orange` `amber` `yellow` `lime` `green` `emerald` `teal` `cyan` `sky`
`blue` `indigo` `violet` `purple` `fuchsia` `pink` `rose` `slate` `gray` `zinc`
`neutral` `stone` `mauve` `olive` `mist` `taupe`

The last four are easy to miss — `mauve`, `olive`, `mist`, and `taupe` are
first-class palettes with the full 11 shades, useful when `gray` and `stone`
feel too neutral.

Opacity is a slash modifier on any color utility: `bg-sky-500/10`,
`text-black/75`, `bg-pink-500/[71.37%]`, `bg-cyan-400/(--my-alpha)`.

In CSS, reference colors as `var(--color-blue-500)`. To adjust alpha there, use
`--alpha(var(--color-gray-950) / 10%)`, which compiles to `color-mix()`.

## Customizing the theme

```css
@import 'tailwindcss';

@theme {
	--color-mint-500: oklch(0.72 0.11 178); /* adds bg-mint-500, text-mint-500, … */
	--breakpoint-3xl: 120rem; /* adds 3xl:* */
	--breakpoint-sm: 30rem; /* overrides the default sm */
}
```

Reset a namespace with `initial` to drop the defaults:

```css
@theme {
	--color-*: initial; /* remove every default color */
	--color-lime-*: initial; /* remove just one palette */
	--breakpoint-2xl: initial; /* remove one breakpoint */
	--*: initial; /* start from nothing */
}
```

Keep breakpoint units consistent — mixing `rem` and `px` can sort the generated
media queries in an order that makes them override each other unexpectedly.

**Referencing another variable requires `inline`:**

```css
@theme inline {
	--font-sans: var(--font-inter);
}
```

Without `inline`, the variable resolves where it was _defined_ rather than where
it is used, so a value supplied deeper in the tree silently falls back.

That is also the pattern for themes driven by a data attribute:

```css
:root {
	--acme-canvas-color: oklch(0.967 0.003 264.542);
}
[data-theme='dark'] {
	--acme-canvas-color: oklch(0.21 0.034 264.665);
}

@theme inline {
	--color-canvas: var(--acme-canvas-color);
}
```

`@theme static` emits every variable even when unused. Keyframes for an
`--animate-*` variable go inside `@theme`. Sharing tokens across projects is
just a CSS file the projects both `@import`.

## Arbitrary values

| Form                                     | Use                                                   |
| ---------------------------------------- | ----------------------------------------------------- |
| `top-[117px]`                            | literal value                                         |
| `bg-(--brand)`                           | CSS variable, shorthand for `bg-[var(--brand)]`       |
| `[mask-type:luminance]`                  | arbitrary property, no matching utility               |
| `[--gutter:1rem]`                        | set a CSS variable, `lg:[--gutter:2rem]` to change it |
| `grid-cols-[24rem_2.5rem_minmax(0,1fr)]` | underscore stands in for a space                      |
| `bg-[url('/what_a_rush.png')]`           | underscores preserved where a space is invalid        |
| `text-(length:--my-var)`                 | type hint resolving an ambiguous namespace            |

`text-[22px]` infers font-size and `text-[#bada55]` infers color, but a variable
gives Tailwind nothing to infer from — hence hints like `length:` and `color:`.
Available hints match CSS data types: `color`, `length`, `angle`, `image`,
`percentage`, `ratio`, `url`, `family-name`, and more.

Theme variables compose inside `calc()`:
`max-h-[calc(100dvh-(--spacing(6)))]`, `rounded-[calc(var(--radius-xl)-1px)]`.

Prefer an inline style when the value comes from a database or API, or when the
expression is long enough to hurt readability. A useful hybrid is setting
variables inline and consuming them with utilities:

```jsx
<button style={{ "--bg": buttonColor }} className="bg-(--bg) hover:bg-(--bg-hover)">
```

## Logical property utilities

Alongside the physical directions, there is a full logical set that respects
writing mode and text direction. Inline axis uses `s`/`e` (start/end), block
axis uses `bs`/`be`.

| Physical                      | Inline logical          | Block logical             |
| ----------------------------- | ----------------------- | ------------------------- |
| `pt` `pr` `pb` `pl`           | `ps` `pe`               | `pbs` `pbe`               |
| `mt` `mr` `mb` `ml`           | `ms` `me`               | `mbs` `mbe`               |
| `border-t` … `border-l`       | `border-s` `border-e`   | `border-bs` `border-be`   |
| `scroll-pt` …                 | `scroll-ps` `scroll-pe` | `scroll-pbs` `scroll-pbe` |
| `top` `right` `bottom` `left` | `inset-s` `inset-e`     | `inset-bs` `inset-be`     |

Bare `start-*` and `end-*` positioning utilities are deprecated — use
`inset-s-*` and `inset-e-*`. This does not affect `col-start-*`, `row-start-*`,
`items-start`, `justify-end`, or `text-start`, which are different utilities.

Logical sizing mirrors `w-*` and `h-*`: `inline-*` for inline size and `block-*`
for block size, each with `min-`/`max-` variants. They take the same scales —
`inline-64`, `inline-full`, `inline-md`, `block-screen`, `block-lh`.

`font-features-[<value>]` and `font-features-(<custom-property>)` set
`font-feature-settings` directly.

## Custom utilities

```css
@utility content-auto {
	content-visibility: auto;
}

@utility scrollbar-hidden {
	&::-webkit-scrollbar {
		display: none;
	}
}
```

Registered this way they land in the `utilities` layer and work with every
variant, including `hover:content-auto`.

**Functional utilities** take an argument through `--value()`:

```css
@utility tab-* {
	tab-size: --value(--tab-size-*); /* matches theme keys: tab-2, tab-github */
}

@utility tab-* {
	tab-size: --value(integer); /* bare values: tab-1, tab-76 */
}

@utility tab-* {
	tab-size: --value([integer]); /* arbitrary: tab-[76] */
}

@utility tab-* {
	tab-size: --value('inherit', 'initial'); /* literals: tab-inherit */
}
```

Bare types: `number`, `integer`, `ratio`, `percentage`. Arbitrary types add
`length`, `color`, `url`, `image`, `angle`, `position`, `family-name`, and more.

Combine forms as multiple declarations — any that fail to resolve are dropped —
or pass several arguments to resolve left to right:

```css
@utility tab-* {
	tab-size: --value(--tab-size-*, integer, [integer]);
}
```

`--default(n)` supplies a value for the bare class (`tab` alongside `tab-2`).
`--modifier()` handles the slash portion, as in `text-lg/6`. Fractions rely on
the `ratio` type, which tells Tailwind to treat value and modifier as one.
Negative variants are registered separately as `@utility -inset-*`.

For a component class you want utilities to override, `@layer components` is
still right — it just isn't a _utility_:

```css
@layer components {
	.card {
		background-color: var(--color-white);
		border-radius: var(--radius-lg);
		padding: --spacing(6);
		box-shadow: var(--shadow-xl);
	}
}
```

Base styles for bare elements go in `@layer base`.

## Source detection and safelisting

Tailwind scans every file except `.gitignore`d paths, `node_modules`, binaries,
CSS files, and lock files. It reads them as plain text and never parses them as
code, which is why interpolated class names never work.

The same indifference to context cuts the other way: Tailwind cannot tell an
application component from a markdown table listing class names. Documentation
inside the repo — READMEs, Storybook MDX, design-system notes, changelogs, agent
instruction files — contributes every class name it mentions to the production
bundle. A few dense reference files can add a hundred-plus unused rules and tens
of kilobytes. Symptom: a bundle far larger than the application's real class
usage explains, full of utilities no page requests.

```
python3 scripts/check_tailwind_v4.py --docs-audit README.md docs/*.md
```

reports utility-looking tokens per file, highest first. Exclude whatever is not
application source:

```css
@import 'tailwindcss' source('../src'); /* set the scan root */
@source '../node_modules/@acme/ui-lib'; /* add an ignored path */
@source not '../src/legacy'; /* skip a directory */
@import 'tailwindcss' source(none); /* register everything manually */
```

Force generation of classes that never appear in source — for example ones
assembled at runtime on the server:

```css
@source inline('underline');
@source inline('{hover:,focus:,}underline');
@source inline('{hover:,}bg-red-{50,{100..900..100},950}');
@source not inline('bg-red-{50,{100..900..100},950}');
```

The argument is brace-expanded, so ranges and variant sets expand in one line.
This replaces the v3 `safelist` config option.
