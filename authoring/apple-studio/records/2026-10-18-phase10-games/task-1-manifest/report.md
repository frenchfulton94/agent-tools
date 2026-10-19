# Task 1 report: seed maps and the corpus manifest

The controller wrote this file from the implementer's returned reports. The
harness refused the implementer's Write of report files (SDD ledger ruling
P10). The figures below were recomputed from the committed `manifest.tsv`.

## Command

    python3 authoring/apple-studio/pipeline/crawl_corpus.py \
      authoring/apple-studio/pipeline/maps/apple-metal-live.md \
      authoring/apple-studio/pipeline/maps/apple-games-live.md \
      --out authoring/apple-studio/records/2026-10-18-phase10-games/task-1-manifest/manifest.tsv \
      --cache authoring/apple-studio/pipeline/tmp/corpus

Exit 0. Every seed returned 200. A second run with `--offline` produced a
byte-identical manifest (`cmp` exit 0).

## Seeds

59 seeds: 26 in `apple-metal-live.md` and 33 in `apple-games-live.md`. They
are the 50 survey seeds (`survey/seed-probe.tsv`) plus the 9 Finding 8
additions. Touch Controller is the only recursive Finding 8 addition, and
GameSave is depth1, per spec Deliverable 4. No seed is `MISSING:`.

## Rows per destination

| dest | rows | words |
|---|---:|---:|
| apple-games | 832 | 467,025 |
| apple-metal | 276 | 261,911 |
| apple-performance | 39 | 46,972 |
| app-release | 29 | 32,835 |
| **total** | **1,176** | **808,743** |

## Comparison with the survey (909 pages, 622,615 words)

The manifest is 29% larger in pages and 30% larger in words. That is more
than 15%, for these reasons:

1. **`doc://` links.** The survey crawler followed only `](/documentation/…)`
   links. The manifest crawler also follows `](doc://…)` and `<doc://…>`
   autolinks (ruling P12), because the spec defines a depth1 seed as "the
   page itself and the pages it links". Accelerate's collection pages link
   their articles only through autolinks. So Accelerate grew from 1 row to
   **265 rows (183,448 words)**. Against this crawler's first run (891 rows,
   before the `doc://` change), that accounts for 264 of the 285 added rows,
   and the other 21 come from depth1 seeds.
2. **Case-variant duplicates.** The survey counted `/documentation/Xcode/x`
   and `/documentation/xcode/x` as two pages, and the manifest folds them
   into one. In the first run, Metal had 173 rows against the survey's 203,
   and Xcode 110 against 128. The final manifest has 174 and 117.
   This offsets part of item 1.
3. **Finding 8 additions.** The survey did not count them. They add about
   21,000 words.

The first run, before the `doc://` change, produced 891 rows and 601,748
words: 2.0% and 3.4% below the survey.

## Rows with http ≠ 200

Four rows. All four are real 404s from the server, and none is a seed.
Ruling P11 applies: each gets a `no-unfetchable:404:deferred-<n>` ledger row
in the reading task, not a crawler change.

| path | seed | dest |
|---|---|---|
| `/documentation/kernel/1387446-sysctlbyname` | Apple-Silicon/addressing-architectural-differences-in-your-macos-code | apple-games |
| `/documentation/kernel/1462446-mach_absolute_time` | Apple-Silicon/addressing-architectural-differences-in-your-macos-code | apple-games |
| `/documentation/metal/compute_passes/creating_threads_and_threadgroups` | metal | apple-metal |
| `/documentation/os/reading-unix-manual-pages` | Security/notarizing-macos-software-before-distribution | app-release |

The Metal row is a broken figure link in Apple's own
`Metal/creating-threads-and-threadgroups` article. That article is itself a
manifest row.

## Attribution rule

Each row's `dest` comes from one seed:

1. A seed keeps its own row.
2. Otherwise, a recursive seed that reached the page wins when its scope
   (the first two path segments) contains the page.
3. Otherwise, the shallowest seed that reached the page wins. At equal
   depth, a seed whose own scope matches the page's scope wins, then the
   earliest seed (ruling P16).

`dest` is a seed attribution, not a per-page classification.

## Fetch behaviour

- Pages whose last path segment contains `(` (function, method, and
  initializer symbols) are extracted but never fetched (ruling P15).
- A real 404 or 410 is cached as `<key>.md.gone`, so an offline rerun
  reproduces the row.
- Any other failure exits 2 and writes no manifest: a transport error, any
  other non-200, or an `--offline` cache miss.

Crawling took about 7,100 symbol-page fetches to learn page types. The cache,
`pipeline/tmp/corpus/`, is gitignored.
