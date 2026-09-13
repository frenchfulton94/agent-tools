> verified: 2026-08 against https://developer.apple.com/documentation/tipkit, https://developer.apple.com/tutorials/data/documentation/tipkit.json, https://developer.apple.com/tutorials/data/documentation/tipkit/highlightingappfeatureswithtipkit.json, https://developer.apple.com/tutorials/data/documentation/tipkit/tips/configurationoption/datastorelocation(_:).json, https://developer.apple.com/tutorials/data/documentation/tipkit/tips/rule.json, https://developer.apple.com/tutorials/data/documentation/tipkit/tips/configurationoption/cloudkitcontainer(_:).json
> sources: live docs

# TipKit

## What it is / when to reach for it

TipKit is Apple's framework for surfacing short, contextual callouts that "teach people about a new feature in your app, or show them ways to
accomplish a task faster." It is explicitly scoped: the docs frame tips as pointing out nonobvious features a user hasn't discovered on their own —
not as an onboarding walkthrough mechanism and not as a promotional/advertising surface. That scoping is the first adoption decision: if what you
actually need is a multi-step guided tour (sequential coach-marks that walk a first-run user through the whole UI) or in-app marketing banners,
TipKit's own design intent argues against forcing it into that role, even though `TipGroup` can sequence a small set of related tips.

Compare against the realistic alternative — a custom overlay/coach-mark view you build and own. A custom system wins when you need: strict
sequencing through many steps, custom animation/anchoring beyond popover/inline, or tip logic that must run identically on OS versions below the
17.0/14.0/1.0/10.0 floors below. TipKit wins when the underlying feature-discovery problem is small (a handful of independent, rules-gated call-outs)
and you want the eligibility/frequency/persistence bookkeeping — donation counting, max-display-count, "don't show again after dismissal" — handled
by a system framework instead of hand-rolled `UserDefaults` flags. In practice, most apps end up wanting exactly the kind of thing TipKit is built
for: sparse, rule-gated, dismissible hints tied to app state or user actions, not a full onboarding flow.

## Architecture integration

A tip is a plain value type conforming to `Tip` (SwiftUI-first, with UIKit and AppKit counterparts: `TipUIView`/`TipUIPopoverViewController` and
`TipNSView`/`TipNSPopover`). Content (`title`, `message`, `image`, `actions`) is separated from eligibility (`rules`) and frequency (`options`) —
that separation is what makes tips something you can define near the feature they describe (a view file, a feature module) rather than centralizing
all tip text in one giant registry. `Tips.configure()` must be called once per app session — the docs' worked example calls it from the app's
`init()` — before any `TipView`/`popoverTip` renders; this is app-launch-boundary wiring, similar in spirit to other once-per-process framework
setup calls, not something safe to defer into a lazily-constructed view.

Eligibility is driven by two building blocks, both declared as static members on the tip type: `@Parameter` (tracks app/domain state — e.g. "is the
user logged in" — via a property wrapper) and `Event` (tracks repeatable user actions via `sendDonation()` calls you place at the interaction site).
Both are referenced from `rules` through the `#Rule` macro, and multiple rules on one tip **AND together** — a tip needs every rule to pass, not
just one. If a tip declares no rules at all, it is eligible to display until dismissed or until it exceeds its display-frequency threshold — a
useful default for trivial always-relevant tips, but easy to trip over accidentally (a tip you meant to gate ships ungated because the `rules`
array was left empty during a refactor).

For testability: `Tips.showAllTipsForTesting()`, `showTipsForTesting(_:)`, `hideAllTipsForTesting()`, `hideTipsForTesting(_:)`, and
`resetDatastore()` are documented, purpose-built for UI tests and local iteration — use them rather than manufacturing fake app state to satisfy
rules in a test target. Because `@Parameter`/`Event` types must be `Codable` and `Sendable`, the underlying app-state model driving a tip's rules is
naturally decoupled from view code, which keeps rule logic unit-testable independent of SwiftUI.

Datastore configuration matters architecturally the moment more than one target needs to see the same tip state: `Tips.configure([...])` accepts a
`datastoreLocation` option, and `.groupContainer(identifier:)` is the documented way to put the datastore in an App Group container — called out by
the docs specifically as "useful for shared extensions." A `cloudKitContainer` option exists separately to sync the datastore across a user's
devices via CloudKit; the docs recommend using a **separate** CloudKit container for tips (not reusing your app's main container) to avoid record
collisions.

## Privacy, entitlements, review

- No tip-specific Info.plist keys are documented on the pages fetched for this primer.
- **CloudKit sync of the tip datastore** (opt-in via `.cloudKitContainer(_:)`) requires two entitlements/capabilities per the docs: the **iCloud**
  capability (to specify a CloudKit container) and the **Background Modes** capability (so the app can receive remote notifications describing
  server-side changes). If you don't call `.cloudKitContainer(_:)`, the docs state the datastore does not sync with CloudKit by default — no
  entitlement is needed for local-only tip state.
- **App Group** usage (`.groupContainer(identifier:)`) — the fetched TipKit docs describe the option itself ("useful for shared extensions") but do
  not spell out the entitlement requirement; App Groups is a general platform capability that normally requires an entitlement on every participating
  target, so verify current entitlement setup against the live App Groups docs rather than treating this primer as the source of truth there. This
  primer did not find TipKit-specific App Review guidance beyond that; treat "only request what you use" as prudent default practice, not a quoted
  TipKit-specific policy.
- No other App Review implications were surfaced in the fetched pages — TipKit's own docs frame tips as sparse, dismissible, non-intrusive UI, which
  is the practical bar to satisfy since there's no separate documented review checklist for it.

## Availability

Per the framework overview page: iOS 17.0+, iPadOS 17.0+, Mac Catalyst 17.0+, macOS 14.0+, tvOS 16.0+, visionOS 1.0+, watchOS 10.0+. Note tvOS's
floor (16.0+) predates the rest of the family (17.0/14.0) — and tvOS also has a materially different default datastore mechanism (see below), so
don't assume tvOS behavior mirrors iOS/macOS just because the framework is nominally available there. Verify individual API availability (e.g. newer
`ConfigurationOption` cases) against the live per-symbol doc page before relying on it, rather than assuming everything in the framework shares the
framework-level floor.

## Classic pitfalls

- **Leaving `rules` empty by accident.** A tip with no rules is eligible immediately and stays eligible until dismissed or frequency-capped — fine
  for a genuinely always-relevant tip, a silent bug for one that was supposed to be gated on state that got refactored away.
- **Forgetting rules AND together, not OR.** A tip with two rules meant as "show if either condition holds" will never fire if written naively,
  because TipKit requires every declared rule to pass simultaneously; model "OR" logic inside a single parameter/event's rule closure instead of as
  separate rule entries.
- **Assuming a dismissed tip can reappear.** Per the docs: "A tip dismissed by the user won't appear again until its datastore is reset." Treating
  dismissal as "hidden until conditions change again" (rather than "gone until `resetDatastore()`") leads to bug reports like "the tip never comes
  back even though the user re-entered the flow" — that's correct, documented behavior, not a bug.
- **Multi-target/extension apps not sharing the datastore.** By default TipKit's datastore is per-target local storage; a widget, share extension, or
  watch companion that needs to see the same tip eligibility/dismissal state as the main app must be explicitly pointed at a shared App Group
  container via `.datastoreLocation(.groupContainer(identifier:))` — and every target involved needs the datastore configured with the *same*
  identifier and needs the App Groups entitlement.
- **Reusing the main app's CloudKit container for tip sync.** The docs specifically recommend a separate container from your app's primary CloudKit
  container to avoid record collisions between app data and TipKit's own records.
- **tvOS datastore assumptions.** tvOS is documented as using `URL.cachesDirectory` plus `UserDefaults` by default (unlike the Application Support
  directory used elsewhere) — code or expectations ported from iOS about persistence durability/location can be wrong on tvOS specifically.
- **Treating TipKit as an onboarding-flow engine.** The framework's own guidance frames tips as sparse, feature-discovery nudges, not a sequential
  tutorial mechanism — `TipGroup` sequences a small set of related tips one at a time, but reaching for TipKit to build a multi-screen first-run
  walkthrough fights the framework's design intent rather than working with it.
- **Calling `Tips.configure()` more than once, or too late.** The documented pattern is exactly one call, early (app `init()`), before any tip view
  renders; deferring it into a lazily-created view or calling it repeatedly isn't the documented/tested path.

## Current docs

- https://developer.apple.com/documentation/tipkit
- https://developer.apple.com/documentation/tipkit/highlightingappfeatureswithtipkit
- https://developer.apple.com/documentation/tipkit/tip
- https://developer.apple.com/documentation/tipkit/tipgroup
- https://developer.apple.com/documentation/tipkit/tips/configure(_:)
- https://developer.apple.com/documentation/tipkit/tips/configurationoption/datastorelocation(_:)
- https://developer.apple.com/documentation/tipkit/tips/configurationoption/cloudkitcontainer(_:)
- https://developer.apple.com/documentation/tipkit/tips/configurationoption/displayfrequency(_:)
- https://developer.apple.com/documentation/tipkit/tipview
- https://developer.apple.com/documentation/swiftui/view/popovertip(_:arrowedge:action:)
- https://developer.apple.com/documentation/tipkit/tips/rule
- https://developer.apple.com/documentation/tipkit/tips/parameter
- https://developer.apple.com/documentation/tipkit/tips/event
- https://developer.apple.com/documentation/tipkit/tipviewstyle
- https://developer.apple.com/documentation/tipkit/minitipviewstyle
- https://developer.apple.com/documentation/tipkit/tips/showalltipsfortesting()
- https://developer.apple.com/documentation/tipkit/tips/resetdatastore()
