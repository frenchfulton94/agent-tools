> verified: 2026-08 against https://developer.apple.com/documentation/swiftui/scene, https://developer.apple.com/documentation/swiftui/scenes, https://developer.apple.com/documentation/swiftui/scenephase, https://developer.apple.com/documentation/swiftui/windowgroup, https://developer.apple.com/documentation/swiftui/window, https://developer.apple.com/documentation/swiftui/settings, https://developer.apple.com/documentation/swiftui/settings/init(content:), https://developer.apple.com/documentation/swiftui/settingslink, https://developer.apple.com/documentation/swiftui/opensettingsaction, https://developer.apple.com/documentation/swiftui/windowresizability, https://developer.apple.com/documentation/swiftui/documentgroup, https://developer.apple.com/documentation/swiftui/creating-a-document-based-app, https://developer.apple.com/documentation/swiftui/building-a-document-based-app-with-swiftui, https://developer.apple.com/documentation/swiftui/menubarextra, https://developer.apple.com/documentation/swiftui/menubarextrastyle, https://developer.apple.com/documentation/swiftui/nsapplicationdelegateadaptor, https://developer.apple.com/documentation/appkit/nsapplicationdelegate/applicationshouldterminateafterlastwindowclosed(_:), https://developer.apple.com/documentation/swiftui/navigationview, https://developer.apple.com/documentation/uikit/mac-catalyst
> sources: macOS by Tutorials v1.0.0 (judgment only), live Apple docs

## Choosing a Mac target

Four ways to get an app onto a Mac. Assess against Apple's own bar for a great Mac app — flexible (adapts to mouse/trackpad/keyboard, lets people show/hide/rearrange parts of the UI), familiar (standard menu layout, standard window zones), expansive (works from a small laptop window to a 36" display, multiple windows across multiple screens), precise (denser controls than touch allows) (macOS by Tutorials, ch. 6).

- **Native SwiftUI (or AppKit) target.** The only path that hits all four criteria. Default choice whenever you control the codebase and don't have a hard Windows requirement.
- **iPad app run directly on Apple Silicon.** No project changes; the App Store just allows it. Layout, controls, and interaction model stay iPad-shaped — oversized touch targets, no real menu bar integration. Treat this as a fallback for apps that will never get a Mac-specific pass, not a distribution strategy (macOS by Tutorials, ch. 6).
- **Mac Catalyst.** Check the Mac checkbox on an iPad target's project settings to get a second, Mac-building target from the same UIKit/SwiftUI source (`https://developer.apple.com/documentation/uikit/mac-catalyst`). Apple's own description is just that build checkbox — the tuning work (menu bar content, sizing, idiom-specific layout) is on you afterward. Judgment: worth it only when you already have a substantial iPad app and want a low-effort Mac presence; the out-of-the-box result reads as an iPad app in a Mac window until you invest in Mac-specific polish (macOS by Tutorials, ch. 6).
- **Cross-platform (Electron, web-wrapped, etc.).** Only justified when Windows/Linux parity is a hard requirement — no Apple technology gets you there. Expect a resource-usage and native-feel tax; some apps (VS Code) pull it off well by leaning into consistency across platforms rather than chasing native chrome (macOS by Tutorials, ch. 6).
- **Xcode Multiplatform template.** When you're building for iOS and macOS together, prefer this over Catalyst: one project, shared files plus platform-specific files, two genuinely native targets. You get Catalyst's code reuse without giving up per-platform independence — small/shared views can live in the common code; platform-specific screens (e.g., a Mac sidebar layout vs. an iOS `NavigationStack`) get their own files (macOS by Tutorials, ch. 6).

Code sharing is not one-directional: a Mac app's data models, settings, and data flow are generally portable back to an iOS target too. Don't just reuse the Mac interface on iOS, though — that repeats the "iPad app on a Mac" mistake in reverse.

## Scene types at a glance

An `App`'s `body` is composed of `Scene` values — a `Scene` is a system-managed container for a view hierarchy, and how it's presented (window, menu bar item, tab, full-screen) is platform- and context-dependent (`https://developer.apple.com/documentation/swiftui/scene`, `https://developer.apple.com/documentation/swiftui/scenes`). Pick the scene type by what the content *is*, not by copying an iOS app's `WindowGroup`:

| Scene | Use when | Not when |
|---|---|---|
| `WindowGroup` | Free-form content the user can open in any number of windows | Content is a document (use `DocumentGroup`) or must be a single instance (use `Window`) |
| `Window` | Exactly one instance of a utility/inspector window makes sense | The window should support multiple simultaneous instances |
| `Settings` | Any app with user preferences | Never optional in practice — Mac users expect Cmd-, to work |
| `DocumentGroup` | Content the user creates, saves, and reopens as files | In-app data that isn't file-backed |
| `MenuBarExtra` | Background utility, always-available quick access, or an app with no primary window at all | The functionality genuinely needs a full window-managed experience |

## WindowGroup — the default multi-window scene

```swift
import SwiftUI

@main
struct MailApp: App {
    var body: some Scene {
        WindowGroup {
            MailViewer()
        }
    }
}
```

Each window opened from a `WindowGroup` gets independent `@State`; on macOS the system automatically adds window-management commands and lets users merge windows into tabs (`https://developer.apple.com/documentation/swiftui/windowgroup`). Give the group an `id:` (and optionally a presentation type) to open specific windows programmatically via `@Environment(\.openWindow)` — useful for "open this one item in its own window" flows.

**Window sizing is a Mac-specific decision iOS doesn't force on you.** Constrain a window's size with `.frame(minWidth:idealWidth:maxWidth:minHeight:idealHeight:maxHeight:)`. Set `max` to `.infinity` for a main window unless you have a specific reason to cap it. `min` is the value that matters most — it's the smallest size the window can be resized to, so it must fit your densest useful layout without assuming a particular screen size. `ideal` is only a hint for the window's first-ever size; SwiftUI persists whatever size the user leaves a window at and reapplies it on reopen (macOS by Tutorials, ch. 2).

**Multi-pane sidebar layouts don't work like iOS push navigation.** On iOS you'd reach for `NavigationLink` to drill into a detail view; on a Mac window, all panes are visible simultaneously, so the split view is built with all panes present up front and a `selection` binding decides what the detail pane shows (macOS by Tutorials, ch. 2). The book builds this with `NavigationView`; that type is now deprecated in favor of `NavigationStack`/`NavigationSplitView`, and `NavigationSplitView` is the current, correct choice for a sidebar+detail Mac layout (https://developer.apple.com/documentation/swiftui/navigationview).

## Window — single-instance and single-window apps

```swift
import SwiftUI

@main
struct MailApp: App {
    var body: some Scene {
        WindowGroup {
            MailViewer()
        }
        Window("Connection Doctor", id: "connection-doctor") {
            ConnectionDoctor()
        }
    }
}
```

`Window` gives a title as its first initializer argument and a stable `id:` you match against when opening it via `openWindow(id:)`; if it's already open, that call brings it to the front instead of duplicating it (`https://developer.apple.com/documentation/swiftui/window`). Use `Window` for secondary singleton panels (an inspector, a connection-status panel), and reach for it as an app's *only* scene when multi-window behavior is actively wrong for the app (e.g., a video-call app tied to one camera).

That last case has a lifecycle consequence worth internalizing: **an app whose primary scene is `Window` quits when that window closes.** An app whose primary scene is `WindowGroup` keeps running after every window closes — this is the opposite of the iOS mental model, where the app process and its foreground UI are tightly coupled (`https://developer.apple.com/documentation/swiftui/window`).

## Settings — the Preferences window

```swift
import SwiftUI

@main
struct OnThisDayApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        Settings {
            SettingsView()
        }
    }
}

struct ContentView: View {
    var body: some View {
        Text("Main window")
    }
}

struct SettingsView: View {
    var body: some View {
        TabView {
            Tab("General", systemImage: "gear") {
                GeneralSettingsView()
            }
            Tab("Advanced", systemImage: "star") {
                AdvancedSettingsView()
            }
        }
        .scenePadding()
        .frame(maxWidth: 350, minHeight: 100)
    }
}

struct GeneralSettingsView: View {
    @AppStorage("showPreview") private var showPreview = true

    var body: some View {
        Form {
            Toggle("Show Previews", isOn: $showPreview)
        }
    }
}

struct AdvancedSettingsView: View {
    var body: some View {
        Form {
            Text("Advanced settings go here.")
        }
    }
}
```

Adding a `Settings` scene is what turns on the app menu's *Settings…* item and its Cmd-, shortcut; SwiftUI owns showing/dismissing the window (`https://developer.apple.com/documentation/swiftui/settings`). Bind settings controls straight to `@AppStorage` — that's the whole mechanism, no separate persistence layer needed. When a settings surface grows past one screen's worth of controls, Apple's own current sample groups it with `TabView` and `Tab(_:systemImage:) { }` (the current view-builder form; the book's older `.tabItem { Image(...); Text(...) }` modifier pattern still exists but this is the form to reach for now). The `Tab(_:systemImage:content:)` view-builder form requires a macOS 15.0+ deployment target — on an older target, use `.tabItem { }` instead (both forms verified with `swiftc -typecheck -parse-as-library`).

`Settings` has exactly one initializer (`init(content:)`) with no `id:` or data parameter — unlike `WindowGroup`/`Window`, there is no API surface for opening a second instance, so the single-Preferences-window behavior the book describes is guaranteed by the type's shape, not a runtime convention you have to preserve yourself (https://developer.apple.com/documentation/swiftui/settings/init(content:)). Constrain the settings window's size the same way you would any window — via `.frame(...)`, and via the `.windowResizability(.contentSize)` scene modifier if you want it to strictly track content size rather than being freely resizable; a size-constrained settings window is a deliberate, common pattern (https://developer.apple.com/documentation/swiftui/windowresizability) (macOS by Tutorials, ch. 5).

Two design calls worth keeping as fixed rules, not per-app judgment calls: use **checkboxes** (`Toggle`) when the user may pick any/all/none of a set, and **radio buttons** (`Picker` with `.pickerStyle(.radioGroup)`) only when exactly one choice from a fixed set is required (macOS by Tutorials, ch. 5). And it's normal, not redundant, for the same setting to be reachable both from a menu item with a keyboard shortcut *and* from the Settings window — the menu gives fast access to a handful of common toggles, Settings is the single place that gathers everything (macOS by Tutorials, ch. 5).

To open Settings programmatically (e.g., from inside a `MenuBarExtra`, where there's no app menu to click), use `SettingsLink` as a button-like view or call the `openSettings` environment action (`https://developer.apple.com/documentation/swiftui/settingslink`, `https://developer.apple.com/documentation/swiftui/opensettingsaction`).

## DocumentGroup — document-based apps

```swift
import SwiftUI
import UniformTypeIdentifiers

@main
struct MarkDownerApp: App {
    var body: some Scene {
        DocumentGroup(newDocument: MarkdownFile()) { file in
            ContentView(document: file.$document)
        }
    }
}
```

The mental model: one document per window, opened/saved/created through file-coordinated infrastructure SwiftUI manages for you — autosave, conflict handling, the standard File menu commands (`https://developer.apple.com/documentation/swiftui/documentgroup`, matches macOS by Tutorials, ch. 10). Conform your model to `FileDocument` (value type, in-memory whole-file read/write — the common case) or `ReferenceFileDocument` (reference type, for large or incrementally-edited content); both need `readableContentTypes`/`writableContentTypes` `UTType` arrays and the corresponding read/write methods (`https://developer.apple.com/documentation/swiftui/building-a-document-based-app-with-swiftui`). Newer replacement worth knowing about but not defaulting to yet: the `Document` protocol (combining `ReadableDocument`/`WritableDocument`, with direct file-URL access and async snapshot-based reader/writer types) is available as of the current OS cycle and is the better fit once you need direct URL access for frameworks like Core Graphics/AVFoundation or want package-style (directory) documents (`https://developer.apple.com/documentation/swiftui/creating-a-document-based-app`).

**What makes a file "yours to open" is entirely UTI-driven, not code.** Declare a Uniform Type Identifier, what standard type it conforms to, and its file extension(s) in the target's Info settings (Document Types / Imported/Exported Type Identifiers). That's what makes Finder's "Open With" list include your app and what makes double-click resolve to it — there's no runtime registration call (macOS by Tutorials, ch. 10; `https://developer.apple.com/documentation/swiftui/creating-a-document-based-app`). If more than one `DocumentGroup` in your app could match a file, SwiftUI checks them top to bottom in declaration order, so put more specific types before broader ones.

`DocumentGroup(viewing:)` gives you a read-only variant (viewer apps); multiple `DocumentGroup` scenes in one `body` support multiple document types in the same app.

## MenuBarExtra — menu-bar-only and menu-bar-plus apps

```swift
import SwiftUI

@main
struct UtilityApp: App {
    var body: some Scene {
        MenuBarExtra("Utility App", systemImage: "hammer") {
            AppMenu()
        }
    }
}

struct AppMenu: View {
    var body: some View {
        Button("Quit") {
            NSApplication.shared.terminate(nil)
        }
        .keyboardShortcut("q")
    }
}
```

This is the current SwiftUI-native way to live in the menu bar — it supersedes the book's approach of hand-rolling an AppKit `NSStatusItem` (see below) (`https://developer.apple.com/documentation/swiftui/menubarextra`). Two shapes:

- **Menu-bar-only app**, as above: `MenuBarExtra` is the app's only scene. Apple's own docs are explicit that removing the item from the menu bar auto-terminates the app (`https://developer.apple.com/documentation/swiftui/menubarextra`) — which is why this file's judgment is to not combine it with other scene types when it's acting as the app's primary scene. If such an app also needs Settings, reach it via `SettingsLink`/`openSettings` from inside the extra's content rather than adding a sibling `Settings` scene at the top level.
- **App-plus-menu-bar-extra**: pair `MenuBarExtra` with a `WindowGroup` (and optionally `Settings`) for an app that has a normal window *and* menu bar quick-access. Add `isInserted:` (a `Binding<Bool>`, typically backed by `@AppStorage`) so the user can toggle the menu bar item on/off without quitting the app.

For richer content than a simple pull-down menu, apply `.menuBarExtraStyle(.window)` to get a popover-style panel that can host arbitrary SwiftUI content (scroll views, grids, controls); `.menu` (the default alongside `.automatic`) renders as a standard pull-down menu (`https://developer.apple.com/documentation/swiftui/menubarextrastyle`). For a menu-bar-only app that shouldn't appear in the Dock or app switcher, set `LSUIElement` (Application is agent) to `YES` in Info.plist — this is the same plist flag the book sets by hand for its AppKit-based menu bar app, and it applies equally to a SwiftUI `MenuBarExtra`-only app (macOS by Tutorials, ch. 7).

### Maintaining older code: AppKit status-bar apps

Pre-`MenuBarExtra` (and still relevant in AppKit-lifecycle apps), a menu bar app is built by: deleting the window/view-controller scenes and unwanted menus from the storyboard, creating an `NSStatusItem` via `NSStatusBar.system.statusItem(withLength:)` in `applicationDidFinishLaunching(_:)`, assigning it a button image/title and an `NSMenu`, and setting `LSUIElement` in Info.plist (macOS by Tutorials, ch. 7). If you're not maintaining an existing AppKit app, use `MenuBarExtra` instead — it's a direct, less code-heavy replacement for this whole pattern.

## Mac app lifecycle vs iOS habits

- **App-wide `ScenePhase` is coarser than a single scene's, and Mac usage patterns rarely surface `.background`.** Read `@Environment(\.scenePhase)` inside an `App` and you get an aggregate: `.active` if *any* scene is active, `.background` only once *none* are. Apple's own guidance treats entering `.background` as a signal the app is about to terminate soon after, not as a routine suspend/resume event the way iOS backgrounding is — don't port iOS "did enter background, save state" habits onto per-window Mac behavior without checking which level you're reading the phase at (`https://developer.apple.com/documentation/swiftui/scenephase`).
- **Windows close without the app dying — that's the default, not an edge case.** A `WindowGroup`-rooted app keeps running with zero open windows (menu bar and Dock icon remain); only a `Window`-rooted (single-window) app quits when its one window closes (`https://developer.apple.com/documentation/swiftui/window`). Design for "no windows open, app still alive" as a real, common state rather than something to special-case.
- **Apps can live with no window at all**, indefinitely — that's the whole `MenuBarExtra`-only shape, and it's a first-class app category on macOS with no iOS equivalent.
- **Termination is a policy decision, not automatic.** If you need to hook lifecycle events AppKit-side (e.g., customizing what happens when the last window closes, or handling remote notifications), bridge in an `NSApplicationDelegate` via `@NSApplicationDelegateAdaptor` in your `App` — declare it exactly once, and if the delegate conforms to `ObservableObject` it's placed in the environment automatically (https://developer.apple.com/documentation/swiftui/nsapplicationdelegateadaptor). The specific hook for overriding "quit after last window closes" is confirmed: `applicationShouldTerminateAfterLastWindowClosed(_:)` — return `true` to allow termination, `false` to keep the app running with no windows open (https://developer.apple.com/documentation/appkit/nsapplicationdelegate/applicationshouldterminateafterlastwindowclosed(_:)).
