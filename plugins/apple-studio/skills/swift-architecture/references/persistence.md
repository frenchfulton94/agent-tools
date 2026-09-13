> verified: 2026-08 against https://developer.apple.com/documentation/swiftdata.md, https://developer.apple.com/documentation/swiftdata/modelconfiguration.md, https://developer.apple.com/documentation/swiftdata/versionedschema.md, https://developer.apple.com/documentation/swiftdata/schemamigrationplan.md, https://developer.apple.com/documentation/swiftdata/model().md, https://developer.apple.com/documentation/swiftdata/datastore.md, https://developer.apple.com/documentation/coredata.md, https://developer.apple.com/documentation/coredata/nspersistentcloudkitcontainer.md, https://developer.apple.com/documentation/coredata/mirroring-a-core-data-store-with-cloudkit.md, https://developer.apple.com/documentation/coredata/creating-a-core-data-model-for-cloudkit.md, https://developer.apple.com/documentation/cloudkit.md, https://developer.apple.com/documentation/cloudkit/cksyncengine, https://developer.apple.com/documentation/foundation/userdefaults.md, https://developer.apple.com/documentation/foundation/userdefaults/init(suitename:).md
> sources: Advanced iOS App Architecture (thin corpus coverage for this topic; distilled mainly from the live docs above, per plan)

# Persistence: SwiftData vs. Core Data vs. CloudKit sync vs. files/UserDefaults

Persistence is a technology choice, not an architecture choice. The architecture decision is
upstream of it: put a protocol-shaped seam (a repository or data-store abstraction) between your
domain/view layer and whatever writes bytes to disk or a server, and the choice of SwiftData, Core
Data, CloudKit, or a flat file becomes a swappable implementation detail rather than a load-bearing
wall. This file assumes that seam exists (see "Defer the decision" below) and gives the criteria
for picking what sits behind it.

## Decision signals, not defaults

Don't start from "what's newest" or "what everyone uses now." Start from these signals:

- **Shape of the data.** A handful of scalar preferences (theme, feature flags, last-viewed tab) is
  not the same problem as a graph of related entities (orders → line items → products, notes →
  tags → folders). The former doesn't need a database at all; the latter does.
- **Query needs.** Do you need predicates, sorting, aggregation, or relationship traversal across a
  nontrivial object count? If "load the whole thing into memory and filter with `Array` methods" is
  fine at your data volume, you don't need a database.
- **Sync requirement, and its timing.** Does the app need multi-device sync now, later, or never?
  "Never" and "now" both narrow the field; "later, probably" is the case the corpus's advice about
  deferring the database decision is written for — pick something that doesn't foreclose adding
  sync, and don't build a bespoke sync layer speculatively.
- **Team's need for migration control.** Regulated data, apps with a multi-year upgrade tail, or
  schemas that will undergo real structural surgery (splitting an entity, renaming with data
  transformation, moving relationships) want a persistence technology with a mature,
  well-documented manual-migration path, not just "it usually migrates itself."
- **Existing stack.** A codebase with years of Core Data already in it has sunk cost, tooling, and
  tests around that stack. Migrating an established Core Data store to SwiftData is a deliberate,
  scoped project — not a default upgrade to do because SwiftData is newer.
- **Greenfield and SwiftUI-only.** A new app, SwiftUI throughout, no legacy store,
  modest-to-moderate schema complexity: this is the profile SwiftData targets.
- **Tolerance for CloudKit's schema constraints.** If you want CloudKit-backed sync (via either
  SwiftData or Core Data), your domain model has to fit CloudKit's rules, which are stricter than
  either persistence framework's own rules. If your domain genuinely needs uniqueness constraints
  enforced at the store, required (non-optional) relationships, or a `Deny` delete rule as a core
  invariant, decide up front whether you can live without those things at the sync layer, or
  whether you need a different sync strategy entirely.

## SwiftData vs. Core Data

SwiftData is Apple's macro-based, Swift-native persistence framework. Apple describes it as
"combining Core Data's proven persistence technology and Swift's modern concurrency features,"
letting you add persistence "quickly, with minimal code and no external dependencies" — it's built
on the same underlying persistence engine lineage as Core Data, exposed through `@Model` types
instead of `NSManagedObject` subclasses and `.xcdatamodeld` files. It targets iOS/iPadOS 17.0+,
macOS 14.0+, Mac Catalyst 17.0+, watchOS 10.0+, tvOS 17.0+, and visionOS 1.0+. That version floor
alone rules SwiftData out for any app still supporting older OS releases.

Reach for SwiftData when:

- The app is SwiftUI-first (or SwiftUI-only) and greenfield — no existing `NSManagedObjectModel` to
  carry forward.
- The schema is a normal object graph (entities, attributes, relationships) without needing the
  most exotic Core Data features (custom migration policies, fetched properties, expression-based
  derived attributes).
- You want less boilerplate: model definitions live in the model file itself via `@Model`,
  `@Attribute`, `@Relationship`, `@Transient`, `@Unique` (uniqueness constraints on a key path), and
  `@Index` (binary or R-tree indexes on a key path), rather than a separate visual model editor
  artifact.
- You're fine being on a framework with a much shorter production track record than Core Data
  (SwiftData shipped in 2023; Core Data has been in production since 2005).

Reach for (or stay on) Core Data when:

- You already have a Core Data stack. Rewriting a working, tested persistence layer to chase a
  newer framework is not free — it's a migration project with its own risk, and the corpus's point
  about not making irreversible technology bets early cuts both ways: don't lock in early, but also
  don't unlock a working choice without a concrete reason.
- You need `NSFetchedResultsController`-grade fine control over fetch/diffing behavior in a
  non-SwiftUI (UIKit/AppKit) context, or you're building for a platform/version floor SwiftData
  doesn't reach.
- You have complex migration needs that go beyond lightweight migration — manual mapping models,
  custom migration policies, staged migrations across many schema versions — where Core Data's
  migration tooling has two decades of production mileage. SwiftData's equivalent
  (`VersionedSchema` + `SchemaMigrationPlan`) is a real, documented mechanism, but it's a
  meaningfully younger tool with far fewer edge cases worked out in the field.
- You rely on mature third-party tooling, debugging utilities, or team expertise built around Core
  Data (`.xcdatamodeld` inspection, `NSPersistentContainer` configuration patterns, established
  testing patterns) that would need to be rebuilt for SwiftData.
- The object graph needs Core Data features SwiftData doesn't expose equivalents for — fetched
  properties and expression-based derived (computed-at-the-store-level) attributes have no SwiftData
  counterpart today. Custom storage backends are no longer a Core Data-only capability: SwiftData's
  `DataStore` protocol (iOS 18+/macOS 15+) lets you plug in a non-Core-Data backend, but it's newer
  and narrower than Core Data's incremental-store machinery, and its default `DefaultStore`
  implementation is still Core Data underneath.

Be honest that SwiftData is still the newer framework, with far less production history than Core
Data — don't treat "modern" as a substitute for checking it handles your specific schema.

## CloudKit sync: on top of either, or roll your own

CloudKit sync is not a separate persistence engine you choose instead of SwiftData/Core Data — it's
a layer you add on top of one of them (or build independently of both):

- **SwiftData + CloudKit**: opt in through configuration — `ModelConfiguration`'s `cloudKitDatabase`
  (which database) and `cloudKitContainerIdentifier` (which container) — rather than a separate
  integration layer; SwiftData automates the CloudKit schema setup Core Data requires you to trigger
  manually.
- **Core Data + CloudKit**: `NSPersistentCloudKitContainer` mirrors your Core Data schema into a
  CloudKit **private database** per iCloud account, and supports sharing object graphs via `CKShare`
  (no public-database mirroring). The mature path if you're already on Core Data; promote your
  schema explicitly via `initializeCloudKitSchema(options:)` — once promoted to production, record
  types and fields are add-only (immutable).
- **Roll your own sync**: `CKSyncEngine` is Apple's current recommended primitive — a higher-level,
  delegate-based API handling background syncing, retry, and account-status monitoring for private-
  or shared-database sync (not the public database; use `CKOperation`-based APIs there, or when you
  need synchronous "sync now" behavior). Reach for this, a custom backend, or a third-party sync
  service when CloudKit's schema constraints (below) don't fit your domain.

CloudKit's off-the-shelf sync (via either SwiftData or Core Data) is enough when your domain model
can accept CloudKit's schema constraints, which are stricter than the underlying persistence
framework's own rules and apply to both frameworks identically, since both are ultimately mirroring
into the same CloudKit schema:

- **No unique constraints enforced at the store** — CloudKit does not support them, so anything your
  domain treats as unique (an email address, an external ID) has to be de-duplicated at the app
  layer, not the schema layer.
- **All relationships must be optional, and every relationship must have an inverse** — CloudKit
  doesn't guarantee an entire object graph synchronizes atomically, so a relationship can
  legitimately be nil for a period while the rest of the graph has already synced; non-optional or
  ordered relationships, and relationships without a defined inverse, aren't accepted into a
  CloudKit-backed schema.
- **The `Deny` delete rule isn't supported.** `Cascade`, `Nullify`, and `No Action` are all valid
  CloudKit-backed delete rules, but Apple's own docs flag that CloudKit may not save a large
  cascading relationship change as a single atomic operation, so a cascade across a big object graph
  can partially apply under sync — worth testing deliberately rather than assuming it behaves like a
  local, single-device cascade delete.
- **Non-optional attributes need a default value.** An attribute that is neither optional nor given
  a default isn't accepted into a CloudKit-backed schema, and Core Data's `Undefined` attribute type
  isn't supported either.
- **There's no server-side business logic.** CloudKit is a record store and sync layer, not a
  backend-as-a-service: it moves `CKRecord` data between devices and the cloud, but runs no
  validation, computed fields, or workflow logic on the server. Anything that needs to happen "in
  the cloud" beyond storing and syncing key-value records has to live in your client code, or in a
  separate backend.

When these constraints don't fit your domain — you truly need enforced uniqueness, required
relationships, guaranteed-atomic cascading deletes as an invariant, or any server-side logic beyond
storage — CloudKit (through either framework) is the wrong sync layer, and you should look at a
custom backend or a third-party sync service instead of fighting the constraint set.

## Files and UserDefaults: know the ceiling

Both are legitimate, correctly-scoped choices — the failure mode is reaching for a database when
one of these is sufficient, or (worse) reaching for one of these when the data has outgrown it.

**UserDefaults** is for small amounts of lightweight, preference-shaped data: settings, flags, small
scalars, small arrays/dictionaries of property-list-compatible types (`Int`, `Float`, `Double`,
`Bool`, `String`, `URL`, `NSNumber`, `Date`, `Data`, `Array`, `Dictionary`). Apple's own guidance is
to "prefer simple types over custom objects whenever possible" — anything else has to be archived to
`Data` before storing. It is stored on disk in an **unencrypted** format, and Apple's guidance is
explicit: "Don't store personal or sensitive information as settings... Store personal or sensitive
information in the person's Keychain instead." `UserDefaults` also posts a
`sizeLimitExceededNotification` when the defaults database exceeds its allowed maximum size — the
system doesn't publish an exact byte ceiling, but the notification's existence is itself the signal
that you've outgrown intended usage. Never use UserDefaults as a database: no querying, no
relationships, no meaningful concurrency story for structured mutation, and every read pulls from an
in-memory cache backed by a plist-shaped store not designed for growth. If you need it shared across
an app and its extensions, that's `UserDefaults(suiteName:)` with an App Group identifier, still
under the same size/shape constraints.

**File-based storage** (JSON, plist, or a custom format written into the app's container) is the
right choice for simple structured data that doesn't need querying: a single document, a small
cache of records you always load in full, an export/import format, app state you serialize wholesale
on backgrounding. It's also the right choice when "just add SwiftData/Core Data" would be pulling in
a database engine, a schema, and a migration story for something that's really just "serialize this
struct to disk and read it back." The corpus's example of this judgment call: a team designed
`DataStore` protocols and used `NSCoding` to serialize objects to disk as a stated stopgap until
they had time to bring in Core Data — and shipped to millions of users on the simple solution
without ever needing the database (Advanced iOS App Architecture, ch. 2). The lesson isn't "files
beat databases" — it's that the actual data-volume and query needs, discovered during development,
should decide the technology, not a guess made in week one.

The ceiling for both: once you need querying across many records, relationships between entities,
partial updates without rewriting a whole file, or any real concurrency control over structured
mutation, move to SwiftData or Core Data. Don't hand-roll indexing or query logic over a JSON blob
past that point.

## Migration implications

Migration difficulty compounds with how long the app lives and how much its schema changes, so this
is where "pick the modern-sounding option" can bite hardest.

- **SwiftData**: supports automatic lightweight migration for additive/simple schema changes. For
  non-trivial changes it uses `VersionedSchema` (a protocol you conform to, declaring a
  `versionIdentifier` and the `models` that make up that schema version) and `SchemaMigrationPlan`
  (a protocol declaring the ordered `schemas` and the `MigrationStage` values — lightweight or
  custom — that migrate between them). The mechanism is real and documented, but it's a
  meaningfully younger tool than Core Data's mapping-model system, with far fewer years of
  production edge cases behind it — treat it as something to prototype against your actual schema
  changes before betting a long-lived app's migration story on it, not as an automatic substitute
  for that verification.
- **Core Data**: lightweight migration handles common cases (added/removed attributes, renamed
  elements with a rename identifier) automatically; more complex changes require a mapping model
  and, for the hardest cases, custom migration policies with manual entity/attribute mapping logic.
  This tooling has two decades of production mileage and is the safer bet when you know in advance
  the schema will need real surgery (splitting an entity, restructuring relationships) rather than
  incremental additive changes.
- **CloudKit (either framework)**: schema evolution has to satisfy CloudKit's constraint set (above)
  at every version, and once a schema is promoted to CloudKit's production environment its record
  types and fields are immutable — you can only add new record types and fields, never remove or
  change existing ones. A change that's a trivial lightweight migration locally can still be blocked
  or complicated by CloudKit's add-only rule on the synced schema.
- **Files/UserDefaults**: migration is entirely manual and entirely your responsibility — there's no
  framework-provided lightweight-migration mechanism. This is a real cost, but it's a small,
  well-understood cost for small/simple data (bump a version key, write a decode-then-transform
  step) compared to the cost of getting a database migration wrong.

Net effect on the decision: if your team needs fine-grained migration control today, or you can
already foresee non-additive schema surgery, that pulls toward Core Data (mature manual migration
tooling) or toward deferring the whole decision until you know more. If your schema is simple and
likely to change only additively, SwiftData's automatic path is sufficient and its extra boilerplate
for the complex case is a cost you may never pay.

## Testability implications

Whatever you choose, keep it swappable for tests, in two layers:

- **In-memory store configuration.** Both frameworks support an in-memory-only store for fast,
  isolated tests against the real persistence engine, without touching disk. SwiftData: pass
  `isStoredInMemoryOnly: true` to `ModelConfiguration`. Core Data: set an
  `NSPersistentStoreDescription`'s store type to `NSInMemoryStoreType` (or point it at `/dev/null`
  for a SQLite-backed store that never touches disk) before assigning it to your
  `NSPersistentContainer`. Caveat: `NSInMemoryStoreType` doesn't support all SQLite-dependent
  behavior (cascading deletes among them) — prefer the `/dev/null` SQLite store when a test needs
  faithful delete-rule behavior. Give each test its own container rather than sharing one across
  parallel runs.
- **Protocol-abstracted persistence (repository pattern).** For tests of business logic that
  shouldn't care which persistence technology is behind it at all, the corpus's repository pattern
  is the connective tissue: a façade that owns CRUD against the cloud-remote-API layer, the
  persistent-store layer, and an in-memory-cache layer, exposing none of that to callers (Advanced
  iOS App Architecture, ch. 5). View models and business logic depend on the repository's protocol,
  not on SwiftData/Core Data types directly, so unit tests substitute an in-memory fake repository
  implementation with zero real persistence involved, and the persistence technology underneath the
  real implementation can change — REST to a different API, Core Data to SwiftData, sync added
  later — without touching a single call site or test that exercises business logic through the
  repository's interface (Advanced iOS App Architecture, ch. 5).

Use in-memory store configuration to test the persistence layer itself (does this fetch descriptor
/ predicate / migration actually behave correctly against the real framework). Use the
repository-protocol seam to test everything above the persistence layer without depending on any
concrete store at all. The two are complementary, not alternatives: a repository test suite still
needs *something* to run its real implementation against in integration tests, and an in-memory
store is that something.

## Defer the decision behind a protocol

None of the above needs to be settled before you start building. The corpus's core argument:
database technology choices feel like one-way doors made early in a project, before you have enough
information to make them well, and a good architecture avoids forcing that bet upfront (Advanced
iOS App Architecture, ch. 2). Concretely, that means: define the repository/data-store protocol
first, ship an intentionally simple implementation behind it (a plist file, `Codable` + file
storage, or an in-memory store) as a stated stopgap, and let real usage data — actual object counts,
actual query patterns, actual sync requirements — tell you whether you ever need to swap in
SwiftData, Core Data, or CloudKit sync at all. Sometimes, as in the corpus's own example, you don't
(Advanced iOS App Architecture, ch. 2).
