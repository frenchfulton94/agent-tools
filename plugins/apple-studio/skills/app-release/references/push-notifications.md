> verified: 2026-08 against https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns, https://developer.apple.com/documentation/usernotifications/establishing-a-token-based-connection-to-apns, https://developer.apple.com/documentation/usernotifications/establishing-a-certificate-based-connection-to-apns, https://developer.apple.com/documentation/bundleresources/entitlements/aps-environment, https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.aps-environment, https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app, https://developer.apple.com/documentation/usernotifications/registering-your-app-with-apns, https://developer.apple.com/documentation/usernotifications/modifying-content-in-newly-delivered-notifications, https://developer.apple.com/documentation/usernotifications/unnotificationserviceextension, https://developer.apple.com/documentation/usernotifications/testing-notifications-using-the-push-notification-console, https://developer.apple.com/documentation/usernotifications/sending-push-notifications-using-command-line-tools, https://developer.apple.com/documentation/usernotifications/scheduling-a-notification-locally-from-your-app, `xcrun simctl help push` (local toolchain, empirical), https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/RevisionHistory.html
> sources: Push Notifications by Tutorials v4.0.0 (judgment only), live Apple docs

# Push Notifications: APNs Operations

Scope: getting a production-grade APNs delivery pipeline configured, entitled, and debugged on the
app side — auth material, environments, capabilities, token lifecycle, silent-push constraints,
extension signing, and delivery debugging tools. This is not about `UNUserNotificationCenter` API
usage (authorization requests, delegate wiring, foreground/tap handling) — see
apple-frameworks's `usernotifications.md` primer for that. It is also not about what a provider
server implements (HTTP/2 request construction, JWT signing code, provider architecture) — that's
a backend concern outside this skill's surface; a provider is assumed to exist wherever "your
server" is mentioned below.

## Provider auth: keys vs. certificates

Two credential types authenticate a provider to APNs; they are not interchangeable and one has
clearly won:

- **`.p12` certificates** (PKCS#12): still per-app — sending to multiple apps means one certificate
  and one managed connection per app — and still expire annually, forcing yearly renewal tracked
  per app (Establishing a certificate-based connection to APNs,
  https://developer.apple.com/documentation/usernotifications/establishing-a-certificate-based-connection-to-apns).
  One thing the book gets wrong for the current day: certificates are no longer split per
  environment. The certificate type Apple issues today is explicitly "Apple Push Notification
  service SSL (**Sandbox & Production**)" — a single certificate authenticates both environments,
  correcting the ch. 5 framing that certs are separately issued per environment.
- **`.p8` authentication tokens** (JWT, RFC 7519): not a single undifferentiated key. Apple issues
  two kinds, and the distinction matters operationally: **team-scoped keys** work across every
  topic (app) on the team but are restricted to one environment each (sandbox or production), with
  a hard cap of two keys per environment; **topic-specific keys** are scoped to specific topics
  within a single environment (up to 400 topics per key), with a cap of 200 keys per environment
  (Establishing a token-based connection to APNs,
  https://developer.apple.com/documentation/usernotifications/establishing-a-token-based-connection-to-apns).
  So a `.p8` key still saves you from certificate-style per-app issuance — one team-scoped key can
  authenticate an entire app portfolio — but it is environment-scoped like a certificate, not a
  universal all-apps-all-environments credential. Tokens must also be refreshed (re-signed) every
  20–60 minutes; APNs rejects anything older than an hour with `ExpiredProviderToken` (same URL).

Live docs confirm the resulting capability gap directly: token-based (JWT bearer) auth supports
every `apns-push-type`, while certificate-based auth supports only a subset — Live Activities'
broadcast push and a few other newer push types are JWT-only (Sending notification requests to
APNs, https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns).
Combined with the per-app certificate-management overhead, this is why `.p8` keys are the current
default recommendation — reach for a certificate only when integrating with legacy provider
tooling that hasn't moved off it.

Building the JWT/HTTP-2 request itself, or deciding cert vs. key at the request layer, is
provider/server work and out of scope here — the app-side concern is just knowing which artifact
your team's provider holds, since it changes nothing about what the app does at registration time.

## Dev vs. production environments and `aps-environment`

APNs runs two independent server environments with separate hostnames: sandbox at
`api.sandbox.push.apple.com:443` and production at `api.push.apple.com:443` (alternate port `2197`
available for restrictive firewalls) (Sending notification requests to APNs, same URL as above).
A device token minted while the app is registered against one environment is not valid against the
other — same physical device, two disjoint token spaces. A provider silently pointed at the wrong
host for a given token is one of the most common "push never arrives" root causes and won't surface
as an app-side bug at all.

Which environment an installed app registers into is controlled by the `aps-environment`
entitlement (`com.apple.developer.aps-environment` on macOS), a string valued `development` or
`production` (APS Environment Entitlement,
https://developer.apple.com/documentation/bundleresources/entitlements/aps-environment; macOS
variant, https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.aps-environment).
Xcode sets this automatically from whichever provisioning profile signed the build — a development
profile yields `development`, and any distribution profile (Ad Hoc, App Store, TestFlight) yields
`production` — so a build's push environment is a direct, mechanical consequence of how it's
signed, not a separate switch to flip. Enabling the Push Notifications capability in Xcode is what
adds the entitlement to the app at all; without it there's no `aps-environment` key and remote
registration fails outright. For the entitlement/profile binding mechanics in general (why the
profile determines this), see `signing-and-provisioning.md` — this file only owns the
`aps-environment` values and their dev/prod meaning.

## Capabilities: Push Notifications and Background Modes

Two capability toggles matter for APNs ops, at a judgment level rather than a click-path:

- **Push Notifications** — adds the `aps-environment` entitlement and the associated App ID/
  provisioning requirement; without it, `registerForRemoteNotifications` fails to produce a usable
  token.
- **Background Modes → Remote notifications** — required in addition to (not instead of) the
  `content-available` payload key for silent push to actually wake the app in the background: "To
  receive background notifications, you must add the remote notifications background mode to your
  app. In the Signing and Capability tab, add the Background Modes capability, then select the
  Remote notification checkbox" (watchOS: add it to the WatchKit Extension instead) (Pushing
  background updates to your app,
  https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app).
  A payload with `content-available: 1` but no Background Modes capability is a classic "silent
  push does nothing" bug that looks like a payload problem but is a capability gap.

## Device-token lifecycle

Treat the device token as an opaque, size-unstable address scoped to one app-device pairing:

- **Never hardcode a token length or format.** The token has grown since APNs' early years — Apple's
  own documentation revision history for remote notifications logged a "larger token size" change
  as far back as 2017, and simulator-issued tokens (supported for testing since Xcode 14) run
  considerably longer than a real device's — and current live docs still instruct providers not to
  assume a specific size (Sending notification requests to APNs, same URL as above). Any storage
  schema (DB column width, fixed-size buffer) that bakes in today's observed length will break
  silently on a future OS.
- **Tokens rotate, and are per-app.** A new token is issued when the user restores a device from
  backup, installs the app on a new device, or reinstalls the OS — and a token is never shared
  across two different apps on the same device, even from the same developer (Registering your app
  with APNs,
  https://developer.apple.com/documentation/usernotifications/registering-your-app-with-apns).
  Every `didRegisterForRemoteNotificationsWithDeviceToken` call should be treated as "here is the
  current token for this app on this device" and upserted server-side, never assumed stable across
  app launches, and never cached to local storage as if it were permanent.
- **A user can hold multiple tokens; don't collapse them to one.** Associating a token with a
  user's account is the documented pattern (Apple's own guidance is to store tokens alongside
  account info so a server can target a person's devices), but because a person can own multiple
  devices — and a device can generate a new token at any time — a provider must track a *set* of
  live tokens per account and prune ones that go stale (bounce with an `Unregistered` / `BadDeviceToken`
  error), not overwrite "the" token for a user as if only one could exist (same URL). A provider
  that assumes one current token per user misdelivers the moment someone has two devices or
  reinstalls on one of them.

## Silent push: budget, pairing, and "hint, not guarantee"

Silent (background) push is data-refresh plumbing, not a notification the user sees, and it comes
with hard pairing rules and no delivery guarantee (Pushing background updates to your app,
https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app,
unless noted otherwise below):

- The payload's `aps` dictionary must contain only `content-available: 1` — no `alert`, `sound`, or
  `badge` key, since any of those would trigger user interaction and disqualify it as "background."
- The `apns-priority` header must be `5`; pairing `content-available` with priority `10` is an
  explicit, documented APNs error, not merely discouraged — confirmed directly in the push-type
  reference: "Always use priority 5. Using priority 10 is an error" (Sending notification requests
  to APNs, https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns).
- `apns-push-type` must be set to `background` — required outright on watchOS 6+, and recommended
  (treat as required) on every other platform.
- Requires the Background Modes → Remote notifications capability (above) — without it, background
  pushes are simply never delivered to the app's background handler.
- Once the OS wakes the app, the code has **30 seconds** to perform its work and call the provided
  completion handler — stated as an exact figure, not an approximation, in Apple's own docs.
- **The system treats background notifications as low priority and does not guarantee delivery,
  and it throttles aggressively: don't try to send more than two or three per hour.** This is a
  concrete, documented ceiling, not just qualitative "may get throttled" language — a feature that
  needs more frequent server-initiated wake-ups than that needs a different mechanism (e.g.
  BackgroundTasks' periodic refresh), not more background pushes.
- Only the newest background notification is held for a device at a time — when a new one arrives,
  the system discards the older undelivered one, and if the app is force-quit or killed the held
  notification is discarded entirely (delivered only if the user relaunches the app first). Design
  background-refresh payloads to be idempotent "there's new data, go fetch it" hints rather than
  each carrying unique data the app must not miss — a miss is expected behavior, not a bug.
- **Silent push is a hint, not a delivery guarantee**, full stop: don't design a feature that depends
  on it firing promptly, or even firing at all, every time. Always keep a foreground-refresh
  fallback for anything a background push merely optimizes.
- The "only the newest survives" behavior above generalizes beyond just silent push: APNs stores
  only one notification per bundle ID per device at all, so several notifications sent before a
  device comes online typically collapse to just the latest (though the docs note this isn't
  strictly guaranteed under high volume) (Sending notification requests to APNs, same URL as
  above). `apns-collapse-id` — capped at 64 bytes, confirmed exactly in the live header reference —
  is the explicit, deliberate version of that same idea: set it to a stable ID (e.g. a game-session
  key) to intentionally supersede one specific in-flight notification with a newer one, rather than
  relying on APNs' implicit, less-predictable last-write-wins behavior.

## Notification extensions: what each is for, and their separate signing

Both extension types are covered API-wise in apple-frameworks's `usernotifications.md` primer
(`didReceive`/content handler, the `mutable-content` trigger conditions, "not all notifications
invoke it," and the time-budget pitfall) — don't re-derive that here. What's new at the ops layer:

- **Notification Service Extension** — runs as middleware between APNs and the displayed
  notification. Apple's own stated motivating cases are exactly what the book names: decrypting
  data sent in an encrypted format, and downloading images or other media attachments whose size
  would exceed the payload's 4 KB limit (Modifying content in newly delivered notifications,
  https://developer.apple.com/documentation/usernotifications/modifying-content-in-newly-delivered-notifications).
  For the payload-shape trigger condition (`mutable-content: 1` + non-silent/non-sound-only/
  non-badge-only) and the "assuming it intercepts all notifications" pitfall, see the primer's
  "Conflating local and remote notification handling" entry — not restated here.
- **Notification Content Extension** — a UI concern, not a payload-mutation one; see the primer for
  what it does.
- **Signing**: each extension is its own target with its own bundle ID and needs its own App ID and
  provisioning profile, exactly like any other app extension — see `signing-and-provisioning.md`
  for the general extension-target signing mechanics (per-target entitlements, profile binding,
  automatic vs. manual signing tradeoffs). Nothing about push specifically changes that model; the
  extension doesn't register for remote notifications itself; and don't restate the service
  extension's time-budget-then-silent-fallback behavior here — see the primer.

## Debugging delivery

Real production APNs delivery cannot be simulated locally — treat that as a hard boundary when
choosing a debugging tool:

- **`xcrun simctl push <device> [<bundle-id>] (<payload.json> | -)`** — Simulator-only payload
  testing, confirmed via `xcrun simctl help push` on this repo's local toolchain: it injects a JSON
  payload (max 4096 bytes, must contain a top-level `aps` key, optionally a `Simulator Target
  Bundle` key instead of passing the bundle ID as an argument) directly into a running Simulator
  instance to exercise your app's handling code (foreground presentation, service extension logic,
  delegate routing), with no real device token, provider, or network round-trip involved. Apple's
  own tool help is explicit that only application remote push is supported — VoIP, Complication,
  and File Provider push types are not. Useful for iterating on payload shape and in-app handling,
  useless for validating that real APNs delivery actually works.
- **Push Notification Console** (web dashboard at Apple's developer portal) — the ops-grade way to
  test real delivery without writing any provider code: send raw JSON payloads to a real device
  token or a broadcast channel against sandbox or production, generate the equivalent `curl`
  command, and validate a JWT (signature, team ID, expiration) or a device token against a bundle
  ID entirely client-side (the signing key is used only in-browser, never uploaded). Sending to the
  *production* environment requires an admin role on the team; sending to development does not, and
  all team members can view the 30-day sent-notification history regardless of role. One sharp
  edge: the **Delivery Log — the tool that shows a notification's actual delivery-state
  outcome, keyed by the `apns-unique-id` APNs returns per request — is available only for the
  development environment**, for up to 7 days after sending; there is no equivalent delivery-log
  visibility for production sends through the console (Testing notifications using the Push
  Notification Console,
  https://developer.apple.com/documentation/usernotifications/testing-notifications-using-the-push-notification-console).
- **Command-line testing against real sandbox APNs** — Apple documents `curl`-based recipes (via a
  certificate, or via a JWT built with `openssl`) for posting a single test payload straight to
  `api.sandbox.push.apple.com` (Sending push notifications using command-line tools,
  https://developer.apple.com/documentation/usernotifications/sending-push-notifications-using-command-line-tools).
  Useful only as an ops sanity check — "does this auth key/cert plus this device token actually
  reach this device" — before or instead of standing up provider code; constructing that flow as
  part of a real provider is server work and out of scope here.
- **Console.app / log streaming on-device** — for a real device, streaming the system log (filtered
  to the relevant push-related subsystem) while a push is expected is the only way to see ground
  truth for production APNs delivery: registration success/failure, whether the device received and
  attempted to display a push, and extension launch/timeout behavior. This is the fallback of last
  resort precisely because production delivery can't be simulated any other way.

## When none of this applies: local notifications

Local notifications (interval, calendar, or location triggers) sidestep the entire APNs ops path.
Confirmation by omission is as clear as a live doc gets here: Apple's own guide to scheduling a
local notification (Scheduling a notification locally from your app,
https://developer.apple.com/documentation/usernotifications/scheduling-a-notification-locally-from-your-app)
never mentions a device token, a provider server, or an environment entitlement anywhere — content
and delivery conditions are built entirely from local Swift objects (content object, a
calendar/interval/location trigger object, and a request object handed to
`UNUserNotificationCenter.add(_:)`), with nothing transmitted over the network at all. If a
feature's "notification" always originates from data the device already has — a timer, a scheduled
reminder — everything above (keys, environments, capabilities, token lifecycle) simply doesn't
apply; don't route that feature through APNs machinery just because it displays through the same
`UNUserNotificationCenter` surface.
