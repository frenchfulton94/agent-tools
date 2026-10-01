# Deferred items

Not-now items carried forward from the Phase 1 whole-branch review (superseded
`docs/phase-1-debt.md`, cleared by Phase 2 Task 0 — see
`.superpowers/sdd/2026-08-04-phase2-design-ux/task-0-report.md`). None of these
block Phase 2; each has an explicit trigger for when to act.

1. **Kill-switch load-frequency check — measured 2026-08-04, Phase 3 Task 0.**
   Method: `grep -rlE 'swift-reviewer|design-reviewer' ~/.claude/projects
   --include='*.jsonl'` found 248 files with a text mention (136
   `swift-reviewer`, 233 `design-reviewer`); 18 were scratchpad/fixture-harness
   sessions (`-scratchpad-`/`-private-tmp-` in the project path) and excluded.
   Of the remaining 230, a structural scan (JSON-parsed every `Agent`/`Task`
   tool_use block for an `input.subagent_type` containing "reviewer") found
   only 7 genuine agent invocations — the other 223 files were text
   mentions only: mainly the per-session `agent_listing_delta` attachment
   that lists every installed agent (including `apple-studio:swift-reviewer`
   and `apple-studio:design-reviewer`) at session start regardless of
   project or use, plus incidental discussion in unrelated planning
   transcripts. Of the 7 genuine invocations, 3 were `brand-studio:design-reviewer`
   — a same-named but unrelated agent from a different plugin, out of scope
   for this measurement (2 in `Documents/brand-studio`, 1 in
   `Projects/chizyhub`). The remaining 4 were apple-studio's own agents, all
   in the `apple-studio` project itself: 2× `apple-studio:swift-reviewer`
   (sessions `7144207a…`, `3ef371c5…`) and 2× `apple-studio:design-reviewer`
   (sessions `e1f504a9…`, `dd71bab2…`). Each of the 4 confirmed as a genuine
   invocation (Task tool_use naming the agent, followed in the subagent
   transcript by `Read` tool_uses on `skills/*/references/` paths — 11 files
   / 2,062 lines for swift-reviewer, 6 files / 801 lines for design-reviewer,
   matching this doc's original line-count estimate). But every one of the 4
   is a plugin-verification/fixture run, not real-world use: the invoking
   user message is literally "Use the swift-reviewer agent to review
   pipeline/fixtures/flawed/FlawedFeature.swift…" (both swift-reviewer runs)
   or "…review the screen in /tmp/flawed-profile.png; source file is
   ~/Projects/StudioFixture/StudioFixture/FlawedProfileScreen.swift…" (both
   design-reviewer runs) — StudioFixture and `pipeline/fixtures/flawed/` are
   the plugin's own acceptance-test fixtures. **Result: 0 genuine invocations
   of either reviewer agent outside the plugin's own verification runs.**
   **Agent gate: FAIL.** Deferred: release-preflight agent; trigger: first
   real release.

   **Phase 4 decision (2026-08-04): one-phase grace.** Both reviewer agents
   (`swift-reviewer`, `design-reviewer`) are kept unchanged despite the
   0-genuine-use measurement. Rationale: no real feature work has happened
   yet for them to be used in — the measurement cannot distinguish "not
   useful" from "not yet needed". **Trigger: the kill-switch rule fires for
   real at the Phase 5 opening measurement unless a genuine non-fixture
   invocation has occurred by then.**

   **Phase 5 decision (2026-08-05): kill-switch fired — agents cut.**
   Re-measurement found 7 hits, all fixture/out-of-scope (evidence:
   `.superpowers/sdd/2026-08-04-phase5-animations/task-0-killswitch.log`).
   Two consecutive zero measurements; the Phase 4 grace trigger fired as
   written. Both agent definitions deleted; all skills/references kept.
   **Restore pointer: both agents recoverable from the v0.5.0 tag
   (`git show v0.5.0:plugin/agents/<name>.md`). Restore trigger: the first
   real workflow that needs one.** Pointer re-checked 2026-09-12:
   `git ls-tree -r v0.5.0 --name-only` still lists
   `plugin/agents/design-reviewer.md` and `plugin/agents/swift-reviewer.md`.
   A restore pointer nobody tests is a guess, so this gets re-checked whenever
   the item is touched.

   **Phase 6 measurement (2026-09-02): the rule pointed at skills for the
   first time — measured, gate NOT fired.** Both agents are gone, so Phase 6
   is the first sweep where the kill-switch rule has skills as its only
   subject. The agent scan was adapted from `input.subagent_type` on
   `Agent`/`Task` blocks to `input.skill` on `Skill` blocks: 3,440 transcripts
   across 596 project directories yielded **128** distinct
   (session, skill, date) invocations naming an `apple-studio:*` skill.
   All 128 came from exactly two project directories — the plugin repo
   (101) and `StudioFixture` (27) — with no third directory anywhere in the
   set. **Result: 0 genuine non-fixture invocations since 2026-08-05.**
   Evidence:
   `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/task-0-killswitch.log`.

   Recorded alongside the zero, because it is a different fact: **all nine
   shipped skills fired**, 8–28 times each (`swift-concurrency` 28,
   `xcode-loop` 22, `swift-architecture` 16, `apple-design` 14,
   `app-release` 12, `swift-testing` 10, `apple-frameworks` 9, `apple-macos`
   9, `apple-animations` 8). Nothing here shows a skill that fails to
   trigger; it shows skills that trigger reliably in the eval harness and
   have not yet been put in front of real feature work. This is **not** the
   first evidence the plugin is earning its keep — that evidence does not
   exist yet.

   **Decision rule, taken at spec time and applied unchanged (not
   improvised at measurement time):** a skill is cut or merged only after it
   has been available during **real feature work on a real project** and
   still not fired. Charter verification item 6 remains a PARTIAL PASS — no
   real feature has shipped through this plugin — so the precondition is
   unmet and **no skill is cut in Phase 6, regardless of the count**. The
   count was always going to be zero; the rule was written first precisely
   so that outcome could not re-open the question.

   **Hard trigger: the skill gate fires at the opening sweep of the first
   phase following a shipped real feature, and does not renew again on
   "not yet needed" grounds.** The agents got an ad-hoc one-phase grace in
   Phase 4 that drifted a full phase before firing in Phase 5. This is not a
   second open-ended grace: it is a precondition with a named event. If at
   that point the honest reading is that the plugin has grown skills nobody
   loads, the rule says deletion is a feature, and it gets applied.

   **Phase 7 measurement (2026-09-12): second consecutive zero, method
   unchanged.** Re-run of the Phase 6 scan above, scoped to sessions since
   2026-09-02 (the prior measurement date): 3,153 transcripts across 425
   project directories yielded **80** distinct (session, skill, date)
   invocations naming an `apple-studio:*` skill, all 80 from a single
   project directory — `StudioFixture` — with zero hits in the
   `apple-studio` repo itself this time, confirmed by direct grep of its own
   transcripts rather than the classifier alone: those invoke `superpowers:*`
   and `controlled-engineering-english`, no `apple-studio:*` skill. **Result:
   0 genuine non-fixture invocations since 2026-09-02.** Evidence:
   `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/task-0-killswitch.log`.

   Worth recording separately, the same distinction Phase 6 drew: two skills
   absent from the Phase 6 tally now show hits — `apple-intelligence` (15)
   and `apple-performance` (24), both shipped in Phase 6 and exercised since
   only inside the fixture. All eleven shipped skills have now fired at
   least once in the harness; none have fired outside it.

   **Decision rule applied unchanged, not improvised:** the precondition
   stated above — a shipped real feature — remains unmet, so **no skill is
   cut this phase, regardless of the count.** The count is zero again, which
   is a repeat of the prior finding, not a new reason for the outcome.

   **Phase 9 measurement (2026-09-30).** This re-runs the Phase 6/7 scan,
   scoped to sessions since 2026-09-12 (the prior measurement date). It
   found 2,168 transcripts and **0** genuine non-fixture invocations of an
   `apple-studio:*` skill. All 60 excluded invocations came from a single
   project directory, `StudioFixture`. Evidence:
   `records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch.log`.

   **Decision rule applied unchanged, not improvised:** the precondition —
   a shipped real feature — remains unmet, so **no skill is cut this phase,
   regardless of the count.**
2. **Stop-gate session-start baseline (only on observed pain).** Add a
   session-start baseline build capture to `stop-gate` to avoid a one-turn
   false block on projects that were already red before the session started.
   Build only if this false-block actually happens in practice — no
   preemptive build.
3. **Xcode plug-in surface (found 2026-08-04).** Re-import of apple-studio
   into Xcode 27 (delete + Add Plug-in at `~/Projects/apple-studio`, phase-2
   working tree) succeeded. The import dialog explicitly lists the plug-in's
   contents as "2 subagent definitions, hooks" alongside the skills — Xcode
   detects and imports agents (`swift-reviewer`, `design-reviewer`) and
   hooks, resolving the previous open question at the import layer. The
   post-import detail view enumerates skills only (all six: apple-design,
   apple-frameworks, swift-architecture, swift-concurrency, swift-testing,
   xcode-loop) with Version 0.2.0 (correct — pre-bump working tree);
   agents/hooks are imported but not enumerated by name in that view. Xcode
   imports a **copy** of the plugin — re-import after each merge remains the
   operational rule.

   **Phase 5 update (2026-08-05):** both subagent definitions were deleted
   in the Phase 5 opening sweep (item 1's kill-switch decision). The import
   dialog's "2 subagent definitions" line will disappear at the next
   re-import — expect "hooks" alongside the skills, with no subagent count.
4. **Exercise agents/hook inside an actual Xcode Claude Agent conversation.**
   Runtime behavior of `swift-reviewer`/`design-reviewer` and the
   `stop-gate` hook inside an Xcode Claude Agent conversation is still
   unexercised (item 3 confirmed import only). Natural moment to close this:
   first real design-review use in Xcode.

   **Phase 5 update (2026-08-05):** the agent half of this item is moot —
   both `swift-reviewer` and `design-reviewer` were deleted in the Phase 5
   opening sweep (item 1's kill-switch decision, two consecutive zero
   measurements). This item now narrows to the `stop-gate` hook alone:
   its runtime behavior inside an Xcode Claude Agent conversation is still
   unexercised. Revisit the agent half only if item 1's restore trigger
   fires (a real workflow that needs one of the deleted agents).

   **ANSWERED 2026-09-12 — the gate is inert in Xcode.** Exercised in Xcode
   27.0's Claude Agent against StudioFixture. The **Stop** hook runs, with a
   correct `CLAUDE_PLUGIN_DATA`, `cwd`, and a payload that is a superset of
   Claude Code's. The **PostToolUse** hook does not run at all — confirmed by
   instrumenting Xcode's own copy of both scripts to log before any early
   exit. So nothing writes the `.edited` marker, `stop_gate.sh` exits at its
   marker check on every Stop, and the gate never builds and never blocks.
   It fails open exactly as the convention requires, which is why four phases
   passed without anyone noticing: **a hook that fails open is silent when it
   is broken.**

   Two independent defects would each break tracking on their own, and both
   are real: the matcher `Edit|Write|MultiEdit` does not select Xcode's
   `mcp__xcode-tools__XcodeWrite`, and `track_swift_edits.sh` reads
   `.tool_input.file_path` while Xcode's tool sends `filePath`. Neither is
   the root cause: rewriting Xcode's copy of the matcher to `.*` still
   produced no PostToolUse invocation. Evidence:
   `.superpowers/sdd/2026-09-12-debt-items-2-5/item-2-report.md`,
   `item-2-probe.log`.

   **FIXED same day, 2026-09-12.** `stop_gate.sh` no longer depends on
   PostToolUse having run: when the marker is absent it reads the
   `transcript_path` the Stop payload already carries and scans it for writes
   to `.swift` files, accepting both `file_path` and `filePath`, and matching
   tool names on `Write|Edit` so `mcp__xcode-tools__XcodeWrite` is caught
   without enumerating hosts. It records how many transcript lines it has
   scanned, so a green build stays green instead of rebuilding on every Stop
   from the same old edits. `track_swift_edits.sh` accepts both key spellings
   too, for the hosts where PostToolUse does run.

   Verified end to end against the real fixture, not only in unit cases: a
   deliberately broken Swift file produced
   `{"decision":"block"}` carrying the actual compiler error, driven purely by
   the transcript path with no marker in play; fixing the file produced a
   silent exit 0 and cleared the marker. `pipeline/test_stop_gate.sh` covers
   10 cases / 17 assertions offline, including fail-open with `jq` hidden and
   the rebuild-loop regression.

   **CONFIRMED IN XCODE the same day.** Re-imported, then asked Xcode's agent
   for an edit that cannot compile. The gate built, failed, and blocked the
   completion claim in 27 s. Filesystem evidence, not the agent's self-report:
   a `.edited` marker naming `ContentView.swift`, a `.scanned` watermark of 24
   lines, and a 30 KB build log carrying
   `ContentView.swift:9:26: error: cannot convert value of type 'String' to
   specified type 'Int'` — all under
   `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/plugins/data/apple-studio-inline/stop-gate/`,
   copied to `item-2-xcode-confirmed/`. **This item is closed.**

   Detail worth keeping: Xcode's `filePath` arrives **project-relative**
   (`StudioFixture/StudioFixture/ContentView.swift`), not absolute. The gate
   only needs to know a Swift file changed, so it matches either way — but any
   future hook that tries to *resolve* that path must not assume absolute.

5. **SwiftUI / Animation Hitches instrument path — unverified (found
   2026-09-02, Phase 6 Task 9).** The Time Profiler half of the performance
   workflow was verified end to end with real before/after numbers (4961 ms ->
   1246 ms in the planted function, identified from the trace rather than from
   prior knowledge). The SwiftUI half was not: the fixture's SwiftUI scene never
   activated in the execution session — `RowView.body`, instrumented to log
   every invocation, recorded **zero** with the process at **0.0% CPU** across
   four launch methods (direct, `open(1)`, under a pty, and after `osascript`
   activation, each after killing prior instances to defeat bundle-ID reuse).
   `List` is lazy, so rows that never render never compute, and a list that
   never renders cannot hitch.

   Untested as a result: the **Animation Hitches** template, the
   commit-hitch/render-hitch split, and the **SwiftUI** instrument's View Body
   Updates / Update Groups / Show Causes lanes.
   `plugin/skills/apple-performance/references/swiftui-performance.md` ships on
   doc fidelity and snippet compilation alone — it is the only file in the
   plugin with no runtime exercise behind it.

   **Trigger: the next time anyone runs Xcode interactively on a SwiftUI
   project.** Product > Profile with the Animation Hitches and SwiftUI
   templates, and confirm the documented lanes show what the reference says
   they show. This needs a human at a GUI session; it is not automatable from a
   headless shell, and repeated attempts to force it were the wrong instinct.
   Evidence:
   `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/task-9-report.md`.

   **HALF CLOSED 2026-09-12.** Run on an iPhone 16 Pro Max (iOS 27.0) from the
   Instruments GUI, with the regression re-planted as a 400-row `List` whose
   rows cost ~6 ms each. **Animation Hitches: verified** — 79 hitches, and the
   commit/render split reads as 73 frames flagged in the `updates` lane against
   1 in `renders`, which is where the planted app-side cost belongs. Three
   claims were corrected in the shipped references as a result: hitches are
   **not** labelled "commit" or "render" (the column is *Potential Issue*, e.g.
   "Potentially expensive app update(s)"); the SwiftUI lane names in both our
   file and Apple's live doc are stale against Xcode 27, which shows *Update
   Groups*, *Long View Body Updates*, *Long Representable Updates*, *Other Long
   Updates*; and the "blue = your objects, gray = system" claim about Show
   Causes is unsourced and was removed. Both files now carry a `gui-verified:`
   header line.

   **The SwiftUI half remains unexercised, for a new reason.** That template
   recorded nothing — twice, 29.5 s of scrolling, zero rows in all 20 tables
   including `time-profile`, with "No Data" in the GUI and after clearing the
   toolbar filter — on the same device and session where Animation Hitches
   captured 275 MB. **Next trigger: one run with the scheme's Profile action
   set to Debug** (Profile builds Release by default); if the SwiftUI
   instrument needs a debuggable build, that is both the explanation and a line
   the reference should carry. Evidence:
   `.superpowers/sdd/2026-09-12-debt-items-2-5/item-3-report.md`.

   **STILL OPEN at the close of Phase 7 (2026-09-12) — the trigger was not
   consumed.** The Phase 7 spec named this phase's real exercise as the
   occasion to run the SwiftUI template with the scheme's Profile action set to
   Debug. That did not happen. The exercise was split: Task 3a ran the
   automatable half in the Simulator — a drag-to-dismiss surface, both
   projections logged, 48 flicks — and deliberately ran no Instruments session,
   because the SwiftUI template's failure is a GUI-and-device symptom that a
   headless simulator run cannot reproduce or refute. Task 3b, the device half,
   is Michael's and is outstanding. **The trigger stands exactly as written
   above** — one run, Profile action set to Debug — and is not renewed on new
   grounds, extended, or weakened by having been named in a phase spec and not
   reached. Evidence that the simulator half ran without it:
   `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/task-3a-report.md`,
   `task-3a-commands.log`.

   **The rest of Task 3b is item 10**, added at the same close: the physical-device
   flicks and the feel judgment. They are tracked separately so that this item's
   trigger — one run, Profile action set to Debug — is not silently renewed or
   broadened by being bundled with them. Whoever picks up one should read the other;
   both need the same human at the same GUI session.

6. **The eval harness can write to the fixture despite `--allowedTools`
   (found 2026-09-02, Phase 6 Task 10).** The sweep runs
   `claude --plugin-dir ... --allowedTools "Skill Read"` from
   `~/Projects/StudioFixture`. That does **not** stop the session from creating
   and modifying files: the Phase 6 sweep left nine source files, a `build/`
   directory, and modified `ContentView.swift`/`StudioFixtureApp.swift` behind,
   each traceable to a specific eval prompt. Fully restored with
   `git clean -fd` + `git restore .`.

   Phases 3-5 ran the same harness against the same fixture on the assumption
   that `--allowedTools` bounded it. **Action for the next phase that runs
   evals:** check `git -C ~/Projects/StudioFixture status --porcelain` in the
   *closing* verification pass, not only after the task that deliberately
   touches the fixture — this was caught only because the final pass re-checked
   rather than trusting an earlier revert. A dirty fixture does not invalidate
   trigger-eval verdicts (they depend on which skill fires, not on file
   contents), but it would quietly contaminate any prompt that reads the
   project. Evidence:
   `.superpowers/sdd/2026-09-02-phase6-intelligence-performance/task-10-evals/README.md`.

   **CLOSED 2026-09-12 — enforced rather than remembered.** The driver is now
   `pipeline/run_evals.py`, and the check is behavior: it reads the fixture's
   git status before the sweep, after **every** prompt, and at close; it
   attributes writes to the prompt id that made them, restores the tree, and
   exits non-zero. It also refuses to start on a dirty fixture, because writes
   made during a sweep that began dirty cannot be attributed. The other two
   Phase 6 harness defects are carried as behavior too — stdin at `/dev/null`
   for the leak, and `--max-turns 6` by default, with an `error_max_turns` run
   reported in its own column rather than scored as a silent miss.
   `pipeline/test_run_evals.sh` self-tests four cases offline against a
   throwaway repo (12 assertions), and a live sweep of three Phase 6 prompts
   reproduced their recorded verdicts exactly. Evidence:
   `.superpowers/sdd/2026-09-12-debt-items-2-5/item-4-selftest.log`,
   `item-4-live-sweep/results.tsv`.

   **Amended 2026-09-12, Phase 7 Task 4 — the cause is now known, and it reaches
   further than the fixture.** The guard above still holds: 8 of 35 prompts wrote
   to the fixture, every write was attributed to its prompt, the tree was restored
   and the driver exited non-zero. But the sweep also showed **why** the writes
   happen. `--allowedTools "Skill Read"` does not restrict tool use at all —
   `Bash` ran in essentially every session in the sweep, visible as `tool_use`
   blocks in the transcripts. It is not that writes slip past an allow-list; there
   is no effective allow-list.

   Two consequences, both measured rather than reasoned:

   - **A session can leave the fixture entirely, and writes landed in a real
     project.** `xcode-fire` ("Run the test suite for BreeziTip") searched
     StudioFixture, found nothing, walked up to `~/Projects` and then `~`, and
     located `~/BreeziTip/Projects/breezitip_new` — an unrelated real project.
     **The escape scales with the turn budget.** In the sweep, at `--max-turns 6`,
     it exhausted its turns on `ls`/`grep` reconnaissance and executed nothing
     (`error_max_turns`, 7 turns). In the `--max-turns 12` rerun it had budget to
     act: it `cd`'d into the project, ran `bun run db:migrate`, then `bun run
     test`, and returned `success` at 15 turns. Raising the cap enlarges the blast
     radius, not just the runtime.

     **Writes did land**, at 18:30:06–18:30:18, inside that session: miniflare D1
     state under `.wrangler/state/v3/d1/miniflare-D1DatabaseObject/*.sqlite-{shm,wal}`,
     regenerated sources **inside the source tree** at
     `src/lib/paraglide/messages/*.{js,d.ts}`, and `.svelte-kit/generated/*`. The
     substance is benign — build artifacts and local dev state, no remote writes,
     no surviving process — but the original note here claimed "nothing was
     damaged" on the strength of a `git status` check, and **that check could not
     have seen any of it**: every one of those paths is gitignored, confirmed with
     `git check-ignore`. An empty `git status` in a repo with a real `.gitignore`
     is not evidence that nothing was written. Corrected 2026-09-12 in the same
     pass that made the claim. Do not put a prompt naming a real project outside
     the fixture into a sweep corpus.

     **The prompt is gone, 2026-09-12, at the close of Phase 7.** Leaving the rule
     here while the prompt stayed in the corpus meant the next sweep would have run
     it again — and the corpus ships to users, so a private project name was also
     going out in every install. `plugin/skills/xcode-loop/evals/triggers.md:4` now
     reads **"Run the test suite for this project and show me the failures"**,
     which is verbatim the `diag-xcode` probe that routed to `xcode-loop` in this
     phase's diagnostic run, so the replacement is measured rather than assumed
     (`task-4-evals-diagnostic/prompts.tsv:9`, `results.tsv:4`). The historical
     records of the escape keep the original wording on purpose: it is what ran.
   - **Prompts that name code the fixture does not have fail for a reason that
     has nothing to do with routing.** `anim-fire-8` ("this sheet"), `test-fire`
     ("this view model") and `xcode-fire` ("BreeziTip") each sent the session
     hunting for a file in a bare Xcode template. All three reproduce at
     `--max-turns 12`, so this is not turn exhaustion.

     **The mechanism is not "it never reached the answering step" — that was the
     first reading and it is wrong.** Only `test-fire` behaves that way, ending
     "I'd need to know what it should do rather than invent behavior to test".
     `anim-fire-8` **did** reach an answering step in both runs (`success`, 7
     turns at the 6-cap and 8 at the 12-cap) and answered from priors with three
     to four ranked hypotheses **without ever loading the skill**; `xcode-fire` at
     12 turns answered in the wrong repository. The accurate statement is that a
     missing referent shifts the session into **answering blind from priors**
     rather than into loading the skill. That is a more interesting failure than
     turn exhaustion, and a worse one: the output looks like a confident answer.

     All three pass when the same question is asked in how-to form —
     `diag-sheet`, `diag-test`, `diag-xcode`, 3/3, same skills and settings — but
     **none of the three is a clean single-variable control.** `diag-sheet` also
     adds "drag-to-dismiss" and `diag-test` also adds the literal skill name
     "Swift Testing", so each moves the referent *and* the vocabulary. `diag-xcode`
     was described here as swapping the referent alone, and **that was wrong**,
     corrected 2026-09-12 by diffing the two prompt files rather than re-reading the
     sentence: the sweep asks "Run the test suite for BreeziTip"
     (`task-4-evals/prompts.tsv:38`) and the probe asks "Run the test suite for this
     project **and show me the failures**" (`task-4-evals-diagnostic/prompts.tsv:9`),
     so it appends a clause as well as swapping the referent. It is the closest of
     the three and still not clean. The conclusion above rests on the transcripts —
     `anim-fire-8` answering blind without loading the skill — and not on any of
     these probes; they are weaker evidence than a 3/3 suggests.

   **Trigger: before the next sweep, walk the corpus for prompts whose referent
   the fixture does not contain**, and either seed the fixture with that code or
   mark the prompt as fixture-dependent. A prompt that cannot run in the fixture
   produces a FAIL that looks exactly like a skill miss, and "fixing" it by
   editing a skill description is the Phase 6 mistake in a new costume. Evidence:
   `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/task-4-evals/README.md`,
   `task-4-evals/results.tsv`, `task-4-evals-rerun/results.tsv`,
   `task-4-evals-diagnostic/results.tsv`.

7. **The snippet ship gate was never run backwards over Phases 1-5 (found
   2026-09-12, Phase 7 planning).** `pipeline/typecheck_snippets.py` was
   written in Phase 6 and run only over Phase 6's own output, which passed
   22/22. Running it across every shipped reference gives **28/48 clean** —
   20 failures across 13 files, every one of them authored in Phases 1 to 5.
   Zero failures in Phase 6 files. Breakdown: `apple-macos` 7,
   `apple-animations` 5, `apple-design` 3, `swift-testing` 3,
   `swift-concurrency` 2.

   **Not all of them are defects, and that is the point — nobody has triaged
   them.** The one in `apple-design/references/animation-taste.md` is
   `@State private var committedOffset: CGFloat = 0` at top level, which
   fails as `'nonmutating' is only valid on methods` because the fragment has
   no enclosing `View`. That is a framing artifact and the fix is to show the
   struct. A different failure might be an invented symbol, which is what the
   gate exists to catch. The two are indistinguishable from the count alone.

   **Trigger: triage every outstanding failure in the phase after Phase 7**,
   one pass, each classified as framing artifact or reference defect before
   anything is edited. **The count is 19, not the 20 written here** — Phase 7
   fixed the single `animation-taste.md` failure, because Phase 7 edits that file
   and would otherwise leave a known-red file redder, and touched none of the
   other 19. The number is stated once, in the corrected baseline below; this
   paragraph deliberately no longer carries a second copy of it, because it
   carried 20 while the amendment carried 19 and a scanner reading only one of
   them got it wrong. **19 is the live figure.**

   Related, same date: `typecheck_snippets.py`'s `FRAMEWORK_HINTS` had no
   entry for CoreGraphics, so a snippet using `CGFloat` and no SwiftUI type
   failed with "cannot find type 'CGFloat' in scope" — which reads exactly
   like an invented symbol. Fixed in Phase 7 planning by adding a
   `CoreGraphics` hint and extending the SwiftUI hint to cover gesture and
   animation types. The 28/48 baseline above is identical before and after
   that fix, so it changed no verdict; it removed a false-failure mode.

   **Baseline corrected 2026-09-12 at the close of Phase 7 — it is now 32/51,
   and the untriaged count is 19, not 20.** The 28/48 figure above was measured
   before Phase 7 wrote anything, and Phase 7 moved it twice. Task 1's new
   `fluid-interfaces.md` added three blocks, all passing (48 -> 51, 28 -> 31).
   Task 2's `@State` framing fix converted the single pre-existing failure in
   `apple-design/references/animation-taste.md` (31 -> 32), which is the one
   repair this item authorized. 51 - 32 = 19 outstanding, and the arithmetic
   closes: 20 - 1 = 19.

   Re-measured rather than derived, with the same command as the original:
   `python3 pipeline/typecheck_snippets.py plugin/skills/*/references/*.md
   plugin/skills/*/references/primers/*.md` -> `TOTAL: 32/51 snippets typecheck
   clean`. Revised breakdown, now 19 failures across **12** files rather than 20
   across 13 — `animation-taste.md` has left the list entirely: `apple-macos` 7
   (`mac-app-structure` 3, `mac-sandbox-and-files` 2, `appkit-interop` 1,
   `mac-windows-menus-commands` 1), `apple-animations` 5
   (`transitions-and-matched-geometry` 3, `scroll-and-visual-effects` 2),
   `swift-testing` 3, `apple-design` 2 (both `accessibility.md`),
   `swift-concurrency` 2. Zero failures in Phase 6 and Phase 7 files.
   **The trigger is unchanged: triage all 19 in the phase after Phase 7**, one
   pass, each classified as framing artifact or reference defect before anything
   is edited. 19 is the single live count for this item; the trigger paragraph
   above defers to it rather than restating it. Evidence:
   `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/task-4-typecheck-repowide.log:4627`
   (the `TOTAL:` line), summarized in `task-4-typecheck-summary.txt:1-18`.

   **Phase 9 (2026-09-30).** Item 7's trigger — triage in the phase after
   Phase 7 — passed in Phase 8 unaddressed. Phase 9 triaged the two
   `apple-design` failures. Both are framing artifacts, each paired with a
   reference defect: a deprecated `accentColor`, and `AnyView` in a ternary.
   Phase 9 fixed both. Evidence:
   `records/2026-09-30-phase9-adaptive-layout/task-3-a11y/triage.md`. 17
   failures remain, none in `apple-design`. The trigger stands: triage them
   in the next phase.

8. **The SDD tooling rewrites `.superpowers/sdd/.gitignore` to `*` on every
   invocation (found 2026-09-12, Phase 7 Task 0; root cause found Task 1).**
   `scripts/sdd-workspace:39` in the superpowers `subagent-driven-development`
   skill does `printf '*\n' > "$base/.gitignore"` unconditionally, with no
   existence check and no merge. That reverts the deliberate-tracking version
   committed in `2ec677c`, whose own comment says "If the tooling rewrites this
   file back to `*`, that is the regression to fix". Verified in both installed
   copies, 6.2.0 and 6.3.0, at the same line.

   **It is not one script, it is three.** `scripts/task-brief:24` and
   `scripts/review-package:28` both shell out to `sdd-workspace` to derive the
   workspace path, so extracting a task brief and building a review package each
   clobber the file too. A phase that never calls `sdd-workspace` directly still
   triggers it once per task and once per review round.

   **The failure mode is silence.** Nothing errors and nothing is deleted; the
   evidence simply stops appearing in `git status`, so the commit that was
   supposed to carry it is made without it. In Phase 7 it fired at least three
   times and Task 0's evidence was missing from `e5885eb` as a result, restored
   in `b2fc721` only because the controller re-read the file rather than
   trusting the status output. This repo cites those logs by path from
   `docs/deferred.md` and from every spec's verification table (CLAUDE.md:
   "Every verification claim cites a log here"), so a citation that resolves to
   nothing outside this machine is a broken record.

   **Trigger — a standing check, not a Phase 7 incident.** At the close of any
   phase that runs `sdd-workspace`, `task-brief`, or `review-package`, run
   `git diff --stat .superpowers/sdd/.gitignore`; a non-empty diff means the
   tooling won and the file must be restored with
   `git checkout .superpowers/sdd/.gitignore` before the closing commit. Also
   re-check it whenever `git status` appears not to see files that were just
   written under `.superpowers/sdd/`.

   **There is also a bypass, which beats detecting it afterwards.** Both wrapper
   scripts skip `sdd-workspace` entirely when handed an explicit output path:
   `task-brief:21-24` is `if [ $# -eq 3 ]; then out=$3; else dir=$(sdd-workspace
   ...)`, and `review-package:25-28` is the same with `$# -eq 4`. So passing the
   destination as the final argument avoids the clobber for two of the three
   scripts; only `sdd-workspace` invoked directly has no escape. Confirmed in
   practice this phase — the Task 4 review package was built with an explicit path
   and the tracked `.gitignore` survived it, the first time this phase it did.
   Upstream fix if it is ever worth carrying: make the `printf` conditional on the
   file not already existing. Evidence:
   `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/progress.md:66-76` and
   `:105-109`.

9. **`apple-intelligence` takes a Foundation Models *performance* question that
   its own eval corpus assigns to `apple-performance` (found 2026-09-12, Phase 7
   Task 4).** `apple-intelligence/evals/triggers.md` lists
   "Why is my Foundation Models feature so slow?" under **Should NOT fire**, with
   the reason written beside it: "apple-performance — profiling, not
   implementation". It fires anyway. Reproduced at `--max-turns 6` and again at
   12, and it is not a fixture artifact — the session loaded the skill first and
   went to the references, rather than hunting for code and giving up.

   Not caused by Phase 7, which changed neither skill's description; both shipped
   in Phase 6 and this is the first sweep to sample that particular boundary. The
   bleed is one-directional and the opposite boundary is clean: `perf-not`
   ("Make this card flip with a spring animation") correctly routes away from
   `apple-performance` to `apple-animations`, and the Phase 7 addition `anim-not-5`
   ("Why does my ScrollView stutter when I scroll fast?") correctly routes away
   from `apple-animations` to `apple-performance`.

   **Not fixed here, deliberately.** One sampled prompt is thin evidence for
   editing either description, and description edits made in response to a single
   eval result are the failure mode Phase 6 recorded. **Trigger: sample this
   boundary with three prompts in the next phase's sweep** — "why is it slow",
   "why does it hitch", "why does first token take so long". If two or more bleed,
   add the profiling-versus-implementation split to `apple-intelligence`'s
   description; if only this one does, record the prompt as a known ambiguity and
   leave both skills alone. Evidence:
   `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/task-4-evals/results.tsv`
   (row `ai-not`), `task-4-evals/ai-not.log`, `task-4-evals-rerun/ai-not.log`.

10. **Phase 7's real exercise ran in the Simulator only — the device half and the
    feel judgment are outstanding (found 2026-09-12, Phase 7 close).** The Phase 7
    spec's definition of done asked for four things: build a drag-to-dismiss
    surface, implement both projections, measure an identical flick under each,
    **and confirm the ratio on a device rather than in arithmetic**. Task 3a
    delivered the first three in the Simulator — 1.996000 across 48 flicks, both
    directions, 201–2125 pt/s, min 1.995999, max 1.996000, with
    `predictedEndTranslation` implying exactly 0.250000 s of travel on 48 of 48 —
    and found a real defect in the shipped example while doing it. Task 3b, the
    human half, did not run. It is recorded here because `docs/deferred.md` is
    where this repo keeps its not-now items with triggers, and until now the only
    record of the outstanding two-thirds was the phase spec's "Carried forward"
    list and the SDD ledger. **It is the phase's largest known-incomplete item and
    it was the hardest to find.**

    Three things are owed, and none is a re-run of what 3a did:

    - **Flicks on a physical device at representative velocities.** The Simulator
      synthesizes pointer events; a finger does not. The ratio is linear in
      velocity and provable at any velocity, so this is not expected to move the
      number — it is expected to confirm that real touch input produces the same
      `velocity` and `predictedEndTranslation` relationship. A device reading
      outside 1.995–1.997 would falsify the reference's central claim, and the
      stop-gate in `docs/plans/2026-09-12-phase7-fluid-interfaces.md:187` states
      it in that form.
    - **The feel judgment.** The spec's own words are "a gesture is felt, not
      read", and nobody has yet felt the difference between the two projections.
      The reference's central recommendation — use `project(initialVelocity:)` for
      anything that should feel like scrolling — is measured but not experienced.
      Task 3a flagged one item specifically for this attention: whether the
      pre-fix snap-back at release is visible to the eye, or only to the frame
      trace. Record the answer as judgment, explicitly labelled as such.
    - **Confirm or refute the mid-flight-grab limitation in the shipped example.**
      `fluid-interfaces.md:165-176` states, as a reading of the code and labelled
      unmeasured, that `DismissableCard` cannot be caught in flight: `lastOffset` is
      committed to `target` at release, so a finger landing on a flying card composes
      its translation against the destination and the card jumps by the remaining
      travel. **That is a second unmeasured reading about the same release boundary
      that already defeated two readers.** Task 1's re-reviewer read it, could not
      settle it, and flagged it; the controller read the same mechanism and ruled the
      `@GestureState` example in; Task 3a measured it and both readings were wrong —
      191–210 pt of snap-back on 12 of 12 flicks. The note is honestly labelled and
      stays either way, but it must not sit indefinitely as a reading nobody checks
      when checking it is a short run on a harness that already exists: touch the
      card while it is still springing and observe the first frame, the same way 3a
      observed the release frame. Reuse `task-3a-harness.log`'s setup rather than
      building a new one. If it is refuted, the scope note goes; if confirmed, it
      stops being a reading and gets the measurement beside it.

    **Trigger: the next time anyone runs this plugin's guidance against a real
    gesture on a real device** — which is also the first occasion on which these
    questions can be answered honestly. Nothing headless or simulated substitutes for
    the first two, and a phase that names this exercise without reaching it does not
    consume the trigger; Phase 7 named it and did not, which is exactly the failure
    this item exists to keep visible. (The third piece does not strictly need a
    device — it runs on 3a's Simulator harness. It is tracked here rather than split
    off because it is the same boundary, the same harness and the same sitting.)
    Evidence:
    `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/task-3a-report.md:1-20`,
    `:344-366` (the item flagged for 3b), `progress.md:53-62` (the 3a/3b split
    ruling, taken before Task 3 started), and items 10 and 11 of the verification
    append in `docs/specs/2026-09-12-phase7-fluid-interfaces-design.md`.

    **The Instruments SwiftUI-template run — the remaining piece of Task 3b — is
    item 5, not this item.** It is tracked separately on purpose: item 5's trigger is
    older, narrower and deliberately unrenewed, and folding it in here would have
    re-opened it on new grounds. Whoever picks up one should read the other.

11. **52 validator warnings on the catalog, 40 of them apple-studio's — measured
    2026-09-12, Phase 8 Task 6.** `bun run audit:strict` now reports `0 error(s), 52
    warning(s)` for the whole catalog, up from the 12 the catalog carried before
    this phase. All 40 new ones arrived with apple-studio: 16 `apple-frameworks`
    primer files nested a level deeper than the validator expects and the same 16
    not linked from that skill's `SKILL.md` (one warning line apiece, same file
    set — `references/primers/*.md`), 37 reference files over 100 lines with no
    table of contents in their first 30 lines, and one `swift-testing` description
    missing a `Use when...` trigger clause. None are errors, and `bun run audit`
    (non-strict) is unaffected — exit 0.

    **Trigger: revisit if `audit:strict` is ever made a commit gate, or if a
    reader reports trouble navigating a long reference.**

12. **`~/Projects/StudioFixture` cited in a shipped reference (found 2026-09-12,
    Phase 8 Task 6).** `xcode-loop/references/headless-commands.md:6-7` names the
    fixture app by a path on one machine, inside a verified-against statement
    ("Verified against a Multiplatform SwiftUI app fixture
    (`~/Projects/StudioFixture`, scheme `StudioFixture`, ...)"). It is a
    provenance citation, not an instruction, so it ships as it stands.

    **Trigger: rewrite it the next time that reference is revised for any other
    reason.**

    **Resolved 2026-09-30, Phase 9 Task 8.** Task 8 edited
    `headless-commands.md` for the Duo pose section and rewrote the citation.
    Line 6 now names the fixture with no machine-specific path. This item is
    closed. Evidence:
    `plugins/apple-studio/skills/xcode-loop/references/headless-commands.md:6-7`.

13. **`apple-design`'s trigger evals fail in both directions (found 2026-09-12,
    Phase 8 final fix wave).** A sweep of the skill's own
    `evals/triggers.md` prompts scored 9/14. Four of seven should-fire rows
    reached no skill at all: the session explored the fixture with file-reading
    tools first, concluded there was nothing to review, and answered directly
    without ever considering routing (`stop_reason: end_turn`, no `Skill` call).
    One should-not-fire row — "Design our brand color palette" — wrongly reached
    `apple-design`, which its own description disclaims in as many words.

    The sweep ran while a candidate description edit was in place, and that edit
    was reverted for want of evidence. But the three rows probing the edit's own
    content all passed, and the failures are independent of it, so this is
    pre-existing rather than anything Phase 8 introduced. Two reviewers reached
    that conclusion separately. Part of the should-fire failure is the known
    `--allowedTools` leak that lets `Bash` run regardless, but not all of it:
    `Read` alone would reach the same "nothing here to review" conclusion on a
    stock-template fixture, so a harness fix would not settle it.

    Evidence: `.superpowers/sdd/2026-09-12-phase8-catalog-migration/final-fix-evals/`
    in the archived `apple-studio` repository — the TSV, `results.tsv`, and all
    14 session logs.

    **Trigger: before any phase that edits `apple-design`'s description, and
    before trusting a trigger-eval pass rate on a fixture with no real UI in it.**

    **Phase 9 (2026-09-30).** The fixture now has a real screen.
    `MailboxScreen.swift` adds a mailbox with `NavigationSplitView`,
    `TabView`, and per-context toolbars. It is committed to StudioFixture at
    `5287d2c`. `triggers.md` gained four Duo should-fire rows and two Duo
    should-NOT-fire rows.

    The baseline sweep, with the description unedited, scored 11/16 PASS.
    Should-fire rows scored 6/10: fire-1 through fire-6 passed, and fire-7
    through fire-10, the four Duo rows, all failed. Should-NOT rows scored
    5/6: nofire-1 ("Design our brand color palette") failed, and the rest
    passed.

    Full evidence is in `task-6-evals/classification.md`. fire-7 and fire-10
    are genuine Duo routing misses. The session never invokes the skill, and
    it answers from priors or asks an avoidable clarifying question. fire-8
    is a genuine Duo routing miss too. The session calls `xcode-loop`
    instead of `apple-design`. fire-9 is a prompt-wording defect, not a
    routing miss. The model reads "gets cut off" as a claim about its own
    message and never engages the task. This reproduced outside the fixture
    and outside the harness. nofire-1 reproduces the Phase 8 brand-color
    finding unchanged.

    Because fire-7, fire-8, and fire-10 are Duo routing misses, Step 8's
    description edit was made. The post-edit sweep also scored 11/16. fire-7
    and fire-8 were fixed. But two rows that passed in the baseline failed
    after the edit. nofire-6 ("What screenshot sizes does the App Store need
    for iPhone Duo?") now called `apple-design` first. The added "iPhone
    Duo" wording pulled it in, before the session self-corrected to
    `app-release`. fire-5 ("Add a confirmation flow before deleting")
    stopped calling any skill at all, for reasons the wording change does
    not explain. Per Step 9's rule, a regression on a previously-passing row
    reverts the edit. **The description edit is reverted. SKILL.md carries
    no diff from before Step 8.**

    **Item 13 is not resolved.** Open should-fire rows are fire-7, fire-8,
    and fire-10 — genuine Duo routing misses. fire-9 counts as non-routing
    per its classification and does not block resolution. The open
    should-NOT row is nofire-1, the pre-existing brand-color miss, unaffected
    by this phase's edit.

    **Trigger for the next try:** find a change that fixes fire-7,
    fire-8, and fire-10. It must not pull `apple-design` ahead of
    `app-release` on release-logistics questions that merely mention iPhone
    Duo. Evidence: `records/2026-09-30-phase9-adaptive-layout/task-6-evals/`
    (`prompts.tsv`, `baseline/results.tsv`, `after-edit/results.tsv`,
    `classification.md`).

    **Phase 9 Task 10 (2026-10-01).** A revised pair of description edits
    was swept three times per row, not once as before. The `apple-design`
    skill's description gained the Duo/pose/fold wording, plus an App
    Store screenshots exclusion. The `app-release` skill's description
    gained an App Store screenshots and metadata clause.

    Row `ad-fire-9` no longer reads "Content gets cut off at the fold."
    It now reads "Part of my list is hidden where the screen folds," a
    fix for a prompt-corpus defect (not a routing question), per
    `task-6-evals/classification.md`.

    The `app-release` skill gained a matching should-fire row: "What
    screenshot sizes does the App Store need for iPhone Duo?" It mirrors
    `apple-design`'s existing should-NOT row of the same text.

    All four Duo should-fire rows held at 3/3 PASS: `ad-fire-7`, `ad-fire-8`,
    `ad-fire-9`, `ad-fire-10`. The baseline held none of them.

    One candidate regression surfaced: `ad-fire-5`, "Add a confirmation
    flow before deleting", scored 1/3 post-edit. A re-run baseline, against
    the pre-Task-10 descriptions in a worktree at `9f3c3a6`, scored 3/3 for
    the same row. This is a confirmed regression by the task's mechanical
    rule. The two failing sessions never called `Skill` at all. They went
    straight to `Bash`/`Read`/`Edit` and implemented the change directly,
    the same `--allowedTools` leak pattern (item 6) that Task 6 recorded
    for this identical prompt. The prompt shares no wording with either
    edited description, so no wording change could plausibly address it.
    No revision round was tried.

    **Per the task's rule, a confirmed regression with no viable revision
    means REVERT. Both description edits are reverted; `SKILL.md` carries no
    diff from before Task 10.** The `triggers.md` changes are kept: the
    `ad-fire-9` reword fixes a corpus defect independent of the description,
    and the new `app-release` row documents the boundary either way.

    **Item 13 is not resolved.** All four Duo rows held in this sweep, but
    the `ad-fire-5` confirmed regression blocks resolution per the task's
    own rule. `nofire-1` (the pre-existing brand-color miss) also remains
    open, unaffected by this task; it failed all 3/3 runs again, unchanged.
    Evidence: `records/2026-09-30-phase9-adaptive-layout/task-10-routing/`
    (`prompts.tsv`, `run-1/`..`run-3/`, `tally.md`, `baseline-ad-fire-5-*/`,
    `task-10-report.md`).

14. **Re-verify every iOS 27.1 claim at GA (found 2026-09-30, Phase 9).**
    `adaptive-layout.md` was compiled against a 27.1 beta SDK — build
    `27A9269`, recorded in `task-7-compile/sdk.log`. A beta API can be
    renamed before it ships. **Trigger: the first Xcode release whose
    iPhoneOS SDK is 27.1 non-beta** — re-run the gate and Task 8's probe.

15. **A camera primer for direction-aware capture (found 2026-09-30, Phase
    9).** Apple's "Choosing a camera by the direction it faces" and the
    iPhone Duo camera-accessory article are cited once in
    `adaptive-layout.md`. No AVFoundation primer exists in
    `apple-frameworks`. **Trigger: the first real app that captures photos
    or video on iPhone Duo.**

16. **App Store Connect upload support for Duo screenshots (found
    2026-09-30, Phase 9).** `app-store-submission.md` states that App Store
    Connect does not yet accept iPhone Duo uploads. **Trigger: Apple's
    screenshot specification page drops that note** — then delete the
    caveat.

17. **iPhone Duo pose control is GUI-only (found 2026-09-30/2026-10-01,
    Phase 9 Task 8).** Task 8's discovery class is B. `simctl` and
    `devicectl` can create, boot, and launch the Duo simulator. Neither
    exposes a pose or rotation command. Device Hub set every pose and
    rotation by hand, so the probe cannot run unattended. It did not cover
    `landscapeLeft`, right-to-left layouts, or the camera occlusion regions.
    **Trigger: the first `simctl` or `devicectl` release that sets iPhone
    Duo poses from the command line.** Re-run the probe unattended, and
    extend it to the uncovered cases. Evidence:
    `records/2026-09-30-phase9-adaptive-layout/task-8-probe/discovery.log`,
    `devicectl-cli.log`, `results.md`.

## Accepted (no action)

Phase 3 minors reviewed and accepted as-is — no follow-up action needed:

- **`testflight-and-versioning.md` is 80 lines, under the ~100 floor.**
  Reviewer confirmed no missing depth (cross-ref discipline) — the file is
  short because it defers appropriately to other reference files, not
  because content is missing.
- **`push-notifications.md:214-220` Push Notification Console + curl/openssl
  debugging exceeds the spec's named examples.** Accurate and useful content,
  accepted as a deliberate scope expansion. File is at 240/250 lines.
