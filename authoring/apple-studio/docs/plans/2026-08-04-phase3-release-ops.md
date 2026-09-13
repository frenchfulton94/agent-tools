# apple-studio Phase 3: Release & Ops Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear the Phase 2 debt, run the deferred kill-switch measurement, then ship the release-engineering slice: an `app-release` skill (five references distilled from live Apple docs + two judgment-only books) covering signing, TestFlight, App Store submission, rejection avoidance, versioning, push-notification ops, and Xcode Cloud-first CI — plus, only if the kill-switch gate passes, a `release-preflight` agent.

**Architecture:** Same two-layer pattern as Phases 1–2: knowledge references distilled per the pipeline, consumed by a lean SKILL.md (and conditionally the preflight agent). Primary truth is live docs (the books are old — durable judgment only). Verification is free-tier: archive + development export of StudioFixture, `simctl push`, trigger evals, consume tests. Spec: `docs/specs/2026-08-04-phase3-release-ops-design.md`.

**Tech Stack:** Claude Code plugin components, existing `pipeline/` (convert.sh, distill-prompt.md), pandoc, DocC JSON endpoints (probed 2026-08-04, all returning 200 — see Task 1), `xcodebuild archive`/`-exportArchive`, `xcrun simctl push`.

## Global Constraints

- Repo: `~/Projects/apple-studio`, branch `phase-3` (create from `main` at start). All paths relative to repo root unless absolute.
- Toolchain: Xcode 27.0 beta active; fixture app `~/Projects/StudioFixture` (Multiplatform, scheme `StudioFixture`; leave its git tree clean after any test).
- Spec boundary (verbatim): "The references document the **complete paid-membership release path** … at full depth. The free tier limits only what this phase's verification can *exercise*, never what the references *cover*." No paid Apple Developer Program membership is used for verification.
- Live-docs-first: the distribution book (v1.0.0, ~2021) predates Xcode Cloud and privacy manifests; the push book (v4.0.0) predates current APNs consoles. Books contribute durable judgment ONLY; every process- or API-specific claim is distilled from live docs and cited (canonical human URL in headers; fetch via the DocC JSON endpoints `https://developer.apple.com/tutorials/data/documentation/<path>.json`). The App Review Guidelines page (`https://developer.apple.com/app-store/review/guidelines/`) is plain HTML — fetch it directly.
- Reference files: CONVENTIONS.md header block, decision-grade only, ~100–250 lines, no copied book/doc prose (own words; short attributed quotes with quotation marks OK), no remaining `[VERIFY` markers at commit.
- Evidence standard (standing): every consume-test/verification claim is backed by a captured log under the SDD workspace, with quoted lines in the report; verification tables use `file:line-range` evidence pointers.
- **Implementer-brief template text (spec process adoption — copy VERBATIM into every subagent brief that runs nested sessions):** "Run nested `claude` sessions synchronously in the foreground and wait for completion — never background-and-wait. When the nested session must write files, use `--permission-mode auto`."
- Consume-test prompts (spec process adoption): before running any consume-test, re-validate the prompt's topic against the ACTUAL shipped reference content (grep the reference for the topic); if coverage is missing, adjust the prompt to a covered topic and record the adjustment in the task report. From-scratch "Build X" prompts get a fixture cwd and `--max-turns` ≥ 25.
- Commit after every task minimum. Version bump to 0.4.0 only in Task 8.
- `claude plugin validate . --strict` must pass at every commit that touches `plugin/`.

---

### Task 0: Branch + Phase 2 debt clearance + kill-switch measurement + agent gate

**Files:**
- Modify: `plugin/skills/apple-design/references/swiftui-design-implementation.md` (~line 53)
- Modify: `plugin/skills/apple-design/SKILL.md` (empty-states routing line)
- Modify: `plugin/skills/apple-design/references/hig-foundations.md` (~lines 24-28, 154-155, 207-212)
- Modify: `plugin/skills/apple-design/references/accessibility.md` (~lines 50, 87)
- Modify: `plugin/skills/apple-design/references/hig-patterns.md` (~line 143 + header)
- Modify: `docs/deferred.md` (kill-switch result + agent-gate decision recorded)
- Delete: `docs/phase-2-debt.md`

**Interfaces:**
- Consumes: `docs/phase-2-debt.md` (authoritative item list — read it first) and `docs/deferred.md` item 1.
- Produces: a debt-free plugin tree; the **agent-gate verdict** (PASS/FAIL, recorded in `docs/deferred.md`) that decides whether Task 6 runs.

- [ ] **Step 1: Create the branch**

```bash
cd ~/Projects/apple-studio && git checkout -b phase-3
```

- [ ] **Step 2: Fix the generic clause.** In `swiftui-design-implementation.md` ~line 53 (verify with `grep -n "repeat each" plugin/skills/apple-design/references/swiftui-design-implementation.md`): the quoted generic clause must read `<each Content>`, not `<repeat each Content>` (`repeat` belongs in usage positions only).

- [ ] **Step 3: Fix the empty-states routing line.** In `apple-design/SKILL.md`, the routing line sends "empty states" to `hig-patterns.md`, but the HIG has no empty-states page. Either trim "empty states" from the line or annotate it "(HIG gap — hig-patterns.md covers the pattern from SwiftUI conventions)" to match what hig-patterns.md actually discloses. Read hig-patterns.md's empty-state section first and make the SKILL.md line truthful to it.

- [ ] **Step 4: Kill-switch trim.** Remove the stray watchOS/tvOS/visionOS bullets (platforms not shipped): `hig-foundations.md` ~:26-28, ~:154-155, ~:207-212 and `accessibility.md` ~:50, ~:87. Verify each line with `sed -n '<line>p'` before deleting (line numbers drifted if earlier edits landed); remove the bullet content, keep surrounding structure coherent.

- [ ] **Step 5: Deduplicate consistent facts → cross-refs.** Two pairs: (a) Settings{}/Cmd-, wiring at `hig-patterns.md:143` + `swiftui-design-implementation.md:77` — keep the hig-patterns.md version, replace the swiftui-design-implementation.md passage with one line pointing at it; (b) macOS bottom-edge rule at `hig-foundations.md:24-25` + `platform-idioms.md:59` — keep the platform-idioms.md version, cross-ref from hig-foundations.md. Verify line numbers first as in Step 4.

- [ ] **Step 6: Drop the uncited path-controls URL** from `hig-patterns.md`'s header block (it was investigated-and-excluded in Phase 2; the token-fields URL stays — it is cited).

- [ ] **Step 7: Kill-switch load-frequency measurement** (`docs/deferred.md` item 1). Measure real-world exercise of the two reviewer agents from session transcripts:

```bash
mkdir -p /tmp/killswitch && cd ~/.claude/projects
grep -rlE 'swift-reviewer|design-reviewer' . --include='*.jsonl' > /tmp/killswitch/all-hits.txt
wc -l /tmp/killswitch/all-hits.txt
```

Then classify: exclude hits whose project directory is a scratchpad/fixture path (contains `-scratchpad-` or `-private-tmp-`) or an apple-studio/StudioFixture plugin-verification session (inspect the transcript's first user message). For each remaining candidate, confirm a GENUINE invocation: the transcript contains a Task/agent tool_use with the reviewer as agent type (not a mere text mention), followed by Read tool_uses on `skills/*/references/` paths. Record per-agent counts (genuine invocations / references read) and the classification evidence (file paths + quoted lines) in the task report.

- [ ] **Step 8: Apply the agent gate** (spec rule, verbatim): "if the measurement shows real exercise — any genuine invocations with reference reads outside the plugin's own verification runs — the release-preflight agent … ships in this phase. If not, no new agent this phase." Record in `docs/deferred.md`: replace item 1 with the measurement result, the verdict (`Agent gate: PASS` or `Agent gate: FAIL`), and — on FAIL — a deferred entry "release-preflight agent; trigger: first real release". Task 6 executes only on PASS.

- [ ] **Step 9: Delete `docs/phase-2-debt.md`** (all five items now cleared; the process adoptions are baked into this plan's Global Constraints).

- [ ] **Step 10: Validate + commit**

```bash
claude plugin validate . --strict
git add -A && git commit -m "chore: clear Phase 2 debt + kill-switch measurement and agent-gate verdict"
```

---

### Task 1: Convert Phase 3 books + build the two distillation maps

**Files:**
- Create: `corpus/ios-app-distribution-and-best-practises-v1-0-0.md` (+ `.toc.md`) and `corpus/push-notifications-by-tutorials-v4-0-0.md` (+ `.toc.md`) — gitignored
- Create: `pipeline/maps/app-release-books.md` (chapter map, both books)
- Create: `pipeline/maps/app-release-live.md` (live-doc endpoint map)

**Interfaces:**
- Consumes: `pipeline/convert.sh`; the endpoints pre-probed during planning (all returned 200 on 2026-08-04, listed in Step 3).
- Produces: maps that Tasks 2–4 dispatch from. Book-map format identical to Phases 1–2 (`- L<start>–L<end>: <chapter title> → <target reference file>`); live-map format: `## <reference file>` sections listing `- <canonical human URL> → <DocC JSON endpoint>` (or `→ HTML` for the guidelines page).

- [ ] **Step 1: Convert the two books**

```bash
cd ~/Projects/apple-studio && pipeline/convert.sh \
  "/Users/michaelfrenchfultonjr/Documents/Apple Books/iOS_App_Distribution_and_Best_Practises_v1.0.0.epub" \
  "/Users/michaelfrenchfultonjr/Documents/Apple Books/Push_Notifications_by_Tutorials_v4.0.0.epub"
```

Expected: two `.md` + two `.toc.md` files in `corpus/`. Spot-check one mid-book heading per file via `sed -n '<line>p'`.

- [ ] **Step 2: Build `pipeline/maps/app-release-books.md`.** From the TOCs, map chapters to targets — remembering both books are **judgment-only** sources (see Global Constraints):
  - Distribution book → `signing-and-provisioning.md`: chapters explaining the signing mental model (certificates/keys/profiles relationships, why signing exists); → `app-store-submission.md`: chapters on review process judgment and rejection patterns; → `testflight-and-versioning.md`: beta-testing strategy and versioning-discipline chapters; → `ci-release-automation.md`: automation-principles chapters ONLY (its fastlane-era tooling chapters are presumptively stale — skip mechanics, keep the "what should a release pipeline guarantee" judgment).
  - Push book → `push-notifications.md`: APNs architecture, token lifecycle, delivery semantics, silent-push judgment, extension concepts. Skip server-implementation chapters (out of scope per spec) and any UI/API walkthroughs (live primer territory).
  - Be ruthless; most walkthrough chapters carry no durable judgment. Verify every range start with `sed -n '<start>p'`.

- [ ] **Step 3: Build `pipeline/maps/app-release-live.md`.** Seed with the eight endpoints probed during planning (all 200, 2026-08-04):
  - `https://developer.apple.com/tutorials/data/documentation/xcode/distribution.json` (index — enumerate its child topics)
  - `https://developer.apple.com/tutorials/data/documentation/xcode/xcode-cloud.json` (index — enumerate)
  - `https://developer.apple.com/tutorials/data/documentation/xcode/distributing-your-app-for-beta-testing-and-releases.json`
  - `https://developer.apple.com/tutorials/data/documentation/usernotifications.json`
  - `https://developer.apple.com/tutorials/data/documentation/usernotifications/sending-notification-requests-to-apns.json`
  - `https://developer.apple.com/tutorials/data/documentation/appstoreconnectapi.json`
  - `https://developer.apple.com/tutorials/data/documentation/bundleresources/privacy-manifest-files.json`
  - `https://developer.apple.com/app-store/review/guidelines/` (HTML)

  Fetch the two index endpoints, enumerate their section topics, and assign child endpoints per reference file: → `signing-and-provisioning.md`: certificates/profiles/entitlements/signing pages under distribution; → `app-store-submission.md`: submission pages + privacy-manifest pages + the guidelines HTML page; → `testflight-and-versioning.md`: TestFlight/beta pages + version-numbering pages; → `ci-release-automation.md`: the Xcode Cloud topic tree + App Store Connect API automation pages; → `push-notifications.md`: the UserNotifications APNs-setup/sending pages + `com.apple.developer.aps-environment` entitlement page. Every endpoint listed must have returned JSON (or HTML for the guidelines page) when actually fetched — no invented endpoints; record expected-but-missing pages as `MISSING:`.

- [ ] **Step 4: Commit**

```bash
git add pipeline/maps && git commit -m "feat: Phase 3 distillation maps (books + live release/push endpoints)"
```

---

### Task 2: Distill `signing-and-provisioning.md` + `app-store-submission.md`

**Files:**
- Create: `plugin/skills/app-release/references/signing-and-provisioning.md`
- Create: `plugin/skills/app-release/references/app-store-submission.md`

**Interfaces:**
- Consumes: `pipeline/maps/app-release-live.md` (primary) + `pipeline/maps/app-release-books.md` (judgment ranges); `pipeline/distill-prompt.md` (adapted as in Phase 2: corpus-lines input becomes "Fetch these DocC JSON endpoints: <the map's list for your file>" plus "…and these corpus line ranges for judgment only"; currency rule becomes "cite the canonical human URL per claim cluster; `[VERIFY: ...]` for anything inferred beyond fetched text").
- Produces: the two references (exact filenames above) read by SKILL.md (Task 5) and release-preflight (Task 6, conditional).

- [ ] **Step 1: Dispatch two distiller subagents** (parallel, model sonnet), one per file, with the adapted pipeline prompt. Include the implementer-brief template text from Global Constraints verbatim. Content requirements from the spec:
  - `signing-and-provisioning.md`: certificates vs App Store Connect API keys, automatic vs manual signing judgment (when manual is actually warranted), provisioning profiles, entitlements, classic signing failures (local and CI keychain) each with the error text a developer actually sees. Covers the full paid-team path (distribution certificates, App Store profiles) even though this phase can't exercise it.
  - `app-store-submission.md`: submission flow end-to-end, top rejection causes with the review-guideline numbers they map to (from the guidelines HTML page), privacy manifests and nutrition labels, export compliance (`ITSAppUsesNonExemptEncryption`), metadata requirements.
  - Book input is judgment-only: any book claim about process mechanics gets `[VERIFY:]` and is checked against the live pages (the book predates Xcode Cloud AND privacy manifests — assume its mechanics are stale).

- [ ] **Step 2: Resolve `[VERIFY:]` flags** (fetch the relevant endpoint; drop unverifiable inferences). `grep -rn "VERIFY" plugin/skills/app-release/` → empty.

- [ ] **Step 3: Add CONVENTIONS.md headers** (`> verified: 2026-08 against <human URLs checked>` / `> sources: iOS App Distribution v1.0.0 (judgment only), live Apple docs`).

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/app-release && git commit -m "feat: app-release signing + submission references"
```

---

### Task 3: Distill `testflight-and-versioning.md` + `ci-release-automation.md`

**Files:**
- Create: `plugin/skills/app-release/references/testflight-and-versioning.md`
- Create: `plugin/skills/app-release/references/ci-release-automation.md`

**Interfaces:**
- Consumes: both maps; adapted distill prompt as in Task 2; `plugin/skills/xcode-loop/references/headless-commands.md` (sibling — for the consistency check in Step 3).
- Produces: the two references (exact filenames) for Tasks 5–6.

- [ ] **Step 1: Dispatch two distillers** (parallel, sonnet; brief template text verbatim). Content requirements:
  - `testflight-and-versioning.md`: internal vs external testing (review implications, tester limits), `CFBundleVersion` vs `CFBundleShortVersionString` discipline (what must increase when, per-platform uniqueness rules), phased release and expedited review judgment, release-strategy guidance (when TestFlight externally vs internal-only).
  - `ci-release-automation.md`: **Xcode Cloud first** as the default voice (workflows, environments, TestFlight distribution from CI, when Xcode Cloud is enough); generic self-managed path second (`xcodebuild archive` → `-exportArchive` with an `ExportOptions.plist`, a minimal GitHub Actions job sketch, App Store Connect API keys for automated signing/upload); fastlane named once as an established alternative, not documented.
  - The GitHub Actions sketch must be a complete runnable YAML block (checkout, Xcode selection, archive, export) — no "..." placeholders — with signing handled via App Store Connect API key secrets, and a stated caveat that it is doc-derived, not CI-executed (free-tier boundary).

- [ ] **Step 2: Resolve `[VERIFY:]` flags**; grep → empty. Headers as in Task 2 Step 3.

- [ ] **Step 3: Sibling-consistency check.** `ci-release-automation.md` must not restate xcode-loop's verified build/test commands — where the inner loop overlaps (build, test, simulator), point at `xcode-loop`'s `headless-commands.md` instead. Archive/export commands are new ground and belong here.

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/app-release && git commit -m "feat: app-release testflight/versioning + CI automation references"
```

---

### Task 4: Distill `push-notifications.md` + primer cross-ref

**Files:**
- Create: `plugin/skills/app-release/references/push-notifications.md`
- Modify: `plugin/skills/apple-frameworks/references/primers/usernotifications.md` (one cross-ref line)

**Interfaces:**
- Consumes: both maps (push book ranges + UserNotifications/APNs endpoints); adapted distill prompt; `plugin/skills/apple-frameworks/references/primers/usernotifications.md` (sibling — read before writing to avoid duplication).
- Produces: `push-notifications.md` for Tasks 5–6; the primer cross-ref.

- [ ] **Step 1: Dispatch one distiller** (sonnet; brief template text verbatim). Scope is **APNs ops only** (spec): auth keys vs certificates (and why keys won), dev/prod APNs environments and the `aps-environment` entitlement, capabilities setup, device-token lifecycle judgment, silent-push budget and throttling reality, notification service/content extensions (including their separate signing), delivery debugging (`xcrun simctl push` for simulator payload testing, Console.app APNs logging). What the server must guarantee is judgment-level only — no server implementation (out of scope). API usage (requesting authorization, handling notifications in-app) is the primer's territory: read `primers/usernotifications.md` first and cross-reference it rather than restating anything it covers.

- [ ] **Step 2: Resolve `[VERIFY:]` flags**; grep → empty. Header: `> sources: Push Notifications by Tutorials v4.0.0 (judgment only), live Apple docs`.

- [ ] **Step 3: Add the primer cross-ref.** In `primers/usernotifications.md`, append one line in its pointers/see-also position (match the primer's existing style): `For APNs ops — keys, environments, entitlements, delivery debugging — see the app-release skill's references/push-notifications.md.`

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/app-release plugin/skills/apple-frameworks && git commit -m "feat: app-release push-notifications ops reference + primer cross-ref"
```

---

### Task 5: `app-release` SKILL.md + evals + consume-test

**Files:**
- Create: `plugin/skills/app-release/SKILL.md`
- Create: `plugin/skills/app-release/evals/triggers.md`

**Interfaces:**
- Consumes: the five references from Tasks 2–4 (exact filenames as listed there).
- Produces: the complete skill; Task 6's agent (conditional) points at `${CLAUDE_PLUGIN_ROOT}/skills/app-release/references/`.

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: app-release
description: Shipping iOS/macOS apps - code signing and provisioning, certificates and App Store Connect API keys, TestFlight beta distribution, App Store submission and rejection avoidance, privacy manifests and export compliance, version and build numbering, push notification (APNs) setup and delivery debugging, and CI release automation with Xcode Cloud. Use when archiving or distributing a build, fixing signing or provisioning errors, setting up TestFlight, preparing for or responding to App Review, configuring push infrastructure, or automating releases. Not for in-app feature work, UI, or local-notification API usage.
---

# App release (shipping and operating)

Scope: release engineering and ops. In-app API usage (requesting notification
permission, handling pushes in code) belongs to the apple-frameworks
usernotifications primer; UI belongs to apple-design.

Read the reference for the decision at hand:
- Certificates, profiles, entitlements, signing errors → `references/signing-and-provisioning.md`
- Submitting, App Review, rejections, privacy manifests → `references/app-store-submission.md`
- TestFlight, beta strategy, version/build numbers → `references/testflight-and-versioning.md`
- APNs keys, environments, delivery debugging → `references/push-notifications.md`
- Xcode Cloud, archive/export automation, CI pipelines → `references/ci-release-automation.md`

Rules that always apply:
- Read the actual error before theorizing: signing and upload failures name
  their cause more often than developers expect.
- The live App Review Guidelines page wins over anything written here:
  https://developer.apple.com/app-store/review/guidelines/
- Releases are repeatable or they are broken: anything done twice by hand
  belongs in the CI reference's automation path.
- Version/build numbers are a contract with App Store Connect — follow the
  discipline in testflight-and-versioning.md before every upload.
- Inner-loop build/test/simulator commands live in the xcode-loop skill;
  this skill starts where distribution starts (archive).
```

- [ ] **Step 2: Write `evals/triggers.md`**

```markdown
# app-release trigger evals
## Should fire
- "Set up TestFlight so external testers can try the beta"
- "xcodebuild says 'No signing certificate iOS Distribution found'"
- "What do I need in place before submitting to the App Store?"
- "My app was rejected under guideline 2.1 - what now?"
- "Set up push notifications - APNs keys, entitlements, the works"
- "Automate our release builds with Xcode Cloud"
- "How should I manage version and build numbers across releases?"
## Should NOT fire
- "Build and run the app on the simulator"      (xcode-loop)
- "Show a local notification when the timer ends" (apple-frameworks primer)
- "Design the onboarding screens"                (apple-design)
- "Should I use SwiftData or Core Data?"         (swift-architecture)
```

- [ ] **Step 3: Pre-validate the consume-test prompt** (Global Constraints rule): `grep -in "signing certificate\|distribution certificate" plugin/skills/app-release/references/signing-and-provisioning.md` — confirm the reference actually covers missing-distribution-certificate failures. If not covered, pick a covered signing-failure topic from the file and adjust the Step 4 prompt accordingly; record the adjustment.

- [ ] **Step 4: Consume-test with captured evidence.** From `~/Projects/StudioFixture`: `claude --plugin-dir ~/Projects/apple-studio/plugin -p "I'm getting 'No signing certificate iOS Distribution found' when archiving for TestFlight. Explain what's wrong and exactly how to fix it. Answer now, no clarifying questions." --output-format stream-json --verbose --max-turns 15` → save to the SDD workspace as `task-5-consume-test.log`. Evidence required: skill invocation, ≥1 reference Read (expect `signing-and-provisioning.md`), answer visibly applying its content (certificate types, where they live, the automatic-signing judgment). Fixture tree stays clean (read-only prompt; verify `git -C ~/Projects/StudioFixture status --porcelain` is empty).

- [ ] **Step 5: Validate + commit**

```bash
claude plugin validate . --strict
git add plugin/skills/app-release && git commit -m "feat: app-release skill (SKILL.md + evals)"
```

---

### Task 6 (CONDITIONAL — only if Task 0 recorded `Agent gate: PASS`): `release-preflight` agent + seeded-flaw verification

**Skip rule:** if `docs/deferred.md` records `Agent gate: FAIL`, this task is a no-op — verify the deferred entry exists ("release-preflight agent; trigger: first real release") and move on. Do not build the agent "since we're here".

**Files:**
- Create: `plugin/agents/release-preflight.md`
- Create: `pipeline/fixtures/flawed-release/Info.plist`, `pipeline/fixtures/flawed-release/FlawedRelease.entitlements`, `pipeline/fixtures/flawed-release/TrackedSettings.swift`

**Interfaces:**
- Consumes: `plugin/skills/app-release/references/` (all five files from Tasks 2–4).
- Produces: the `apple-studio:release-preflight` agent.

- [ ] **Step 1: Write `plugin/agents/release-preflight.md`**

```markdown
---
name: release-preflight
description: Pre-submission release audit for iOS/macOS apps - signing and entitlements consistency, Info.plist release requirements, privacy manifest coverage, export compliance, version and build number discipline, push/APNs configuration, and App Store rejection risks. Use before archiving for TestFlight or the App Store, before submitting for review, or when the user asks whether the app is ready to ship.
tools: Read, Grep, Glob, Bash
---

You are a release-readiness auditor. You audit against written standards -
never invent requirements Apple does not impose.

Process:
1. Inputs: the app project path. Locate and Read: the project's Info.plist
   (or generated-Info.plist build settings in project.pbxproj), any
   .entitlements files, any PrivacyInfo.xcprivacy, and the source files that
   use permission-gated or required-reason APIs (Grep for usage-description
   API families: camera, photos, location, tracking, notifications,
   UserDefaults).
2. Load the standards. Read ALL files in:
   - ${CLAUDE_PLUGIN_ROOT}/skills/app-release/references/
3. Audit dimensions: signing/entitlements consistency (entitlements present
   but unused, or used capabilities without entitlements), Info.plist release
   requirements (usage descriptions for every gated API actually used,
   export-compliance key), privacy manifest coverage (required-reason APIs
   declared), version/build discipline (CFBundleVersion vs
   CFBundleShortVersionString per testflight-and-versioning.md), ATS
   configuration (arbitrary-loads exceptions), push configuration
   (aps-environment vs actual registration code), known rejection risks
   (app-store-submission.md).
4. Verify each finding against a reference before reporting; cite file:line
   in the audited project for every finding.

Output (your final message is the deliverable):
- Findings ranked [BLOCKER] > [MAJOR] > [MINOR] > [NIT], each with
  what/where (file:line), the reference that makes it a problem, and a
  concrete fix.
- End with verdict (READY / READY WITH CHANGES / NOT READY) and a one-line
  summary. Clean projects get a clean verdict - never invent findings.
```

- [ ] **Step 2: Write the seeded fixture** with exactly five planted release flaws. `pipeline/fixtures/flawed-release/Info.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<!-- Seeded release-flaw fixture for release-preflight verification. Planted flaws:
     1 (ATS): NSAllowsArbitraryLoads true - App Review red flag, weakens transport security.
     2 (export compliance): ITSAppUsesNonExemptEncryption missing entirely.
     3 (usage description): TrackedSettings.swift uses the camera; no NSCameraUsageDescription here.
     4 (versioning): CFBundleShortVersionString 2.3 but CFBundleVersion regressed to 1. -->
<plist version="1.0">
<dict>
	<key>CFBundleShortVersionString</key>
	<string>2.3</string>
	<key>CFBundleVersion</key>
	<string>1</string>
	<key>NSAppTransportSecurity</key>
	<dict>
		<key>NSAllowsArbitraryLoads</key>
		<true/>
	</dict>
</dict>
</plist>
```

`pipeline/fixtures/flawed-release/FlawedRelease.entitlements` (flaw 5 — production APNs entitlement with no registration code anywhere in the fixture source):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>aps-environment</key>
	<string>production</string>
</dict>
</plist>
```

`pipeline/fixtures/flawed-release/TrackedSettings.swift` (feeds flaws 3 and 5; also uses a required-reason API with no PrivacyInfo.xcprivacy in the fixture — acceptable overlap with flaw 3's dimension, count it under flaw 3's usage-description finding OR as a privacy-manifest finding, either is a pass):

```swift
import AVFoundation
import Foundation

// Part of the seeded release-flaw fixture. Uses the camera (no usage
// description in Info.plist) and UserDefaults (required-reason API, no
// privacy manifest in this fixture). Never registers for remote
// notifications despite the production aps-environment entitlement.
final class TrackedSettings {
    func startCapture() async -> Bool {
        await AVCaptureDevice.requestAccess(for: .video)
    }
    func save(lastReview: Date) {
        UserDefaults.standard.set(lastReview, forKey: "lastReview")
    }
}
```

- [ ] **Step 3: Verification run with captured evidence.** Fresh session: `claude --plugin-dir ~/Projects/apple-studio/plugin -p "Use the release-preflight agent to audit the project at ~/Projects/apple-studio/pipeline/fixtures/flawed-release for release readiness. Report its findings verbatim." --output-format stream-json --verbose` → `task-6-verify.log`. All five planted flaws must be found with reference citations. A missed flaw = strengthen the corresponding reference (knowledge gap, not agent prompt), re-run, document the iteration.

- [ ] **Step 4: Validate + commit**

```bash
claude plugin validate . --strict
git add plugin/agents pipeline/fixtures && git commit -m "feat: release-preflight agent + seeded release-flaw fixture"
```

---

### Task 7: Free-tier exercise — archive/export + simctl push

**Files:**
- Create (SDD workspace only, not committed to plugin): captured logs `task-7-archive.log`, `task-7-export.log`, `task-7-push.log`, screenshot `task-7-push-banner.png`

**Interfaces:**
- Consumes: `ci-release-automation.md`'s archive/export commands (Task 3) and `push-notifications.md`'s `simctl push` flow (Task 4) — this task executes what those references claim.
- Produces: captured evidence for Task 8's verification table; corrections back into the references if any documented command fails as written.

- [ ] **Step 1: Archive StudioFixture** using the exact command documented in `ci-release-automation.md` (free personal-team signing):

```bash
cd ~/Projects/StudioFixture && xcodebuild archive -scheme StudioFixture \
  -destination 'generic/platform=iOS Simulator' \
  -archivePath /tmp/StudioFixture.xcarchive 2>&1 | tail -20
```

If the reference documents a device-destination archive, run that variant too if it succeeds with personal-team signing; on failure, capture the failure as the documented free-tier boundary (device archives may require provisioning a device). At least the simulator-destination archive must succeed. Save output → `task-7-archive.log`. **If the command as written in the reference fails for a fixable documentation reason, fix the reference, re-run, and record the correction.**

- [ ] **Step 2: Development export dry-run.** Attempt `-exportArchive` with a development-method `ExportOptions.plist` exactly as the reference documents it. Personal teams cannot export App Store method — that expected failure, captured verbatim, IS the free-tier boundary evidence. Save output → `task-7-export.log`.

- [ ] **Step 3: simctl push test.** Temporarily modify StudioFixture: add a `UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound])` call on launch with an OSLog line on grant and a foreground-presentation delegate that logs receipt (use `Logger(subsystem: "dev.frenchfultonjr.StudioFixture", category: "push-test")`). Build, boot a simulator, install, launch (xcode-loop headless commands). **CHECKPOINT (user-assisted, one tap):** ask the user to tap "Allow" on the permission alert in the simulator window. Then:

```bash
cat > /tmp/push-test.apns <<'EOF'
{ "aps": { "alert": { "title": "Phase 3 verification", "body": "simctl push delivery test" }, "sound": "default" } }
EOF
xcrun simctl push booted dev.frenchfultonjr.StudioFixture /tmp/push-test.apns
xcrun simctl io booted screenshot /tmp/push-banner.png
```

Evidence: the push command's success output, the delegate's OSLog receipt line (`xcrun simctl spawn booted log show --last 2m --predicate 'subsystem == "dev.frenchfultonjr.StudioFixture"'`), and the banner screenshot → `task-7-push.log` + `task-7-push-banner.png`. Then **revert StudioFixture** (`git -C ~/Projects/StudioFixture checkout . && git -C ~/Projects/StudioFixture status --porcelain` → empty).

- [ ] **Step 4: Fold corrections back.** If Steps 1–3 revealed any reference claim that didn't survive contact (wrong flag, wrong plist key, wrong log predicate), the reference is fixed in this task and the fix committed:

```bash
cd ~/Projects/apple-studio && git add plugin/skills/app-release && git commit -m "fix: app-release reference corrections from free-tier exercise" || echo "no corrections needed"
```

---

### Task 8: Integration verification + 0.4.0 release

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json` (0.3.0 → 0.4.0)
- Modify: `docs/specs/2026-08-04-phase3-release-ops-design.md` (append `## Phase 3 verification results (<date>)`)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Trigger-eval sampling.** For `app-release`: all 7 should-fire + all 4 should-NOT-fire prompts. For each prior skill (apple-design, apple-frameworks, swift-architecture, swift-concurrency, swift-testing, xcode-loop): 1 should-fire + 1 should-NOT prompt (regression sample). Method: `claude --plugin-dir ./plugin -p "<prompt>" --max-turns 2 --output-format stream-json`, one log per prompt in the SDD workspace. Record the pass/fail table. Misfire → tighten the description, re-run that prompt, record old → new.

- [ ] **Step 2: `claude plugin validate . --strict`** — pass, zero warnings, captured.

- [ ] **Step 3: Append `## Phase 3 verification results (<date>)`** to the Phase 3 spec: one entry per deliverable (debt cleared; kill-switch measurement + gate verdict with evidence; 5 references with sources; skill consume-test; agent verification 5/5 or the deferred entry; free-tier exercise incl. the captured export boundary; eval table) — with `file:line-range` evidence pointers, honest caveats verbatim where things were partial.

- [ ] **Step 4: Bump version to 0.4.0, commit, tag**

```bash
git add -A && git commit -m "release: apple-studio 0.4.0 - Phase 3 (release & ops)"
git tag v0.4.0
claude plugin validate . --strict
```

(Installed-plugin update happens post-merge, controller-handled, as in Phases 1–2. Xcode re-import after merge — operational rule, `docs/deferred.md` item 3.)

---

## Self-review notes

- Spec coverage: deliverables (5 refs → Tasks 2–4; SKILL.md + evals → Task 5; primer cross-ref → Task 4; conditional agent → Task 6 with the gate in Task 0) ✓; sources/pipeline + endpoint probing (probed at planning, listed in Task 1) ✓; opening task debt + kill-switch (Task 0) ✓; coverage-vs-verification boundary (Global Constraints verbatim + Task 7 Step 2 capturing the boundary as evidence) ✓; free-tier verification (Tasks 5, 7, 8) ✓; out-of-scope list respected (no server push code, no fastlane depth, no store submission) ✓; process adoptions (brief template text, consume-test pre-validation, turn budgets) in Global Constraints ✓.
- Deliberate scope cuts (YAGNI): no notarization/Developer ID coverage this phase (macOS direct distribution is a different path; the skill covers App Store distribution for both platforms — revisit if Michael ships outside the Mac App Store); no App Store Connect API client tooling beyond documented usage; no watchOS/tvOS/visionOS distribution (charter).
- Line numbers in Task 0 are approximate by design (Phase 2's own convention) — every step verifies with grep/sed before editing.
- Task 6's conditionality is explicit with a skip rule so a subagent can't rationalize building the agent on a FAIL verdict.
- Task 7 deliberately exercises the references' own documented commands (not independently invented ones) so failures indict the docs, matching the Phase 2 "missed flaw = knowledge gap" principle.
