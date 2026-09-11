# Plan template

Every plan follows this structure. The executor may be a less capable model with
no context and no taste, so the plan has to contain everything, exactly — no
references to "the audit above" or "the easing we discussed".

````markdown
# NNN — <short imperative title>

- **Status**: TODO
- **Commit**: <output of `git rev-parse --short HEAD` when this plan was written>
- **Severity**: HIGH | MEDIUM | LOW
- **Category**: <audit category>
- **Estimated scope**: <n files, rough size>

## Problem

What is wrong, where, and why it matters to how the product feels. Cite every
location as `src/lib/components/Dropdown.svelte:14`, with the code verbatim:

```svelte
<!-- src/lib/components/Dropdown.svelte:14 — current -->
{#if open}
	<div class="menu" transition:scale>…</div>
{/if}
```

## Target

The exact end state, every value spelled out — curves, durations, spring
configs, media queries. Never "use a nicer easing":

```svelte
<!-- target -->
{#if open}
	<div
		class="menu"
		transition:scale={{
			start: prefersReducedMotion.current ? 1 : 0.95,
			duration: 200,
			easing: quintOut
		}}
	>…</div>
{/if}

<style>
	.menu { transform-origin: var(--bits-dropdown-menu-content-transform-origin); }
</style>
```

## Repo conventions to follow

How this codebase already does it, with one exemplar to imitate — token names,
file placement, prop patterns:

- Easing tokens live in `src/app.css` under `@theme`, e.g.
  `--ease-out: cubic-bezier(0.23, 1, 0.32, 1);`
- <exemplar file:line that already does this correctly>

## Steps

1. <One concrete edit per step: file, what changes, resulting code.>
2. …

## Boundaries

- Do not touch <files or components out of scope>.
- Do not change markup or structure — motion properties only, unless a step says
  otherwise.
- Do not add dependencies.
- If a step does not match the code you find (drift since the commit stamp),
  stop and report rather than improvising.

## Verification

- **Mechanical**: <exact commands and expected outcome — `bun run check`, `bun test`>.
- **Feel check**: run the app, trigger <interaction>, and confirm:
  - <observable check, e.g. "the menu scales out of its trigger, not from centre">
  - <e.g. "spamming the toggle never restarts the animation from zero">
  - In DevTools, set animation playback to 10% and confirm <detail>.
  - In the Rendering panel, force `prefers-reduced-motion: reduce` and confirm
    movement is gone while opacity feedback remains — in the running app, not by
    reading CSS, since a media query does not reach a Svelte transition.
- **Done when**: <machine- or eye-checkable completion criteria>.
````

## Notes for the plan author

- One plan per finding, unless two share every file and the same fix pattern —
  the same easing token swap across components may merge into one.
- Pull every value from `audit.md`; never approximate from memory. That includes
  Svelte's own defaults, which are the thing most often recalled wrong.
- The feel check is not optional. Motion can be mechanically correct and still
  feel wrong; give the executor, or the human reviewing its diff, concrete
  things to watch for in slow motion.
- Where a plan changes reduced-motion handling, the verification step has to
  exercise the running app. A plan that only asserts a media query is present
  can pass while the animation it guards still plays at full strength.
- Afterwards, create or update `plans/README.md` with a table of plans (number,
  title, severity, status), the execution order, and any dependencies.
