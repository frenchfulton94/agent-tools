// Which thread, at which QoS, runs a Metal 3 command buffer's completed
// handler, compared with the thread that committed it. The frames-in-flight
// DispatchSemaphore pattern signals from that handler, and Apple's
// priority-inversion rule compares the waiter's QoS with the signaler's.
//
// Build: swiftc -O completion_qos.swift -o completion_qos
// Run:   ./completion_qos
import Foundation
import Metal

func qosName(_ q: qos_class_t) -> String {
    switch q {
    case QOS_CLASS_USER_INTERACTIVE: return "userInteractive"
    case QOS_CLASS_USER_INITIATED: return "userInitiated"
    case QOS_CLASS_DEFAULT: return "default"
    case QOS_CLASS_UTILITY: return "utility"
    case QOS_CLASS_BACKGROUND: return "background"
    case QOS_CLASS_UNSPECIFIED: return "unspecified"
    default: return "raw(\(q.rawValue))"
    }
}

func describeCurrentThread() -> String {
    var name = [CChar](repeating: 0, count: 64)
    pthread_getname_np(pthread_self(), &name, name.count)
    let label = String(cString: __dispatch_queue_get_label(nil))
    return "main=\(Thread.isMainThread) qos=\(qosName(qos_class_self())) " +
        "pthread_name='\(String(cString: name))' queue_label='\(label)'"
}

guard let device = MTLCreateSystemDefaultDevice(),
      let queue = device.makeCommandQueue() else {
    print("no Metal device")
    exit(1)
}
print("device=\(device.name)")

let rounds = 5
for committerQoS in [DispatchQoS.QoSClass.userInteractive, .utility] {
    for round in 0..<rounds {
        let done = DispatchSemaphore(value: 0)
        DispatchQueue.global(qos: committerQoS).async {
            print("[\(committerQoS) round \(round)] commit:  \(describeCurrentThread())")
            guard let commandBuffer = queue.makeCommandBuffer() else { exit(1) }
            commandBuffer.addCompletedHandler { _ in
                print("[\(committerQoS) round \(round)] handler: \(describeCurrentThread())")
                done.signal()
            }
            commandBuffer.commit()
        }
        done.wait()
    }
}
print("finished")
