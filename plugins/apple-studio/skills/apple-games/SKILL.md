---
name: apple-games
description: Writing the game side of a native Mac, iPhone, or iPad game on Apple silicon - the Metal game loop on CAMetalDisplayLink, fixed-step simulation and frame pacing, threads, QoS, and os_workgroup, thermal state, Game Mode, Game Controller, keyboard and mouse, Touch Controller, AVAudioEngine, PHASE, the audio session, real-time audio threads, Core Haptics, GameKit / Game Center achievements, leaderboards, and matches, game saves, Network framework multiplayer, compression and pak files, Model I/O, Background Assets, and the HIG for games. Use when hosting a Metal view, choosing a loop driver, pacing frames, reading a controller or mouse-look, playing sound or haptics, adding Game Center or cloud saves, delivering large game content, or checking a game against the HIG. Not for GPU frame time or Metal code (apple-metal), CPU profiling or launch time (apple-performance), general HIG layout (apple-design), signing and notarization (app-release), or SpriteKit and third-party engine questions.
---

# Games (the loop, input, audio, and online play)

Scope: **what a native game does around its renderer: the loop, its threads,
input, sound, Game Center, saves, and content delivery.** Mac first, then
iPhone and iPad. Apple silicon only. SpriteKit, SceneKit, RealityKit,
GameplayKit, Unity, Unreal, Godot, visionOS, tvOS, Apple Arcade, and engine
architecture are out of scope.

Read the reference for the decision at hand:
- Loop driver, Metal view hosting, the fixed simulation step, clocks, threads
  and QoS, job systems, `os_workgroup`, thermal state, Game Mode, full screen,
  pausing → `references/game-loop-and-threading.md`
- Which input path: controller discovery and reading, keyboard and mouse,
  mouse-look and pointer lock, Touch Controller, controller haptics,
  remapping, racing wheels → `references/input.md`
- Audio layer choice: AVAudioEngine and its OS 27 changes, the audio session,
  3D audio and PHASE, real-time audio threads, FFT scaling, Core Haptics →
  `references/audio-and-haptics.md`
- Distribution decides online play: GameKit setup, the access point,
  achievements, leaderboards, challenges, matches, saves across devices,
  Network framework multiplayer → `references/game-center-and-online.md`
- Content delivery: compression, pak files, archives, Model I/O and USD at
  bake time, texture bakes, file types, Background Assets, file locations →
  `references/assets.md`
- Game HIG: platform expectations, the controller rule, control sizes, text
  legibility, drawn menus and VoiceOver, pause, onboarding, Game Center
  presentation → `references/game-design.md`

Name the symptom before you pick the skill:
- **Frame pacing policy, the fixed step, threads and QoS, input, audio, Game
  Center, saves, and assets are here.** Examples are game speed that changes
  with the refresh rate and a render thread at the wrong QoS. A controller
  that the game does not see and audio that stays silent after an
  interruption are here too.
- **GPU frame time and the display-link mechanics go to apple-metal.**
  Drawable acquisition, present, `preferredFrameLatency`, and the
  `CAMetalDisplayLink` delegate and render-thread code are its job. This skill
  decides which driver to use and where the simulation sits around that code.
  In the Game Performance timeline, a long display interval with a busy GPU
  track is GPU work and goes there.
- **CPU tick cost goes to apple-performance.** Time Profiler, call trees,
  signposts, hangs, and launch time are its job. This skill decides how the
  tick is built. That skill measures what it costs.
- **General HIG layout goes to apple-design.** Type scaling, color, and
  settings for an ordinary app are there. Only what a game does differently is
  in `references/game-design.md`.
- **Signing, notarization, and App Store submission go to app-release.**

The OS floor:
- **The floor is macOS 26.0 and iOS 26.0.** Every reference compiles its
  snippets at that deployment target.
- **Gate every OS 27 symbol with `#available(macOS 27, iOS 27, *)`, and keep
  the 26 path beside it.** Examples are the throwing AVAudioEngine `connect`,
  the iOS 27 audio-session interruption notifications, the Swift `DTLS` type,
  and the LZMESH and LZRAVEN codecs.
- **The compiler does not catch every OS 27 symbol.** `COMPRESSION_LZMESH` and
  `COMPRESSION_LZRAVEN` compile at 26.0 with no warning, because the header
  gives their availability in a comment. Gate them yourself.

Rules that always apply:
- **A Developer ID build cannot use Game Center,** In-App Purchase, or Sign in
  with Apple. Decide how the Mac build ships before you write GameKit code:
  `references/game-center-and-online.md`.
- **Run the simulation in fixed steps and render at the rate the display
  grants.** Take time from `targetTimestamp` (`CADisplayLink`) or
  `targetPresentationTimestamp` (`CAMetalDisplayLink`), never from a nominal
  60 or 120 Hz. Cap the steps per frame, so that a stall slows the game
  instead of freezing it in catch-up.
- **Ship on `CAMetalDisplayLink` on a dedicated render thread, and set that
  thread's QoS to `.userInteractive` before `start()`.** A new `Thread` runs
  at `.default` (runtime-checked). Do not run the frame loop in a Swift
  `Task`.
- **A game cannot create an interval workgroup for its render or simulation
  loop.** Only audio has interval workgroups. Never join a game thread to the
  audio device's workgroup.
- **Read gameplay input through Game Controller.** Use AppKit or UIKit only
  for typed text, the cursor position, and other input that Game Controller
  does not model. Every Mac has a keyboard and a pointing device; a controller
  is optional on every platform here.
- **The audio render callback is real-time code.** No allocation, no file
  I/O, no locks, and no Swift or Objective-C runtime calls while it renders.
  Write the kernel in C or C++.
- **Game Mode needs `LSSupportsGameMode` in a hand-written Info.plist.** Xcode
  27.1 writes only the old `GCSupportsGameMode` key.
- **Spell names from the references or the SDK, not from memory.** The SDK
  wins over a doc page or an Apple sample. The references record each
  disagreement that they found.
- **Where a workflow is GUI-only, it is GUI-only.** Game Progress Manager, the
  capability editor, the Metal Performance HUD's Game Mode indicator, and a
  VoiceOver pass have no command-line form. Do not invent a flag. Give the
  user the exact menu path. Background Assets packaging does have one:
  `xcrun ba-package` and `xcrun ba-serve`.
- **Measured claims come from one machine.** The references label each one
  as runtime-checked. The machine was an M4 Pro MacBook Pro with macOS
  27.0.1 installed. Core Haptics reports no haptics support on it, despite its
  Force Touch trackpad. Measure again on a new OS or device before you depend
  on such a claim.
