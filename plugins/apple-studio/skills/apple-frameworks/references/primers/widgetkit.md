> verified: 2026-08 against https://developer.apple.com/documentation/widgetkit, https://developer.apple.com/tutorials/data/documentation/widgetkit.json, https://developer.apple.com/tutorials/data/documentation/widgetkit/developing-a-widgetkit-strategy.json, https://developer.apple.com/tutorials/data/documentation/widgetkit/creating-a-widget-extension.json, https://developer.apple.com/tutorials/data/documentation/widgetkit/timelineprovider.json, https://developer.apple.com/tutorials/data/documentation/widgetkit/previewing-widgets-and-live-activities-in-xcode.json, https://developer.apple.com/tutorials/data/documentation/widgetkit/debugging-widgets.json, https://developer.apple.com/tutorials/data/documentation/widgetkit/widgetfamily.json, https://developer.apple.com/tutorials/data/documentation/swiftui/widgetbundle.json
> sources: live docs

# WidgetKit

## What it is / when to reach for it

WidgetKit is Apple's framework for putting glanceable, personally relevant app content outside the app itself. Per the framework overview, that spans Home Screen and Lock Screen widgets, Today View (iOS/iPadOS), desktop/Notification Center (macOS), Smart Stacks, 3D placements on visionOS, and — via companion frameworks layered on the same rendering surface — watch complications and Control Center controls. The docs frame this as one ecosystem, not a single surface: the recommended path is to build one widget and extend it to more sizes and contexts over time, not to design each surface as a separate project.

Reach for it when the app has content that's useful to see *without opening the app*, and that changes on a knowable, boundable schedule — scores, balances, next event, delivery status, a stock's last price. The strategy doc's own pre-development checklist is worth adopting wholesale before writing code: which platforms the widget needs to reach, which sizes/appearances are required on each, what technology drives updates (timeline vs. push), whether interactivity or configuration is needed, and what the Smart Stack/battery/privacy constraints are for the content in question.

The docs frame the underlying design contract as "glanceable": small, focused interfaces; energy-efficient updates (which is why the update model is a budgeted timeline rather than free-running refresh); and built-in support for personalization (user configuration and arrangement). A feature that can't be reduced to that contract — glanceable, cheap to keep current, meaningful even out of context — is usually a sign it belongs in the app proper, not in a widget.

Do not reach for it as a substitute for:

- **A full in-app dashboard.** Widgets are deliberately small, "focused" surfaces — the docs explicitly steer `systemSmall` toward "only the most critical data, such as a single image or simple gauge," with `systemLarge`/`systemExtraLarge` only stretching to "more-complex graphs and small blocks of text." If the content needs real interaction, filtering, search, or drill-down, that belongs in the app; the widget should deep-link into it (tap-to-launch a specific scene), not replicate it.
- **Notifications.** WidgetKit is a pull/scheduled model (timelines), not a push-alert model. If the requirement is "notify the user the instant X happens," that's UserNotifications (or ActivityKit for an ongoing session), not a widget refresh — timeline updates are budgeted and are not guaranteed to land at a precise moment.
- **Live Activities.** WidgetKit renders Live Activities' UI, but the content model is different: Live Activities are driven by ActivityKit plus ActivityKit push, explicitly *do not* use `TimelineProvider`/timelines, and — per the strategy doc's constraints table — lose network and location access that ordinary widgets and complications retain. Treat WidgetKit here as the rendering surface only; the activity lifecycle, updates, and entitlements are ActivityKit's concern. See the companion ActivityKit primer for that side of the boundary.

## Architecture integration

A widget lives in a **separate widget extension target**, added via Xcode's Widget Extension template, and it runs as its own process, independent of the host app. Several consequences follow directly from that:

- **The extension can't just call into app code and expect shared in-memory state.** Data has to be handed across the process boundary — the strategy doc's guidance is to "store shared data in app group containers accessible to both the app and widget extension." Plan the App Group and the shared data format (files, a shared SQLite/Core Data store, `UserDefaults(suiteName:)`) as part of the widget design, not as an afterthought bolted on when the first "why is my widget showing stale/empty data" bug shows up.
- **The widget won't appear until the app has been launched once after install** — the docs are explicit: "a person must launch the app that contains the widget at least once after the app is installed." Any onboarding flow that promises "add our widget" before first launch needs to account for that ordering.
- **A single extension can host multiple widget types**, and an app can host multiple extensions. The documented reason to split into more than one extension is permission scoping, not code organization: "if some of your widgets use location information and others don't, keep the widgets that use location information in a separate extension," so the system only prompts for location authorization on the extension that actually needs it.
- The generated extension entry point is a `@main` struct conforming to `Widget`, with a `body` built from a configuration type (e.g. `StaticConfiguration`) naming the widget's kind, its provider, and its content closure. To expose more than one widget from a single extension, apply `@main` to a struct conforming to `WidgetBundle` instead — documented as "a container used to expose multiple widgets from a single widget extension."

The **timeline provider** is the core architectural seam. It conforms to `TimelineProvider`, and WidgetKit drives it through three entry points described in the docs:

- `placeholder(in:)` — a placeholder entry shown before real content is available.
- `getSnapshot(in:completion:)` — a single-entry, fast-turnaround response used for the widget gallery (`context.isPreview` is `true` there); the docs say to fall back to sample data if real data isn't readily available rather than blocking on a fetch.
- `getTimeline(in:completion:)` — the real array of dated `TimelineEntry` values plus a reload policy (`.atEnd`, `.after(date)`, or `.never`); this path is allowed to do asynchronous work before calling the completion handler.

Design the provider so `getSnapshot` can answer near-instantly (the gallery is time-sensitive and user-facing), while `getTimeline` owns the actual data-fetch/compute latency.

WidgetKit is deliberately not a monolith — the strategy doc names the companion frameworks a real integration typically pulls in, and each is a separate architectural decision:

- **SwiftUI** for all widget UI (there is no other supported UI layer for widget content).
- **AppIntents** for three distinct things: user-facing configuration (letting someone pick which stock or which tracking number a widget shows), interactivity (buttons/toggles that act without launching the app), and Smart Stack relevance signaling.
- **ActivityKit** specifically for Live Activities — a different content/update model layered on the same rendering surface, as noted above.
- **RelevanceKit** for widget suggestions and improving a widget's Smart Stack ranking.

Treat each of those as an opt-in layer: a first widget needs only SwiftUI and a `TimelineProvider`; configuration, interactivity, and Smart Stack tuning are each separate scopes of work with their own framework surface, not bundled in by default.

Testability leans on Xcode previews (`#Preview` macros that supply timeline entries and content states, letting you "click through timeline updates and content changes" without waiting for real reload triggers) plus running the widget-extension scheme directly, with environment variables like `_XCWidgetFamily`/`_XCWidgetKind`/`_XCWidgetDefaultView` for macOS/simulator debugging. Because the extension is a separate process and separate scheme, iterating on it does not require rebuilding or relaunching the host app each time.

## Privacy, entitlements, review

- **App Groups**: shared-container data access between app and extension is an App Group entitlement, configured on both targets — required as soon as the widget needs anything the timeline provider can't compute standalone.
- **Location/network scoping**: split location-using widgets into their own extension so location authorization prompts are scoped to just that surface (see above) — this is a review/UX consideration as much as an architectural one, since over-broad permission prompts are a common source of friction and rejection.
- **Live Activities have no network or location access** per the strategy doc's constraints table — don't design a Live Activity that assumes it can fetch data live; updates must arrive via ActivityKit push.
- **Lock Screen privacy**: the docs are explicit that "Lock Screens are always visible — plan for sensitive data redaction when devices are locked or in Always On mode." Any widget that can appear on the Lock Screen needs a redacted/placeholder presentation for sensitive content; this is a design requirement, not an edge case.
- Widget appearance/rendering context varies by placement (full color vs. accented vs. vibrant across Home Screen, Lock Screen, StandBy/Night Mode, CarPlay, Mac, Watch) — treat "how does this look accented and vibrant, not just full color" as a review-readiness checklist item, not a nice-to-have.
- The strategy doc's own functional-constraints table is worth carrying into a privacy review: widgets and watch complications both retain network and location access; Live Activities have neither. If a feature needs live network calls or location while active, it cannot be built as a Live Activity — that's a hard constraint, not a configuration option.
- Apple points implementers at dedicated Human Interface Guidelines pages for widgets, complications, Live Activities, and controls as the design-review reference — treat HIG conformance (not just functional correctness) as part of what gets checked before a widget-bearing app is considered review-ready.

## Availability

Per the current WidgetKit documentation page, the framework is available on:
- iOS 14.0+
- iPadOS 14.0+
- macOS 11.0+
- Mac Catalyst 14.0+
- watchOS 9.0+
- visionOS 26.0+ (widgets only — Live Activities and Controls are explicitly *not* available on visionOS)

`WidgetFamily` cases (which sizes/shapes you can target) carry the same platform floors. Accessory families (`accessoryCircular`, `accessoryRectangular`, `accessoryInline`, `accessoryCorner`) are the watch-complication-oriented shapes; `systemSmall`/`systemMedium`/`systemLarge`/`systemExtraLarge`/`systemExtraLargePortrait` are the Home Screen–style shapes. Confirm the specific family's minimum OS against the live `WidgetFamily` doc before committing to it, since floors are tracked per-case, not just at the framework level.

Note the asymmetry on visionOS: the framework is listed at 26.0+ there, but only for widgets — Live Activities and Controls are called out as unavailable on that platform. Don't assume feature parity across platforms just because the framework itself reports a floor for each.

Practical reading for planning: the iOS/iPadOS/macOS floors (14.0/14.0/11.0) are old enough that they are rarely the binding constraint for a new app targeting current-generation OS support. The floor worth actually checking per feature is watchOS 9.0+ for complications work, and the visionOS 26.0+ widgets-only floor if targeting that platform — both are recent enough to matter for a deployment-target decision in a way the iOS/macOS numbers no longer do.

## Classic pitfalls

- **Treating the timeline reload budget as unlimited.** WidgetKit enforces a daily refresh-request budget per widget based on foreground/background state and how often the widget is actually on screen — and critically, *the docs warn this budget is not enforced while debugging in Xcode*, so a provider that looks fine during development can silently stop refreshing in the field. Test outside the debugger before trusting refresh behavior.
- **Picking `.atEnd` by default and letting timelines run dry.** If the last entry's date passes and nothing has scheduled a refresh, the widget freezes on stale data until the next system-granted opportunity. Match the reload policy to when the underlying data actually changes (`.after(date)` for known next-change times like market open/close or a flight landing; `.never` + explicit `WidgetCenter.reloadTimelines(ofKind:)` for state that only your app knows has changed, e.g. a logout).
- **Slow or data-dependent `getSnapshot`.** The gallery preview path needs a fast answer and is expected to fall back to sample/placeholder data when real data isn't readily available (`context.isPreview`). A provider that blocks on network in `getSnapshot` makes the widget gallery feel broken.
- **Forgetting the App Group boundary.** Because the extension is a separate process, any assumption that it can read the host app's in-memory caches, Keychain items without shared access groups, or un-shared `UserDefaults` will simply fail silently in the extension. Data has to be deliberately staged into a shared container by the app (ideally via background tasks keeping it current), not fetched live by the widget on a whim.
- **Building the Lock Screen/StandBy appearance last.** Because rendering context varies (accented, vibrant, full color, no-background on CarPlay) and Lock Screen requires redaction for sensitive content, a widget designed only against the Home Screen full-color case tends to need a late, disruptive redesign pass. Plan the rendering-context matrix and redaction states up front, as the strategy doc recommends.
- **Skipping the "small first" path.** The docs' own recommended strategy is to start with a nonconfigurable `systemSmall` widget for broad reach across iPhone, iPad, Mac, and visionOS, then layer on configuration, additional sizes, and Live Activities or watch complications depending on the app's features. Building multiple large, configurable widgets before validating the smallest surface works tends to produce rework.
- **Over-scoping one extension's permissions.** Bundling a location-using widget into the same extension as widgets that don't need location forces every widget in that extension to trigger the location prompt; split extensions by permission needs instead.
- **Designing only for full-color Home Screen.** The same content needs to hold up when rendered accented, vibrant, scaled up (StandBy/Night Mode, CarPlay), or with no background (CarPlay) — a design validated only in the default Home Screen appearance often breaks (illegible, wrong contrast, missing background) the first time it's viewed in one of these other contexts.
- **Assuming `getSnapshot` and `getTimeline` have the same performance budget.** `getSnapshot` backs the widget gallery and is expected to answer fast, using placeholder/sample data if necessary; treating it like `getTimeline` and doing a real network fetch there makes the gallery preview feel broken or slow to populate.
- **Calling `WidgetCenter.reloadTimelines(ofKind:)` too often.** The `.never` policy exists specifically so the app can trigger a reload only when it knows something changed; using it (or manual reloads generally) as a substitute for a well-chosen `.after(date)` policy burns into the same daily refresh budget and defeats the point of having a declarative reload policy at all.
- **Not distinguishing debugger-visible behavior from production behavior.** Because Xcode doesn't enforce the refresh budget while debugging, and previews use synthetic timeline entries you control, a widget can look perfectly correct through the entire development loop and still misbehave once budget enforcement is live on a real device — this is one of the few places where "it works in the simulator/preview" is not sufficient evidence of correctness.

## Current docs

Fetch these before implementing — this primer intentionally omits API shapes, method signatures, and configuration-type details that live here instead:

- https://developer.apple.com/documentation/widgetkit
- https://developer.apple.com/documentation/widgetkit/developing-a-widgetkit-strategy
- https://developer.apple.com/documentation/widgetkit/creating-a-widget-extension
- https://developer.apple.com/documentation/widgetkit/timelineprovider
- https://developer.apple.com/documentation/widgetkit/widgetfamily
- https://developer.apple.com/documentation/widgetkit/previewing-widgets-and-live-activities-in-xcode
- https://developer.apple.com/documentation/widgetkit/debugging-widgets
- https://developer.apple.com/documentation/widgetkit/widgets-and-complications-collection
- https://developer.apple.com/documentation/activitykit (Live Activities — separate primer)
