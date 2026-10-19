// Phase 10 final fix, F1. Instrumented copies of sendOverDTLS.
//
// `original26` and `original27` are the two branches as they shipped at
// d742a42, with a state logger added. `instrumented` is the fixed sendOverDTLS from
// game-center-and-online.md with log lines added; `classic: true` forces its
// OS 26 branch, which this macOS 27 machine would otherwise never take.
// run.sh also compiles the reference's block verbatim, and main.swift drives
// it through the `verbatim*` functions; this file only adds logging.

import Foundation
import Network
import os

func probeParameters() -> NWParameters {
    NWParameters(dtls: NWProtocolTLS.Options(), udp: NWProtocolUDP.Options())
}

nonisolated(unsafe) var probeStart = Date()

func log(_ message: String) {
    let t = String(format: "%7.3f", Date().timeIntervalSince(probeStart))
    print("[\(t)s] \(message)")
    fflush(stdout)
}

// The OS 26 branch at d742a42, with a state logger only.
func original26(_ payload: Data, to endpoint: NWEndpoint) async throws {
    let connection = NWConnection(to: endpoint, using: probeParameters())
    connection.stateUpdateHandler = { state in log("state: \(state)") }
    connection.start(queue: .global(qos: .userInitiated))
    defer { connection.cancel() }
    try await withCheckedThrowingContinuation { (sent: CheckedContinuation<Void, any Error>) in
        connection.send(content: payload, completion: .contentProcessed { error in
            log("send completion fired, error: \(String(describing: error))")
            if let error { sent.resume(throwing: error) } else { sent.resume() }
        })
    }
}

// The OS 27 branch at d742a42, with a state logger only.
func original27(_ payload: Data, to endpoint: NWEndpoint) async throws {
    if #available(macOS 27, iOS 27, *) {
        try await withNetworkConnection(to: endpoint, using: { DTLS() }) { connection in
            connection.onStateUpdate { _, state in log("state: \(state)") }
            log("send enqueued")
            try await connection.send(payload)
            log("send returned")
        }
    }
}

// The fixed sendOverDTLS, with log lines.
func instrumented(_ payload: Data, to endpoint: NWEndpoint,
                  timeout: Duration, classic: Bool) async throws {
    let lastWait = OSAllocatedUnfairLock<NWError?>(initialState: nil)
    try await withThrowingTaskGroup(of: Void.self) { group in
        group.addTask {
            defer { log("send child ended") }
            if #available(macOS 27, iOS 27, *), !classic {
                try await withNetworkConnection(to: endpoint, using: { DTLS() }) { connection in
                    connection.onStateUpdate { _, state in
                        log("state: \(state)")
                        if case .waiting(let error) = state { lastWait.withLock { $0 = error } }
                    }
                    try Task.checkCancellation()
                    log("send enqueued (OS 27 branch)")
                    try await connection.send(payload)
                    log("send returned")
                }
            } else {
                try await instrumentedClassic(payload, to: endpoint, lastWait: lastWait)
            }
        }
        group.addTask {
            defer { log("deadline child ended") }
            try await Task.sleep(for: timeout)
            log("deadline reached")
            throw lastWait.withLock { $0 } ?? NWError.posix(.ETIMEDOUT)
        }
        _ = try await group.next()
        group.cancelAll()
    }
}

func instrumentedClassic(_ payload: Data, to endpoint: NWEndpoint,
                         lastWait: OSAllocatedUnfairLock<NWError?>) async throws {
    let connection = NWConnection(to: endpoint, using: probeParameters())
    connection.stateUpdateHandler = { [weak connection] state in
        log("state: \(state)")
        switch state {
        case .waiting(let error):
            lastWait.withLock { $0 = error }
        case .failed:
            log("state handler: cancel()")
            connection?.cancel()
        default:
            break
        }
    }
    connection.start(queue: .global(qos: .userInitiated))
    defer { connection.cancel() }
    try await withTaskCancellationHandler {
        try await withCheckedThrowingContinuation { (sent: CheckedContinuation<Void, any Error>) in
            log("send enqueued (OS 26 branch)")
            connection.send(content: payload, completion: .contentProcessed { error in
                log("send completion fired, error: \(String(describing: error))")
                if let error { sent.resume(throwing: error) } else { sent.resume() }
            })
        }
    } onCancel: {
        log("onCancel: cancel()")
        connection.cancel()
    }
}
