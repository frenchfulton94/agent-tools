> verified: 2026-08 against https://developer.apple.com/documentation/swiftdata.md, https://developer.apple.com/tutorials/data/documentation/swiftdata.json, https://developer.apple.com/tutorials/data/documentation/swiftdata/syncing-model-data-across-a-persons-devices.json, https://developer.apple.com/tutorials/data/documentation/CoreData/adopting-swiftdata-for-a-core-data-app.json
> sources: live docs

# SwiftData

## What it is / when to reach for it

SwiftData is Apple's declarative persistence layer: annotate a Swift class with
`@Model`, and it becomes storable, queryable, and (optionally) CloudKit-syncable,
with no separate schema file. Per the docs, it "combines Core Data's proven
persistence technology with Swift's modern concurrency features" — it is not a
new database engine, it's a Swift-macro front end over the same storage
technology Core Data uses.

Reach for it when: the app's persistence needs map cleanly onto an object graph
(entities with attributes and relationships), you want `@Query` to drive
SwiftUI views reactively, and you don't need iOS versions below 17 / macOS
below 14.

Prefer **Core Data** instead when: you need to support pre-iOS 17 deployment
targets, you rely on Core Data features SwiftData doesn't yet expose 1:1
(complex migration mapping models, certain fetch request configurations), or
the app already has a mature Core Data stack — the docs' own migration guide
frames "coexistence" (both stacks sharing one store file) as a first-class,
supported path, not just a stopgap, so a full rewrite is rarely required to
start adopting SwiftData incrementally.

Prefer **raw file/JSON persistence** (Codable + FileManager, or a flat
key-value store) instead when: the data is a small blob, a settings bag, or
doesn't benefit from relational queries/predicates — pulling in a model
container for a handful of Codable structs is overhead without payoff.

## Architecture integration

A `ModelContainer` is the app-wide persistence coordinator (schema + storage
configuration); a `ModelContext` is the unit-of-work object views and
view models mutate against. In a SwiftUI app the container is typically
attached once at the app root (`.modelContainer(for:)`) and the default
context is pulled from the environment; UIKit/AppKit and non-UI code
construct and own a `ModelContainer` explicitly.

For testability: build the `ModelContainer` with an in-memory
`ModelConfiguration` in tests/previews so each test gets an isolated store
with no disk I/O or cross-test bleed. Keep code that needs to be unit-tested
independent of `@Query` (which is a SwiftUI property wrapper tied to a live
view) — drive business logic off `ModelContext` fetches/`FetchDescriptor`
directly so it's callable outside a view hierarchy.

For multi-target apps (app + widget, app + share extension), the docs note
persistence normally lives in Application Support, but adopting the App
Groups entitlement moves the store to the shared app-group container
automatically (existing stores are migrated on adoption) — that's the
supported way for an app and its extensions to share one `ModelContainer`/store.

## Privacy, entitlements, review

- No entitlement is required for local-only SwiftData persistence — plain
  on-device storage carries no Info.plist key or App Review disclosure beyond
  whatever the data itself implies (e.g. if you separately access contacts,
  health data, etc., those frameworks' own usage-description keys apply, not
  SwiftData's).
- CloudKit sync (`ModelConfiguration(cloudKitDatabase:)` or the default
  automatic sync SwiftData enables when it detects CloudKit config) requires
  two Xcode capabilities per the docs: the **iCloud** capability (with CloudKit
  enabled and a container selected — needs an Apple Developer account with
  admin permissions) and the **Background Modes** capability with **Remote
  notifications** enabled, so SwiftData can process silent push and keep
  local data in sync. SwiftData reads `Entitlements.plist` to infer the
  CloudKit container automatically; with multiple containers, specify one
  explicitly via `ModelConfiguration`'s `cloudKitDatabase` parameter.
- CloudKit sync means user data leaves the device into the user's private
  iCloud database — worth calling out in a privacy nutrition label /
  privacy policy even though Apple doesn't gate it behind a runtime
  permission prompt the way Photos or Location are gated.
- No other App Review-specific gate is documented on these pages for
  SwiftData itself.

## Availability

Per the current documentation's platform table: iOS 17.0, iPadOS 17.0, Mac
Catalyst 17.0, macOS 14.0, tvOS 17.0, visionOS 1.0, watchOS 10.0. These are
hard floors — there is no back-deployment story for SwiftData the way there
sometimes is for other Swift-only APIs, so a pre-17/pre-14 deployment target
rules it out entirely (fall back to Core Data).

## Classic pitfalls

- **Treating CloudKit sync as a drop-in toggle.** The docs are explicit that
  CloudKit-compatible schemas have real constraints: `@Attribute(.unique)`
  cannot be enforced under CloudKit (concurrent sync can't guarantee
  uniqueness), all `@Relationship` properties must be optional (CloudKit
  doesn't process relationship changes atomically), and `DeleteRule.deny`
  isn't supported. Designing a schema first for local-only use and bolting
  on CloudKit sync later often means reworking the model, not just flipping
  a flag.
- **Forgetting CloudKit schemas are additive-only.** Once a schema is
  promoted to CloudKit production, you cannot delete model types or change
  existing attributes — only add. Schema mistakes shipped to production are
  effectively permanent; validate the schema against CloudKit Console during
  development before promoting.
- **Skipping schema initialization in DEBUG.** The documented pattern
  initializes the CloudKit schema once via `NSPersistentCloudKitContainer`
  inside `#if DEBUG`, then lets `ModelContainer` open the same store in
  production. Skipping this step is a common source of "sync silently does
  nothing" bugs — always verify record types actually appear in CloudKit
  Console.
- **Coexisting with Core Data without enabling history tracking on the Core
  Data side.** SwiftData enables persistent history tracking automatically;
  Core Data does not — it must be turned on explicitly
  (`NSPersistentHistoryTrackingKey`) for either stack to see the other's
  changes when sharing a store file.
- **Name collisions when running Core Data and SwiftData against the same
  store.** The documented coexistence pattern prefixes Core Data class names
  (`CDTrip`) to avoid clashing with the SwiftData model (`Trip`) — worth
  deciding a naming convention up front rather than after a collision.
- **Using `@Query` outside a view context and being surprised it doesn't
  work.** `@Query` is a SwiftUI property wrapper bound to a live view's
  environment `ModelContext`; anything that needs to fetch outside a view
  (services, background tasks, previews without a full view tree) needs a
  `FetchDescriptor` against an explicit `ModelContext` instead.
- **App Group adoption after the fact.** Adding the App Groups entitlement
  moves the store from Application Support to the shared container and
  SwiftData migrates the existing store automatically — but Xcode
  provisioning-profile management and App Group identifiers need to be
  updated project-wide first, or the build/signing step breaks before the
  data migration ever runs.

## Current docs

- https://developer.apple.com/documentation/swiftdata.md
- https://developer.apple.com/documentation/swiftdata/preserving-your-apps-model-data-across-launches.md
- https://developer.apple.com/documentation/swiftdata/adding-and-editing-persistent-data-in-your-app.md
- https://developer.apple.com/documentation/swiftdata/syncing-model-data-across-a-persons-devices.md
- https://developer.apple.com/documentation/coredata/adopting-swiftdata-for-a-core-data-app.md
- https://developer.apple.com/documentation/swiftdata/modelcontainer.md
- https://developer.apple.com/documentation/swiftdata/modelcontext.md
- https://developer.apple.com/documentation/swiftdata/adopting-inheritance-in-swiftdata.md
