---
name: bem-css
description: Write, refactor, and review CSS class names using the BEM (Block Element Modifier) methodology. Use this skill whenever the user is writing HTML/CSS and mentions BEM, or asks for maintainable/scalable class names, component-based CSS, or a naming convention — and also whenever you're generating a UI component's CSS and want the class names to be clean and reusable, even if the user didn't say "BEM" explicitly. Covers naming syntax (block__element--modifier), decomposing a UI into blocks/elements/modifiers, the core BEM rules (flat specificity, no element-of-element nesting, modifiers alongside their base class, mixes), and converting existing CSS to BEM.
---

# Writing CSS with BEM

BEM (Block, Element, Modifier) is a naming methodology for CSS classes. Its goal is CSS that is **modular** (a block's styles never leak into or depend on anything around it), **reusable** (blocks can be dropped in anywhere), and **structured** (a class name alone tells you what a rule does). It achieves this by giving every class a single, flat, predictable name instead of relying on nesting, tag selectors, or the cascade.

Use this skill when writing new component CSS, refactoring tangled CSS, or reviewing markup for BEM compliance.

## The three concepts

**Block** — a standalone, meaningful component that could be reused on its own. Think `menu`, `header`, `search-form`, `button`, `card`. If you could lift it out and drop it elsewhere and it would still make sense, it's a block.

**Element** — a part of a block with no standalone meaning; it only exists inside its block. Think the `__title` of a card, the `__item` of a menu, the `__input` of a search form. An element is meaningless outside its block.

**Modifier** — a flag that changes a block's or element's appearance, state, or behavior. A modifier is a variation, never a thing on its own. It comes in two forms:

- **Boolean** — the flag is either present or not: `--disabled`, `--highlighted`, `--checked`, `--fixed`.
- **Key–value** — a property set to a value, written `block--key-value`: `--size-big`, `--color-yellow`, `--state-success`. getbem states the rule as **`block--modifier-value` syntax**, so reach for the key–value form whenever a modifier represents one option out of several (sizes, colors, themes, states).

Because BEM styles everything by class, a block or element can be built with **any HTML tag** — `.button` works equally on a `<button>`, an `<a>`, or a `<div>`. The class carries the meaning, not the tag.

## Naming syntax

This is the exact convention. Follow it precisely — consistency is the whole point.

```
.block                     /* block */
.block__element            /* element: block + TWO underscores + element */
.block--modifier           /* modifier on a block: block + TWO hyphens + modifier */
.block__element--modifier  /* modifier on an element */
```

- Separator between block and element is **two underscores** (`__`).
- Separator before a modifier is **two hyphens** (`--`).
- Within any single name (block, element, or modifier), multiple words are joined with a **single hyphen** (kebab-case): `search-form`, `__nav-item`, `--is-loading`.

**Example — a button with state modifiers** (the canonical getbem example; note the key–value `--state-success` form and that the base `.button` class is always present):

```html
<button class="button">Normal button</button>
<button class="button button--state-success">Success button</button>
<button class="button button--state-danger">Danger button</button>
```

```css
.button {
	/* shared button styles: padding, border, font, etc. */
}
.button--state-success {
	/* only the success overrides */
}
.button--state-danger {
	/* only the danger overrides */
}
```

**Example — a search form** (shows elements and an element modifier):

```html
<form class="search-form">
	<div class="search-form__content">
		<input class="search-form__input" type="text" />
		<button class="search-form__button search-form__button--disabled">Search</button>
	</div>
</form>
```

```css
.search-form {
}
.search-form__content {
}
.search-form__input {
}
.search-form__button {
}
.search-form__button--disabled {
}
```

Notice the button carries **two** classes: `search-form__button` (the base) and `search-form__button--disabled` (the modifier). That's not optional — see the rules below.

## How to decompose a UI into BEM

When you're handed a component or a design, work top-down:

1. **Name the block.** What is this reusable thing? That name prefixes everything inside it. (`card`, `site-nav`, `pricing-table`.)
2. **Find the elements.** What are its meaningful parts? Each becomes `block__part`. A card might have `__image`, `__title`, `__body`, `__cta`.
3. **Find the modifiers.** What variations or states exist? Each becomes a `--modifier` on the block or element it varies. A card might be `card--featured`; its button might be `card__cta--disabled`.
4. **Ask "is this still part of the same block, or is it its own block?"** If a part is complex and reusable in its own right (e.g., the button inside a card is really just a `button` component), make it its own block rather than an element. Elements are for parts that only make sense here.

## Core rules

These are what make BEM actually work. Breaking them reintroduces the problems BEM exists to prevent.

### 1. Style with classes only — no tag or ID selectors

Every BEM rule targets a class. No `#id`, no `ul li`, no `.card h2`. This keeps **specificity flat** (every rule is a single class, so rules are easy to override and order-independent) and keeps blocks portable (a rule tied to a tag breaks the moment the markup changes).

```css
/* Bad — depends on tag/structure, specificity varies */
.card h2 {
}
ul.menu li {
}

/* Good — flat, explicit */
.card__title {
}
.menu__item {
}
```

### 2. Elements are named relative to the block, never to other elements

There is **no** `block__el1__el2`. Even when an element is nested inside another element in the DOM, its class is still `block__` + its own name. The block is the only prefix.

```html
<!-- Bad: element of an element -->
<nav class="nav">
	<ul class="nav__list">
		<li class="nav__list__item">...</li>
		<!-- WRONG -->
	</ul>
</nav>

<!-- Good: every element is prefixed by the block only -->
<nav class="nav">
	<ul class="nav__list">
		<li class="nav__item">...</li>
	</ul>
</nav>
```

This keeps names short and lets you rearrange the DOM without renaming everything.

### 3. A modifier never appears without its base class

A modifier only tweaks; it doesn't define the whole thing. Always keep the base class next to it so the shared styles still apply.

```html
<!-- Bad: modifier alone, base styles are lost -->
<button class="button--primary">Go</button>

<!-- Good: base + modifier -->
<button class="button button--primary">Go</button>
```

In CSS, write the base rule once and let modifiers layer on top:

```css
.button {
	/* shared button styles */
}
.button--primary {
	/* just the primary overrides */
}
.button--large {
	/* just the size overrides */
}
```

### 4. Keep modifier styles additive

A modifier rule should only contain the properties that _change_. Don't re-declare everything — that defeats reuse. `.button--primary` sets the color; `.button` still provides padding, font, border-radius.

### 5. Blocks don't set their own outer geometry

A block shouldn't hardcode its margins or position for one specific spot on the page, or it stops being reusable. Positioning a block within a layout is the parent's job — often via a **mix** (next rule).

## Mixes: putting more than one BEM entity on one node

You can place multiple BEM classes on a single element to combine behaviors. The most common use is letting a parent block position a child block without the child knowing about it: the node is simultaneously an **element of the outer block** and **a block of its own**.

```html
<header class="header">
	<!-- this node is BOTH header__search (positioned by header)
       AND search-form (a reusable block) -->
	<form class="header__search search-form">...</form>
</header>
```

```css
.header__search {
	margin-left: auto;
} /* placement only */
.search-form {
	/* the reusable component's own styles */
}
```

This is how BEM keeps blocks reusable: `search-form` never contains layout-specific margins; the `header__search` element supplies them.

## Converting existing CSS to BEM

When refactoring:

1. Identify the reusable component and give it a block name.
2. Replace descendant/tag selectors (`.card h2`, `.card > .btn`) with element classes (`.card__title`, `.card__btn`).
3. Replace state classes and variant selectors (`.card.active`, `.card.large`) with modifiers (`.card--active`, `.card--large`), and add the base class in the markup.
4. Remove ID selectors; convert to classes.
5. Flatten specificity — after conversion every selector should be a single class.
6. Move any layout-specific margins/positioning out of the block onto a mix element in the parent.

## Before you finish — checklist

- Every selector is a single class (no tags, no IDs, no descendant selectors).
- Element names are `block__element`, prefixed by the block only (no `__el1__el2`).
- Every modifier in the markup sits next to its base class (`class="block block--mod"`).
- Modifier rules contain only the properties that change.
- Multi-word names use single hyphens; blocks/elements use `__`; modifiers use `--`.
- No block hardcodes layout-specific outer margins/position; use a mix instead.
- Anything complex and independently reusable is its own block, not an element.

## Quick reference

| Thing                      | Syntax                       | Example                              |
| -------------------------- | ---------------------------- | ------------------------------------ |
| Block                      | `.block`                     | `.menu`                              |
| Element                    | `.block__element`            | `.menu__item`                        |
| Block modifier (boolean)   | `.block--modifier`           | `.menu--horizontal`                  |
| Block modifier (key–value) | `.block--key-value`          | `.button--state-success`             |
| Element modifier           | `.block__element--modifier`  | `.menu__item--active`                |
| Multi-word name            | kebab-case within a part     | `.search-form__submit-button`        |
| Mix                        | multiple classes on one node | `class="header__search search-form"` |
