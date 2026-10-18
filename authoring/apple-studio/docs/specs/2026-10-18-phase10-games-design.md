# apple-studio Phase 10: Game development on Metal — design

Phase spec under the standing charter
(`docs/specs/2026-08-03-apple-studio-design.md`). Decisions taken 2026-10-18;
this doc is the input to the Phase 10 implementation plan.

Register: spec prose (engineer audience). Terms follow CONVENTIONS.md. Paths
are relative to `authoring/apple-studio/` unless they start with `plugins/`.

## Goal

Teach the plugin to help someone build a game on Apple platforms with their
own engine, written directly against Metal. Two new skills carry it:

- `apple-metal` — the GPU: Metal 4 and its Metal 3 fallback, the Metal
  Shading Language, passes and pipelines, resources and memory, Apple's
  tile-based GPUs, display and upscaling, GPU debugging and profiling, and
  driving Metal from C++ and Rust.
- `apple-games` — everything around the renderer: the frame loop and
  threading, input, audio and haptics, Game Center and saves, assets, and
  Apple's design guidance for games.

Two existing skills are extended rather than duplicated: `apple-performance`
(the CPU side of a frame) and `app-release` (distribution outside the App
Store).

Version bump to 0.11.0. Tag `apple-studio-v0.11.0`.

### Origin

A user request on 2026-10-18, not the charter's long tail. Like Phase 9, it is
on-demand work. The request supplied:

- About 50 developer.apple.com pages: Metal, MetalFX, MetalKit, QuartzCore,
  AppKit, Game Controller, Dispatch, workgroups, the Apple-silicon porting
  guide, AVFAudio, AudioToolbox, PHASE, Accelerate, Compression, Model I/O,
  MPS, MPSGraph, Network, GameKit, logging, Core Haptics, Uniform Type
  Identifiers, the HIG page *Designing for games*, 17 Metal tooling pages,
  5 CPU-profiling pages, and 4 build-and-ship pages. The full list, with each
  page's probe result, is `records/2026-10-18-phase10-games/survey/seed-probe.tsv`.
- The Metal Shading Language specification (PDF). The user supplied a copy
  in `~/Downloads/`. It is byte-identical to the survey's download of the
  published URL (`survey/metal-toolchain.log`).
- The *Metal Feature Set Tables*, added by the user on the same day, as a PDF
  (18 pages, dated May 21, 2026) and as a Numbers spreadsheet of the same
  tables. Both are in `~/Downloads/`.
- The `metal-by-tutorials` book skill, at
  `~/Projects/book-skills/.agents/skills/metal-by-tutorials/` (*Metal by
  Tutorials*, 5th ed., Begbie and Horga).
- An instruction to read all of it thoroughly, without skimming. That
  instruction is a requirement of this phase, not a style note. See
  "Reading discipline".

The charter's long-tail list is unchanged. ML remains its one outstanding
item. The phase record notes this, and no charter amendment is needed.

## Decisions (user-approved 2026-10-18)

| Question | Decision |
|---|---|
| Who it serves | Generic. No specific game. The reader builds their own engine directly on Metal, not on SpriteKit, SceneKit, RealityKit, or a third-party engine. |
| Language | **Swift first.** C++ and Rust are covered too, where they differ from Swift. |
| Platforms | **Mac first.** iPhone and iPad are covered too. |
| Hardware and OS floor | **Apple silicon only** (answered after the builder check). Metal 4 is the default voice. Metal 3 gets one gating section, not a second path. Intel Macs and their discrete GPUs are out of scope. |
| Notarization evidence | **Yes**: notarize the probe for real (R6), with a stop for the user to confirm the team before anything is submitted. |
| Scope | The playback approved in conversation: rendering, frame loop and threading, input, audio, haptics, Game Center, assets, GPU debugging and profiling, CPU profiling of the simulation, distribution outside the App Store, and the HIG for games. |

These choices in the approved playback were Claude's calls, and the user
accepted them along with the rest:

- Metal 4 is the default voice where the hardware supports it, with Metal 3
  as the fallback.
- The book supplies technique, and Apple's docs supply the current API.
- CPU profiling and signing extend `apple-performance` and `app-release`
  instead of moving into a game skill.
- General rendering theory stays out of scope.

## What the survey established

Evidence root: `records/2026-10-18-phase10-games/survey/`.

### Finding 1 — Apple serves Markdown at `.md`; the pipeline's premise is stale

All 50 seeds return `200 text/markdown` when `.md` is appended to the
documentation URL, and so do 1,148 of the 1,180 pages they link
(`toolchain.log`, last line). The 32 misses were the survey's own regex
truncating symbol URLs at `)`. That is the artifact Phase 6 recorded
(`docs/specs/2026-09-02-phase6-intelligence-performance-design.md`, Verification
results item 3), and it recurred here.

CONVENTIONS.md and `pipeline/docc.py` both say developer.apple.com serves a
JavaScript shell, so content must come from the DocC JSON. That is no longer
the only route. The `.md` body carries a JSON metadata comment
(`documentType`, `role`, availability), the prose, and topic links as
Markdown links.

**`WebFetch` is not a read.** Its own tool description says it answers a
prompt against the page "using a small fast model". What comes back is a
summary written by another model. Under this phase's reading rule, a page
fetched with `WebFetch` counts as unread.

### Finding 2 — the reading corpus is about 770K words

Measured by crawling articles, collections, and sample-code pages from the
seeds inside each seed's framework path (`corpus-size.tsv`):

| Source | Size |
|---|---|
| Bounded doc corpus | 909 article-type pages, 622,615 words |
| — of which Metal | 203 pages, 184,176 words |
| — Xcode tooling pages (seed + linked pages) | 128 pages, 159,588 words |
| — HIG (seed + linked pages) | 30 pages, 59,234 words |
| — AppKit / AudioToolbox / GameKit / Network | 116 / 253 / 35 / 29 pages |
| MSL specification 4.1 | 383 pages, 97,341 words (`pdftotext`) |
| Metal Feature Set Tables | 18 pages, 6,587 words (`pdftotext`) |
| `metal-by-tutorials` skill | 31 chapters plus glossary, patterns, cheatsheet: 52,602 words |

The Xcode and HIG seeds are bounded at depth 1. Unbounded, they pull in the
whole Xcode documentation and the whole HIG: 934 articles and 1.09M words.
Symbol pages (773 at the first level alone) are outside the corpus. They come
in only through the claim rule in "Reading discipline".

### Finding 3 — the docs are Metal 4-first; the book stops at Metal 3

The Metal hub's Essentials section opens with *Understanding the Metal 4 core
API* and *Drawing a triangle with Metal 4*. The installed macOS SDK ships 31
`MTL4*` headers, including `MTL4CommandQueue`, `MTL4CommandAllocator`,
`MTL4ArgumentTable`, `MTL4Compiler`, and `MTL4MachineLearningCommandEncoder`.
This Mac is an M4 Pro that reports "Metal Support: Metal 4"
(`toolchain.log`). The book skill states that it does not cover Metal 4.

The Feature Set Tables set the gate. The Metal 3 programming model (the
combined Metal 1–3 API) is available on every Apple GPU family. The Metal 4
programming model starts at **Apple7**: A14 and M1, and later. Some Metal 4
features start later, for example placement sparse resources at Apple8 and
address-driven acceleration-structure builds at Apple9. M4 is Apple9, and A19
and M5 are Apple10.

Consequence: book technique (shadows, deferred shading, particles, skinning)
is sound, but its API spelling is Metal 3. Every book-derived API claim must
be re-expressed against the live Metal 4 docs, or labelled as the Metal 3 path.

### Finding 4 — the shader compiler is a separate download, now installed

At survey time, `xcrun metal` exited with "missing Metal Toolchain; use:
xcodebuild -downloadComponent MetalToolchain" (`toolchain.log`). Xcode 27
ships the shader compiler as a separately downloaded component of about
839 MB.

**Resolved the same day, at the user's request.** Metal Toolchain 27A266a
(`metal` 32023.921) is installed. A valid kernel compiles under
`-std=metal3.2`, `metal4.0`, and `metal4.1`. An invented identifier fails with
"use of undeclared identifier" (`metal-toolchain.log`). The MSL gate is
therefore viable on this machine. The plan does not install it again, but
CONVENTIONS.md records the download as a prerequisite for anyone rerunning
the pipeline.

### Finding 5 — the hardware can run every tool on the list

| Tool | Requirement | This machine |
|---|---|---|
| GPU performance heatmaps, shader cost graph | A17 / M3 or later | M4 Pro |
| Processor Trace | M4 or later | M4 Pro |
| `gpudebug` | — | `/usr/bin/gpudebug` |
| `xctrace` templates | — | Game Performance, Game Performance Overview, Game Memory, Metal System Trace, Processor Trace, CPU Counters, Audio System Trace |
| `notarytool`, `stapler`, `codesign` | — | present |
| Rust | — | rustc and cargo 1.97.1 |
| C++ | — | Apple clang 21. CMake is not installed. |

Xcode 27.1 (27A9275) is selected, with macOS SDK 27.0 and iPhoneOS SDK 27.1.

### Finding 6 — the binding landscape for C++ and Rust

- **Rust:** `objc2-metal` 0.3.2 exposes 81 `MTL4*` items, including
  `MTL4CommandQueue`, `MTL4CommandAllocator`, and `MTLResidencySet`. The older
  `metal` crate (0.33.0) carries a README deprecation notice that points to
  `objc2` and `objc2-metal`. `objc2-quartz-core` and `objc2-game-controller`
  exist at 0.3.2.
- **C++:** metal-cpp is Apple's header-only C++ interface. It follows Cocoa
  ownership rules without ARC, and is a download, not part of the SDK. The
  survey did not resolve a download URL, because the page builds its links in
  script.

### Finding 7 — what the plugin already covers

- `apple-performance/references/profiling-workflow.md` already cites all five
  CPU-profiling pages on the list. `responsiveness-hangs-and-hitches.md`
  cites *Understanding hitches*, and `memory-power-and-size.md` cites
  *Reducing your app's memory use*. All three files are `verified: 2026-09`.
  `apple-performance/SKILL.md` currently declares Metal graphics out of
  scope.
- `app-release` has almost no Developer ID coverage: "notar" or "Developer
  ID" appears at most 4 times in any of its references. `apple-macos`'s
  `mac-sandbox-and-files.md` covers the hardened runtime, but not the
  notarization workflow.
- `apple-animations` owns SwiftUI's Metal shader-effect modifiers
  (`colorEffect` and related). That stays put.
- `framework-catalog.md` already lists Game Controller, GameKit, GameplayKit,
  GameSave, MetalFX, PHASE, and Touch Controller.

### Finding 8 — Apple's own map of game technologies names pages the list omits

`documentation/TechnologyOverviews/games-technologies` (1,500 words) is
Apple's index for games. It points to sources the request did not list:

- Touch Controller (on-screen controls for Metal games on iPhone and iPad).
- Background Assets (downloading large game assets).
- *Tuning your code's performance for Apple silicon* (QoS and thread
  scheduling).
- *Addressing architectural differences in your macOS code*.
- *Tailor your apps for Apple GPUs and tile-based deferred rendering*.
- *Notarizing macOS software before distribution* and the hardened runtime.
- iCloud game saves.

## Shape: two new skills, two extended

Three shapes were considered. This is Claude's call, recorded here for the
user to check.

| Shape | For | Against |
|---|---|---|
| **One skill, `apple-games`** | One trigger. No routing contest between two new skills. | A Metal compute or visualization question from a non-game app would have to load a "games" skill. The routing list would carry about 13 references. |
| **Two skills, `apple-metal` + `apple-games`** (chosen) | Metal serves non-game apps too: compute, visualization, custom SwiftUI rendering. The split runs where the work splits, between the GPU and everything around it. It also gives a clean phase seam. | Two descriptions have to be tuned against each other. "My game stutters" could route to either one. |
| **Three or more skills** (Metal, Metal tooling, games) | Tighter triggers. | The same reader authors and debugs Metal. The kill-switch record shows 11 skills with no genuine use so far, and every added skill costs context in every session. |

The two-skill split also resolves the stutter case: each SKILL.md names the
symptom split explicitly. GPU frame time belongs to `apple-metal`. CPU tick
cost belongs to `apple-performance`. Frame pacing and display-link scheduling
belong to `apple-games`. Each file carries a one-line cross-reference to the
others.

**Naming.** CONVENTIONS.md gives platform and tooling skills plain names with
the `apple-` prefix. Neither name collides with a skill elsewhere in the
catalog: the `godot` plugin's skills are `godot-*`.

## Deliverables

### 1. New skill `plugins/apple-studio/skills/apple-metal/`

A lean SKILL.md (triggers, routing, the Metal 4-or-3 decision), plus
`evals/triggers.md` and references. Proposed references, one per decision
area:

1. `command-model.md` — the device, queues, the Metal 4 command allocator and
   command buffer model, argument tables, residency sets, synchronization
   (barriers, fences, events, shared events), and frames in flight. The
   Metal 3 path gets one section under `## Maintaining older code: Metal 3`.
   It covers when that path applies (GPU families below Apple7 and OS
   releases before Metal 4), how to gate at runtime, and where the two
   models' concepts map onto each other. It is not a second copy of the
   guidance.
2. `pipelines-and-render-passes.md` — compiling pipelines (the Metal 4
   compiler, function constants and specialization, pipeline archives and data
   sets, avoiding compile hitches), render passes, load and store actions,
   attachments, depth and stencil, MSAA, and forward against deferred.
3. `apple-gpu-tbdr.md` — how Apple GPUs differ: tile memory, memoryless
   targets, imageblocks, tile shaders, raster order groups, hidden-surface
   removal, and the porting guidance for code written for discrete GPUs.
4. `resources-and-memory.md` — buffers, textures, heaps, storage modes,
   sparse and placement resources, resource streaming (the IO command queue),
   texture compression, purgeability, and budgeting unified memory against the
   CPU-side simulation.
5. `shading-language.md` — MSL 4.1: address spaces, attributes, function
   kinds, SIMD-group and quad-group functions, threadgroup memory, precision
   and `half`, and the version and family gates on language features.
6. `compute-and-gpu-driven.md` — compute passes and dispatch sizing, indirect
   command buffers and GPU-driven rendering, mesh and object shaders,
   acceleration structures and ray tracing, when to reach for MPS or MPSGraph,
   and machine-learning passes at the level of "what exists and when".
7. `display-and-upscaling.md` — `MTKView` against `CAMetalLayer` against
   `CAMetalDisplayLink`, drawable acquisition and presentation, HDR/EDR and
   color spaces, and MetalFX (every mode the live docs list).
8. `gpu-debugging-and-profiling.md` — the Metal debugger, programmatic
   capture, `gpudebug` and Apple's agent workflow, API and shader validation,
   the Metal Performance HUD, Metal System Trace, counters, heatmaps, the
   shader cost graph, and the memory and dependency viewers. It states which
   steps are GUI-only.
9. `cpp-and-rust.md` — metal-cpp (setup, ownership, autorelease pools) and
   `objc2-metal` (types, unsafety, feature flags). Also how an external build
   (cargo, CMake, make) is hosted in Xcode through an External Build System
   target or a scheme, so that Instruments and GPU capture attach, and how to
   capture outside Xcode.

The builder may merge or split these after the reading, within six to ten
files, under CONVENTIONS.md's rule of one file per decision area. A merge or
split is recorded in the phase record with its reason.

### 2. New skill `plugins/apple-studio/skills/apple-games/`

A lean SKILL.md, plus `evals/triggers.md` and references:

1. `game-loop-and-threading.md` — hosting a Metal view in SwiftUI and AppKit
  (and UIKit on iPhone and iPad), the frame loop on the display link, fixed
  simulation steps against variable rendering, QoS, `os_workgroup`, Dispatch,
  thermal and power state, Game Mode on macOS, full screen, and the cursor.
2. `input.md` — Game Controller (controllers, `GCKeyboard`, `GCMouse`,
   physical input profiles, controller haptics), Touch Controller on iPhone
   and iPad, AppKit events where Game Controller does not reach, and remapping.
3. `audio-and-haptics.md` — AVAudioEngine and the audio session, PHASE
   spatial audio, AudioToolbox where it is still the right layer, real-time
   audio-thread rules, and Core Haptics.
4. `game-center-and-online.md` — GameKit (authentication, the access point,
   achievements, leaderboards, matchmaking, real-time and turn-based play),
   iCloud saves, and the Network framework for custom multiplayer.
5. `assets.md` — Model I/O and USD, Compression, Uniform Type Identifiers for
   custom asset and save types, Background Assets, and where texture
   compression decisions hand off to `apple-metal`.
6. `game-design.md` — the HIG page *Designing for games* and every HIG page it
   links: controls, Game Center presentation, onboarding, and platform
   expectations on Mac, iPhone, and iPad.

The same merge and split latitude applies, within four to seven files.

### 3. Changes to existing skills

- **`apple-performance`.** `SKILL.md` drops "Metal graphics" from its
  out-of-scope line and routes GPU work to `apple-metal`.
  `profiling-workflow.md` gains game-frame CPU profiling: the Game Performance
  and Game Memory templates, per-frame signposts, reading a slow tick with
  Processor Trace, and the Apple-silicon CPU guidance in *Addressing CPU
  bottlenecks*. The five CPU pages and *Understanding hitches* are re-read in
  full for this phase. A file is re-stamped `verified: 2026-10` only if this
  phase edits it.
- **`app-release`.** New reference `direct-distribution.md`: Developer ID
  certificates, the hardened runtime, `notarytool` and `stapler`, DMG, zip, and
  pkg packaging, and what Gatekeeper checks. It also covers capabilities
  outside the Mac App Store (Game Center, iCloud) with their provisioning
  profiles, and targeting the Mac App Store at Apple silicon only. `SKILL.md`
  gains a routing line for it.
- **One-line cross-references** in `apple-design` (to `game-design.md`),
  `apple-macos` (hosting a Metal view and Game Mode), `xcode-loop` (external
  build systems), and `apple-animations` (SwiftUI shader modifiers stay there,
  and engine shaders go to `apple-metal`).
- `framework-catalog.md` is regenerated in Task 0 and not hand-edited.

### 4. Pipeline changes

- **`.md` route.** Document `<doc URL>.md` as the primary fetch route in
  CONVENTIONS.md, with `docc.py` kept as the fallback and for `--children`.
  Whether `docc.py` gains an `--md` mode is left to the builder.
- **Corpus manifest.** A committed script,
  `pipeline/crawl_corpus.py`, regenerates the bounded corpus from the seed
  maps deterministically, using the rule in Finding 2, and writes a
  manifest with one row per page: path, `documentType`, `role`, and word
  count. The survey's crawler is the prototype. Its link regex must not
  truncate at `)`.
- **Compile gates for three more languages** in `typecheck_snippets.py`
  (or sibling scripts, as the builder prefers):
  - ` ```metal ` blocks compile with `xcrun metal` at the MSL version the
    reference declares.
  - ` ```cpp ` blocks compile with `clang++ -fsyntax-only` against metal-cpp
    headers fetched to a cache outside the repository.
  - ` ```rust ` blocks compile with `cargo check` in a scratch crate that pins
    `objc2-metal` and its siblings to the versions the reference declares.

  Swift snippets in `apple-metal` and `apple-games` compile at the Metal 4
  OS floor, not at the SDK default. The floor is the earliest macOS and iOS
  release on which the live docs list `MTL4CommandQueue`, read during the
  phase rather than assumed. At the SDK default (macOS 27), an availability
  error against the floor would pass unseen. Metal 3 snippets under the
  "Maintaining older code" heading carry their own lower target.

  Each gate has an offline self-test in the style of
  `test_typecheck_snippets.sh`, including a deliberately invented symbol that
  must fail. A header directive per file, in the style of
  `> typecheck: ios <version>`, declares the MSL version and the crate
  versions.
- **Seed maps** `pipeline/maps/apple-metal-live.md` and
  `pipeline/maps/apple-games-live.md`, holding the request's 50 seeds plus the
  Finding 8 additions. Adding those is Claude's call, made because Apple's own
  index names them.
- **Crawl bound for the Finding 8 additions (Claude's call).** Touch
  Controller is a game framework and is crawled recursively, like Game
  Controller. Every other addition is crawled at depth 1, meaning the page
  itself and the pages it links, as the Xcode and HIG seeds are. Recursing
  into `documentation/security` or Background Assets would pull in whole
  frameworks that games touch at one point. The manifest records the bound
  applied to each seed.

### 5. Runtime probe `pipeline/fixtures/metal-probe/`

A small Swift executable that renders a Metal 4 frame offscreen and runs one
compute pass. It also captures a GPU trace programmatically to a file. The
probe exists to check behavioral claims, not to demonstrate. The plan names
each claim it checks (R1, R2, …) before the probe is written. At minimum:

- R1: the documented Metal 4 frame structure runs as the reference describes
  it.
- R2: programmatic capture writes a trace that `gpudebug` can open and
  query, following *Investigating GPU issues with AI agents*.
- R3: `xctrace record` with Metal System Trace and with Game Performance
  captures the probe, and `xctrace export --toc` confirms what was recorded.
- R4: a deliberately slow simulation tick is found with Processor Trace on
  this M4 Pro.
- R5: one frame each from a minimal C++ (metal-cpp) host and a minimal Rust
  (`objc2-metal`) host, launched from an Xcode scheme or External Build
  System target, so that capture attaches to a binary Xcode did not build.
- R6: the probe goes through direct distribution end to end. It is signed
  with a Developer ID Application certificate and the hardened runtime,
  submitted with `notarytool submit --wait`, stapled with `stapler`, and
  assessed with `spctl --assess`. The notarization log is kept in the
  record. R6 has two user steps:
  - **Before R6:** the user creates a Developer ID Application certificate
    and stores notarization credentials with `xcrun notarytool
    store-credentials`. Today this machine holds only an *Apple Development*
    certificate, for team `RTC3TK2XFJ`. The builder
    does not assume that is the team to ship under.
  - **Before any submission:** the builder lists the signing identity's
    team ID and name, states which team it is about to submit under, and
    waits for the user to confirm. A submission sends a binary to Apple, so
    it is an external write.

A claim that cannot be checked at runtime ships with a "not runtime-checked"
marker, as in Phase 9.

### 6. Trigger evals

Each new skill gets should-fire and should-not rows. The should-not rows cover
SwiftUI shader modifiers (`apple-animations`), app-level slowness
(`apple-performance`), a SpriteKit or Godot question, and general rendering
theory. Each prior skill gets one should-fire and one should-not regression
row. Every changed description is re-run against its neighbours. Runs go
through `pipeline/run_evals.py`.

Deferred item 6 showed that prompts naming code the fixture lacks ("this
renderer") make sessions answer blind rather than load the skill. The builder
chooses one of two fixes: seed StudioFixture with a Metal view and a frame
loop, or phrase rows as how-to questions. The record states which one was
used.

### 7. CONVENTIONS.md amendments

- Stack baseline: Metal guidance is Swift first, with C++ and Rust covered
  where they differ. Snippets in those languages are allowed, and each one is
  compile-gated.
- Scope boundary: rendering and engine code are native correctness, so they
  are in scope. Custom visual design and art direction stay out.
- Pipeline tooling: the `.md` route, the rule that `WebFetch` is not a read,
  the corpus manifest, and the three new compile gates.
- The same `.md` correction in `.claude/rules/apple-studio.md`, whose first
  bullet repeats the "JavaScript shell" claim, and in the `docc.py` docstring.

### 8. Release and records

- `plugin.json`: 0.10.0 → 0.11.0. The description gains game development on
  Metal, and the keywords gain `metal` and `games`.
- `plugins/apple-studio/README.md` component rows, and the catalog README row
  (`bun run audit` checks that every shipped skill is listed in it).
- `docs/deferred.md`: new items for every claim not checked at runtime and
  for any corpus page that could not be fetched.
- Phase record: `records/2026-10-18-phase10-games/`.

## Reading discipline

The request said to read thoroughly, without skimming. This section makes
that checkable.

1. **Every page in the corpus manifest is read in full by a distiller.** A
   page is read when its raw text, fetched by `.md` or `docc.py` into a local
   file, has been loaded completely with the Read tool. A `WebFetch` result
   does not count (Finding 1).
2. **Slices fit in context.** Each distiller gets a slice small enough to read
   without compaction. A summary written by compaction is a skim. The plan
   sizes the slices; about 60K words each is the working figure.
3. **A read ledger records coverage.** Each distiller writes one row per page:
   path, words, read in full (yes or no), and what it fed (reference and
   section), or "nothing distilled" with the reason. The phase does not close
   until the ledger has a row for every manifest row and every row reads
   "yes". Ledgers are committed in the record. They hold summaries, never
   Apple's or the book's text.
4. **The MSL specification is read in full, chapter by chapter,** from
   `pdftotext` output kept outside the repository.
5. **The Feature Set Tables are read in full.** Every claim in a reference
   about GPU family, programming model, or a per-family limit cites its table
   by name. Where `pdftotext` garbles a cell (footnote markers can fuse with
   values), the Numbers file is the cross-check. The builder exports it to CSV
   outside the repository.
6. **The book skill is read in full:** all 31 chapters, the glossary,
   patterns, and cheatsheet. Every book claim that names an API is checked
   against the live docs (Finding 3). Docs win, per CONVENTIONS.md.
7. **Symbol pages come in through claims.** Any symbol a reference makes a
   behavioral claim about has its symbol page read in full. Its use in a
   snippet must also compile.
8. **No API name ships from memory.** If a symbol is not in a fetched page and
   the shipped SDK, it does not go in a reference. This is the Phase 6
   staleness stance, and it binds harder here: Metal 4 is newer than most
   priors.

## Opening task: phase sweep

1. Kill-switch measurement since 2026-09-30, per `docs/deferred.md` item 1.
   Record the number. The precondition is still unmet unless a shipped real
   feature says otherwise.
2. Regenerate `framework-catalog.md` and record what was added and removed.
3. Verified-header check on every existing file this phase edits.

## Sequence and the external dependency

Order: pipeline (manifest, `.md` route, compile gates) → reading and
distillation in parallel slices → write references → compile → runtime probe
→ existing-skill changes → evals → gates → release.

**The Metal Toolchain is installed** (Finding 4). No install task remains.

**What the builder may install or fetch unattended (Claude's call):**
- Network reads are fine: Apple doc pages, the metal-cpp download, and
  crates.io. Caches live outside the repository.
- No new system packages. CMake is not installed, and it is not needed: the
  C++ gate and R5's C++ host build with `clang++` directly.
  `cpp-and-rust.md` may describe CMake from the docs, and it marks any CMake
  step as not runtime-checked.
- If Processor Trace (R4) needs a system setting turned on, that is a user
  checkpoint. The builder stops, names the setting, and waits. It does not
  look for a workaround.

**Seam and the checkpoint (Claude's call).** This phase is larger than
Phase 6, which was the largest so far. It has one named checkpoint: the
moment `apple-metal`'s references pass every compile gate and R1–R3. There the
builder stops and asks the user one question: continue to `apple-games`, or
ship `apple-metal` and the pipeline as 0.11.0 and carry `apple-games`, with
the `apple-performance` and `app-release` changes, to a Phase 11 at 0.12.0.
The builder does not make that call alone.

**Branch.** The work happens on its own branch, in a worktree cut from
`main`. The current `add-crossover-plugin` checkout has unrelated uncommitted
work (the `rust` plugin, `book-to-skill`) that this phase must not touch or
commit. The survey files already written under `records/` move with the
phase.

## Verification (definition of done)

- The read ledger covers every manifest row with "read in full: yes". The one
  exception is a page that will not fetch (non-200 after a retry, and after
  the disambiguated URL from its parent's links is tried). Its row reads "no,
  unfetchable: <status>" and names a `docs/deferred.md` item. It blocks the
  close only if a shipped claim depends on it (Claude's call).
- `typecheck_snippets.py` (and the new gates) report every Swift, MSL, C++,
  and Rust block clean in every reference this phase writes or edits. Each
  gate's invented-symbol self-test fails as it should.
- R1–R6 each carry runtime evidence or the "not runtime-checked" marker.
- Trigger evals run through `pipeline/run_evals.py`, as in Phase 9 (Claude's
  call on the bar):
  - One baseline sweep, plus one more sweep after any description edit.
  - Every row on the two new skills passes.
  - A prior skill's row must not regress from its last recorded verdict.
  - A description edit that regresses a previously passing row is reverted.
  - The rows `docs/deferred.md` item 13 already records as open (for example
    `nofire-1`) are reported and do not gate.
  - `git -C ~/Projects/StudioFixture status --porcelain` is empty at close.
- `bun test` and `bun run audit` pass. `bun run audit --since main` reports
  no unbumped change.
- `claude plugin validate . --strict` passes. The plugin loads under
  `--plugin-dir`, and both new skills appear.
- No simulator is left booted, and no probe process is left running.

Evidence pointers use `<file>:<line-range>`, per CONVENTIONS.md.

## Out of scope

- **Engines and high-level frameworks:** SpriteKit, SceneKit, RealityKit,
  GameplayKit, Unity, Unreal, and Godot (which has its own plugin).
- **visionOS and Compositor Services.** Mac first, then iPhone and iPad.
- **Intel Macs and discrete GPUs.** The floor is Apple silicon (Decisions).
  `apple-gpu-tbdr.md` describes Apple GPUs only.
- **General rendering theory**, engine architecture, and game physics. The
  references carry Apple-specific judgment, not textbook graphics.
- **Porting Windows games** (Game Porting Toolkit, Metal shader converter).
- **Art direction and visual design**, per the scope boundary.
- **Apple Arcade** and App Store product-page marketing.
- **tvOS.** Several of the frameworks support it, but it is not a requested
  platform.

## Left to the builder

- The final reference boundaries, within the ranges in Deliverables 1 and 2.
- Slice sizes and how many distillers run.
- Whether the new compile gates extend `typecheck_snippets.py` or sit beside
  it.
- Whether `docc.py` gains an `--md` mode.
- The eval fixture approach (Deliverable 6).
- Where metal-cpp's headers are cached.
