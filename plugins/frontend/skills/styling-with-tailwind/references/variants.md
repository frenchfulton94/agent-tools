# Variants Reference

Contents:

- [How variants compose](#how-variants-compose)
- [Parent, sibling, and descendant state](#parent-sibling-and-descendant-state)
- [Negation](#negation)
- [Child selectors](#child-selectors)
- [Container queries](#container-queries)
- [Arbitrary and custom variants](#arbitrary-and-custom-variants)
- [Full variant table](#full-variant-table)

## How variants compose

A variant is a prefix that makes a utility conditional. A single utility never
carries both states — `bg-white dark:bg-gray-800` is two classes, one per mode.

Stack them left to right, matching CSS reading order:

```html
<button class="dark:md:hover:bg-fuchsia-600">Save</button>
```

Compiles to `@media (prefers-color-scheme: dark) and (width >= 48rem) { &:hover }`.

Breakpoints are mobile-first: `sm:` means "at 40rem and up", never "on small
screens". Style mobile with unprefixed utilities, then layer overrides.

To target a range, stack a breakpoint with a `max-*` variant: `md:max-xl:flex`
applies between 48rem and 80rem. `md:max-lg:flex` targets only the `md` band.

For one-off breakpoints, `min-[320px]:` and `max-[600px]:` take arbitrary values.

## Parent, sibling, and descendant state

**`group-*`** — mark an ancestor `group`, then style descendants from its state:

```html
<a href="#" class="group rounded-lg p-8">
	<h3 class="text-gray-900 group-hover:text-white">New project</h3>
</a>
```

Works with every pseudo-class variant: `group-focus`, `group-active`,
`group-odd`, `group-aria-[sort=ascending]`.

Nested groups need names — `group/item` on the ancestor, `group-hover/item:` on
the target. Names need no configuration.

**`peer-*`** — mark a _previous_ sibling `peer`, then style later siblings:

```html
<input type="email" class="peer" />
<p class="invisible peer-invalid:visible">Please provide a valid email.</p>
```

CSS's sibling combinator only looks forward, so a `peer` cannot be marked after
the element it styles. Named peers work like named groups: `peer/draft`,
`peer-checked/draft:`.

**`in-*`** — like `group-*` without marking the parent. Responds to _any_
ancestor's state, so use `group` when you need to pin down which one:

```html
<div tabindex="0">
	<div class="opacity-50 in-focus:opacity-100">...</div>
</div>
```

**`has-*`** — style an element from its descendants' state or content:
`has-checked:bg-indigo-50`, `has-[img]:p-0`, `has-[:focus]:ring-2`. Combine with
the markers above for `group-has-[a]:block` and `peer-has-checked:hidden`.

## Negation

`not-*` inverts a condition, and composes with other variants:

```html
<button class="bg-indigo-600 hover:not-focus:bg-indigo-700">…</button>
```

Also works on feature queries and media variants: `not-supports-[display:grid]:flex`,
`not-forced-colors:appearance-none`.

## Child selectors

`*` targets direct children, `**` targets all descendants. Use them for markup
you don't control:

```html
<ul class="*:rounded-full *:border *:px-2 *:py-0.5">
	<li>Sales</li>
</ul>
```

Children cannot override a style handed down this way — the child rules are
generated later with the same specificity, so `<li class="bg-red-50">` loses to
the parent's `*:bg-sky-50`. Put the utility on the child instead when you control it.

`**` shines when narrowed by another variant:
`**:data-avatar:size-12` styles every descendant carrying `data-avatar`.

## Container queries

Mark a container, then size children against it rather than the viewport:

```html
<div class="@container">
	<div class="flex flex-col @md:flex-row">…</div>
</div>
```

Container variants are mobile-first like breakpoints, and support the same
patterns: `@max-md:` below a size, `@sm:@max-md:` for a range, `@min-[475px]:`
for arbitrary values.

Name containers to reach past the nearest one: `@container/main` paired with
`@sm/main:flex-col`.

Container query length units work as arbitrary values: `w-[50cqw]`. Units that
need the block axis (`cqb`, `cqh`) require `@container-size` instead of
`@container`.

Sizes run `@3xs` (16rem) through `@7xl` (80rem) — see the table below. Add more
with `--container-*` theme variables.

## Arbitrary and custom variants

Write a selector inline in square brackets. `&` marks the element:

```html
<li class="[&.is-dragging]:cursor-grabbing">…</li>
<div class="[&_p]:mt-4">…</div>
<!-- underscore = space -->
<div class="[@supports(display:grid)]:grid">…</div>
```

Register one you reuse:

```css
@custom-variant theme-midnight (&:where([data-theme="midnight"] *));
```

Multi-rule variants nest, with `@slot` marking where the utility lands:

```css
@custom-variant any-hover {
	@media (any-hover: hover) {
		&:hover {
			@slot;
		}
	}
}
```

This is also how dark mode switches from the OS preference to a class or
attribute you control:

```css
@custom-variant dark (&:where(.dark, .dark *));
@custom-variant dark (&:where([data-theme=dark], [data-theme=dark] *));
```

`data-*` and `aria-*` accept bare attribute names (`data-active:border-purple-500`)
or explicit values (`data-[size=large]:p-8`). Shortcuts for common values are
worth registering: `@custom-variant data-checked (&[data-ui~="checked"]);`

Inside custom CSS, apply a variant with `@variant`:

```css
.my-element {
	background: white;
	@variant dark {
		background: black;
	}
}
```

## Full variant table

Every built-in variant.

| Variant                 | CSS                                              |
| ----------------------- | ------------------------------------------------ |
| `hover`                 | `@media (hover: hover) { &:hover }`              |
| `focus`                 | `&:focus`                                        |
| `focus-within`          | `&:focus-within`                                 |
| `focus-visible`         | `&:focus-visible`                                |
| `active`                | `&:active`                                       |
| `visited`               | `&:visited`                                      |
| `target`                | `&:target`                                       |
| `*`                     | `:is(& > *)`                                     |
| `**`                    | `:is(& *)`                                       |
| `inert`                 | `&:is([inert], [inert] *)`                       |
| `first`                 | `&:first-child`                                  |
| `last`                  | `&:last-child`                                   |
| `only`                  | `&:only-child`                                   |
| `odd`                   | `&:nth-child(odd)`                               |
| `even`                  | `&:nth-child(even)`                              |
| `first-of-type`         | `&:first-of-type`                                |
| `last-of-type`          | `&:last-of-type`                                 |
| `only-of-type`          | `&:only-of-type`                                 |
| `empty`                 | `&:empty`                                        |
| `disabled`              | `&:disabled`                                     |
| `enabled`               | `&:enabled`                                      |
| `checked`               | `&:checked`                                      |
| `indeterminate`         | `&:indeterminate`                                |
| `default`               | `&:default`                                      |
| `optional`              | `&:optional`                                     |
| `required`              | `&:required`                                     |
| `valid`                 | `&:valid`                                        |
| `invalid`               | `&:invalid`                                      |
| `user-valid`            | `&:user-valid`                                   |
| `user-invalid`          | `&:user-invalid`                                 |
| `in-range`              | `&:in-range`                                     |
| `out-of-range`          | `&:out-of-range`                                 |
| `placeholder-shown`     | `&:placeholder-shown`                            |
| `details-content`       | `&:details-content`                              |
| `autofill`              | `&:autofill`                                     |
| `read-only`             | `&:read-only`                                    |
| `before`                | `&::before`                                      |
| `after`                 | `&::after`                                       |
| `first-letter`          | `&::first-letter`                                |
| `first-line`            | `&::first-line`                                  |
| `marker`                | `&::marker, & *::marker`                         |
| `selection`             | `&::selection`                                   |
| `file`                  | `&::file-selector-button`                        |
| `backdrop`              | `&::backdrop`                                    |
| `placeholder`           | `&::placeholder`                                 |
| `sm`                    | `@media (width >= 40rem)`                        |
| `md`                    | `@media (width >= 48rem)`                        |
| `lg`                    | `@media (width >= 64rem)`                        |
| `xl`                    | `@media (width >= 80rem)`                        |
| `2xl`                   | `@media (width >= 96rem)`                        |
| `max-sm`                | `@media (width < 40rem)`                         |
| `max-md`                | `@media (width < 48rem)`                         |
| `max-lg`                | `@media (width < 64rem)`                         |
| `max-xl`                | `@media (width < 80rem)`                         |
| `max-2xl`               | `@media (width < 96rem)`                         |
| `@3xs`                  | `@container (width >= 16rem)`                    |
| `@2xs`                  | `@container (width >= 18rem)`                    |
| `@xs`                   | `@container (width >= 20rem)`                    |
| `@sm`                   | `@container (width >= 24rem)`                    |
| `@md`                   | `@container (width >= 28rem)`                    |
| `@lg`                   | `@container (width >= 32rem)`                    |
| `@xl`                   | `@container (width >= 36rem)`                    |
| `@2xl`                  | `@container (width >= 42rem)`                    |
| `@3xl`                  | `@container (width >= 48rem)`                    |
| `@4xl`                  | `@container (width >= 56rem)`                    |
| `@5xl`                  | `@container (width >= 64rem)`                    |
| `@6xl`                  | `@container (width >= 72rem)`                    |
| `@7xl`                  | `@container (width >= 80rem)`                    |
| `@max-3xs` … `@max-7xl` | `@container (width < …)` for each size above     |
| `dark`                  | `@media (prefers-color-scheme: dark)`            |
| `motion-safe`           | `@media (prefers-reduced-motion: no-preference)` |
| `motion-reduce`         | `@media (prefers-reduced-motion: reduce)`        |
| `contrast-more`         | `@media (prefers-contrast: more)`                |
| `contrast-less`         | `@media (prefers-contrast: less)`                |
| `forced-colors`         | `@media (forced-colors: active)`                 |
| `inverted-colors`       | `@media (inverted-colors: inverted)`             |
| `pointer-fine`          | `@media (pointer: fine)`                         |
| `pointer-coarse`        | `@media (pointer: coarse)`                       |
| `pointer-none`          | `@media (pointer: none)`                         |
| `any-pointer-fine`      | `@media (any-pointer: fine)`                     |
| `any-pointer-coarse`    | `@media (any-pointer: coarse)`                   |
| `any-pointer-none`      | `@media (any-pointer: none)`                     |
| `portrait`              | `@media (orientation: portrait)`                 |
| `landscape`             | `@media (orientation: landscape)`                |
| `noscript`              | `@media (scripting: none)`                       |
| `print`                 | `@media print`                                   |
| `supports-[…]`          | `@supports (…)`                                  |
| `aria-busy`             | `&[aria-busy="true"]`                            |
| `aria-checked`          | `&[aria-checked="true"]`                         |
| `aria-disabled`         | `&[aria-disabled="true"]`                        |
| `aria-expanded`         | `&[aria-expanded="true"]`                        |
| `aria-hidden`           | `&[aria-hidden="true"]`                          |
| `aria-pressed`          | `&[aria-pressed="true"]`                         |
| `aria-readonly`         | `&[aria-readonly="true"]`                        |
| `aria-required`         | `&[aria-required="true"]`                        |
| `aria-selected`         | `&[aria-selected="true"]`                        |
| `rtl`                   | `&:where(:dir(rtl), [dir="rtl"], [dir="rtl"] *)` |
| `ltr`                   | `&:where(:dir(ltr), [dir="ltr"], [dir="ltr"] *)` |
| `open`                  | `&:is([open], :popover-open, :open)`             |
| `starting`              | `@starting-style`                                |

`nth-*`, `nth-last-*`, `nth-of-type-*`, and `nth-last-of-type-*` take any number
(`nth-3:underline`) or an arbitrary expression (`nth-[2n+1_of_li]`).

`before` and `after` add `content: ""` automatically. Both `marker` and
`selection` are inheritable — set them on a parent rather than repeating.
