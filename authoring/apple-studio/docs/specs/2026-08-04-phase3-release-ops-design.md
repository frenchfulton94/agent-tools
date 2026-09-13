# apple-studio Phase 3: Release & ops — design

Phase spec under the standing charter
(`docs/specs/2026-08-03-apple-studio-design.md`, "Phase 3 — Release & ops").
Decisions taken 2026-08-04 in brainstorming; this doc is the input to the
Phase 3 implementation plan.

## Goal

Ship the release-engineering slice: one new skill, `app-release`, covering
signing, TestFlight, App Store submission, rejection avoidance, versioning,
push-notification ops, and CI guidance — built to charter quality with no
imminent release driving it ("completing the toolkit"). Version bump to 0.4.0.

## Deliverables

**New skill `plugin/skills/app-release/`** — lean SKILL.md (triggers, routing,
release-process judgment) + `evals/triggers.md` + five references:

1. `signing-and-provisioning.md` — certificates vs App Store Connect API keys,
   automatic vs manual signing judgment, provisioning profiles, entitlements,
   classic signing failures (local and CI keychain).
2. `app-store-submission.md` — submission flow, top rejection causes and
   review-guideline judgment, privacy manifests and nutrition labels, export
   compliance, metadata.
3. `testflight-and-versioning.md` — internal/external beta flow,
   CFBundleVersion vs CFBundleShortVersionString discipline, phased release,
   release-strategy judgment.
4. `push-notifications.md` — APNs ops only: auth keys vs certificates,
   dev/prod environments, capabilities and entitlements, token lifecycle,
   silent-push budget, notification extensions (incl. their signing),
   delivery debugging (`simctl push`, Console). API usage defers to the
   live-docs `apple-frameworks` usernotifications primer via cross-ref —
   no duplication.
5. `ci-release-automation.md` — Xcode Cloud first (workflows, build/test,
   TestFlight distribution) as the first-party default voice; generic
   self-managed path second (xcodebuild archive/export, a GitHub Actions
   sketch, App Store Connect API keys for automation); fastlane named as an
   alternative only, not documented in depth.

**Primer cross-ref:** one line added to
`plugin/skills/apple-frameworks/references/primers/usernotifications.md`
pointing at `app-release/references/push-notifications.md` for APNs ops.

**Conditional agent — release-preflight:** built in this phase only if the
kill-switch gate passes (see below). Otherwise recorded in `docs/deferred.md`
with trigger "first real release".

## Sources and pipeline

Same pipeline as Phases 1–2: `pipeline/convert.sh` on
`iOS_App_Distribution_and_Best_Practises_v1.0.0.epub` and
`Push_Notifications_by_Tutorials_v4.0.0.epub` (both present in
`~/Documents/Apple Books/`) → gitignored `corpus/`; two maps under
`pipeline/maps/`: `app-release-books.md` (chapter → target reference) and
`app-release-live.md` (live-doc endpoints → target reference).

**Staleness stance:** both books are old — the distribution book (v1.0.0,
~2021) predates Xcode Cloud and privacy manifests; the push book (v4.0.0) also
predates current APNs consoles and privacy manifests. They contribute **durable judgment only** (mental models, rejection
patterns, versioning discipline, APNs architecture). Everything process- or
API-specific is distilled from live docs: developer.apple.com distribution /
Xcode Cloud / TestFlight DocC endpoints and the App Review Guidelines page,
cited per the live-docs-first rule.

**Endpoint probing (Phase 2 lesson, binding):** every live endpoint assumed by
the maps is probed (actually fetched) during planning before any distillation
task is written against it. Expected-but-missing pages are recorded in the map
with `MISSING:`.

## Opening task: Phase 2 debt + kill-switch gate

Task 0 of the plan:

1. Clear the five items in `docs/phase-2-debt.md` (generic-clause wording fix,
   SKILL.md routing line trim, kill-switch trim candidates — stray
   watchOS/tvOS/visionOS bullets in hig-foundations.md and accessibility.md,
   duplicated-consistent facts → cross-refs, uncited path-controls URL call).
2. Run the deferred kill-switch load-frequency check (`docs/deferred.md`
   item 1): measure from session transcripts/history how often
   `swift-reviewer` and `design-reviewer` have actually been invoked and their
   references read since Phase 1.

**Agent gate:** if the measurement shows real exercise — any genuine
invocations with reference reads outside the plugin's own verification runs —
the release-preflight agent (pre-submission audit: entitlements, Info.plist,
privacy manifest, versioning, rejection-risk scan) ships in this phase.
If not, no new agent this phase; the decision and evidence go to
`docs/deferred.md`.

## Coverage vs verification

The references document the **complete paid-membership release path** — App
Store Connect setup, certificates and profiles under a paid team, TestFlight
internal/external distribution, submission and review, production APNs, Xcode
Cloud — at full depth. The free tier limits only what this phase's
verification can *exercise*, never what the references *cover*.

## Verification (free-tier, definition of done)

No paid Apple Developer Program membership is used for verification.
Boundaries are explicit:

- Trigger evals for `app-release`: fires on release/signing/TestFlight/
  push-setup/CI requests, silent otherwise.
- Consume tests with captured logs; every consume-test prompt validated
  against actual reference coverage before it enters the plan (Phase 2
  lesson). Evidence pointers as `<file>:<line-range>`.
- Real exercise where free: `xcodebuild archive` of StudioFixture plus a
  development-method export (personal team signing); `simctl push` payload
  test against StudioFixture in the simulator.
- Store-side claims (TestFlight upload, submission, review) remain
  live-doc-cited but unexercised — an explicit, recorded verification
  boundary, closed at first real release.
- `claude plugin validate . --strict` passes at every commit touching
  `plugin/`; version bump to 0.4.0 in the final task only; re-import into
  Xcode after merge (operational rule from `docs/deferred.md` item 3).

**Process adoptions (from `docs/phase-2-debt.md`, binding on the plan):**
implementer briefs carry the synchronous-foreground/no-backgrounding rule and
`--permission-mode auto` verbatim in template text; from-scratch consume-test
prompts get a fixture cwd and adequate turn budget or a coexistence caveat.

## Out of scope

- StoreKit/monetization depth (storekit2 primer exists; live docs cover the rest).
- Server-side push provider implementation (any language) beyond judgment
  about what the server must do.
- fastlane beyond naming it as an alternative.
- Performing an actual App Store submission or TestFlight upload as part of
  this phase's verification (needs paid membership). The *guidance* for both
  is fully in scope — see "Coverage vs verification".
- Marketing assets, screenshot design, App Store page optimization (branding
  scope boundary).
- watchOS/tvOS/visionOS distribution.

## Phase 3 verification results (2026-08-04)

Evidence artifacts live in `.superpowers/sdd/2026-08-04-phase3-release-ops/`
(SDD workspace, not committed to `plugin/`). Branch `phase-3`, commits
`b05ead7..f5a5b91` plus the release commit.

1. **Phase 2 debt cleared** — all five items resolved and
   `docs/phase-2-debt.md` deleted in commit `b05ead7` (Task 0). One judgment
   call recorded: `accessibility.md:87` kept its load-bearing 44×44pt rule and
   shed only the non-shipped-platform fragments (task-0-report.md, "Concerns").
2. **Kill-switch measurement + agent gate: FAIL** — 230 candidate transcript
   files classified; 7 genuine agent invocations found, all against the
   plugin's own verification fixtures; **0 genuine invocations of either
   reviewer agent outside plugin verification runs**
   (`docs/deferred.md:8-41`). Per the gate, no release-preflight agent this
   phase; deferred entry with trigger "first real release" at
   `docs/deferred.md:39-41`.
3. **Five references shipped with sources** — `signing-and-provisioning.md`
   (115 lines), `app-store-submission.md` (110), `testflight-and-versioning.md`
   (80), `push-notifications.md` (238), `ci-release-automation.md` (210), each
   opening with a `> verified: 2026-08 against <live URLs>` + `> sources:`
   header (line 1–2 of each file); commits `66fe4fd`, `a2438f9`, `f8eccba` with
   review-fix commits `5a9d86a`, `cc341ad`, `0e3708d`. Caveat, verbatim from
   the ledger: `testflight-and-versioning.md` is 80 lines, under the ~100
   floor — reviewer confirmed no missing depth (cross-ref discipline), flagged
   for the record.
4. **SKILL.md + evals + consume-test** — `SKILL.md` (29 lines) +
   `evals/triggers.md` (7 should-fire / 4 should-NOT) in commit `f5a5b91`;
   consume-test passed with captured log (`task-5-consume-test.log`, exit 0,
   `permission_denials: []`). Caveat, verbatim: first attempt hit a permission
   denial on the reference Read (plain `-p` does not auto-grant Read outside
   the invoking cwd); fixed by adding `--allowedTools "Read"` and re-ran
   successfully with full evidence. Second caveat: the attempt-1 log was
   overwritten; its failure narrative rests on transcription, not artifact.
5. **Primer cross-ref** — `usernotifications.md:84-85` points at
   `app-release/references/push-notifications.md` for APNs ops (commit
   `f8eccba`, trimmed to cross-ref form in `0e3708d`).
6. **Conditional agent** — not built, per the gate verdict in item 2; the
   deferred entry is the deliverable (Task 6 formally SKIPPED under the plan's
   skip rule).
7. **Free-tier exercise** — `task-7-archive.log`, `task-7-export.log`,
   `task-7-push.log`, `task-7-push-banner.png`:
   - Simulator-destination archive of StudioFixture: `** ARCHIVE SUCCEEDED **`
     ("Sign to Run Locally").
   - Device-destination archive: failed as the free-tier boundary — with
     `-allowProvisioningUpdates`: "Your team has no devices from which to
     generate a provisioning profile."
   - Export boundary, captured verbatim: `-exportArchive` fails with
     `Found no compatible export methods` for **both** `debugging` and
     `app-store-connect` methods — the boundary sits one step earlier than
     anticipated (no device-signed archive is producible at all on a
     zero-device personal team), a stricter boundary than the expected
     method-specific block.
   - `simctl push`: authorization granted, delivery confirmed by the
     delegate's OSLog receipt line and banner screenshot; documented payload
     shape, `booted` alias, and log predicate all worked as written.
   - All documented commands in `ci-release-automation.md` and
     `push-notifications.md` survived contact; zero reference corrections
     needed.
8. **Trigger-eval table** — 23 prompts (app-release: 7 fire + 4 no-fire;
   1 fire + 1 no-fire regression sample per prior skill), method
   `claude --plugin-dir ./plugin -p "<prompt>" --max-turns 2
   --output-format stream-json --verbose --allowedTools "Skill Read"`, one log
   per prompt (`task-8-eval-*.log`): **23/23 pass** — app-release 11/11
   (all 7 should-fire invoked `apple-studio:app-release`; all 4 should-NOT
   stayed silent or routed to the annotated sibling skill), prior skills
   12/12 with one documented substitution. Caveat: the original apple-design
   should-fire prompt ("Build the settings screen UI") is unevaluable in a
   headless harness with the user-level superpowers plugin installed — its
   process-skill priority routes every "build X" prompt to
   `superpowers:brainstorming` first, which ends a headless session asking
   clarifying questions before any implementation skill can fire (verified
   at max-turns 6 and from a fixture cwd; no wrong apple-studio skill fired).
   Substituted "Does this screen feel native?" from the same should-fire set:
   `apple-studio:apple-design` fired
   (`task-8-eval-apple-design-fire-2-substitute.log`). Not a routing
   regression; recorded as an eval-harness interaction.
9. **`claude plugin validate . --strict`** — "Validation passed", zero
   warnings (`task-8-validate.log`).
