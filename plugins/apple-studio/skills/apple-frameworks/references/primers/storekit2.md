> verified: 2026-09 against https://developer.apple.com/documentation/storekit, https://developer.apple.com/documentation/storekit/in-app-purchase, https://developer.apple.com/documentation/storekit/transaction, https://developer.apple.com/documentation/appstoreservernotifications, https://developer.apple.com/documentation/storekittest, https://developer.apple.com/documentation/storekit/external-purchase
> sources: live docs

# StoreKit 2

## What it is / when to reach for it

StoreKit is Apple's framework for "In-App Purchases and interactions with the App Store." StoreKit 2 is the modern surface within it: a Swift-native, async/await API for offering content and services in-app.

The docs describe it as the framework handling secure payment processing and transaction management, and explicitly call out that it leans on Swift concurrency and SwiftUI to simplify the purchase flow.

**vs. StoreKit 1.** Apple's own documentation now files the original, delegate/callback-based API under a **Deprecated** topic group.

Treat StoreKit 1 as legacy-maintenance-only: reach for it only if you're extending an existing Objective-C/delegate-based purchase stack, not for new work. New apps and new purchase flows should default to StoreKit 2.

**vs. RevenueCat-style wrappers.** These are not a verification shortcut. StoreKit 2 already returns `Transaction`s wrapped in a `VerificationResult` with cryptographic (JWS) validation, and Apple's App Store Server Library exposes that same JWS-based verification server-side.

Reach for a third-party wrapper when you need something StoreKit 2 doesn't give you on its own — cross-platform (Android/web) entitlement sync, a hosted receipt/analytics dashboard, one SDK across storefronts — not simply to "do IAP" on iOS. On iOS alone, StoreKit 2 plus the App Store Server Library already covers purchase, verification, and entitlement state.

**Scope check before reaching for it.** The docs organize StoreKit 2 around a fixed catalog of products you configure in App Store Connect — one-time products and auto-renewable subscriptions (`Product`, `Product.SubscriptionInfo`, `SubscriptionStatus`, `SubscriptionRenewalInfo`). If your business model needs dynamic, server-driven pricing or generic SKUs — think marketplace or creator-economy pricing rather than a fixed subscription tier list — that's what the docs' Advanced Commerce API and `AdvancedCommerceProduct` surface is for, not the standard `Product`/`Transaction` path.

## Architecture integration

There is no mandatory backend to ship a basic StoreKit 2 flow. The App Store cryptographically signs transaction data as a JWS, and StoreKit validates it on-device, returning a `VerificationResult<Transaction>` your app can trust for the `.verified` case.

For production apps with real revenue at stake, mirror entitlements server-side anyway. The same `jwsRepresentation` your app receives is what the App Store Server API and App Store Server Notifications V2 send your server, and the App Store Server Library exposes `verifyAndDecodeTransaction` / `verifyAndDecodeRenewalInfo` for that path — described in the docs as the "added control and security" option.

The core lifecycle pattern is a long-lived listener, not a request/response call.

Start a `Task` iterating `Transaction.updates` early in app startup, not just after tapping "buy." That async sequence is how you learn about renewals, purchases completed outside your app, and purchases made on other devices — a listener scoped only to the purchase button misses all of that.

Use `Transaction.currentEntitlements` as your source of truth for "what is this customer entitled to right now," rather than a locally cached purchase flag that can drift from reality.

**Where it sits.** Because purchase state can change out-of-band (renewals, refunds, other devices, the App Store's own UI), don't let StoreKit types leak into view code. Wrap `Product` fetching, `purchase()` calls, and the `Transaction.updates` listener behind a single app-level entitlement/store layer that the rest of the app reads from — the listener needs to run for the app's whole lifetime, which fits a long-lived service object far better than a view-scoped one.

**Testability.** Use the **StoreKit Test** framework (`SKTestSession`) rather than only exercising the real sandbox. The docs position it explicitly for automation: full, scriptable control over transactions — renewals, Ask to Buy, refunds — usable in unit tests and continuous integration, alongside Xcode's local StoreKit configuration file for interactive testing during development.

## Privacy, entitlements, review

Standard in-app purchases don't require special Info.plist keys beyond enabling the In-App Purchase capability in your project.

The area that does carry explicit entitlement and Info.plist requirements — and correspondingly high App Review scrutiny — is **External Purchase**, Apple's regional-compliance surface for letting customers pay via an alternative processor, or by linking out of the app entirely. The docs define four distinct optional entitlements, each tied to a specific region set:

- `StoreKit External Purchase` — in-app external purchases (EU, South Korea)
- `StoreKit External Purchase Link` — external purchase links (EEA, Russia)
- `StoreKit External Custom Purchase Link Regions` — custom links (EU, Brazil, Japan)
- `Music Streaming Services EEA` — music streaming apps in the EEA

with matching Info.plist keys: `SKExternalPurchase`, `SKExternalPurchaseLink`, `SKExternalPurchaseMultiLink`, `SKExternalPurchaseCustomLinkRegions`, `SKExternalPurchaseLinkStreamingRegions`.

The docs are explicit about the review-relevant obligations here: the entitlement has to match the region(s) actually served, an in-app disclosure notice is required, and server-side reporting via the External Purchase Server API is mandatory. Get the entitlement/region mapping wrong, or skip the disclosure or reporting, and that's a review rejection vector specific to this API family — not a generic bug.

Separately, App Store Server Notifications requires configuring an HTTPS endpoint in App Store Connect, and the docs note you must opt in for production and sandbox environments **separately**. That split opt-in is a recurring source of "notifications work in prod but I get nothing in sandbox" confusion.

## Availability

Per the docs fetched this session, availability differs sharply by sub-API — do not treat "StoreKit" as one floor:

- **StoreKit** (the framework overall, including legacy surface): iOS/iPadOS 3.0+, macOS 10.7+, Mac Catalyst 13.0+, tvOS 9.0+, watchOS 6.2+, visionOS 1.0+.
- **Core StoreKit 2 transaction APIs** (`Transaction`, `VerificationResult`) — the practical floor for "StoreKit 2" as commonly meant: iOS/iPadOS 15.0+, macOS 12.0+, tvOS 15.0+, watchOS 8.0+, visionOS 1.0+.
- **StoreKitTest** (`SKTestSession`, local/CI testing): iOS/iPadOS 14.0+, macOS 11.0+, Mac Catalyst 14.0+, tvOS 14.0+, watchOS 7.4+, visionOS 1.0+; requires Xcode 12+ running on macOS 10.15+.
- **External Purchase / External Purchase Link**: iOS/iPadOS 17.4+, macOS 14.4+, tvOS 17.4+, watchOS 10.4+, visionOS 1.1+.
- **External Purchase Custom Link**: newer still — iOS/iPadOS 18.1+, macOS 15.1+, with later region-specific floors layered on top (Brazil from iOS 26.5+; Japan from iOS 26.2+, its token function from iOS 26.4+).

If a target OS floor is below iOS 15, the `Transaction`/`VerificationResult` API surface that defines "StoreKit 2" isn't available at all. That's a real go/no-go constraint for the framework choice, not a nice-to-have.

Note the granularity: External Purchase's sub-features (base link, custom link, region-specific rollouts) each shipped on their own timeline, years after core StoreKit 2. Don't assume "External Purchase" as a whole has one floor — check the specific sub-API you need.

## Classic pitfalls

- **Listener scoped to the purchase button, not the app lifecycle.** `Transaction.updates` is what catches renewals, Ask to Buy approvals, and purchases completed on other devices. If you only await it inside the "buy" action's scope, you silently miss all of that traffic.

- **Trusting on-device verification alone for high-value entitlements.** `.verified` means StoreKit's local JWS check passed. Apple's own docs describe the additional step — sending `jwsRepresentation` to your server and re-validating with the App Store Server Library — as the path for "added control and security." Skipping it is fine for low-stakes content, riskier for anything expensive.

- **Forgetting to call `finish()` on a transaction after delivering content.** The lifecycle the docs describe is: unlock the content, *then* finish the transaction. An unfinished transaction keeps reappearing in `Transaction.updates` and in `Transaction.all`, which reads as a bug even though it's working as designed.

- **Treating a locally cached purchase flag as truth instead of `Transaction.currentEntitlements`.** Entitlement state can change from outside your running app — refunds, other devices, renewals — so re-derive it from StoreKit rather than trusting a boolean set once at purchase time.

- **Only testing against the network sandbox.** Sandbox has real App Store latency and behavioral quirks, and isn't scriptable. Use `SKTestSession` or a local StoreKit configuration file for the fast day-to-day loop and CI, and treat sandbox as the final pre-release check rather than the primary test environment.

- **Guessing at External Purchase entitlements and regions.** The four entitlements map to different, non-overlapping region sets (EU/South Korea vs. EEA/Russia vs. EU/Brazil/Japan). Picking the wrong one, or omitting the mandatory disclosure notice or External Purchase Server API reporting, is an App Review failure mode specific to this feature.

- **Forgetting the separate sandbox opt-in for App Store Server Notifications.** Production and sandbox notification delivery are configured independently in App Store Connect. Assuming one implies the other leads to "notifications vanished" debugging sessions that are actually just a missing config toggle.

- **Restoring purchases as an afterthought.** Because `currentEntitlements` and `Transaction.all` are the durable source of truth, "restore purchases" should be a thin call into the same entitlement-refresh path you already use elsewhere — not a separate, bespoke code path that can drift out of sync with the main purchase flow.

- **Mixing StoreKit 1's payment-queue observer with StoreKit 2's `Transaction.updates` in the same app.** The docs now file the original API as deprecated; running both an `SKPaymentQueue` observer and a `Transaction.updates` listener side by side is a common source of the same purchase getting processed twice during a migration. Pick one processing path and migrate fully rather than layering StoreKit 2 on top of untouched StoreKit 1 code.

- **Checking External Purchase eligibility once, at build time, instead of at the moment of use.** The API exposes runtime eligibility checks (e.g. `ExternalPurchaseCustomLink.isEligible`) precisely because eligibility can depend on region, account, and configuration state that isn't fixed at compile time. Gate the flow behind the runtime check every time you present it, not just once during onboarding.

## Current docs

Fetch these when actually implementing:

- https://developer.apple.com/documentation/storekit — framework index and full topic map
- https://developer.apple.com/documentation/storekit/in-app-purchase — the StoreKit 2 API surface: `Product`, `Transaction`, purchase flow, offers, promoted purchases
- https://developer.apple.com/documentation/storekit/transaction — transaction lifecycle, `VerificationResult`, JWS/server verification detail
- https://developer.apple.com/documentation/appstoreservernotifications — server-to-server event notifications (V2), setup and opt-in requirements
- https://developer.apple.com/documentation/storekittest — `SKTestSession` and automated/CI testing of purchase flows
- https://developer.apple.com/documentation/storekit/external-purchase — External Purchase entitlements, Info.plist keys, and regional compliance requirements
