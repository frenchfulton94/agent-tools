// Does Foundation's Thread.qualityOfService, set before start(), reach the
// thread as its QoS class? And what does a plain Thread get?
//
// Build: swiftc -O thread_qos.swift -o thread_qos
// Run:   ./thread_qos
import Foundation

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

final class Probe: Thread {
    let label: String
    let done = DispatchSemaphore(value: 0)
    init(label: String) { self.label = label; super.init() }
    override func main() {
        print("\(label): qos_class_self=\(qosName(qos_class_self())) Thread.qualityOfService.rawValue=\(qualityOfService.rawValue)")
        done.signal()
    }
}

let plain = Probe(label: "Thread, no QoS set")
plain.start(); plain.done.wait()

let ui = Probe(label: "Thread, qualityOfService = .userInteractive before start")
ui.qualityOfService = .userInteractive
ui.start(); ui.done.wait()

let util = Probe(label: "Thread, qualityOfService = .utility before start")
util.qualityOfService = .utility
util.start(); util.done.wait()
