# Task 8 report: runtime probe R1–R6 and the `xcode-loop` pose section

Status: DONE. The work ran in three sessions:
- 2026-09-30, first session: stopped NEEDS_CONTEXT because no iOS 27.1 runtime was installed.
- 2026-09-30, second session: built and installed the probe, captured the states the command line can reach, then stopped NEEDS_CONTEXT for class B.
- 2026-10-01, third session: the controller ran the Device Hub pose walk with the user, and I finished the task.

## Discovery and pose method: class B

- Toolchain: every `xcodebuild` / `xcrun` / `simctl` / `devicectl` call ran with `DEVELOPER_DIR` set to Xcode 27.1 beta (27A9269). `xcode-select` was not changed. `run.sh` and `capture.sh` export the variable and carry a comment that gives the reason.
- Device type: `com.apple.CoreSimulator.SimDeviceType.iPhone-Duo` (iPhone19,4) exists. It needs runtime 27.1.0 or later.
- Runtime: iOS 27.1 is build 24A94401, and the SDK expects 24A94403. Create, boot, build, install, and launch all worked on 24A94401. The first boot's `bootstatus` reported "Data Migration Failed", which had no visible effect.
- No command-line pose control exists:
  - `simctl` has no pose command.
  - `devicectl device orientation set` and `rotate` print success, but the orientation stays portrait.
  - `devicectl device motion hinge-angle` only reads the hinge.
  - `simctl io screenConfig power off` does not fold the device.
- Device Hub set the poses and rotations. The controller ran `capture.sh` after each pose the user set. Evidence: `discovery.log`, `devicectl-cli.log`, `capture-states.log`.

## Build

`run.sh` → `** BUILD SUCCEEDED **`. `build.log` comes from the final build, the R2 re-probe; three builds ran in total. The launch printed `dev.frenchfultonjr.StudioFixture: <pid>`.

## Verdicts (details and quotes in `results.md`)

| Claim | Verdict | Evidence |
|---|---|---|
| R1 bar axis per display and orientation | CONFIRMED | `outer-portrait.png`, `outer-landscape.outer.png`, `inner-landscape.inner.png` (vertical, `.trailing`); `inner-portrait.inner.png` (horizontal, `nil`); `unified.log` 10:57:55 |
| R2 title-only item never in a vertical bar | CONFIRMED (re-probe) | `outer-portrait-r2.outer.png`: the star is in the vertical bar, and TitleOnly is a capsule in the top bar beside the title. The re-probe had no "…" button, so no overflow menu needed opening. The first walk was confounded because both `.secondaryAction` items went to the overflow menu (`outer-portrait-overflow.outer.png`) |
| R3 fold active only when partly open | CONFIRMED | `inner-partial.inner.png` `[true]`; `inner-portrait/landscape.inner.png` `[false]`; closed: 0 divisions; `unified.log` 10:59:50 |
| R4 outer-display sheets vertical by default | CONFIRMED | `outer-sheet.png` (vertical, `.trailing`); `outer-sheet-disabled.png` (horizontal, `nil`); `unified.log` 2026-09-30 18:06:29 |
| R5 default `reservedRegions` query | Matches the SDK header: the default omits inactive regions | Fully open: default 0 vs. `.includeInactive` 1 `[false]`. Partly folded: both 1 `[true]`. `unified.log` 10:56:35 |
| R6 `.secondaryAction` start in overflow | YES, on both displays, in every captured pose | Each main-view capture shows only Share and "…"; `outer-portrait-overflow.outer.png` |

## Reference changes: `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md`

- I added a runtime citation after [R1], [R2], [R3], and [R4]: `(runtime-checked 2026-10, iOS 27.1 simulator: records/2026-09-30-phase9-adaptive-layout/task-8-probe/results.md).` The date is 2026-10, not the brief's 2026-09, because the pose walk that decides R1–R3 and the R2 re-probe ran on 2026-10-01. The citation ends with a period so that it stands as its own sentence. Without the period, vale's sentence-length rule fired on the following sentence.
- R5 correction to § Reserved regions. Old text: "the docs and the SDK header do not agree…". New text: the default query returns only active regions. On a fully open device, the default query returns no fold, and `.includeInactive` returns the fold with `isActive` false. The docs' wording does not hold, and the runtime follows the header. The text still advises checking `isActive`. The runtime citation sits in the paragraph's closing source note.
- R6: a new paragraph after the `MessageDetail` snippet says that on iPhone Duo `.secondaryAction` items start in the overflow menu on both displays, with or without a symbol. It also says the runtime check set no `visibilityPriority`, so it does not show whether `.high` keeps Reply in the bar. It ends with the citation.
  - Deviation: the controller asked for wording that `visibilityPriority` "orders items within overflow". The probe set no priority, so the runtime check did not test that. I wrote only what the run showed.
- R1–R4 needed no text correction.
- Checks:
  - vale: 0 errors, 1 warning, the same as the baseline (the header line).
  - `typecheck_snippets.py` with the 27.1 toolchain: `TOTAL: 8/8 snippets typecheck clean`.

## xcode-loop changes: `plugins/apple-studio/skills/xcode-loop/references/headless-commands.md`

- Line 1 now reads `…; § 9 verified 2026-10 against Xcode 27.1 beta (27A9269), by execution`.
- Lines 6–7 (deferred item 12) now read "Verified against a multiplatform SwiftUI fixture app (one target for iOS + macOS, Swift Testing unit tests)." I reflowed the rest of that paragraph. The scheme name `StudioFixture` still appears in the command examples in §§ 1–8. Item 12 covered only the path citation.
- New § 9, iPhone Duo — displays and poses. It holds only commands that I ran:
  - poses are not scriptable, so set them in Device Hub;
  - the toolchain requirement;
  - `simctl create` for the Duo;
  - the display numbers from `simctl io enumerate`;
  - `screenshot --display=1|3`, and the default to display 1, which is black when the device is open;
  - `devicectl device info displays`;
  - three commands that look like pose control but are not (`orientation set`/`rotate`, `motion hinge-angle`, `screenConfig power`).
- vale: 9 warnings, the same count as the baseline. None of them is in § 9.

## Probe files: `authoring/apple-studio/pipeline/fixtures/duo-probe/`

- `DuoProbeView.swift`. Additions to the brief's view:
  - the R5 default query;
  - the launch arguments `-DuoProbeOpenSheet` and `-DuoProbeSheetDisabled`;
  - R4 edge logging above and below the modifier;
  - the R2 items as `.primaryAction`. This is the version that produced the R2 evidence; the earlier states came from the `.secondaryAction` build, as `results.md` records.
- `run.sh`: the brief's script, plus the `DEVELOPER_DIR` export.
- `capture.sh` (new): screenshots both displays for one state and appends the `devicectl` display state to `capture-states.log`.

## Cleanup

- `simctl shutdown` and `delete` ran on B4066944-1CF0-46D6-90A4-5FD552B36FE4. No "Duo Probe" device remains.
- `xcrun simctl list devices booted` lists no device, with both the 27.1 and the default toolchain.
- All three temp workdirs are removed, and `workdir.txt` is deleted.
- `git -C ~/Projects/StudioFixture status --porcelain` is empty, at 5287d2c.

## Gates

- `bun test`: 198 pass, 0 fail.
- `bun run audit`: 0 errors, 55 warnings. The `headless-commands.md` table-of-contents warning was already there, because the file was over the threshold before this task.
- `claude plugin validate . --strict`: ✔ Validation passed.

## Files changed

- `authoring/apple-studio/pipeline/fixtures/duo-probe/{DuoProbeView.swift,run.sh,capture.sh}`
- `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md`
- `plugins/apple-studio/skills/xcode-loop/references/headless-commands.md`
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-8-probe/`:
  - text records: brief, `discovery.log`, `devicectl-cli.log`, `build.log`, `bundle-id.txt`, `capture-states.log`, `unified-cli-phase.log`, `unified.log`, `results.md`, this report;
  - 17 PNG files.

## Concerns

1. The `MessageDetail` snippet teaches `visibilityPriority(.high)` on a `.secondaryAction` Reply. The runtime puts secondary items in the overflow menu from the start, so that priority may have no visible effect on iPhone Duo. A probe that sets the priorities, or a snippet that makes Reply `.primaryAction`, would settle it. I did not change the snippet without evidence.
2. `unified.log` holds transient `edge=.leading` values during launches and pose changes, and no settled state showed a leading bar. The reference's "stays on the hardware side" and right-to-left claims are not runtime-checked. The landscapeLeft rotation was not walked either.
3. `adaptive-layout.md`'s header note still names only R1–R4. R5 and R6 carry inline citations.
4. Deferred item 12 has fired and is done in this commit. `docs/deferred.md` still lists it as open; close it in Task 9 or the phase record.
5. The plugin version is not bumped here. That belongs to the release task.
6. The exact Device Hub control labels in § 9 come from the user's walk and the plugin binary. I did not see them on screen. § 9 names the controls generically: "pose and rotate controls".
