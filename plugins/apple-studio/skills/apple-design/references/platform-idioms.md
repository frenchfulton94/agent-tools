> verified: 2026-08 against https://developer.apple.com/design/human-interface-guidelines/designing-for-ios, https://developer.apple.com/design/human-interface-guidelines/designing-for-ipados, https://developer.apple.com/design/human-interface-guidelines/designing-for-macos, https://developer.apple.com/design/human-interface-guidelines/windows, https://developer.apple.com/design/human-interface-guidelines/multitasking, https://developer.apple.com/design/human-interface-guidelines/pointing-devices, https://developer.apple.com/design/human-interface-guidelines/keyboards
> sources: live HIG (DocC JSON)
> note: organized by cross-platform decision, not per-platform encyclopedia — see the file body's opening paragraph. Scope is iOS/iPadOS/macOS; visionOS and watchOS idioms are out of scope. No book chapters feed this file (the SwiftUI book's macOS-adaptation chapters route to `swiftui-design-implementation.md` instead). All SwiftUI API symbols named below were individually confirmed against live Apple documentation JSON (exact name, signature, and platform availability) before this file was committed.

# Platform Idioms

This file is organized by decision, not by platform: for one SwiftUI codebase running on iPhone, iPad, and Mac, each section below covers a question that genuinely resolves differently per platform, and why. Skip anything here that SwiftUI already handles for you — see the "When to branch" section for the boundary between real platform differences and adaptivity you get for free. Scope is iOS/iPadOS/macOS; visionOS and watchOS idioms aren't covered.

## Navigation structure: sidebar, tab bar, and the menu bar

Mechanics of choosing sidebar vs. tab bar vs. split view, sizing tab bars, and search placement are covered in `hig-patterns.md § Navigation: Sidebar vs. Tab Bar vs. Split View` and `§ Search` — don't re-derive that here. What's platform-idiom-specific is *where commands live at all*:

- iOS has no menu bar and no command-palette equivalent. Every action must be discoverable directly in the view hierarchy — inline, in a toolbar, or via a context menu (long-press). There's no fallback surface to stash a rarely-used command in.
- iPadOS shares iOS's on-screen navigation idioms, but layers a shortcuts panel on top (hold Command with a keyboard attached) that groups an app's keyboard shortcuts into File/Edit/View-style categories. This is a keyboard-discovery aid, not a substitute for real menus — an iPad app has no menu bar of its own.
- macOS makes the menu bar mandatory, not optional chrome: every command your app exposes must be reachable from it, even if you've also surfaced it as a toolbar button or a context-menu item. Toolbar and context menu are conveniences layered on the menu bar, never a replacement for it. `.commands { }` in your `App` scene is the one navigation-adjacent surface with no iOS/iPadOS equivalent at all — this is a genuine, required platform branch, not something adaptivity covers.
(HIG: Designing for macOS, https://developer.apple.com/design/human-interface-guidelines/designing-for-macos; Designing for iPadOS, https://developer.apple.com/design/human-interface-guidelines/designing-for-ipados)

Decision rule: build your primary navigation once — it already adapts by size class (see below) — and write menu-bar commands as a strictly additive macOS-only layer that calls into the same actions your UI already exposes, rather than a parallel command system.

## Input assumptions: touch-only, touch+pointer, pointer+keyboard-primary

- iOS: Multi-Touch, the virtual keyboard, and Siri are the entire input surface. Design every control for a finger, never assume a hardware keyboard is attached, and don't design anything around hover — there is no pointer.
- iPadOS: touch is primary and mandatory; a physical keyboard or pointing device is additive, not a replacement for it. The practical consequence is that you can never shrink a touch target because a pointer might be connected — your view code can't reliably know whether one is, and even when one is, the same person can switch back to a finger mid-session, so touch has to keep working regardless.
- macOS: pointer and keyboard are primary and always present; touch does not exist on any Mac running your app. This is what licenses denser controls, hover-revealed UI, secondary-click as a first-class (not just "extra") discovery path, and pixel-precise drag/resize interactions that iPadOS and iOS can't assume.
(HIG: Designing for iOS, https://developer.apple.com/design/human-interface-guidelines/designing-for-ios; Designing for iPadOS; Designing for macOS)

The pointer itself is a different interaction system on the two platforms that have one. macOS uses a small, fixed set of system cursor shapes (arrow, I-beam, resize handles) people don't expect to be reinvented per app — style it with `.pointerStyle(_:)` (macOS 15+) or the older `.onHover(perform:)` plus `NSCursor` for finer control. iPadOS layers a distinct content-effect system on top — highlight, lift, and hover — where both the cursor and the element beneath it change shape and appear to attract the pointer as it approaches, via `.hoverEffect(_:)`. Don't port one platform's pointer language to the other; use macOS's plain cursor conventions on Mac and iPadOS's content-effect system on iPad. (HIG: Pointing Devices, https://developer.apple.com/design/human-interface-guidelines/pointing-devices)

Treat hover itself as having different reliability per platform: on Mac, hover is a constant signal you can lean on, since a pointer is effectively guaranteed. On iPad, hover only fires when a pointer happens to be attached, so anything you reveal on hover needs an equally-discoverable touch path — never make hover the *only* way to find an action on iPad. `.onHover(perform:)` is available and behaves consistently across both platforms; it's the underlying signal both `.hoverEffect()` (iPadOS-flavored) and `.pointerStyle()` (macOS-flavored) build on.

On iPadOS specifically, `.hoverEffect()` isn't a single visual style — pick among its three system content effects by element size and background, not by taste: **highlight** (a translucent rounded-rectangle background with subtle parallax) for small elements with a transparent background, like toolbar/bar buttons; **lift** (scale-up, shadow, specular highlight) for small elements with an opaque background, like app icons; **hover** (custom scale/tint/shadow you configure yourself) for larger elements, since lift's scale-up behavior crowds neighbors once an element is big. Matching the effect to the element this way is also why the system applies pointer magnetism (the pointer visually "snaps" toward the element as it approaches) to highlight- and lift-effect elements but deliberately not to hover-effect ones — a custom hover element that doesn't transform the pointer shape would make magnetism feel like losing control of it. (HIG: Pointing Devices)

## Keyboard depth and focus navigation

Standard shortcuts (Cmd-Z, Cmd-C, etc.) and the Control–Option–Shift–Command ordering rule for custom shortcuts apply identically on iPadOS and macOS — write that code once with `.keyboardShortcut(_:modifiers:)`, don't branch it, and let the system localize and mirror shortcuts for RTL layouts automatically. (HIG: Keyboards, https://developer.apple.com/design/human-interface-guidelines/keyboards)

Where platforms genuinely diverge is whether *you* build keyboard focus/tab-navigation among ordinary controls:

- macOS: keyboard-only workflows are an expected, everyday use pattern, not an edge case — support Full Keyboard Access across your custom controls as baseline behavior. SwiftUI's `.focusable()` plus `@FocusState` gets a custom control into the standard Tab-key focus order; you own building it for anything that isn't already a standard control.
- iPadOS: explicitly do *not* hand-build tab- or arrow-key focus navigation for standard controls like buttons, segmented controls, or switches. That's what system-level Full Keyboard Access — an accessibility feature people opt into — is for. Do support keyboard navigation for genuinely list- or text-like content (text fields, text views, sidebars), since that's expected even with Full Keyboard Access off.
- iOS: same content-only rule as iPadOS, but the case rarely comes up, since most iPhone sessions never involve a hardware keyboard.
(HIG: Keyboards)

Decision rule: implement standard shortcuts once via `.keyboardShortcut()`; implement broad custom-control keyboard support once via `.focusable()`/`@FocusState` rather than hand-rolling a tab order per platform, and don't duplicate what Full Keyboard Access already covers for standard controls on iPadOS.

## Windows and multitasking behavior

- iOS has no window concept at all — one scene fills the screen at a time (aside from Picture in Picture). "Multitasking" on iOS means your app gets backgrounded or suspended without warning, not that it shares screen space with itself. Design for clean pause/resume, not for simultaneous views of your own content.
- iPadOS has real windows, but your app doesn't choose or detect whether the person is running full screen or in freely resizable windowed mode — that's a system-level preference outside your control, and the API gives you no signal to branch on. The consequence is layout that must survive arbitrary width, not a fixed set of split-screen ratios: build fluid layout, not fixed breakpoints. Windowed iPad also draws system window controls at the toolbar's leading edge, so leading-edge toolbar buttons need to be inset rather than pinned flush, or the window controls will sit on top of them.
- macOS treats multitasking as the platform's default assumption, not an opt-in mode — many windows across many apps open at once is normal, not exceptional. Windows carry main/key/inactive state with distinct system-drawn appearance (colored vs. gray traffic-light controls, presence or absence of translucency) that people rely on to tell which window is listening for input. Never build custom window chrome that reimplements this by hand — use system window components and this comes for free; a custom chrome that gets it even slightly wrong reads as a broken app, not a stylistic choice.
(HIG: Windows, https://developer.apple.com/design/human-interface-guidelines/windows; Multitasking, https://developer.apple.com/design/human-interface-guidelines/multitasking)

macOS's three window states are a real semantic distinction, not just a color scheme, and they only matter because macOS is the one platform where several of an app's own windows — or windows from different apps entirely — are routinely visible at once:

- **Main** — an app's frontmost window; at most one per app.
- **Key** — whichever window currently accepts keyboard/input focus; usually, but not always, the main window (a floating panel like a color picker can be key while the main window stays main).
- **Inactive** — everything else currently visible.

Two consequences follow directly: never put critical information or controls in a bottom bar on a custom panel or auxiliary window — people routinely drag windows until the bottom edge runs off-screen, so a bottom bar is only safe for small, non-essential supplementary status (item counts, disk space), never for something someone must see or reach. And refer to windows as "windows" in user-facing copy, never "scene" — scene is your implementation's term, and using it in the UI reads as an internal leak.

Apps genuinely don't get to know or influence which multitasking configuration (full-screen vs. windowed on iPad; how many other windows are open on Mac) a person has chosen — there's no API signal for it. This is precisely why the earlier "build fluid layout, not fixed breakpoints" rule matters: since you can't detect the configuration, you can't special-case it, so the layout has to hold up at any width regardless.

Opening a new window (`WindowGroup` plus `@Environment(\.openWindow)`) is meaningful on macOS and iPadOS but has no equivalent on iOS — a flow that assumes "open this in a new window" must degrade to an in-place push or a sheet on iOS; it can't simply be omitted from that build. Reserve new windows for content that genuinely benefits from staying visible alongside what's already open (a compose pane next to an inbox); don't make a new window the default way of drilling into content, or windows accumulate into clutter. Separately, decide primary vs. auxiliary per window regardless of platform: a primary window carries your app's own navigation, an auxiliary window is one dedicated task with an explicit close action and no further drill-in — use that distinction, not platform, to decide whether new content belongs in a new window, a sheet, or in-place. (HIG: Windows)

App-lifecycle expectations follow the same platform split:

- **iOS/iPadOS**: anything mid-task must pause cleanly and restore full context on return, or — if the person already started it — finish in the background (an export, a download) before the system suspends you. Audio needs explicit interruption handling: pause indefinitely for primary playback (music, podcasts) that's interrupted, but only duck or briefly pause for transient interruptions (a turn-by-turn prompt) and restore afterward.
- **macOS**: apps aren't suspended the same way — switching between them is instant and near-lossless, so the equivalent expectation is a smooth main/key/inactive visual transition rather than state-restoration engineering.
- **All three platforms**: `@Environment(\.scenePhase)` reports the same three cases (`.active`, `.inactive`, `.background`) everywhere — no platform branch is needed to read it; only deciding what "inactive" should mean *behaviorally* per platform is a real decision. Keep background-completion notifications rare everywhere: reserve them for tasks people would otherwise wonder about, not routine completions.
(HIG: Multitasking)

## Content density and reach: display size vs. viewing distance

Physical viewing distance and grip — not device category by itself — should drive how dense your content is and how far controls can sit from the thumb:

- iPhone: held one- or two-handed, viewed roughly 1–2 feet away. Bottom and middle screen space is the comfortable reach zone, which is why leading-edge swipe-back gestures and bottom-anchored primary actions are the iOS idiom — put frequent actions where a thumb already rests.
- iPad: held, propped, or laid flat, viewed roughly 3 feet away. Grip is inconsistent enough that there's no single reliable reach zone the way there is on iPhone, so favor the larger display's room to show more content with fewer modal detours, and position controls by information hierarchy rather than thumb reach.
- Mac: stationary, roughly 1–3 feet away, and the pointer reaches every pixel equally regardless of where a control sits — reach is a non-issue. Control placement should be driven by convention (toolbar, menu, inspector) and precision instead.
(HIG: Designing for iOS; Designing for iPadOS; Designing for macOS)

Because a pointer can select individual pixels but a finger can't, hit-target sizing is asymmetric between a pointer-plus-touch platform and a pointer-only one. iPadOS's pointer-accessory guidance adds roughly 12pt of hit-padding around bezeled controls and roughly 24pt around edge-only elements for pointer users — but that padding is additive on top of the platform's touch-target minimum, not a replacement for it, since a finger still has to land on the same control (see `accessibility.md § Tap targets and motor accessibility` for the base 44×44pt minimum this padding sits on top of). Mac controls, with no touch requirement at all, can be sized purely for pointer precision. (HIG: Pointing Devices)

## When to branch code vs. when the system already adapts for you

SwiftUI's structural containers already handle most of the iPhone/iPad/Mac shape difference without any platform branching:

- `NavigationSplitView` collapses to a stacked single-column layout on iPhone or a compact-width iPad slot and expands to a real sidebar-plus-detail split on a regular-width iPad or Mac, automatically.
- `List`/`Form` pick up each platform's native list or grouped style on their own.
- Standard controls (`Button`, `Toggle`, `Picker`) already render each platform's idiomatic look — a macOS bordered button vs. an iOS filled or plain style — without per-platform styling code from you.
- Dynamic Type and Dark Mode/appearance adapt identically everywhere as long as you use semantic colors and fonts and avoid hardcoded sizes; don't branch for these, and don't fight them with fixed frames.

`@Environment(\.horizontalSizeClass)` already captures most of the iPhone-vs-iPad shape difference — an iPad in a narrow multitasking slot reports `.compact` exactly like an iPhone in portrait does. Prefer branching layout decisions on size class over `#if os(iOS)`; reserve OS-level conditionals for capabilities, not shapes.

Genuine reasons to branch with `#if os(macOS)` or an equivalent platform check:

- Whether menu-bar commands exist at all (no iOS/iPadOS equivalent).
- Whether windows exist as a concept (absent on iOS).
- Hover-driven disclosure and pointer/cursor styling (absent on iOS, a different system on iPadOS vs. macOS).
- Full Keyboard Access vs. hand-built control focus order (see Keyboard section).
- Any system-feature integration that's genuinely platform-exclusive (see below).

Everywhere else — layout shape, text scaling, appearance, standard control rendering — the system already handles it; adding a platform branch there is redundant code to maintain, not a correctness requirement.

## System-feature surface: what to hook into per platform

- iOS/iPadOS home-screen surfaces — widgets, Home Screen quick actions, Siri Shortcuts and suggestions — are opt-in integration points, not requirements. Skipping them for a content-heavy app leaves real discoverability on the table that a Mac build of the same app has no equivalent surface for at all.
- iPadOS specifically treats drag-and-drop between apps and multiple-window-per-app support as base expectations for anything productivity-flavored, not nice-to-haves — people expect to drag content out of your app into whatever's open alongside it.
- macOS specifically: the Dock menu (secondary-click your app's Dock icon) is where people expect quick access to common actions or recent items without opening a window first. File-menu conventions (New/Open/Save/Close) are a fixed, already-known vocabulary — put your app's document-like actions under those exact names rather than inventing new ones. Native full-screen mode is a distinct, expected state (not just a maximized window) worth supporting deliberately as a distraction-free context.
(HIG: Designing for iOS; Designing for iPadOS; Designing for macOS)

None of this is required for a minimal cross-platform SwiftUI app to feel structurally correct on each platform — but each item you skip is a specific, named gap on that platform, not a neutral omission. Decide with intent rather than by default.
