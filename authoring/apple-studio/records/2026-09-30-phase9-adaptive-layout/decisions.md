# Phase 9 design decisions — 2026-09-30

Taken with the user during brainstorming, before the spec
(`docs/specs/2026-09-30-phase9-adaptive-layout-design.md`) was written. Each
entry records the options weighed and why the chosen one won.

## 1. The 27.1 compile gate

The Duo layout APIs are iOS 27.1 beta; the installed SDK is 27.0
(`survey/sdk-survey.log`).

- A. Install the Xcode 27.1 beta and compile everything. **Chosen.**
- B. Ship design guidance and 27.0 APIs; name 27.1 APIs without snippets.
- C. Ship 27.1 snippets marked "documented, not compiled".

C spends the gate on the least trustworthy case: Phase 6 found documented
symbols absent from the shipped SDK. B was the fallback if the user would not
install. A keeps the gate as written.

## 2. Where the knowledge lives

- 1. A device-named `iphone-duo.md` reference.
- 2. Spread across `hig-patterns.md`, `platform-idioms.md`, and
  `swiftui-design-implementation.md`.
- 3. A new `apple-duo` skill.
- 4. A concept-named `adaptive-layout.md`. **Chosen.**

The user asked which option was best long term. The APIs are documented for
iOS, iPadOS, macOS, tvOS, visionOS, and watchOS 27.1, and the HIG compares
reserved regions to iPad window controls. Duo is the first device to need them
all, not their only user. A device-named file ages on the next device; a new
skill overlaps `apple-design`'s triggers; spreading scatters the beta surface
that must be re-verified at GA. `platform-idioms.md` already declares
"organized by decision, not per-platform encyclopedia". Option 4 follows that
precedent and gives the topic one home. Cost: a seventh reference, so the
file-count convention is amended to a rule rather than a larger number.

## 3. Runtime verification depth

- A. Compile only.
- B. Compile, then check every behavioral claim on the Duo simulator.
- C. Compile, then check the three or four claims that code depends on.
  **Chosen.**

Phase 7 found the running framework contradicting a careful interface reading
12 of 12 times, so A was rejected. B scales with every pose-by-context
combination. C targets the claims where a wrong rule produces broken code
rather than a weaker design.

## 4. Eval fixture and the description edit

Deferred item 13 fires: this phase edits `apple-design`, and StudioFixture has
no real UI.

- A. Seed the fixture with a real screen, baseline, then edit the description
  only if the baseline shows a gap. **Chosen.**
- B. Edit the description and report a pass rate marked untrustworthy.
- C. Skip the description edit and rely on the routing line.

B and C each avoid the trigger rather than meet it. A is the only option under
which this phase's eval result means something.

## Folded in without a separate decision

- Deferred item 7: triage the two `accessibility.md` failures so
  `apple-design` compiles clean. The other 17 stay out of scope.
- Deferred item 12: rewrite the StudioFixture citation when
  `headless-commands.md` is edited.
- Charter: amend the stale "ML moves to Phase 8" line.
