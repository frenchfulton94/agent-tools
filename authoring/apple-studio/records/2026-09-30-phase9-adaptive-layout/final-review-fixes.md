# Phase 9 final review fixes — report

Branch `phase9-adaptive-layout`, from HEAD `73447ef`. One wave, 13 findings
(4 Important, 9 Minor), from the final whole-branch review. The version stays
at 0.10.0. Neither skill description changed (`apple-design/SKILL.md:3` and
`app-release/SKILL.md:3` have no diff). `~/Projects/StudioFixture` was not
touched (`git status --porcelain` is empty).

Abbreviations: `AL` = `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md`,
`HP` = `.../apple-design/references/hig-patterns.md`, `DEF` =
`authoring/apple-studio/docs/deferred.md`, `SPEC` =
`authoring/apple-studio/docs/specs/2026-09-30-phase9-adaptive-layout-design.md`.
All line numbers are in the committed files.

## Findings

### Important

1. **Arrangement-view nesting contradiction — FIXED.** `AL:102` keeps
   `NavigationStack` and `TabView` outside an arrangement view and cites the
   HIG. `AL:104` is new. It states that Apple's two pages differ on
   `NavigationSplitView`, and it cites both pages. The HIG places navigation
   split views around an arrangement view. The developer overview says to
   avoid an arrangement view inside one. The paragraph follows the developer
   overview, because the split view already adapts to the fold
   (`AL:26`). The wording is "avoid", the word that the source uses. The
   old double "never" is gone. Both pages were re-fetched this wave (see
   Pages fetched). The spec's Deliverables §1 item 4 (`SPEC:143-145`) still
   says "Never inside". It is the original design input, so it was left as
   written.
2. **`toolbarVerticalEdge` nil wording — FIXED.** `AL:187` now reads "`nil`
   on devices without a vertical bar, and in contexts that never use one".
   This matches the live `toolbarVerticalEdge` page.
3. **LiveBadgeOverlay moved too far — FIXED.** The snippet at `AL:58-87` is
   rewritten. The badge rests at the top trailing corner. A
   `CGRect` gives its resting spot, from a size that `onGeometryChange`
   measures. The active occlusions that intersect that spot are found, and
   the badge moves down to the lowest `frame.maxY` among them. The
   `isActive` check stays. The unexplained 80/160 constants are gone. The
   one constant left, `inset`, is named and explained. The prose at `AL:89`
   now describes this. It states that the frame already includes the
   margins. The source is the `frame` comment in the SDK header
   `UIViewReservedRegion.h`, paraphrased here. It states that the test uses the
   resting spot, so the badge does not move back and forth. It marks the
   right-to-left sentence "documented, not runtime-checked". Compiled under
   `ios 27.1`: PASS.
4. **Destructive-action confirmation not covered by a reference — FIXED
   without a description edit.** `HP:69-98` adds a sourced paragraph to
   § Modality. The rules: when to confirm (from HIG Alerts, with a pointer
   to the existing rule in § Feedback and Loading). An action sheet over an
   alert, with `confirmationDialog`. `role: .destructive` and the default
   dismiss action, and the iOS popover in a regular size class. The HIG's
   alert-only rule for the destructive style. Button titles, and the iOS
   rule that dialog buttons show only a `Text` label. One snippet,
   `DeleteProjectButton` (`HP:77-98`), compiles for macOS (no directive in
   the file): PASS. The HP header (`HP:1`) gained the fetched URLs under
   "re-checked 2026-10 ... (Phase 9 final review)". Two record sentences
   were corrected. They now say that no reference covered the topic at the
   time, and that this wave added it: `DEF:773-778` (item 13, Fix round 1)
   and `SPEC:614-618` (the Task 10 addendum).

   **One deviation from the prescribed text, from the docs.** The HIG's two
   pages differ on the destructive style. Action sheets: use it for
   destructive choices. Alerts: use it only for a destructive action that
   people did not deliberately choose (the Empty Trash example). The
   paragraph states both, each scoped to its own control.

### Minor

5. **Spec pointers — FIXED, re-verified after all deferred.md edits.** §1:
   `SPEC:344` now points at `docs/deferred.md:126-135`. The finding
   estimated `~:126-136`, but line 136 is item 2, so the range ends at 135.
   §6: `SPEC:478` now points at `docs/deferred.md:843-853` (item 17). The
   new item 18 starts at `DEF:855`.
6. **Records wording — FIXED.**
   - `SPEC:587`: "Task 9 baseline" became "Task 6 baseline".
   - `SPEC:611-613`: "Task 9's baseline" and "Task 9's single post-edit
     run" became Task 6. The addendum had the same error as item 13, so it
     was fixed too.
   - `DEF:770-772`: "Task 9's single baseline run" and "Task 9's post-edit
     run" became Task 6.
   - `SPEC:572-573`: "App Store Connect exclusion" became "App Store
     screenshots exclusion".
   - `SPEC:365-367`: the docs corrected the first two claims in Task 4, and
     the Task 8 probe corrected the third (R5).
   - `SPEC:543-549`: the Carried-forward bullet for item 13 is marked
     superseded by the Task 10 addendum.
   - Row prefixes in item 13's Task 10 section: `nofire-1` became
     `ad-nofire-1` at `DEF:811` and `DEF:816`. The Task 6 paragraph
     (`DEF:684-729`) keeps that task's unprefixed row names.
7. **xcode-loop Screenshots line — FIXED.**
   `plugins/apple-studio/skills/xcode-loop/SKILL.md:19` appends the iPhone
   Duo `--display` note and the § 9 pointer.
8. **platform-idioms restatement — FIXED.** `.../platform-idioms.md:49`
   drops "build fluid layout, not fixed breakpoints" and the split-screen
   sentence. It keeps the iPad-window fact, the pointer to `AL` § What
   layout reads, and the window-controls inset fact.
9. **Screenshot specification link for all devices — FIXED without a
   description edit.**
   `plugins/apple-studio/skills/app-release/references/app-store-submission.md:101`
   now links the specifications page in the general sentence, for every
   device. The Duo sentence refers to "the same page". A WebFetch this wave
   confirmed that the page lists iPhone, iPad, Mac, Apple TV, Vision Pro,
   and Apple Watch sizes, plus Duo with its upload note. The URL was
   already in the file's `verified:` header.
10. **New deferred item — FIXED.** `DEF:855-875` is item 18. It covers two
    gaps: `docc.py` drops `termList` nodes, and its `table` branch leaks
    blank lines. The trigger is the next distillation that hits either
    node type. Before this item, the `termList` gap had only one standing
    record, `pipeline/maps/apple-design-duo-live.md:76-83`, beside a note
    in `task-4-reference/task-4-report.md`. The table leak had no record.
    This wave reproduced the leak on four tables: the Alerts page has two
    (the keyboard-shortcut table and the change log), the Action sheets
    page has one (button styles), and the Duo page has one (change log).
    The item paraphrases the dropped `termList` lead-in and does not quote
    it. `SPEC:556-557` lists item 18 under Carried forward.
11. **Citations — FIXED.**
    - `AL:4`: the note now covers R1–R7 and names `results.md`.
    - `[R5]` is at `AL:41`. `[R6]` and `[R7]` are at `AL:181`.
    - The citations at `AL:47`, `:123`, `:129`, `:141`, and `:181` now sit
      inside their sentences. These are the old `:47`, `:111`, `:117`,
      `:129`, and `:168`.
    - Right-to-left claims carry "documented, not runtime-checked" at
      `AL:51` and `AL:89`, and also at `AL:123`. The probe did not test
      right-to-left (deferred item 17), and the vertical-bar right-to-left
      sentence there had the same gap.
    - `SPEC:443-447` now records the header-note change. It no longer says
      that the note names only R1–R4.
    - Spec pointers into `AL` moved with the edits: `:194` → `:209`, and
      `:174-192` → `:189-207` (`SPEC:382-383`). The pointers at `:41` and
      `:51` did not move.
12. **Asymmetry guidance — FIXED.** `AL:185` opens § Custom views with the
    HIG's guidance: the vertical bar makes content space asymmetric, so use
    safe areas so that no bar covers content. This includes a bar on the
    opposite edge in Split View multitasking. Cited to HIG: Designing for
    iPhone Duo § Vertical controls.
13. **MessageDetail comment — FIXED.** `AL:174` reads "Takes effect when a
    TabView shares the vertical bar with this toolbar." The source is the
    `toolbarVerticalCompressionBehavior(_:)` page, which describes bars
    hosted together, with a `TabView` example.

## Pages fetched (DocC JSON via `pipeline/docc.py`, output in the session scratchpad, 2026-10-01)

- `--hig alerts`, `--hig action-sheets`, `--hig designing-for-iphone-duo`
- `technologyoverviews/preparing-your-app-for-iphone-duo`
- `swiftui/view/confirmationdialog(_:ispresented:titlevisibility:actions:)`,
  `swiftui/view/confirmationdialog(_:ispresented:titlevisibility:actions:message:)`
- `swiftui/buttonrole`, `swiftui/buttonrole/destructive`,
  `swiftui/button/init(_:role:action:)`, `--children swiftui/button`
- `swiftui/reservedregion`,
  `swiftui/geometryproxy/reservedregions(kind:options:layoutdirectionbehavior:)`
- `swiftui/environmentvalues/toolbarverticaledge`,
  `swiftui/view/toolbarverticalcompressionbehavior(_:)`,
  `swiftui/view/ongeometrychange(for:of:action:)`
- MISSING: `--hig changes` and `--hig change-log` both returned HTTP 404.
  The table leak was reproduced on the change-log tables of other pages
  instead.
- Not DocC: the App Store Connect screenshot specifications page, by
  WebFetch.
- SDK: `ReservedRegion` in the iPhoneOS 27.1 SDK (Xcode 27.1, build
  27A9269) `SwiftUICore.swiftinterface` (`arm64e`). The frame and margins
  comments come from `UIViewReservedRegion.h` in the same SDK.

## Snippet compile results

`DEVELOPER_DIR="/Applications/Xcode 27-1-beta.app/Contents/Developer" python3 authoring/apple-studio/pipeline/typecheck_snippets.py plugins/apple-studio/skills/apple-design/references/*.md`
reports **`TOTAL: 9/9 snippets typecheck clean`**:

- `accessibility.md`: 2/2.
- `adaptive-layout.md`: 4/4 under `ios 27.1`. This includes the rewritten
  `LiveBadgeOverlay` and the commented `MessageDetail`.
- `animation-taste.md`: 1/1.
- `hig-foundations.md`: 1/1.
- `hig-patterns.md`: 1/1. `DeleteProjectButton` compiles for macOS, against
  the macOS 27.0 SDK of the 27.1 beta Xcode.

`xcode-select` was not changed.

## Vale

Config: `.claude/skills/controlled-engineering-english/scripts/vale/.vale.ini`.
Only warnings on changed lines were judged, and the "amend" warning is
waived.

- **Fixed this wave:** four long sentences in new text, at `AL:51`,
  `AL:104`, `HP:71`, and item 18 in `DEF`.
- **Accepted, path tokens:** `AL:4`, `:47`, `:123`, `:129`, and `:141`
  (G-S1). Each sentence is under 25 words without the
  `records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md`
  citation. Finding 11 requires that citation inside the sentence.
- **Pre-existing sentences, not changed:**
  - `AL:1` and `HP:1`: the `verified:` header URL lists.
  - `platform-idioms.md:49`, columns 3 and 322: the first and last
    sentences of the bullet. The new pointer sentence is clean.
  - `app-store-submission.md:101`, column 46: the bullet's opening
    sentence. The new sentences are clean.
- `DEF` and `SPEC`: no warning on a changed line. `SPEC:346`'s "amended"
  is waived.

## Gates (repository root)

| Gate | Result |
|---|---|
| `bun test` | 198 pass, 0 fail, 429 `expect()` calls |
| `bun run audit` | 0 errors, 55 warnings — the same count as at `73447ef` (checked with the edits stashed) |
| `bun run audit --since main` | 0 errors, 55 warnings, no unbumped plugin reported |
| `claude plugin validate . --strict` | `✔ Validation passed` |
| `python3 authoring/apple-studio/pipeline/test_docc.py` | `PASS test_docc.py` |
| `bash authoring/apple-studio/pipeline/test_typecheck_snippets.sh` | all cases ok (`invented.md -> 1`, `bad-directive.md -> 2`, `too-new.md -> 2`, `uikit.md -> 0`) |

The version is still `"version": "0.10.0"` in
`plugins/apple-studio/.claude-plugin/plugin.json`.

## Pointers re-verified by opening the target

- `SPEC:344` → `DEF:126-135`, item 1's Phase 9 measurement and decision.
- `SPEC:478` → `DEF:843-853`, item 17.
- `SPEC:382-383` → `AL:209`, the floating-controls rule, and `AL:189-207`,
  the `FloatingPaletteHost` block from fence to fence.
- `SPEC:446` → `AL:4`, the header note.
- `SPEC:376` and `SPEC:390` → `AL:51` and `AL:41`. Both are unchanged and
  still correct.
- `DEF:855-875` (item 18) → `pipeline/maps/apple-design-duo-live.md:76-83`,
  the Known rendering gaps heading and bullet.
- `SPEC:428` → `DEF:478-486` (item 7) and `SPEC:507` → `DEF:684-730`
  (item 13, Task 6). Both are unchanged and still on target.
