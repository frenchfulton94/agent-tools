> verified: 2026-08 against https://developer.apple.com/documentation/activitykit.md, https://developer.apple.com/tutorials/data/documentation/activitykit.json, https://developer.apple.com/documentation/activitykit/starting-and-updating-live-activities-with-activitykit-push-notifications.md, https://developer.apple.com/tutorials/data/documentation/activitykit/starting-and-updating-live-activities-with-activitykit-push-notifications.json, https://developer.apple.com/tutorials/data/documentation/activitykit/displaying-live-data-with-live-activities.json, https://developer.apple.com/tutorials/data/documentation/activitykit/Activity.json
> sources: live docs

# ActivityKit

## What it is / when to reach for it

ActivityKit shares live, glanceable updates from your app as a "Live Activity" that the system surfaces in high-visibility, out-of-app contexts: Lock
Screen, Dynamic Island, Home Screen, the Watch Smart Stack, the Mac menu bar, and CarPlay. It's the right tool when you have a bounded, ongoing
real-world event (a delivery, a ride, a live score, a timer, a workout) whose state a user wants to track without opening the app, for a duration
measured in hours, not days.

Reach for it instead of:

- **Regular push notifications** — a notification is a one-shot interruption; it can't hold a persistent, updating, glanceable surface on the Lock
  Screen or Dynamic Island. If the value of "live" is that the user can glance at a status without unlocking or opening the app, that's Live Activity
  territory, not a notification stream.
- **An in-app-only status view** — cheaper to build, but only visible while the app is foregrounded/open. If the whole point is ambient visibility
  while the user is doing something else on the device, in-app UI can't deliver that.

Live Activities are not a general-purpose background-execution mechanism — they carry hard duration and update-budget ceilings (see Classic pitfalls
below). Don't reach for ActivityKit as a way to sneak in longer background processing; that's BackgroundTasks' job, not this framework's.

## Architecture integration

ActivityKit itself is a thin, imperative lifecycle API (`Activity.request`, `.update`, `.end`) that your main app target owns: it decides when to
start/update/end an activity and owns the server relationship for push tokens. The actual on-screen presentation — Lock Screen banner, Dynamic Island
compact/minimal/expanded regions, Smart Stack — is built as SwiftUI views wired up through WidgetKit's `ActivityConfiguration` in a Widget Extension
target. That split (ActivityKit owns lifecycle/data, WidgetKit owns presentation) is a real target boundary, not just a naming convention — this
primer stays on the ActivityKit side; see the companion WidgetKit primer for the presentation layer.

Practically: the state/networking code that decides "start/update/end" belongs in the app (or an App Intent, for background starts), while
`ActivityAttributes` and its `ContentState` act as the typed contract crossing into the extension. Keep that contract small and serializable — it's
also, byte-for-byte, the shape of your push payload.

Testability: the lifecycle calls are async/throwing, so they compose fine with normal Swift Concurrency test patterns and can be exercised behind a
thin protocol seam. The harder part to test is the extension-side rendering and the server-side push path — both live outside a unit-test loop and
need device/simulator or live APNs verification to actually confirm.

## Privacy, entitlements, review

- **Info.plist**: `NSSupportsLiveActivities` must be set to enable Live Activities at all for the app. `NSSupportsLiveActivitiesFrequentUpdates` opts
  into higher-frequency updates — but the user can override this in Settings, so check `ActivityAuthorizationInfo().frequentPushesEnabled` (and
  subscribe to `frequentPushEnablementUpdates`) rather than assuming the entitlement guarantees the behavior.
- **Push Notifications capability**: required in Xcode for push-to-start and push-to-update. You cannot register a Live Activity for push through the
  User Notifications framework — you must go through ActivityKit's own token streams (`Activity.pushTokenUpdates`,
  `Activity.pushToStartTokenUpdates`).
- **Broadcast/channel capability**: needed only if you push updates to many devices via a server-created channel ID instead of per-device tokens. Per
  the docs, this capability can be enabled only through the developer.apple.com portal — not through Xcode's capability picker.
- Because Live Activities occupy some of the most visible, ambient surfaces on the device (Lock Screen, Dynamic Island, menu bar), treat content
  correctness and freshness as a trust surface in its own right: a stale or wrong-looking Live Activity is far more visible — and more damaging to
  user trust — than a stale in-app screen nobody is currently looking at.

## Availability

Per the `Activity` class documentation: **iOS 16.1+, iPadOS 16.1+, Mac Catalyst 16.1+**. The framework overview separately describes Live Activities
as appearing on iPhone, iPad, Apple Watch (Smart Stack), and Mac (menu bar), but the Watch and Mac menu-bar surfaces are companion presentations of
the same activity, not a separate watchOS/macOS ActivityKit platform target listed in the API's own availability. The overview also explicitly states
visionOS does not support Live Activities.

Push-to-start — starting an activity from a server push rather than from the app — requires iOS/iPadOS 17.2+; on 17.1 and earlier, push can only
update or end an already-started activity. iOS/iPadOS 18+ adds further payload options (`input-push-token`, `input-push-channel`) for starting an
activity directly with token- or channel-based updates already attached. Treat each of these as its own floor to check, not something inherited
automatically from the 16.1+ framework baseline.

## Classic pitfalls

- **Assuming the 8-hour active window is a promise, not a ceiling.** The docs state a Live Activity can run active for up to 8 hours before the system
  force-ends it, removing it from the Dynamic Island immediately; it can then linger on the Lock Screen for up to 4 more hours (12 hours total) before
  removal. Design for expected, graceful termination — don't build a feature whose usefulness quietly breaks at hour 8.
- **Blowing the 4KB combined data budget.** Static plus dynamic content for a Live Activity — including what you send via ActivityKit push — "can't
  exceed a combined size of 4 KB" per the docs. Easy to hit if `ContentState` carries images, long strings, or nested data; keep it to small scalars
  and short strings, and reference larger assets by ID instead of embedding them.
- **Burning the priority-10 push budget.** `apns-priority: 10` updates count against a system update budget and get throttled if overused;
  `apns-priority: 5` updates don't count against that budget but land as lower priority. Sending everything at priority 10 is a common way to get
  updates silently throttled — mix priorities deliberately (routine updates at 5, must-land updates at 10).
- **Relying on push alone for final state.** Pushes that arrive after an activity has already ended are ignored by the system. If a last update
  absolutely needs to land, drive it from the app as well when possible, and always pass a real, final `ContentState` to `Activity.end(...)` rather
  than assuming a trailing push will clean it up.
- **Forgetting the foreground-start requirement.** Starting a new activity from the app (`Activity.request`) requires the app be in the foreground,
  unless you adopt `LiveActivityIntent` (App Intents) for a background start. Push-to-start (17.2+) is the other legitimate background-start path —
  there is no way to just call `request()` from an ordinary background task.
- **Confusing the three push identifiers.** The update token (per-activity, obtained asynchronously and can rotate over the activity's lifetime —
  invalidate old tokens server-side on rotation), the push-to-start token (obtained without ever starting an activity, via
  `Activity.pushToStartTokenUpdates`), and the channel ID (server-provisioned, broadcast-only, can update/end but cannot start an activity) are not
  interchangeable — mixing them up is a frequent server-integration bug.
- **Assuming unlimited concurrent activities.** The docs are explicit that there's a device-level limit on simultaneous active and scheduled
  activities across apps, without giving a fixed number — `Activity.request` can throw for this reason, and code that doesn't handle that error will
  fail confusingly under ordinary use (e.g. a user who already has several delivery apps running Live Activities at once).

## Current docs

- https://developer.apple.com/documentation/activitykit.md
- https://developer.apple.com/documentation/activitykit/activity.md
- https://developer.apple.com/documentation/activitykit/displaying-live-data-with-live-activities.md
- https://developer.apple.com/documentation/activitykit/starting-and-updating-live-activities-with-activitykit-push-notifications.md
- https://developer.apple.com/documentation/activitykit/creating-custom-views-for-live-activities.md
- https://developer.apple.com/documentation/activitykit/launching-your-app-from-a-live-activity.md
- https://developer.apple.com/documentation/bundleresources/information-property-list/nssupportsliveactivities.md
- https://developer.apple.com/documentation/bundleresources/information-property-list/nssupportsliveactivitiesfrequentupdates.md
