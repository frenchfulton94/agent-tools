# Live endpoint map: apple-metal

Targets: the `apple-metal` reference files for game rendering on Metal 4, built from
the Metal, MetalFX, MetalKit, and Metal Performance Shaders pages and the Xcode Metal
tooling pages.

This map is a **seed list, not an exhaustive registry**, per the CONVENTIONS.md
"Distillation maps" rule. `pipeline/crawl_corpus.py` expands each seed into the corpus
manifest, and the manifest, not this map, is the list of pages a reader must read in full.
The reference files' own header citations are the citation record. Expected-but-missing
pages are recorded under `## Missing` as `MISSING:`.

## Endpoint pattern

Phase 10 reads the Markdown route, not the DocC JSON route. Each page is one fetch:

```text
https://developer.apple.com/documentation/<path>.md
https://developer.apple.com/design/human-interface-guidelines/<path>.md
```

The first lines of a body are an HTML comment holding a JSON object. Its `documentType`
is `symbol` or `article`, and its `role` is `Class`, `collectionGroup`, `article`,
`sampleCode`, and so on. Topic links appear as `[Title](/documentation/Path)`.

## Seed format and bounds

One seed per line under `## Seeds`: `- <bound> <dest> <url>`.

- `recursive`: expand every article and `collectionGroup` page that shares the seed's
  first two path segments, compared case-insensitively.
- `depth1`: expand the seed once. The linked articles and collection pages are in the
  corpus, and their own links are not.
- `page`: the seed alone.

A `symbol` page is excluded unless its role is `collectionGroup`. A seed is always kept.

## Probe status

50 survey seeds probed on 2026-10-18, all 200 (`survey/seed-probe.tsv` under the phase
record). The Finding 8 additions were probed the same day and are all 200.

## Seeds

<!-- Metal frameworks (recursive) -->
- recursive apple-metal https://developer.apple.com/documentation/metal.md
- recursive apple-metal https://developer.apple.com/documentation/metalfx.md
- recursive apple-metal https://developer.apple.com/documentation/metalkit.md
- recursive apple-metal https://developer.apple.com/documentation/quartzcore.md
- recursive apple-metal https://developer.apple.com/documentation/metalperformanceshaders.md
- recursive apple-metal https://developer.apple.com/documentation/metalperformanceshadersgraph.md
- recursive apple-metal https://developer.apple.com/documentation/apple-silicon/porting-your-metal-code-to-apple-silicon.md

<!-- Xcode Metal tooling and build system, plus tile-based rendering (depth1) -->
- depth1 apple-metal https://developer.apple.com/documentation/xcode/metal-debugger.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/capturing-a-metal-workload-programmatically.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/optimizing-gpu-performance.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/investigating-gpu-issues-with-ai-agents.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/debugging-with-interactive-command-line-tools.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/metal-developer-workflows.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/analyzing-resource-dependencies.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/analyzing-memory-usage.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/debugging-the-shaders-within-a-draw-command-or-compute-dispatch.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/monitoring-your-metal-apps-graphics-performance.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-metal-app.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/analyzing-apple-gpu-performance-using-a-visual-timeline.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/analyzing-apple-gpu-performance-using-performance-heatmaps-a17-m3.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/analyzing-apple-gpu-performance-using-shader-cost-graph-a17-m3.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/validating-your-apps-metal-api-usage.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/validating-your-apps-metal-shader-usage.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/analyzing-the-memory-usage-of-your-metal-app.md
- depth1 apple-metal https://developer.apple.com/documentation/xcode/build-system.md
- depth1 apple-metal https://developer.apple.com/documentation/Metal/tailor-your-apps-for-apple-gpus-and-tile-based-deferred-rendering.md

## Missing

None as of the 2026-10-18 probe.
