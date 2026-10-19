// What Core Haptics reports for the Mac's own hardware.
// Build: swiftc -O haptics_caps.swift -o /tmp/.../haptics_caps
import CoreHaptics

let caps = CHHapticEngine.capabilitiesForHardware()
print("supportsHaptics=\(caps.supportsHaptics) supportsAudio=\(caps.supportsAudio)")

do {
    let engine = try CHHapticEngine()
    print("CHHapticEngine() created: \(engine)")
} catch let error as CHHapticError {
    print("CHHapticEngine() threw CHHapticError code=\(error.code.rawValue) (\(error.code))")
} catch {
    print("CHHapticEngine() threw \(error)")
}
print("CHHapticErrorCode.notSupported rawValue=\(CHHapticError.Code.notSupported.rawValue)")
