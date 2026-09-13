> verified: 2026-08 against https://developer.apple.com/documentation/appintents.md, https://developer.apple.com/tutorials/data/documentation/appintents.json, https://developer.apple.com/tutorials/data/documentation/appintents/app-shortcuts.json, https://developer.apple.com/tutorials/data/documentation/appintents/apple-intelligence-and-siri-ai.json, https://developer.apple.com/tutorials/data/documentation/appintents/spotlight.json, https://developer.apple.com/tutorials/data/documentation/appintents/donations-and-discovery.json, https://developer.apple.com/tutorials/data/documentation/appintents/adopting-app-intents-to-support-system-experiences.json, https://developer.apple.com/tutorials/data/documentation/appintents/app-extension.json, https://developer.apple.com/tutorials/data/documentation/appintents/getting-started-with-the-app-intents-framework.json
> sources: live docs

# App Intents

> **This primer answers "should we, and what does it cost".** For *how to write
> the code* — `AppIntent`, `AppEntity` and queries, `AppShortcutsProvider`,
> Spotlight and Siri exposure, the extension target, and testing — see the
> **`apple-intelligence`** skill (`references/app-intents-implementation.md`).
> Widgets, Controls and Live Activities are not covered there; they stay with
> the `widgetkit` and `activitykit` primers.

## What it is / when to reach for it

App Intents is Apple's structured way of expressing an app's actions and data
so the system — Siri, Spotlight, the Shortcuts app, widgets/Controls/Live
Activities, the Action button, Focus, visual intelligence, and Apple
Intelligence generally — can discover, query, and invoke them. Per the docs,
you wrap actions in `AppIntent` types and data in `AppEntity`/`AppEnum` types;
"your app's code remains the source of truth," and the framework types are an
adapter layer the system understands, not a new runtime for your logic.

Reach for it when you want app functionality to be reachable *outside* the
app's own UI: voice ("Siri, do X in my app"), search (Spotlight surfacing app
content and, since the entity is typed, opening straight to it), automation
(user- or LLM-composed Shortcuts), Home Screen/Lock Screen widgets driving
real actions, or Apple Intelligence reasoning about what your app can do in a
multi-app request.

Prefer a **custom URL scheme / universal link** instead when the need is
simple "get me back into this exact screen" deep linking with no requirement
for voice, search, or automation discoverability — URL schemes are far less
code and have no system-side data-collection or schema-conformance overhead.

Prefer **not exposing functionality at all** when the action is destructive,
requires rich in-app context to be safe (a multi-step confirmation flow that
doesn't reduce to a few parameters), or when only narrow value would be
gained relative to the ongoing cost of keeping the intent's schema,
parameters, and entity resolution in sync with in-app logic as it evolves.

## Architecture integration

An `AppIntent`'s `perform()` method should be a thin adapter: parse/resolve
parameters (already-typed `AppEntity`/`AppEnum` values, not raw strings),
call into the app's existing service/business-logic layer, and translate the
result into `IntentResult`/`ProvidesDialog`/snippet output. The docs'
"Getting Started" guidance frames intents and entities as *lightweight
projections* of existing data/actions — "each intent performs a unique action
within your app" — not a place to newly implement behavior. Business logic
that both the UI and an intent need should live in a layer both can call
(a service object, a shared Swift package), so the intent doesn't become a
second, divergent implementation of the same feature.

For multi-target apps (app + widget + intents extension), the docs describe
sharing intent/entity code via a Swift package imported into every target
(`AppIntentsPackage`) rather than duplicating definitions, and note an
`AppIntentsExtension` lets intents run when the app process isn't
foregrounded — `allowedExecutionTargets` on an intent can pin it to `.main`,
`.appIntentsExtension`, `.widgetKitExtension`, or a combination.

For testability: because `perform()` is meant to be a thin call-through, most
of the logic worth unit testing should already be testable independently of
App Intents — test the underlying service layer directly. The framework does
ship a dedicated `AppIntentsTesting` module (referenced in the docs' Testing
section) for exercising intents, entities, and queries as such.

## Privacy, entitlements, review

- The docs describe no dedicated App Intents entitlement or capability for
  basic adoption — intents, entities, and App Shortcuts are picked up
  automatically once the relevant types exist in the app (or an app
  extension/shared package), with "no manual registration required" for App
  Shortcuts specifically.
- App Shortcuts carries an explicit data-collection disclosure in the docs:
  "Apple may extract anonymized App Shortcuts data such as localized phrases,
  display representation values, and the title and description of related
  intents. Machine learning models use this data when training to improve
  the App Shortcuts experience." Worth surfacing in a privacy review even
  though it's system-level ML training data, not user content.
- Donations have a documented behavioral restriction, not just a style
  suggestion: "Restrict your donations to direct interactions with your
  app's interface, and not to interactions started by Siri or the Shortcuts
  app." Donating an intent that was itself triggered by Siri/Shortcuts
  double-counts and skews the system's behavior predictions.
- Spotlight indexing (`IndexedEntity`/`CSSearchableIndex`) surfaces app
  content and entity metadata in system search — treat indexed entity data
  with the same sensitivity as anything else exposed to a system-level
  surface outside the app sandbox.
- The specific Info.plist keys and Xcode capability names for App Intents
  itself were not present on any page fetched this session — the fetched
  pages describe protocol/type adoption (`AppShortcutsProvider`,
  `AppIntentsExtension`, `AppIntentsPackage`) rather than plist entries.
  Confirm current Info.plist/capability requirements against live docs
  before implementation rather than assuming none exist.
- No App Review–specific gate beyond the general review guidelines is
  documented on the fetched pages.

## Availability

Per the framework's platform table in the current docs: iOS 16.0+, iPadOS
16.0+, Mac Catalyst 16.0+, macOS 13.0+, tvOS 16.0+, visionOS 1.0+, watchOS
9.0+. That's the framework floor — individual capabilities layered on top
(e.g. the visual-intelligence and union-value-parameter APIs shown in the
"Adopting App Intents to support system experiences" sample, which targets
iOS/iPadOS/macOS 27.0 betas) require materially newer OS versions. Don't
assume every feature under the App Intents umbrella shares the 16.0/13.0
floor — check the specific type/protocol's own availability before building
against it.

## Classic pitfalls

- **Putting real logic in `perform()`.** The docs frame intents as adapters
  over existing app code; teams that instead grow business logic inside
  `perform()` end up with a second, UI-and-voice-triggered code path that
  drifts from the in-app implementation and is awkward to unit test.
- **Assuming Siri/Shortcuts phrases work like free-text NLU.** App Shortcuts
  pair a specific intent with specific spoken phrases and preconfigured
  parameters; it's a curated shortcut, not a general voice command parser —
  design phrases and parameter defaults deliberately rather than expecting
  arbitrary phrasing to resolve correctly.
- **Donating actions triggered by Siri/Shortcuts back into the system.** The
  docs explicitly restrict donations to direct in-app interactions; doing it
  from every `perform()` call regardless of trigger source pollutes the
  prediction signal the docs describe as the entire point of donating.
- **Skipping `IndexedEntity`/Spotlight and expecting Siri/Apple Intelligence
  to find app content anyway.** The "Apple Intelligence and Siri AI" page
  is explicit that Apple Intelligence leans on Spotlight's semantic search
  to locate app content "even when described vaguely" — entities that are
  never indexed are effectively invisible to that path, not just to manual
  search.
- **Not associating on-screen content with its `AppEntity`.** Without
  `.appEntityIdentifier` (or the equivalent onscreen-context APIs) wired to
  visible views, conversational references like "this photo" have nothing
  to resolve against — this is a separate mechanism from indexing and both
  are needed for the full discovery/context story the docs describe.
- **Treating extension code sharing as an afterthought.** Defining intents
  directly in both the app and an intents/widget extension (instead of a
  shared Swift package per the documented `AppIntentsPackage` pattern) leads
  to duplicated, divergent intent definitions across targets.
- **Ignoring `allowedExecutionTargets` for state-mutating intents run from a
  widget extension.** Widget extensions and the main app are different
  processes; an intent that needs to touch main-app-only state should pin
  `.main` explicitly rather than assuming it runs there by default.

## Current docs

- https://developer.apple.com/documentation/appintents.md
- https://developer.apple.com/documentation/appintents/getting-started-with-the-app-intents-framework.md
- https://developer.apple.com/documentation/appintents/app-shortcuts.md
- https://developer.apple.com/documentation/appintents/apple-intelligence-and-siri-ai.md
- https://developer.apple.com/documentation/appintents/spotlight.md
- https://developer.apple.com/documentation/appintents/donations-and-discovery.md
- https://developer.apple.com/documentation/appintents/donating-your-apps-data-and-actions-to-the-system.md
- https://developer.apple.com/documentation/appintents/making-app-entities-available-in-spotlight.md
- https://developer.apple.com/documentation/appintents/adopting-app-intents-to-support-system-experiences.md
- https://developer.apple.com/documentation/appintents/app-extension.md
- https://developer.apple.com/documentation/appintents/app-schema-domains.md
- https://developer.apple.com/documentation/AppIntentsTesting.md
