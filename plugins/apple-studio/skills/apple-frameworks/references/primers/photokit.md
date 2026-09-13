> verified: 2026-09 against https://developer.apple.com/documentation/photokit.md, https://developer.apple.com/tutorials/data/documentation/photokit.json, https://developer.apple.com/tutorials/data/documentation/photokit/delivering-an-enhanced-privacy-experience-in-your-photos-app.json, https://developer.apple.com/tutorials/data/documentation/photosui.json, https://developer.apple.com/tutorials/data/documentation/photosui/phpickerviewcontroller.json
> sources: live docs

# PhotoKit

## What it is / when to reach for it

PhotoKit (per the docs: "work with image and video assets that the Photos app manages, including those from iCloud Photos and Live Photos")
is Apple's framework for browsing, fetching, caching, and modifying the user's actual photo library — albums, Moments, Shared Albums,
Live Photos, and both on-device and iCloud-hosted assets. The umbrella page groups two frameworks together: **Photos** (the data/model
layer — `PHAsset`, `PHAssetCollection`, fetch requests, change requests) and **PhotosUI** (picker UI, Live Photo display, photo-editing
and Photos-app extensions).

The obvious alternative to rule out first is **`PHPickerViewController`** (PhotosUI, iOS 14+) or its SwiftUI counterpart `PhotosPicker`.
Per the fetched picker docs, the picker is a **system-rendered UI that runs out-of-process** on top of your app and, critically,
**does not require photo library authorization at all** — the user picks assets in a system-owned view, and your app only ever sees
what was explicitly selected. If the feature is "let the user attach/upload a few photos" (avatar, support-ticket attachment, one-off
share), reach for `PHPickerViewController`/`PhotosPicker` and stop there — no Info.plist key, no permission prompt, no App Review privacy
scrutiny, no `PHAsset` handling at all beyond what the picker itself hands back (typically a `PHPickerResult` you resolve to a
`UIImage`/`Data`/file via `NSItemProvider`, or a `PhotosPickerItem` in SwiftUI).

Reach for PhotoKit proper — the **Photos** framework with real authorization — only when the app genuinely needs to *browse or manage
the library itself*: a custom gallery/album browser, a backup/sync tool, a photo-editing extension, background monitoring for new
Live Photos, or anything that needs to enumerate assets the user hasn't explicitly hand-picked in the moment. That capability comes
with a real privacy surface (see below) that the picker exists specifically to let most apps avoid.

## Architecture integration

Photos-framework code sits at a data-access boundary similar to a persistence layer: `PHFetchResult`/`PHAsset`/`PHAssetCollection` are
Apple's model types, and `PHPhotoLibrary.shared().performChanges(_:)` is the mutation entry point (change requests, executed
asynchronously, all-or-nothing). Wrap library access behind your own repository/service protocol rather than threading `PHAsset` and
fetch-request types through domain/UI code directly — this is what makes the boundary testable, since PhotoKit itself has no
mock/in-memory story described in the fetched docs; you fake your own protocol in tests rather than driving `PHPhotoLibrary` in CI.

Two docs-stated architectural commitments to build around: (1) apps must register a **change observer** (the standard change-observer
API referenced in the privacy article) to react to library edits made elsewhere — including a user *changing their limited-library
selection* after the fact — so the data layer needs a live-update path, not just a one-shot fetch; (2) asset thumbnails/full images are
loaded and cached through a request/caching API (per the topic listing: "Loading and Caching Assets and Thumbnails") rather than
synchronously — treat image loading as async I/O with cancellation, the same as any remote-image pipeline, not a cheap in-memory read.

PhotosUI's picker (`PHPickerViewController`) is architecturally distinct: it's not subclassable and its view hierarchy is private to
the system (per the docs, apps must not alter its visibility/opacity or interaction breaks) — treat it as an opaque, presented
system component, not a customizable view you compose into.

## Privacy, entitlements, review

- **Info.plist usage-description keys, and which one depends on access level.** The docs describe two access tiers apps must pick
  between: **read/write access** (retrieving assets/collections, or updating the library) uses `NSPhotoLibraryUsageDescription`;
  **add-only access** (an app that only saves photos out, never reads the library) uses the narrower
  `NSPhotoLibraryAddUsageDescription` instead. Requesting the broader read/write key when add-only would suffice is both unnecessary
  privacy exposure and a plausible App Review friction point.
- **Limited Library is not an edge case — it's a first-class, common authorization state.** Since iOS 14, `PHAuthorizationStatus`
  includes `.limited` alongside `.notDetermined/.restricted/.denied/.authorized`, and the docs are explicit that the **deprecated**
  `authorizationStatus()`/`requestAuthorization(_:)` (no-parameter versions) are **not compatible** with limited mode — they
  incorrectly report `.authorized` even when the user actually granted only limited access. Any code still calling the deprecated,
  parameterless authorization APIs will misclassify limited-access users as fully authorized. Use `authorizationStatus(for:)` /
  `requestAuthorization(for:handler:)`.
- **`.limited` changes what the app can do, not just how much it can see**: per the docs, apps **cannot create or fetch user
  albums** while authorization is `.limited` — this is a real behavioral branch, not just a smaller data set, and UI that assumes
  "album" is always a valid concept needs a limited-mode fallback.
- **The limited-library picker UX is explicitly an App Review / UX expectation, not an optional nicety.** The docs state the system
  prompts once per app lifecycle by default to re-offer the selection picker, and instruct apps to also **offer their own in-app
  affordance** to let the user update the limited selection (via `PHPhotoLibrary.shared().presentLimitedLibraryPicker(from:)`,
  with an identifier callback available from iOS 15). Apps can suppress the automatic system re-prompt via an Info.plist key
  ("Prevent limited photos access alert"), but the docs frame that as something you do *in addition to*, not *instead of*, giving
  users their own way back into the picker.
- **Timing of the permission prompt matters to the docs, not just to general best practice**: request authorization in response to
  a direct user action, not at launch — this is stated as guidance in the privacy article, mirroring the same principle documented
  for other sensitive-data frameworks.
- **`PHPickerViewController`/`PhotosPicker` need none of the above.** Per the fetched picker docs, it runs with system-level
  permissions rather than app-level, so it requires no usage-description key and no authorization request at all — this is the
  concrete, docs-stated reason to prefer it whenever full library access isn't actually needed.

## Availability

Per the PhotoKit umbrella page: **iOS 8.0+, iPadOS 8.0+, macOS 10.11+, Mac Catalyst 13.1+, tvOS 10.0+, visionOS 1.0+, watchOS 10.0+.**
That's the combined-framework floor and is old enough to not be a binding constraint on its own. Individual capabilities sit well
above it and must be checked per-API: **limited library access** (`.limited` status, the limited-library picker) is **iOS 14+**;
`PHPickerViewController` itself is **iOS 14.0+, iPadOS 14.0+, Mac Catalyst 14.0+, macOS 13.0+, visionOS 1.0+**; the
callback-returning overload of `presentLimitedLibraryPicker(from:)` is **iOS 15.0+**. Don't assume a PhotoKit feature is available
just because the framework's own floor is old — check the specific type/method's availability annotation.

## Classic pitfalls

- **Reaching for full PhotoKit authorization when `PHPickerViewController`/`PhotosPicker` would do the whole job.** This is the
  single most consequential judgment call for this framework: full library access adds a permission prompt, an Info.plist
  requirement, ongoing App Review privacy scrutiny, and mandatory limited-mode handling — all avoidable if the actual feature is
  "user picks some photos to attach/upload," which the picker handles with zero authorization.
- **Using the deprecated, parameterless authorization APIs.** They report `.authorized` for users who only granted limited access,
  so code branching on that result will treat limited-access users as if they'd granted everything — silently over-promising
  functionality (e.g., trying to fetch or create a user album) that then fails or returns nothing.
- **Building the whole data layer as if `.authorized` is the only granted state.** `.limited` is common (it's the default outcome
  many privacy-conscious users choose) and removes album creation/fetching specifically — code that only tests against full access
  in development will hit unexpected failures against the far more common limited-access case in the field.
- **Treating the limited-library selection as static.** The docs require a change observer specifically because the user can update
  their limited selection at any time (via the system's own re-prompt or the app's in-app picker affordance); code that fetches
  once at launch and never re-observes will silently work against a stale asset set.
- **Never surfacing an in-app way to change the limited selection.** Suppressing the automatic system prompt (via the Info.plist
  "prevent alert" key) without adding your own `presentLimitedLibraryPicker` entry point strands limited-access users with no way
  to add more photos later — a real UX dead end the docs explicitly guard against by recommending both together.
- **Requesting the broader read/write usage-description/authorization for an add-only feature** (e.g., "save this generated image to
  the library") instead of the narrower add-only tier — unnecessary access, unnecessary privacy-review surface, for no functional
  gain.
- **Prompting for authorization at app launch** rather than at the moment a Photos-dependent feature is actually invoked — the docs
  call this out directly as the wrong timing, and it's the same pattern that increases denial rates and reads as suspicious across
  every sensitive-permission framework on the platform.

## Current docs

- https://developer.apple.com/documentation/photokit.md
- https://developer.apple.com/documentation/photos.md
- https://developer.apple.com/documentation/photosui.md
- https://developer.apple.com/documentation/photokit/delivering-an-enhanced-privacy-experience-in-your-photos-app.md
- https://developer.apple.com/documentation/photosui/phpickerviewcontroller.md
- https://developer.apple.com/documentation/photosui/phpickerconfiguration-swift.struct.md
- https://developer.apple.com/documentation/photokit/bringing-photos-picker-to-your-swiftui-app.md
