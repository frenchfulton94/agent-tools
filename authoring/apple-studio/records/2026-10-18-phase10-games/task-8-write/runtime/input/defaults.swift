// Runtime check for input.md: GameController defaults on macOS.
// Build: swiftc -target arm64-apple-macos26.0 defaults.swift -o /tmp/<dir>/defaults
// Prints the default of GCController.shouldMonitorBackgroundEvents for a binary
// linked against the installed SDK, and the Swift spelling of the unmapped
// live-input property (compile-time check: this file does not build if the
// spelling is wrong). Exits at once; starts no run loop and leaves no process.
import Foundation
import GameController

print("shouldMonitorBackgroundEvents default:", GCController.shouldMonitorBackgroundEvents)

// Never called; present so the compiler resolves the spelling.
func unmappedSpelling(_ controller: GCController) -> GCControllerLiveInput? {
    controller.input.unmapped
}
