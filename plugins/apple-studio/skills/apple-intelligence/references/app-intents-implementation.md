> verified: 2026-09 against https://developer.apple.com/documentation/AppIntents/getting-started-with-the-app-intents-framework, https://developer.apple.com/documentation/AppIntents/app-intents, https://developer.apple.com/documentation/AppIntents/app-entities, https://developer.apple.com/documentation/AppIntents/app-enums, https://developer.apple.com/documentation/AppIntents/common-data-types, https://developer.apple.com/documentation/AppIntents/app-extension, https://developer.apple.com/documentation/Updates/AppIntents, https://developer.apple.com/documentation/AppIntents/AppIntent, https://developer.apple.com/documentation/AppIntents/app-intent-types, https://developer.apple.com/documentation/AppIntents/creating-your-first-app-intent, https://developer.apple.com/documentation/AppIntents/adding-parameters-to-an-app-intent, https://developer.apple.com/documentation/AppIntents/AppEntity, https://developer.apple.com/documentation/AppIntents/defining-app-entities-for-your-custom-data-types, https://developer.apple.com/documentation/AppIntents/entity-queries, https://developer.apple.com/documentation/AppIntents/EntityQuery, https://developer.apple.com/documentation/AppIntents/EntityStringQuery, https://developer.apple.com/documentation/AppIntents/EntityPropertyQuery, https://developer.apple.com/documentation/AppIntents/EnumerableEntityQuery, https://developer.apple.com/documentation/AppIntents/IndexedEntityQuery, https://developer.apple.com/documentation/AppIntents/AppEnum, https://developer.apple.com/documentation/AppIntents/AppIntent/perform(), https://developer.apple.com/documentation/appintents/appintent/donate()-jp6k, https://developer.apple.com/documentation/AppIntents/AppIntent/isDiscoverable, https://developer.apple.com/documentation/AppIntents/AppIntent/allowedExecutionTargets, https://developer.apple.com/documentation/AppIntents/LongRunningIntent, https://developer.apple.com/documentation/AppIntents/UndoableIntent, https://developer.apple.com/documentation/AppIntents/CancellableIntent, https://developer.apple.com/documentation/AppIntents/PredictableIntent, https://developer.apple.com/documentation/AppIntents/DynamicOptionsProvider, https://developer.apple.com/documentation/AppIntents/ParameterSummary, https://developer.apple.com/documentation/AppIntents/AppIntent/summary, https://developer.apple.com/documentation/AppIntents/IntentResult, https://developer.apple.com/documentation/AppIntents/ProvidesDialog, https://developer.apple.com/documentation/AppIntents/ReturnsValue, https://developer.apple.com/documentation/AppIntents/ShowsSnippetView, https://developer.apple.com/documentation/AppIntents/IntentParameter, https://developer.apple.com/documentation/AppIntents/EntityCollection, https://developer.apple.com/documentation/AppIntents/AppDependencyManager, https://developer.apple.com/documentation/AppIntents/AppDependency, https://developer.apple.com/documentation/AppIntents/AppIntentsExtension, https://developer.apple.com/documentation/AppIntents/AppIntentsPackage, https://developer.apple.com/documentation/AppIntents/AppIntent/requestConfirmation(conditions:actionName:dialog:), https://developer.apple.com/documentation/AppIntents/IntentChoiceOption, https://developer.apple.com/documentation/AppIntents/IntentPerson, https://developer.apple.com/documentation/AppIntents/IntentFile, https://developer.apple.com/documentation/AppIntents/IntentCurrencyAmount, https://developer.apple.com/documentation/AppIntents/adopting-app-intents-to-support-system-experiences, https://developer.apple.com/documentation/AppIntents/apple-intelligence-and-siri-ai, https://developer.apple.com/documentation/AppIntents/spotlight, https://developer.apple.com/documentation/AppIntents/making-app-entities-available-in-spotlight, https://developer.apple.com/documentation/AppIntents/app-shortcuts, https://developer.apple.com/documentation/AppIntents/AppShortcutsProvider, https://developer.apple.com/documentation/AppIntents/AppShortcut, https://developer.apple.com/documentation/AppIntents/AppShortcutPhrase, https://developer.apple.com/documentation/AppIntents/AppShortcutPhraseToken, https://developer.apple.com/documentation/AppIntents/AppShortcutPhraseToken/applicationName, https://developer.apple.com/documentation/AppIntents/NegativeAppShortcutPhrase, https://developer.apple.com/documentation/AppIntents/donations-and-discovery, https://developer.apple.com/documentation/AppIntents/donating-your-apps-data-and-actions-to-the-system, https://developer.apple.com/documentation/AppIntents/visual-presentation, https://developer.apple.com/documentation/AppIntents/displaying-static-and-interactive-snippets, https://developer.apple.com/documentation/AppIntents/verifying-your-app-intents-implementation, https://developer.apple.com/documentation/AppIntentsTesting, https://developer.apple.com/documentation/AppIntentsTesting/testing-your-app-intents-code, https://developer.apple.com/documentation/AppIntentsTesting/IntentDefinitions, https://developer.apple.com/documentation/AppIntents/AppIntentError, https://developer.apple.com/documentation/AppIntents/AppIntentError/PermissionRequired, https://developer.apple.com/documentation/AppIntents/AppIntentError/Unrecoverable, https://developer.apple.com/documentation/AppIntents/AppIntentError/UserActionRequired, https://developer.apple.com/documentation/AppIntents/AppIntentError/init(predefinedError:description:), https://developer.apple.com/documentation/AppIntents/CustomAppIntentErrorConvertible
> sources: live Apple docs (no book input — the corpus predates these frameworks)

# App Intents implementation

Scope: the Siri / Spotlight / Apple Intelligence discovery path. Adoption judgment
("should this be an intent at all") lives in
`apple-frameworks/references/primers/app-intents.md` — this file is implementation
only. Widgets/Controls/Live Activities, App schema domains, visual intelligence,
hardware interactions, and Focus are each their own live-docs child topic, deferred to
a future phase; any mention below is a pointer, not coverage.

## The shape of a well-formed intent

Merely *compiling* against `AppIntent` isn't the bar. It also needs: a `perform()` that
does the action; `title`/`description` that read as real, localized UI copy (Siri
speaks them verbatim); declared `@Parameter` properties for every input; and, once
there's more than one parameter, a `parameterSummary` — skipping it produces an intent
Shortcuts renders as a bare, unreadable list, not a build failure.

```swift
struct OrderAlbum: AppIntent {
    static var title: LocalizedStringResource { "Order Album" }
    @Parameter(title: "Album") var albumName: String

    func perform() async throws -> some IntentResult {
        return .result()   // call into existing app/service logic first
    }
    static var parameterSummary: some ParameterSummary {
        Summary("Order \(\.$albumName)")
    }
}
```

`isDiscoverable` (default `true`) gates Siri/Spotlight/Shortcuts visibility; App
Shortcuts require it `true`. `allowedExecutionTargets` restricts which process runs the
intent (`.main`, `.appIntentsExtension`, `.widgetKitExtension`) — documented at the
27.0-beta tier and confirmed present in the Xcode 27 beta SDK used to verify this file,
alongside `EntityCollection`, `IndexedEntityQuery`, and `AppIntentsTesting` below; treat
every "27.0 BETA" tag as a check-your-toolchain flag, not a guarantee — the live docs
have independently been caught describing symbols the shipped SDK lacks. Keep
`perform()` a thin adapter over logic you'd test independently; wire in app services
with `@Dependency`, registered via `AppDependencyManager.shared.add(dependency:)`.

## Parameters and results

Non-optional means required — the system resolves it before `perform()` runs; optional
means your code handles `nil`, typically by throwing `$param.needsValueError(_:)` to
pause and ask. Supported types: the obvious primitives, `Array`/`Set` of a compatible
element, framework types (`EntityCollection`, `IntentPerson`, `IntentFile`,
`IntentCurrencyAmount`, `IntentPaymentMethod`, `UnionValue()`), a few system types
(`PersonNameComponents`, `PHAsset`, `PlaceDescriptor`, `SemanticContentDescriptor`), and
your own `AppEntity`/`AppEnum` — nothing else compiles as a parameter. Restrict values
statically with an `AppEnum`, or dynamically via `DynamicOptionsProvider` passed to
`@Parameter(optionsProvider:)`. For large sets, type the property
`EntityCollection<Entity>` instead of `[Entity]` — identifiers only, resolved lazily via
`resolvedEntities()`; a plain array forces full hydration during parameter resolution.

Compose result marker protocols on `perform()`'s return type via the static
`.result(...)` factory rather than implementing `IntentResult` directly —
`ReturnsValue<T>`, `ProvidesDialog` (`IntentDialog`), `ShowsSnippetView` (a SwiftUI
view), `OpensIntent`/`ShowsSnippetIntent` — compose with `&`. `IntentDialog`'s `full` is
what's spoken with no screen present (AirPods, CarPlay); write it to stand alone.

## Add-on behaviors beyond plain `AppIntent`

- **`LongRunningIntent`** extends the ~30s background budget (macOS has none; other
  platforms do). Wrap work in `performBackgroundTask { ... }`, updating the inherited
  `ProgressReportingIntent.progress` regularly or the system ends the extension early.
- **`CancellableIntent`** gives cleanup time on cancellation via
  `withIntentCancellationHandler(operation:onCancel:)`, whose `onCancel` receives a
  reason (`.timeout`, `.userCancelled`) — see Classic Pitfalls below for a verified
  type-checking trap inside this closure.
- **`UndoableIntent`** adds `undo()`, reversing `perform()` with the same parameters —
  what offers a system Undo affordance.
- **`PredictableIntent`** supplies `predictionConfiguration` so suggestion surfaces
  describe a *predicted future* run — distinct from the parameter summary, which
  describes an actual configured one.

## AppEntity: your data, projected

Required shape: a stable `id` (prefer `UUID`/`String`/`Int`), `static let defaultQuery`,
`displayRepresentation`, and `static var typeDisplayRepresentation` — the last is easy
to forget and, unlike a missing query, **is a compile error** (confirmed by
typechecking a minimal entity without it). Properties get `@Property`
(`@ComputedProperty` for a getter, `@DeferredProperty` for something large you don't
want archived eagerly). Hard limit: **10 MB** per instance including child properties.

`Identifiable` only guarantees uniqueness *on one device*; if a Siri conversation
continues elsewhere and a locally-generated `id` won't resolve there. Adopt
`SyncableEntity` (a stable `id`, or `SyncableEntityIdentifier<Local, Stable>` when
local and stable IDs differ) to mark which form is safe cross-device.

## Queries — where most implementations actually break

An entity with no query, or the wrong query, is the most common "shipped but
invisible" cause. Minimal to most capable:

- **`EntityQuery`** — the floor: `entities(for:)` maps identifiers to entities.
- **`EntityStringQuery`** — free-text lookup, the path Siri uses from a spoken name.
- **`EntityPropertyQuery`** — matches declared properties/comparators for structured
  filtering ("trails longer than 5 miles"); use once querying beyond name/identifier.
- **`EnumerableEntityQuery`** — small, fully-enumerable sets only; unlocks an automatic
  Find action in Shortcuts. Don't use it for a large/unbounded set.
- **`IndexedEntityQuery`** — `reindexEntities(for:)`/`reindexAllEntities(...)`, called
  when Spotlight rebuilds its index for entities donated via `indexAppEntities(_:)`.

Wire the query via `static let defaultQuery = YourQuery()`. A `defaultQuery` that only
supports identifier lookup when the app needs name resolution behaves exactly like "the
query is never called": Siri has no path from a spoken phrase to the data.

## AppEnum and common data types

`AppEnum` is for a closed, static value set — never data that changes at runtime
(that's `AppEntity`; the docs are explicit the two aren't meant on one type). Base it on
`String` + `RawRepresentable`, and implement both `typeDisplayRepresentation` and
`caseDisplayRepresentations` — skipping per-case descriptions produces raw case-name
text ("crossCountrySkiing") in a prompt. For common shapes, prefer framework types over
hand-rolled equivalents so the system already knows how to render/resolve them:
`IntentFile`, `IntentPerson`, `IntentCurrencyAmount`/`IntentPaymentMethod`,
`IntentItem`/`IntentItemCollection`/`IntentItemSection` (sectioned list results).

## Parameter summaries and visual presentation

The summary is what Shortcuts renders in its editor — natural-language text with
parameter key paths as tappable placeholders, worth writing even with zero parameters.
Summaries branch on already-resolved values with a result-builder DSL
(`Switch`/`Case`/`When`/`DefaultCase`). Beyond the summary, `perform()` can return a
**snippet**: a SwiftUI view via `ShowsSnippetView`, or a full separate `SnippetIntent`
(via `ShowsSnippetIntent`) when it needs its own buttons triggering further intents. A
`SnippetIntent` is re-created and re-run on every content change — keep its `perform()`
cheap and side-effect-free, pulling state from a shared `@Dependency` rather than
parameters. `requestConfirmation(conditions:actionName:dialog:snippetIntent:)` chains a
confirmation snippet mid-`perform()` and throws on cancel — that's the control-flow
signal; whether the result is spoken, shown as a card, or both is the system's call.

## AppShortcutsProvider and App Shortcuts

An App Shortcut packages an intent with phrases, a title, and an icon, surfaced with no
registration step. Implement `AppShortcutsProvider` and build `AppShortcut` values:

```swift
struct StartHike: AppIntent {
    static let title: LocalizedStringResource = "Start Hike"
    func perform() async throws -> some IntentResult { .result() }
}

struct MyShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: StartHike(),
            phrases: ["Start a hike with \(.applicationName)"],
            shortTitle: "Start Hike",
            systemImageName: "figure.hiking"
        )
    }
}
```

`\(.applicationName)` is `AppShortcutPhraseToken.applicationName`, interpolated because
`AppShortcutPhrase` conforms to `ExpressibleByStringInterpolation` — verified compiling
against the current SDK. **Include it in every phrase**, but as a
convention rather than a verified hard rule: no fetched page states it as a
requirement, `AppShortcutPhraseToken`'s own abstract uses permissive wording
("Dynamic values you can include"), and every documented example nonetheless has
one. Treat a phrase without an app token as untested ground, not as a build error
waiting to happen. The wrapped intent must have
`isDiscoverable == true`; the primer covers the ML-training data-disclosure that comes
with shipping any App Shortcut. Shortcuts appear, with no registration, in the
Shortcuts app's Action Library, Spotlight suggestions as phrases are typed, Siri
Suggestions, and the Action button; `SiriTipView`/`ShortcutsLink` surface them from your
own UI too, but aren't required for the above.

## Donations, Spotlight, and discovery: why nobody can find your intent

A correct intent with nothing telling the system it matters is the common
"shipped but invisible" outcome. Three signals, and shipping only one is the usual gap:

1. **Donate the intent** after a *direct, in-app* interaction (`donate()`, or
   `IntentDonationManager`). Never donate one Siri/Shortcuts itself triggered — it
   double-counts and skews predictions.
2. **Donate entities to Spotlight**, independent of any intent: conform to
   `IndexedEntity` and either call `CSSearchableIndex(name:
   "YourIndex").indexAppEntities(entities)` directly (named index, not default, outside
   prototyping), or `attributes.associateAppEntity(entity, priority:)` on existing
   `CSSearchableItem` code. Route wrapped properties in via `indexingKey:`/
   `customIndexingKey:` (wins over the same key in `attributeSet`), and pair every
   indexed entity with an `OpenIntent` so a tapped result navigates in-app.
3. **Attach onscreen entities** to visible views via SwiftUI's `.appEntityIdentifier(_:)`
   — what resolves "play *this* song" to a specific entity instead of requiring it
   spelled out.

## Apple Intelligence and Siri: how the pieces connect

Apple Intelligence/Siri AI consume exactly the `AppIntent`/`AppEntity`/`AppEnum`
surface above — there's no separate "turn on Apple Intelligence" API. Three
multipliers matter beyond basic conformance: an **app schema** (deferred here) tells
the model what an intent/entity structurally *means*; **`Transferable`** conformance
(`FileRepresentation`/`DataRepresentation`/`ValueRepresentation`, the last via
`IntentValueRepresentation` for file-less types like a `PlaceDescriptor`) lets a
cross-app Shortcut or Siri request hand your entity to another app; onscreen
annotation (above) resolves pronouns. None of this overlaps Foundation Models directly
— `perform()` can call a `LanguageModelSession` (`foundation-models-sessions.md`) to
generate a response, but that's your code's choice, not something App Intents wires up.

## The App Intents extension target, and errors

Add an **App Intents extension** (`AppIntentsExtension`) when intents must run without
the host app foregrounded. Share intent/entity code between app, extension, and any
framework with an `AppIntentsPackage` conformance per module; an app-level package
declares `includedPackages` to pull in a framework's package without duplication.
`allowedExecutionTargets` on an individual intent pins *which* linked target runs it —
set it explicitly for anything with a write side effect a read-only widget extension
shouldn't perform.

For errors, throw one of three shapes, in order of control: **predefined** —
`AppIntentError.PermissionRequired`/`.UserActionRequired`/`.Unrecoverable`, cases the
system already knows how to react to; **wrapped** — any
`CustomLocalizedStringResourceConvertible` error wraps automatically (the recommended
default); or **fully custom** — conform to `CustomAppIntentErrorConvertible` and supply
`appIntentError` yourself (a type conforming to both uses only this). `GenerationError`
is a Foundation Models type, not an App Intents one — don't reach for it here.

## Testing: what AppIntentsTesting can and can't tell you

`AppIntentsTesting` runs real intents out-of-process the way Siri/Shortcuts do, so it
belongs in a **UI Testing target**, not a unit-test target. Everything is looked up by
string name through one `IntentDefinitions` instance — no importing app-concrete types:

```swift
let definitions = IntentDefinitions(bundleIdentifier: "com.example.my-app")
let result = try await definitions.intents["OpenFavorites"].makeIntent().run()
```

Entity/enum results use `@dynamicMemberLookup`. Beyond running an intent, it drives:
entity search (`entities(matching:)`), enum construction (`makeCase(_:)`), cross-intent
entity chaining, `Transferable` round-tripping (`exported(as:)` → `resolved(from:)`),
Spotlight queries (`spotlightQuery(_:)`), and onscreen annotations
(`viewAnnotations()`); use `#if DEBUG`-only intents with `isDiscoverable = false` for
state setup. What it can't tell you: it confirms `perform()`'s return value, not that a
summary *reads* naturally or that Siri maps varied phrasing to the right intent —
those still need a manual Shortcuts-app pass and end-to-end Siri testing with filler
words and a voice-only pass. Cumulative gates, not alternatives.

## Classic pitfalls

- **Intent never appears anywhere.** Check in order: `isDiscoverable` flipped false; no
  `AppShortcutsProvider` entry; zero donations.
- **Query "never gets called."** Usually it *is* called, just the wrong one for the
  input shape (identifier vs. name vs. property filter — see Queries above).
- **Phrases that don't match.** Missing an app-identifying token, or phrasing nobody
  would say — test with filler words and reordering, not the literal string.
- **Summary/phrasing fine in code, wrong in Shortcuts/Siri.** Only a real Shortcuts-app
  or end-to-end Siri pass catches this; no unit test substitutes.
- **`AppEntity` compiles but isn't reachable.** Missing `typeDisplayRepresentation` is a
  compile error; an identifier-only `defaultQuery` is not, and just makes the entity
  unfindable by name. **`.result(...)` fails to type-check** two closures deep (e.g.
  inside `withIntentCancellationHandler`) — spell it `IntentResultContainer.result(...)`.
- **Donating intents Siri/Shortcuts itself triggered** distorts future predictions.

## Deferred to a future phase (pointers only)

Widgets/Live Activities/Controls (see the `widgetkit`/`activitykit` primers meanwhile),
App schema domains (the `@AppIntent(schema:)`/`@AppEntity(schema:)` macro surface),
visual intelligence (`IntentValueQuery` against `SemanticContentDescriptor`), hardware
interactions/Action button, and Focus — each its own child page under `AppIntents` in
the live docs.
