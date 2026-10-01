# Task 1 report: docc.py renders inline markup, deprecation, and HIG pages

## What was implemented

`authoring/apple-studio/pipeline/docc.py`:

1. Replaced `BASE_DOC`/`BASE_TUT` and `fetch(path, tutorial=False)` with a
   `BASES` dict keyed `"doc"`/`"tutorial"`/`"hig"`, a new `url_for(path, kind)`
   helper, and `fetch(path, kind="doc")`. The `"hig"` base points at
   `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/`.
2. Added three `render()` branches before the `paragraph` branch:
   - `emphasis`/`strong`/`newTerm` — these carry `inlineContent`, which the
     generic key-walk at the bottom of `render()` skips (it explicitly
     excludes `inlineContent` from that walk), so their text was silently
     dropped. Now wrapped in `*`/`**` and recursed into.
   - `aside` — renders as a blockquote-style `> **Note:** ...` line.
   - `table` — renders rows as a pipe-delimited line.
3. Split the per-page printing out of `main()` into
   `print_page(d, url, children=False)`, unchanged in what it prints for
   existing flags, plus a new block right after the PLATFORMS line: it
   collects `f"{name} {deprecatedAt}"` for every platform carrying a
   `deprecatedAt`, and if any exist, renders `deprecationSummary` and prints
   `DEPRECATED: <platforms> — <summary>`.
4. `main()` now parses `--children`, `--tutorial`, and `--hig <slug>`
   (the latter consumes its own value), picks `kind` (`"hig"` > `"tutorial"`
   > `"doc"`), calls `fetch(path, kind)`, then `print_page(d, url, children)`.
5. Replaced the bare `main()` call at module scope with
   `if __name__ == "__main__": main()`, which is what let the test import
   `docc.py` as a module without triggering a live fetch.
6. Added `python3 docc.py --hig designing-for-iphone-duo` to the Usage block.

Created `authoring/apple-studio/pipeline/fixtures/docc/inline-markup.json`
(fixture, our own words) and `authoring/apple-studio/pipeline/test_docc.py`
(offline, stdlib-only test), both exactly as specified in the task brief.

## TDD evidence

**RED** — before implementation, run:

```
$ python3 authoring/apple-studio/pipeline/test_docc.py
```

Output:

```
Traceback (most recent call last):
  File ".../authoring/apple-studio/pipeline/test_docc.py", line 22, in <module>
    docc.print_page(page, "fixture://inline-markup")
    ^^^^^^^^^^^^^^^
AttributeError: module 'docc' has no attribute 'print_page'
```

Matches the brief's expectation exactly: `main()` ran on import with empty
`sys.argv[1:]` (the loop over `args` did nothing, so nothing printed), then
the test failed because `print_page` didn't exist yet (pre-refactor, all
printing lived inline in `main`).

**GREEN** — after implementation:

```
$ python3 authoring/apple-studio/pipeline/test_docc.py
PASS test_docc.py
```

Also spot-checked `url_for` for all three kinds against the old and new
constants to confirm doc/tutorial URLs are byte-identical to before the
refactor, and grepped the repo for other callers of `docc.fetch`/`docc.main`/
`BASE_DOC`/`BASE_TUT` — none exist, so the signature change is safe.

## Live-check results (Step 6)

Saved to `live-check.log` (grep output only, per the brief — no full rendered
Apple page text committed):

- `docc.py --hig designing-for-iphone-duo | grep -c "reserved regions"` → `5`
  (≥ 1, as expected; confirms the `--hig` flag reaches a real HIG page).
- `docc.py technologyoverviews/preparing-your-app-for-iphone-duo | grep -o "represent an [^,]*,"`
  → `represent an *arrangement view*,` (exact match to the brief's expected
  string — confirms `newTerm` no longer renders as a gap).
- `docc.py "swiftui/view/accentcolor(_:)" | grep DEPRECATED` →
  `DEPRECATED: iOS 27.2, iPadOS 27.2, Mac Catalyst 27.2, macOS 27.2, tvOS 27.2, visionOS 27.2, watchOS 27.2 — Use the asset catalog's accent color or \`tint(_:)\` instead.`
  (starts with `DEPRECATED: iOS 27.2`, as expected).

## Files changed

- Modified: `authoring/apple-studio/pipeline/docc.py`
- Created: `authoring/apple-studio/pipeline/fixtures/docc/inline-markup.json`
- Created: `authoring/apple-studio/pipeline/test_docc.py`
- Created: `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-1-docc/live-check.log`
- Created: `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-1-docc/task-1-report.md` (this file)

## Self-review

- **Completeness against brief**: all 7 steps done — fixture, failing test,
  RED capture, implementation (all 6 sub-points), GREEN capture, live check,
  and this report ahead of commit.
- **Style**: kept the file's existing compactness (single-line `if`/`elif`
  bodies where the original did the same, e.g. `render`'s dict dispatch);
  comments added at the two Phase-9 additions (`BASES["hig"]` and the
  deprecation block) explain WHY, matching the file's existing comment
  style (see the module docstring's "Two endpoint traps" and "CAUTION"
  paragraphs, and the inline `# Phase 9` style now used for the render
  branches).
- **Tests verify real behavior**: `test_docc.py` asserts on rendered text
  content (defined terms, list/aside/reference text, the DEPRECATED line,
  the deprecation summary text) rather than just "doesn't crash", and
  explicitly checks for the regression string pattern ("an , which") that
  motivated the fix. It also pins `url_for` for the new `--hig` kind.
- **CLI behavior unchanged for existing flags**: `print_page` reproduces
  `main`'s prior print sequence verbatim for `--children`/`--tutorial`
  (title/SOURCE/PLATFORMS/ABSTRACT/body/topic sections/see-also), with only
  the new DEPRECATED line inserted after PLATFORMS when applicable. Verified
  `url_for("path", "doc")` and `url_for("path", "tutorial")` produce the same
  URLs the old `BASE_DOC`/`BASE_TUT` constants did.
- **Output pristine**: `live-check.log` contains only the three grep lines,
  no full Apple page text.

## Concerns

- None blocking. One judgment call: `main()`'s `--hig <slug>` parsing treats
  the flag as taking exactly one path argument (consistent with the brief's
  `--hig designing-for-iphone-duo` usage and Task 4/8's stated single-slug
  use); if `--hig` were combined with other positional paths in one
  invocation, only the HIG slug is fetched — this matches the brief's
  description of the flag ("CLI flag `--hig <slug>`", singular) and every
  example invocation in the brief and live-check step, but it is a narrower
  contract than `--tutorial`/plain paths, which still accept multiple
  positional arguments in one run.
