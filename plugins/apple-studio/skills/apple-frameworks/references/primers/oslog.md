> verified: 2026-08 against https://developer.apple.com/tutorials/data/documentation/os/logging.json, https://developer.apple.com/tutorials/data/documentation/os/generating-log-messages-from-your-code.json, https://developer.apple.com/tutorials/data/documentation/os/viewing-log-messages.json, https://developer.apple.com/tutorials/data/documentation/os/logger.json
> sources: live docs

# OSLog

## What it is / when to reach for it

OSLog (the unified logging system) is Apple's replacement for Apple System Logger (ASL) and syslog. It's a
centralized, binary-compressed log store shared across the whole system — not a text file your app owns and
appends to.

The docs frame its purpose narrowly: debugging without a debugger attached (e.g. on a user's machine),
catching intermittent problems, and tracking general app behavior such as task start/end events. Reach for it
whenever you want log output that survives past the debug session, can be filtered by subsystem/category after
the fact, and won't leak sensitive data by default.

Default to `Logger` (Swift, struct-based) for any Swift codebase — it's the modern surface. Fall back to the
`os_log`/`os_log_t` C API only in Objective-C, or when supporting OS versions below Logger's floor (see
Availability).

Versus the alternatives:

- **`print()` / `NSLog`** — fine for scratch debugging in Xcode's console, but the output isn't structured,
  isn't filterable by subsystem/category, and isn't privacy-redacted. Neither gives you Console's correlation
  story or `log show`/`log stream` after the process has already exited.
- **Third-party logging frameworks** (CocoaLumberjack, SwiftyBeaver, etc.) — still sometimes justified for
  shipping logs to a remote backend, custom formatting, or unifying logging across a codebase that also
  targets non-Apple platforms. For anything staying on-device or triaged via Console/`log`, OSLog is the
  platform-native answer with lower overhead and nothing to vendor. Don't reach for a third-party logger just
  for convenience methods OSLog already provides (levels, subsystem/category, signposts).

OSLog is not a general telemetry/analytics pipeline and not a crash reporter — it's local, system-integrated
logging. If you need remote aggregation, you still have to ship OSLog output (or a parallel event) to a
backend yourself; the fetched docs describe no built-in network sink.

## Architecture integration

Treat a `Logger` instance the way you'd treat any other cross-cutting infrastructure dependency: construct it
with an explicit subsystem/category pair near the top of a module or type, not ad hoc per call site. The docs
define the two strings as:

- **subsystem** — "identifies a large functional area within your app or apps," conventionally reverse-DNS
  (e.g. `com.example.myapp`).
- **category** — "identifies a particular component or module in a given subsystem," free-form.

Pick a subsystem-per-app (or per-module in a multi-target app) and category-per-feature convention up front.
Retrofitting subsystem/category onto scattered `Logger()` default-init call sites later is annoying, because
nothing forces you to pass them. If you don't need filtering, the docs say the default log (no
subsystem/category) is acceptable — but for anything beyond a small app, unlabeled log lines are a cost you're
pushing onto whoever triages Console/`log` output later.

Keep logging out of business logic the same way you'd keep any I/O out of pure functions: pass a `Logger` in
(or resolve one from a small logging facade) rather than reaching for a global singleton inside domain types.
That keeps domain logic testable without a live logging subsystem, and lets you swap in a no-op logger for
unit tests without conditionals in the code under test. This is ordinary dependency-injection hygiene, not
something specific to OSLog — the docs don't prescribe an architecture, so treat it as judgment, not a
documented requirement.

Consumption is a separate concern from emission. The docs list four distinct tools: the Console app (GUI,
correlation and filtering), the `log` command-line tool (`log show` / `log stream`), Xcode's debug console
(automatic while a debugger is attached), and the OSLog framework itself for programmatic access. Logs are
stored in binary compressed form — the docs are explicit that "you can't read and parse the log files
directly." Don't design tooling around scraping a log file on disk; go through one of these four paths
instead.

A related but distinct API surface worth knowing about, not adopting by default: **signposts**
(`OSSignposter`, `os_signpost_*`) for measuring task/interval performance, visualized in Instruments. They
live in the same framework family as OSLog but solve a different problem — timing, not narrative debugging.
Don't reach for `Logger` calls to hand-roll performance measurement when signposts already exist for that.

## Privacy, entitlements, review

No entitlement or capability is required to use OSLog for standard logging — nothing in the fetched docs
(overview, message-generation, or Logger pages) mentions an Info.plist key or capability toggle for basic use.
Treat that as "not required by anything these pages describe," not as a guarantee for every edge case — e.g.
remote/streaming log access from another device may have its own story worth checking separately before you
rely on it.

The privacy behavior that actually matters for App Review and for your own data-handling posture is built into
the string-interpolation formatter itself, not a separate mechanism you opt into:

- **Default redaction** — per the docs, "the system doesn't redact integer, floating-point and Boolean values,
  but it does redact the contents of dynamic strings and complex dynamic objects." A raw `\(someString)` is
  redacted by default; a raw `\(someInt)` is not.
- **Explicit public** — `\(smoothieName, privacy: .public)` opts a specific interpolated value into
  visibility.
- **Explicit private** — `privacy: .private` (Swift) / `%{private}d` (C) marks an otherwise-visible value
  (e.g. a number) private when it's sensitive despite the default.
- **Hash correlation** — `.private(mask: .hash)` / `%{mask.hash}d` lets you correlate repeated occurrences of
  the same value across log lines without exposing it; the docs note the hash "is unique for the current
  process" and "doesn't provide any identifying information about that value."

This redaction is a genuine App Review and privacy asset: it's why OSLog is safer-by-default than
`print()`/`NSLog` for anything that might touch user data — a stray interpolated string doesn't silently leak
PII into device logs that could be pulled via sysdiagnose or Console. But it is not a substitute for thinking
about what you log. The docs' own caution is direct: "Log messages that contain sensitive user data present a
potential problem for users, because anyone with access to the logs or the user's computer can see the
information." Their recommendation is to limit messages to static strings and defined numbers, and redact
anything dynamically generated that's sensitive.

## Availability

- The unified logging system overall (the Objective-C `os_log` API): iOS 10.0+, macOS 10.12+, tvOS 10.0+,
  watchOS 3.0+, per the top-level Logging overview page. It explicitly supersedes ASL and syslog.
- The Swift `Logger` struct specifically has a higher floor: iOS 14.0, iPadOS 14.0, macOS 11.0, Mac Catalyst
  14.0, tvOS 14.0, watchOS 7.0 (plus visionOS, unversioned in the fetched data), per the Logger reference
  page.

If you need to support iOS/macOS versions below Logger's floor, the docs point you at the C `os_log()`
functions taking an `os_log_t` instead. Check the current Logger page yourself before committing to a
deployment floor — this file only reflects what was fetched this session.

## Classic pitfalls

- **Assuming redaction covers everything.** Only dynamic strings and complex dynamic objects are redacted by
  default; numbers and booleans are not. A user ID that happens to be an `Int`, or an account balance as a
  `Double`, prints in the clear unless you explicitly mark it `.private`. Reason per interpolated value, not
  "it's OSLog, so it's safe."
- **Marking sensitive data `.public` for debugging convenience, then shipping it.** The `.public` override
  exists so you can see values in Console during development; it's easy to leave it on a call site that later
  carries real user data once the code path changes. Treat any `.public` annotation as something that needs
  its own review pass.
- **Misusing severity levels as a substitute for control flow.** Debug logs are memory-only and cheap;
  Notice/Error/Fault get persisted to disk (up to a system-managed limit) and cost more — the docs note
  "faults and other severe messages incur more overhead because the system often captures additional
  information and writes all of that information to disk." Logging routine, high-frequency events at `.error`
  or `.fault` pollutes the persisted log, making real faults hard to find, and burns overhead you didn't need
  to pay.
- **Treating log messages as parseable data.** The docs are explicit that you "can't read and parse the log
  files directly" — they're binary and require Console, `log`, Xcode, or the OSLog framework itself to decode.
  Don't build tooling that greps a log file on disk.
- **No subsystem/category discipline.** Defaulting every `Logger()` call site to the unlabeled default log
  makes Console/`log` filtering useless at scale — you end up scrolling an undifferentiated stream instead of
  filtering by feature. Decide the scheme before logging calls proliferate.
- **Forgetting logging is local-first.** OSLog has no built-in remote sink. If the plan is "we'll debug
  production issues by reading users' logs," that requires sysdiagnose/Console access to the device, or your
  own pipeline to ship log data off-device — don't assume OSLog alone gives you remote observability.

## Current docs

- https://developer.apple.com/documentation/os/logging
- https://developer.apple.com/documentation/os/generating-log-messages-from-your-code
- https://developer.apple.com/documentation/os/viewing-log-messages
- https://developer.apple.com/documentation/os/logger
- https://developer.apple.com/documentation/os/oslogtype
- https://developer.apple.com/documentation/os/customizing-logging-behavior-while-debugging
- https://developer.apple.com/documentation/os/recording-performance-data
