> verified: 2026-08 against https://developer.apple.com/documentation/bundleresources/adding-a-privacy-manifest-to-your-app-or-third-party-sdk.md, https://developer.apple.com/documentation/bundleresources/describing-data-use-in-privacy-manifests.md, https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api.md, https://developer.apple.com/documentation/xcode/preparing-your-app-for-distribution.md, https://developer.apple.com/documentation/bundleresources/information-property-list/itsappusesnonexemptencryption.md, https://developer.apple.com/app-store/review/guidelines/, https://developer.apple.com/documentation/appstoreconnectapi/appversionstate.md, https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases, https://developer.apple.com/distribute/app-review/; re-checked 2026-09 against https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications (Phase 9: iPhone Duo sizes)
> sources: iOS App Distribution and Best Practises v1.0.0 (judgment only), live Apple docs
> note: no dedicated DocC page exists for the App Store Connect submission/review workflow itself (App ID → app record → version → build → submit) — App Store Connect Help, where that workflow is documented, sits outside the DocC/tutorials JSON system and its help.apple.com pages render via client-side JS with no static content to fetch. The submission-flow structure below is therefore sourced primarily from the book (flagged and softened where UI-specific), corroborated against the live AppVersionState enum (the current, non-deprecated status enum) and App Review page where possible.

# App Store Submission

## The structural shape of a submission

Four distinct objects, created and edited in a fixed order, govern every submission — get the order wrong and you'll hit walls that look like bugs but are structural:

1. **App ID** — the Team ID + bundle ID pair that uniquely identifies the app across all of Apple's platforms. Created once, never renamed. The bundle ID in Xcode's Signing & Capabilities pane must match it exactly (iOS App Distribution and Best Practises, ch. 3). Once you upload a first build under a bundle ID, that ID is permanent for that app record — you cannot retarget an app record to a different bundle ID later (Preparing your app for distribution, https://developer.apple.com/documentation/xcode/preparing-your-app-for-distribution.md).
2. **App record** — the app's home in App Store Connect, created from the App ID. It holds app-level info, every version, every build, pricing, and review correspondence (iOS App Distribution and Best Practises, ch. 3).
3. **App-level metadata** vs **version-level metadata** — this is the split developers most often get wrong. App-level fields (name, primary/secondary category, age rating baseline) apply to the whole app and, after the first release, can only change when you submit a new version for review. Version-level fields (build, screenshots, description, release notes, localizations) are scoped to one version and reset with each new one (iOS App Distribution and Best Practises, ch. 3). Both are in App Review's jurisdiction — a single bad screenshot can sink an otherwise-compliant build (iOS App Distribution and Best Practises, ch. 7).
4. **Build → attach → submit** — upload a build via Xcode Organizer or `xcodebuild`/`altool`/`notarytool`-adjacent tooling, wait for App Store Connect to finish processing it (minutes to over an hour), then select that processed build for the version you're editing and submit for review. The exact screens shift release to release; the structural requirement doesn't — a version cannot be submitted without a processed build attached to it.

Getting this right in practice means: lock the bundle ID before your first upload, treat app-level fields as slow-moving (they gate through review too), and never assume version-level content (screenshots, description) is exempt from scrutiny just because the binary passed.

### Review states and release

After submission the app moves through app-status states — conceptually stable even though the exact list and UI presentation change over time: waiting for review, in review, and then either rejected/metadata-rejected or approved. A Resolution Center thread opens on rejection; you can request clarification, contest the finding, or ask for a phone call with App Review, and if you reach an impasse you can appeal to the App Review Board (iOS App Distribution and Best Practises, ch. 7). The App Store Connect API's `AppVersionState` (the current, non-deprecated status enum — it superseded `AppStoreVersionState` as of App Store Connect API v3.7) enumerates 15 distinct states today (up from the book's 2021-era 17) — including `PREPARE_FOR_SUBMISSION`, `WAITING_FOR_REVIEW`, `IN_REVIEW`, `REJECTED`, `METADATA_REJECTED`, `INVALID_BINARY`, `PENDING_DEVELOPER_RELEASE`, `PENDING_APPLE_RELEASE`, and `READY_FOR_DISTRIBUTION` among them (AppVersionState, https://developer.apple.com/documentation/appstoreconnectapi/appversionstate.md) — treat the exact list as an implementation detail that will keep drifting; the durable structure is the three-phase shape (pre-review → in review → resolved as rejected/approved, then released).

Approval does not equal availability. Three release modes exist and the decision is a judgment call, not a formality:

- **Manual release** — you trigger going live after approval; use when you need a last-minute check or want to coordinate a launch moment.
- **Automatic release** — goes live within ~24 hours of approval with no further action; best for routine or time-sensitive updates.
- **Automatic release, no earlier than [date]** — for coordinating with an external launch date when you can't predict exact review timing.

After the initial release, phased release ramps a new version to an increasing share of auto-update-enabled users over a fixed 7-day schedule — 1%, 2%, 5%, 10%, 20%, 50%, then 100% — and can be paused for up to 30 days total across any number of pauses if a problem surfaces; this is the only Apple-sanctioned way to roll out gradually. Shipping features "dark" and flipping them server-side without disclosure runs against guideline 2.3.1 (Hidden or undocumented features) instead (Release a version update in phases, https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases; App Review Guidelines §2.3.1, https://developer.apple.com/app-store/review/guidelines/).

If sign-in is required, provide a working test account and reviewer notes under App Review Information — this single omission is a routine, avoidable rejection cause on its own (iOS App Distribution and Best Practises, ch. 7).

## Top rejection causes, mapped to real guideline numbers

The App Review Guidelines are organized into five top-level sections — Safety (1.x), Performance (2.x), Business (3.x), Design (4.x), Legal (5.x) — each broken into numbered subsections (App Review Guidelines, https://developer.apple.com/app-store/review/guidelines/). Map common failure patterns to the actual sections instead of guessing:

| Failure pattern | Guideline(s) |
|---|---|
| Crashes, obvious bugs, broken core flow, incomplete build | §2.1 App Completeness |
| Placeholder/Lorem Ipsum content, non-functional links, broken demo accounts | §2.1, §2.3.9 (Rights to materials) |
| Inaccurate or misleading screenshots/previews | §2.3.3 Screenshots, §2.3.4 Previews |
| Misleading description, keywords, or "What's New" text | §2.3.7 (App naming and metadata rules), §2.3.12 (Feature descriptions in "What's New") |
| Wrong category selection | §2.3.5 App category selection |
| Wrong or inaccurate age rating | §2.3.6 Age rating accuracy |
| Hidden, dormant, or server-flagged "dark" features | §2.3.1 Hidden or undocumented features |
| Missing IAP restore, broken purchase flow, IAP not reflected in binary review build | §3.1.1 In-App Purchase, §2.1(b) |
| Steering users to outside payment without qualifying | §3.1.1(a) Link to Other Purchase Methods, §3.1.3 Other Purchase Methods |
| Subscription terms/pricing not disclosed | §3.1.2(c) Subscription Information |
| App is a thin wrapper around a website / template-generated with no differentiation | §4.2 Minimum Functionality, §4.2.6 Template and generated apps |
| Duplicate or near-identical app spam, multiple bundle IDs for one app | §4.3 Spam |
| Copying another app's UI, name, or icon | §4.1 Copycats |
| Data collected without disclosure or without a clear purpose | §5.1.1 Data Collection and Storage, §5.1.2 Data Use and Sharing |
| Location APIs used for autonomous vehicle/device control | §5.1.5 Location Services |
| Kids-category privacy or content violations | §1.3 Kids Category, §5.1.4 Kids |
| Objectionable/offensive user-generated or app content | §1.1 Objectionable Content, §1.2 User-Generated Content |
| Private API usage (caught by automated binary scanning, not just human review) | §2.5.1 Public APIs and current OS |

App Review pairs human reviewers making judgment calls on ambiguous cases with automated scanning for things like private-API usage that a human wouldn't reliably catch (iOS App Distribution and Best Practises, ch. 3; ch. 7). When triaging a rejection, resist arguing "other apps do this too" in Resolution Center — Apple evaluates your submission on its own facts, not by precedent (iOS App Distribution and Best Practises, ch. 7).

### The five guiding principles (the distribution book's framing)

Because the numbered guidelines change wording over time, orient a developer around the durable intent instead of memorizing section text: **provide value** (no thin wrappers, no saturated-category apps without differentiation), **ensure quality** (no crashes, no placeholder content, keep up with current SDKs), **don't cheat** (don't circumvent review, don't exploit users), **respect users** (ask permission properly, don't track unnecessarily, extra care for kids), and **assume full responsibility** (you own third-party SDK behavior and user-generated content moderation, not just your own code) (iOS App Distribution and Best Practises, ch. 7). A rejection that doesn't cleanly map to a guideline number often still maps to one of these five.

## Privacy manifests vs. the App Store "nutrition label" — two distinct systems

These are commonly conflated. Keep them separate in advice to developers:

- **Privacy manifest (`PrivacyInfo.xcprivacy`)** is a *code-level, per-bundle* property list shipped inside the app, framework, or Swift package. It is enforced by App Store Connect at upload time — invalid keys/values cause outright rejection of the upload, not just a review note (Adding a privacy manifest to your app or third-party SDK, https://developer.apple.com/documentation/bundleresources/adding-a-privacy-manifest-to-your-app-or-third-party-sdk.md).
- **App Privacy details / "nutrition label"** is a *store-listing disclosure* you fill out as a questionnaire in App Store Connect; it's what shows on the product page. Xcode can generate a **privacy report** (Product > Archive > Generate Privacy Report) by aggregating your app's manifest with every linked third-party SDK's manifest, organized to mirror the nutrition label — use that report as the source of truth when answering the App Store Connect questionnaire rather than re-deriving it by hand (Describing data use in privacy manifests, https://developer.apple.com/documentation/bundleresources/describing-data-use-in-privacy-manifests.md).

Manifest placement is bundle-type-specific: root of the bundle for iOS/iPadOS/tvOS/visionOS/watchOS apps and frameworks (`YourApp.app/PrivacyInfo.xcprivacy`); `Contents/Resources/` for macOS/Mac Catalyst apps; `Versions/A/Resources/` for macOS frameworks; and for Swift packages, alongside the target's sources (or wherever `resources:` in `Package.swift` points, declared explicitly since SwiftPM doesn't treat it as a resource by default) (Adding a privacy manifest to your app or third-party SDK).

What a manifest declares, concretely:

- `NSPrivacyCollectedDataTypes` — an array of dictionaries, one per data category you collect, each stating whether it's linked to the user's identity, whether it's used for tracking, and its declared purpose(s). Your app's manifest only needs to cover what *your own code* collects — each third-party SDK is responsible for declaring its own collection in its own manifest (Describing data use in privacy manifests).
- `NSPrivacyAccessedAPITypes` — required-reason API usage. **Required-reason APIs** are APIs that, while legitimate for core functionality, are also fingerprinting vectors (e.g., file timestamps, `UserDefaults`, disk space, system boot time, active keyboard) — Apple requires an approved reason code per category regardless of whether the app tracks users at all, because fingerprinting is disallowed independent of tracking consent (Describing use of required reason API, https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api.md). Since May 1, 2024, App Store Connect rejects uploads that use a required-reason API without a declared reason in the manifest. The declaration belongs in whichever bundle's code actually calls the API — an app can't claim reasons on behalf of a third-party SDK's usage, and vice versa.
- `NSPrivacyTracking` / `NSPrivacyTrackingDomains` — whether the app tracks per Apple's definition and which domains receive tracking data.

Since February 12, 2025, apps must ship a valid privacy manifest for certain commonly-used third-party SDKs specifically, not just for the app's own code — an outdated SDK without one is a submission blocker the app developer often can't fix without an SDK update from that vendor (Adding a privacy manifest to your app or third-party SDK).

## Export compliance

`ITSAppUsesNonExemptEncryption` is an `Info.plist` Boolean that declares whether the app — including everything it links against — uses encryption beyond what's exempt from U.S. export compliance rules (standard OS-provided encryption, like TLS/HTTPS via system frameworks, is exempt) (ITSAppUsesNonExemptEncryption, https://developer.apple.com/documentation/bundleresources/information-property-list/itsappusesnonexemptencryption.md).

```xml
<key>ITSAppUsesNonExemptEncryption</key>
<false/>
```

The common case: an app that only uses HTTPS via `URLSession`/system TLS and doesn't implement or link custom/proprietary cryptography can set this to `NO` (`false`) and skip App Store Connect's export-compliance questionnaire on every upload, as well as the annual self-classification report obligation that non-exempt encryption use otherwise carries. Omitting the key entirely doesn't skip the question — App Store Connect just prompts for it on every single upload, so setting it explicitly streamlines the pipeline (ITSAppUsesNonExemptEncryption).

A real export-compliance question exists when the app implements or bundles its own cryptographic algorithms (not just consuming HTTPS), does end-to-end encryption of user content, or otherwise goes beyond calling standard OS crypto/TLS APIs — in that case `ITSAppUsesNonExemptEncryption` should be `true`, and after Apple reviews the required export documentation you typically also set `ITSEncryptionExportComplianceCode` to the code Apple issues (ITSAppUsesNonExemptEncryption).

## Metadata requirements — where submissions commonly trip up

Beyond the binary itself, treat these as review-gating, not administrative:

- **Bundle ID, version, and build string.** `CFBundleShortVersionString` (marketing version, e.g. `2.4.1`) and `CFBundleVersion` (build string) are both required and both appear in Organizer crash/field reports — get the format right (`[Major].[Minor].[Patch]`) since it's user-visible on the product page. Xcode can auto-manage the build number on upload if you use a standard distribution method or enable "Manage version and build number" (Preparing your app for distribution).
- **App icon.** Provide either a single Icon Composer file (supports Liquid Glass) or a full asset-catalog icon set; an asset catalog gets the Liquid Glass treatment applied automatically by the system (Preparing your app for distribution). Missing required icon sizes is a mechanical, avoidable rejection.
- **Launch screen.** Required and reviewed as part of app completeness — a blank or crashing launch screen reads as an incomplete app (Preparing your app for distribution; App Review Guidelines §2.1).
- **Usage description strings** (`NSLocationWhenInUseUsageDescription` and siblings) — required any time the app accesses a protected resource; a generic or missing description is both a review risk and a poor permission-prompt UX (Preparing your app for distribution).
- **Screenshots per required device class.** Must accurately represent the app's actual UI and functionality — this is the single most cited "inaccurate metadata" rejection reason in practice (§2.3.3) and is also enforced structurally: you need a screenshot set per required display size class, not just one set reused everywhere. Apple's screenshot specifications page lists the required sizes for every device (https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications); check it before planning any screenshot set. iPhone Duo adds two size classes, one per display: outer 1398 × 2034 px (portrait) and inner 2007 × 2853 px (portrait), with their landscape equivalents. As of 2026-09 App Store Connect cannot yet accept Duo uploads, so check the same page before planning a Duo screenshot set. Capture each display in the poses `apple-design`'s `adaptive-layout.md` § Checking a layout on iPhone Duo lists.
- **Description, keywords, support URL, marketing URL.** All are subject to review (§2.3.7, §2.3.9); a dead support URL or a description promising functionality the build doesn't have is a rejection, not just a UX gap.
- **Category and age rating.** Must match actual app content and functionality (§2.3.5, §2.3.6) — picking a category for discoverability rather than accuracy is a guideline violation, not just a marketing choice.
- **Content rights / third-party material.** You must have rights to everything in the app and its metadata, including any user-generated or licensed content shown in screenshots (§2.3.9, §5.2.1).
- **In-app purchase completeness.** Every IAP needs to be created in App Store Connect, tied to StoreKit integration in the binary, and include a working "Restore Purchases" path before submission — this is a chronic, avoidable rejection source (§3.1.1; iOS App Distribution and Best Practises, ch. 3). First-ever IAPs must be submitted alongside an app version; subsequent IAPs review independently once the first has cleared (iOS App Distribution and Best Practises, ch. 7).
- **Add-on platforms and extensions** (macOS/tvOS companion apps, App Clips, iMessage apps, watchOS apps) each carry their own guideline sections and, for macOS/tvOS companions, a separate build submitted under the same App ID — don't assume one universal binary covers a companion platform (iOS App Distribution and Best Practises, ch. 7).

## Speed and process levers

Apple publishes rough review-time expectations but no guarantee — the current published figure is that, on average, 90% of submissions are reviewed in less than 24 hours (App Review, https://developer.apple.com/distribute/app-review/), tighter than the book's ~2021-era 50%-in-24h/90%-in-48h framing; most of the wait still happens before "In Review" actually starts, not during active review (iOS App Distribution and Best Practises, ch. 3; ch. 7). For a genuine time-sensitive issue (critical bug, security vulnerability), an expedited review request is available through the developer contact form — reserve it for real emergencies and provide enough written justification, since Apple can and does deny requests it judges non-urgent (iOS App Distribution and Best Practises, ch. 7).
