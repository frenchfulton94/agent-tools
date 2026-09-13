> verified: 2026-08 against https://github.com/swiftlang/swift-evolution/blob/main/proposals/0386-package-access-modifier.md, https://docs.swift.org/swift-book/documentation/the-swift-programming-language/accesscontrol/
> sources: Advanced iOS App Architecture (thin corpus coverage for this topic; supplemented with current Swift/SPM tooling knowledge and the live sources above)

# Module Boundaries

## Default to one target

A single app target with a well-organized folder structure is the correct starting point
for most apps, including most apps that will eventually ship to the App Store. Module
boundaries are not free: every boundary is an API surface you now have to design, version
internally, and keep in sync; every new local package is another node in the build graph,
another `Package.swift` to touch when you rename a type across a boundary, and another
place where "just make it public real quick" erodes the reason you split in the first
place. A solo developer or a two-person team on a pre-product-market-fit app pays this
cost with no offsetting benefit — nobody is stepping on anybody else's files, and the app
isn't big enough for full rebuilds to hurt.

Treat modularization as a refactor you do in response to concrete pain, not a default
architecture decision made on day one of a new project.

## Signals it's time to modularize

Reach for SPM module boundaries when one or more of these is actually true today, not
hypothetically:

- **Full-rebuild pain.** Editing a leaf file forces recompilation of a large fraction of
  the app because everything lives in one module and the compiler has to reparse the
  whole module on most changes. (Advanced iOS App Architecture, ch. 2) frames this
  directly: Swift's lack of header files means the compiler may need to re-read every
  file in a module when one file changes, so splitting into smaller modules lets the
  build system skip modules whose files didn't change. If your inner loop (edit → build →
  run) is minutes long on a modern machine, that's a build-time-driven case for module
  boundaries, independent of team size.
- **Parallel teams.** Multiple engineers or sub-teams work on different features
  concurrently and keep colliding — merge conflicts in shared files, or one team's WIP
  breaking another team's build. A module boundary turns "don't touch that file" into
  "you literally cannot depend on that internal type."
- **Enforced encapsulation.** You want it to be a compile error, not a code-review nit,
  when Feature A reaches into Feature B's view models, stores, or navigation internals.
  Folders plus `internal` don't stop this within one target — everything in one module
  can see everything else marked `internal`. Separate modules with disciplined access
  control do stop it.
- **Isolated build/test/preview.** You want to open, build, test, or SwiftUI-preview one
  feature without compiling the rest of the app — useful once app-wide build time is high
  enough that iterating on one screen inside the full app target is slow.
- **Reuse across more than one target.** The same code needs to run inside the app, a
  widget extension, a watchOS companion, a share extension, or a second app — an app
  target can't be a dependency of another target, but a package can.

If none of these are true yet, the honest move is to keep it flat and revisit later —
modularizing before any of these signals show up usually means guessing at boundaries
you'll have to redraw once real usage reveals the actual seams (see Anti-patterns below).

## How to draw the boundaries

Two axes, and most non-trivial apps end up needing both.

**By feature (vertical).** Each package is a user-facing capability — `Onboarding`,
`Search`, `Checkout` — containing its own views, view models/presenters, and
feature-local logic. Feature packages should never depend on each other directly. This
gives the clearest match to how product work and teams are organized (a feature package
maps to a user story), and it's what makes "build/test/preview one feature in isolation"
actually work, since a feature package's dependency graph stays small.

**By layer (horizontal).** Shared, feature-agnostic packages — `Networking`,
`Persistence`, `DesignSystem`, `CoreModels` — that encode capabilities every feature
needs. These packages tend to be more stable (churn less) and are natural candidates for
reuse across app + widget + watch targets, since they typically have no
UIKit/SwiftUI/feature-specific dependencies.

**The real-world shape is a DAG, not a pure hierarchy.** Feature packages depend downward
on one or more shared core packages; shared core packages don't depend on feature
packages; feature packages don't depend on each other. (Advanced iOS App Architecture,
ch. 3) shows this pattern concretely in its sample app "Koober": an iOS app target with
almost no code of its own, sitting on top of `KooberiOS` (UI code), which sits on
`KooberUIKit` (UIKit-specific, platform-bound), which sits on `KooberKit`
(platform-agnostic domain/data logic reusable on any Apple platform) — a layered stack
rather than a flat feature list, because Koober's split was driven by platform-dependency
boundaries as much as by feature boundaries. Your own split should be driven by whichever
axis actually reflects where the pain in "Signals it's time to modularize" is coming
from — build time and reuse push you toward layering; parallel teams and encapsulation
push you toward features; most apps need both simultaneously.

If a feature module seems to need another feature module, that's usually a sign the
shared logic belongs in a lower-layer core package, not that the two features should
depend on each other directly.

## Protocol boundaries between modules

When module A needs to call into behavior that "belongs" to module B (or to a lower
layer), don't make A depend on B's concrete implementation types if you can help it —
depend on a protocol (and/or a small set of public value types) instead, and inject the
concrete conformer at the composition root. This is the same discipline used inside a
single module for testability (see `state-and-di.md` for the DI mechanics), applied at
the module boundary:

- It keeps the module graph acyclic: a `Networking` package can define a
  `NetworkErrorReporting` protocol without knowing about the `Analytics` package that
  supplies the conformance, so `Analytics` depends on `Networking`, never the reverse.
- It lets you substitute a fake/mock conformer when testing a feature package in
  isolation, without linking that feature package against the real implementation module
  (and its transitive dependencies — databases, network stacks, third-party SDKs).
- It keeps the module's compiled public interface small and stable, which matters for
  incremental build time: a module whose public API is a handful of protocols changes its
  public interface far less often than one that exposes concrete types with every
  property change.

Put the protocol in whichever module owns the *consumer's* need, not necessarily the
module that implements it, when the direction of the dependency needs to be inverted
(classic dependency-inversion at the module level, not just the type level).

## Access control across module boundaries

Swift's access levels map directly onto SPM module boundaries, and getting this right is
most of what makes a module boundary actually enforce anything:

- `private` / `fileprivate` — scoped below the module; irrelevant to inter-module
  boundaries.
- `internal` (default) — visible within the declaring module only. This is what should
  hold for the vast majority of a feature package's types: view models, internal state,
  helper types.
- `public` — visible to any module that imports this one, including modules outside your
  app (if this package were ever extracted as a standalone library). Reserve `public` for
  the deliberate surface a module exposes to its consumers — protocols, DTOs/value types
  crossing the boundary, factory/entry-point types.
- `open` — `public` plus subclassing/overriding from outside the module; rarely needed in
  an app's own internal packages since you're not designing for third-party subclassing.
- `package` (Swift 5.9+, SE-0386) — visible to any module that shares the same package
  identity, but invisible outside it. The compiler's notion of "same package" is purely a
  string comparison: each module is compiled with a `-package-name <string>` flag, and a
  `package`-level declaration in one module is visible from another module only if both
  were compiled with an identical package-name string — the language itself has no
  concept of a manifest or a workspace, only that string. SwiftPM computes the string for
  you: it passes its own package identity (which it keeps unique per package) as
  `-package-name` automatically for every target declared in one `Package.swift`, so
  targets in the same package see each other's `package`-level API without any manual
  flag. This is on by default; an individual target can opt out with `packageAccess:
  false` in its target definition, which drops `-package-name` for that target and makes
  it invisible to `package`-level declarations in the rest of the package.

Why `package` matters for the modularization calculus: before SE-0386, sharing an
internal helper type between two targets in the same local package meant either making
it `public` (over-exposing it to every future external consumer of that package) or
duplicating it. `package` closes that gap — you get real encapsulation from the rest of
the app while still sharing freely among the targets that conceptually belong together,
without the discipline cost of an ever-growing `public` surface. Package access is scoped
per package identity, and in ordinary SwiftPM usage that identity tracks one
`Package.swift` manifest: SwiftPM keeps package identities unique, so a `Feature` package
and a `Core` package declared in separate `Package.swift` manifests get different
package-name strings and do not share `package`-level access with each other, even when
both are pulled into the same Xcode workspace as local package dependencies. So `package`
access only helps for splitting one package into multiple targets, not for sharing
internals across genuinely separate packages. If your app modularizes via several
*separate* local packages (one `Package.swift` per feature) rather than one package with
many targets, `package` access won't bridge between them — you're back to `public` (or
duplicating) for anything shared across package boundaries, which is itself an argument
for preferring "one package, many targets" over "many packages" when the modules are
tightly related and owned by the same team.

Since most iOS/macOS apps are not distributing their internal modules as a library —
there's no external consumer to protect against — this changes the traditional
cost-benefit of modularizing: `package` (or a "one package, many targets" layout
generally) gets you compiler-enforced module boundaries without the discipline overhead
of a `public`-everywhere API, which removes one of the classic objections to splitting a
target early.

## Anti-patterns

- **Organizational theater.** A module per type, or a module graph drawn to mirror an org
  chart rather than actual coupling. If a module has one consumer, one implementation,
  and never changes independently of its consumer, it isn't paying for itself — merge it
  back.
- **Circular dependencies between feature modules.** If `FeatureA` needs something from
  `FeatureB` and vice versa, that is a signal the boundary is wrong, not a signal to add
  a "shared" escape hatch between them or to introduce a fragile late-binding trick to
  break the cycle. Pull the shared piece down into a lower-layer package both can depend
  on, or reconsider whether these are really two features rather than one.
- **Premature modularization.** Splitting along feature or layer lines before the
  boundaries have stabilized from real product usage. Early in a feature's life the
  "right" seam between two capabilities is often still moving weekly; a module boundary
  calcifies that seam behind a compiled interface and an access-control wall, making the
  natural refactor (merge, split differently, move a type across the line) much more
  expensive than it would be inside one target. Let a feature's shape settle inside the
  main target first; extract it into its own package once it's stable and one of the
  signals above is actually firing.
- **Splitting by layer only, ignoring feature ownership** (or vice versa) once the app is
  large enough to need both — see "How to draw the boundaries" above. A single giant
  `Core` package that every feature depends on, containing unrelated logic for a dozen
  different features, recreates the "everything can see everything" problem one level
  up, just with a different module name.
