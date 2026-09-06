---
name: layerchart
description: Build charts and data visualizations in Svelte/SvelteKit using the LayerChart library (v2 / "next"). Use this skill whenever the user wants any chart, graph, plot, sparkline, gauge, heatmap, treemap, sankey, map, or other data visualization in a Svelte component — bar, line, area, pie, scatter, radial, hierarchical, or geographic — even if they don't mention "LayerChart" by name. Also use it when debugging, styling, or extending existing LayerChart components. Always fetch the linked live docs before writing code; the library's API changes between versions and training knowledge is unreliable.
compatibility: Svelte 5 / SvelteKit project. Requires network access to next.layerchart.com to fetch live documentation.
---

# LayerChart (v2 / next)

LayerChart is a composable Svelte charting library built on D3. This skill targets **v2** (the `next` docs at https://next.layerchart.com), which uses **Svelte 5 runes and snippets**. v1 knowledge from training data (slot-based syntax, old state APIs) will produce broken code — that's why the single most important rule in this skill is:

## Rule 1: Fetch live docs before writing code

LayerChart v2 is actively evolving. Your memory of its props and patterns is likely stale or contaminated with v1. Before writing or modifying any LayerChart code, fetch the current docs for the components involved. Every docs page has an LLM-optimized plain-text version at the same URL with `/llms.txt` appended:

| What you need        | URL pattern                                                                       |
| -------------------- | --------------------------------------------------------------------------------- |
| Index of all pages   | `https://next.layerchart.com/llms.txt`                                            |
| A guide (concepts)   | `https://next.layerchart.com/docs/guides/<guide>/llms.txt`                        |
| A component's API    | `https://next.layerchart.com/docs/components/<Component>/llms.txt`                |
| Working example code | `https://next.layerchart.com/docs/components/<Component>/<example-slug>/llms.txt` |

Minimum fetches for a typical task: the component page for the chart type you're using, plus one or two example pages closest to the user's request. Example slugs are listed on each component page and in the index; `references/doc-map.md` in this skill has a curated map of guides, components, and high-value example slugs so you can route without pulling the full index every time.

Fetching an example that matches the request (e.g. `BarChart/stack-series` for a stacked bar chart) is usually worth more than the API reference alone — the examples are complete, current, and compile.

## Mental model (stable concepts)

These architectural ideas are durable even as individual props change:

- **Everything composes inside `<Chart>`.** `<Chart>` provides dimensions, scales, and contexts (tooltip, geo, transform). Visual content renders through ordered **snippets**: `belowContext` → `belowMarks` → `marks` → `aboveMarks` → `aboveContext`. Put your data marks (Spline, Bars, Area, Points…) in `marks`; annotations/reference lines under the data in `belowMarks`; overlays and labels in `aboveMarks`. All snippets receive `{ context }` (the full ChartState).
- **Simplified charts are the default starting point.** `LineChart`, `BarChart`, `AreaChart`, `ScatterChart`, `PieChart`, and `ArcChart` are pre-configured `<Chart>` wrappers: they pick the right mark, tooltip mode, axes, grid, and highlight for the chart type. Reach for them first; drop to raw `<Chart>` only when you're combining multiple mark types, need full render-order control, or building non-standard/hierarchical/geo/radial visualizations.
- **Escape hatches, not rewrites.** Simplified charts accept the same snippets as `<Chart>`. Overriding just `marks` (or `legend`, `tooltip`, …) keeps every other built-in feature intact. Prefer this over rebuilding with raw `<Chart>`.
- **Feature flags come in three forms.** Built-in features (`axis`, `grid`, `rule`, `highlight`, `points`, `labels`, `legend`, `tooltipContext`, `brush`) each accept a boolean (toggle), a props object (customize), or a snippet (replace). The `props` object additionally lets you tweak internally-rendered components (e.g. `props={{ xAxis: { tickCount: 5 }, spline: { curve: curveCatmullRom } }}`) — especially useful with simplified charts.
- **Three render layers.** Marks render to `Svg` (default, styleable with CSS), `Canvas` (large datasets, performance), or `Html`. The `Layer` component wraps the choice.
- **Series drive multi-data charts.** Pass `series={[{ key, color, ... }]}` and iterate `context.series.visibleSeries` in a custom `marks` snippet. Stacking/grouping is controlled by `seriesLayout`.
- **Annotations are first-class.** Simplified charts take an `annotations` prop (`[{ type: 'line' | 'point' | 'range', ... }]`) for reference lines, thresholds, and callouts — check it before dropping to composition just to draw one dashed line.

## Workflow

1. **Confirm the environment.** Svelte 5 + SvelteKit project with `layerchart` installed (`bun add layerchart`). If the project is on LayerChart v1 (check `package.json`), stop and discuss migration first — fetch `https://next.layerchart.com/docs/guides/migrations/v1-to-v2/llms.txt`.
2. **Pick the approach.** Standard chart type → simplified chart. Mixed marks / custom render order / hierarchy / geo → `<Chart>` composition. When unsure, start simplified; the escape hatches usually suffice.
3. **Fetch docs** per Rule 1: the component page + the closest example(s).
4. **Write the component**, modeling structure on the fetched example, not on memory.
5. **Verify it compiles** (see Verification below) before presenting it. LayerChart bugs are usually type/prop mismatches that `svelte-check` catches immediately.

## Setup and styling (vanilla CSS)

LayerChart works without Tailwind. Out of the box it uses `currentColor` as the primary mark color; theme it globally via CSS variables on `.lc-root-container`:

```css
/* app.css or global stylesheet */
.lc-root-container {
	--color-primary: #3b82f6; /* default mark color */
	--color-surface-100: #ffffff; /* lightest surface (background) */
	--color-surface-200: #f3f4f6;
	--color-surface-300: #d1d5db;
	--color-surface-content: #111827; /* text/content color */
}
```

For dark mode, redefine the same variables under your dark-mode selector. Individual marks accept explicit `color`/`fill`/`stroke` props or `class` for one-off styling. Don't import the framework theme CSS files (`layerchart/shadcn-svelte.css` etc.) in a vanilla CSS project — define the variables yourself as above.

## Gotchas

Concrete corrections to mistakes you will otherwise make:

- **Svelte 5 snippets, not slots.** v2 uses `{#snippet marks({ context })}...{/snippet}`. Any `<svelte:fragment slot="...">` or `let:` directive means you're writing v1 code — stop and re-fetch the docs.
- **Stacked series + array `y` = zero-height bars.** When stacking against shared chart data on raw `<Chart>`, each series needs its own `value` accessor (or relies on the `s.key` fallback). Setting `y={['q1','q2']}` alongside `seriesLayout="stack"` shadows that fallback and feeds the stack a whole tuple per series, producing zero-height bars. `<BarChart>` avoids this internally — one more reason to prefer simplified charts for standard stacks.
- **Tooltip mode matters per chart type.** Simplified charts set it for you (`quadtree-x` for lines, `band` for bars). If composing with raw `<Chart>`, set `tooltipContext={{ mode: ... }}` to match — the wrong mode makes hover feel broken, not just different.
- **`children` replaces everything.** Providing the `children` snippet on `<Chart>` discards default axes, grid, rule, and tooltip. Use `marks` unless you deliberately want a blank canvas.
- **Chart needs a height.** Simplified charts accept a `height` prop directly (`height={300}` — the pattern used throughout the docs). Without it (or a parent element with an explicit height for raw `<Chart>`), the chart renders zero-height and appears blank.
- **Dates on the x-axis need real `Date` objects** (or an explicit time scale). ISO strings silently produce a band/ordinal axis with ugly ticks.

When you correct a new mistake during a task, consider whether it belongs in this list.

## Verification

Before presenting a component, run a compile check in the project:

```bash
bun run check          # if the project defines it (svelte-check)
# or directly:
bunx svelte-check --workspace . --fail-on-warnings false
```

Fix all errors originating from your component. Type errors on LayerChart imports/props almost always mean the API differs from what you assumed — go back to the fetched docs (or fetch the component page if you skipped it) rather than guessing at prop names.

## Where to look next

`references/doc-map.md` — curated map of all guides, component categories, and high-value example slugs, with the URL patterns to fetch them. Read it when routing a task to the right docs, especially for less common needs: brushing/selection, pan-zoom, animation, geo projections, SSR image rendering, or bundle-size optimization.
