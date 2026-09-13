> verified: 2026-08 against https://developer.apple.com/documentation/swiftui/windows, https://developer.apple.com/documentation/swiftui/customizing-window-styles-and-state-restoration-behavior-in-macos, https://developer.apple.com/documentation/swiftui/scenerestorationbehavior, https://developer.apple.com/documentation/swiftui/scenelaunchbehavior, https://developer.apple.com/documentation/swiftui/openwindowaction, https://developer.apple.com/documentation/swiftui/dismisswindowaction, https://developer.apple.com/documentation/swiftui/windowresizability, https://developer.apple.com/documentation/swiftui/scenestorage/init(_:), https://developer.apple.com/documentation/swiftui/commands, https://developer.apple.com/documentation/swiftui/commandgroup, https://developer.apple.com/documentation/swiftui/commandgroupplacement, https://developer.apple.com/documentation/swiftui/commandmenu, https://developer.apple.com/documentation/swiftui/toolbars, https://developer.apple.com/documentation/swiftui/toolbaritem, https://developer.apple.com/documentation/swiftui/toolbaritemgroup, https://developer.apple.com/documentation/swiftui/toolbaritemplacement, https://developer.apple.com/documentation/swiftui/customizabletoolbarcontent, https://developer.apple.com/documentation/swiftui/view/searchable(text:placement:prompt:), https://developer.apple.com/documentation/swiftui/view/keyboardshortcut(_:modifiers:), https://developer.apple.com/documentation/swiftui/eventmodifiers/all, https://developer.apple.com/documentation/swiftui/focusstate, https://developer.apple.com/documentation/swiftui/focusedbinding, https://developer.apple.com/documentation/swiftui/resetfocusaction
> sources: macOS by Tutorials v1.0.0 (judgment only), live Apple docs

## Window management and restoration

### Scene types

Three scene types create windows:

- `WindowGroup` — multi-instance. The system can spawn any number of windows from one declaration, each with independent view state even when they share an `@EnvironmentObject`.
- `Window` — single-instance. Use when a scene should never have more than one window.
- `UtilityWindow` — an auxiliary window (tool palette / inspector), with behavior you don't get from `Window` and shouldn't hand-roll.

See [Windows](https://developer.apple.com/documentation/swiftui/windows).

`UtilityWindow` specifics worth knowing before reaching for a plain `Window` plus manual visibility state:

- Receives focused values from whichever main scene currently has focus, so an inspector can reflect the active document without its own window-tracking code.
- Defaults to a floating window level, so it stays visible while focus moves between main windows.
- Hides automatically when the app is inactive; not minimizable.
- Dismisses on Escape when focused.
- SwiftUI auto-adds a show/hide toggle to the View menu — suppress that with `.windowManagerRole(_:)` if you're placing your own menu item instead.

### Window titles and per-window state

Each window in a `WindowGroup` needs its own distinguishable title. The Window menu lists every open window by title, and if they're all identical (e.g. all showing the app name because they share environment state), the user can't tell them apart. Derive the title from per-window selection state and apply it with `.navigationTitle(_:)` (macOS by Tutorials, ch. 2).

**What restores for free vs. what you own:**

- The system persists window frame (position/size) automatically when restoration is enabled — nothing to do for that.
- Your view's *data* state is not saved automatically. `@AppStorage` is app-wide (one value shared across every window); for state that belongs to one specific window — selected item, scroll position, search text, view mode — use `@SceneStorage` instead. Same declaration syntax as `@AppStorage`, but `UserDefaults`-backed per-window (macOS by Tutorials, ch. 4).

Confirmed for the `Optional`-`Bool` case: `SceneStorage`'s no-default initializer (`init(_:)`, constrained `where Value == Bool?`) takes no `wrappedValue` parameter at all — unlike the non-Optional initializer, there's no overload that lets an Optional-typed `@SceneStorage` property carry a default value at declaration. Set the initial value in `.onAppear` instead, matching the book's pattern for a nil-defaulted selection (https://developer.apple.com/documentation/swiftui/scenestorage/init(_:)).

### Restoration and launch behavior

Restoration is opt-out at the system level (System Settings) — your app respects that global preference unless you override it per-scene:

- `.restorationBehavior(_:)` scene modifier, taking `SceneRestorationBehavior`: `.automatic` (respect the system setting — default) or `.disabled` (never restore this scene). Reach for `.disabled` on windows representing transient or expensive-to-reconstruct activity.
- `.defaultLaunchBehavior(_:)`, taking `SceneLaunchBehavior`: `.automatic`, `.presented` (show even when nothing was restored), `.suppressed` (don't auto-present at launch). Use for scenes like a welcome window that should only appear when there's no prior session to restore.

See [Customizing window styles and state-restoration behavior in macOS](https://developer.apple.com/documentation/swiftui/customizing-window-styles-and-state-restoration-behavior-in-macos), [`SceneRestorationBehavior`](https://developer.apple.com/documentation/swiftui/scenerestorationbehavior), [`SceneLaunchBehavior`](https://developer.apple.com/documentation/swiftui/scenelaunchbehavior).

### Opening, closing, sizing

Open/close windows programmatically via the `openWindow`/`dismissWindow` environment actions (`OpenWindowAction`/`DismissWindowAction`) — not AppKit. Target a scene by string `id`, by a `Data`-conforming value matching the scene's initializer type, or both (multiple `WindowGroup`s taking the same value type, disambiguated by id). If a window presenting that value already exists, the system brings it forward instead of duplicating it. See [`OpenWindowAction`](https://developer.apple.com/documentation/swiftui/openwindowaction), [`DismissWindowAction`](https://developer.apple.com/documentation/swiftui/dismisswindowaction).

Control resizing with `.windowResizability(_:)` (`WindowResizability`):

- `.automatic` — default.
- `.contentSize` — window bounds track the content's ideal/fixed size exactly.
- `.contentMinSize` — content's minimum size becomes the window's minimum.

See [`WindowResizability`](https://developer.apple.com/documentation/swiftui/windowresizability).

### Flattened/edge-to-edge toolbars

When flattening a toolbar for an immersive or edge-to-edge window:

- `.toolbarVisibility(_:for:)` removes it entirely.
- `.toolbarBackgroundVisibility(_:for:)` removes only the background (keeps title/controls).

Both are visual-only — the system still reports the window's title to accessibility tools, and the Window menu keeps showing it. If you remove or flatten the toolbar, restore draggability with `WindowDragGesture` on an overlay, and pair it with `.allowsWindowActivationEvents(_:)` so the click that activates a background window also passes through to that gesture. See [Customizing window styles and state-restoration behavior in macOS](https://developer.apple.com/documentation/swiftui/customizing-window-styles-and-state-restoration-behavior-in-macos).

## Commands, CommandMenu, CommandGroup

### Structure

`Commands` is a protocol, structurally parallel to `View`/`Scene` — a conforming type's `body` assembles menu content and attaches to a scene via `.commands { }` on a `WindowGroup`/`Window`, never on a leaf view. Keep menu declarations in their own file rather than inline in the App struct; the whole menu tree updates automatically as the `Commands` type's `body` changes (macOS by Tutorials, ch. 3).

**Concurrency:** a type conforming to `Commands` inherits `@MainActor` isolation *if the conformance is declared in the type's base declaration* — the common case. Declare the conformance in an `extension` instead if you need to opt out of main-actor isolation. See [`Commands`](https://developer.apple.com/documentation/swiftui/commands).

### Prebuilt vs. custom

Prefer prebuilt command groups over hand-rolled ones whenever they fit. They follow HIG placement automatically, are already localized, and need no manual action-wiring — but you get zero control over where the system inserts them. Reach for a custom `CommandGroup`/`CommandMenu` only when you need placement control or app-specific actions.

Current full set of prebuilt `Commands`-conforming types, confirmed against `Commands`' own Conforming Types list (https://developer.apple.com/documentation/swiftui/commands): `SidebarCommands`, `ToolbarCommands`, `TextEditingCommands`, `TextFormattingCommands`, `ImportFromDevicesCommands`, `InspectorCommands`, plus `EmptyCommands` for a conditionally-empty menu. `InspectorCommands` is new since the book — reach for it when your app has an inspector pane and wants the standard menu item for toggling it.

### CommandGroup

Inserts (or replaces) items *within* an existing menu. On macOS these become real menu-bar items; on iOS/iPadOS/tvOS they become key commands. Position with a `CommandGroupPlacement` via `init(before:)`, `init(after:)`, or `init(replacing:)` — `replacing:` is how you remove or completely swap out a standard item (e.g. drop Undo an app doesn't support).

Standard placements:

- App interactions: `.appInfo`, `.appSettings`, `.appTermination`, `.appVisibility`, `.systemServices`
- File manipulation: `.importExport`, `.newItem`, `.printItem`, `.saveItem`
- Content updates: `.pasteboard`, `.textEditing`, `.textFormatting`, `.undoRedo`
- Bars: `.sidebar`, `.toolbar`
- Windows: `.singleWindowList`, `.windowArrangement`, `.windowList`, `.windowSize`
- `.help`

See [`CommandGroup`](https://developer.apple.com/documentation/swiftui/commandgroup), [`CommandGroupPlacement`](https://developer.apple.com/documentation/swiftui/commandgroupplacement).

```swift
CommandGroup(before: .help) {
    Button("Product Web Site") { showWebSite() }
        .keyboardShortcut("/", modifiers: .command)
}
```

### CommandMenu

Creates a brand-new top-level menu instead of editing an existing one. On macOS it's always inserted between the built-in View and Window menus, ordered by the sequence in which you declare your `CommandMenu`s — relative order among your own menus, no control over absolute position. Use `CommandGroup` when extending something users already expect to find; use `CommandMenu` only for a genuinely new category of app-specific commands. See [`CommandMenu`](https://developer.apple.com/documentation/swiftui/commandmenu).

### Menu item view choice

- `Button` — gets an action, can carry a keyboard shortcut, shows no selection indicator.
- `Toggle` bound to `@AppStorage`/`@State` — renders as a checkable item.
- `Picker` — renders as a submenu with a checkmark on the current selection; its items cannot carry keyboard shortcuts.

Persist app-wide menu settings (display mode, show/hide toggles) with `@AppStorage` so `UserDefaults` sync and view updates come for free (macOS by Tutorials, ch. 3).

## Keyboard shortcuts

`.keyboardShortcut(_:modifiers:)` takes a `KeyEquivalent`, not a `String`. Construct one dynamically from a `Character` with `KeyEquivalent(someCharacter)` when the shortcut key comes from data rather than a literal. `modifiers` defaults to `.command` alone if omitted. Pass an array (`[.command, .shift, .option]`) for a shortcut needing multiple modifiers.

`EventModifiers.all` still exists as documented — "all possible modifier keys" combined into one value (https://developer.apple.com/documentation/swiftui/eventmodifiers/all).

Shortcut case doesn't matter when declaring (`"t"` vs `"T"`) — the menu always displays uppercase, and the user does not need Shift to trigger it unless `.shift` is explicitly one of the modifiers.

**Resolution order matters when shortcuts collide.** On macOS, the system searches the key window first, then the main window, then command groups (a depth-first, leading-to-trailing walk of each). The first control found with a matching shortcut wins, silently, if more than one control claims the same combination. See [`keyboardShortcut(_:modifiers:)`](https://developer.apple.com/documentation/swiftui/view/keyboardshortcut(_:modifiers:)).

Reserved system shortcuts (Cmd-C/Cmd-V/Cmd-X and other system-level bindings) take priority over an app-assigned `.keyboardShortcut` using the same combination — don't plan on reassigning them; pick a different combination for anything that would collide (corroborated across multiple Apple Developer Forums threads on shortcut conflicts).

**Checkmark vs. shortcut is a real trade-off, not just a styling choice:**

- A `Picker` gives you the checkmark for free but forfeits shortcuts entirely.
- Individual `Button`s give you shortcuts but no automatic selection indicator.

For an editor-style app where users keep their hands on the keyboard, prioritize shortcuts and fake the selection cue with a `.foregroundColor` swap (accent color for the active choice, primary otherwise) on the item's `Text`, rather than trying to force a checkmark onto a `Button` — semantic colors keep this correct in light and dark mode for free. Conversely, when the exact current state is easy to confuse (e.g., an "Auto" mode whose real value depends on time of day), the checkmark's unambiguous confirmation is worth losing the shortcut (macOS by Tutorials, ch. 3 & ch. 11).

## Toolbars on Mac

### Building content

Attach with `.toolbar { }` on the window's content view, building `ToolbarItem`/`ToolbarItemGroup` content.

- `ToolbarItemGroup` — for a cluster of controls that should be visually and positionally treated as one unit.
- `ToolbarItem` — for items that need independent identity, which matters for customization (below).

See [Toolbars](https://developer.apple.com/documentation/swiftui/toolbars).

### Placement

macOS-relevant placements: `.navigation` (leading edge, before the window title), `.principal` (centered), `.primaryAction` (trailing edge), `.automatic` (system chooses), plus `.status`, `.secondaryAction`, `.confirmationAction`, `.cancellationAction`, `.destructiveAction`.

`.topBarLeading`/`.topBarTrailing`/`.bottomBar`/`.keyboard`/`.accessoryBar(id:)` etc. are iOS/visionOS-only — skip them for a Mac-only surface. `.navigationBarLeading`/`.navigationBarTrailing` are deprecated. See [`ToolbarItemPlacement`](https://developer.apple.com/documentation/swiftui/toolbaritemplacement).

### Customizable toolbars

To make a toolbar user-customizable ("Customize Toolbar…" in the View menu, drag-to-rearrange), every piece needs an `id`:

- Give the toolbar itself an id via the `.toolbar(id:content:)` overload.
- Conform your content type to `CustomizableToolbarContent`, not plain `ToolbarContent`.
- Give each item an id through `ToolbarItem`'s `init(id:placement:content:)` / `init(id:placement:showsByDefault:content:)`.

`ToolbarItemGroup` has no id-bearing initializer — you cannot make a `ToolbarItemGroup` customizable, so a customizable toolbar means falling back to individual `ToolbarItem`s even for what would otherwise be a natural group (macOS by Tutorials, ch. 3, confirmed against current `ToolbarItem`/`ToolbarItemGroup` initializer lists).

Control default visibility per item with `defaultCustomization(_:options:)` and `customizationBehavior(_:)` on `CustomizableToolbarContent`. See [`CustomizableToolbarContent`](https://developer.apple.com/documentation/swiftui/customizabletoolbarcontent), [`ToolbarItem`](https://developer.apple.com/documentation/swiftui/toolbaritem), [`ToolbarItemGroup`](https://developer.apple.com/documentation/swiftui/toolbaritemgroup).

Confirmed current behavior: on macOS, `.searchable(text:)` places the search field in the trailing position of the window's toolbar automatically — no manual `ToolbarItem` needed for search itself (WWDC21, "Craft search experiences in SwiftUI"; https://developer.apple.com/documentation/swiftui/view/searchable(text:placement:prompt:)).

## The focus system

### @FocusState

`@FocusState` binds a local `Bool` (or `Hashable?`) property to whether a specific view holds focus. Assign it programmatically to move focus (e.g., jump to the first empty field on submit); read it to react to focus changes. The wrapped value must be optional or `Bool` so "no focus anywhere in this tree" is representable — set it to `nil`/`false` to clear focus from every field it's bound to (also useful for dismissing an on-screen keyboard). See [`FocusState`](https://developer.apple.com/documentation/swiftui/focusstate).

Binding the same `@FocusState` value to two different views is a programmer error: SwiftUI logs a runtime warning, and if you set the value programmatically it resolves the ambiguity by picking whichever candidate comes first in the view tree — treat the warning as a bug to fix, not as defined behavior.

### Nested focusable views

`.focused(_:)` reports true only when that exact view has focus. With nested focusable views (e.g. a `TextField` inside a focusable container), a single shared `@FocusState<Bool>` bound to both the outer and inner view goes true when *either* has focus, because SwiftUI walks up to the nearest ancestor carrying a focus binding — it can't tell you which one triggered it.

When you need to distinguish "the container itself is focused" from "a child inside it is focused," bind a custom `Hashable` enum with `.focused(_:equals:)` instead of two independent `Bool` states — one `@FocusState` property, two cases, unambiguous.

### Focused values for menu commands

For directing menu-command actions at "the active window" — the real problem behind a document/editor app's Commands — publish state from the focused scene:

- `.focusedSceneValue(_:)` — per-window/scene, most relevant on macOS.
- `.focusedValue(_:)` — per-view-hierarchy.

Read it back inside a `Commands` body with `@FocusedValue`/`@FocusedBinding`/`@FocusedObject`. This is the supported, current mechanism for exactly the problem macOS by Tutorials (ch. 11) solves with a third-party AppKit-observer package (`KeyWindow`) — the book reached for that package because it found `@FocusedBinding` unreliable at app launch and after the app regains focus from the background. Treat that as historical context, not a standing recommendation: start with the native focused-value mechanism above, and only reach for a third-party observer if you independently reproduce the same launch/refocus symptom in your own app.

See [`FocusedBinding`](https://developer.apple.com/documentation/swiftui/focusedbinding).

### Default focus and scoping

`resetFocus` (the `ResetFocusAction` environment value, called as a function) forces SwiftUI to re-evaluate default focus at runtime — call it after removing or replacing focused content so focus lands back on a view marked with `.prefersDefaultFocus(_:in:)`/`.defaultFocus(_:_:priority:)` instead of going nowhere.

`.focusScope(_:)`/`.focusSection()` constrain Tab-key traversal to a subtree without affecting focus order elsewhere in the hierarchy — reach for these on composite custom controls, not on ordinary form layouts.

See [`ResetFocusAction`](https://developer.apple.com/documentation/swiftui/resetfocusaction).
