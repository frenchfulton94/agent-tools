// Reads the power and thermal signals a game loop adapts to, from an
// unentitled command-line process. Prints values only; changes nothing.
//
// Build: swiftc -O power_state.swift -o power_state
// Run:   ./power_state
import Foundation
import Metal

let info = ProcessInfo.processInfo
print("thermalState=\(info.thermalState.rawValue) (0 nominal, 1 fair, 2 serious, 3 critical)")
print("isLowPowerModeEnabled=\(info.isLowPowerModeEnabled)")
print("hasPerformanceProfile(.default)=\(info.hasPerformanceProfile(.default))")
print("hasPerformanceProfile(.sustained)=\(info.hasPerformanceProfile(.sustained))")
print("isDeviceCertified(for: .iPhonePerformanceGaming)=\(info.isDeviceCertified(for: .iPhonePerformanceGaming))")
