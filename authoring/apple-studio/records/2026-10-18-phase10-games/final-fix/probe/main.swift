// Phase 10 final fix, F1 probe driver.
//
// usage: dtls-probe <function> <endpoint> <mode> [deadline-seconds]
//   function: original26 | original27 | fixed26 | fixed27 | verbatim | verbatimClassic
//     original26/27    the 3d25847 branches, instrumented
//     fixed26/fixed27  the fixed sendOverDTLS, instrumented, forced to one branch
//     verbatim         the reference's sendOverDTLS (OS 27 branch on macOS 27)
//     verbatimClassic  the reference's sendOverClassicDTLS, with no deadline
//   endpoint: unresolvable | refused | blackhole
//   mode:     plain | cancel-after-1s | precancelled
//
// The probe never waits on the function under test without a deadline. It
// prints RETURNED (with the thrown error, if any) or TIMEOUT, then exits.

import Foundation
import Network
import os

let args = CommandLine.arguments
guard args.count >= 4 else {
    print("usage: dtls-probe <function> <endpoint> <mode> [deadline-seconds]")
    exit(2)
}
let function = args[1], endpointName = args[2], mode = args[3]
let deadline = args.count > 4 ? Double(args[4]) ?? 10 : 10
// The timeout passed to the fixed function. The probe's own deadline is longer.
let sendTimeout: Duration = .seconds(2)

let endpoint: NWEndpoint
switch endpointName {
case "unresolvable":   // .invalid never resolves (RFC 6761)
    endpoint = .hostPort(host: "dtls-probe.invalid", port: 4433)
case "refused":        // loopback, a port nothing listens on
    endpoint = .hostPort(host: "127.0.0.1", port: 9)
case "blackhole":      // TEST-NET-1 (RFC 5737): routed, never answers
    endpoint = .hostPort(host: "192.0.2.1", port: 4433)
default:
    print("unknown endpoint \(endpointName)"); exit(2)
}

let body: @Sendable (Data, NWEndpoint) async throws -> Void
switch function {
case "original26":      body = original26
case "original27":      body = original27
case "fixed26":         body = { try await instrumented($0, to: $1, timeout: sendTimeout, classic: true) }
case "fixed27":         body = { try await instrumented($0, to: $1, timeout: sendTimeout, classic: false) }
case "verbatim":        body = { try await sendOverDTLS($0, to: $1, timeout: sendTimeout) }
case "verbatimClassic": body = {
    try await sendOverClassicDTLS($0, to: $1, lastWait: OSAllocatedUnfairLock<NWError?>(initialState: nil))
}
default: print("unknown function \(function)"); exit(2)
}

print("case: function=\(function) endpoint=\(endpointName) (\(endpoint)) mode=\(mode) probe-deadline=\(deadline)s send-timeout=\(sendTimeout)")
print("os: \(ProcessInfo.processInfo.operatingSystemVersionString)")
probeStart = Date()

let done = DispatchSemaphore(value: 0)
let payload = Data("snapshot".utf8)
// Detached: top-level code is main-actor isolated, and the main thread blocks
// in done.wait below, so an attached Task would never start.
let task = Task.detached {
    if mode == "precancelled" {
        withUnsafeCurrentTask { $0?.cancel() }
        log("task cancelled before the call")
    }
    do {
        try await body(payload, endpoint)
        log("RETURNED without error")
    } catch {
        log("RETURNED, threw: \(error)")
    }
    done.signal()
}
if mode == "cancel-after-1s" {
    DispatchQueue.global().asyncAfter(deadline: .now() + 1) {
        log("cancelling the task")
        task.cancel()
    }
}
if done.wait(timeout: .now() + deadline) == .timedOut {
    log("TIMEOUT: the function did not return within \(deadline) s")
    exit(3)
}
exit(0)
