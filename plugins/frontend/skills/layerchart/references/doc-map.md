# LayerChart doc map

All URLs below serve LLM-optimized plain text. Fetch on demand — do not rely on memory of the library's API. If a URL 404s or the page you need isn't listed here, fetch the live index at `https://next.layerchart.com/llms.txt` (this file is a curated snapshot; the index is the source of truth).

Base: `https://next.layerchart.com`

## Guides — `/docs/guides/<slug>/llms.txt`

| Slug                        | When to read                                                                                                          |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `structure`                 | How `<Chart>` renders (snippets, default features, simplified charts vs composition). Read for any non-trivial chart. |
| `state`                     | ChartState, sub-states, accessing `context`                                                                           |
| `data`                      | Data shapes, accessors, performance patterns                                                                          |
| `series`                    | Multi-series, stacking, grouping, legend integration                                                                  |
| `scales`                    | Scale types, domains, ranges, overrides                                                                               |
| `layers`                    | SVG vs Canvas vs HTML rendering                                                                                       |
| `tooltip`                   | Tooltip modes and customization                                                                                       |
| `styles`                    | Styling and theming, dark mode                                                                                        |
| `animation`                 | Transitions, tweens, motion                                                                                           |
| `brush`                     | Selection/brushing                                                                                                    |
| `transform`                 | Pan and zoom                                                                                                          |
| `geo`                       | Maps and projections                                                                                                  |
| `primitives`                | Low-level building blocks                                                                                             |
| `bundle-size`               | Reducing bundle footprint                                                                                             |
| `ssr-images`                | Server-side rendering charts as PNG/JPEG                                                                              |
| `migrations/v1-to-v2`       | Upgrading from LayerChart v1                                                                                          |
| `migrations/state-refactor` | `@next` state refactor changes                                                                                        |

Getting started (install, CSS setup): `/docs/getting-started/llms.txt`

## Components — `/docs/components/<Component>/llms.txt`

**Simplified charts (start here):** `LineChart`, `BarChart`, `AreaChart`, `ScatterChart`, `PieChart`, `ArcChart`

**Chart core:** `Chart`, `Layer`, `Svg`, `Canvas`, `Html`, `Frame`, `Bounds`

**Common chrome:** `Axis`, `Grid`, `Rule`, `Legend`, `Labels`, `Tooltip`, `TooltipContext`, `Highlight`

**Marks:** `Area`, `Bars`, `Bar`, `Spline`, `Points`, `Pie`, `Arc`, `ArcLabel`, `Cell`, `Calendar`, `Month`, `Threshold`, `Trail`, `Link`, `Hull`, `BoxPlot`, `Violin`, `Contour`, `Density`, `Raster`, `Waffle`

**Annotations:** `AnnotationLine`, `AnnotationPoint`, `AnnotationRange`

**Primitives:** `Circle`, `Ellipse`, `Line`, `Rect`, `Polygon`, `Path`, `Text`, `Marker`, `Group`, `Point`, `Image`, `Vector`

**Layouts (hierarchy/graph/flow):** `Tree`, `Treemap`, `Pack`, `Partition`, `Sankey`, `Chord`, `Ribbon`, `Dagre`, `ForceSimulation`, `Dodge`

**Geo:** `GeoContext`, `GeoProjection`, `GeoPath`, `GeoPoint`, `GeoCircle`, `GeoSpline`, `GeoTile`, `TileImage`, `GeoRaster`, `Graticule`, `GeoLegend`, `GeoVisible`, `GeoEdgeFade`, `GeoClipPath`

**Interaction:** `BrushContext`, `TransformContext`, `Voronoi`

**Fills/effects/clipping:** `LinearGradient`, `RadialGradient`, `Pattern`, `Blur`, `ColorRamp`, `ClipPath`, `RectClipPath`, `CircleClipPath`, `ChartClipPath`, `MotionPath`

**Utilities** — `/docs/utils/<slug>/llms.txt`: `cls`, `download` (export PNG/SVG), `format` (number/date formatting), `pivot` (long↔wide reshaping), `stats` (boxplot/KDE), `string`

## Examples — `/docs/components/<Component>/<slug>/llms.txt`

Each component page lists all of its example slugs; fetch the component page when the ones below don't match. High-value slugs for common requests:

| Request                         | Fetch                                                                           |
| ------------------------------- | ------------------------------------------------------------------------------- |
| Basic line/area/bar             | `LineChart/basic`, `AreaChart/basic`, `BarChart/vertical-default`               |
| Multi-series line + legend      | `LineChart/series`, `LineChart/legend`                                          |
| Stacked bars                    | `BarChart/stack-series` (also `stack-series-horizontal`, `series-diverging`)    |
| Grouped bars                    | `BarChart/group-series`                                                         |
| Horizontal bars                 | `BarChart/horizontal`                                                           |
| Stacked area                    | `AreaChart/series-stack` (+ `series-stack-legend`)                              |
| Custom tooltip                  | `<X>Chart/custom-tooltip` (exists for LineChart, AreaChart, BarChart)           |
| Click handlers                  | `BarChart/tooltip-click`, `LineChart/series-point-click`                        |
| Sparklines                      | `LineChart/sparkline`, `BarChart/sparkbar`                                      |
| Annotations (line/point/range)  | `<X>Chart/line-annotation`, `point-annotation(s)`, `range-annotation`           |
| Threshold coloring              | `LineChart/threshold`, `AreaChart/threshold`, `BarChart/color-threshold`        |
| Gradient fills                  | `AreaChart/gradient`, `BarChart/gradient`                                       |
| Brush / zoom                    | `<X>Chart/brush`, `<X>Chart/pan-zoom`, `LineChart/pan-zoom-with-overview`       |
| Donut / gauge                   | `PieChart` examples, `Arc/gauge`, `ArcChart/basic`                              |
| Histogram                       | `BarChart/histogram-vertical`                                                   |
| Radar                           | `LineChart/radar`                                                               |
| Heatmap / calendar              | `Cell/color-scale`, `Calendar/basic`, `Month/basic`                             |
| Animated on mount               | `Area/tween-on-mount`, `Bars/vertical-stagger-tween-on-mount`, `LineChart/draw` |
| Choropleth / maps               | `GeoPath/choropleth`, `GeoPath/us-state`, `GeoPoint/us-airports`                |
| Large data / streaming          | `LineChart/large-series`, `LineChart/perf-streaming` (Canvas layer)             |
| Null/missing data gaps          | `LineChart/null-gaps`, `AreaChart/null-gaps`                                    |
| Custom composition on `<Chart>` | `<X>Chart/custom`, `Chart/compound-*` (dual axis etc.)                          |
