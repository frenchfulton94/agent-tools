# Live endpoint map: app-release

Targets (Tasks 2–4): `signing-and-provisioning.md`, `app-store-submission.md`,
`testflight-and-versioning.md`, `ci-release-automation.md`, `push-notifications.md`.

## Endpoint pattern (confirmed, matches the brief's assumption)

```
https://developer.apple.com/tutorials/data/documentation/<path>.json
```

where `<path>` mirrors the human URL path under `developer.apple.com/documentation/`
(lowercase, hyphenated, exactly as Apple's own `topicSections`/`references` JSON
reports it). One exception: `https://developer.apple.com/app-store/review/guidelines/`
has no DocC JSON counterpart — it's a plain marketing/help HTML page, fetched as HTML
per the brief.

Two endpoints are DocC *index* pages (`kind: "article"`/`role: "collection"` with a
non-empty `topicSections`): `xcode/distribution.json` and `xcode/xcode-cloud.json`.
Both were fetched and every child identifier in their `topicSections` was resolved via
the `references` map to get its human URL, then that child's own JSON endpoint was
individually fetched (`curl -s -o <file> -w '%{http_code}'`) and confirmed 200 before
being added below — see the Task 1 report for the full probe log (33 additional
fetches beyond the 8 pre-probed seeds, all 200). Two other endpoints from the seed
list — `usernotifications.json` and `bundleresources/privacy-manifest-files.json` —
are themselves smaller collection/collectionGroup pages with their own
`topicSections`; their children were enumerated and probed the same way, though the
brief only named them as "index — enumerate" for the two Xcode pages. `appstoreconnectapi.json`
is a large 12-section Web Service reference (hundreds of REST resources); rather than
enumerate it exhaustively, only the automation-relevant "Essentials" (API keys, tokens,
rate limits) and the Xcode Cloud REST resource were pulled in, per the brief's narrower
"App Store Connect API automation pages" phrasing.

## signing-and-provisioning.md

- `https://developer.apple.com/documentation/xcode/distribution` → `https://developer.apple.com/tutorials/data/documentation/xcode/distribution.json` (index, enumerated below)
- `https://developer.apple.com/documentation/xcode/changing-the-bundle-identifier` → `https://developer.apple.com/tutorials/data/documentation/xcode/changing-the-bundle-identifier.json`
- `https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices` → `https://developer.apple.com/tutorials/data/documentation/xcode/distributing-your-app-to-registered-devices.json`
- `https://developer.apple.com/documentation/xcode/using-the-latest-code-signature-format` → `https://developer.apple.com/tutorials/data/documentation/xcode/using-the-latest-code-signature-format.json`
- `https://developer.apple.com/documentation/xcode/sharing-your-teams-signing-certificates` → `https://developer.apple.com/tutorials/data/documentation/xcode/sharing-your-teams-signing-certificates.json`
- `https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles` → `https://developer.apple.com/tutorials/data/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles.json`

(`distribution.json`'s index also lists macOS-only pages — packaging Mac software for
distribution, creating distribution-signed code for the Mac, notarizing macOS
software, signing a daemon with a restricted entitlement, testing a beta OS — left
unassigned as out of scope for an iOS-app-release skill set.)

## app-store-submission.md

- `https://developer.apple.com/documentation/bundleresources/privacy-manifest-files` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/privacy-manifest-files.json` (index, enumerated below)
- `https://developer.apple.com/app-store/review/guidelines/` → HTML (confirmed 200, `<title>App Review Guidelines - Apple Developer</title>` present in the fetched body)
- `https://developer.apple.com/documentation/xcode/preparing-your-app-for-distribution` → `https://developer.apple.com/tutorials/data/documentation/xcode/preparing-your-app-for-distribution.json` (Info.plist + icon prep before a submission — child of the `distribution.json` index but routed here, not to signing-and-provisioning.md, since it's submission-readiness content, not signing mechanics)
- `https://developer.apple.com/documentation/bundleresources/adding-a-privacy-manifest-to-your-app-or-third-party-sdk` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/adding-a-privacy-manifest-to-your-app-or-third-party-sdk.json`
- `https://developer.apple.com/documentation/bundleresources/describing-data-use-in-privacy-manifests` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/describing-data-use-in-privacy-manifests.json`
- `https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/describing-use-of-required-reason-api.json`
- `https://developer.apple.com/documentation/bundleresources/app-privacy-configuration` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/app-privacy-configuration.json`

MISSING: a dedicated DocC page for the App Store Connect submission/review workflow
itself (App ID → app record → version → build → "Submit for Review"). Tried
`xcode/submitting-your-app-for-review.json` and
`xcode/preparing-the-final-release-for-distribution.json` — both 404. Apple's actual
submission-workflow documentation lives in App Store Connect Help
(`help.apple.com/app-store-connect/`), which is not part of the
`developer.apple.com/documentation` DocC/tutorials JSON system and has no equivalent
endpoint to probe. The distiller for `app-store-submission.md` should treat the
distribution book's Chapter 7 (see `app-release-books.md`) as the primary source for
the submission *process* and rely on the guidelines HTML + privacy-manifest pages
above only for current policy/requirement specifics.

## testflight-and-versioning.md

- `https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases` → `https://developer.apple.com/tutorials/data/documentation/xcode/distributing-your-app-for-beta-testing-and-releases.json`
- `https://developer.apple.com/documentation/xcode/testing-a-release-build` → `https://developer.apple.com/tutorials/data/documentation/xcode/testing-a-release-build.json`
- `https://developer.apple.com/documentation/xcode/viewing-and-responding-to-feedback` → `https://developer.apple.com/tutorials/data/documentation/xcode/viewing-and-responding-to-feedback.json`
- `https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleshortversionstring` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/information-property-list/cfbundleshortversionstring.json`
- `https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleversion` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/information-property-list/cfbundleversion.json`

(note: the `information-property-list` path segment uses a hyphen; the naive
underscore form `information_property_list` 301-redirects to the hyphenated one —
confirmed via `curl -sI` before fetching the hyphenated URL directly.)

## ci-release-automation.md

- `https://developer.apple.com/documentation/xcode/xcode-cloud` → `https://developer.apple.com/tutorials/data/documentation/xcode/xcode-cloud.json` (index, enumerated below)
- `https://developer.apple.com/documentation/appstoreconnectapi` → `https://developer.apple.com/tutorials/data/documentation/appstoreconnectapi.json` (large collection index; only the automation-essentials children below were pulled in, not enumerated exhaustively)

Xcode Cloud topic tree (Essentials, Setup and maintenance, Workflows, Source code
management, Custom build scripts sections — Troubleshooting, Notifications and Usage
data sections were left out as narrow tool-support/reporting pages rather than
release-pipeline-guarantee content):

- `https://developer.apple.com/documentation/xcode/getting-started-with-xcode-cloud` → `https://developer.apple.com/tutorials/data/documentation/xcode/getting-started-with-xcode-cloud.json`
- `https://developer.apple.com/documentation/xcode/distributing-your-xcode-cloud-builds-through-testflight` → `https://developer.apple.com/tutorials/data/documentation/xcode/distributing-your-xcode-cloud-builds-through-testflight.json`
- `https://developer.apple.com/documentation/xcode/about-continuous-integration-and-delivery-with-xcode-cloud` → `https://developer.apple.com/tutorials/data/documentation/xcode/about-continuous-integration-and-delivery-with-xcode-cloud.json`
- `https://developer.apple.com/documentation/xcode/setting-up-your-project-to-use-xcode-cloud` → `https://developer.apple.com/tutorials/data/documentation/xcode/setting-up-your-project-to-use-xcode-cloud.json`
- `https://developer.apple.com/documentation/xcode/configuring-your-first-xcode-cloud-workflow` → `https://developer.apple.com/tutorials/data/documentation/xcode/configuring-your-first-xcode-cloud-workflow.json`
- `https://developer.apple.com/documentation/xcode/making-dependencies-available-to-xcode-cloud` → `https://developer.apple.com/tutorials/data/documentation/xcode/making-dependencies-available-to-xcode-cloud.json`
- `https://developer.apple.com/documentation/xcode/configuring-xcode-cloud-for-your-team` → `https://developer.apple.com/tutorials/data/documentation/xcode/configuring-xcode-cloud-for-your-team.json`
- `https://developer.apple.com/documentation/xcode/sharing-custom-aliases-across-xcode-cloud-workflows` → `https://developer.apple.com/tutorials/data/documentation/xcode/sharing-custom-aliases-across-xcode-cloud-workflows.json`
- `https://developer.apple.com/documentation/xcode/sharing-environment-variables-across-xcode-cloud-workflows` → `https://developer.apple.com/tutorials/data/documentation/xcode/sharing-environment-variables-across-xcode-cloud-workflows.json`
- `https://developer.apple.com/documentation/xcode/building-swift-packages-or-swift-playground-app-projects-with-xcode-cloud` → `https://developer.apple.com/tutorials/data/documentation/xcode/building-swift-packages-or-swift-playground-app-projects-with-xcode-cloud.json`
- `https://developer.apple.com/documentation/xcode/setting-the-next-build-number-for-xcode-cloud-builds` → `https://developer.apple.com/tutorials/data/documentation/xcode/setting-the-next-build-number-for-xcode-cloud-builds.json`
- `https://developer.apple.com/documentation/xcode/including-notes-for-testers-with-a-beta-release-of-your-app` → `https://developer.apple.com/tutorials/data/documentation/xcode/including-notes-for-testers-with-a-beta-release-of-your-app.json`
- `https://developer.apple.com/documentation/xcode/removing-your-project-from-xcode-cloud` → `https://developer.apple.com/tutorials/data/documentation/xcode/removing-your-project-from-xcode-cloud.json`
- `https://developer.apple.com/documentation/xcode/developing-a-workflow-strategy-for-xcode-cloud` → `https://developer.apple.com/tutorials/data/documentation/xcode/developing-a-workflow-strategy-for-xcode-cloud.json`
- `https://developer.apple.com/documentation/xcode/xcode-cloud-workflow-reference` → `https://developer.apple.com/tutorials/data/documentation/xcode/xcode-cloud-workflow-reference.json`
- `https://developer.apple.com/documentation/xcode/creating-a-workflow-that-builds-your-app-for-distribution` → `https://developer.apple.com/tutorials/data/documentation/xcode/creating-a-workflow-that-builds-your-app-for-distribution.json`
- `https://developer.apple.com/documentation/xcode/understanding-infrastructure-validation-builds` → `https://developer.apple.com/tutorials/data/documentation/xcode/understanding-infrastructure-validation-builds.json`
- `https://developer.apple.com/documentation/xcode/source-code-management-setup` → `https://developer.apple.com/tutorials/data/documentation/xcode/source-code-management-setup.json`
- `https://developer.apple.com/documentation/xcode/configuring-requirements-for-merging-a-pull-request` → `https://developer.apple.com/tutorials/data/documentation/xcode/configuring-requirements-for-merging-a-pull-request.json`
- `https://developer.apple.com/documentation/xcode/writing-custom-build-scripts` → `https://developer.apple.com/tutorials/data/documentation/xcode/writing-custom-build-scripts.json`
- `https://developer.apple.com/documentation/xcode/environment-variable-reference` → `https://developer.apple.com/tutorials/data/documentation/xcode/environment-variable-reference.json`

(`changing-the-bundle-identifier` is also listed under Xcode Cloud's "Setup and
maintenance" section — already captured once under signing-and-provisioning.md above,
not duplicated here.)

App Store Connect API automation essentials:

- `https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api` → `https://developer.apple.com/tutorials/data/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api.json`
- `https://developer.apple.com/documentation/appstoreconnectapi/generating-tokens-for-api-requests` → `https://developer.apple.com/tutorials/data/documentation/appstoreconnectapi/generating-tokens-for-api-requests.json`
- `https://developer.apple.com/documentation/appstoreconnectapi/identifying-rate-limits` → `https://developer.apple.com/tutorials/data/documentation/appstoreconnectapi/identifying-rate-limits.json`
- `https://developer.apple.com/documentation/appstoreconnectapi/xcode-cloud-workflows-and-builds` → `https://developer.apple.com/tutorials/data/documentation/appstoreconnectapi/xcode-cloud-workflows-and-builds.json` (the REST-resource counterpart to the `xcode/xcode-cloud-workflow-reference` human guide above — distinct page, same subject)

## push-notifications.md

- `https://developer.apple.com/documentation/usernotifications` → `https://developer.apple.com/tutorials/data/documentation/usernotifications.json` (index, enumerated below)
- `https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns` → `https://developer.apple.com/tutorials/data/documentation/usernotifications/sending-notification-requests-to-apns.json`
- `https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications` → `https://developer.apple.com/tutorials/data/documentation/usernotifications/asking-permission-to-use-notifications.json`
- `https://developer.apple.com/documentation/usernotifications/unusernotificationcenter` → `https://developer.apple.com/tutorials/data/documentation/usernotifications/unusernotificationcenter.json`
- `https://developer.apple.com/documentation/usernotifications/sending-push-notifications-using-command-line-tools` → `https://developer.apple.com/tutorials/data/documentation/usernotifications/sending-push-notifications-using-command-line-tools.json`
- `https://developer.apple.com/documentation/usernotifications/testing-notifications-using-the-push-notification-console` → `https://developer.apple.com/tutorials/data/documentation/usernotifications/testing-notifications-using-the-push-notification-console.json`
- `https://developer.apple.com/documentation/usernotifications/scheduling-a-notification-locally-from-your-app` → `https://developer.apple.com/tutorials/data/documentation/usernotifications/scheduling-a-notification-locally-from-your-app.json`
- `https://developer.apple.com/documentation/usernotifications/modifying-content-in-newly-delivered-notifications` → `https://developer.apple.com/tutorials/data/documentation/usernotifications/modifying-content-in-newly-delivered-notifications.json`
- `https://developer.apple.com/documentation/usernotifications/unnotificationserviceextension` → `https://developer.apple.com/tutorials/data/documentation/usernotifications/unnotificationserviceextension.json`
- `https://developer.apple.com/documentation/usernotifications/handling-notifications-and-notification-related-actions` → `https://developer.apple.com/tutorials/data/documentation/usernotifications/handling-notifications-and-notification-related-actions.json`
- `https://developer.apple.com/documentation/bundleresources/entitlements/aps-environment` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/aps-environment.json` (the iOS/tvOS/watchOS `aps-environment` entitlement key)
- `https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.aps-environment` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.developer.aps-environment.json` (the macOS-scoped variant of the same entitlement; this is the literal `com.apple.developer.aps-environment` page the brief named — kept both since a distiller writing about the entitlement should know they differ by platform)

(`usernotifications.json`'s index also lists "Setting up a remote notification
server", server-side sample code, custom-actions/categories pages, and most of the
notification-content/trigger class reference — left unassigned: server-side setup is
explicitly out of scope per the task spec, and the class-reference pages are
API-mechanics that don't carry the delivery-semantics/token-lifecycle/silent-push/
extension-concept judgment this map targets.)
