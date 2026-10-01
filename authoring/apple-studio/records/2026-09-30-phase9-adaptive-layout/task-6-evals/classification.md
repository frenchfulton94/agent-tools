# Task 6 baseline failure classification

Baseline sweep: `baseline/results.tsv`, 11/16 PASS. Five rows failed:
`fire-7`, `fire-8`, `fire-9`, `fire-10`, `nofire-1`. Each is classified per
`.claude/rules/eval-harness.md` (`max_turns`, fixture-dependent, or routing
miss) before any description edit is considered, per Step 8's rule: "A
failure is a harness defect until proven otherwise."

## fire-7 — "Make my app work on iPhone Duo"

**Verdict: routing miss (Duo).**

`baseline/fire-7.log`: the session ran three `Bash` calls — listing project
files, `xcrun simctl list devices | grep -i duo`, and a grep of the codebase
for "duo" — found nothing, and answered directly:

> "I don't recognize 'iPhone Duo' as an existing device — it's not in the
> iOS Simulator's device list, and there's nothing about it in this codebase
> ... Apple hasn't shipped a device by that name; Microsoft's 'Surface Duo'
> is the closest match..."

No `Skill` tool call anywhere in the transcript (`stop_reason: end_turn`,
`is_error: false`). This is not fixture-dependent: the question does not
require "iPhone Duo" code to exist in the fixture, only that the session
recognize the topic as adaptive-layout guidance and route to `apple-design`.
It never got that far because nothing in `apple-design`'s `description:`
(SKILL.md line 3, unedited) mentions foldables, poses, or iPhone Duo — the
routing table entry that names it lives in the SKILL.md body
(`SKILL.md:16`, from Task 4), which a session never reads before deciding
whether to invoke the skill. Reproduced identically in a diagnostic rerun
(`diagnostic/fire-7.log`, `(none)` fired again).

## fire-8 — "My toolbar buttons disappear when the phone is closed"

**Verdict: routing miss (Duo).**

`baseline/fire-8.log`: the session found the toolbar code
(`grep -l toolbar`), read `MailboxScreen.swift`, and reasoned:

> "Before I guess at a fix, let me actually reproduce 'closed' behavior in
> the simulator — I'll build and run the app and test rotation/backgrounding/
> split-view-collapse scenarios..."

— then called `Skill` with `apple-studio:xcode-loop`, read
`xcode-loop/references/headless-commands.md`, and ran `xcodebuild -list
-json` before exhausting its turn budget (`error_max_turns`, `num_turns: 7`).
This is a genuine routing decision, not turn exhaustion before any decision:
the session saw the skill list, picked a skill, and picked the wrong one —
it treated "toolbar buttons disappear when closed" as a build-and-reproduce
problem for `xcode-loop` rather than a bars-move-to-the-side layout problem
that `apple-design`'s adaptive-layout guidance covers. The `max_turns` note
in `results.tsv` reflects only that its (wrong) plan ran out of budget before
completing; the defect is the routing choice, made at full turn budget.
Reproduced identically in the diagnostic rerun (`diagnostic/fire-8.log`,
`xcode-loop` fired again).

## fire-9 — "Content gets cut off at the fold"

**Verdict: prompt-wording defect — not a routing miss, not fixture-dependent,
not max_turns.** Excluded from the Step 8 Duo-routing-miss count.

`baseline/fire-9.log`: `num_turns: 1`, `stop_reason: end_turn`, the entire
response is:

> "Hi! What would you like to work on in StudioFixture today?"

No tool call, no engagement with the prompt's content at all. Reproduced
identically in a diagnostic rerun (`diagnostic/fire-9.log`: "I'm ready to
help. What would you like to work on in StudioFixture?").

This looked at first like a prompt-delivery failure (the literal string
"Content gets cut off at the fold" appears nowhere in either raw log —
confirmed with `grep`), matching the class of harness defect this project
has seen before (stdin leaks, `deferred.md` item 6). That reading turned out
to be wrong once tested directly, outside `run_evals.py` and outside the
fixture entirely:

```
cd /tmp/neutral-test-dir && claude --plugin-dir .../apple-studio \
  -p "Content gets cut off at the fold" --output-format stream-json \
  --verbose --max-turns 6 --allowedTools "Skill Read" < /dev/null
```

reproduces the same non-engagement, with no fixture and no hooks specific to
StudioFixture in play. A second short prompt run the same way from the same
neutral directory, "Fix this Sendable warning", is delivered and engaged
with normally ("The working directory is empty — there's no code here...").
So the CLI's `-p` delivery is not broken in general; something about this
specific wording is.

Bisecting the wording (all run the same way, neutral directory) isolates it:

| prompt | result |
|---|---|
| "Content gets cut off" | "What would you like to work on..." (still fails) |
| "cut off at the fold" | "What would you like to work on?" (still fails) |
| "My content is cut off at the fold" | "It looks like your message got cut off — I only see the system context, no actual question..." |
| "Something gets cut off at the fold" | "It looks like your message got cut off — I only see 'Something gets cut off at the fold' with no actual question or task attached." |
| "Content gets cut off at the crease" | "What would you like to work on..." (still fails, same as first row) |

The prompt *is* delivered (the fourth row echoes it back verbatim). The
model reads "[X] gets cut off" as a first-person claim that its own incoming
message was truncated, rather than as a description of a UI bug in the
fixture app, and asks for the "real" message instead of treating the
sentence as the task. Swapping "fold" for "crease" does not fix it — the
self-referential misreading is driven by "cut off", not by the word "fold".

This never reaches a point where the session "saw the skill list and chose
another route" (`eval-harness.md`'s definition of a routing miss) — it never
engages with the task as a task. It is a defect in the eval corpus's prompt
wording (added verbatim from the task brief, Step 5), not evidence about
`apple-design`'s description or routing. Per the brief's Step 8 rule, only a
routing miss on `fire-7`..`fire-10` counts toward the description-edit
decision; `fire-9` does not qualify either way, and is recorded here rather
than silently dropped.

## fire-10 — "Should I use an arrangement view here?"

**Verdict: routing miss (Duo).**

`baseline/fire-10.log`: the session found and read `MailboxScreen.swift` and
`ContentView.swift`, then asked:

> "Quick check before I answer: what do you mean by 'arrangement view' here
> — a DAW-style tracks/timeline arrangement (Logic/Ableton-style), or
> something else? The mailbox fixture you just added uses
> `NavigationSplitView` (list/detail), and 'arrangement view' isn't a term
> from SwiftUI or the HIG, so I want to make sure I point you at the right
> pattern..."

`num_turns: 4`, `stop_reason: end_turn`, no `Skill` call. But "arrangement
view" *is* a real, current SwiftUI/HIG term: `ArrangementView` is documented
in this same skill's own `references/adaptive-layout.md:81-102` (added Task
4) as the type Apple ships for laying out primary/secondary content across
iPhone Duo poses, cited to "Preparing your app for iPhone Duo" and
"Designing for iPhone Duo" in Apple's HIG. The session's claim that it
"isn't a term from SwiftUI or the HIG" is wrong precisely because it never
read that reference — routing never fired, so the knowledge the skill holds
was never consulted. This is a routing miss, not a legitimate ambiguity: the
skill's own reference disproves the "not a real term" premise the session
answered from.

## nofire-1 — "Design our brand color palette"

**Verdict: routing miss — reproduces a pre-existing, non-Duo bug (deferred
item 13's second finding). Does not bear on the Step 8 Duo decision.**

`baseline/nofire-1.log`: the session read the fixture's files, then called
`Skill` with `apple-studio:apple-design` and the explicit args "color and
brand palette guidance for a SwiftUI app — defining an accent color and
semantic brand colors...", read `hig-foundations.md`'s color section, and
ran out of turns before answering (`error_max_turns`, `num_turns: 7`). This
is `apple-design` firing on exactly the request its own description
disclaims — "Not for brand identity or custom visual styling" — matching
the Phase 8 finding recorded in `deferred.md` item 13 verbatim ("One
should-not-fire row — 'Design our brand color palette' — wrongly reached
`apple-design`"). Unchanged since Phase 8; not introduced by anything in
this task, and not addressed by the Step 8 description edit (which adds
Duo/adaptive-layout terms and does not touch the brand-identity disclaimer
already present in the description).

## Summary against Step 8's decision rule

Of the four Duo should-fire rows (`fire-7`..`fire-10`), three
(`fire-7`, `fire-8`, `fire-10`) are genuine routing misses; `fire-9` is
excluded as a prompt-wording defect. **One or more Duo should-fire row is a
routing miss, so the description edit specified in Step 8 is made.**

`nofire-1` remains a separate, pre-existing, non-Duo routing miss that the
edit does not fix. It keeps deferred item 13 open regardless of the Duo
outcome (see item 13's update in `docs/deferred.md`).

## Step 9 — post-edit sweep and the regression that reverted the edit

`after-edit/results.tsv`: also 11/16 PASS, but not the same 11. `fire-7` and
`fire-8` flipped baseline-FAIL to PASS — the edit fixed the two clearest Duo
routing misses (`fire-7` fired `apple-design` at `max_turns`; `fire-8` fired
`apple-design` at `max_turns`, no longer `xcode-loop`). `fire-9`, `fire-10`,
and `nofire-1` are unchanged FAILs, consistent with their classifications
above (`fire-9` a prompt-wording defect the description cannot fix;
`fire-10`'s "arrangement view" miss was not resolved by adding "iPhone
Duo" and "pose"/"fold" wording alone — the term itself never appears in the
edited description; `nofire-1` is the unrelated brand-color bug).

Two rows that **passed in the baseline flipped to FAIL** — regressions by
the brief's Step 9 rule ("A row that passed in the baseline and fails after
the edit is a regression: revert the edit and record why"):

- **`nofire-6`** — "What screenshot sizes does the App Store need for
  iPhone Duo?" `after-edit/nofire-6.log`: the session called `Skill
  apple-studio:apple-design` **first**, with args "iPhone Duo foldable pose
  — what is it, and does it have App Store Connect screenshot size
  requirements?", searched the skill's own references for "duo", found
  nothing skill-side, self-corrected ("This looks like it maps to the
  `app-release` skill"), and called `apple-design`'s app-release next to
  get the (correct, detailed) answer. `verdict_for` scores on the *first*
  skill invoked, so this is a FAIL: the edited description's own words
  "foldables such as iPhone Duo" is what pulled `apple-design` in first on
  a pure App Store screenshot-sizing question, exactly the over-triggering
  the description's existing "Not for brand identity or custom visual
  styling" disclaimer exists to prevent, now extended to a second boundary
  (release logistics) that the edit's added wording created. This is a
  directly traceable, edit-caused regression, not noise.
- **`fire-5`** — "Add a confirmation flow before deleting." `baseline/fire-5.log`
  called `Skill apple-studio:apple-design` and passed (`max_turns`, wrote to
  the fixture). `after-edit/fire-5.log` never called any `Skill` at all —
  it went straight to `Bash`/`Read`/`Edit` and implemented the confirmation
  dialog directly in `MailboxScreen.swift`. This prompt shares no wording
  with anything the edit changed (no size, pose, fold, or Duo content), so
  the mechanism is not directly traceable the way `nofire-6`'s is; the more
  likely explanation is session-to-session routing variance under
  `--allowedTools` leaking `Bash`/`Edit`/`Write` regardless of the
  description (`deferred.md` item 6), not the edit itself. It is recorded
  as a regression per the brief's mechanical rule regardless of suspected
  cause, since the rule does not carve out an exception for a plausibly
  unrelated flip and a single sample cannot rule out the edit's involvement.

**Action: the SKILL.md description edit is reverted** (back to the original
text, unchanged from before Step 8) because at least one baseline-passing
row (`nofire-6`, directly traceable) and a second (`fire-5`, unexplained)
both flipped to FAIL after the edit, meeting the brief's revert condition.
The fix for `fire-7`/`fire-8` does not ship this phase. `fire-7`/`fire-8`'s
Duo routing misses, `fire-10`'s "arrangement view" miss, and `nofire-1`'s
brand-color miss all remain open, recorded in `docs/deferred.md` item 13
rather than papered over by a change whose net effect (per Step 9's own
measurement) traded two Duo fixes for two new regressions on rows that were
previously clean.
