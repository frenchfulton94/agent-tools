> verified: 2026-09 against https://developer.apple.com/documentation/corelocation.md, https://developer.apple.com/tutorials/data/documentation/corelocation.json, https://developer.apple.com/tutorials/data/documentation/corelocation/requesting-authorization-to-use-location-services.json, https://developer.apple.com/tutorials/data/documentation/corelocation/configuring-your-app-to-use-location-services.json, https://developer.apple.com/tutorials/data/documentation/corelocation/handling-location-updates-in-the-background.json
> sources: live docs

# Core Location

## What it is / when to reach for it

Core Location gathers actual device position using whatever hardware is available — Wi-Fi, GPS, Bluetooth, magnetometer, barometer, and cellular —
and exposes it through `CLLocationManager` and the newer `CLLocationUpdate` async-stream API. Reach for it when the app needs the device's real,
current position: navigation, geofencing/region monitoring, proximity to iBeacons, compass heading, or filtering/sharing content by where the user
actually is.

The obvious alternatives are worth ruling out explicitly before adding this framework, because both are cheaper in privacy and engineering cost:

- **IP-based geolocation** (server-side, from the client's IP address) is good enough for coarse personalization — currency, language, "nearby
  region" content — without any permission prompt, Info.plist entry, or on-device framework at all. If the feature only needs city/country-level
  accuracy and can tolerate being wrong for VPN/travelling users, this avoids Core Location entirely.
- **Asking the user to type or pick an address** is often better UX than it sounds for one-shot flows (shipping address, "search near this city") —
  no permission friction, no battery cost, and it's precise in a way GPS in a building often isn't.

Core Location is the right call once the app needs live, on-device, hardware-sourced position — not merely "roughly where is this user."

## Architecture integration

`CLLocationManager` is the entry point apps configure and control directly; the docs also describe a newer async/await surface
(`CLLocationUpdate.liveUpdates()`) that yields an async stream of updates and folds authorization-change and denial states into the same stream
rather than a separate delegate callback. Treat location as an injected service/protocol at the boundary of your domain layer — wrap
`CLLocationManager` (or the `CLLocationUpdate` stream) behind your own thin interface so business logic that consumes "current location" doesn't
depend on the concrete Core Location types directly.

That indirection is what makes the framework testable at all: Core Location itself has no simulator/mock story described in the fetched docs beyond
the standard Xcode Simulator location-simulation menu (GPX file or canned location), which is a manual, not automated, testing aid. For unit tests,
plan to fake your own location-service protocol rather than trying to drive `CLLocationManager` itself in CI.

`CLBackgroundActivitySession` and the newer `CLServiceSession` are the pieces that matter architecturally for background work: a service session
(created while the app is foregrounded, requiring either `.whenInUse` or `.always` authorization) governs whether background delivery is even
possible, and per the docs it must be **recreated immediately on launch** if the app terminates and relaunches in the background — this is
lifecycle-boundary code, not something safe to defer to lazy initialization inside a feature module.

## Privacy, entitlements, review

This is one of the most privacy-sensitive frameworks on the platform, and the docs are correspondingly strict about setup:

- **Info.plist keys are required before any authorization request works** — the docs state requests fail immediately if the keys are missing:
  - `NSLocationWhenInUseUsageDescription` — required for either When in Use or Always authorization.
  - `NSLocationAlwaysAndWhenInUseUsageDescription` — required in addition to the above when requesting Always.
  - `NSLocationUsageDescription` — macOS-specific, general location-use description.
  - `NSLocationAlwaysUsageDescription` and the bare `NSLocationUsageDescription` (non-macOS) are marked **deprecated** in current docs.
  - `NSLocationDefaultAccuracyReduced` — optional Boolean to request reduced accuracy by default.
- **Two-tier authorization: When in Use vs Always.** When in Use is the preferred/default tier — updates only while the app is foregrounded (or
  briefly transitioning), better privacy and battery story, supported on all platforms. Always is scoped to specific valid use cases per the docs
  ("time-sensitive automatic responses to location changes," location push service extensions) and is **not available on visionOS**. The docs are
  explicit that an app can only request the Always upgrade **once** — it must be requested as a separate step after When in Use is already granted,
  not requested cold.
- **Accuracy tier is a separate axis from authorization tier.** `CLAccuracyAuthorization` governs precise vs. reduced location independent of
  When-in-Use/Always — a user can grant location access but deny precise accuracy, and the app must handle "authorized but reduced-accuracy" as a
  first-class, expected state, not an edge case.
- **Background Modes capability**: enabling background location updates requires turning on "Location updates" under Signing & Capabilities, which
  updates Info.plist automatically. For Always authorization specifically, the docs say the app **must inform the user** that location updates will
  continue arriving in the background — this is a documented transparency requirement, not just good practice.
- **Location Push Service Extension** requires its own entitlement, `com.apple.developer.location.push`, distinct from the general location
  capability — needed only for the push-triggered background location-sharing extension pattern.
- **Security expectation from the docs**: encrypt location data at rest and in transit, and provide a clear privacy policy — the docs explicitly
  call location "sensitive personal information controlled by the device owner," with access grantable/revocable per-app in system Settings at any
  time.
- **`UIRequiredDeviceCapabilities`**: only declare `"location-services"`, `"gps"`, or `"magnetometer"` here if the app genuinely cannot function
  without that hardware — the docs explicitly warn against declaring it if the app degrades gracefully (e.g., users can type a postal code instead),
  since this key affects App Store availability/install eligibility on devices lacking that hardware.
- **App Review**: the fetched docs don't spell out a specific enumerated review policy beyond what's implied by the above (accurate usage-description
  strings, requesting Always only for the documented valid use cases, informing users about background Always updates). Treat "usage description
  must honestly match what the feature does, and Always must be justified" as the safe baseline, consistent with Apple's general pattern of App
  Review scrutinizing background-capability declarations that don't match actual app behavior.

## Availability

Per the framework overview page: **iOS 2.0+, iPadOS 2.0+, macOS 10.6+, Mac Catalyst 13.0+, tvOS 9.0+, watchOS 2.0+, visionOS 1.0+.** That's the
framework floor and is old enough on every platform except visionOS to not be a binding constraint for most apps. Newer APIs sit well above that
floor — the async `CLLocationUpdate.liveUpdates()` stream, `CLServiceSession`, and `CLBackgroundActivitySession` are all modern additions layered on
top of a framework that has existed since the original iPhone SDK — so check each specific type/method's own availability annotation on its doc page
rather than assuming it inherits the framework-level 2.0/10.6 floor. `CLGeocoder`/`CLPlacemark` (coordinate-to-place-name geocoding) are marked
**deprecated** in current docs; don't build new reverse-geocoding code against them without checking the doc page for the current replacement.

## Classic pitfalls

- **Requesting Always before proving When in Use is actually used.** The docs are explicit: Always can only be requested once, as an *upgrade* after
  When in Use is already granted — asking for Always cold, or asking for it before the user has any context for why, both burns the one-shot request
  and reads as overreach to the user (and, functionally, wastes the only upgrade attempt if denied).
- **Requesting authorization at app launch instead of at the moment of use.** The docs state this plainly: request only when the user engages a part
  of the app that actually needs location, because a launch-time or context-free prompt reads as suspicious and increases denial rates. This is
  stated as a direct causal claim in the docs, not just a style preference.
- **Treating "authorized" as "precise."** Authorization status and accuracy authorization (`CLAccuracyAuthorization`) are separate; an app can be
  fully authorized for When in Use or Always and still only receive reduced-accuracy coordinates. Code that assumes any authorized state implies
  full-precision GPS-grade coordinates will silently degrade (wrong distances, wrong nearest-item results) for users who denied precise location.
- **Assuming background delivery survives app termination.** The system can terminate the app at any time to reclaim resources; the docs say
  services must be **restarted at next launch**, including recreating `CLServiceSession` immediately if the app relaunches in the background. Code
  that only sets up location services in a "normal" foreground launch path will silently stop receiving updates after any termination.
- **Starting location services while authorization is still `.notDetermined`.** The docs explicitly warn against starting services at launch when
  authorization hasn't been decided yet — do the check-then-request dance via `authorizationStatus` / the delegate callback first.
- **Declaring "Always" or background-location capabilities without the documented user-transparency step.** The docs require informing the user that
  updates continue in the background when Always is granted — skipping this is both a trust problem and a plausible App Review flag.
- **Ignoring battery cost as a design constraint, not an afterthought.** Continuous background location (especially with GPS-level accuracy) is one
  of the most battery-expensive things an app can do; picking the right accuracy/activity-type hint and using region monitoring or visits instead of
  continuous streaming when the use case allows it is a real architectural decision, not a later optimization pass.
- **Building new reverse-geocoding code against `CLGeocoder`/`CLPlacemark`.** Both are marked deprecated in current docs — check the live API page
  for the current recommended replacement before writing new code against them.

## Current docs

- https://developer.apple.com/documentation/corelocation.md
- https://developer.apple.com/documentation/corelocation/requesting-authorization-to-use-location-services.md
- https://developer.apple.com/documentation/corelocation/configuring-your-app-to-use-location-services.md
- https://developer.apple.com/documentation/corelocation/handling-location-updates-in-the-background.md
- https://developer.apple.com/documentation/corelocation/cllocationmanager.md
- https://developer.apple.com/documentation/corelocation/clauthorizationstatus.md
- https://developer.apple.com/documentation/corelocation/claccuracyauthorization.md
- https://developer.apple.com/documentation/corelocation/clservicesession-pt7n.md
- https://developer.apple.com/documentation/corelocation/clbackgroundactivitysession
- https://developer.apple.com/documentation/corelocation/cllocationupdate.md
