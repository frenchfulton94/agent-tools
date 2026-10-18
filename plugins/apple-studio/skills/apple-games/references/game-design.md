> verified: 2026-10 against https://developer.apple.com/design/human-interface-guidelines/designing-for-games.md, https://developer.apple.com/design/human-interface-guidelines/designing-for-macos.md, https://developer.apple.com/design/human-interface-guidelines/designing-for-ios.md, https://developer.apple.com/design/human-interface-guidelines/designing-for-ipados.md, https://developer.apple.com/design/human-interface-guidelines/game-controls.md, https://developer.apple.com/design/human-interface-guidelines/game-center.md, https://developer.apple.com/design/human-interface-guidelines/going-full-screen.md, https://developer.apple.com/design/human-interface-guidelines/typography.md, https://developer.apple.com/design/human-interface-guidelines/layout.md, https://developer.apple.com/design/human-interface-guidelines/menus.md, https://developer.apple.com/design/human-interface-guidelines/buttons.md, https://developer.apple.com/design/human-interface-guidelines/accessibility.md, https://developer.apple.com/design/human-interface-guidelines/launching.md, https://developer.apple.com/design/human-interface-guidelines/onboarding.md, https://developer.apple.com/design/human-interface-guidelines/loading.md, https://developer.apple.com/design/human-interface-guidelines/settings.md, https://developer.apple.com/design/human-interface-guidelines/ratings-and-reviews.md, https://developer.apple.com/design/human-interface-guidelines/apple-in-app-purchase.md, https://developer.apple.com/documentation/gamekit/adding-an-access-point-to-your-game.md, https://developer.apple.com/documentation/gamekit/gkaccesspoint.md, https://developer.apple.com/documentation/gamekit/gkaccesspoint/isactive.md, https://developer.apple.com/documentation/gamekit/gkaccesspoint/ispresentinggamecenter.md, https://developer.apple.com/documentation/gamekit/gkaccesspoint/location-swift.property.md, https://developer.apple.com/documentation/gamekit/gkaccesspoint/parentwindow.md, https://developer.apple.com/documentation/gamekit/gkaccesspoint/frameinscreencoordinates.md, https://developer.apple.com/documentation/gamekit/gkaccesspoint/showhighlights.md, https://developer.apple.com/documentation/gamekit/creating-engaging-challenges-from-leaderboards.md, https://developer.apple.com/documentation/gamekit/creating-activities-for-your-game.md, https://developer.apple.com/documentation/bundleresources/information-property-list/gcrequirescontrolleruserinteraction.md, https://developer.apple.com/documentation/bundleresources/information-property-list/gcrequirescontrolleruserinteraction/ios.md, https://developer.apple.com/documentation/bundleresources/information-property-list/gcrequirescontrolleruserinteraction/visionos.md, https://developer.apple.com/documentation/bundleresources/information-property-list/gcsupportscontrolleruserinteraction.md, https://developer.apple.com/documentation/metal/adapting-your-game-interface-for-smaller-screens.md, https://developer.apple.com/documentation/metal/improving-your-games-graphics-performance-and-settings.md, https://developer.apple.com/documentation/quartzcore/cametallayer/drawablesize.md, https://developer.apple.com/documentation/uikit/uifontmetrics.md, https://developer.apple.com/documentation/uikit/uifontmetrics/scaledfont(for:compatiblewith:).md, https://developer.apple.com/documentation/uikit/uifontmetrics/scaledfont(for:maximumpointsize:compatiblewith:).md, https://developer.apple.com/documentation/uikit/uicontentsizecategory/didchangenotification.md, https://developer.apple.com/documentation/uikit/uiapplication/willresignactivenotification.md, https://developer.apple.com/documentation/appkit/nsapplication/didresignactivenotification.md, https://developer.apple.com/documentation/appkit/nsapplication/didbecomeactivenotification.md, https://developer.apple.com/documentation/swiftui/scenephase.md, https://developer.apple.com/documentation/appkit/custom-controls.md, https://developer.apple.com/documentation/appkit/nsaccessibilityelement-swift.class.md, https://developer.apple.com/documentation/appkit/nsaccessibilityelement-swift.class/accessibilityframeinparentspace.md, https://developer.apple.com/documentation/appkit/nsaccessibilitybutton.md, https://developer.apple.com/documentation/appkit/nsaccessibilitybutton/accessibilityperformpress().md, https://developer.apple.com/documentation/appkit/nsaccessibilitybutton/accessibilitylabel().md, https://developer.apple.com/documentation/appkit/nsaccessibilityprotocol/setaccessibilitychildren(_:).md, https://developer.apple.com/documentation/appkit/nsaccessibilityprotocol/setaccessibilityfocused(_:).md, https://developer.apple.com/documentation/appkit/nsaccessibility-swift.struct/post(element:notification:).md, https://developer.apple.com/documentation/appkit/nsaccessibility-swift.struct/notification/focuseduielementchanged.md, https://developer.apple.com/documentation/uikit/uiaccessibilityelement.md, https://developer.apple.com/documentation/uikit/uiaccessibilityelement/accessibilityframeincontainerspace.md, https://developer.apple.com/documentation/objectivec/nsobject-swift.class/accessibilityactivate().md, https://developer.apple.com/documentation/storekit/requestreviewaction.md, https://developer.apple.com/documentation/storekit/appstore/canmakepayments.md; the shipped `GKAccessPoint.h` and `NSAccessibilityProtocols.h` in the MacOSX 27.0 SDK
> typecheck: macos 26.0, ios 26.0

# Game Design: HIG Expectations for Games on Mac, iPhone, and iPad

Contents:
- Scope and hand-offs
- Platform expectations: Mac
- Platform expectations: iPhone and iPad
- Input: the defaults and the controller rule
- Controls the HIG specifies
- Text size and legibility
- Menus, buttons, and layout
- VoiceOver for menus you draw yourself
- Pause and interruptions
- Launch, onboarding, and requests
- Game Center presentation
- Apple In-App Purchase in a game
- Gates: tvOS and visionOS
- Where else to look

## Scope and hand-offs

Scope: *what the Human Interface Guidelines expect of a game, and the places
where a game diverges from an ordinary app*. The HIG page "Designing for
games" and the pages it links are the source. General HIG layout, typography,
color, onboarding, and settings live in `apple-design`; this file keeps only
what is game-specific and points there for the rest. It does not cover art
direction, Apple Arcade, or App Store product-page marketing.

| Topic | Owner |
|---|---|
| Full-screen mechanics, hiding the Dock, deferring screen edges, the cursor | `game-loop-and-threading.md` |
| Controller, keyboard, mouse, and Touch Controller APIs, glyphs, remapping | `input.md` |
| Audio session, interruptions of audio, haptics and the haptics off switch | `audio-and-haptics.md` |
| GameKit authentication, achievements, leaderboards, activities, GameSave | `game-center-and-online.md` |
| Background Assets and the initial download size | `assets.md` |
| Text on a drawable after upscaling, drawable size | `apple-metal/references/display-and-upscaling.md` |
| General type scaling, contrast, settings windows | `apple-design/references/hig-foundations.md`, `hig-patterns.md`, `accessibility.md` |

Two 2026 HIG changes affect anything written from older material:

- **The Layout page lost its per-device size tables.** The page revision of
  September 9, 2026 removed the point-size specifications that earlier
  versions listed per iPhone, iPad, and Watch model. Do not quote per-device
  screen sizes from memory. Read the safe area and the view's bounds at
  runtime.
- **"In-App Purchase" is now "Apple In-App Purchase"** in the HIG (renamed
  September 17, 2026). StoreKit is still the API. Use the new name in
  design copy and the StoreKit names in code.

## Platform expectations: Mac

A Mac game shares the screen with other apps and runs at a desk 1 to 3 feet
from the player. The HIG's macOS page treats a game like any Mac app in these
respects, and a port from a console or a PC build misses each of them:

- **Windows behave like windows.** The player can resize, move, hide, and
  show the game window. Full screen is offered through the system mechanism,
  never forced, and never left automatically. Never change the display mode
  on entering full screen: the HIG states that it does not improve
  performance, and the player owns the display mode. Hiding the Dock is
  allowed in a full-screen game and in no other app. The mechanics are in
  `game-loop-and-threading.md`.
- **The menu bar carries every command.** Settings goes in the App menu as
  well as behind Esc in the game (see below). Keyboard shortcuts exist for
  menu commands.
- **Active and inactive are frequent and fast.** Players switch apps while a
  game runs. The transition must be smooth, and gameplay pauses (see
  "Pause and interruptions").
- **Keep critical HUD and controls off the bottom edge of a window.** Players
  drag windows until the bottom runs off the screen. Keep window content out
  from behind the camera housing.
- **Several displays, including an iPad used as a display.** Do not assume one
  screen.
- **Several logged-in users.** Fast user switching means more than one
  person may be active on the Mac at once. Do not assume who is signed in;
  keep saves and settings in the current user's own locations.
- **No launch screen.** macOS does not use one (it is required only on iOS,
  iPadOS, and tvOS).
- **No Dynamic Type.** See "Text size and legibility". This is the Mac-first
  gotcha with the most consequences.

Settings defaults: choose graphics settings from the device rather than
asking. Apple's graphics-settings article recommends a few tested presets
over a long list of independent options, selected at launch from the GPU
family and memory. Players expect fewer, well-tuned settings on iPhone than on
Mac. GPU-family checks are `apple-metal`'s; low-power and thermal reactions
are `game-loop-and-threading.md`'s. Never duplicate a system-wide setting,
such as an accessibility accommodation, in the game's own settings.

## Platform expectations: iPhone and iPad

- **iPhone.** Held in the hands at 1 to 2 feet, rotated freely, and switched
  away from often. Touch is the default input. A launch screen is required
  (on iPad too):
  make it nearly identical to the game's first frame (a solid color if the
  first frame is one), with no text, because the launch screen cannot be
  localized, and no logo unless the first screen has one. A landscape-only
  game must work in both landscape orientations.
- **iPad.** Viewed at about 3 feet, held, propped, or flat. Touch is the
  default, and keyboard, mouse, trackpad, and Apple Pencil are additional.
  Windows are resizable when the player multitasks, and the HIG expects iPad
  experiences to carry over to running on the Mac.
- **Layout follows size classes, not device type or orientation.** The HIG
  says this even for a landscape-locked game: iPad windows and iPhone
  Mirroring on a Mac can take nearly any width and height. Keep the same
  functionality at every size.
- **Home indicator.** Keep the default single-swipe exit. Require a second
  swipe only if players exit by accident; the API is in
  `game-loop-and-threading.md`.

## Input: the defaults and the controller rule

The HIG's default input per platform:

| Platform | Default | Additional |
|---|---|---|
| macOS | Keyboard, mouse, trackpad | Game controller |
| iOS | Touch | Game controller |
| iPadOS | Touch | Game controller, keyboard, mouse, trackpad, Apple Pencil |

Every Mac has a keyboard and a pointing device, and every iPhone and iPad has
a touchscreen; a controller is an optional purchase. **A game on these three
platforms must be fully playable with the default input.** A controller is
additive, even when it is the best way to play.

Only visionOS (and tvOS, per the HIG) may require a controller. The Info.plist
key `GCRequiresControllerUserInteraction` is a dictionary of per-platform
Booleans, and its documentation gives it two entries:

- `visionOS` set to `YES` *requires* a controller. The App Store shows a
  Controller Required badge.
- `iOS` set to `YES` only *recommends* one. The App Store shows a Controller
  Recommended badge. The game must still run with touch alone.

The key's documented availability is iOS, iPadOS, and visionOS; there is no
macOS entry, so a Mac game has no way to declare a controller requirement.
Adding the key also needs the Game Controllers capability with
ExtendedGamepad selected, which writes `GCSupportsControllerUserInteraction`
for you. To recommend a controller on iPhone and iPad:

```plist
<key>GCRequiresControllerUserInteraction</key>
<dict>
    <key>iOS</key>
    <true/>
</dict>
```

Even where a controller is required, the player can launch the game with none
connected. Detect that at launch and prompt the player to connect one.

## Controls the HIG specifies

**Controller buttons outside gameplay** follow one mapping on every Apple
platform: A activates, B cancels or goes back, the left and right shoulder
buttons switch to the neighboring screen or section, the sticks and D-pad
move the selection, Menu opens settings or pauses, and Home is reserved for the
system. X, Y, and the triggers have no UI meaning. Show the connected
controller's own glyphs, not position names, and switch glyphs to whichever
controller the player is using (`input.md` has the API).

**Mac keyboard bindings:**

- Prefer single keys: a mnemonic letter (I for inventory, M for map) and Space
  for the main action.
- Keep frequent commands near the movement keys, and group related commands
  physically (the number row for inventory slots).
- Test on an Apple keyboard. A binding on Control in a PC build often belongs
  on Command, which sits next to the Space bar.
- Always allow rebinding.
- Esc opens settings in a game; Command-Comma is the app convention, and the
  App menu item is still required.
- Never redefine system-wide trackpad or mouse gestures (Mission Control,
  App Exposé, swiping between full-screen apps), even while the game is full
  screen.

**Touch controls on iPhone and iPad:**

- Prefer touching game objects directly over adding a virtual button.
- Movement goes on the left half and the camera on the right half. Spawn the
  virtual stick where the thumb lands, and pan the camera by dragging, not
  with a second stick.
- Menus and secondary controls go along the top, clear of the Home
  indicator and the Dynamic Island.
- Frequent controls are at least 44x44 pt; less important ones are at least
  28x28 pt.
- Give every virtual control a press state the player can see around a thumb
  (a glow or an opacity change), with sound and haptics.
- Draw the action on the button (a sword, a hand), never "A", "X", or "R1".
- Hide controls whose action is unavailable, and fade the stick at rest.
- Replace chords and sequences with tap, double tap, and touch-and-hold
  variants of one control.

Custom gestures are legitimate in a game, but each needs feedback while it
happens, a visible cue when it is unavailable, and another way to reach any
important action.

## Text size and legibility

The HIG's default and minimum text sizes apply to custom fonts as well as
system fonts:

| Platform | Default | Minimum |
|---|---|---|
| macOS | 13 pt | 10 pt |
| iOS, iPadOS | 17 pt | 11 pt |

Thin custom weights need more than the minimum, and Regular through Bold
reads better at small sizes. Labels over characters or objects need a backing
shape, such as a shaded lozenge, as well as the minimum size; the HIG's own
example contrasts bare small labels with labels on a pill. The Accessibility
page asks for text that can grow to at least 200 percent, either through
Dynamic Type or through the game's own setting. When text grows, grow what
the player reads (character dialog) and cap what is transient (hit-damage
numbers).

Sizes are in points, and a Metal-drawn HUD needs pixels. Apple's conversion
divides the drawable width by the layer's bounds width. It is valid while
the layer keeps the default `contentsGravity` and the drawable fills it. If
the scene renders at a lower resolution and is upscaled, draw text at the
output resolution, after the upscale (`apple-metal/references/display-and-upscaling.md`):

```swift
import QuartzCore

struct GameTextSize {
    static let macMinimum: CGFloat = 10

    /// The player's choice from the game's options screen. Offer at least 1.0...2.0.
    var playerScale: CGFloat = 1.0

    func points(for basePoints: CGFloat) -> CGFloat {
        max(basePoints * playerScale, Self.macMinimum)
    }
}

func drawablePixels(forPoints points: CGFloat, in layer: CAMetalLayer) -> CGFloat {
    points * layer.drawableSize.width / layer.bounds.width
}
```

**macOS has no Dynamic Type.** The Typography page lists it on iOS, iPadOS,
tvOS, visionOS, and watchOS only, and `UIFontMetrics` is not available on
macOS (Mac Catalyst aside). A Mac game that wants scalable text must offer
its own text-size setting, as `GameTextSize` above does. SwiftUI chrome on the
Mac does not respond to `.dynamicTypeSize(_:)` either: on macOS 27.0.1, `.body` and `.title` rendered at the same height from
`.xSmall` to `.accessibility5`, while an explicit `.system(size:)` scaled
(runtime-checked, `task-8-write/runtime/game-design/runs.txt`). Drive SwiftUI
menus on the Mac from the same scale factor, by point size.

On iPhone and iPad, Metal-drawn text follows the system setting through
`UIFontMetrics`. Always scale from the unscaled base font: passing an
already-scaled font raises an exception. Rebuild glyph atlases when
`UIContentSizeCategory.didChangeNotification` posts.

```swift
import UIKit

enum GameTextRole { case dialog, damageNumber }

@MainActor
func dynamicPointSize(for role: GameTextRole, traits: UITraitCollection) -> CGFloat {
    let metrics = UIFontMetrics(forTextStyle: .body)
    let base = UIFont.systemFont(ofSize: 17)
    switch role {
    case .dialog:
        return metrics.scaledFont(for: base, compatibleWith: traits).pointSize
    case .damageNumber:
        // Transient text: scale it, but cap it so it never crowds the scene.
        return metrics.scaledFont(for: base, maximumPointSize: 22, compatibleWith: traits).pointSize
    }
}
```

Unity games can get Dynamic Type through Apple's Unity plug-ins; where they do
not fit, the game still owes the player a text-size control. Structural
fixes for large text (stacking, fewer columns, truncation rules) are in
`apple-design/references/hig-foundations.md`.

## Menus, buttons, and layout

- **In-game menus use the platform's default input.** On a Mac, a menu
  must work with the keyboard and mouse even if the game also supports a
  controller. On iPhone and iPad, it must work by touch.
- **Resize menus, do not shrink them.** A menu scaled down from desktop art
  becomes unreadable and untappable on a phone. Rebuild target sizes for each
  screen. Menus must survive aspect ratios from 4:3 to 19.5:9, and both
  orientations if the game supports them. Use relative constraints, and
  build a device-specific layout only as a last resort.
- **Button sizes.** The games and Accessibility pages give macOS controls a
  28x28 pt default and a 20x20 pt minimum, and iOS and iPadOS 44x44 pt and
  28x28 pt. The Buttons page states a general 44x44 pt hit region for any
  input. The pages differ for the Mac: treat 20 pt as the floor for a
  pointer-only Mac menu, and use 44 pt hit regions for any menu that also
  ships to iPhone or iPad. Every drawn button needs a pressed state.
- **One or two prominent buttons per menu screen.** Mark the preferred option
  by style, not size. Never give a destructive action, such as deleting a save
  or quitting without saving, the default (Return) role.
- **Menu item labels** in games rarely show keyboard commands, because the
  game takes input from many devices and keys are remappable.
- **Background art fills, it never stretches.** On an aspect change, scale
  the art to fill and author it wider and taller than the usual visible area.
  Avoid letterboxing; if it is unavoidable, fill the bars with art
  (`apple-design/references/adaptive-layout.md` § Games).
- **Test the largest and smallest layouts first.** Xcode's Device Hub
  simulates resized iPad windows and iPhone Mirroring on the Mac, to catch
  clipping.

## VoiceOver for menus you draw yourself

A menu drawn in Metal has no views, so VoiceOver finds nothing in it, and
nothing tells the player so. Model each drawn control as an accessibility
element parented to the hosting view.

On the Mac, subclass `NSAccessibilityElement`, set its role, and give it a
frame in the host view's coordinates (points, with the view's own origin)
with `setAccessibilityFrameInParentSpace(_:)`. That frame follows the view
as the window moves. AppKit's Custom Controls guide says to adopt the
role-specific protocol (`NSAccessibilityButton` for a button). **In Swift,
against the macOS 27 SDK, that conformance on an `NSAccessibilityElement`
subclass does not compile**: `NSAccessibilityElementProtocol` (the
Objective-C `NSAccessibilityElement` protocol) declares
`accessibilityIdentifier` nonnull (`NSAccessibilityProtocols.h` line 26), and
the class's property is nullable (line 362). The SDK wins. Set the role and
override the `NSAccessibilityProtocol` methods instead, as below. Do not use
the legacy key-based `NSAccessibility` attribute methods, which are deprecated.

```swift
import AppKit

final class DrawnMenuButton: NSAccessibilityElement {
    private let title: String
    private let action: () -> Void

    /// `frame` is in the host view's coordinates, in points.
    init(title: String, frame: NSRect, in hostView: NSView, action: @escaping () -> Void) {
        self.title = title
        self.action = action
        super.init()
        setAccessibilityRole(.button)
        setAccessibilityParent(hostView)
        setAccessibilityFrameInParentSpace(frame)
    }

    override func accessibilityLabel() -> String? { title }

    override func accessibilityPerformPress() -> Bool {
        action()
        return true
    }
}

/// Call when the menu opens and whenever controller or keyboard focus moves.
@MainActor
func publish(_ buttons: [DrawnMenuButton], on hostView: NSView, focused: DrawnMenuButton?) {
    hostView.setAccessibilityChildren(buttons)
    if let focused {
        focused.setAccessibilityFocused(true)
        NSAccessibility.post(element: focused, notification: .focusedUIElementChanged)
    }
}
```

Labels follow AppKit's rule: one capitalized word where possible, no control
type ("Play", not "Play button"), no trailing period, always localized. A
drawn slider posts `.valueChanged` when it moves; nothing else tells
VoiceOver. On iPhone and iPad the counterpart is `UIAccessibilityElement`
with `accessibilityFrameInContainerSpace`, the `.button` trait, and an
`accessibilityActivate()` override. Not runtime-checked (GUI): whether
VoiceOver reads these elements needs a VoiceOver session, so test it by hand.

```swift
import UIKit

final class DrawnTouchButton: UIAccessibilityElement {
    private let action: () -> Void

    init(title: String, frame: CGRect, in container: UIView, action: @escaping () -> Void) {
        self.action = action
        super.init(accessibilityContainer: container)
        accessibilityLabel = title
        accessibilityTraits = .button
        accessibilityFrameInContainerSpace = frame
    }

    override func accessibilityActivate() -> Bool {
        action()
        return true
    }
}
```

The rest of the HIG's game accessibility list: let players adjust text size,
control mapping, motion intensity, and sound balance; offer difficulty
accommodations; caption cutscenes; pair off-screen audio cues with a visual
pointer; never signal state by color alone. Switch Control can be driven by a
game controller, and Full Keyboard Access must work.

## Pause and interruptions

The HIG's rule: when the player leaves, the game pauses on its own, and on
return it resumes from that point. Players should miss nothing. In practice,
return to a paused state with the pause menu up, and let the player resume;
never drop them back into live action.

| Event | Mac | iPhone and iPad |
|---|---|---|
| App loses focus | `NSApplication.didResignActiveNotification` | `UIApplication.willResignActiveNotification` |
| Game Center overlay opens | `GKAccessPoint.isPresentingGameCenter` becomes true | same |
| Controller Menu button | open settings or pause | same |

On the Mac, use the AppKit notification. The documentation says it posts as
soon as the app gives up active status, on the main actor. `ScenePhase`
promises only that `.inactive` means "in the foreground but should pause"; it
does not document when a Mac window changes phase as another app comes
forward. (`NSApplication.DidResignActiveMessage`, the Swift-concurrency form,
is macOS 27 only.) Interruptions of audio, such as a phone call on iPhone, are
`audio-and-haptics.md`'s; macOS has no audio session to report them.

```swift
import AppKit
import GameKit

enum GameScene { case title, mainMenu, settings, loading, cutscene, gameplay }

@MainActor
final class PresentationPolicy {
    private(set) var isPaused = false
    private var observers: [NSObjectProtocol] = []
    private var overlayObservation: NSKeyValueObservation?

    init(menuWindow: NSWindow) {
        let accessPoint = GKAccessPoint.shared
        accessPoint.parentWindow = menuWindow   // NSWindow on macOS, UIWindow on iOS
        accessPoint.location = .topTrailing

        overlayObservation = accessPoint.observe(\.isPresentingGameCenter) { [weak self] point, _ in
            let presenting = point.isPresentingGameCenter
            Task { @MainActor in
                if presenting { self?.pause() }
            }
        }
        observers.append(NotificationCenter.default.addObserver(
            forName: NSApplication.didResignActiveNotification, object: nil, queue: .main
        ) { [weak self] _ in
            MainActor.assumeIsolated { self?.pause() }
        })
    }

    /// The access point shows on the main menu and nowhere in play.
    func enter(_ scene: GameScene) {
        GKAccessPoint.shared.isActive = (scene == .mainMenu)
    }

    /// Show the pause menu. Do not resume on didBecomeActive; the player resumes.
    func pause() {
        isPaused = true
    }
}
```

## Launch, onboarding, and requests

General onboarding rules (tips over tours, a skippable flow that never
reappears, permission at first use) are in
`apple-design/references/hig-patterns.md` § Onboarding. What is particular to
games:

- **Playable at install.** Ship enough content in the initial install to play
  without waiting, and keep the initial download to 30 minutes or less. The
  base install must not be just a launcher for a second download. Fetch the
  rest in the background (`assets.md`).
- **Interactive within a couple of seconds.** Draw something at once; a blank
  screen reads as a hang. Let players browse menus or a level briefing while
  content streams. For a long load, size the hints to the measured remaining
  time. A custom, styled loading view is fine in a game.
- **A splash screen belongs at the start of onboarding**, not in the launch
  sequence, and stays up only long enough to read.
- **Teach through play.** Fold controls and configuration into a playable
  tutorial. A written tutorial is a reference the player can open, not a
  prerequisite.
- **Ask for permissions inside the moment that needs them.** The HIG's
  example asks for hand tracking between the opening cutscene and the first
  time the hands control anything. On Mac and iPhone the same applies to the
  microphone for voice chat and to local network access for LAN play.
- **Ratings after real play.** Ask at a natural break, such as a completed
  level; never on first launch, in onboarding, or mid-play; and allow a week
  or two between requests. `RequestReviewAction` (macOS 13, iOS 16) may show
  nothing. StoreKit shows the prompt at most three times in 365 days to a
  player who has not rated the game. It shows it to one who has rated only
  for a new version, after 365 days. Players can also opt out for all apps.
  For that reason StoreKit says never to call it from a button tap.

## Game Center presentation

The HIG frames Game Center as a discovery channel as much as a social
feature. Activity from a signed-in player shows in the Apple Games app, the
App Store, and notifications, and feeds the Top Played chart and friend
recommendations. Check sign-in at launch and initialize the local player
then (`game-center-and-online.md` has the authentication API).

**Developer ID gate.** A Mac game distributed outside the Mac App Store
with Developer ID cannot use Game Center: Apple's supported-capabilities
table for macOS marks Game Center (with In-App Purchase and Sign in with
Apple) as Apple Developer Program distribution only. Decide the distribution
channel before designing around Game Center
(`game-center-and-online.md`, `app-release/references/direct-distribution.md`).

**The access point** is Apple's own control. On Mac, iPhone, and iPad it opens
the Game Overlay; on tvOS and visionOS it opens a full-screen dashboard.

- **Show it on the main menu, optionally in settings, and nowhere else.** Hide
  it in gameplay, cutscenes, splash screens, and any tutorial before the main
  menu. GameKit's article says to hide it in settings too; the HIG allows
  the settings area. The HIG governs design, so either choice conforms.
- **Pick one corner and keep controls out of it.** The access point has a
  collapsed and an expanded size. The default is the top leading corner,
  which flips in right-to-left languages. To keep clear of it,
  `frameInScreenCoordinates` (an `NSRect` on macOS) is observable; convert it
  from screen coordinates before comparing with your layout.
- **On the Mac, set `parentWindow`** to the window that shows the menu.
  Otherwise GameKit picks the app's main window.
- **Pause while the overlay is up** (`isPresentingGameCenter`, above).
- **Do not set `showHighlights`.** GameKit's access-point article still sets
  it. The shipped `GKAccessPoint.h` deprecates it from 26.0 as "No longer
  supported", and the symbol page shows no deprecation.

**Custom Game Center UI** may deep-link into the overlay (leaderboards, a
profile) with Apple's artwork unaltered and Apple's exact terms: "Game Center"
(not GameKit or GameCenter), "Game Center Profile", "Achievements" (not
trophies), "Leaderboards", "Challenges", "Add Friends".

**Entering from the Games app.** Players start challenges and multiplayer
activities from the Games app, the overlay, or an invite link, and the system
deep-links into the game:

- Route to the exact mode or level on a warm launch and on a cold launch
  after a force quit.
- Do not interrupt with unrelated content (news, an event banner) while the
  challenge loads.
- Send a first-time player through the tutorial first, and say that the
  challenge follows.
- If the content needs more progression, tell the player what unlocks it.

For party codes, the HIG asks for late join, early leave and rejoin, the
current code visible in game, and manual code entry. Challenges should take 1 to
5 minutes and score the most recent attempt, not a personal best, so that an
invited newcomer is not beaten by construction. Artwork sizes for
achievements, leaderboards, challenges, and activities are on the HIG Game
Center page (and in `assets.md`).

## Apple In-App Purchase in a game

Designing-for-games links the Apple In-App Purchase page. The game-specific
points:

- **The four types, in game terms.** Consumable: lives, gems, boosts that run
  out and can be bought again. Non-consumable: a permanent unlock.
  Auto-renewable subscription. Non-renewing subscription: time-boxed access
  such as a battle pass, bought again to extend it.
- **Let players play before selling.** Style the store as part of the game,
  and show the full billing price on every item.
- **Hide or explain the store when `AppStore.canMakePayments` is false.**
  Screen Time restrictions or an MDM profile block purchases.
- **Never imitate or alter the system purchase sheet.**

Purchase prompts, like ratings, come after engagement. Developer ID Mac
builds cannot use In-App Purchase (see "Game Center presentation").

## Gates: tvOS and visionOS

Out of scope except where they change what a Mac, iPhone, or iPad build must
contain:

- The text and button tables have tvOS (29/23 pt text, 66x66/56x56 pt
  buttons) and visionOS (17/12 pt text, 60x60/28x28 pt buttons) rows. A game
  that later ships there cannot reuse the Mac or iPhone sizes.
- `GCRequiresControllerUserInteraction`'s `visionOS` entry also applies to an
  iPhone or iPad build running on Vision Pro as a compatible app. Set it only
  if the game has no input but a controller there.
- On visionOS and tvOS the access point opens a dashboard, and on visionOS
  its placement depends on whether the game is windowed, volumetric, or
  immersive (`game-center-and-online.md`).

## Where else to look

- `input.md`: controller, keyboard, mouse, and Touch Controller APIs; glyphs;
  remapping.
- `game-loop-and-threading.md`: full screen, the Dock, deferring edges, the
  cursor, Game Mode, power and thermal state.
- `audio-and-haptics.md`: audio session and interruptions, the haptics off
  switch.
- `game-center-and-online.md`: GameKit APIs, GameSave, Developer ID
  capability limits.
- `assets.md`: Background Assets, initial download size, Game Center artwork.
- `apple-design`: general layout, typography, color, onboarding, settings
  windows, accessibility review.
- `apple-macos`: AppKit windows and the menu bar.
