# Task 7 report: Compile gate against the iOS 27.1 SDK

## SDK evidence (Step 1)

`sdk.log`:
```
/Applications/Xcode.app/Contents/Developer
Xcode 27.1
Build version 27A9269
27.1
```

Per Ruling 6: `xcode-select -p` correctly still points at the default
Xcode.app (untouched, as required — no sudo, no system-default change). The
DEVELOPER_DIR-scoped commands, which are the ones that matter for the stop
condition, report Xcode 27.1 / build 27A9269 / iPhoneOS SDK 27.1. SDK present
and at or above the required version — proceeded.

All subsequent SDK-touching commands (Step 2, Step 4, and my extra
SwiftUICore checks) were run with
`DEVELOPER_DIR="/Applications/Xcode 27-1-beta.app/Contents/Developer"`
exported.

## Step 2: typecheck gate

`typecheck.log` tail: `TOTAL: 8/8 snippets typecheck clean`. As expected —
Task 4 already compiled this file 8/8 against 27.1 while writing it, so no
snippet fixes were needed.

## Step 4: name check — every MISSING symbol and its resolution

Raw run flagged 7 lines as MISSING:

```
MISSING ArrangementView
MISSING arrangementViewStyle
MISSING hig
MISSING toolbarVerticalEdge
MISSING VStack
MISSING xcode
MISSING ZStack
```

**Root cause found:** the Step 4 command as literally written only searches
`SwiftUI.framework`'s swiftinterface and `UIKit.framework`'s Headers/Modules.
In the iOS 27.1 SDK, SwiftUI's actual declarations (View, the stack types,
layout/environment modifiers, and the whole iPhone Duo surface —
`ArrangementView`, `ReservedRegion`, `toolbarVerticalEdge`, etc.) live in a
separate `SwiftUICore.framework` that `SwiftUI.framework` re-exports via
`@_exported import`. That framework isn't on the Step 4 script's search path,
so it produces false MISSING results for real, correctly-named, correctly-used
symbols. This explains why `typecheck_snippets.py` (Step 2) had no trouble —
it invokes the real Swift compiler against the SDK, which resolves
`@_exported import`s automatically, unlike a bare grep.

Resolutions (grepped `SwiftUICore.swiftmodule/arm64e-apple-ios.swiftinterface`
directly, word-boundary match, same method as Step 4):

| Symbol | Resolution |
|---|---|
| `ArrangementView` | Confirmed: `nonisolated public struct ArrangementView<Primary, Secondary> : SwiftUICore::View, ~Swift::Sendable where Primary : SwiftUICore::View, Secondary : SwiftUICore::View`. Matches the file's two-view description. No change needed. |
| `arrangementViewStyle` | Confirmed: `nonisolated public func arrangementViewStyle(_ style: some ArrangementViewStyle) -> some SwiftUICore::View`. Matches the `.arrangementViewStyle(.split.axes(.horizontal))` snippet, which already typechecks clean. No change needed. |
| `toolbarVerticalEdge` | Confirmed: `public var toolbarVerticalEdge: SwiftUICore::HorizontalEdge? { get }` — optional edge, matching the file's `nil`-handling claim. No change needed. |
| `VStack` | Confirmed: `@frozen nonisolated public struct VStack<Content> : SwiftUICore::View, ~Swift::Sendable`. Core SwiftUI type, present as expected. No change needed. |
| `ZStack` | Confirmed: same shape as VStack. No change needed. |
| `hig` | Not a symbol — last path component of the inline reference `` `hig-patterns.md` `` (a filename). Expected non-symbol noise per the brief. |
| `xcode` | Not a symbol — last path component of the inline reference `` `xcode-loop` `` (a skill name). Expected non-symbol noise per the brief. |

I also spot-checked (beyond the brief's requirement, for confidence once the
SwiftUICore gap was found) `ReservedRegion`'s `isActive`/`frame`/`margins`,
`.occlusion`/`.division`/`.includeInactive`, and
`reservedRegions(kind:options:layoutDirectionBehavior:)` with its
`layoutDirectionBehavior: SwiftUICore::LayoutDirectionBehavior = .mirrors`
default — all exist in SwiftUICore exactly as the file describes, including
the `.fixed` case the file names for the physical-hardware override.

**No claim was documented-but-absent.** Every real symbol in the file exists
in the shipped 27.1 SDK; none required removal or correction. Full detail and
grep evidence recorded in `names.log`.

## Header changes (Step 5)

Replaced the header's `verified:` line. `<build>` → `27A9269` (from
`sdk.log`). `<every other URL fetched in Step 1 that this file cites>` →
the URLs this file's own citations actually name (cross-referenced against
`authoring/apple-studio/pipeline/maps/apple-design-duo-live.md` for correct
slugs), converted to `.md` doc-URL form per the header-URL convention:

- `https://developer.apple.com/design/human-interface-guidelines/layout`
- `https://developer.apple.com/design/human-interface-guidelines/designing-for-games`
- `https://developer.apple.com/documentation/swiftui/reservedregion.md`
- `https://developer.apple.com/documentation/swiftui/geometryproxy/reservedregions(kind:options:layoutdirectionbehavior:).md`
- `https://developer.apple.com/documentation/swiftui/arrangementview.md`
- `https://developer.apple.com/documentation/swiftui/view/arrangementviewstyle(_:).md`
- `https://developer.apple.com/documentation/swiftui/view/toolbarverticalbehavior(_:).md`
- `https://developer.apple.com/documentation/swiftui/toolbarcontent/axisbehavior(_:).md`
- `https://developer.apple.com/documentation/swiftui/environmentvalues/toolbarverticaledge.md`

(`designing-for-iphone-duo` and `technologyoverviews/preparing-your-app-for-iphone-duo.md`
were already present in the header from Task 4.)

I deliberately did **not** copy the distillation map wholesale. The map
records what was *fetched* during Task 4's research (including `--hig
toolbars` and `--hig split-views`, and every individual UIKit doc page for
the "Maintaining older code" table); per the controller ruling, the header
lists what the file's own prose *cites*, and the map itself says its own
citation record is the file's header, not the map. The file's own
parenthetical citations only ever name the "Designing for iPhone Duo" and
"Layout" HIG pages (never a standalone Toolbars or Split Views page), and
only cite the tech-overview page for the UIKit table (never a per-symbol UIKit
doc URL) — so I matched the header to that, not to the map's full fetch list.

## Gate results

- `bun test` — 198 pass, 0 fail (pre-existing warnings across the whole
  catalog, unrelated to this file).
- `bun run audit` — 0 errors, 55 warnings (same pre-existing warning set;
  `adaptive-layout.md`'s only warning, "no table of contents in the first 30
  lines," predates this task).
- `claude plugin validate . --strict` — Validation passed.

All three run with the default toolchain (no `DEVELOPER_DIR`), per the
ruling.

## Files changed

- `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md` —
  header `verified:` line filled (build + URL list). No body/snippet changes;
  Step 2 and Step 4 required none.
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-7-compile/sdk.log` — new.
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-7-compile/typecheck.log` — new.
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-7-compile/names.log` — new, includes a resolutions section documenting the SwiftUICore search-path gap and each symbol's confirmation.
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-7-compile/task-7-report.md` — this report.

## Concerns

- The Step 4 command as specified in the brief has a real, reusable gap: it
  never checks `SwiftUICore.framework`, which is where SwiftUI's actual
  declarations live in the 26+/27.1 SDK generation. Any future reference
  whose prose names a bare SwiftUI symbol (not routed through the UIKit
  fallback check) will hit the same false-MISSING pattern. Worth fixing in
  `authoring/apple-studio/pipeline/` (add the SwiftUICore swiftinterface to
  the search path) rather than re-discovering this per task; I did not patch
  the shared script since it's outside this task's file scope, but flagging
  it for whoever owns Task 9's re-run or the pipeline itself.
- No other concerns. No claim in `adaptive-layout.md` needed correction or
  removal.
