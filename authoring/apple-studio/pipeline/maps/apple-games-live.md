# Live endpoint map: apple-games

Targets: the `apple-games` reference files, covering game input, audio, haptics, Game
Center, saving, threading, and the Apple silicon pages.

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

One seed per line under `## Seeds`: `- <bound> <dest> <url>`. The `dest` column also
carries the Xcode CPU, memory, and release pages (`apple-performance`, `app-release`),
because they are reached from the same crawl and later tasks route them to those skills.

- `recursive`: expand every article and `collectionGroup` page that shares the seed's
  first two path segments, compared case-insensitively.
- `depth1`: expand the seed once. The linked articles and collection pages are in the
  corpus, and their own links are not.
- `page`: the seed alone.

A `symbol` page is excluded unless its role is `collectionGroup`. A seed is always kept.

## Finding 8 additions

Touch Controller, GameSave, Background Assets, the two Apple Silicon porting articles,
the tile-based rendering article, the notarization and hardened-runtime articles, and the
Game technologies overview came from the Game technologies page
(`/documentation/TechnologyOverviews/games-technologies`). Paths use the spelling that
page uses. Touch Controller and GameSave are not linked from that page; their framework
roots are `/documentation/touchcontroller` and `/documentation/gamesave`.

## Probe status

50 survey seeds probed on 2026-10-18, all 200 (`survey/seed-probe.tsv` under the phase
record). The Finding 8 additions were probed the same day and are all 200.

## Seeds

<!-- Game frameworks (recursive) -->
- recursive apple-games https://developer.apple.com/documentation/gamecontroller.md
- recursive apple-games https://developer.apple.com/documentation/touchcontroller.md
- recursive apple-games https://developer.apple.com/documentation/gamekit.md
- recursive apple-games https://developer.apple.com/documentation/phase.md
- recursive apple-games https://developer.apple.com/documentation/avfaudio.md
- recursive apple-games https://developer.apple.com/documentation/audiotoolbox.md
- recursive apple-games https://developer.apple.com/documentation/corehaptics.md
- recursive apple-games https://developer.apple.com/documentation/appkit.md
- recursive apple-games https://developer.apple.com/documentation/dispatch.md
- recursive apple-games https://developer.apple.com/documentation/os/workgroups.md
- recursive apple-games https://developer.apple.com/documentation/network.md
- recursive apple-games https://developer.apple.com/documentation/modelio.md
- recursive apple-games https://developer.apple.com/documentation/compression.md
- recursive apple-games https://developer.apple.com/documentation/uniformtypeidentifiers.md
- recursive apple-games https://developer.apple.com/documentation/accelerate.md
- recursive apple-games https://developer.apple.com/documentation/gamesave.md

<!-- Design, overview, and Apple silicon pages (depth1) -->
- depth1 apple-games https://developer.apple.com/design/human-interface-guidelines/designing-for-games.md
- depth1 apple-games https://developer.apple.com/documentation/TechnologyOverviews/games-technologies.md
- depth1 apple-games https://developer.apple.com/documentation/BackgroundAssets.md
- depth1 apple-games https://developer.apple.com/documentation/Apple-Silicon/tuning-your-code-s-performance-for-apple-silicon.md
- depth1 apple-games https://developer.apple.com/documentation/Apple-Silicon/addressing-architectural-differences-in-your-macos-code.md

<!-- Xcode CPU, hitch, memory, and logging pages (depth1) -->
- depth1 apple-performance https://developer.apple.com/documentation/xcode/addressing-cpu-bottlenecks.md
- depth1 apple-performance https://developer.apple.com/documentation/xcode/analyzing-cpu-usage-with-processor-trace.md
- depth1 apple-performance https://developer.apple.com/documentation/xcode/analyzing-cpu-profiles-with-call-tree-views.md
- depth1 apple-performance https://developer.apple.com/documentation/xcode/diagnosing-performance-issues-early.md
- depth1 apple-performance https://developer.apple.com/documentation/xcode/improving-your-app-s-performance.md
- depth1 apple-performance https://developer.apple.com/documentation/xcode/understanding-hitches-in-your-app.md
- depth1 apple-performance https://developer.apple.com/documentation/xcode/reducing-your-app-s-memory-use.md
- depth1 apple-performance https://developer.apple.com/documentation/os/logging.md

<!-- Distribution and notarization pages (depth1) -->
- depth1 app-release https://developer.apple.com/documentation/xcode/distribution.md
- depth1 app-release https://developer.apple.com/documentation/xcode/command-line-tools.md
- depth1 app-release https://developer.apple.com/documentation/Security/notarizing-macos-software-before-distribution.md
- depth1 app-release https://developer.apple.com/documentation/Security/hardened-runtime.md

## Missing

None as of the 2026-10-18 probe.
