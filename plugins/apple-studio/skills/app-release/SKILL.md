---
name: app-release
description: Shipping iOS/macOS apps - code signing and provisioning, certificates and App Store Connect API keys, TestFlight beta distribution, App Store submission and rejection avoidance, App Store screenshots and metadata for every device size, privacy manifests and export compliance, version and build numbering, push notification (APNs) setup and delivery debugging, and CI release automation with Xcode Cloud. Use when archiving or distributing a build, fixing signing or provisioning errors, setting up TestFlight, preparing screenshots or metadata for App Store Connect, preparing for or responding to App Review, configuring push infrastructure, or automating releases. Not for in-app feature work, UI, or local-notification API usage.
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
