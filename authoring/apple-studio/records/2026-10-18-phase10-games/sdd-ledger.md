# SDD ledger — plan: authoring/apple-studio/docs/plans/2026-10-18-phase10-games.md

> Copied from the ignored SDD workspace at the phase close (ruling P2). Apple ID email addresses are redacted (ruling P51); the team IDs stay.

Spec: authoring/apple-studio/docs/specs/2026-10-18-phase10-games-design.md
Worktree: .claude/worktrees/apple-studio-phase10-games, branch apple-studio-phase10-games, base 838ccda.
Baseline: bun test 542 pass / 0 fail (2026-10-18).

## Pre-flight scan

### Shared files and interfaces, by task pair

| Tasks | Produces → consumes | Finding |
|---|---|---|
| T0 → T6, T13 | `$REC/README.md` created → appended | consistent |
| T0 header check → T9, T10, T11, T5, T8 | `headers.log` → re-stamp only when edited | T0 Step 4 list omits `apple-frameworks/SKILL.md` (T11 edits it). Ruling P5 |
| T1 → T3, T4, T7, T13 | `manifest.tsv` columns, `key()` cache naming → sources.tsv, the reader brief, check_ledger | consistent. Seed table assigns all 50 seed-probe rows (core 9, useful 13, tooling 17, design 1, cpu 5, gpu 1, ship 4) |
| T2 → T5, T6, T8, T9, T10, T13 | directive grammar, `device` binding, the native gate's fence allowlist → every reference | Allowlist lacks config fences (`toml` for Cargo.toml in cpp-and-rust, `xml`/`plist` for Info.plist keys). Ruling P3 |
| T2 Step 4 → T9 Step 4, T13 Step 2 | `catalog-before.log` → no PASS→FAIL | consistent |
| T3 → T4, T7, T13 | slices ≤60K words, ledger format, check_ledger args | A single source row (an MSL chapter) could exceed 60K. Ruling P6 |
| T4 → T5 | notes sections named for the nine apple-metal files | consistent with T5 and spec Deliverable 1 |
| T5 → T6 | `command-model.md § Frame structure`; gpudebug commands in `gpu-debugging-and-profiling.md`; `cpp-and-rust.md` snippets | consistent |
| T5, T8 → bun test | new skill names → `tests/security-evals.test.ts` (every skill is a decoy or an acknowledged omission) | Plan never adds them to `plugins/security/skills/reviewing-code-security/evals/manifest.json`. Ruling P4 |
| T5, T8 → T13 | README component rows and skills column → T13 rewrites summary only | consistent |
| T6 → T9 | `MetalProbe sim --ticks <n> [--slow]`, `plantedSlowStep()` | consistent |
| T6 → T10 | release MetalProbe → `bundle.sh` | consistent |
| T7 → T8, T9, T10 | notes sections: six apple-games files, `profiling-workflow.md` (p01), `direct-distribution.md` (r01) | consistent |
| T10 → T12 | app-release description change → full app-release triggers in prompts.tsv | consistent |
| T13 | plugin.json description = marketplace description (bun test checks identity) | consistent: T13 changes both |

### Each task against itself

| Task | Finding |
|---|---|
| T0 | Step 1 (worktree, move files) done by the controller in setup. Ruling P1. Step 6 omits `claude plugin validate . --strict`, which Global Constraints require for commits touching plugins/. Ruling P5 |
| T1 | tests (6) match the functions specified; Files lists every artifact |
| T2 | Step 2's expectation (existing cases pass except the re-patterned bad-directive) matches Step 1 |
| T3 | 6 tests named match check_ledger's contract |
| T4 | Execution is a parallel fan-out; SDD forbids parallel implementers. Ruling P7 |
| T5 | Files block omits the README files that Step 9 commits (Step 7 adds them). Same fan-out as T4. Ruling P7 |
| T6 | Step 9 checkpoint is a spec-mandated stop. Ruling P8 |
| T7, T8 | same shape as T4, T5. Ruling P7 |
| T9 | R4 may need a user-enabled setting: planned stop. Ruling P8 |
| T10 | notarytool submit is an external write: planned stop after the user confirms the team. Ruling P8 |
| T11, T12 | consistent |
| T13 | tag is local; push/PR wait for the user. Ledger copy into the record. Ruling P2 |

### Rulings

- P1. Ruling: Task 0 Step 1 was done by the controller during setup (EnterWorktree from origin/main 838ccda, branch renamed to apple-studio-phase10-games, spec/plan/survey copied and verified byte-identical with cmp/diff, the session-created originals deleted from the main checkout). The Task 0 implementer verifies instead of redoing it — the worktree must exist before any implementer runs — costs nothing if wrong; the state is checkable.
- P2. Ruling: briefs, reports, and review packages stay in this git-ignored SDD workspace; at Task 13 this ledger is copied to `$REC/sdd-ledger.md`, as Phase 9 did — CONVENTIONS.md forbids relying on `.superpowers/` for the phase record — if wrong, one extra committed file.
- P3. Ruling: the native gate's allowlist of ungated fences also accepts the config/data fences `xml`, `json`, `toml`, `plist`, `yaml`, `cmake`, `makefile`; any other unknown fence (objc, c, msl, …) still exits 2 — they are configuration, not code in a gated language, and cpp-and-rust needs Cargo.toml — if wrong, a wrong config snippet ships unchecked; R5 and R6 run real configs, which limits that.
- P4. Ruling: Tasks 5 and 8 add `apple-metal` / `apple-games` to `acknowledgedOmissions` in `plugins/security/skills/reviewing-code-security/evals/manifest.json`, alphabetically — `tests/security-evals.test.ts` fails otherwise, and the rust plugin commit set the precedent — costs nothing if wrong.
- P5. Ruling: Task 0's header check also records `apple-frameworks/SKILL.md` and `plugins/apple-studio/README.md`; Task 0's commit also runs `claude plugin validate . --strict` — Global Constraints bind every plugins/ commit — costs nothing.
- P6. Ruling: a source row over 60,000 words is split in sources.tsv into page-range rows (`pdf:msl-4.1#ch<N>-p<a>-<b>`) so every slice stays within the cap — the cap exists so a reader never reads through compaction — if wrong, more ledger rows.
- P7. Ruling: in Tasks 4, 5, 7, and 8 the controller dispatches the plan's readers/writers in parallel. Each writes only its own files (ledger/<ID>.tsv + notes/<ID>.md, or one reference file) and never commits. One finisher implementer then runs the task's remaining steps and commits, and the task review follows. SDD's no-parallel rule exists to prevent file conflicts, and these outputs are disjoint — if wrong, shared $TMP caches contend (cargo serializes on its lock); no committed file conflicts.
- P8. Ruling: the spec-mandated checkpoint (Task 6 Step 9) and the planned user steps (Task 9 setting, Task 10 certificate and team confirmation) are honored as stops — the spec is binding, and notarization is an external write — the cost is waiting time.
- P9. Ruling: models — T0–T3 code and bookkeeping on sonnet; readers and writers on opus (the distillation is the product); T6, T9, T10 probe work on opus; task reviewers sonnet by default, opus for reference-content reviews; final whole-branch review on opus — cost if wrong: spend.

## Progress
Task 0: dispatched (BASE 838ccda, implementer a4ec94666a1b69309, sonnet)
Task 0: implementer DONE_WITH_CONCERNS (97cecb9). Concerns: generate_catalog.sh omits the Phase 8 `.md` suffix rule, implementer re-applied it by hand to keep tests/apple-doc-links.test.ts green; plan said survey has 5 files, it has 4 (plan typo, no action); SKILL.md files carry no verified stamp (expected). Kill-switch: 1 genuine non-fixture invocation (apple-studio:xcode-loop, 2026-10-01, dependency-tracker) — first ever; transcript read denied by the classifier (PII), recorded as unconfirmed.
Task 0: review dispatched (sonnet, package review-838ccda..97cecb9.diff)
Task 0: review — spec ✅, quality Approved, 1 Important (catalog regeneration not reproducible: .md rule applied by an uncommitted scratchpad script). ⚠️ trailer checked by controller: Opus 5.5, correct. ⚠️ survey 4 files: plan typo, PDFs correctly uncommitted.
Task 0: minor (deferred): killswitch.log commits a session UUID and the sibling project name dependency-tracker (follows Phase 9 precedent; UUID needed to act on the hit)
Task 0: minor (deferred): deferred.md Phase 10 paragraph drops the "precondition remains unmet" clause, and says "The author" where "this phase" is clearer
Task 0: minor (deferred): headers.log has no line saying the SKILL.md entries carry no stamp
Task 0: fix round 1 dispatched (FIX_BASE 97cecb9): teach generate_catalog.sh the .md rule mirroring KNOWN_PAGE_FORM_EXCEPTIONS
Task 0: fix round 1/5 (1 addressed, 0 open; commits 97cecb9..11040e1)
Task 0: minor (deferred): generate_catalog.sh $bare list duplicates KNOWN_PAGE_FORM_EXCEPTIONS by hand; no test pins equality (comment is the only guard)
Task 0: complete (commits 838ccda..11040e1, review clean after 1 fix round)
Task 1: dispatched (BASE 11040e1, sonnet)
Task 1: implementer aa6a0c21b9a68a6bf
Task 1: implementer DONE_WITH_CONCERNS (d261220): 891 rows / 601,748 words (survey 909 / 622,615; −2.0% / −3.4%); deterministic offline re-run; 1 non-200 row (Apple broken figure link, 404).
- P10. Ruling: when the harness refuses a subagent's Write of a report file ("Subagents should return findings as text"), the subagent returns the report as text and the controller writes the SDD report file from it; committed record files the plan names (e.g. $REC/task-N-*/report.md) are written by the controller from the returned text in a small bookkeeping commit inside the task's range, so the task review sees them. No renaming or Bash workaround — the guard is the harness's, not ours to dodge — if wrong, the controller authored record prose the implementer meant; the reviewer checks it against the evidence.
- P11. Ruling: the one 404 manifest row (`/documentation/metal/compute_passes/creating_threads_and_threadgroups`, Apple's broken figure link) stays in the manifest and gets a `no-unfetchable:404:deferred-<n>` ledger row in Task 4, per the spec's unfetchable rule — no crawler change — if wrong, one noise deferred item.
- P12. Ruling: extract_links must also follow `doc://com.apple.documentation/documentation/…` and `doc://com.apple.documentation/design/…` links (both `<doc://…>` autolinks and `](doc://…)` targets), mapped to `/documentation/…` / `/design/…` paths. The spec defines depth1 as "the page itself and the pages it links"; the survey counted 13–86 doc:// links on several seeds (capturing-a-metal-workload 13, analyzing-memory-usage 25, porting 17, HIG games 10, Accelerate 86). The plan's brief named only `](/documentation/` and `](/design/` — a plan defect against the spec — if wrong, the corpus grows by pages the reading tasks must read.
Task 1: review dispatched (sonnet)
Task 1: review — spec ❌ (report.md missing — P10 covers it: controller writes it after the fix), quality Needs fixes: Important = fetch failures recorded as fake 404 rows with exit 0. ⚠️ survey-row coverage: implementer's script claim; reviewer verified 59 seeds.
- P13. Ruling: gamesave is depth1, not recursive (spec Deliverable 4: only Touch Controller recursive among Finding 8 additions; the plan's seed table put gamesave recursive) — spec wins — no effect today (GameSave root has only symbol children).
Task 1: minor (deferred): parse_map silently drops a seed line with a mistyped bound (treated as prose); ValueError path untested
Task 1: minor (deferred): tests don't check paren paths survive Fetcher URL quoting; cache-key test doesn't assert case variants collide; no depth1 collectionGroup-child test
Task 1: minor (deferred): manifest sort is case-sensitive on canonical spelling — check_ledger must sort/compare consistently
Task 1: minor (deferred): a 200 response with a non-Markdown body is cached and silently non-expandable (no content-type check)
Task 1: fix round 1 dispatched (FIX_BASE d261220): real fetch-failure codes + exit, doc:// links (P12), gamesave depth1 (P13), regenerate manifest
Task 1: fix round 1 implementer report (6e2ce2f): real fetch codes, exit 2 + no manifest on non-404/410 failure, `.gone` cache marker for real 404/410 (added), doc:// links in 3 forms (any bundle host; HIG mapped), gamesave depth1, signature-link skip (added). 21 tests OK. Manifest now 1176 rows / 808,743 words (+285 rows; 264 from Accelerate autolinks, 21 from depth1 seeds); 4 real-404 rows.
- P14. Ruling: Accelerate stays recursive — spec's recursive rule covers it and the user asked for no skimming; its 265 rows / ~183k words are read in full — cost: ~3 extra reader slices.
- P15. Ruling: accept the implementer's signature-link skip (child links whose last segment contains "(" are not fetched): verified against 13,859 cached pages, all 445 such pages are symbols, none collectionGroup; seeds never skipped; avoids 5 edge-403s on Accelerate expm1 symbols — if wrong, a collectionGroup with "(" in its slug would be missed (none exist today).
- P16. Ruling: dest attribution must be topical — a recursive seed whose scope contains the path wins; among depth1 seeds at equal depth prefer one sharing the row's first two segments; then earliest — 3 rows flipped dest to apple-games via games-technologies depth1 reach (metal/accelerating-ray-tracing, metal/setting-up-a-command-structure, xcode/preparing-your-app-for-distribution) — slicing feeds on dest — if wrong, a page goes to the other skill's readers (it is still read).
Task 1: fix round 1 continued (same round): topical dest attribution
Task 1: fix round 1 complete (commits d261220..6712a82 incl. controller report commit); scoped re-review dispatched
Task 1: re-review — all 6 items ADDRESSED, no new Critical/Important. Controller corrected 2 figures in its own P10 report.md (b3f981b).
Task 1: minor (deferred): `.md.gone` marker written non-atomically (unlike page cache .part + os.replace)
Task 1: minor (deferred): `.gone` markers are permanent; a 404'd page is never re-checked unless deleted
Task 1: minor (deferred): `python3 -I -m unittest test_crawl_corpus` from the pipeline dir fails (cwd dropped); repo-root path form works
Task 1: complete (commits 11040e1..b3f981b, review clean after 1 fix round)
Task 2: dispatched (BASE b3f981b, sonnet)
Task 2: implementer a654f1d8d8695e2fa
Task 2: implementer DONE_WITH_CONCERNS (1b69951): self-tests 11/11 + 12/12; catalog 39/56 before and after, byte-identical; metal-cpp 26.4 pinned by sha256 (page no longer links it; conventional path serves 26 and 26.4).
Task 2: minor (deferred): pre-existing no-directive snippet in apple-animations scroll-and-visual-effects.md fails only for a missing `import SwiftUI` (one of the 17 pre-existing catalog failures; deferred item 7 territory)
Task 2: review dispatched (opus)
Task 2: review (opus) — Needs fixes. Critical: Rust gate false PASS on invented symbol under concurrent runs sharing a directive (6/6) — shared scratch crate dir. Important: with-prior accumulator keeps duplicate `use` → correct snippets fail; swift-like fences (```Swift, ~~~swift, trailing info) reach no compiler; bare fences accepted beyond the constraint.
- P17. Ruling: gated blocks must use the exact opener "```<lang>\n"; any ~~~ fence, trailing info string, or swift-like opener the Swift gate cannot parse exits 2 — closes the silent-ungated path for every language — cost: writers must use canonical fences.
- P18. Ruling: a bare (unlabelled) fence exits 2; writers label plain text `text` — the Global Constraints list no bare fence; supersedes the implementer's lang=="" pass — cost: none.
Task 2: minor (deferred): run_cmd and the Swift gate's run() do not catch subprocess.TimeoutExpired → traceback reads as snippet failure (should be setup error, exit 2)
Task 2: minor (deferred): fetch_metal_cpp.sh cache hit does not re-verify the sha256; CppGate trusts the directory
Task 2: minor (deferred): test_typecheck_native.sh is mode 100644 (sibling is 100755)
Task 2: minor (deferred): single-target PASS lines don't name the target (FILE line does)
Task 2: minor (deferred): -fsyntax-only / metal -c don't diagnose invented names in uninstantiated templates; cargo doesn't check uninvoked macro_rules! bodies — CONVENTIONS could say so
Task 2: minor (deferred): check_file docstring says three return values, returns two
Task 2: minor (deferred): native self-test needs network on first run (cargo, metal-cpp) — brief-mandated, diverges from spec's "offline self-test" wording
Task 2: fix round 1 dispatched (FIX_BASE 1b69951)
Task 2: fix round 1 implementer DONE (e7b61c7): 23/23 + 11/11; race closed via per-run dir + unique crate name (cargo fingerprints by member path); re-review dispatched (opus)
Task 2: fix round 1/5 (3 addressed, 1 open — use dedupe still raw on as-written path; commits 1b69951..e7b61c7). Re-review also: Minor new breakage = splitlines() lets ```swift+\x0c/U+2028 escape both gates (folded into round 2 under P17); temp-file leak in self-test.
Task 2: minor (deferred): P17's exact-opener check runs only where the native gate runs; a Swift-only reference outside Phase 10 with ```Swift is checked by the Swift gate alone (0 blocks, exit 0) — consider running the native gate catalog-wide
Task 2: minor (deferred): pre-existing — Swift gate regex closes a block at the first ``` anywhere, even mid-line (e.g. in a // comment); later code in the block is never compiled
Task 2: fix round 2 dispatched (FIX_BASE e7b61c7)
Task 2: fix round 2 implementer DONE (18cc387); re-review dispatched
Task 2: fix round 2/5 (2 addressed, 0 open; commits e7b61c7..18cc387)
Task 2: minor (deferred): a Rust block whose every line is indented loses top-level `use` recognition → duplicate use → false E0252 (fails closed, not a regression)
Task 2: minor (deferred): hoist_uses still uses splitlines() on Rust bodies (cosmetic)
Task 2: complete (commits b3f981b..18cc387, review clean after 2 fix rounds)
Task 3: dispatched (BASE 18cc387, sonnet)
Task 3: implementer aca06f9c1cbcb839b
Task 3: implementer DONE_WITH_CONCERNS (44b2b67) + controller report (c50cc8a): 19 slices (m01–m08, g01–g09, p01, r01), 1,222 rows; checker 10/10; FST CSV export failed (AppleEvent timeout) — Numbers left running (user to close); review dispatched (sonnet)
Task 3: review — spec ✅, Approved, no Critical/Important; reviewer independently re-derived coverage (1,222 rows exactly once), cap (max 59,558 loaded), MSL tiling 1–383, and failed to fool the checker.
Task 3: minor (deferred): no tests pin case-insensitive match, in-two-slices/listed-twice malformed cases, empty fed, non-numeric words, unknown --only exit 2, split_pages
Task 3: minor (deferred): `nothing:` with empty reason passes; fed shape unchecked; ledger words not checked against manifest words (Task 4 finisher verifies by script instead)
Task 3: minor (deferred): make_slices.py MSL_SHA256 defined but unused; --check is machine-local (untracked inputs, hardcoded ~/Projects/book-skills path); read_text() lacks encoding="utf-8"
Task 3: complete (commits 18cc387..c50cc8a, review clean)
- P19. Ruling: readers may write cross-skill note sections named `## <skill>/<file>` (e.g. `## apple-games/input.md`) — Metal pages feed game-loop and profiling material too — cost: writers must gather sections across all slices (the writer brief says so).
- P20. Ruling: readers write `no-unfetchable:404:deferred-PENDING` for `.gone` rows; the task finisher adds the deferred.md items and replaces PENDING with the item numbers before running check_ledger — readers cannot know the numbers — cost: none.
- P21. Ruling: each reader first proves it can Write its ledger and notes files and stops with NEEDS_CONTEXT if the harness refuses (no Bash workaround) — 60K words of reading must not be wasted on an unwritable output — cost: one early round trip if refused.
- P22. Ruling: Task 4/7 finishers also verify, by script, that every ledger `words` equals the manifest/sources value and every `fed` is `nothing: <non-empty>` or `<file>[#section]` targets naming a known destination — closes the Task 3 review's weak-validation minor at the point it matters — cost: none.
Task 4: dispatching 8 readers (m01–m08, opus, parallel; brief .superpowers/sdd/2026-10-18-phase10-games/reader-brief.md). BASE c50cc8a.
Task 4: readers dispatched — m01 a5473eb8c475cc67b, m02 ae44f6bc88a2d40c6, m03 a071f531c0a3f03b2, m04 a7074eb7c8477c04c, m05 a8f6b9a840ff502f8, m06 a8b69314fd76c272f, m07 ac21ced28a8fc637f, m08 a1c2eb340223c64af
Task 4: all 8 readers stopped by an API usage limit (429) mid-slice; ledgers empty, notes partial (m01 73 bullets, m04 14, m07 74). All 8 resumed via SendMessage with: continue, re-read any page not certainly finished, write ledger rows per page as finished.
Task 4: m07 DONE — 6/6 read; 115 bullets; 6 book differs (Metal 3 spellings in ch01); findings: FST lists Apple families only (no Mac2/Intel); MSL appendix lacks a 4.1 delta (tagged in body); spec typos matmuld2d/is_compatiable_as_left_input vs SDK matmul2d/is_compatible_as_left_input; spec says plain Metal 4 for cube-texture atomics and ICB raster/depth-stencil but FST requires Apple10; atomics ordering self-contradiction (4.1 text wins); tessellation Metal 3 model only per FST. Note: its bash append was refused by the harness; it recovered with Edit.
Task 4: m06 DONE — 5/5 (MSL ch1–5, 48,917 words); 126 bullets; own 12-word copy check clean; errata: requiredThreadsPerThreadgroup is on (MTL4)ComputePipelineDescriptor not MTLDevice; MTLCompileOptions not MTLCompilerOptions; device memory threadgroup-coherent by default (coherent(device), MSL 3.2, Apple silicon); fast math default; constexpr sampler mip_filter::none default; meshlet uchar indices (inference); int4b/uint4b and tensor get/set need SDK 26.4.
Task 4: m05 DONE — 45/46 + 1 unfetchable (compute_passes/creating_threads_and_threadgroups: .md 404, bare 301s to m01's row); 81 bullets incl. cross-skill (games 6, performance 2, app-release 4); findings: porting page errors (simd_barrier→simdgroup_barrier, mem_device→mem_flags::mem_device, §6.8.1→§6.10.1); Xcode 27 not on Intel Macs, macOS 27 Intel slice needs x86_64 in ARCHS; API Validation unretained check covers MTLCommandBuffer only; MetalFX availability conflicts; undocumented MTLContentionRelief/MTLForwardProgressUsage; MPSRayIntersector deprecated; Enhanced Security ENABLE_CPLUSPLUS_BOUNDS_SAFE_BUFFERS breaks raw-pointer C++; capture page Metal 3 only but makeCaptureScope(commandQueue: MTL4CommandQueue) exists.
Task 4: m02 DONE — 59/59; 128 bullets (games 14, performance 2); 5 stub pages fed nothing; own copy check clean; Apple doc errors flagged (MTLArgumentBufferEncoder→MTLArgumentEncoder, gpuHandle→gpuAddress; UISceneDelegateClassName; .private vs .memoryless; deprecated supportsFeatureSet gating; stale Simulator claim; 'depth 128' means stencil; binary-archive filename mismatch); game-performance article: hw mesh shading + ray tracing = Apple9; NSProcessPerformanceProfile undocumented usage. Helper scripts in pipeline/tmp/m02/ (gitignored); one stray file in the session scratchpad.
Task 4: m03 DONE — 53/53; 112 bullets; copy check clean; key: Metal 4 MTLFence same-queue only (cross-queue → MTLEvent/MTLSharedEvent); MTL4 compute encoder runs dispatches concurrently; no intrapass barrier on .fragment/.tile on Apple GPUs; MSL 4.1 generic this + mangling change (4.0/4.1 binaries mis-link silently); MTL4CommandBuffer device-made, reusable after commit, doesn't retain; doc bug load/store sample uses colorAttachments[0] for depth; makeIOFileHandle vs makeIOHandle unclear; FST: 8x MSAA Apple10 only, texture view pools Apple7+.
Task 4: m04 DONE — 52/52 (build-settings-reference 4,753 lines read in 5 chunks); 2 fed nothing; ~94 bullets (games 16, app-release 6); key: MPS image filters encode only on Metal 3 MTLCommandBuffer (only MPSNDArray kernels take MTL4ComputeCommandEncoder; MPSGraph runs on MTL4CommandQueue) → separate Metal 3 queue + events; MTL_FAST_MATH defaults YES in Xcode 27 (page's opt-in advice stale), MTL_LANGUAGE_REVISION Metal41; CALayer.wantsExtendedDynamicRangeContent deprecated OS 26 → preferredDynamicRange, CAMetalLayer's not deprecated; HUD insights map to Metal 4 fixes; MPS ObjC sample broken.
Task 4: m01 DONE — 67/67; ~109 bullets (games 8, app-release 4); key: events/sparse mapping on MTL4CommandQueue; no useResource/useHeap on MTL4 encoders (residency sets); MTL4CounterHeap timestamps only (stage-utilization/statistic sets Metal 3 only); ICB reset/optimize/execute on MTL4ComputeCommandEncoder; MTL4PipelineDataSetSerializer + MTL4Archive; Metal 4 needs explicit barriers where Metal 3 auto-ordered; doc errors (CADisplayLink macOS 14+, Simulator claims, apple7=A14 not A15, .familyMac2, executeIndirectCommandBuffer nonexistent, broken Swift fn/MTLComputePipeline, r16Float depth, mip-count off by one, 196 vs 192); general Rosetta ends with macOS 27.
Task 4: m08 DONE — 34/34 book rows; 120 bullets; 25 book differs; check_ledger --only m08 exit 0; copy check clean; key: tessellation gone in Metal 4 (mesh shaders replace it; book ch19 Metal-3-only); MTL4RenderPipelineDescriptor has no depth/stencil pixel format; MTL4ArgumentTable has no setBytes; no blit encoder (copies on MTL4ComputeCommandEncoder); no waitUntilCompleted (MTLSharedEvent); MPSMatrixMultiplication MTLCommandBuffer only; supportIndirectCommandBuffers is MTL4IndirectCommandBufferSupportState; book family gates disagree with FST.
Task 4: all 8 readers DONE. Controller check_ledger --only m01..m08: 1 problem (the P20 PENDING placeholder on m05's 404 row) — as designed. Notes total ~54K words.
Task 4: finisher dispatched (sonnet) for Steps 2–4
Task 4: finisher DONE (b4865b4): check_ledger exit 0; field check 0/322; copy check 1 hit (MTL_HUD_ELEMENTS option list — facts) + 1 excluded signature; deferred item 19 for the 404 row. report.md refused by harness → controller wrote it (a1b1f9a), merging reader-reported findings.
Task 4: observation: bun test's marketplace-audit test timed out at 5s under parallel-agent load (bun run audit ~5.5s); passes with --timeout 30000; not caused by this task.
- P23. Ruling: each Task 5/8 writer also writes a sidecar `$REC/task-5-write/<stem>.sources.tsv` (section, claim, source) so the reviewer can trace claims — the plan's Step 6 asks a reviewer to trace 3 claims per reference; the sidecar makes that tractable — cost: writer time.
- P24. Ruling: every `## Maintaining older code: Metal 3` section carries the verbatim sentence "Snippets in this section compile at the file's macOS 26.0 floor; they are not compile-checked against earlier OS releases." — implements the plan's recorded spec deviation — cost: none.
Task 4: review dispatched (opus): 10-bullet sample, read-in-full spot checks, checker/script logic, copy, notes fitness.
Task 4: review (opus) — spec ✅, Approved; 10/10 sampled bullets ACCURATE (8 slices, 7 sections, seeded random); last-third spot checks on 5 long sources confirm full reads; checker and scripts sound. Important carry-forwards (corpus scope, not reading): no objc2-metal material, almost no metal-cpp; MetalFX per-mode inputs and CAMetalDisplayLink usage thin.
Task 4: minor (deferred): finding 20 incomplete — requiredThreadsPerThreadgroup also on MTLCompileOptions (MTLLibrary.h:417)
Task 4: minor (deferred): m04:78 cites doc pages not the xcspec that proves the MTL_FAST_MATH default; m01:125 cites "those paths" not full paths
Task 4: minor (deferred): copy_check.py holes (excludes any run containing "(", per-line runs, slice-only comparison, pdftotext hyphenation); reviewer's whole-corpus probe found no real miss at 12 words; a few m08 lines echo the book's phrasing closely
Task 4: minor (deferred): field_check.py doesn't check fed against notes (reviewer probe: 306/312 cited; 6 stubs cited in grouped form)
Task 4: minor (deferred): stub-only bullets sit in destination sections (m01:151, m02:121, m03:120), inflating counts
Task 4: minor (deferred): the stop/resume claim is not verifiable from the commit (last-third evidence consistent with full reads)
Task 4: complete (commits c50cc8a..a1b1f9a, review clean)
- P25. Ruling: cpp-and-rust.md's Rust spellings come from the pinned crates' source in the cargo registry (objc2-metal-0.3.2, objc2-0.6.5, cargo fetch for siblings) and docs.rs for those versions; C++ from the metal-cpp 26.4 headers and README in $TMP — the corpus carries neither and "No API from memory" needs an allowed source — cost: none.
- P26. Ruling: display-and-upscaling.md's writer reads in full the MetalFX scaler/interpolator/denoiser symbol pages (and MTL4FX variants) and the CAMetalDisplayLink pages — the corpus's MetalFX and display-link sample pages are stubs; spec asks for "every mode" — cost: extra symbol-page reads.
- P27. Ruling: writers carry the correction that requiredThreadsPerThreadgroup is also on MTLCompileOptions (MTLLibrary.h), not on MTLDevice — completes finding 20 — cost: none.
Task 5: dispatching 9 writers (opus, parallel; brief writer-brief.md amended with P25–P27). BASE a1b1f9a.
Task 5: writers dispatched — command-model a0463f51589eb4dcb, pipelines a4ec7d1f05d31c070, tbdr a81b9506256fd0f97, resources aa83b8aaee223556c, shading acba2b2f06905f7e9, compute af0c12ffd6bc1fb66, display ab27e10a26fbaebfc, gpu-debugging a0149df94acea437e, cpp-and-rust aea49d7c2d27059e7
Task 5: shading-language.md DONE — 663 lines (over 'a few hundred'; largest corpus); sidecar 116 rows; gates 4/4 Swift + 7/7 MSL (metal4.1), exit 0; 29 symbol pages; runtime findings: fresh MTLCompileOptions reads .fast on M4 Pro (doc says relaxed default); xcrun metal default std 4.1 (4.0 at 26.0 deployment target); runtime makeLibrary defaults 4.1 on OS 27 (4.0/4.1 ABI boundary); non-relaxed memory_order only in 4-arg mem_flags overload; reduction kernel exact 20/20.
Task 5: command-model.md DONE — 738 lines (~330 code); sidecar 87 rows; gates 8/8 Swift + 1/1 MSL exit 0; Frame structure run verbatim: 120 offscreen frames, pixel [119,128,64,255], clean under MTL_DEBUG_LAYER + MTL_SHADER_VALIDATION (writer pre-ran the R1 contract); ~88 symbol pages; resolved: MTLFence same-queue only (MTL4CommandEncoder.h); MTL4CommandQueueError.deviceRemoved deprecated in SDK; intrapass-barrier page params swapped; MTLSharedEvent.wait(untilSignaledValue:timeoutMS:) won't compile in async Swift 6; MTKView.residencySet needs 26.4; residency omission experiment documented as non-proof.
Task 5: display-and-upscaling.md DONE — 621 lines; sidecar 107 rows; gates 6/6 Swift (macos 26.0, ios 26.0) + 1/1 MSL exit 0; ~162 symbol pages (all MetalFX + CAMetalDisplayLink per P26); SDK-wins: displaySyncEnabled macOS-only; MetalFX temporal/interp/denoiser unavailable on visionOS; denoiser effectively 26; MTKView.residencySet 26.4; CAEDRMetadata.hdr10(minLuminance:maxLuminance:opticalOutputScale:); several temporal-scaler/interpolator props 27.0 (gated); jitter sign given as a test, not a claim.
Task 5: resources-and-memory.md DONE — 661 lines (~250 code); sidecar 129 rows; gates 9/9 Swift + 2/2 MSL exit 0; Metal 3 sentence verbatim; 91 symbol pages; SDK-wins: getTextureAccessCounters deprecated 26.4, no Metal 4 counterpart; makeIOHandle deprecated → makeIOFileHandle; .managed deprecated macOS 27 SDK; Metal 4 sparse = placement sparse only (updateMappings, .placement heaps, .resourceState barrier; residency sets reject .sparse heaps); supportsPlacementSparse 26.4+ (pre-26.4 .apple8 fallback labeled inference); runtime: placement sparse works on M4 Pro, recommendedMaxWorkingSetSize 37.4 GiB/48 GB.
Task 5: apple-gpu-tbdr.md DONE — 664 lines (~200 code); sidecar 94 rows; gates 7/7 Swift + 3/3 MSL exit 0; ~56 symbol pages + metal_imageblocks header; SDK-wins: MTLGPUFamilyMac2 deprecated at 27 (→ .apple7); isDepth24Stencil8PixelFormatSupported deprecated ('Never supported on Apple Silicon'); barrier page params swapped; imageblock<T> with [[color]] members is implicit layout (m07 note wrong); m07 imageblock size per pixel shifted one column (FST agrees with m03); 8x MSAA Apple10 per FST.
Task 5: compute-and-gpu-driven.md DONE — 878 lines (13 code blocks, 6 subtopics); sidecar 126 rows; gates 9/9 Swift + 4/4 MSL exit 0 (gate caught raytracing:: qualifier); 58 symbol pages (one guessed URL 404'd, deleted); SDK: pipeline states conform to MTLAllocation, ICB-referenced pipelines must be in a residency set; tables-win on mesh A14, ICB raster state Apple10; payloadMemoryLength 0 sizes from type; inferences marked not runtime-checked.
Task 5: gpu-debugging-and-profiling.md DONE — 773 lines; sidecar 99 rows; gates 9/9 Swift + 1/1 MSL exit 0; 62 symbol pages + 27 articles + headers; every gpudebug/gpucapture/xctrace/metal-dsymutil command and the capture code RAN on the M4 Pro (R2 contract pre-checked); runtime findings: makeCaptureScope(commandQueue: MTL4CommandQueue) as captureObject CRASHES in startCapture (unrecognized selector traceStream) — device or makeCaptureScope(device:) works (cpp-and-rust writer saw the same); gpudebug exits 0 on command failure; session keeps position (use absolute paths); gpucapture --output needs absolute path; reused MTL4CommandBuffer labels don't hold per frame (debug groups do); counter-heap timestamps in ticks (24 MHz); Shader Validation catches missing residency, API Validation doesn't; startCapture(device:/commandQueue:/scope:) deprecated; HUD range env var name unresolved (both named).
Task 5: cpp-and-rust.md DONE — 755 lines (~200 code: two complete hosts); sidecar 88 rows; gates Swift 0/0 + native 6/6 (3 cpp, 3 rust) exit 0; hosts RUN on M4 Pro (red pixel, API validation on); both capture helpers wrote a .gputrace gpudebug opened (R5 partly pre-checked); confirmed MTL4CommandQueue capture-scope crash from Swift and C++; reused MTL4CommandBuffer created before capture still recorded (doc says otherwise for Metal 3); supportsDestination(.gpuTraceDocument) false without MTL_CAPTURE_ENABLED; C++ dialect: set c++20 explicitly (clang default C++14, Xcode doc says GNU++98); CMake + Xcode External Build System marked not runtime-checked (R5).
Task 5: pipelines-and-render-passes.md DONE — 841 lines; sidecar 124 rows; gates 10/10 Swift + 2/2 MSL exit 0; ~90 symbol pages; measured: depth-only pipeline needs rasterization ON (docs say off — fails creation); MTL4PipelineDataSetSerializer captureDescriptors default 0, archive write needs exactly .captureBinaries, second write throws "Nothing to serialize"; metal-tt rejects serializeAsPipelinesScript() output; a macOS-26.0 metal-tt archive would not open on 27.0.1 (treat failed open as miss); memoryless texture in a residency set fails validation; storeActionOptions deprecated; depth24Stencil8 never on Apple silicon; MTL4CompilerTask unavailable in Swift.
Task 5: all 9 writers DONE. Reference sizes 621–878 lines (~6,700 total), every fenced block gated clean per writer.
- P28. Ruling: reference lengths of 620–880 lines are accepted (each is one decision area with 200–330 lines of compiled code); every reference over 300 lines gets a short "Contents" list of its `##` sections within its first 30 lines, after the header block — CONVENTIONS' "a few hundred lines" is a soft guide and the audit warns on long files without a TOC — cost: if wrong, the reviewer asks for trims.
Task 5: finisher dispatched (opus): SKILL.md, triggers, apple-animations line, README rows, security manifest (P4), TOCs (P28), gates on all 9, Vale, catalog gates, commit.
Task 5: finisher adac70ecf47f3a095
Task 5: finisher DONE (6a40dd7) + controller report (031d473): SKILL.md 112 lines (desc 1015 chars), triggers 8+6, 9 refs 6,715 lines, gates 62/62 Swift + 27/27 native, bun test 542/0 (--timeout 30000), audit 0 errors, validate pass. Finisher reworded the apple-games pointer to evade the catalog-integrity test.
- P29. Ruling: until apple-games ships, apple-metal's description names no unshipped skill (frame pacing, input, audio, Game Center described as out of scope without a skill name); Task 8 restores `(apple-games)` so the integrity test guards it — rewording to dodge the test defeats its purpose, and if the user ships apple-metal alone at the Task 6 checkpoint the pointer would be false — cost: weaker routing hint until Task 8.
- P30. Ruling: cross-skill pointers use `<skill>/references/<file>.md` (the catalog's majority form) — display-and-upscaling.md uses the bare form — cost: none.
Task 5: review dispatched (opus): spec + quality + 27 claim traces (3 per reference) via sidecars.
Task 5: review (opus) — Needs fixes. 25/27 claims SUPPORTED, 2 MISSTATED (Shader Validation "silent" on missing residency — report goes to unified log without MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1), 0 UNSUPPORTED; 16/16 prose symbols exist; no invented API. Important: 2 misstated claims; P29 unmet; Mac2 baseline contradiction; pacing-owner contradiction; P30 incomplete; ~100–150 lines padding/duplication.
- P31. Ruling: snippet correctness in a reference is Important, not Minor — agents copy reference code; promoted 4 reviewer minors (display Renderer commits unbegun buffer; gpu-debugging early return leaves buffer begun; compute requiredThreadsPerThreadgroup zero precondition; OS-27-only MTL4ComputePipeline props ungated) — cost: one larger fix round.
- P32. Ruling: runtime evidence behind every "Measured" claim is copied (commands, key output, machine/OS) into $REC/task-5-write/runtime/<stem>/ and sidecars point there — the record must be auditable without the session scratchpad — cost: small.
Task 5: minor (deferred): shading-language.md:648–659 Metal 3 loader gates on family only, not OS (contradicts SKILL.md "check both")
Task 5: minor (deferred): compute-and-gpu-driven.md:327 comment broader than header (only pipelines the ICB sets)
Task 5: minor (deferred): Metal 3 contrasts outside the Metal 3 section (pipelines 47–56 table, compute 701–716 MPS side-queue) are justified but unannounced
Task 5: minor (deferred): apple-performance description doesn't hand GPU frame time to apple-metal (Task 9/13)
Task 5: minor (deferred): `> sources:` order differs in shading-language (cosmetic)
Task 5: fix round 1 dispatched to finisher adac70ecf47f3a095 (FIX_BASE 031d473)
Task 5: fix round 1 implementer DONE (df65d1a): 11/11 items; refs 6,715→6,711 lines (cuts ~70, fixes +~65); gates 62/62 + 27/27; bun test 542/0, audit 0 errors, validate pass; description 968 chars ("Frame pacing, input, audio, and Game Center are outside this skill."); runtime records in $REC/task-5-write/runtime/<stem>/runs.txt; new measured fact: MSL required_threads_per_threadgroup attribute pin reads back 0 from requiredThreadsPerThreadgroup.
P29 RESTORE LIST (for Task 8 — add apple-games pointers back at): SKILL.md:3 (description last sentence → "(apple-games)"); SKILL.md:50–53; display-and-upscaling.md:23–26, 47–48, 651–652; gpu-debugging-and-profiling.md:657–658; evals/triggers.md:24 should-not row (was "(apple-games — input)"); optionally command-model.md:25–26.
Task 5: fix round 1/5 (7 addressed, 1 open — compute dispatch fallback silently 32×8 for attribute-pinned 16×16 kernel, proven by probe; commits 031d473..998380b). Round 2 also carries: gpu-debugging log-stream advice yields <private> (promoted under P31).
Task 5: minor (deferred): apple-gpu-tbdr porting checklist lost its position-invariance item without a pointer to pipelines-and-render-passes.md
Task 5: minor (deferred): bun test marketplace-audit 5 s timeout flakes under load (passes alone in 4.95 s) — environment, not content; consider raising that test's timeout
Task 5: minor (deferred): report.md says "Metal 3 baseline is .apple7" — should say the family to gate on (controller to fix wording)
Task 5: fix round 2 dispatched (FIX_BASE 998380b)
Task 5: fix round 2 implementer DONE (9792a9f): dispatch now precondition(group.width > 0) on the descriptor pin; widestGroup doc says pin-nothing only; probes recorded (old fallback 32×8 silent; pinned → correct; attribute-only → precondition trap); gpu-debugging log advice → REPORT_TO_STDERR, log shows <private>; gates 62/62 + 27/27; bun test 542/0, audit 0 errors, validate pass. Re-review dispatched.
Task 5: fix round 2/5 (2 addressed, 0 open; commits 998380b..9792a9f). Controller report wording fix committed after.
Task 5: minor (deferred): compute-and-gpu-driven.md:130 "Read the shape from the pipeline, never from a constant" sits in tension with the pinned-kernel rule; add "unless the kernel pins its size"
Task 5: minor (deferred): shading-language.md:657 Metal 3 table maps required_threads_per_threadgroup to max_total_threads_per_threadgroup — loses an exact-tile pin (same hazard)
Task 5: minor (deferred): precondition guard unchecked under -Ounchecked (prose doesn't overclaim)
Task 5: complete (commits a1b1f9a..HEAD, review clean after 2 fix rounds)
- P33. Ruling: Task 6's optional GUI step (attaching Xcode's GPU debugger to an externally built binary) is offered to the user inside the Task 6 Step 9 checkpoint question, not as a separate stop — one stop instead of two — cost: none.
Task 6: dispatched (opus). BASE recorded below.
Task 6: BASE 6c6d834, implementer a7f755ac519655472 (opus)
Task 6: implementer DONE (15e4ca8, report 0ee80c1); R1 pass, R2/R3/R5 pass after reference fixes; GUI step not runtime-checked
Task 6: reviewer a30b461d6f05a8992 (opus), package review-6c6d834..0ee80c1.diff
Task 6: review — Needs fixes: 2 Important (Instruments sizes/thresholds/exit-54 rule unlogged or contradicted by r3-toc.log; failure modes behind the R2/R5 fixes unlogged), 5 Minor
- P34. Ruling: a reference claim stated as runtime-checked must be reproduced by run.sh and visible in a committed log at the stated values; otherwise it is cut or reworded to what the logs show — no unlogged numbers — why: P32 principle, and Task 9 copies the exit-54 rule — cost if wrong: a few lines of measured detail lost from the reference
- P35. Ruling: the 15e4ca8 commit body's "R1 and R5 pass as written" is not amended (history rewrite); report.md is corrected instead — cost: one misleading commit message in history
Task 6: fix round 1 — resume implementer a7f755ac519655472
Task 6: fix round 1 DONE (65e1692 + report commit); P34 applied: sizes/50k/20k cut, exit-54 rule and pre-fix failures now logged
Task 6: re-review round 1 dispatched ae7bc21f00aafcbf3 (sonnet), package review-0ee80c1..da3dd12.diff
Task 6: re-review round 1 — all 5 findings ADDRESSED, no new breakage; residual P34 out-of-scope: "three rows" (gpu-debugging:665) and cold-build 83 s/15 s (cpp-and-rust:340), both unlogged Task 5 claims
- P36. Ruling: the controller made the two residual one-line rewordings itself (no numbers; "a one-frame host gave one row" per r5.log; build timing marked observed-once-not-logged) instead of a third implementer round — a two-sentence mechanical edit, gates 9/9+1/1 and 0/0+6/6, bun test 542/0, audit exit 0 — cost if wrong: the edits skipped an independent review; the final whole-branch review covers them
Task 6: complete (commits 15e4ca8..HEAD, review clean after 1 fix round + P36 controller edit). Step 9 checkpoint next.
Checkpoint (Task 6 Step 9): user chose A — continue to apple-games (Tasks 7–13)
Task 7: dispatching 11 readers (g01–g09, p01, r01; opus) per reader-brief.md + P37
Task 7: readers dispatched (opus): g01 a681165bf7d83b5ce, g02 a5b2ca797e4edd056, g03 aeb658dd9cc3c6bea, g04 a7fed036b931a80ec, g05 ae96808e5ba613678, g06 a061749f0cd7b421d, g07 ae5639ee6a40b5581, g08 a3677297fcb2bd296, g09 ac46bab1ed36e937d, p01 adb61deab99f6a497, r01 a062599aeece0597d
Task 7: g05 DONE 74/74, notes 28 bullets
Task 7: g01 DONE 29/29, 139 bullets
Task 7: g03 DONE 91/91, 34 bullets
Task 7: g04 DONE 59/59, 20 bullets
- Task 8 carry: vDSP FFT normalization conflicts (vDSP.h/ref pages say inverse 1/N; data-packing article + g05 say never scales) — writer must run a round trip before stating it (P34). CVDisplayLink deprecated macOS 15 → NSView/NSScreen.displayLink(target:selector:) macOS 14. Biquad DF1 vs DF2 pages disagree.
Task 7: p01 DONE 39/39, 64 bullets
- Task 9 carry: p01's suggested verdict "Output file saved line + termination reason" — only the toc's launched-process exit status/termination reason is evidence (false and true print the same completion lines, r3-toc.log); p01's "466 MB" size is not a logged value (P34). Open checks: frames-in-flight DispatchSemaphore priority inversion; GPU memory in iOS footprint. --only-test-configuration single dash per xcodebuild -help.
Task 7: r01 DONE 28/29 + 1 404 (/documentation/os/reading-unix-manual-pages, PENDING deferred), 104 bullets
- Task 8/10 carry: per Apple "Supported capabilities (macOS)" (read by r01, $TMP/r01-extra/), Developer ID cannot use Game Center, IAP, Sign in with Apple; iCloud and push need an embedded Developer ID provisioning profile — game-center-and-online.md and direct-distribution.md must say so; user to be told at the Task 10 stop. No page covers Apple-silicon-only MAS targeting (writer needs another source). Existing signing reference: re-sign threshold v=20400 (reference implies 20500) — Task 10/11 fix candidate.
Task 7: g02 DONE 68/68, 52 bullets
- Task 8 carry (audio): OS 27 SDK adds realtime-safe render blocks (CA_REALTIME_API, Swift-unavailable → render code in C/ObjC/C++), deprecates non-throwing connect/play for connectNode/playAudio, deprecates AVAudioSession.interruptionNotification (iOS-family 27). Writers at the 26.0 floor must gate OS 27 symbols with #available and say which OS each spelling needs; the typecheck directive must cover both (macos 26.0 plus a 27.0 check where used).
Task 7: g08 DONE 70/70, 165 bullets (GameKit deprecations: GKGameCenterViewController, showHighlights, GKVoiceChat; Apple activity snippets misspelled vs SDK)
Task 7: g09 DONE 64/66 + 2 404 (kernel sysctlbyname, mach_absolute_time; PENDING deferred), 113 bullets
- Task 8 carry: g09 claims no public API creates an interval workgroup for a render/sim loop — writer must check os/workgroup_interval.h (os_workgroup_interval_create and its attr rules) before stating it. TouchController draws only via a Metal 3 MTLRenderCommandEncoder (iOS 26) — game-loop/input must say so and apple-metal's Metal 3 section is the cross-ref.
Task 7: g06 DONE 169/169 (AppKit/AudioToolbox/Apple-silicon, my dispatch note mislabeled it Accelerate), 38 bullets. Carry: Xcode 27 / macOS 27 Intel ARCHS claim (JIT page) for Task 10 writer to confirm; 3DMixer deprecated → SpatialMixer
Task 7: g07 DONE 206/206, 47 bullets. All 11 readers done.
Task 7: finisher dispatched af4e77f96000a419a (opus): deferred 20–22, check_ledger g/p/r + whole corpus, field/copy checks, sampling, consolidated findings, commit; controller writes report.md (P10)
Task 7: finisher DONE f257557 + report 8be1fb0 (controller extracted report text from the finisher's returned message, P10); reviewer a6f80dd967c4d4b54 (sonnet)
Task 7: review Approved (18 independent bullets, 17 accurate; checks reproduce byte-identical)
Task 7: minor (carried to Task 8 brief): g02:36 muted-speech listener gate macOS 14/iOS 17; g09:100 Mac controller-haptics claim rests on GCDeviceHaptics.h macos(11.0), unlabeled; g06:18 last sentence is unlabeled inference
Task 7: minor (deferred): deferred item 21 lists six man pages, stapler also read; r01.md:155 prose still says PENDING; copy_check/field_check holes (parentheticals excluded, no header/man sources for g/p, per-line runs, missing cache silently skipped; fed-target bullets and nothing-reasons unchecked)
Task 7: complete (commits f257557..8be1fb0, review clean)
Task 8: BASE 8be1fb0; writers dispatched per writer-brief-games.md (opus)
Task 8: writers (opus): game-loop aa81ac9e3aa7f802c, input a1160123604ad9a78, audio a43168e225b62efee, game-center afd6d375627240594, assets ae72386ece7c2c4ee, game-design a05fd2aa04e16ff79
Task 8: game-center-and-online.md DONE (670 lines, 9/9 + 1/1; party-code runtime log; DTLS Swift struct is OS 27, gated)
Task 8: game-design.md DONE (600 lines, 5/5 + 0/0; runtime: dynamicTypeSize no-op on macOS; NSAccessibilityButton conformance compile failure logged)
Task 8: input.md DONE (658 lines, 11/11 + 0/0; runtime: shouldMonitorBackgroundEvents, unmapped spelling)
Task 8: game-loop-and-threading.md DONE (914 lines, 12/12 + 0/0; runtime: timebase 125/3, completion-handler QoS, priority 45 vs QoS, sysctl hw.nperflevels)
- Parked finding (gate): typecheck_snippets.py passes a block wrapped in `#if os(iOS)`/`#if os(macOS)` on the other target as empty code — writers must not wrap gated blocks; gate fix candidate (Task 11 or deferred) — cost if unfixed: a platform-wrapped block ships unchecked on its real platform
- Parked finding (apple-metal): display-and-upscaling.md RenderLoopThread sets no QoS (runs at .default per game-loop runtime log) — fix in Task 11 cross-refs
Task 8: audio and assets writers stopped by usage limit (429); resuming both via SendMessage
Task 8: assets.md DONE (582 lines, 6/6 + 0/0; runtime: compression codecs/ratios, UTI resolution, KTX2 via MTKTextureLoader → BGRA8 single mip, Model I/O imports; RGB8Unorm exists on OS 27 for texture buffers only)
Task 8: audio-and-haptics.md DONE (909 lines, 7/7 + 3/3; runtime: FFT round trip ×2n (vDSP.h inverse pseudocode wrong), DFT lengths, haptics unsupported on Mac mini, -Wfunction-effects)
Task 8: finisher aed187e61c8132c06 (opus): SKILL.md, triggers, P29 restore, RenderLoopThread QoS fix, cross-refs, READMEs, P4 manifest, gate logs, Vale/tests, commit; controller writes report.md (P10)
Task 8: finisher DONE 408b1df (SKILL.md 101 lines, desc 998 chars; triggers 8+6; P29 restored; RenderLoopThread QoS fixed; 50/50 + 4/4; bun test 542/0; audit 0 errors; validate passed); report 911dc44 (controller extracted from returned text, P10)
- Note: SKILL.md cross-refs name the skill, not `<skill>/references/<file>`, because validate_skill.ts reads that form as a local path — P30 form applies inside reference files only
Task 8: reviewer a1b16693fca39a86d (opus), package review-8be1fb0..911dc44.diff
Task 8: review — Needs fixes: 2 Important (haptics machine misnamed Mac mini — it is MacBook Pro Mac16,8 with Force Touch trackpad, confirmed by system_profiler; sendOverDTLS OS 26 branch leaks a started NWConnection per call), 7 Minor
- P38. Ruling: iOS-only snippets in dual-target files stay unwrapped (no `#if os(iOS)`), because the gate compiles a wrapped block as empty on the other target and so stops checking it; the prose tells readers to wrap — reviewer Minor 3 declined — cost if wrong: a paste into a multiplatform target fails to compile (loudly) until wrapped
Task 8: fix round 1 — resume finisher aed187e61c8132c06
Task 8: fix round 1 DONE 2c9f786 + report 9ab3b79; re-review ab91f522832bee4ee (sonnet)
Task 8: re-review — all 8 findings ADDRESSED, no new Critical/Important
Task 8: minor (parked for final review): sendOverDTLS OS 26 branch awaits forever if the connection sits in .waiting (no route) — no timeout or state handler; pre-existing, not a leak
Task 8: complete (commits 408b1df..9ab3b79, review clean after 1 fix round)
Task 9: BASE 9ab3b79
Task 9: implementer a45ac790fb9cee131 (opus); exit-54 correction in SKILL.md:37 + profiling-workflow.md:67,233 folded in; NEEDS_USER stop if Processor Trace needs enabling (P8)
Task 9: NEEDS_USER — Processor Trace not enabled (record exit 2: 'The target device is not configured for tracing. Enable Processor Trace in System Settings → Privacy & Security → Developer Tools'); asked the user (P8 stop)
Task 9: user chose option 1 (enable Processor Trace); resuming implementer — if recording still fails, it stops again
Task 9: second check recording failed (exit 2, same enablement error, before restart — expected, the setting needs a restart). P39. Ruling: defer R4 to one combined user stop with Task 10 (enable Processor Trace + Developer ID cert + notarytool profile + team confirm, then one restart); Task 9 commits its section with Processor Trace claims marked R4 pending — cost if wrong: one follow-up edit if R4 contradicts the section
Task 9: DONE_WITH_CONCERNS 88887c8 (R4 pending; analysis self-tested on Time Profiler: plantedSlowStep 99.32% vs control simulationStep 65.52%; exit 2 for failed recording logged); report committed
Task 9: reviewer a9c6255759824ab05 (sonnet), package review-9ab3b79..67a63f9.diff
Task 10: BASE 67a63f9; implementer a9056e4e75427ef7b (opus) for Step 1 + bundle.sh only, stops at R6 Step 1 (user step); runs alongside the Task 9 review (disjoint files) — P40. Ruling: Task 10 Step 1 runs while Task 9 is under review because their files are disjoint (app-release vs apple-performance) and R6 Step 1 needs the user anyway — cost if wrong: a Task 9 fix round could conflict on nothing shared
Task 9: review Approved (no Critical/Important)
Task 9: minor (fold into post-restart R4 edit): profiling-workflow.md:283-284 "in this category" unlogged; :341-345 `<thread ref="2"/>` example unlogged (say illustrative or log it); heaviest_under_interval.py must require a processor-trace-* verdict for R4 pass and restrict the `name` fallback to symbol/backtrace tables; soften "a recording that cannot trace exits 2" to the one logged cause; report's Vale/bun/audit counts have no committed log
Task 9: complete except R4 run (commits 88887c8..67a63f9); R4 + minors after the combined restart (P39)
Task 10: Step 1 DONE 04f7345 + report; R6 stops at Step 1 (user). Findings: hdiutil create deprecated on 27.0.1 → diskutil image create from (defaults ULFO); Xcode 27.1 at 26.0 floor builds universal, at 27.0 arm64 only; ditto zip step added before submit
Task 10: reviewer ae99275f04091f545 (opus) on 67a63f9..7548363; R6 Step 1 user stop raised (P8). P41. Ruling: the restart is needed only for R4 (Processor Trace), not for R6 — the user does the Developer ID setup now, R6 runs without a restart, and the single restart happens before Task 13 — cost: none
Task 10: Step 1 review — Needs fixes: 1 Important (SUBMISSION_ID never set in the verbatim release block; log path should be a variable), 5 Minor; fix round 1 — resume implementer a9056e4e75427ef7b
Task 10: Step 1 fix round 1 DONE facb146 + report
Task 10: re-review a93dc79780f5961d1 (sonnet) on 7548363..1636526
Task 10: Step 1 re-review — all 6 ADDRESSED; carry to R6: the release block has no `set -e` (a failed submit leaves SUBMISSION_ID empty and continues) — R6 runs step by step and stops on any failure; Step 5 reconcile decides whether the reference adds `set -e` or a guard
- P42. Ruling: Tasks 11–12 proceed while Task 10's R6 waits on the user (the R6 run edits only direct-distribution.md and $REC/task-10-r6; Task 11's cross-ref check of that file re-runs after R6) — cost: one re-check of direct-distribution pointers after R6
Task 11: complete (2e4f229) — controller wrote the two lines (P36: two-line mechanical edit); bun test 542/0, audit 0, validate passed; final review covers it. Pointer re-check of direct-distribution after R6 pending (P42)
Task 12: BASE 2e4f229; implementer a129329d2146f1f9b (opus)
Task 12: NEEDS_USER — sweep 58/60 (apple-metal 14/14, apple-games 14/14, prior 30/32); test-fire known-open; conc-fire failed because ar-fire-5 switched StudioFixture to branch push-notifications (driver checks porcelain, not HEAD) — guard blocks git -C on the fixture; asked user to restore, then re-run conc-fire
Task 12: user chose option 1; controller restored StudioFixture (switch main; branch -d push-notifications, same commit 5287d2c; status clean on main) — the guard allowed it from this session; resuming implementer for the conc-fire re-run
Task 12: DONE_WITH_CONCERNS 8216091 — new skills 28/28, prior 30/32; conc-fire fails on clean main (missing referent, "this" with no class in fixture), diagnostic how-to phrasing passes; test-fire known-open; deferred item 22 (guard misses branch switch)
- P43. Ruling: conc-fire is recorded as a known-open prompt defect and does not gate — the branch changes nothing in swift-concurrency (description and triggers untouched), the failure reproduces the missing-referent pattern deferred item 6/13 already record, and the how-to control routes correctly; rewording a prior skill's eval row to pass would be grading our own exam inside this phase — a deferred item records the reword — cost if wrong: a real swift-concurrency routing regression goes unnoticed until the next sweep
Task 12: deferred item 23 (conc-fire reword) committed 72d81d4; Tasks 11–12 reviewer a368978f937435329 (sonnet)
Task 11–12: review Approved; controller fixed classification.md minors 1–3 (P43 recorded, "mainly the referent", known-open row) under P36
Task 11: complete. Task 12: complete (commits 8216091..HEAD)
- Reviewer suggestion parked: a one-time how-to-form re-run of conc-fire could close item 23 now — left to item 23's trigger (P43)
Remaining: Task 10 R6 (waits on user: Developer ID cert, notarytool profile, team), Task 9 R4 + its minors (waits on Processor Trace + restart), Task 13 release, final review
User confirmed P43: don't block on conc-fire (2026-10-18)
- P44. Ruling (user-approved 2026-10-18, option 1): R6 real notarization is skipped for this release — neither team (2F7J72JV48 [Apple ID 1, redacted], ULQJ329QSN [Apple ID 2, redacted]) offers Developer ID in Xcode; the reference's 'R6 pending' markers become 'not runtime-checked: needs a Developer ID identity', and a deferred item records the re-run — cost: the end-to-end notarization path ships unverified (JSON keys, the spctl source string)
Task 10: complete without R6 (P44) — e350ac8 + report 72ef2b2; deferred item 24
- P45. Ruling: the final whole-branch review covers e350ac8's new claims (identity facts, 403 pitfall) instead of a separate task review now — avoids an agent running across the user's restart — cost: one review cycle later
- Task 13 carry: spec line 406 says the identity is "for team RTC3TK2XFJ ([Apple ID 2, redacted])"; RTC3TK2XFJ is the identity-name ID, the team is ULQJ329QSN (identity.log) — correct it in Task 13's spec verification append, not by editing the approved text
RESUME POINT (after the user's restart for Processor Trace):
 1) Task 9 R4: per task-9-r4/report.md "Open after the restart" — run.sh r4 > $REC/task-9-r4/r4-toc.log; run.sh r4-finding > $REC/task-9-r4/r4-finding.log; replace the "R4 pending" paragraph in profiling-workflow.md; fold in the Task 9 review minors logged above; review
 2) Task 13: release 0.11.0, tag apple-studio-v0.11.0, deferred items, spec verification append (incl. the line-406 correction), copy this ledger to $REC/sdd-ledger.md
 3) final whole-branch review (most capable model)
 4) finishing-a-development-branch — push and PR wait for the user
User restarted with Processor Trace enabled (2026-10-18). Resuming at RESUME POINT 1.
Task 9 R4: controller runs it (P36-sized: run + paragraph swap + review minors). r4 exit 0: both Processor Trace recordings launched the CLI target, return-exit-status 0, 390M / 767M bundles, processor-trace-{gaps,intervals,points,threads} + time-profile tables (r4-toc.log)
Task 9 R4: first r4-finding (pre-minor script) named plantedSlowStep 99.89% in processor-trace-intervals; stopped and re-run after the script minors (--require processor-trace-, name fallback → text-location etype, category printed) so the committed log comes from the committed script
Task 9 R4: PASS — r4-finding (committed script, --require processor-trace-): --slow → plantedSlowStep 99.89% (processor-trace-intervals), control → simulationStep 38.84%; time-profile agrees 99.87% / 61.29%. Clean-state check found two stopped (T) MetalProbe copies from build/MetalProbe.app, PPID 1, PIDs one below the traced ones — logged (orphans.log), killed with -KILL, reference bullet added
Task 9 R4: committed 0e0f335 (paragraph → result, minors folded, gates-r4.log: Swift 1/1, Vale 0 errors, bun 542/0, audit 0, validate --strict pass). Scoped re-review dispatched (sonnet) on 72ef2b2..0e0f335
- P46. Ruling: Task 13 runs while the R4 re-review is open — Task 13 edits no R4 file (profiling-workflow.md, metal-probe/*, task-9-r4/) — cost if wrong: a re-run of Task 13's whole-plugin gates after an R4 fix
- P47. Ruling: the tag apple-studio-v0.11.0 is created by the controller after the final whole-branch review and its fix round, on the head that review approves, not inside Task 13 — a tag cut before the final review's fixes would name a commit that is not the release — cost: none; the tag is local and unpushed until the user says
- Deferred candidate (Task 13): run.sh record_sim leaves Processor Trace's stopped .app copy running; the fixture should end it after each recording
Task 13: BASE 0e0f335
Task 13: implementer ad32af64721b26c38 (opus); no tag (P47), no ledger copy (controller, end)
Task 9 R4 re-review (a1456c37a09b3cb27, sonnet): items 2–6 ADDRESSED; item 1 open — Important: "ten seconds made 390M and 767M" false for the control (ended on target exit); Minor: pgrep/kill unlogged and signal(3) cite unsupported; "one failed recording" (two logged); report.md pre-restart text stale; "same 99.89%" and kill unlogged. Out-of-scope: --slow hit the 10 s limit yet the target finished 100000 ticks, exit 0, trace holds 53,644 — conflicts with the time-limit-kill-gives-54 rule (that was Metal System Trace, r3-toc.log:103-116)
Task 9 R4: controller fix (P36 size) a3a77fa — time limit ends the Processor Trace recording, not the target; exit-54 rule scoped to Metal System Trace (profiling-workflow.md ×2); stopped-copy bullet advice-only; exit-2 bullet "one cause"; report pre-restart text marked superseded; gates-r4.log re-run (1/1, Vale 0 errors, 542/0, audit 0, validate pass)
- P48. Ruling: the a3a77fa fix gets no second scoped re-review; the final whole-branch review covers it, as P36 — every change is a rewording toward what the committed logs show — cost if wrong: one review cycle later
Task 9: complete (88887c8..a3a77fa; R4 pass)
Task 13: DONE_WITH_CONCERNS 02b636b (no tag, P47) — ledger check 1,222/1,222; Swift 153/170, 0 PASS→FAIL, 0 Phase 10 FAILs; native 31/31; bun 542/0; audit 0; validate + --strict pass; load check registers apple-metal + apple-games at 0.11.0 (stream-json init, --tools Skill); deferred 25–41; spec append items 1–7 (4 PARTIAL: conc-fire P43)
- P49. Ruling: the security plugin stays at 0.4.0 although audit --since main warns — the branch's only security change is the P4 eval-roster line in reviewing-code-security/evals/manifest.json, which changes nothing an installed user runs, and #14/#15 made the same edit unbumped — cost if wrong: users' installed security plugin carries a stale eval roster, which no installed behavior reads
Task 13: reviewer a9f3cea4837a354b6 (sonnet), package review-a3a77fa..02b636b.diff
Task 13: review — Needs fixes: 2 Important (spec append §2 "No shipped snippet is wrapped" false — game-loop-and-threading.md:260-282 and display-and-upscaling.md:284-288 are platform-wrapped and passed only @ macos 26.0; spec line 406 carries an Apple ID email), 5 Minor (clean-state.log range 6-16; P43 confirmation only in the gitignored ledger; 1,176/46 counts unlogged; "re-confirmed" gate claim unlogged; README "P1–P47" range)
- Controller check: catalog-after.log shows the gate compiles each block on ONE target even when the file declares two; blocks containing `#if os(` in game-loop-and-threading.md are #1, #4, #11, #12 and in display-and-upscaling.md one block — all compiled @ macos only
- P50. Ruling: fix the gate in this round instead of deferring item 39 — a block containing `#if os(` compiles on every target its file declares, and must pass on each — the review found shipped instances, so item 39's trigger has fired — cost if wrong: a larger fix round, and possibly a shipped snippet edit if an iOS branch fails
- P51. Ruling: redact the email parenthetical at spec line 406 and say so in the append — the user's standing rule (no Apple ID emails in committed records) outranks "do not edit approved text", and the redaction changes no decision — the email stays in this unpushed branch's history (Task 0 commit); whether to rewrite that history before a push is the user's call, raised at the finish — cost: none in the tree
Task 13: fix round 1 — resume implementer ad32af64721b26c38
Task 13: fix round 1 DONE 5e1efe4 + 3d25847 (gate P50: 5 wrapped blocks now PASS @ ios 26.0 too, no snippet changes; email redacted P51; minors; gates-fix.log). Concerns: redact P44 emails in the ledger copy (controller); apple-gpu-tbdr.md:90-111 targetEnvironment(simulator) branch outside P50, recorded in item 39/§2; CONVENTIONS.md one-sentence rule added (unasked, accepted — the rule belongs there)
Task 13: re-review round 1 a71d04cd163c8ce0b (sonnet) on 02b636b..3d25847
Task 13: re-review round 1 — all 7 ADDRESSED, no new breakage. Parked for final review: gate trigger is the literal `#if os(` (not `#if !os(`, `#if canImport`, `#if targetEnvironment`) — no shipped multi-target block uses those forms; email remains in unpushed history (P51, user's call at finish)
Task 13: complete (02b636b..3d25847, review clean after 1 fix round); tag deferred to after the final review (P47)
Final review: BASE origin/main 838ccda, HEAD 3d25847
Final review: a8c7e85aaee8093f0 (opus) on 838ccda..3d25847
Final review: With fixes — 0 Critical, 1 Important (sendOverDTLS OS 26 branch hangs in .waiting; item 40's task-group alternative would also hang), 11 Minor. P36, P45, P48 accepted; gate trigger acceptable for this release
- P52. Ruling: the final fix dispatch fixes Important 1 and Minors 4 (overlay ring after the wait), 5 (drawable-before-wait trade-off), 6 (release-block guard), 7 (xcode-cargo.sh does not archive), 8 (Team ID wording), 10 (apple-frameworks "in a game"), and Minor 2's SKILL.md sentence (scope "compiles at that deployment target" to what the gates do); deferred items for Minor 2's C++ floor gate change, 3 (MSL 4.0 compile of unlabelled blocks), 9 (apple-performance description exclusion — evals pass, a description edit needs an eval sweep), 11 (R4 fixture self-assert), the broader #if trigger + targetEnvironment(simulator) note on item 39, and the P38 revisit — why: text fixes in shipped files are cheap and user-facing; gate and description changes need their own test cycle — cost if wrong: deferred minors ship as known limits, each with a deferred item
- Pre-push for the user (not tree): Apple ID email in commit 97cecb9 history (P51); all branch commits authored with a manhattan.edu address while recent main uses the personal domain; ledger copy must redact P44 emails; tag after this round (P47)
Final fix: BASE 3d25847
Final fix: implementer a4594042e6c57ed93 (opus), brief final-fix-brief.md (F1–F8 fix, D1–D6 defer)
Final fix: DONE_WITH_CONCERNS c071b41 — F1: both 3d25847 branches hang (.waiting 8 s; .preparing 180 s against a peer that never answers); fix adds timeout (default 5 s) + task group, withTaskCancellationHandler on OS 26, checkCancellation before the OS 27 send (OS 27 NetworkConnection.send in a pre-cancelled task leaks its continuation); cancel delivers ECANCELED to the pending completion in ≤2 ms (f1-probe*.log). F2–F8 text fixes; deferred 42–47 (D1–D6); item 40 resolved. Gates: bun 542/0, audit 0, validate + --strict pass, check_verbatim 12/12
Final fix: controller wrote final-fix/report.md from the returned text (P10), c466628
Final fix: re-review dispatched (opus — F1 is concurrency) on 3d25847..c071b41
Final fix re-review (aa9cb9b24092de682, opus): F1–F8 and D1–D6 all ADDRESSED; every F1 exit path traced (one resume site; cancel delivers the completion); probe hash matches the shipped block; 4 Minor wording faults + report "23 cases" (20)
- P53. Ruling: the controller fixed the four Minors and the count itself (P36 size) instead of a second fix round — the skill allows one final fix dispatch; these are wording, and two touch only comments inside the probed block — residuals.log proves the comment-only diff (probed 7058b6cb… → shipped 34dc5dba…) and re-runs the gates (Swift 9/9, 11/11; native 6/6; Vale 0 errors, input.md back to 7; bun 542/0; audit 0; --strict pass) — cost if wrong: four sentences shipped without an independent read
Final review: closed (aace63d). Phase 10 complete pending the user's push decisions. Ledger copy to $REC/sdd-ledger.md with Apple ID emails redacted (P2, P51); tag apple-studio-v0.11.0 on that commit (P47)
- P54. Ruling (supersedes P47's timing): tag apple-studio-v0.11.0 on main's merge commit after the PR merges, not on the branch head — the existing tags (v0.10.0, v0.9.1) are lightweight tags on main's PR merge commits, and a squash merge would leave a branch-head tag off main — cost: none; one command after the merge
- Record note: P37 was written to global-constraints.md at Task 7 dispatch and not to this ledger; its text, copied here at the close:
- P37. Ruling: Task 7 readers write ledger rows page by page (a usage-limit stop in Task 4 needed resumes); a g-slice reader's own skill is apple-games, so its six files use bare headings and apple-metal material goes under `## apple-metal/<file>`; p01's own file is `## profiling-workflow.md`, r01's is `## direct-distribution.md` — cost: none.
