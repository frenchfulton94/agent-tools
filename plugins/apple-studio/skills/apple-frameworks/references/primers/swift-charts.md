> verified: 2026-09 against https://developer.apple.com/documentation/charts, https://developer.apple.com/tutorials/data/documentation/charts.json, https://developer.apple.com/tutorials/data/documentation/charts/visualizing-your-app-s-data.json, https://developer.apple.com/tutorials/data/documentation/charts/chart.json, https://developer.apple.com/tutorials/data/documentation/charts/creating-a-chart-using-swift-charts.json, https://developer.apple.com/tutorials/data/documentation/charts/chartcontent/accessibilitylabel(_:)-28985.json, https://developer.apple.com/tutorials/data/documentation/swiftui/view/accessibilitychartdescriptor(_:).json, https://developer.apple.com/tutorials/data/documentation/charts/creating-a-data-visualization-dashboard-with-swift-charts.json
> sources: live docs

# Swift Charts

## What it is / when to reach for it

Swift Charts is Apple's first-party SwiftUI framework for turning data into
charts declaratively. Per the docs: it "provides marks, scales, axes, and
legends as building blocks to create a broad range of data-driven charts with
minimal code," and it explicitly bakes in "localization, accessibility
features, and customization through chart modifiers and animations." A chart
is composed the same way a SwiftUI view tree is — `Chart { BarMark(...) }` —
using `ForEach` over your data to emit one mark per data point, the same
mental model as building a `List`.

Reach for it as the default for any in-app chart on Apple platforms: bar,
line, area, point/scatter, rule (threshold lines), sector (pie/donut), and as
of newer OS versions, 3D charts (`Chart3D`) and vectorized plots for large
collections. It integrates natively with SwiftUI state, animation, and the
accessibility tree, and requires no third-party dependency or license.

Prefer a **third-party charting library** (DGCharts/Charts, Swift
Charts alternatives, or web-based charting embedded in a `WKWebView`) only
when you need a chart type or interaction Swift Charts genuinely doesn't
support yet, or when your deployment target is below Swift Charts' floor and
back-deployment isn't viable. Don't reach for one just because Swift Charts
requires learning its mark/scale vocabulary — that vocabulary is also what
gets you free accessibility and Dynamic Type support.

Prefer **hand-rolled Canvas/Shape-based drawing** only for genuinely custom,
non-standard visualizations that don't map onto marks/scales/axes at all
(bespoke game-like visualizations, non-Cartesian custom art) — and be aware
that going this route means you also own accessibility for that view
yourself (see Privacy/Pitfalls below), since none of Swift Charts' automatic
VoiceOver support comes along for free.

## Architecture integration

A `Chart` is a plain SwiftUI `View`; it composes into any existing view
hierarchy like any other view and participates normally in SwiftUI's
diffing/animation system. `ChartContent` (built via `ChartContentBuilder`,
the mark-side analog of `ViewBuilder`) is the protocol individual marks
conform to, so custom composite chart content can be built the same way you'd
build a composite `View`.

For testability and separation of concerns: feed `Chart` view models or
pre-shaped `[Plottable]`-conforming value arrays rather than raw
model/persistence objects — keep the mapping from domain data to
chart-ready data (bucketing, date binning via `DateBins`/`NumberBins`,
sorting, series labeling) in a plain Swift type you can unit test without
instantiating SwiftUI at all. The chart view itself should stay a thin
rendering layer: given the same shaped data, its correctness is a snapshot/UI
concern, not a logic concern.

For genuinely large or streaming datasets, the docs' 2024-era vectorized
plots (`LinePlot`, `PointPlot`, `AreaPlot`, etc., operating over a
`RandomAccessCollection` instead of one mark per `ForEach` iteration) are
built for this — they're a different API shape than the mark-per-row model,
so if a chart's data volume is large or animates continuously, the vectorized
plot types are worth reaching for at design time, not retrofitted later.

## Privacy, entitlements, review

Swift Charts itself requires no Info.plist key, no capability/entitlement,
and triggers no runtime permission prompt — it's a pure rendering framework
over data you already have in memory. There is nothing App Review gates
specifically for using Swift Charts.

The privacy/review surface that *does* matter is whatever the charted data
represents: if you're charting HealthKit, location, or other
protection-worthy data, the entitlement and usage-description requirements
come from that source framework, not from Charts. The one Charts-adjacent
obligation worth flagging here is accessibility, not privacy: Apple documents
`accessibilityChartDescriptor(_:)` and per-mark `accessibilityLabel`/
`accessibilityValue` modifiers as the supported way to expose chart data to
VoiceOver — treat this as a near-mandatory implementation step for any
chart conveying information not available elsewhere on screen, since a chart
with no accessible description is effectively invisible to VoiceOver users
and a plausible App Review accessibility rejection.

## Availability

Per the framework's current platform table: iOS 16.0, iPadOS 16.0, Mac
Catalyst 16.0, macOS 13.0, tvOS 16.0, watchOS 9.0, visionOS 1.0. These are
hard floors for the core `Chart`/mark types (`BarMark`, `LineMark`,
`PointMark`, etc.) — there's no back-deployment path for a SwiftUI-only
framework like this.

Newer additions sit on higher floors and were confirmed independently while
fetching child pages: `Chart3D`/3D surface plots and the vectorized plot
family (`LinePlot`, `PointPlot`, `AreaPlot`, `RectanglePlot`, `RulePlot`,
`BarPlot`, `SectorPlot`) require iOS 18.0 / iPadOS 18.0 / macOS 15.0 / Mac
Catalyst 18.0 / visionOS 2.0. If a deployment target sits between 16 and 18,
the vectorized/3D APIs are off the table even though the base framework is
available — check the specific mark/plot type's own availability, not just
the framework page's headline floor.

## Classic pitfalls

- **One mark per `ForEach` iteration at real scale.** The idiomatic
  "beginner" pattern — a `ForEach` over your array emitting one `LineMark`/
  `PointMark` per element — is fine for dozens to low hundreds of points but
  degrades with large or frequently-updating datasets. The docs' own
  dashboard sample reaches for vectorized plot types specifically because
  they "enable efficient plotting [of] an entire `RandomAccessCollection`"
  and "enabl[e] a smooth animation in the chart as the underlying data
  changes" — treat dataset size as a decision point up front, not something
  to profile-and-fix after the chart ships janky.
- **Shipping a chart with no accessible description and assuming Swift
  Charts "just handles it."** The framework exposes chart data to VoiceOver,
  but nontrivial charts (multi-series, annotated, custom-styled) often need
  explicit `accessibilityLabel`/`accessibilityValue` on chart content, or a
  full `AXChartDescriptor` via `accessibilityChartDescriptor(_:)`, to produce
  a description that actually communicates the data — the default summary
  can be too thin for anything beyond a simple single-series chart.
- **Using `accessibilityChartDescriptor(_:)` only for hand-rolled charts and
  forgetting it also exists (and helps) for Swift Charts views.** It's a
  general SwiftUI modifier (available since iOS 15, predating Swift Charts)
  applicable to *any* view representing a chart, including a plain `Image`
  of a chart — it's the right fallback if you ever do end up hand-rolling a
  visualization with Canvas/Shape and need it to be VoiceOver-accessible.
- **Assuming customization always means dropping into Canvas.** Axes, scales,
  symbols, legends, and interaction are all first-class, composable
  modifiers/marks (`AxisMarks`, `chartForegroundStyleScale`, `chartXScale`,
  annotations, scroll behaviors) — reaching for a custom Canvas overlay for
  something achievable with a chart modifier adds maintenance burden and
  usually loses the free accessibility/Dynamic Type support that comes with
  staying inside the mark system.
- **Forgetting `Chart3D` and vectorized plots are availability-gated
  separately from the base framework.** Adopting a Swift Charts sample or
  tutorial that uses `Chart3D`, `SurfacePlot`, or any `*Plot` vectorized type
  silently raises your effective deployment floor to iOS/macOS/visionOS
  2024-era versions even if the rest of the app targets the iOS 16 / macOS
  13 floor — verify per-symbol availability before committing to a design
  that needs them.

## Current docs

- https://developer.apple.com/documentation/charts
- https://developer.apple.com/documentation/charts/chart
- https://developer.apple.com/documentation/charts/creating-a-chart-using-swift-charts
- https://developer.apple.com/documentation/charts/visualizing-your-app-s-data
- https://developer.apple.com/documentation/charts/creating-a-data-visualization-dashboard-with-swift-charts
- https://developer.apple.com/documentation/charts/customizing-axes-in-swift-charts
- https://developer.apple.com/documentation/charts/chartcontent
- https://developer.apple.com/documentation/swiftui/view/accessibilitychartdescriptor(_:)
- https://developer.apple.com/documentation/accessibility/axchartdescriptor
