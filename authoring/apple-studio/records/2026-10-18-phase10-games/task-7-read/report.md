# Task 7 report: apple-games, performance, and release corpus read in full

Date: 2026-10-18. Eleven readers (g01 to g09, p01, r01) each wrote one ledger and one notes file. A finisher ran verification and committed (f257557). The controller writes this file from the finisher's returned text, because the harness refuses a subagent's Write of report.md (SDD ruling P10).

## Result

- `check_ledger.py … --only g01,g02,g03,g04,g05,g06,g07,g08,g09,p01,r01` exits 0.
- `check_ledger.py` over the whole corpus (m, g, p and r slices) exits 0. It prints no `unsliced:` or `missing:` lines. The ledgers hold 1,222 rows, equal to the 1,222 rows in `slices.tsv`.
- There are 900 g, p and r ledger rows. 897 are `read_in_full=yes`, and 3 are unfetchable (see below).
- The field check found 0 violations in 900 rows and 78 note headings. The 12-word copy check found 0 hits and excluded 1 run. No notes were reworded.
- Of 20 sampled bullets, 19 are accurate and 1 has a misstated detail (p01; see Bullet sampling).

## Slices, pages, words

Words come from the ledgers. `field_check.py` proves they equal the manifest and sources values.

| Slice | Pages | Words | Read in full | Unfetchable | Fed nothing |
| ----- | ----: | ----: | -----------: | ----------: | ----------: |
| g01 | 29 | 52,310 | 29 | 0 | 0 |
| g02 | 68 | 51,849 | 68 | 0 | 42 |
| g03 | 91 | 51,692 | 91 | 0 | 63 |
| g04 | 59 | 53,135 | 59 | 0 | 37 |
| g05 | 74 | 51,102 | 74 | 0 | 50 |
| g06 | 169 | 50,153 | 169 | 0 | 132 |
| g07 | 206 | 49,070 | 206 | 0 | 159 |
| g08 | 70 | 52,525 | 70 | 0 | 9 |
| g09 | 66 | 55,189 | 64 | 2 | 8 |
| p01 | 39 | 46,972 | 39 | 0 | 6 |
| r01 | 29 | 32,835 | 28 | 1 | 3 |
| Total | 900 | 546,832 | 897 | 3 | 509 |

- g01 and g02 hold the HIG game pages, typography, and AVFAudio.
- g02 to g05 hold Accelerate (vDSP, vImage, simd, Sparse, Compression, AppleArchive).
- g06 holds AppKit, Apple silicon, and AudioToolbox parameters. g07 holds AudioToolbox, Core Haptics, and Background Assets.
- g08 holds Dispatch, GameController, Core Haptics, GameKit, and Model I/O. g09 holds Network, PHASE, framework overviews, Touch Controller, and UTIs.
- p01 holds Xcode performance and os logging. r01 holds Security notarization and Xcode distribution.
- Most "fed nothing" rows are symbol-index or constant-list pages. Each row's reason is in its ledger.

## Unfetchable rows

There are three. The finisher confirmed each with `curl -sL -o /dev/null -w '%{http_code}' -A 'Mozilla/5.0' "https://developer.apple.com<path>.md"`, and each returned 404.

- g09, `/documentation/kernel/1387446-sysctlbyname` and `/documentation/kernel/1462446-mach_absolute_time`: `no-unfetchable:404:deferred-20`.
  - The bare URLs return 200, but that is only the JavaScript shell.
  - Both are numeric-ID symbol links from `/documentation/Apple-Silicon/addressing-architectural-differences-in-your-macos-code`. g06 read that page in full, and g06.md lines 17–18 carry the game use of both symbols.
  - Other sources cover both pages. The SDK ships `usr/share/man/man3/sysctlbyname.3`. The SDK header `mach/mach_time.h` declares `mach_absolute_time`, and `/documentation/driverkit/mach_absolute_time` returns 200.
  - Little content is lost.
- r01, `/documentation/os/reading-unix-manual-pages`: `no-unfetchable:404:deferred-21`.
  - Both the `.md` and the DocC JSON return 404.
  - The article only explains how to read man pages. r01 read the local man pages for `codesign`, `spctl`, `hdiutil`, `pkgbuild`, `productbuild`, and `pkgutil` in its place.
  - No release content is lost.

Items 20 and 21 are in `docs/deferred.md`, after item 19 and in its style. r01.md line 155 still says "deferred-PENDING" in prose. Only the ledger value was changed, because the finisher may not edit notes beyond the copy-check rule.

## Bullets per destination section

The slices hold 804 bullets in destination sections, and 16 more in `(none)` sections. The count is top-level `- ` lines under each `##` section, `###` subsections included.

The r01 `direct-distribution.md` count includes 8 list items in its "What app-release already covers" preamble. Those items are a gap list, not claims.

Bare headings are resolved per ruling P37: apple-games in g slices, apple-performance in p01, and app-release in r01.

| Destination | g01 | g02 | g03 | g04 | g05 | g06 | g07 | g08 | g09 | p01 | r01 | Total |
| ----------- | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | ----: |
| apple-games/game-loop-and-threading.md | 5 | 0 | 2 | 3 | 10 | 13 | 2 | 12 | 11 | 17 | 1 | 76 |
| apple-games/input.md | 23 | 0 | 0 | 0 | 0 | 4 | 0 | 29 | 8 | 2 | 0 | 66 |
| apple-games/audio-and-haptics.md | 17 | 32 | 10 | 10 | 14 | 11 | 29 | 12 | 25 | 1 | 0 | 161 |
| apple-games/game-center-and-online.md | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 96 | 49 | 1 | 2 | 162 |
| apple-games/assets.md | 8 | 9 | 20 | 6 | 1 | 3 | 14 | 10 | 11 | 7 | 2 | 91 |
| apple-games/game-design.md | 71 | 10 | 0 | 0 | 2 | 2 | 0 | 5 | 2 | 0 | 0 | 92 |
| apple-performance/profiling-workflow.md | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 29 | 0 | 30 |
| app-release/direct-distribution.md | 1 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 2 | 1 | 91 | 100 |
| app-release/signing-and-provisioning.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 5 |
| app-release/testflight-and-versioning.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 5 |
| app-release/app-store-submission.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| apple-metal/command-model.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 2 |
| apple-metal/compute-and-gpu-driven.md | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 2 |
| apple-metal/cpp-and-rust.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 2 | 6 |
| apple-metal/gpu-debugging-and-profiling.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |
| apple-metal/resources-and-memory.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 2 |
| apple-metal/shading-language.md | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| (none) | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 2 | 6 | 2 | 16 |

g01 and g03 write their `(none)` sections as prose, so those count 0 bullets.

## Copy check

`task-7-read/copy_check.py` is Task 4's script adapted to the g, p, and r ledgers. It looks for runs of 12 or more consecutive words shared between a slice's notes and the cached corpus pages that slice read (`copy_check.log`).

For r01 it adds two sources the reader used outside its ledger. One is the saved "Supported capabilities (macOS)" page in `$TMP/r01-extra/`, with HTML tags stripped. The other is the man pages r01 read in place of deferred item 21: `codesign`, `spctl`, `hdiutil`, `pkgbuild`, `productbuild`, `pkgutil`, and `stapler`.

- **Hits:** 0.
- **The excluded run** is `g08.md` line 74, the JMESPath team-balance expression. It is code, so no change.
- **Sensitivity:** at an 8-word threshold (`copy_check.py 8`, not committed), the check reports 17 overlaps and 2 exclusions. They are:
  - Apple's notary error strings, quoted as an error-to-fix table (r01 lines 59–60);
  - a `codesign` command line;
  - platform lists ("iOS, iPadOS, tvOS and visionOS");
  - the Audio System Trace jitter bands;
  - short technical phrases.

## Field check

`task-7-read/field_check.py` checked 900 rows and 78 `##` note headings, and found 0 violations (`field_check.log`).

- Every ledger `words` value equals its manifest or sources value.
- Every `fed` value is `nothing: <reason>` or names known destination files.
- A bare file name resolves to the slice's own skill under P37: apple-games for g, apple-performance for p, and app-release for r. `<skill>/<file>` targets resolve directly.
- Valid app-release targets are `direct-distribution.md` plus every file that exists under `plugins/apple-studio/skills/app-release/references/`. r01 writes sections for `app-store-submission.md`, `testflight-and-versioning.md`, and `signing-and-provisioning.md`, and all three exist.
- No other heading was found.

## Findings the readers flagged for writers

Grouped by destination file and deduplicated, each with its notes source. A writer must not copy the wrong form.

### apple-games/audio-and-haptics.md

1. **vDSP FFT normalization: the sources conflict, so run a round trip before stating it.**
   - The `vDSP.h` comments and the FFT reference pages write the inverse as `scale = 1./N`.
   - The data-packing article (`/documentation/Accelerate/understanding-data-packing-for-fourier-transforms`) says vDSP never scales. It gives real forward ×2, real inverse ×N, complex forward ×1, and complex inverse ×N.
   - The DCT sample divides the inverse by N/2.
   - g05 states "vDSP never scales" (g05:19). g04 leans to the article (g04:20). g03 says to divide a round trip by 2n (g03:27).
   - The writer must run a forward/inverse round trip and log it before stating any factor.
2. **OS 27 audio API changes: gate each one with `#available` at the 26.0 floor.**
   - The realtime-safe render, receiver and input blocks are new and `__SWIFT_UNAVAILABLE` (g02:20). So is `AUAudioUnit.osWorkgroup` (g07:16).
   - Swift: `connect(_:to:format:)` and `play()` are deprecated in favor of throwing `connectNode(…)` and `playAudio()`. `auAudioUnit`, `audioUnit` and `musicSequence` are deprecated in favor of the `with…(_:)` scoped borrows (g02:25, g02:45).
   - The `AVAudioSession.interruptionNotification` family is deprecated in favor of `didBecomeActive`, `didBecomeInactive` and `resumptionRecommendation` (g02:37).
   - `AVReadOnlyAudioPCMBuffer` and the tap-provider API are OS 27 (g02:24).
   - Keep the legacy paths for 26.
3. `AVAudioSession.CategoryOptions.allowBluetooth` is deprecated in favor of `.allowBluetoothHFP`. Both are 0x4, and Apple's stereo-capture sample still passes `.allowBluetooth` (g02:31; checked in the iPhoneOS SDK `AVAudioSessionTypes.h`, lines 502 and 520).
4. SDK inconsistency: the deprecation message on `AVAudioSessionInterruptionReasonKey` points at `interruptionDetails.reason`. The declared property is `DeactivationContext.interruptionContext`. Use the declared name (g02:39).
5. `/documentation/AVFAudio/using-voice-processing` is a stub. The voice-processing details come from the `AVAudioIONode.h` header (g02:36).
6. The biquad pages disagree on filter form. `single-channel-biquadratic-filters` says direct form 1, and `multichannel-biquadratic-filters` says direct form 2. Do not repeat either (g04:25; checked, both pages at line 18).
7. Page slips (g04:23, g04:29, g05:23):
   - The `vDSP_vfltu32` summary says "unsigned 16-bit", but the signature takes `unsigned int`.
   - `vDSP_vsmfixu24` is described as "signed", but it writes `vDSP_uint24`.
   - `vDSP.indexOfMinimum(_:)` is described as returning the maximum.
8. Verify before stating (g04:22, g04:29, g04:24, g05:20):
   - whether the DFT setup accepts non-power-of-two lengths (check the setup symbol page);
   - whether vDSP float-to-integer conversion saturates out-of-range values (the page is silent, so clamp first);
   - that FFT, DFT and biquad setup creation allocates (a reader inference, not on the pages).
9. The async-workgroup sample (`/documentation/AudioToolbox/adding-asynchronous-real-time-threads-to-audio-workgroups`) has two defects: `joinToken` is used without a declaration, and `kOneNanosecond` holds 1e9 (g07:17).
10. The spatial-audio sample's prose names `kAudioChannelLayoutTag_MPEG_7_1_A`, but its code passes `kAudioChannelLayoutTag_Atmos_7_1_4`, a 12-channel layout (g07:25).
11. Deprecations missing from the docs:
    - The AudioToolbox C audio-session constant pages show no deprecation banner. The SDK deprecates the API in iOS 7, and it is unavailable on macOS (g07:10).
    - AUGraph is deprecated in its header, but the Graph Services page shows no deprecation. MusicSequence depends on it (g07:22, g07:27).
    - The Audio Queue Services page's line "recommended for all new development" is stale framing (g07:19).
    - `kAudioUnitSubType_3DMixer` is deprecated on macOS (g06:31).
    - `VirtualMaster*` are the old names, replaced by `VirtualMain*` (g06:36). `kUserPreferredAlert` is the deprecated name (g06:37).
12. `intendedSpatialExperience` on the player, output node, and haptic engine is visionOS 26 only per the headers. The article shows no gate (g07:28).
13. **Core Haptics platform claims conflict:**
    - The HIG lists iOS, iPadOS, tvOS and visionOS. The SDK has `macos(10.15)`, but there is no built-in actuator target on the Mac (g01:105, g09:75, g06:28).
    - The HIG's controller-haptics list omits iOS, but the header has `ios(14.0)` (g01:115).
    - The games HIG lists visionOS, but the Buttons page says visionOS plays no haptics (g01:121).
    - `preparing-your-app-to-play-haptics` names iPad, iPod touch and Vision Pro as having no haptics, and does not list the Mac (g08:52).
    - The games overview scopes Core Haptics to iPhone and Apple TV (g09:68).
    - Gate on `capabilitiesForHardware().supportsHaptics`.
14. `AVAudioSession` is `API_UNAVAILABLE(macos)`. The HIG audio-session guidance is iOS-family only, so a Mac game has no session, category or interruption API (g01:107, g02:30, g09:73).

### apple-games/game-loop-and-threading.md

15. **The interval-workgroup claim (g09:92): the finisher checked the header, and it supports the claim.**
    - `os/workgroup_interval.h` lines 44–46 say the only supported interval workgroups are for audio workloads, from AudioToolbox.
    - The `os/` headers declare only `os_workgroup_parallel_create`, `os_workgroup_create_with_port`, and `os_workgroup_create_with_workgroup`.
    - The only public interval creator is `AudioWorkIntervalCreate`. `AudioWorkInterval.h` lines 42–49 document it for audio realtime threads.
    - g07:35 frames the interval pattern as something a game can apply to its own job threads. That conflicts with the header, so the writer states g09's position.
16. `CVDisplayLink` is deprecated in macOS 15 (`API_DEPRECATED_BEGIN` in `CVDisplayLink.h`). Use `NSView/NSWindow/NSScreen.displayLink(target:selector:)` (g04:5, p01:44).
    - The Accelerate cube sample uses `CVDisplayLink` and advances a fixed 0.02 per tick.
    - Verify the macOS 14 floor of the replacement on its symbol page.
17. Verify before stating:
    - The frames-in-flight `DispatchSemaphore` pattern may break Apple's QoS rule: semaphore waits do not donate priority, so the waiter's QoS must not exceed the signaler's. Check which thread runs Metal completion handlers (p01:52; p01:83 for apple-metal).
    - "Barriers act as plain async on a global queue" comes from the `dispatch_barrier_async` reference, not the slice page (g08:13).
    - "16 KB page" is general knowledge in g09:85. p01:88 and p01:78 have page sources (typically 16 KB; the example shows 16384).
    - p01:49 (an engine spinning its own main-thread loop reads as a hang) is labeled inference.
18. Deprecated: `dispatch_get_current_queue` (g08:9), and the whole AppKit OpenGL hosting surface plus `NSDisableScreenUpdates` (g06:12).

### apple-games/input.md

19. Page code errors:
    - The `input.buttons[.a]` subscripts return an optional, so the page's one-liner does not compile (g08:37; per the swiftinterface).
    - The second-generation Siri Remote page's `isKind(of:)` snippet mixes Objective-C and Swift and does not compile (g08:46).
20. Gates and deprecations:
    - `GCVirtualController` is iOS 15 only, with no macOS header at all (g08:20).
    - The snapshot classes `GCGamepad` and `GC*Snapshot*` are deprecated (g08:25).
    - `NSTextInput` is deprecated in favor of `NSTextInputClient` (g06:6).
    - Touch Controller is iOS 26 only. The page metadata gives no availability; the header says `API_UNAVAILABLE(macCatalyst, visionos)`, and the framework is absent from the macOS and tvOS SDKs (g09:105).
    - `GCControllerHomeButtonSettingsManager` (27 SDKs) is `NS_REFINED_FOR_SWIFT`. Check its Swift spelling (g09:103).
21. HIG gaps the readers filled from headers:
    - The gestures page names no iOS symbol for deferring system edges. The property is `preferredScreenEdgesDeferringSystemGestures` (g01:88).
    - The pointing-devices page says nothing on pointer lock. The symbols are `prefersPointerLocked` and `CGAssociateMouseAndMouseCursorPosition` (g01:98).

### apple-games/game-center-and-online.md

22. **Developer ID cannot use Game Center, In-App Purchase, or Sign in with Apple.**
    - iCloud and push need an embedded Developer ID provisioning profile at `Contents/embedded.provisionprofile` (r01:75, r01:149).
    - Source: Apple's "Supported capabilities (macOS)" page, saved in `$TMP/r01-extra/`. The finisher checked the table: Game Center, In-App Purchase and Sign in with Apple are marked ADP only. The three iCloud rows and Push notifications are marked yes for Developer ID.
    - This settles g09:129's "verify" request.
23. Deprecated in the 26 SDKs, while the articles still teach them (g08:116, g08:67):
    - `GKGameCenterViewController` (`API_DEPRECATED_WITH_REPLACEMENT("Replaced by GKAccessPoint")`);
    - `GKAccessPoint.showHighlights`;
    - `GKGameCenterViewControllerState.challenges`.
    - Separately, `GKVoiceChat` is deprecated at iOS 18 and macOS 15 (g08:71).
24. Errors on the activities page (g08:89–93). The first three were checked against `GKGameActivityDefinition.h` lines 66–71 and `GKGameActivity.h` lines 26, 29 and 91.
    - `associatedAchievementDescriptions` does not exist. The SDK names are `achievementDescriptions` and `leaderboards`.
    - `activity.activityIdentifier` is not in the header. Use `activityDefinition.identifier`.
    - The page writes `start(_:partyCode:)`. The SDK spelling is `start(definition:partyCode:)`.
    - `scoreForLeaderboard` and `setScoreOnLeaderboard` are Objective-C selectors, not Swift names.
25. Other page errors:
    - The turn-based sample's next-participant filter uses `||`, which keeps done players. It needs `&&` (g08:156; checked, page line 102).
    - `properties["gc"]["team"]` is pseudo-code (g08:75).
    - The party-codes prose names the rule-sets endpoint, but its JSON uses the rules endpoint, and the JSON is right (g08:141).
    - The skill-level prose lists ages first, but the expression lists thresholds first. Follow the expression (g08:136).
    - The recurring-leaderboard page says the instance method is "only" for recurring boards, but its sample uses the class method (g08:107).
26. Gates:
    - The challenge and activity triggers on `GKAccessPoint` are iOS and macOS 26 only, not tvOS or visionOS (g08:95, g08:117).
    - `GKChallengeDefinition` and `GKGameActivity` are OS 26 (g08:87). This settles g01:135's "check availability".
    - `GKSavedGame` is iOS and macOS only (g08:147). GameSave lists no tvOS (g01:126, g09:49).
    - Mac Game Center needs App Sandbox incoming and outgoing network access (g08:137).
27. Verify before stating:
    - whether multicast on iOS needs the `com.apple.developer.networking.multicast` entitlement (g09:27, not on the page);
    - that `matchDataMaximumSize` has no published number, so read it at runtime (g08:155).

### apple-games/assets.md

28. **Compression:**
    - `COMPRESSION_LZMESH` (0xE05) and `COMPRESSION_LZRAVEN` (0xD05) are buffer-API only, macOS 27 and iOS 27 (checked, `compression.h` lines 131–132).
    - The stream sample and the filters article still recommend LZFSE (g03:35–37, g09:114).
    - Do not tell readers to stream LZMESH. Streamed Apple-only data stays on LZFSE.
29. The AppleArchive decompression sample's `String(cString:)` reads past an unterminated buffer. Decode with a length (g03:45).
30. **Background Assets:**
    - The `statusUpdates` switch writes `case began(let assetPack)` with no leading dot, so it does not compile (g07:49; checked, page lines 74 and 76).
    - SDK deprecations the article omits:
      - `AssetPackManager.assetPack(withID:)` is deprecated in 27, in favor of the `manifest` property;
      - `ensureLocalAvailability(of:)` is deprecated in 26.4;
      - `allAssetPacks` and `status(ofAssetPackWithID:)` are deprecated.
    - The managed API is OS 26 and not on watchOS (g07:50).
31. The 2 GB and 4 GB bundle caps and the on-demand-resource limits are iOS, iPadOS and tvOS only. Do not carry them to the Mac App Store (g08:172).
32. There is no system UTI for glTF, KTX/KTX2, or ASTC (g09:113; checked by the reader in `UTCoreTypes.h`). "Metal has no 24-bit RGB8 format" is reader knowledge, not from a page; verify it (g03:56).
33. vImage specifics a writer may find counterintuitive:
    - Apple says to unpremultiply before Lanczos resampling (g02:61, g03:59).
    - `kvImageHighQualityResampling` does not remove ringing (g04:15).
    - Gray conversion uses Rec. 601 weights implicitly (g03:53).

### apple-games/game-design.md

34. HIG changes in 2026:
    - The Layout page was revised on 2026-09-09 and no longer has per-device point-size tables (g01:55).
    - The HIG renamed "In-App Purchase" to "Apple In-App Purchase" on 2026-09-17. StoreKit is still the API (g01:24).
35. macOS has no Dynamic Type (g02:11). The legacy key-based `NSAccessibility` API is deprecated (g06:48).

### apple-performance/profiling-workflow.md

36. **xctrace exit 54** (p01:5; `task-6-probe/r3-toc.log`). The current SKILL.md and profiling-workflow.md wording, "exits 54 on success", is wrong.
    - The record exit status follows the target: 0 for `/usr/bin/true` and a Metal app that ended on its own; 54 for `/usr/bin/false` and for the `--time-limit` SIGKILL.
    - Only the toc's launched-process `return-exit-status` and `termination-reason` are evidence of how the target ended.
    - `true` and `false` print the same completion lines, "Recording completed. Saving output file..." and "Output file saved as:". So p01's proposed test, the saved-as line plus the toc, rests only on the toc half. The saved-as line shows only that a trace was written.
37. **Ruling P34: do not state values that no committed log shows.**
    - In r3-toc.log: the 466M and 98M sizes (lines 17 and 110), SIGBUS exit 138 twice (lines 22 and 28), and 48 GPU/Metal tables (lines 48 and 117).
    - Not in any log: p01:6's "a 10 s capture". r3-1 ran with `--time-limit 10s`, but the target exited first ("Target app exited, ending recording"), and the log records no duration. Reword it, for example as "a `--time-limit 10s` recording whose target ended first".
    - p01:12's full `xctrace list templates` list is not in a committed log. `survey/toolchain.log` line 17 holds Audio System Trace, CPU Counters, Game Memory, Game Performance, Game Performance Overview, Metal System Trace, and Processor Trace. System Trace, CPU Profiler, RealityKit Trace, Core AI, Network, Logging, and Activity Monitor are not logged. Neither is p01:35's claim that no Energy Log template exists.
    - Re-run and commit a log before stating them, or cut them.
38. Page errors:
    - The page spells `--only-test-configuration` and `--skip-test-configuration` with a double dash. `xcodebuild -help` lists them with a single dash (p01:19; checked, page lines 173 and 179, help lines 109–110).
    - The os_log UUID specifier is `%{uuid_t}.*16P` in the table but `%{uuid}.*P` in the example, and the page labels C and Objective-C code as Swift (p01:22).
    - The performance-cycle page still routes power problems to an "Energy Log" template (p01:35; see 37).
39. The Apple silicon CPU optimization guide is a gated download. Do not paraphrase its numbers from memory (p01:8).

### apple-metal/command-model.md

40. Touch Controller draws only through `renderUsingRenderCommandEncoder:` with a Metal 3 `MTLRenderCommandEncoder`. The iOS 27.1 SDK has no `MTL4RenderCommandEncoder` variant, so a Metal 4 renderer needs a Metal 3 overlay pass (g09:143).

### apple-metal/resources-and-memory.md

41. Whether GPU resource memory counts in the iOS memory footprint is not stated on the page. Verify before claiming it (p01:88).

### apple-metal/cpp-and-rust.md

42. The pages contradict each other on `simctl`. The devicectl page sends readers to the Command Line Tools install page for `simctl`. The CLT page and the Xcode tool reference say Xcode-only tools are absent from the CLT (r01:137).

### app-release/direct-distribution.md

43. Spellings that differ between pages and tools:
    - The page uses `spctl --type exec`. `man spctl` spells it `execute`, `install`, `open`, and as of macOS 15.0 spctl no longer edits the rule database (r01:62; checked, page line 65, man lines 67–70 and 78).
    - The page uses `codesign -d --entitlements :-`. The modern form is `--entitlements - --xml` (r01:67).
    - The page uses `hdiutil create -srcFolder`. The help text spells it `-srcfolder` (r01:100).
    - The page writes `Developer ID Application: <Team ID>`. The Keychain usually shows `Developer ID Application: <Team Name> (<Team ID>)` (r01:86).
44. Deprecations and defaults:
    - `codesign --deep` is deprecated for signing as of macOS 13 (r01:88).
    - From macOS 15, codesign does not embed entitlements in library signatures unless `--force-library-entitlements` is passed (r01:82).
    - The packaging page still names `altool` for Mac App Store upload. `altool` was retired only for notarization (r01:101).
    - `launchctl load` and `start` are the page's legacy verbs. `bootstrap` and `kickstart` are unchecked (r01:111).
45. Verify before stating:
    - Is `ARCHS` without `x86_64` the Xcode 27 default for a macOS 27 target? The page only says to add `x86_64` (g06:55; checked, porting-JIT page lines 18–25).
    - The page says the Account Holder must sign with Developer ID. In practice the Account Holder creates the certificate (r01:57).
    - No slice page covers Apple-silicon-only Mac App Store targeting (r01:105). Only the games overview names it (g09:128).
46. **Environment fact for a later task:** this machine has no Developer ID Application identity. `security find-identity -p codesigning -v` lists only an Apple Development certificate (r01:86).

### app-release/signing-and-provisioning.md (existing reference)

47. **Correction:** a re-sign is needed when `CodeDirectory v=` is below 20400. 20500 is only the page's example value (r01:132).
48. The Foundation `#bundle` macro spelling is unchecked against the SDK (r01:129).

The finisher built this list from a full read of all eleven notes files, plus the controller's five carry-forwards (items 1, 2, 15, 22, 36–37). A flag worded differently could still be missing. The notes files are the complete record.

## Bullet sampling

The finisher sampled 20 bullets, at least one per slice, weighted toward g01, g08, g09, p01, and r01. Each was checked against its page in `$TMP/corpus/` and, where it names a symbol, against the SDK headers.

| Slice | Bullet | Checked against | Verdict |
| ----- | ------ | --------------- | ------- |
| g01 | 8: text-size table | designing-for-games, lines 50–54 | accurate |
| g01 | 83: only tvOS and visionOS may require a controller; `GCRequiresControllerUserInteraction` | game-controls, line 69 | accurate |
| g02 | 31: `.allowBluetooth` deprecated, `.allowBluetoothHFP` same bit 0x4; sample still passes the old option | iPhoneOS SDK `AVAudioSessionTypes.h`, lines 502 and 520; page line 41 | accurate |
| g03 | 36: `COMPRESSION_LZMESH` 0xE05, `LZRAVEN` 0xD05, buffer-only, macOS 27 / iOS 27 | `compression.h`, lines 131–132 | accurate |
| g04 | 25: single-channel page says direct form 1, multichannel says direct form 2 | both pages, line 18 | accurate |
| g05 | 23: `indexOfMinimum` described as returning the maximum | vector-extrema-calculation, lines 46–52 | accurate |
| g06 | 55: Xcode 27 targeting macOS 27 needs `x86_64` added; Xcode runs on Intel only through 26 | porting-JIT page, lines 18–25 | accurate (the reader marks its default-`ARCHS` inference as unconfirmed) |
| g07 | 49: `case began(let assetPack)` with no leading dot | downloading-apple-hosted-asset-packs, lines 74 and 76 | accurate |
| g08 | 89: `associatedAchievementDescriptions` is absent; SDK names `achievementDescriptions`, `leaderboards` | page line 99; `GKGameActivityDefinition.h`, lines 66–71 | accurate |
| g08 | 156: sample filter uses `||` where `&&` is meant | starting-turn-based-matches page, line 102 | accurate |
| g08 | 90–91: `activityIdentifier` not in header; `start(definition:partyCode:)` | `GKGameActivity.h`, lines 26, 29, and 91 | accurate |
| g09 | 92: interval workgroups are audio-only; no public creator for a render or sim loop | `os/workgroup_interval.h`, lines 44–46; `os/workgroup_*.h` create functions; `AudioWorkInterval.h`, lines 42–49 | accurate |
| g09 | 52: `nw_tcp_set_max_pacing_rate` is `anyappleos(27.0)` and returns errno | Network `tcp_options.h`, lines 414–453 | accurate |
| p01 | 19: page's double-dash test-configuration flags; help lists a single dash | page lines 173 and 179; `xcodebuild -help`, lines 109–110 | accurate |
| p01 | 13: 100 ms, less than half for the app, 8.3 / 16.7 ms, ~5 ms, VRR | improving-app-responsiveness, lines 25, 32, 36–39, and 221 | accurate |
| p01 | 6: Task 6 runtime facts | `task-6-probe/r3-toc.log` | **misstated in one detail.** The 466M and 98M sizes, exit 138, and 48 tables match the log. "A 10 s capture" does not: r3-1 had `--time-limit 10s`, the target exited first, and no duration is logged (P34). |
| r01 | 42: most within 5 minutes, 98% within 15, at most 75 per day | customizing-the-notarization-workflow, lines 212 and 224 | accurate |
| r01 | 62: page uses `exec`; man spells `execute`, `install`, `open`; macOS 15 drops rule edits | resolving-common-notarization-issues, line 65; `man spctl`, lines 67–70 and 78 | accurate |
| r01 | 75: Developer ID capability table | `$TMP/r01-extra/supported-capabilities-macos.html` (table rows parsed) | accurate for the rows checked: Game Center, In-App Purchase, Sign in with Apple, the three iCloud rows, Push |
| g01 | 11: default input per platform | designing-for-games, lines 88–97 | accurate. The table says visionOS default is "Touch"; the reader's "eyes and hands" comes from the prose on line 88. |

Verdict: 19 accurate, 1 misstated detail (p01:6). The notes were not edited, under the finisher's rules. Item 37 above carries the correction for the writer.
