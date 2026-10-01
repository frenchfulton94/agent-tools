# Task 8 results — runtime probe on the iPhone Duo simulator

Device: "Duo Probe" (`com.apple.CoreSimulator.SimDeviceType.iPhone-Duo`, iPhone19,4) on the
iOS 27.1 simulator runtime (24A94401). Built with Xcode 27.1 beta (27A9269), iphonesimulator27.1
SDK (24A94403). Probe: `authoring/apple-studio/pipeline/fixtures/duo-probe/DuoProbeView.swift`.
Discovery class: **B**. Device Hub set the poses and the rotations by hand. No command-line pose
control exists (`discovery.log`, `devicectl-cli.log`).

Display numbering: `simctl io --display=1` is the outer display ("LCD", 1398×2034 px);
`--display=3` is the inner display ("LCD-1", 2007×2853 px). `capture.sh` saves both as
`<state>.outer.png` and `<state>.inner.png`. It appends the active display and the
orientation to `capture-states.log`.

## States captured

| State | Pose (from `capture-states.log`) | File | Bar | R1 edge | Width, size (pt) | R3 `includeInactive` | R5 default query |
|---|---|---|---|---|---|---|---|
| outer-portrait | closed, portrait | `outer-portrait.png` | vertical, trailing: Share, "…" | `.trailing` | compact, 382×562 | 0, `[]` | 0, `[]` |
| outer-portrait-overflow | closed, portrait, "…" open | `outer-portrait-overflow.outer.png` | menu lists "R2 TitleOnly" and "R2 WithIcon" (star) | `.trailing` | compact | 0 | 0 |
| outer-landscape | closed, landscapeRight | `outer-landscape.outer.png` | vertical, trailing: Share, "…" | `.trailing` | compact, 594×350 | 0, `[]` | 0, `[]` |
| inner-landscape | fully open, landscapeRight | `inner-landscape.inner.png` | vertical, trailing: Share, "…" | `.trailing` | regular, 867×553 | 1, `[false]` | 0, `[]` |
| inner-portrait | fully open, portrait (devicectl reports `portraitUpsideDown`) | `inner-portrait.inner.png` | horizontal, top: Share, "…" | `nil` | regular, 669×783 | 1, `[false]` | 0, `[]` |
| inner-partial | partly folded, portrait | `inner-partial.inner.png` | horizontal, top: Share, "…" | `nil` | regular, 669×783 | 1, `[true]` | 1, `[true]` |
| outer-sheet | closed, portrait, sheet open | `outer-sheet.png` | sheet bar vertical (Done at trailing) | sheet `.trailing` | — | — | — |
| outer-sheet-disabled | as above, `.disabled` | `outer-sheet-disabled.png` | sheet bar horizontal (Done top right, inline title) | sheet `nil` | — | — | — |
| outer-portrait-r2 | closed, portrait, R2 items as `.primaryAction` | `outer-portrait-r2.outer.png` | vertical, trailing: Share, star; "R2 TitleOnly" as a capsule in the top bar beside the title; no "…" | `.trailing` | compact, 382×562 | 0 | 0 |

The controller captured the open-pose states as `inner-portrait` while the device was still in
landscapeRight. The controller then renamed those files to `inner-landscape` and annotated
the line in `capture-states.log`. In every open pose, `<state>.outer.png` is black: the outer
display is off.

## Verdicts

| Claim | Verdict | Deciding evidence |
|---|---|---|
| **R1**: bars are vertical on the outer display in every orientation and on the inner display in landscape. The inner display in portrait keeps horizontal bars. | CONFIRMED | `outer-portrait.png`, `outer-landscape.outer.png`, `inner-landscape.inner.png`: vertical trailing bar, `R1 toolbarVerticalEdge: Optional(SwiftUI.HorizontalEdge.trailing)`. `inner-portrait.inner.png`: horizontal top bar, `R1 toolbarVerticalEdge: nil`. `unified.log` 2026-10-01 10:57:55 `R1 edge=nil size=585x783`. |
| **R2**: an item with a title and no symbol never goes into a vertical bar. | CONFIRMED (re-probe) | `outer-portrait-r2.outer.png`: with both items as `.primaryAction`, "R2 WithIcon" shows as a star in the vertical bar. "R2 TitleOnly" is absent from the vertical bar and shows as a text capsule in the top bar beside the title. The re-probe had no "…" button, so no overflow menu needed opening. The first walk used `.secondaryAction`. Both items went to the overflow menu there, with or without a symbol (`outer-portrait-overflow.outer.png`), so the first walk did not test R2. |
| **R3**: the fold division is active only when the device is partly open, and inactive when fully open. | CONFIRMED | `inner-partial.inner.png`: `R3 divisions: 1 active: [true]`. `inner-portrait.inner.png`, `inner-landscape.inner.png`: `1 active: [false]`. Closed (`outer-portrait.png`, `outer-landscape.outer.png`): `0 active: []`. `unified.log` 10:59:50 `R3 active=[true] count=1`. |
| **R4**: sheets on the outer display have vertical bars by default. | CONFIRMED | `outer-sheet.png`: sheet bar vertical, `R4 sheet toolbarVerticalEdge: Optional(SwiftUI.HorizontalEdge.trailing)`. `outer-sheet-disabled.png`: with `toolbarVerticalBehavior(.disabled)` the bar is horizontal and both edge reads are `nil`. `unified.log` 2026-09-30 18:06:29 `R4 sheet inside edge=nil disabled=true`. |
| **R5**: does the default `reservedRegions(kind: .division)` query include inactive regions? | The SDK-header reading holds: the default omits inactive regions | Fully open (`inner-portrait.inner.png`, `inner-landscape.inner.png`): `R3 divisions: 1 active: [false]` beside `R5 default query: 0 active: []`. Partly folded (`inner-partial.inner.png`): both queries return `1 [true]`. `unified.log` 10:56:35 `R5 default active=[] count=0 includeInactive count=1`. The ReservedRegion doc page's "regardless of whether they are currently active" does not hold on this runtime. |
| **R6**: do `.secondaryAction` items start in the overflow menu? | YES, on both displays | `outer-portrait.png`, `outer-landscape.outer.png`, `inner-landscape.inner.png`, `inner-portrait.inner.png`, `inner-partial.inner.png`: the bar shows only Share and "…". `outer-portrait-overflow.outer.png`: both secondary items, with and without a symbol, are inside the menu. The probe set no `visibilityPriority`. It does not show what a priority does to a `.secondaryAction` item. |

## Probe changes during the task (the committed probe is the R2 re-probe version)

1. R5: a second query, `proxy.reservedRegions(kind: .division)` with default options. It is shown and logged beside the `.includeInactive` query.
2. Launch arguments `-DuoProbeOpenSheet` and `-DuoProbeSheetDisabled` reach the R4 sheet states, because `simctl` cannot tap: `xcrun simctl launch --terminate-running-process <UDID> <bundle-id> -DuoProbeOpenSheet [-DuoProbeSheetDisabled]`.
3. R4 logs the sheet edge both above and below `toolbarVerticalBehavior`.
4. R2 re-probe: "R2 TitleOnly" and "R2 WithIcon" moved from `.secondaryAction` to `.primaryAction`. The earlier states (all except `outer-portrait-r2`) came from the `.secondaryAction` build.

## Other observations

- `unified.log` holds transient `R1 edge=Optional(SwiftUI.HorizontalEdge.leading)` lines during launches and pose changes, for example 10:56:25 `size=510x350` and 11:19:25 `size=669x783`. Each one changed back within a second. No settled state showed a leading bar. They look like system snapshot passes, but the probe does not prove that. The probe did not test the landscapeLeft rotation or right-to-left layout.
- The `size=` in the first R1 log line after each launch is `0x0`. The log closure captures the proxy before the first layout. The on-screen label carries the real size.
- On the first boot, `simctl bootstatus` reported "Data Migration Failed". Install and launch still succeeded.
- `simctl io screenConfig --display=1 power off` did not fold or unfold the device. After `power on`, the outer display stayed black until the device rebooted.
