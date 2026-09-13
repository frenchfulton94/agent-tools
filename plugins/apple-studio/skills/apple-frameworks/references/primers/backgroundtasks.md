> verified: 2026-08 against https://developer.apple.com/documentation/backgroundtasks.md, https://developer.apple.com/tutorials/data/documentation/backgroundtasks.json, https://developer.apple.com/tutorials/data/documentation/backgroundtasks/choosing-background-strategies-for-your-app.json, https://developer.apple.com/tutorials/data/documentation/backgroundtasks/starting-and-terminating-tasks-during-development.json, https://developer.apple.com/tutorials/data/documentation/backgroundtasks/bgtaskscheduler.json, https://developer.apple.com/tutorials/data/documentation/backgroundtasks/bgapprefreshtask.json, https://developer.apple.com/tutorials/data/documentation/backgroundtasks/bgprocessingtask.json, https://developer.apple.com/tutorials/data/documentation/backgroundtasks/bgtaskscheduler/register(fortaskwithidentifier:using:launchhandler:).json, https://developer.apple.com/tutorials/data/documentation/backgroundtasks/bgtaskscheduler/submittaskrequest(_:completionhandler:).json
> sources: live docs

# BackgroundTasks

## What it is / when to reach for it

BackgroundTasks wraps app work that needs to keep running (or start running) after the app is suspended: refreshing content, running longer
maintenance/processing jobs, and — via `BGContinuedProcessingTask` — letting foreground work finish if the user backgrounds the app mid-task. The
framework's own "Choosing Background Strategies" article lays out the decision space as five distinct tools, not one:

1. **Continue foreground work in background** — `UIApplication.beginBackgroundTask(withName:expirationHandler:)`. Simple, but strictly time-limited;
   the system kills the app if `endBackgroundTask(_:)` isn't called in time. For actual transfers, use `URLSession` background sessions instead, not
   this.
2. **Defer intensive work** — `BGProcessingTask`. System-timed (often overnight, on power), for ML training, DB maintenance, heavy batch work.
3. **Update app content periodically** — `BGAppRefreshTask`. Short (per the docs, up to ~30 seconds), for small/light refreshes.
4. **Background push notifications** — silent push (`content-available: 1`, `apns-priority: 5`, `apns-push-type: background`), for irregular server-
   driven fetches. Docs note it's rate-limited (≤3/hour) and grants up to 30 seconds via
   `application(_:didReceiveRemoteNotification:fetchCompletionHandler:)`.
5. **Background time plus user notification** — `UNNotificationServiceExtension`, when you need both background runtime and a delivered notification
   (e.g. modifying push content before display).

The real decision, before writing any BackgroundTasks code, is picking the right row in that table — not defaulting to BGTaskScheduler because it's
the most powerful-looking option. If updates are irregular and server-driven, silent push (or a notification service extension) is simpler and more
timely than hoping the OS schedules a refresh task. If the app can tolerate "content is occasionally stale until foregrounded," accepting foreground-
only refresh and skipping the framework entirely is a legitimate, lower-maintenance choice — BackgroundTasks buys you *possible* background execution,
never *guaranteed* execution, so it's not a substitute for correctness-critical work.

`BGAppRefreshTask` and `BGProcessingTask` are the two workhorses; `BGHealthResearchTask` is a `BGProcessingTask` variant scoped to health-research
studies, and `BGContinuedProcessingTask` (foreground-started, background-continuable) is the newest addition and can require a GPU entitlement
(`com.apple.developer.background-tasks.continued-processing.gpu`) for GPU-accelerated continuation.

Weigh the alternatives honestly before committing to this framework at all. Silent push means the server decides when to wake the app — good for
irregular, server-triggered updates, but it's rate-limited and adds a server-side dependency (APNs payload plumbing, a backend that knows when to
push) that BackgroundTasks doesn't need. Accepting foreground-only refresh means zero scheduling infrastructure and zero background-execution
uncertainty, at the cost of staler content on cold launch. BackgroundTasks itself sits between those: no server dependency, but also no execution
guarantee — the OS, not your code, decides if and when a task actually runs.

## Architecture integration

BGTaskScheduler is a systemwide singleton (`BGTaskScheduler.shared`) — it isn't a per-feature service you instantiate. Treat it as infrastructure at
the app-lifecycle boundary: register launch handlers once at launch, and have each handler delegate into your existing domain/service layer rather
than embedding business logic in the handler closure itself. That keeps the actual work unit testable independent of the scheduler.

Because launch-handler registration must complete before `applicationDidFinishLaunching(_:)` returns, this is app-delegate/App-struct-init wiring,
not something deferred to a lazily-initialized service — get the registration ordering wrong and the handler silently never fires.

Submission is idempotent-by-replacement, not additive: per the `submitTaskRequest(_:completionHandler:)` docs, submitting a request for an identifier
that already has an unexecuted request queued replaces the previous request rather than stacking a second one. That makes "just resubmit on every
relevant app event" a reasonable, safe pattern for keeping a refresh request's `earliestBeginDate` current, rather than something that needs its own
dedup logic. The completion handler for submission is also explicitly documented as arbitrary-queue and possibly-delayed — don't call the submission
API from the main thread or a performance-critical path, and don't assume the completion handler lands back on the calling queue.

Testability is the framework's real weak point, and it's structural, not incidental: BGTaskScheduler is a concrete singleton with no protocol seam,
task launches are OS-scheduled (not something a unit test can reliably trigger), and the docs' own answer for "how do I test this" is a pair of
**private, undocumented-in-public-API LLDB commands** (`_simulateLaunchForTaskWithIdentifier:` and `_simulateExpirationForTaskWithIdentifier:`) that
only work on a physical device attached to Xcode, invoked by breakpoint. There is no simulator story described anywhere in the docs this primer
fetched. Design around this: wrap `BGTaskScheduler` calls (register, submit, cancel, `getPendingTaskRequests`) behind your own thin protocol so the
plumbing can be faked in unit tests, and treat the actual scheduled-execution path as something verified manually on-device via the debugger workflow,
not something covered by CI.

`getPendingTaskRequests(completionHandler:)`, `cancel(taskRequestWithIdentifier:)`, and `cancelAllTaskRequests()` are worth wiring into a
debug/diagnostics surface early — since real scheduling is opaque and hard to observe, being able to inspect and clear pending requests from within
the app (a debug menu, a logging hook) is often the only visibility a team has outside of the device-and-breakpoint workflow.

## Privacy, entitlements, review

- **Info.plist**: every task identifier the app will register or submit must be declared under the `BGTaskSchedulerPermittedIdentifiers` key (an array
  of reverse-DNS-style strings). Per the `register(forTaskWithIdentifier:using:launchHandler:)` docs, `register` returns `false` — silently, not a
  crash — if the identifier isn't listed there.
- **UIBackgroundModes capability**: `BGAppRefreshTask` requires the `fetch` background mode; `BGProcessingTask` requires the `processing` background
  mode. Wrong or missing mode means the task type is unavailable, surfaced through `BGTaskScheduler.Error` (see below), not a silent no-op at the call
  site.
- **Entitlements**: GPU-accelerated `BGContinuedProcessingTask` work requires the `com.apple.developer.background-tasks.continued-processing.gpu`
  entitlement specifically — a narrower ask than the general background-modes capability.
- **Registration is one-shot per identifier per process**: the docs state plainly that registering the same task identifier twice **kills the app**.
  This makes registration code that could run more than once (e.g. accidentally re-entrant setup, or registration inside a view that can reappear) an
  outright crash bug, not a correctness nit.
- **Submission has hard limits**: at most 1 pending `BGAppRefreshTask` and 10 pending `BGProcessingTask` requests at a time; over that, submission
  fails with `tooManyPendingTaskRequests`. Other documented error codes: `notPermitted` (identifier not permitted, or unsupported resource requested),
  `unavailable` (background refresh disabled, or app not permitted), `immediateRunIneligible`.
- **`submit(_:)` is deprecated** in favor of `submitTaskRequest(_:completionHandler:)` — new code should target the replacement, but check its
  availability floor (below) against your deployment target before dropping the older call.
- **App Review**: declaring `UIBackgroundModes` capabilities you don't meaningfully use is a well-known review-scrutiny target industry-wide; this
  primer did not find framework-doc text spelling out a specific BackgroundTasks App Review policy, so treat "only declare the background mode you
  actually implement and use" as prudent default practice rather than a quoted Apple requirement.

## Availability

Per the framework overview: iOS 13.0+, iPadOS 13.0+, Mac Catalyst 13.1+, tvOS 13.0+, visionOS 1.0+. That's the framework floor — old enough to not be
the binding constraint for most apps today; `BGAppRefreshTask`, `BGProcessingTask`, and `BGTaskScheduler` itself all report that same 13.0+ floor
individually.

Newer additions sit on top of that floor and need their own check, not an inherited assumption from "the framework has existed since iOS 13":
`submitTaskRequest(_:completionHandler:)` (the replacement for the now-deprecated `submit(_:)`) shows as iOS/iPadOS/Mac Catalyst/tvOS/visionOS 27.0+
and is marked **Beta** in current docs — don't assume it's shippable on today's minimum deployment target without verifying against the live API page
first, and don't ship a Beta-marked API as your only submission path without a fallback to `submit(_:)` for older OS versions. `BGHealthResearchTask`,
`BGHealthResearchTaskRequest`, and `BGContinuedProcessingTask` are newer additions too; check each one's individual doc page for its actual floor
rather than assuming it matches the framework-level 13.0+.

## Classic pitfalls

- **Assuming the task will run at all, let alone on schedule.** The system decides if/when a refresh or processing task actually launches, based on
  usage patterns, battery, network, and device state. A `BGAppRefreshTaskRequest` with an `earliestBeginDate` is a hint, not a promise — apps that
  rely on background refresh for correctness-critical behavior (vs. a nice-to-have freshness bump) will eventually see it just not fire for a real
  user, sometimes for days.
- **Treating BGProcessingTask as always-available.** Per the docs, processing tasks run only when the device is idle and get terminated outright if
  the user starts using the device mid-task — that's a materially different contract from "runs for a while in the background," and cleanup has to be
  ready to fire at any moment.
- **Skipping (or mishandling) the expiration handler.** Both task types can be cut off before completion; the `expirationHandler` closure is where
  cleanup and any "mark as incomplete, try again later" bookkeeping belongs. Forgetting it, or doing expensive work inside it, is a common source of
  tasks that silently never make progress.
- **Forgetting `setTaskCompleted(success:)`.** Not calling it (success or failure) leaves the system unable to tell whether the task finished; the OS
  treats it as failed after the time budget lapses, but delaying the call artificially eats into the app's scheduling reputation with the system.
- **Registering an identifier twice.** Explicitly documented as an app-killing bug, not a warning — easy to hit if registration code isn't guarded
  against re-entry.
- **Debugging in the simulator and concluding "it works."** The documented debug workflow (private LLDB `_simulateLaunchForTaskWithIdentifier:` /
  `_simulateExpirationForTaskWithIdentifier:` commands) is device-only; simulator behavior for actual OS-scheduled launches isn't representative, and
  shipping a build that references those private debug functions is explicitly called out as cause for App Store rejection — strip any code path that
  invokes them before archiving.
- **Missing the Info.plist declaration and reading `false` as a generic failure.** `register(...)` returning `false` most commonly means the
  identifier isn't in `BGTaskSchedulerPermittedIdentifiers`, not a deeper scheduler problem — check the plist first.
- **Calling the submission API on the main thread.** The docs explicitly warn against calling `submitTaskRequest(_:completionHandler:)` from the main
  thread or a performance-critical context, and its completion handler runs on an arbitrary queue after an arbitrary delay — code that assumes it
  comes back quickly or on the calling queue will misbehave intermittently.
- **Blowing the pending-request ceiling.** Only 1 pending `BGAppRefreshTask` and 10 pending `BGProcessingTask` requests are allowed at once;
  submitting past that limit fails with `tooManyPendingTaskRequests` rather than silently queuing. Code paths that submit a new request per event
  without checking existing pending requests (or relying on submission's replace-not-stack behavior for the same identifier) can hit this with
  distinct identifiers.

## Current docs

- https://developer.apple.com/documentation/backgroundtasks.md
- https://developer.apple.com/documentation/backgroundtasks/choosing-background-strategies-for-your-app.md
- https://developer.apple.com/documentation/backgroundtasks/starting-and-terminating-tasks-during-development.md
- https://developer.apple.com/documentation/backgroundtasks/bgtaskscheduler.md
- https://developer.apple.com/documentation/backgroundtasks/bgtaskscheduler/register(fortaskwithidentifier:using:launchhandler:).md
- https://developer.apple.com/documentation/backgroundtasks/bgtaskscheduler/submittaskrequest(_:completionhandler:).md
- https://developer.apple.com/documentation/backgroundtasks/bgapprefreshtask.md
- https://developer.apple.com/documentation/backgroundtasks/bgapprefreshtaskrequest.md
- https://developer.apple.com/documentation/backgroundtasks/bgprocessingtask.md
- https://developer.apple.com/documentation/backgroundtasks/bgprocessingtaskrequest.md
