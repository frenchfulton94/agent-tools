# Phase 10 final fix round: report

Base: `3d25847`. Ruling P52 set the scope: fix F1 to F8, and defer D1 to D6. Line numbers are at `c071b41`. Every log named here is in `authoring/apple-studio/records/2026-10-18-phase10-games/final-fix/` unless a path says otherwise.

## Evidence files

| File | What it holds |
|---|---|
| `probe/run.sh`, `probe/main.swift`, `probe/instrumented.swift` | The F1 probe. `run.sh` takes the reference's `sendOverDTLS` block out of the file and compiles it verbatim with Swift 6 at `-target arm64-apple-macos26.0`. It then runs each case. Each case has its own deadline inside the probe, and `perl alarm` ends the process if the probe hangs. |
| `f1-probe.log` | `run.sh <build-dir>`: 20 short cases (21 `==` headers, counting the build). They cover the 3d25847 branches, the fixed function forced onto each branch, and the verbatim snippet. |
| `f1-probe-long.log` | `run.sh <build-dir> long`: the 3d25847 branches against the two peers that never answer, with a 180 s deadline |
| `run_typecheck.sh`, `typecheck.log` | The Swift gate, the native gate, and `bash -n` on each shell block, over every edited reference |
| `run_vale.sh`, `vale.log` | Vale on every edited file, at `3d25847` and now |
| `gates.log` | `bun test`, `bun run audit`, `bun run validate`, `claude plugin validate . --strict`, `check_verbatim.py`, and `pgrep` |

Both probe logs record snippet sha256 `7058b6cb5bb896fc7ecf7d592e1be34459a52f0d857f96bfa98744e2efe1ee54`. That is the shipped block's hash at the commit, so the logs are for the code that ships.

## F1 (Important): `sendOverDTLS` could hang forever

**Changed in** `apple-games/references/game-center-and-online.md`:
- `:533-602` is the snippet.
- `:604-631` says what was runtime-checked and what was not.
- `:739-741` is a new Classic pitfall: "Awaiting a send with no deadline".
- The `verified:` header on line 1 gained nine pages.

**What the probe found** (macOS 27.0.1, Swift 6.4):
- **The hang is wider than the review said.** Both 3d25847 branches hang, not only the OS 26 branch. Against `dtls-probe.invalid`, each branch went to `.waiting(-65554: NoSuchRecord)` within 10 ms. Neither had returned 8 s later (`original26` and `original27` cases).
- **A state handler alone does not bound the send.** Against `127.0.0.1:9` (no listener) and `192.0.2.1` (TEST-NET-1), both branches stayed in `.preparing` for the full 180 s that the probe waited (`f1-probe-long.log`). A DTLS handshake to a peer that never answers reaches neither `.waiting` nor `.failed`. I built the reviewer's sketch first (cancel on `.waiting` or `.failed`), and it hung on these peers. The fix therefore adds a deadline.
- **The reviewer's belief holds.** Cancelling an `NWConnection` calls its pending send completion with `ECANCELED` (POSIX 89), within 2 ms. It also does so when the connection is cancelled before the send is enqueued (`fixed26 … precancelled`).
- **The OS 27 `send` returns when its task is cancelled**, with `ECANCELED` (`original27 unresolvable cancel-after-1s`).
- **Framework fault: an OS 27 `send` that starts in an already-cancelled task never returns.** The Swift runtime printed: "SWIFT TASK CONTINUATION MISUSE: send(content:context:isComplete:) leaked its continuation without resuming it" (`original27 unresolvable precancelled`). The first build of the fix hung on this case.

**The fix.**
- `sendOverDTLS(_:to:timeout:)` takes a `timeout` that defaults to 5 s. It runs the send in a task group beside a `Task.sleep(for: timeout)` child.
- The deadline child throws the last `.waiting` reason, which an `OSAllocatedUnfairLock<NWError?>` holds. If there was no `.waiting` state, it throws `NWError.posix(.ETIMEDOUT)`.
- After `group.next()`, the group cancels the other child.
- **OS 26 branch (`sendOverClassicDTLS`):**
  - `withTaskCancellationHandler` wraps the checked continuation, with `onCancel: connection.cancel()`.
  - The send completion is the only resume path. Every other exit cancels the connection, and the probe showed that cancelling calls the completion. So no guard flag is needed, and a comment says why.
  - The state handler records the `.waiting` reason and cancels on `.failed`.
  - A doc comment says to call it through `sendOverDTLS`.
- **OS 27 branch:** `onStateUpdate` records the `.waiting` reason. `try Task.checkCancellation()` runs before `send`, against the framework fault.

**Runtime result for the fixed code** (`f1-probe.log`, send timeout 2 s):

| Peer | Fixed, OS 26 branch | Fixed, OS 27 branch | Verbatim `sendOverDTLS` |
|---|---|---|---|
| unresolvable name | 2.09 s, threw `NoSuchRecord` | 2.12 s, `NoSuchRecord` | 2.01 s, `NoSuchRecord` |
| loopback, no listener | 2.01 s, `ETIMEDOUT` | 2.01 s, `ETIMEDOUT` | not run |
| never answers | 2.01 s, `ETIMEDOUT` | 2.02 s, `ETIMEDOUT` | 2.02 s, `ETIMEDOUT` |
| never answers, task cancelled at 1 s | 1.05 s, `CancellationError` | 1.05 s, `CancellationError` | 1.05 s, `CancellationError` |
| task already cancelled | 0.003 s, `CancellationError` | 0.001 s, `CancellationError` | 0.001 s, `CancellationError` |

- In each OS 26 case the log shows `onCancel: cancel()`, then the completion firing with error 89, then the return: one resume.
- On this macOS 27 machine `#available` takes the OS 27 branch. The OS 26 branch therefore ran two ways: through the instrumented copy, forced onto that branch, and through `sendOverClassicDTLS` called directly (`verbatimClassic`). It never ran on macOS 26.
- Called alone, `verbatimClassic` has no deadline. It timed out in the probe, as expected, and ended at once when cancelled.

**Not runtime-checked**, and the reference says so:
- a send that succeeds, because no DTLS peer was available;
- `.failed`, which never occurred;
- a cancellation that lands between the OS 27 `checkCancellation()` and the send.

**Docs read.** Each page came through the `.md` route, was saved under `$TMP/corpus/final-fix/`, and was loaded in full with Read:
- **Network:** `NWConnection`; `NWConnection.State` and its `waiting(_:)` and `failed(_:)` cases; `stateUpdateHandler`; `cancel()`; `send(content:contentContext:isComplete:completion:)`; `SendCompletion` and `contentProcessed(_:)`; `NWError` and `posix(_:)`; `NetworkConnection`; `withNetworkConnection(to:using:_:)`.
- **Swift:** `withTaskCancellationHandler(operation:onCancel:isolation:)`; `withCheckedThrowingContinuation(isolation:function:_:)`; `withThrowingTaskGroup(of:returning:isolation:body:)`; `ThrowingTaskGroup` with `next(isolation:)` and `cancelAll()`; `Task.sleep(for:tolerance:clock:)`.
- **os:** `OSAllocatedUnfairLock` and `init(initialState:)`.

I also read the shipped `Network.swiftinterface` (arm64e-apple-macos, macOS 27.0 SDK) for `NetworkConnection`, `NetworkChannel.State`, and `onStateUpdate`. `NetworkConnection` has no `cancel()`, so task cancellation is the only way to end its send.

**Deferred item 40** (`docs/deferred.md:1251-1293`) is marked resolved. The Action's task-group sentence now points to a correction paragraph (`:1284-1293`). That paragraph says a group alone hangs on the 3d25847 continuation, because a group waits at scope exit for a child that ignores cancellation. It works now only because both branches end on cancellation, which the probe checked.

**Gates:** Swift 9/9 and C++ 1/1 (`typecheck.log:4-23`). Vale: 0 errors and 14 alerts, before and after.

## F2 (Minor 4): the TouchOverlay ring
- **Changed:** `apple-games/references/input.md:439-441` (the doc comment on `encode(before:)`) and `:462-472` (the prose).
- The prose now says a ring length equal to the frames-in-flight bound is necessary but not sufficient, because the Metal 3 queue is not ordered after the Metal 4 composite.
- It says to call `encode(before:)` once per frame, after that frame's frames-in-flight wait (step 1 of `## Frame structure` in `apple-metal/references/command-model.md`), and before the commit that composites the overlay.
- I did not show the `encodeWaitForEvent` alternative. It needs a Metal 4 completion event that the class does not hold, and the prose route is exact without it.
- **Gates:** Swift 11/11, with block #7 on iOS 26.0 (`typecheck.log:26-39`). Vale: 7 alerts, before and after.

## F3 (Minor 5): `drawFrame` took the drawable before the wait
- **Changed:** `apple-metal/references/command-model.md:344-353`, in the `drawFrame` extension only. It now runs the next frame's frames-in-flight wait before reading `currentDrawable`. The wait is the same `frameEvent.wait(untilSignaledValue:timeoutMS: 1_000)` with the same `gpuTimeout` throw. `encodeFrame`'s own wait then returns at once.
- The `FrameLoop` class block did not change. That block is pasted verbatim into the metal-probe fixture, and splitting the wait out of `encodeFrame` would have made the fixture drift. `check_verbatim.py` still passes 12/12.
- **Gates:** Swift 8/8 and Metal 1/1 (`typecheck.log:42-60`). Vale: 23 alerts, before and after.

## F4 (Minor 6): the release block had no failure guard
- **Changed:** `app-release/references/direct-distribution.md:311-314`, the prose. It now says to save the block as a script and run it with `bash`, because `set -e` closes an interactive shell.
- **Changed:** `:337-373`, the block:
  - It now starts with `#!/bin/bash` and `set -euo pipefail`.
  - Step 4 ends in `|| true`.
  - Step 6 records `submit`'s exit status with `|| SUBMIT_EXIT=$?`, because the help text does not give it for an Invalid result. It then extracts `id`, fetches the log, and extracts `status` with `plutil -extract status raw -o -`.
  - The block exits 1 before stapling unless the status is `Accepted` and `submit` exited 0.
- The P44 marker and the not-runtime-checked comments are kept.
- **Gates:** `bash -n` passed on all 8 shell blocks (`typecheck.log:89-97`). Vale: 4 alerts, before and after.

## F5 (Minor 7): archiving the External Build System target
- **Changed:** `apple-metal/references/cpp-and-rust.md:561-566` and `app-release/references/direct-distribution.md:254-258`.
- Both now say the cargo script does not archive: it handles only an empty action, `build`, and `clean`. They also say no log shows which `ACTION` an archive passes. For a release, build Release, then sign, notarize, and staple by hand.
- I took the prose route, not the `install` route. The `xcode-cargo.sh` block is pasted verbatim into the metal-probe fixture (`rust/xcode-cargo.sh`), and this round must not touch the fixture.
- **Gates:** native 6/6 and `bash -n` 4/4 (`typecheck.log:63-83`).

## F6 (Minor 8): the Team ID sentence
- **Changed:** `direct-distribution.md:58-64`.
- The sentence now says the ID in an `Apple Development` identity name is not the Team ID, and cites `task-10-r6/identity.log`.
- For any identity, it says to read the Team ID from the certificate subject's OU field, and the team name from its O field. The table at `:51-54` is unchanged.

## F7 (Minor 10): the apple-frameworks routing item
- **Changed:** `apple-frameworks/SKILL.md:17-20`. Metal still goes to `apple-metal`. The game frameworks go to `apple-games` "in a game".

## F8 (Minor 2, text half): the floor sentence
- **Changed:** `apple-games/SKILL.md:55-58`. Swift snippets compile at the floor. C++ snippets compile at the host's default target, so the gate does not catch a C++ call below the floor; check each call's availability in its header.
- `apple-metal/SKILL.md` has no such sentence. Its floor lines (59-68) make no claim about the gates.

## D1 to D6: deferred items
Each item uses the existing format, with its cost while open, an Action, and a Trigger, in `authoring/apple-studio/docs/deferred.md`:

| Item | Line | Topic |
|---|---|---|
| D1 → 42 | 1315 | The native gate compiles C++ with no deployment target from `> typecheck:`, and passes on unguarded-availability warnings |
| D2 → 43 | 1332 | `shading-language.md:35-36` claims the unlabelled blocks compile at MSL 4.0, but the gate runs that file at `metal4.1` only |
| D3 → 44 | 1346 | `apple-performance`'s description claims "the render loop" with no exclusion for GPU frame time or frame pacing. A change needs an eval sweep. |
| D4 → 45 | 1360 | `r4_finding` (and `r4_selftest`) do not fail when the slow verdict equals the control's. Item text only, no fixture change. |
| D5 → 46 | 1373 | A new item, an addendum to 39. Only the literal `#if os(` takes the multi-target path. `targetEnvironment(simulator)` branches are never compiled (`apple-gpu-tbdr.md:99`). |
| D6 → 47 | 1392 | P38's reason no longer holds after P50. Decide again whether to wrap iOS-only snippets. |

Vale on `deferred.md`: 0 errors and 91 alerts, before and after.

## Other files and constraints
- `records/2026-10-18-phase10-games/README.md` has a new row for `final-fix/`.
- There is no version bump, no tag, and no SDD-ledger edit.
- The commit holds no Apple ID email address and no text from Apple or the book.
- The probe binary and its build files are in the session scratch directory, not in the repository.

## Concerns
1. **F1 goes past the reviewer's sketch, because the evidence required it.** A state handler cannot bound a DTLS send to a peer that never answers: it stayed in `.preparing` for the full 180 s. So the function now has a `timeout` parameter and a task group. That is the route item 40 first offered and the brief called a hang. It is safe here only because each branch now ends on cancellation, which the probe checked for both branches. The snippet grew from about 16 lines to 64.
2. **The Network framework has a fault on OS 27.** A `NetworkConnection.send` started in an already-cancelled task leaks its continuation and never returns. The `Task.checkCancellation()` before the send handles the case the probe could reproduce. A cancellation that lands between the check and the send was not reproduced, and it is not ruled out. It may be worth a Feedback Assistant report; nothing was sent.
3. **A successful send was never observed.** No DTLS peer was available, so the success path is compiled but not runtime-checked. That covers the completion with `nil` and the OS 27 `send` returning normally. The reference says so.
4. **Bookkeeping:** the controller needs to write `$REC/final-fix/report.md` and `.superpowers/sdd/2026-10-18-phase10-games/final-fix-report.md` from this text (P10), because the harness refused the Write.

## Controller residual fixes after the re-review (P36 size)

The re-review (opus) found every item addressed and four Minor wording faults.
The controller fixed them:

- `game-center-and-online.md`: the group comment no longer says the group
  "never" waits on a stuck send. It points to the OS 27 window, and the text
  after the block now says the deadline does not bound that window. The doc
  comment names the tested case (a name that does not resolve) instead of "no
  route". The pitfall gives the logged durations (180 s preparing, 8 s waiting)
  instead of "minutes".
- `cpp-and-rust.md`: a bare executable is signed and notarized, not stapled.
  To staple, wrap it in an app bundle.
- `input.md`: the frames-in-flight wait proves the slot is free only when a
  Metal 4 frame commits after every `encode(before:)` call.
- This report: 20 short cases, not 23.

The two block edits are comments only. `residuals.log` shows the probed block
(sha256 `7058b6cb…ee54`, the value in both probe logs), the shipped block
(`34dc5dba…369d`), their diff, and "none" for changed lines that are not
comments. It also holds the gates after the edits.
