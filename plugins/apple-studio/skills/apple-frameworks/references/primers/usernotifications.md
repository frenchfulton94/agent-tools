> verified: 2026-08 against https://developer.apple.com/documentation/usernotifications, https://developer.apple.com/tutorials/data/documentation/usernotifications.json, https://developer.apple.com/tutorials/data/documentation/usernotifications/asking-permission-to-use-notifications.json, https://developer.apple.com/tutorials/data/documentation/usernotificationsui.json, https://developer.apple.com/tutorials/data/documentation/usernotifications/unauthorizationoptions.json, https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.developer.usernotifications.critical-alerts.json, https://developer.apple.com/tutorials/data/documentation/usernotifications/unnotificationserviceextension.json
> sources: live docs

# UserNotifications

## What it is / when to reach for it

UserNotifications is Apple's framework for user-facing notifications: alerts, sounds, and
badges that reach the user regardless of whether the app is running. Per the docs' own
abstract: "Push user-facing notifications to the user's device from a server, or generate
them locally from your app." It covers both locally-scheduled notifications (time interval,
calendar, or location triggers) and remote (APNs-pushed) notifications through one shared
API surface, `UNUserNotificationCenter`.

Reach for it when the message needs to survive the app not being in the foreground, needs
to appear in Notification Center / lock screen / system notification UI, needs to badge
the app icon, or needs to fire on a schedule or geofence even when the app isn't running.

Do NOT reach for it for in-app toasts, banners, or confirmation messages that only make
sense while the user is already looking at your UI. Those are cheaper, don't burn the
user's one real shot at the permission prompt, and don't invite App Review scrutiny of
your notification usage. A common mistake is defaulting to UserNotifications for transient
in-app feedback (e.g. "saved successfully") that a view-layer toast would serve better,
without ever touching authorization state.

If what you actually need is background execution or periodic refresh rather than a
user-visible alert, that's a different framework (BackgroundTasks, or a silent push) —
don't back into requesting notification permission just to get a wake-up hook.

## Architecture integration

The framework centers on `UNUserNotificationCenter` (a singleton, `.current()`), which
owns authorization state, scheduling/canceling local requests, and reading or clearing
delivered notifications. Your app supplies a `UNUserNotificationCenterDelegate` to decide
how to present notifications while the app is foregrounded and to handle the user's
response (tap, action button, text input). This delegate is the seam where notification
handling should be wired into your app's navigation/state layer, rather than left as
disconnected fire-and-forget scheduling code.

Two optional app extensions extend it further, each in its own extension target with its
own process and lifecycle:

- **Notification Service Extension** (`UNNotificationServiceExtension`, part of the base
  UserNotifications framework): launched on demand to mutate a remote notification's
  content before display — e.g. decrypting payloads or downloading an image — via
  `didReceive(_:withContentHandler:)`, under a hard time budget before the system falls
  back to original content when `serviceExtensionTimeWillExpire()` fires. Per the docs, it
  cannot modify silent notifications, or notifications that only play a sound or badge.
- **Notification Content Extension** (`UNNotificationContentExtension`, in the separate
  **UserNotificationsUI** framework): a custom view controller that replaces or
  supplements the system notification UI when the user expands a notification.

Testability: authorization, scheduling, and delegate-callback logic are all mockable
behind `UNUserNotificationCenter`'s async methods (`requestAuthorization`,
`notificationSettings()`, `add(_:)`) — keep a thin protocol wrapper around the singleton
so notification-triggering business logic can be unit tested without touching the real
notification center. The extensions run in separate processes with their own sandboxes
and are much harder to unit test; expect manual/on-device verification instead.

## Privacy, entitlements, review

- Authorization is opt-in and must be explicitly requested via
  `requestAuthorization(options:completionHandler:)` before any alert/sound/badge
  notification can be shown. The docs are explicit that the first request is the one that
  prompts the user — "Subsequent requests don't prompt them again" — so there is exactly
  one shot to get the prompt's context right.
- `UNAuthorizationOptions` includes `.alert`, `.badge`, `.sound`, `.carPlay`,
  `.criticalAlert`, `.provisional`, and `.providesAppNotificationSettings` (per the
  `UNAuthorizationOptions` docs).
- **Critical alerts** require the `com.apple.developer.usernotifications.critical-alerts`
  entitlement, which per the entitlement's own documentation requires Apple's approval
  via a request form — this is not a self-service capability toggle, so budget lead time
  for it. It lets notifications play a sound even when the device is locked, muted, or in
  a Do Not Disturb focus, and lets you set a custom sound and volume.
- **Provisional authorization** (`.provisional`) is the low-friction path: per the "Asking
  permission to use notifications" doc, it can be requested without prompting the user
  immediately — notifications are delivered quietly into Notification Center history with
  Keep / Turn Off controls, and the user only decides once they've actually seen one.
  Apple frames this as suitable for first launch, in contrast to explicit
  `.alert/.sound/.badge` authorization, which Apple recommends requesting "in context"
  (their example: after the user schedules their first task in a task-tracking app).
- Remote push requires the `aps-environment` entitlement (`com.apple.developer.aps-environment`
  on macOS) to select development vs. production APNs.
- For APNs ops — keys, environments, entitlements, delivery debugging — see the app-release
  skill's references/push-notifications.md.
- Always re-check `notificationSettings().authorizationStatus` and per-setting flags
  (e.g. `alertSetting`) before scheduling — the docs' own example guards on this because
  "people can change settings at any time."
- App Review implication: because the permission prompt is a one-shot, an app that
  requests notification authorization on cold launch with no explanatory context is a
  common friction point in review and in practice trains users to deny outright.
  Provisional authorization sidesteps this review/UX tension for apps that don't need
  up-front modal consent.

## Availability

Per the framework's own overview page, UserNotifications requires iOS 10.0+, iPadOS 10.0+,
macOS 10.14+, tvOS 10.0+, watchOS 3.0+, visionOS 1.0+, and Mac Catalyst 13.0+.

UserNotificationsUI (notification content extensions) has a later floor: iOS 10.0+,
iPadOS 10.0+, Mac Catalyst 14.0+, macOS 11.0+, visionOS 1.0+.

`UNNotificationServiceExtension` specifically lists: iOS 10.0+, iPadOS 10.0+, Mac Catalyst
13.1+, macOS 10.14+, visionOS 1.0+, watchOS 6.0+ — a higher watchOS floor than the base
framework.

The critical-alerts entitlement page lists its own availability separately: iOS 5.0+,
iPadOS 5.0+, Mac Catalyst 13.1+, macOS 10.14+, tvOS 12.0+, visionOS 1.0+, watchOS 5.0+.
Floors vary by symbol — check the specific child page for the API or entitlement you're
using rather than assuming the umbrella floor applies everywhere, and re-verify live.

## Classic pitfalls

- **Requesting authorization too early, with no context.** The docs explicitly recommend
  requesting in response to a user action that explains why notifications help, not on
  first launch. First-launch prompts get reflexively denied, and denial is effectively
  permanent friction — a "day one, unrecoverable" mistake, not one fixed quietly later.
- **Treating provisional and full authorization as the same state.** Provisional
  notifications are delivered silently into Notification Center only; a feature that
  assumes alerts, sounds, and badges will fire silently underdelivers for provisional
  users until they choose "Deliver Immediately." Branch UX on `authorizationStatus` and
  the individual `*Setting` fields, not just "authorized vs. not."
- **Assuming critical alerts are a code-only feature.** The entitlement needs Apple's
  sign-off via a separate request form before it works in production — teams that build
  the UX around critical alerts without applying early lose real calendar time waiting.
- **Conflating local and remote notification handling.** Both funnel through the same
  `UNUserNotificationCenterDelegate`, but only remote notifications can carry a service
  extension for content mutation, and only specific payload shapes (`mutable-content: 1`,
  non-silent, non-sound-only, non-badge-only) actually invoke it — assuming it intercepts
  "all notifications" is a common source of "why didn't my extension run" bugs.
- **Ignoring the service extension's time budget.** `didReceive(_:withContentHandler:)`
  must complete quickly; past its budget the system silently falls back to the original,
  unmodified content rather than erroring — always call the content handler, including
  from `serviceExtensionTimeWillExpire()`.
- **Never re-checking authorization/settings state at the point of scheduling.** Users
  can revoke or narrow notification permissions at any time in Settings; code that cached
  the authorization check from launch will schedule notifications that silently never show.
- **Reaching for UserNotifications for in-app-only feedback.** If the user is already in
  the app and the message doesn't need to survive backgrounding, an in-app banner avoids
  burning the permission prompt and avoids unnecessary review scrutiny of notifications.

## Current docs

- https://developer.apple.com/documentation/usernotifications
- https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications
- https://developer.apple.com/documentation/usernotifications/unauthorizationoptions
- https://developer.apple.com/documentation/usernotifications/unusernotificationcenter
- https://developer.apple.com/documentation/usernotifications/unnotificationserviceextension
- https://developer.apple.com/documentation/usernotificationsui
- https://developer.apple.com/documentation/usernotificationsui/customizing-the-appearance-of-notifications
- https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.usernotifications.critical-alerts
- https://developer.apple.com/documentation/usernotifications/setting-up-a-remote-notification-server
