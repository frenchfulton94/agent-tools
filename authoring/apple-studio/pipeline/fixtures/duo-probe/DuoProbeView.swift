import SwiftUI
import os

private let probeLog = Logger(subsystem: "dev.frenchfultonjr.duoprobe", category: "probe")

/// Phase 9 runtime probe. Each label names the claim it checks; the unified
/// log carries the same values so a pose change is recorded even without a
/// screenshot.
///
/// `simctl` cannot tap, so two launch arguments reach the sheet states from
/// the command line: `-DuoProbeOpenSheet` presents the sheet at launch, and
/// `-DuoProbeSheetDisabled` also starts its toggle on.
///
/// Fix round 1 (R7) adds two toolbar variants for the `visibilityPriority`
/// check, selected by launch argument:
/// - `-DuoProbePriority`: MessageDetail's setup (`.secondaryAction` Reply
///   `.high`, Flag `.low`) plus a `.primaryAction` pair, P-Low `.low` declared
///   first and P-High `.high` declared last, with ten extra `.primaryAction`
///   items between them so the bar must overflow.
/// - `-DuoProbePriorityControl`: the same items, every priority `.automatic`.
/// - `-DuoProbeMessageDetail`: the toolbar of adaptive-layout.md's original
///   MessageDetail snippet (Close, Done, `.secondaryAction` Reply `.high` and
///   Flag `.low`, Print in `ToolbarOverflowMenu`), with room to spare in the bar.
/// With no variant argument the toolbar is the R2 re-probe toolbar.
struct DuoProbeView: View {
    @Environment(\.toolbarVerticalEdge) private var barEdge
    @Environment(\.horizontalSizeClass) private var widthClass
    @State private var showSheet = ProcessInfo.processInfo.arguments.contains("-DuoProbeOpenSheet")

    var body: some View {
        NavigationStack {
            GeometryReader { proxy in
                let divisions = proxy.reservedRegions(kind: .division, options: .includeInactive)
                let active = divisions.map(\.isActive)
                // R5: the same query with default options. The docs say it returns
                // regions whether or not they are active; the header's
                // `includeInactive` option implies the default omits inactive ones.
                let defaultDivisions = proxy.reservedRegions(kind: .division)
                let defaultActive = defaultDivisions.map(\.isActive)
                VStack(alignment: .leading, spacing: 12) {
                    Text("R1 toolbarVerticalEdge: \(String(describing: barEdge))")
                    Text("width class: \(String(describing: widthClass))  size: \(Int(proxy.size.width))×\(Int(proxy.size.height))")
                    Text("R3 divisions: \(divisions.count)  active: \(active.description)")
                    Text("R5 default query: \(defaultDivisions.count)  active: \(defaultActive.description)")
                    Button("R4 open sheet") { showSheet = true }
                }
                .padding()
                .onChange(of: active, initial: true) { _, value in
                    probeLog.log("R3 active=\(value.description, privacy: .public) count=\(divisions.count)")
                }
                .onChange(of: defaultActive, initial: true) { _, value in
                    probeLog.log("R5 default active=\(value.description, privacy: .public) count=\(defaultDivisions.count) includeInactive count=\(divisions.count)")
                }
                .onChange(of: String(describing: barEdge), initial: true) { _, value in
                    probeLog.log("R1 edge=\(value, privacy: .public) size=\(Int(proxy.size.width))x\(Int(proxy.size.height))")
                }
            }
            .navigationTitle("Duo probe")
            .toolbar {
                if ProcessInfo.processInfo.arguments.contains("-DuoProbeMessageDetail") {
                    MessageDetailToolbar()
                } else if let usePriorities = PriorityProbe.mode {
                    PriorityProbe(usePriorities: usePriorities)
                } else {
                    R2Toolbar()
                }
            }
        }
        .sheet(isPresented: $showSheet) { SheetProbe() }
    }
}

/// The R2 re-probe toolbar (the default with no variant argument).
private struct R2Toolbar: ToolbarContent {
    var body: some ToolbarContent {
        ToolbarItem(placement: .primaryAction) {
            Button("Share", systemImage: "square.and.arrow.up") {}
        }
        // R2 items use `.primaryAction`. As `.secondaryAction` (the first
        // walk) both items went to the overflow menu with or without an
        // icon, which hid the icon-versus-title difference R2 checks.
        ToolbarItem(placement: .primaryAction) {
            Button("R2 TitleOnly") {}
        }
        ToolbarItem(placement: .primaryAction) {
            Button("R2 WithIcon", systemImage: "star") {}
        }
    }
}

/// R7: does `visibilityPriority` change what stays in the vertical bar?
private struct PriorityProbe: ToolbarContent {
    /// `true` for `-DuoProbePriority`, `false` for `-DuoProbePriorityControl`,
    /// `nil` when neither argument is present.
    static var mode: Bool? {
        let arguments = ProcessInfo.processInfo.arguments
        if arguments.contains("-DuoProbePriority") { return true }
        if arguments.contains("-DuoProbePriorityControl") { return false }
        return nil
    }

    let usePriorities: Bool

    private func priority(_ value: ToolbarItemVisibilityPriority) -> ToolbarItemVisibilityPriority {
        usePriorities ? value : .automatic
    }

    var body: some ToolbarContent {
        ToolbarItem(placement: .primaryAction) {
            Button("P-Low", systemImage: "tortoise") {}
        }
        .visibilityPriority(priority(.low))
        ForEach(1...10, id: \.self) { index in
            ToolbarItem(placement: .primaryAction) {
                Button("Extra \(index)", systemImage: "\(index).circle") {}
            }
        }
        ToolbarItem(placement: .primaryAction) {
            Button("P-High", systemImage: "hare") {}
        }
        .visibilityPriority(priority(.high))
        ToolbarItem(placement: .secondaryAction) {
            Button("Reply", systemImage: "arrowshape.turn.up.left") {}
        }
        .visibilityPriority(priority(.high))
        ToolbarItem(placement: .secondaryAction) {
            Button("Flag", systemImage: "flag") {}
        }
        .visibilityPriority(priority(.low))
    }
}

private struct SheetProbe: View {
    @State private var disableVertical = ProcessInfo.processInfo.arguments.contains("-DuoProbeSheetDisabled")
    @Environment(\.toolbarVerticalEdge) private var barEdge

    var body: some View {
        NavigationStack {
            Form {
                Text("R4 sheet toolbarVerticalEdge: \(String(describing: barEdge))")
                SheetEdgeInside(disabled: disableVertical)
                Toggle("toolbarVerticalBehavior(.disabled)", isOn: $disableVertical)
            }
            .navigationTitle("Sheet")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done", systemImage: "checkmark") {}
                }
            }
            .toolbarVerticalBehavior(disableVertical ? .disabled : .automatic)
        }
        .onChange(of: String(describing: barEdge), initial: true) { _, value in
            probeLog.log("R4 sheet edge=\(value, privacy: .public) (read above toolbarVerticalBehavior)")
        }
    }
}

/// Reads the edge below `toolbarVerticalBehavior`, where the modifier applies.
private struct SheetEdgeInside: View {
    let disabled: Bool
    @Environment(\.toolbarVerticalEdge) private var barEdge

    var body: some View {
        Text("R4 edge inside behavior modifier: \(String(describing: barEdge))")
            .onChange(of: "\(String(describing: barEdge)) disabled=\(disabled)", initial: true) { _, value in
                probeLog.log("R4 sheet inside edge=\(value, privacy: .public)")
            }
    }
}

/// R7: the original MessageDetail snippet's toolbar, unchanged.
private struct MessageDetailToolbar: ToolbarContent {
    var body: some ToolbarContent {
        ToolbarItem(placement: .cancellationAction) {
            Button("Close", systemImage: "xmark") {}
        }
        ToolbarItem(placement: .topBarPinnedTrailing) {
            Button("Done", systemImage: "checkmark") {}
        }
        ToolbarItem(placement: .secondaryAction) {
            Button("Reply", systemImage: "arrowshape.turn.up.left") {}
        }
        .visibilityPriority(.high)
        ToolbarItem(placement: .secondaryAction) {
            Button("Flag", systemImage: "flag") {}
        }
        .visibilityPriority(.low)
        ToolbarOverflowMenu {
            Button("Print", systemImage: "printer") {}
        }
    }
}
