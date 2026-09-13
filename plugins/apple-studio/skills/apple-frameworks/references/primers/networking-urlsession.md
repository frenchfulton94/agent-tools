> verified: 2026-08 against https://developer.apple.com/tutorials/data/documentation/foundation/urlsession.json, https://developer.apple.com/tutorials/data/documentation/foundation/downloading-files-in-the-background.json, https://developer.apple.com/tutorials/data/documentation/foundation/urlsession/data(for:delegate:).json, https://developer.apple.com/tutorials/data/documentation/bundleresources/information-property-list/nsapptransportsecurity.json, https://developer.apple.com/tutorials/data/documentation/foundation/urlprotocol.json
> sources: live docs

# URLSession

## What it is / when to reach for it

URLSession is Foundation's API for downloading and uploading data over HTTP/HTTPS (and
`data`/`file`/`ftp` schemes), including background transfers that continue while the app is
suspended or not running. It natively supports HTTP/1.1, HTTP/2, and HTTP/3, with HTTP/2
requiring server-side ALPN support. It is the default, correct choice for essentially all app
networking on Apple platforms — it is what every third-party HTTP library (Alamofire included)
is built on top of.

Reach for URLSession directly rather than a wrapper library when:
- You want zero third-party dependency surface.
- You need background transfer semantics — Alamofire doesn't add real value here, it's still
  URLSession underneath.
- Your needs are simple enough that async/await plus Codable cover them without a
  request-builder DSL.

Consider a wrapper (Alamofire, or a thin in-house client) when you need consistent
interceptor/retry-policy chains across a large team, or richer multipart/upload ergonomics than
the stdlib gives for free — but treat that as a team-ergonomics decision, not a capability gap
URLSession is missing. Raw sockets (Network.framework) are the alternative only for custom
transport protocols, not HTTP — don't reach for them just to avoid URLSession's abstractions.

## Architecture integration

URLSession sits at the edge of the app, typically wrapped behind a thin networking/data-access
layer (a "client" or "service" type) so call sites depend on a protocol, not on `URLSession`
concretely. This is what makes the boundary testable and swappable.

For testability, the sanctioned seam is `URLProtocol`:
- Subclass it and override the task-based hooks — `canInit(with:)` and
  `init(task:cachedResponse:client:)` — which the docs explicitly prefer over the older
  request-based overloads.
- Register it via `URLProtocol.registerClass(_:)`, or inject a `URLSessionConfiguration` with
  `protocolClasses` set for a scoped, test-only session.
- This intercepts requests at the transport layer without touching app code, which is more
  faithful than hand-rolling a fake `URLSession` — it still exercises your real `URLRequest`
  construction and response parsing.

Combine this with dependency-injecting the `URLSession` instance (or a narrow protocol wrapping
just the one or two methods you call) into your networking layer, so tests can swap
configurations freely without touching production code paths.

Background sessions carry real app-lifecycle coupling, not just data-layer concerns:
- You must recreate the session with the *same identifier* on next launch so the system can
  reassociate pending tasks with your app — the docs are explicit about this.
- The app delegate's `handleEventsForBackgroundURLSession(_:completionHandler:)` must store the
  completion handler, then invoke it on the main queue once
  `urlSessionDidFinishEvents(forBackgroundURLSession:)` fires.

Plan for this plumbing up front if background downloads are in scope — it isn't an afterthought
you can bolt onto an existing networking layer cleanly.

## Privacy, entitlements, review

No capability or entitlement is required for ordinary URLSession networking. There is no
"Networking" capability toggle in Xcode the way there is for, say, HealthKit or Push
Notifications.

The one Info.plist surface that matters is **App Transport Security** (`NSAppTransportSecurity`).
Per the docs, ATS requires all URLSession HTTP connections to use HTTPS and imposes TLS checks
beyond baseline server trust evaluation; ATS blocks connections that don't meet the bar. The
relevant keys, if exceptions are genuinely needed:
- `NSAllowsArbitraryLoads` — global escape hatch, disables ATS everywhere.
- `NSAllowsArbitraryLoadsInWebContent` — scoped to web views only.
- `NSAllowsArbitraryLoadsForMedia` — scoped to AVFoundation requests only.
- `NSAllowsLocalNetworking` — allows local/LAN resources to load.
- `NSExceptionDomains` — per-domain relaxation; prefer this over the global keys.

Apple's own docs carry an explicit App Review warning here: "Always look for ways to improve
server security before adding ATS exceptions. Loosening ATS restrictions reduces the security of
your app." Treat any `NSAllowsArbitraryLoads: true` in a shipping app as a red flag an agent
should question rather than rubber-stamp — it draws reviewer scrutiny and is rarely actually
necessary; fixing the server's TLS configuration is almost always the better fix.

Beyond ATS, nothing else in the privacy/entitlement space applies to plain URLSession usage.

## Availability

The `URLSession` class itself is old and broadly available: iOS/iPadOS 7.0+, macOS 10.9+, tvOS
9.0+, watchOS 2.0+, visionOS 1.0+, Mac Catalyst 13.1+. Availability of the class as a whole is
essentially never the blocker.

The async/await surface is newer and has its own floor. Per the docs page for
`data(for:delegate:)` specifically:

| Platform | Minimum OS |
|---|---|
| iOS / iPadOS | 15.0 |
| macOS | 12.0 |
| tvOS | 15.0 |
| watchOS | 8.0 |
| visionOS | 1.0 |
| Mac Catalyst | 15.0 |

Treat this floor (the iOS 15 / macOS 12 generation) as the baseline for the whole async/await
family — `data(for:)`, `data(from:)`, `bytes(for:)`, `bytes(from:)`, `AsyncBytes` — since they
were introduced together, though confirm a specific method's own page if precision matters. If a
project's deployment target is below iOS 15 / macOS 12, async/await URLSession APIs are
unavailable and you're back to completion-handler or delegate-based APIs (or bridging one with a
continuation).

## Classic pitfalls

- **Delegate retain cycles / leaked sessions.** The docs state plainly: "The session object
  keeps a strong reference to the delegate until your app exits or explicitly invalidates the
  session. If you don't invalidate the session, your app leaks memory until the app terminates."
  Creating a new `URLSession` with `self` as delegate on every request — a common mistake —
  leaks every single one. Either reuse a long-lived session, use `.shared` for simple
  delegate-less calls, or explicitly `invalidateAndCancel()` when done.
- **Background session identifier churn.** Generating the background session identifier
  dynamically (e.g., from a UUID) instead of using a fixed string breaks the app's ability to
  reassociate tasks after relaunch — the docs call out a fixed identifier as the preferred
  approach.
- **Rate-limit-inducing background session patterns.** The docs warn that repeatedly waking the
  app for one download at a time (start, get resumed, start another) triggers escalating
  system-imposed delays. The documented mitigation is to use one, or a few, background sessions
  and enqueue many tasks at once so the system can batch the wake-ups. Architectures that lazily
  schedule background downloads one at a time will silently degrade in real-world usage.
- **Background sessions assumed to support arbitrary uploads.** Background sessions reliably
  support only file-based uploads — data/stream-based uploads fail once the app exits the
  foreground, and custom `URLProtocol`s aren't supported (HTTP/HTTPS only). Redirects are always
  auto-followed; `willPerformHTTPRedirection` is never called.
- **Reaching for ATS exceptions instead of fixing the server.** `NSAllowsArbitraryLoads` is a
  shortcut that both weakens security and draws App Review scrutiny; the narrower
  `NSExceptionDomains`, or simply fixing server TLS, is almost always the right fix.
- **Skipping the `URLProtocol` seam and hand-mocking instead.** Because the transport-level
  interception point already exists and is doc-sanctioned, building a bespoke
  `URLSessionProtocol` abstraction with hand-written fakes is usually more code than registering
  a `URLProtocol` subclass on a test-only `URLSessionConfiguration`, and it exercises less of the
  real request/response path.
- **Deployment-target mismatch with async/await APIs.** Reaching for `data(for:)` without
  checking the iOS 15 / macOS 12 floor against the project's actual deployment target is an easy
  availability bug to introduce silently in an agent-authored change.

## Current docs

- https://developer.apple.com/documentation/foundation/urlsession.md
- https://developer.apple.com/documentation/foundation/urlsession/data(for:delegate:).md
- https://developer.apple.com/documentation/foundation/urlsession/bytes(for:delegate:).md
- https://developer.apple.com/documentation/foundation/fetching-website-data-into-memory.md
- https://developer.apple.com/documentation/foundation/downloading-files-in-the-background.md
- https://developer.apple.com/documentation/foundation/downloading-files-from-websites.md
- https://developer.apple.com/documentation/foundation/uploading-data-to-a-website.md
- https://developer.apple.com/documentation/foundation/urlprotocol.md
- https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity.md
