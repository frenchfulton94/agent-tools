# Chapter map: app-release books

Targets (Tasks 2–4): `signing-and-provisioning.md`, `app-store-submission.md`,
`testflight-and-versioning.md`, `ci-release-automation.md`, `push-notifications.md`.

Book scope per brief (2026-08-04-phase3-release-ops/task-1-brief.md): both books are
**judgment-only** sources. The distribution book (v1.0.0, ~2021) predates Xcode Cloud
and privacy manifests; its fastlane-era tooling chapters (Ch13 Introduction to Fastlane,
and the fastlane-specific sections of Ch15/16) are presumptively stale and excluded
wholesale — only "what should a release pipeline guarantee" automation-principle
judgment is mapped from the automation/CI/publishing chapters. The push book (v4.0.0)
predates current APNs consoles and third-party push-testing tools; its server-side
chapters (Ch6, Ch7) are out of scope per the task spec (server implementation, not an
iOS-app skill), and UI/API implementation walkthroughs (Xcode capability clicking,
SwiftUI notification-UI construction, Core Data wiring) are treated as live-primer
territory and skipped even where they sit inside an otherwise-mapped chapter. Every
range start below was verified with `sed -n '<start>p'` against the converted corpus
files.

## ios-app-distribution-and-best-practises-v1-0-0.md

- L997–L1410: Chapter 4: Code Signing & Provisioning (full chapter — the signing
  mental model: App Sandbox's origin and purpose, the "code-signed provisioning
  profile" as the answer to "who/what/can I trust/where", certificates and X.509
  public-key cryptography, entitlements as key-value capability declarations, how a
  provisioning profile ties App ID + entitlements + certificate + device list
  together) → signing-and-provisioning.md
- L659–L720: Chapter 3, "The anatomy of an app submission" (App ID/app record vs
  app-level info vs version-level info — the structural mental model that Chapter 7's
  rejection-scope diagram depends on) → app-store-submission.md
- L949–L985: Chapter 3, "What to expect from App Review?" (concrete common-rejection
  list: crashes, inaccurate screenshots, subpar UI, incomplete IAP, disallowed
  category, private-API scanning; review-time expectations) → app-store-submission.md
- L2127–L2452: Chapter 7: Preparing for App Review (full chapter — the five guiding
  principles behind the guidelines [provide value, ensure quality, don't cheat,
  respect users, assume full responsibility], the guideline-document map, phased/
  manual/automatic release-option judgment, app-status meanings, and the
  Resolution-Center rejection-handling process) → app-store-submission.md
- L777–L808: Chapter 3, "Bumping the build number" (version vs. build-number
  distinction, semantic-versioning pointer — thin section, mostly a UI-click
  walkthrough, but the versioning-discipline definition is the only place this book
  states it) → testflight-and-versioning.md
- L1421–L1459: Chapter 5, "Types of internal distribution" (Personal Team vs. ad hoc
  vs. TestFlight vs. in-house vs. Custom App Distribution — the tradeoff taxonomy for
  choosing a distribution channel) → testflight-and-versioning.md
- L1777–L1802: Chapter 5, "Choosing a distribution method" + Key points (decision
  judgment: third-party service vs. manual vs. TestFlight, deferred explicitly to
  Chapter 6) → testflight-and-versioning.md
- L1909–L1928: Chapter 6, "Beta testing with TestFlight" (running a beta test is
  coordination work, not technical work: recruiting, onboarding, triaging feedback)
  → testflight-and-versioning.md
- L2097–L2126: Chapter 6, "TestFlight versus ad hoc" + Key points (flexibility vs.
  speed vs. simplicity tradeoff judgment, team-size-driven preference pattern)
  → testflight-and-versioning.md
- L5453–L5460: Chapter 15, "Alternative hosting" (TestFlight vs. self-hosted ad hoc
  for security-conscious orgs — short but distinct judgment not covered above)
  → testflight-and-versioning.md
- L2477–L2503: Chapter 8, "Smoke testing before release" + "Creating a checklist"
  (release-checklist judgment, the Checklist Manifesto framing for why release
  checklists matter, release pages as internal documentation) → ci-release-automation.md
- L3841–L3921: Chapter 12, "Why automation?" (full section — the manual-vs-automated
  release narrative, and the five durable automation benefits: validation by testing,
  consistency, shared/explicit knowledge, frequent builds, the on-ramp to CI)
  → ci-release-automation.md
- L4977–L5070: Chapter 14 intro + "More CI benefits" + "CI components" + "Different
  types of CI" (CI as a practice — detecting problems early, CI server as single
  source of truth, the build-server/job/trigger model, and the full-service/managed/
  manual provider taxonomy; excludes the GitHub Actions implementation walkthrough
  that follows) → ci-release-automation.md
- L5385–L5420: Chapter 15, "Fast deployments" + "Continuous delivery" + "Smooth app
  reviews" + "Frequent updates" (what a CD pipeline adds on top of CI, and the
  build-status-visibility judgment) → ci-release-automation.md
- L5421–L5452: Chapter 15, "Different environments" + "Implementing different
  environments" (the dev/staging/production pattern for release pipelines handling
  sensitive data) → ci-release-automation.md
- L5461–L5490: Chapter 15, "One app, many teams" + "Building with frameworks" +
  "Multiple platforms" (large-team coordination judgment: framework-per-team
  decomposition to avoid merge-conflict coordination overhead) → ci-release-automation.md
- L5553–L5568: Chapter 16, "Twelve-Factor App Methodology" + "DevOps" (naming the
  methodology/practice this book's release-pipeline advice is drawn from — durable
  pointer, not mechanics) → ci-release-automation.md
- L5675–L5733: Appendix B: Release Page & Checklist (a concrete worked release
  checklist: backend-dependency verification, feature-flag verification, promo-code
  smoke test, git tagging, stakeholder notification — durable "what should a release
  guarantee" artifact) → ci-release-automation.md

### SKIP (distribution book)

Chapter 1 (The App Store — generic app-lifecycle/third-party-software framing, no
distinct judgment beyond what later chapters cover), rest of Chapter 2 (Your First App
in the App Store — pure Xcode/App-Store-Connect UI walkthrough for the first upload),
"Introducing App Store Connect" and the App-ID/app-record/build-number *creation*
walkthrough parts of Chapter 3 (administrative-system orientation and UI clicking,
not review judgment), rest of Chapter 5 (registering a device, creating an ad hoc
build, installing manually/wirelessly, AppCenter walkthrough — ad hoc mechanics),
rest of Chapter 6 (onboarding-tester UI clicking, Beta App Review submission
clicking, feedback/crash-report collection UI walkthrough — mechanics, not strategy),
Appendix A (TestFlight distribution-build walkthrough, pure mechanics), Chapter 9
(Build Customizations — Xcode target/scheme/build-configuration mechanics, no
durable judgment independent of the tooling), Chapter 10 (Advanced Build
Configurations — xcconfig mechanics), Chapter 11 (Managing Secrets — Info.plist/
build-setting mechanics; secrets-management judgment belongs to a security skill,
not this map's five targets), Chapter 12's project-setup/archiving/exporting/
uploading walkthrough and Chapter 13 in full (Introduction to Fastlane — explicitly
presumptively-stale fastlane-era tooling per the brief), the GitHub-repository-setup
and GitHub-Actions-workflow-authoring walkthrough in Chapter 14, "White labeling"
and "Automating with fastlane" and "After release" in Chapter 15 (product-branding
strategy, fastlane-specific tooling, and marketing — not release-pipeline judgment
or in scope for this skill set), "Becoming the next fastlane" and "Beyond
publication" in Chapter 16 (fastlane-specific and marketing), all Conclusions, and
all front matter/license/dedications/about-the-authors/forums content. "Monitoring
your app" and "Maintaining your app" in Chapter 8 were also skipped: durable
judgment exists there (built-in vs. third-party analytics tradeoffs, minimum
ongoing SDK/OS maintenance cadence) but it doesn't fit any of this map's five
target files — there's no post-release-monitoring or app-lifecycle-maintenance
skill in this set.

## push-notifications-by-tutorials-v4-0-0.md

- L141–L234: Chapter 2: Push Notifications (full chapter — remote vs. local
  notification distinction, APNs architecture and TLS-based security model, device
  token as address-not-identity, the full registration→token→provider→APNs→device
  message flow) → push-notifications.md
- L419–L464: Chapter 3, "Sending HTTP Headers" (`apns-collapse-id` collapsing
  judgment, `apns-push-type` alert-vs-background requirement, `apns-priority`
  10-vs-5 rule tied to `content-available`) + Key points (payload-design judgment,
  including the client-vs-server localization tradeoff) → push-notifications.md
- L547–L598: Chapter 4, "Provisional Authorization" + "Critical Alerts" + "Getting
  the Device Token" (authorization-strategy judgment: provisional auth for
  low-friction opt-in, critical alerts requiring a special entitlement for
  health/safety apps; token-lifecycle judgment: never hardcode token length, tokens
  rotate on reinstall/restore/new-device, never bind a token to a specific user)
  → push-notifications.md
- L625–L647: Chapter 5, "Authentication Token Types" (why Apple moved from
  PKCS#12/.p12 certificates to JWT-based `.p8` Authentication Tokens — the
  provider-authentication mental model, not the certificate-generation mechanics)
  → push-notifications.md
- L1713–L1826: Chapter 8, "Sending Silent Notifications" + "Method Routing" + Key
  points (silent-push judgment: `content-available` semantics, the required
  `apns-priority: 5` pairing, the Background Modes capability requirement, the
  ~30-second background execution budget; the delegate-method-routing table
  reference for foreground/background × silent/non-silent combinations — the
  Core Data/URL-session implementation code itself is illustrative, not durable)
  → push-notifications.md
- L1991–L2000: Chapter 10 intro (Notification Service Extension concept: "middleware
  between APNs and your UI" that can modify a payload before presentation — the
  size-limit-workaround and decrypt-before-display use cases) → push-notifications.md
- L3487–L3518: Chapter 13 intro + "You Still Need Permission!" + "Objects Versus
  Payloads" (local-notification taxonomy [calendar/interval/location] and the
  judgment to prefer a local notification over a remote one for on-device timing;
  local notifications still require the same revocable permission grant; the core
  remote-payload-vs-local-Swift-object distinction) → push-notifications.md

### SKIP (push book)

Chapter 1 (Introduction — book-scope/prerequisites front matter), rest of Chapter 3
(the `aps` dictionary key-by-key walkthrough for alert/badge/sound — payload-format
mechanics that the live UserNotifications/APNs docs cover more currently), "Adding
Capabilities" and the registration-code walkthrough in Chapter 4 (Xcode UI clicking
and boilerplate `AppDelegate` code), "Getting Your Authentication Token" and
"Sending Push Notifications" in Chapter 5 (Developer Portal UI clicking and
third-party tester-app mechanics), Chapter 6 and Chapter 7 in full (server-side
Vapor/PHP/curl implementation — explicitly out of scope per the task spec, this is
not an iOS-app-facing skill), "Displaying Foreground Notifications" and "Tapping the
Notification" in Chapter 8 (UNUserNotificationCenterDelegate/SwiftUI wiring —
UI/API implementation walkthrough, live-primer territory), Chapter 9 in full (Custom
Actions — interactive-notification-category UI wiring, not in the brief's four
push-notifications.md categories), the bulk of Chapter 10 after its intro
(configuring the extension target, ROT13 "decryption," video download, Core Data
sharing, badging, localization, debugging — all implementation mechanics for one
contrived example), Chapter 11 in full (Custom Interfaces — Notification Content
Extension SwiftUI-UI-building walkthrough), Chapter 12 in full (Putting It All
Together — a cumulative project walkthrough, no new judgment), the mechanics
sections of Chapter 13 after its intro (Creating a Trigger/Defining Content/
Scheduling/the sample-platter UI), Chapter 14 in full (watchOS — dated
platform-specific mechanics; Short/Long Looks and the watchOS notification model
have changed substantially since v4.0.0 and watchOS isn't in this map's scope), the
Conclusion, and all front matter/license/dedications/about-the-author/forums
content.
