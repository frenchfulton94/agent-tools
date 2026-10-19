# Phase 10 Task 12: trigger-eval classification

Sweep: `python3 authoring/apple-studio/pipeline/run_evals.py task-12-evals/prompts.tsv task-12-evals/baseline`,
at the driver defaults (`--max-turns 6`, `--timeout 300`, `--allowedTools "Skill Read"`),
with cwd `~/Projects/StudioFixture`, run on 2026-10-18 with Claude Code 2.1.292. Fixture
decision (Deliverable 6): every new-skill row uses how-to phrasing, and StudioFixture
is not seeded.

Result: **58/60 PASS**, driver exit 1 (`baseline/results.tsv`, `baseline.console.log`).
Session logs are gitignored. The baseline logs are in `raw/task-12-evals-session-logs.tar.xz`.
The `rerun-conc-fire/` and `diagnostic/` logs are in `raw/task-12-evals-rerun-session-logs.tar.xz`.
A citation such as `baseline/conc-fire.log:24` resolves after
`tar -xJf raw/<archive> -C task-12-evals`.

## Rows in the sweep

- `apple-metal` and `apple-games`: every row of each `evals/triggers.md` (8 FIRE and 6 NOFIRE each).
- `app-release`: its full `triggers.md` (8 FIRE and 4 NOFIRE), because Task 10 changed its description.
- The other ten prior skills: one FIRE row and one NOFIRE row each, copied verbatim.

`git diff origin/main -- 'plugins/apple-studio/skills/*/SKILL.md'` shows that no other
prior skill's `description:` line changed on this branch. `apple-performance`'s body changed
in Task 9, and its description did not. It therefore gets the standard two rows.

## Pass bar

| Bar | Result |
|---|---|
| Every new-skill row passes | **Met.** apple-metal 14/14, apple-games 14/14 |
| No prior-skill row regresses from its last recorded verdict | **Not met: `conc-fire`** regressed from PASS to FAIL. It failed again on a restored fixture and is classified as a prompt defect, below. Every other prior row matches or betters its last verdict |
| Known-open rows are reported and do not gate | `test-fire` failed, as it last did. `conc-fire` is known-open by controller ruling P43 (deferred item 23). `ad-nofire-1` (deferred item 13) was not sampled |

Per-skill counts: apple-metal 14/14, apple-games 14/14, app-release 12/12,
apple-animations 2/2, apple-design 2/2, apple-frameworks 2/2, apple-intelligence 2/2,
apple-macos 2/2, apple-performance 2/2, swift-architecture 2/2, swift-concurrency 1/2,
swift-testing 1/2, xcode-loop 2/2. Prior skills combined: 30/32.

No description was edited, so `after-edit/` does not exist. The pass bar allows an edit
only for a routing miss on a new-skill row, and there was none.

## Boundary results for the new skills

Every NOFIRE row routed to the neighbour its `triggers.md` names, or to no skill:

- `metal-not-1` → apple-animations. `metal-not-2` → apple-performance. `metal-not-6` → apple-games.
- `games-not-1` → apple-metal. `games-not-2` → apple-performance. `games-not-5` → apple-design. `games-not-6` → app-release.
- `metal-not-3`, `metal-not-4`, `metal-not-5`, `games-not-3`, and `games-not-4` (SpriteKit, Godot, BRDF theory) were each answered in one turn with no `Skill` call.

The two new skills split their shared boundary cleanly in both directions. `metal-not-6`
(controller thumbsticks) went to apple-games, and `games-not-1` (render-pass GPU time) went
to apple-metal.

The new skills did not pull in neighbouring prior rows. `anim-fire` ("ripple distortion …
shader effect?") loaded only apple-animations, `perf-fire` loaded only apple-performance,
and `games-not-6` (notarization) reached app-release under its new Task 10 description.

## Failures

### `conc-fire` — prompt defect (missing referent). A regression from its last verdict; known-open by ruling P43

The baseline failure had a contaminated fixture, as described next. A re-run on a restored
fixture failed again, and a how-to control fired. Both are described after the baseline
evidence.

**Baseline run (contaminated fixture)**

- Row: `swift-concurrency FIRE "Should this be an actor or a @MainActor class?"`. Fired: (none).
  The session ended `success` at 3 turns, `end_turn` (`baseline/conc-fire.log:25`), so turn
  exhaustion is ruled out.
- Last recorded verdict: **PASS** (Phase 7 Task 4, `conc-fire`, archived `apple-studio`
  repository, `.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/task-4-evals/results.tsv`).
- Session evidence: the session's first action was
  `git log --oneline main..HEAD; git diff main --stat` (`baseline/conc-fire.log:10`). Its
  answer opens "I couldn't find what "this" refers to. The `push-notifications` branch has no
  commits beyond `main` …" and then guesses that "this" is "the push-notification manager
  the branch is for" (`baseline/conc-fire.log:24`).
- Cause: row `ar-fire-5` ("Set up push notifications - APNs keys, entitlements, the works")
  ran `git switch -c push-notifications` in the fixture before it wrote its entitlements
  (`baseline/ar-fire-5.log:51`, `:54`). The driver's per-prompt guard restored the three files
  that row wrote. But the guard compares `git status --porcelain` only, and a branch switch
  leaves that output empty. The fixture's HEAD therefore stayed on `push-notifications`
  (`.git/HEAD` reads `ref: refs/heads/push-notifications`; both branches point at `5287d2c`).
  Rows 34-60 ran on that branch, so each of those sessions started with
  "Current branch: push-notifications" in its git context. A deictic prompt ("this") with no
  referent in the fixture took the branch name as its referent, hunted for it, and answered
  blind. This is the missing-referent mechanism that Phase 7 recorded, with the branch name
  as bait.
**Re-run on the restored fixture (`rerun-conc-fire/`)**

- The controller's session switched StudioFixture back to `main` and deleted
  `push-notifications`. The worktree guard refuses that `git -C` from this session.
  `git status --porcelain --branch` then printed only `## main`. Before the re-run and after
  it, `~/Projects/StudioFixture/.git/HEAD` read `ref: refs/heads/main`.
- `run_evals.py … --only conc-fire` → **FAIL**, fired (none), `success` at 4 turns,
  `end_turn` (`rerun-conc-fire/conc-fire.log:23`, `rerun-conc-fire.console.log`).
- Session evidence: the session grepped the fixture for `class`, `actor`, and `@MainActor`
  (`rerun-conc-fire/conc-fire.log:10`). It read every Swift file (`:13`) and checked the
  project's concurrency build settings (`:19`). It then answered "I couldn't find a class to
  judge. The working tree is clean, and the repo has no `class` or `actor` anywhere …", and
  went on to recommend a `@MainActor @Observable final class` from priors (`:22`). It never
  called `Skill`, though turns remained.
- Conclusion: the branch name only supplied bait. The failure does not depend on it.

**Diagnostic control (`diagnostic/`, not scored)**

- Prompt: "How do I decide whether to use an actor or a @MainActor class?". This is the same
  question with the deictic "this" removed, put in the Phase 10 how-to form. It adds no
  swift-concurrency vocabulary that the original lacks.
- Result: **PASS**. The session called `Skill` `swift-concurrency` as its first action
  (`diagnostic/diag-conc.log:10`), read `references/strict-concurrency.md` (`:14-16`), and
  answered from it (`:24`). It ended `success` at 5 turns (`:25`).

**Classification: prompt defect (missing referent), not a routing miss.**

- Mainly the referent changed between the two prompts (see the framing caveat below), and
  the verdict changed with it.
- This is the mechanism Phase 7 recorded for `anim-fire-8` and `test-fire`: "a missing
  referent shifts the session into answering blind from priors rather than into loading the
  skill".
- No Phase 10 change touches swift-concurrency's description.
- The fixture is not what it was in Phase 7. Phase 9 added `MailboxScreen.swift`, which gives
  a session more code to search before it gives up. The model and Claude Code version are
  also newer. Either may explain why the row passed in Phase 7 and fails now. This sweep does
  not separate the two.
- The control differs from the original in framing ("How do I decide whether to use …") as
  well as in the referent, so it is not a strict single-variable test. It is still the same
  kind of control as Phase 7's `diag-xcode`.

**Gate status:** the row regressed from its last recorded verdict, so the no-regression bar
is **not met** for this row. It was left unfixed on purpose:

- A description edit is out of scope here, and the control shows the description routes
  correctly.
- A reword belongs in `swift-concurrency/evals/triggers.md`, which this task does not edit.
  The obvious reword is the diagnostic prompt.

**Controller ruling P43:** the row is recorded as a known-open prompt defect and does not
gate. Phase 10 touched nothing in swift-concurrency, and the how-to control routes. The
reword is deferred item 23. Each probe ran once, so this rests on one failing run and one
passing control.

### `test-fire` — known-open (prompt defect). Does not gate

- Row: `swift-testing FIRE "Write tests for this view model"`. Fired: (none). The session
  ended `success` at 5 turns, `end_turn` (`baseline/test-fire.log:22`).
- Last recorded verdict: **FAIL**, twice: Phase 7 Task 4 `test-fire` at `--max-turns 6`, and
  `task-4-evals-rerun/` at 12. Phase 7 classified it as a corpus/fixture mismatch. No
  should-fire row in today's `swift-testing/evals/triggers.md` has a passing recorded verdict:
  Phase 6's passing `test-fire` used other wording, and Phase 7's passing `diag-test` probe is
  not in `triggers.md`. The row was therefore taken as known-open, per the brief.
- Session evidence: the session searched for a view model (`baseline/test-fire.log:8-16`) and
  answered "I couldn't find a view model to test. Nothing in the repo uses `ViewModel`,
  `@Observable`, or `ObservableObject` …" (`:21`). The fixture has no view model, so this is
  the Phase 7 failure unchanged. That session also ran on the `push-notifications` branch,
  but the branch played no part in its answer.

## Fixture writes (the `--allowedTools` leak)

Four rows wrote to StudioFixture despite `--allowedTools "Skill Read"`. The driver attributed
each write and restored the files after each row:

| Row | Verdict | Paths |
|---|---|---|
| `ar-fire-5` | PASS | `project.pbxproj`, `StudioFixture.entitlements`, `StudioFixture-macOS.entitlements`. **Also created and switched to branch `push-notifications`, which the guard did not detect or undo** |
| `ar-fire-6` | PASS | `xcshareddata/`, `ci_scripts/` |
| `anim-fire` | PASS | `MailboxScreen.swift`, `Ripple.metal`, `RippleEffect.swift` |
| `macos-fire` | PASS | `MailboxScreen.swift`, `StudioFixtureApp.swift`, `SettingsView.swift` |

The driver's closing `git status --porcelain` check found nothing (`baseline.console.log`
has no "fixture still dirty at close" line). No other session ran a git command that changes
state: a scan of all 60 logs for `switch|checkout|branch|commit|stash|reset|tag|init|restore|clean`
found only read-only listings besides `ar-fire-5`. Each session's `Skill` call happened before
any write, so the writes did not change a verdict.

**Driver gap:** `run_evals.py` restores files but not the branch. This is recorded as
`docs/deferred.md` item 22, with a trigger. The guard should also record HEAD and the branch
list before the sweep, compare them after each prompt, and restore them. Left unfixed here,
because Task 12 does not modify the pipeline.

## Prior-skill row provenance

The last recorded verdict for each regression row. "P7" is Phase 7 Task 4 and "P8" is Phase 8
Task 3; both are in the archived `apple-studio` repository under `.superpowers/sdd/`. "P9" is
`records/2026-09-30-phase9-adaptive-layout/task-10-routing/run-rev-*`.

| Row | Prompt (verbatim from `triggers.md`) | Last recorded | Today |
|---|---|---|---|
| `ar-*` (12 rows) | full `app-release/evals/triggers.md` | P9 `run-1..3` and `run-rev-*`: all PASS | 12/12 PASS |
| `anim-fire` | Add a ripple distortion to this view when tapped - shader effect? | P7 and P8: PASS | PASS |
| `anim-not` | Why does my ScrollView stutter when I scroll fast? | P7 and P8: PASS | PASS (→ apple-performance) |
| `design-fire` | Does this screen feel native? | P9: 3/3 PASS | PASS |
| `design-not` | Fix this Sendable warning | P9: 3/3 PASS | PASS |
| `fw-fire` | Should I use WeatherKit or a third-party weather API? | P7: PASS | PASS |
| `fw-not` | Where should my models live? | P7: PASS | PASS (→ swift-architecture) |
| `ai-fire` | Summarize a note with the on-device model and stream the result into the view | Phase 6 `ai-fire-1`: PASS | PASS |
| `ai-not` | Should this feature use on-device AI or just a rule? | Phase 6 `ai-not-1`, a paraphrase ("… or would a deterministic rule do?"): PASS. See note | PASS |
| `macos-fire` | Add a Settings window with Cmd-comma to my Mac app | P7: PASS | PASS |
| `macos-not` | Does this Mac window layout feel native? | P7: PASS | PASS (→ apple-design) |
| `perf-fire` | Scrolling this list stutters on a real device but feels fine in the Simulator | P7, Phase 6, and the debt-items sweep: PASS | PASS |
| `perf-not` | Make this card flip with a spring animation | P7: PASS | PASS |
| `arch-fire` | Where should this view's state live? | P7: PASS | PASS |
| `arch-not` | Does Apple have a framework for weather? | P7: PASS | PASS (→ apple-frameworks) |
| `conc-fire` | Should this be an actor or a @MainActor class? | P7: PASS | **FAIL**, twice: baseline (contaminated) and re-run on clean `main`. Prompt defect, above |
| `conc-not` | What does the HIG say about loading spinners? | P7: PASS | PASS (→ apple-design) |
| `test-fire` | Write tests for this view model | P7: FAIL ×2. **Known-open** | FAIL |
| `test-not` | Fix this data race | P7: PASS | PASS |
| `xcode-fire` | Run the test suite for this project and show me the failures | P7 diagnostic `diag-xcode`: PASS | PASS |
| `xcode-not` | Write a test for the parser | P7: PASS | PASS |

Note on `ai-not`: the only apple-intelligence NOFIRE row with a verbatim recorded verdict is
"Why is my Foundation Models feature so slow?". It is deferred item 9's open bleed (P7 FAIL
×2), so it was not used. The row chosen has a passing verdict for a paraphrase only. Deferred
item 9's three-prompt sampling trigger was not run here, because this task's row selection
is one FIRE and one NOFIRE row per prior skill.

`ad-nofire-1` ("Design our brand color palette", deferred item 13) was not among the rows
chosen, so the item-13 known-open rows are unaffected by this sweep.
