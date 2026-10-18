> verified: 2026-10 against https://developer.apple.com/documentation/gamecontroller.md, https://developer.apple.com/documentation/gamecontroller/discovering-game-controllers.md, https://developer.apple.com/documentation/gamecontroller/handling-input-events.md, https://developer.apple.com/documentation/gamecontroller/input.md, https://developer.apple.com/documentation/gamecontroller/deprecated-symbols.md, https://developer.apple.com/documentation/gamecontroller/gccontroller/input.md, https://developer.apple.com/documentation/gamecontroller/gccontroller/didconnectmessage.md, https://developer.apple.com/documentation/gamecontroller/gccontroller/shouldmonitorbackgroundevents.md, https://developer.apple.com/documentation/gamecontroller/gccontrollerliveinput.md, https://developer.apple.com/documentation/gamecontroller/gcdevice/handlerqueue.md, https://developer.apple.com/documentation/gamecontroller/gcdevicephysicalinput/queue.md, https://developer.apple.com/documentation/gamecontroller/gcdevicephysicalinput/capture().md, https://developer.apple.com/documentation/gamecontroller/gcdevicephysicalinput/inputstatequeuedepth.md, https://developer.apple.com/documentation/gamecontroller/gcdevicephysicalinput/nextinputstate().md, https://developer.apple.com/documentation/gamecontroller/gcdevicephysicalinputstate/lasteventtimestamp.md, https://developer.apple.com/documentation/gamecontroller/gcphysicalinputelementcollection-swift.struct.md, https://developer.apple.com/documentation/gamecontroller/gckeyboard.md, https://developer.apple.com/documentation/gamecontroller/gckeyboard/coalesced.md, https://developer.apple.com/documentation/gamecontroller/gckeyboardinput.md, https://developer.apple.com/documentation/gamecontroller/gckeyboardinput/keychangedhandler.md, https://developer.apple.com/documentation/gamecontroller/gckeycode.md, https://developer.apple.com/documentation/gamecontroller/gcmouse.md, https://developer.apple.com/documentation/gamecontroller/gcmouse/didconnectmessage.md, https://developer.apple.com/documentation/gamecontroller/gcmouseinput.md, https://developer.apple.com/documentation/gamecontroller/gcmouseinput/mousemovedhandler.md, https://developer.apple.com/documentation/gamecontroller/gcdevicehaptics.md, https://developer.apple.com/documentation/gamecontroller/gcdevicehaptics/createengine(withlocality:).md, https://developer.apple.com/documentation/gamecontroller/gchapticslocality.md, https://developer.apple.com/documentation/gamecontroller/gcvirtualcontroller.md, https://developer.apple.com/documentation/gamecontroller/adding-virtual-controls-to-games-that-support-game-controllers-in-ios.md, https://developer.apple.com/documentation/gamecontroller/discovering-and-tracking-spatial-game-controllers-and-styli.md, https://developer.apple.com/documentation/gamecontroller/gcphysicalinputprofile/hasremappedelements.md, https://developer.apple.com/documentation/gamecontroller/gcphysicalinputprofile/mappedelementalias(forphysicalinputname:).md, https://developer.apple.com/documentation/gamecontroller/gcphysicalinputprofile/mappedphysicalinputnames(forelementalias:).md, https://developer.apple.com/documentation/gamecontroller/gcphysicalinputsource.md, https://developer.apple.com/documentation/gamecontroller/gcphysicalinputelement/localizedname.md, https://developer.apple.com/documentation/gamecontroller/gccontrollerelement/sfsymbolsname.md, https://developer.apple.com/documentation/gamecontroller/gccontrollerelement/unmappedsfsymbolsname.md, https://developer.apple.com/documentation/gamecontroller/gccontrollerelement/preferredsystemgesturestate.md, https://developer.apple.com/documentation/gamecontroller/gccontrollerusercustomizationsdidchangenotification.md, https://developer.apple.com/documentation/gamecontroller/gccontrollerhomebuttonsettingsmanager-258mu.md, https://developer.apple.com/documentation/gamecontroller/gccontrollerhomebuttonsettingsmanager-258mu/controllerhomebuttoninappaction.md, https://developer.apple.com/documentation/gamecontroller/gccontrollerhomebuttonsettingsmanager-258mu/settingsupdates.md, https://developer.apple.com/documentation/gamecontroller/gccontrollerhomebuttonsettingsmanager-258mu/opencontrollerhomebuttonsettings(for:).md, https://developer.apple.com/documentation/gamecontroller/gccontrollerhomebuttonsettinginappaction.md, https://developer.apple.com/documentation/gamecontroller/understanding-game-controller-backward-compatibility.md, https://developer.apple.com/documentation/gamecontroller/racing-wheel-device-support.md, https://developer.apple.com/documentation/touchcontroller.md, https://developer.apple.com/documentation/touchcontroller/tctouchcontroller.md, https://developer.apple.com/documentation/touchcontroller/tctouchcontroller/issupported.md, https://developer.apple.com/documentation/touchcontroller/tctouchcontroller/render(using:).md, https://developer.apple.com/documentation/touchcontroller/tctouchcontroller/handletouchbegan(at:index:).md, https://developer.apple.com/documentation/touchcontroller/tctouchcontrollerdescriptor.md, https://developer.apple.com/documentation/metal/managing-your-game-window-for-metal-in-macos.md, https://developer.apple.com/documentation/metal/reading-pixel-data-from-a-drawable-texture.md, https://developer.apple.com/documentation/appkit/mouse-keyboard-and-trackpad.md, https://developer.apple.com/documentation/appkit/gestures.md, https://developer.apple.com/documentation/appkit/nsresponder/keydown(with:).md, https://developer.apple.com/documentation/appkit/nsevent/addlocalmonitorforevents(matching:handler:).md, https://developer.apple.com/documentation/appkit/adopting-the-system-text-cursor-in-custom-text-views.md, https://developer.apple.com/documentation/appkit/nscursor/hide().md, https://developer.apple.com/documentation/coregraphics/cgassociatemouseandmousecursorposition(_:).md, https://developer.apple.com/documentation/coregraphics/cgwarpmousecursorposition(_:).md, https://developer.apple.com/documentation/uikit/uiviewcontroller/preferspointerlocked.md, https://developer.apple.com/documentation/uikit/uipointerlockstate/islocked.md, https://developer.apple.com/documentation/uikit/uiviewcontroller/preferredscreenedgesdeferringsystemgestures.md, https://developer.apple.com/documentation/bundleresources/information-property-list/uiapplicationsupportsindirectinputevents.md, https://developer.apple.com/design/human-interface-guidelines/game-controls.md
> typecheck: macos 26.0, ios 26.0

# Input: Game Controller, Keyboard and Mouse, Touch, and Remapping

Scope: getting player intent into the simulation on a Mac first, then iPhone and
iPad. The frame loop that consumes it, full screen, and the cursor's look are in
`game-loop-and-threading.md`. Core Haptics itself is in `audio-and-haptics.md`.
Control layout and button-label conventions are in `game-design.md`.

Contents:
- Choosing the input path
- Discovering controllers
- Reading controller input
- Keyboard and mouse on the Mac
- AppKit events where Game Controller does not reach
- Mouse-look and pointer lock
- Touch controls on iPhone and iPad
- Controller haptics
- Remapping and the Home button
- Mac only: synthetic HID devices and racing wheels
- Where else to look

## Choosing the input path

One rule covers most of it: read gameplay input through Game Controller, and
use AppKit or UIKit only for what Game Controller does not model.

| Input | Read it with | Platforms and gates |
| --- | --- | --- |
| Gamepads, arcade sticks | `GCController.input` (`GCControllerLiveInput`) | macOS 14, iOS 17; always present at this file's 26.0 floor |
| Keys as buttons | `GCKeyboard.coalesced?.keyboardInput` | macOS 11, iOS 14 |
| Typed text, IME, dictation | AppKit `NSTextInputClient` / UIKit text views | Not Game Controller at all |
| Raw mouse deltas, buttons, wheel | `GCMouse.current?.mouseInput` | macOS 11, iOS 14 |
| Cursor position | `NSEvent.mouseLocation` / `UIHoverGestureRecognizer` | `GCMouseInput` reports deltas only |
| Trackpad pinch and rotate on Mac | `NSMagnificationGestureRecognizer`, `NSRotationGestureRecognizer` | macOS |
| On-screen controls for a Metal game | Touch Controller (`TCTouchController`) | iOS and iPadOS 26 only |
| On-screen controls, UIKit overlay | `GCVirtualController` | iOS 15; no macOS header |
| Racing wheels | `GCRacingWheel` | macOS 13 only |

Set up the project with the Game Controllers capability. It writes
`GCSupportsControllerUserInteraction` and the `GCSupportedGameControllers`
profile list into Info.plist. With a generated Info.plist the first key is the
build setting `INFOPLIST_KEY_GCSupportsControllerUserInteraction`. Support the
platform's default input as well: every Mac has a keyboard and a pointing
device, and a controller is an optional purchase on every platform here.

## Discovering controllers

- **Never trust one launch-time poll.** `GCController.controllers()` returns
  an empty array when nothing is connected. Apple's spatial-controller article
  adds that the check is not synchronous and can come back empty while a
  controller is connected. Read the array once, then rely on the connect and
  disconnect notifications.
- **Connecting a controller to a Mac shows a system prompt** that the player
  must approve before the game sees the pad. iOS and iPadOS connect a USB
  controller automatically. "No controller yet" at launch on a Mac is not
  final.
- **The 26 SDKs add typed, main-actor messages** for connection:
  `GCController.DidConnectMessage` and friends, observed with
  `NotificationCenter.addObserver(of:for:using:)`. They are macOS 26 / iOS 26,
  so they sit at this file's floor, and they spare the `notification.object`
  cast that the older `.GCControllerDidConnect` pattern needs.
- **Choose the primary pad deliberately.** Filter out on-screen controllers
  (Apple's sample compares `productCategory` with `"Touch Controller"`), then
  prefer a pad where `isAttachedToDevice` is true, such as an iPhone clipped
  into a controller. Otherwise use connection order. Set `playerIndex`
  (`.index1` to `.index4`) per player: it lights the matching LED where the pad
  has one, and `.indexUnset` releases it.
- **A Mac game stops receiving controller input when it is not frontmost.**
  `GCController.shouldMonitorBackgroundEvents` defaults to `false` on macOS 11.3
  and later, and iOS ignores the property. Runtime-checked: a binary built at
  the 26.0 floor read `false` on macOS 27.0.1. Leave it off unless the app is
  a tool that must see input while another app has focus.

```swift
import GameController

@MainActor
final class ControllerRoster {
    private(set) var controllers: [GCController] = []
    private var tokens: [NotificationCenter.ObservationToken] = []

    func start() {
        controllers = GCController.controllers()
        let center = NotificationCenter.default
        tokens.append(center.addObserver(of: GCController.self, for: .didConnect) { [weak self] (message: GCController.DidConnectMessage) in
            self?.controllers.append(message.controller)
        })
        tokens.append(center.addObserver(of: GCController.self, for: .didDisconnect) { [weak self] (message: GCController.DidDisconnectMessage) in
            self?.controllers.removeAll { $0 === message.controller }
        })
    }

    /// The pad to drive player one: physical first, attached first.
    var primary: GCController? {
        let physical = controllers.filter { $0.productCategory != "Touch Controller" }
        return physical.first(where: { $0.isAttachedToDevice }) ?? physical.first
    }
}
```

## Reading controller input

**Use `GCController.input`.** It is the `GCControllerLiveInput` model, gated
macOS 14 / iOS 17, so it is always available at a 26.0 floor. The snapshot
classes are deprecated: `GCGamepad`, `GCGamepadSnapshot`,
`GCExtendedGamepadSnapshot`, `GCMicroGamepadSnapshot`, and the `*SnapshotData`
structs and functions. A frozen copy of the state now comes from `capture()`.
The older `extendedGamepad` and `physicalInputProfile` profiles still compile
and still drive Apple's discovery sample. Keep them only in code that already
uses them, and do not start a new input layer on them.

**The element subscripts return optionals.** `input.buttons[.a]`,
`input.dpads[.leftThumbstick]`, `axes`, and `switches` are all
`subscript(_:) -> T?` in the shipped `GameController.swiftinterface`: a pad
need not have every element. Apple's article shows
`input.buttons[.a].pressedInput.isPressed` as a one-liner, and that does not
compile. Unwrap with `?` or `if let`, as the snippets below do. The same
article's later snippets do unwrap.

**Move input off the main queue.** Callbacks run on the device's
`handlerQueue`, which is the main queue by default. Set
`GCControllerLiveInput.queue` to your input queue before you install any
handler, or input waits behind main-thread UI work.

**Pick polling or buffering per device rate.**

- Polling once per simulation tick: call `capture()` once and read every
  element from that one `GCControllerInputState`. A single element read is
  atomic, but two separate reads from the live input can straddle an update.
  Apple says snapshots are cheap while you do not hold them for long.
- Buffered: a high-rate racing wheel reports hundreds of inputs per second,
  and a per-frame poll misses most of them. Raise `inputStateQueueDepth` from its default of 1
  (no buffering; the header calls 20 more than enough) and drain
  `nextInputState()` until it returns `nil`. `inputStateAvailableHandler` fires
  once when the queue becomes non-empty, and not again until you drain it, so
  it can wake an event-driven loop.
- Overflow is visible: `changedElements()` returns `nil` and `change(for:)`
  returns `.unknownChange`. Treat that state as a resync from absolute values,
  not as a diff.
- `lastEventTimestamp` orders events, also across devices. It has no fixed
  epoch, so use only differences between values.

```swift
import GameController

struct PadSample {
    var move = SIMD2<Float>.zero
    var jumpHeld = false
}

/// Call before installing any handler: callbacks default to the main queue.
func prepare(_ input: GCControllerLiveInput, queue: DispatchQueue, buffered: Bool) {
    input.queue = queue
    if buffered { input.inputStateQueueDepth = 20 }
}

/// Polling: one snapshot per simulation tick.
func samplePad(_ input: GCControllerLiveInput) -> PadSample {
    let state = input.capture()
    var sample = PadSample()
    if let stick = state.dpads[.leftThumbstick] {
        sample.move = SIMD2(stick.xAxis.value, stick.yAxis.value)
    }
    sample.jumpHeld = state.buttons[.a]?.pressedInput.isPressed ?? false
    return sample
}

/// Buffering: every queued state since the last tick, oldest first.
func drainJumps(_ input: GCControllerLiveInput, onJump: (TimeInterval) -> Void) {
    while let state = input.nextInputState() {
        guard let a = state.buttons[.a] else { continue }
        switch state.change(for: a) {
        case .changed where a.pressedInput.isPressed:
            onJump(state.lastEventTimestamp)
        case .unknownChange:
            break   // queue overflowed: resync from absolute values
        default:
            break
        }
    }
}
```

Event-driven code uses `pressedInput.pressedDidChangeHandler` per element, or
one `elementValueDidChangeHandler` on the live input, which fires once for each
changed element. `GCLinearInput.physicalExtents` converts a normalized value to
physical units, but it is macOS 26.2 / iOS 26.2, above this file's floor: gate
it with `if #available`.

## Keyboard and mouse on the Mac

- **`GCKeyboard` is for keys as buttons.** All connected keyboards merge into
  one `GCKeyboard.coalesced` object, so the connect notification arrives once.
  Poll `keyboardInput.button(forKeyCode:)` per tick, or keep a held-key set
  from `keyChangedHandler`, which fires once per changed key. `GCKeyCode`
  values are low-level key codes. The header says to use AppKit or UIKit for
  text, and the next section covers that.
- **`GCMouse` gives raw deltas.** `mouseMovedHandler` receives `deltaX` and
  `deltaY` that the header says ignore the system mouse-sensitivity setting, so
  the game's own sensitivity slider is the only scale. The profile has
  `leftButton`, optional `rightButton` and `middleButton`, `auxiliaryButtons`,
  and `scroll`. It has no cursor position. Track `GCMouse.current` and its
  became-current notifications when several mice are attached.
- **Allow rebinding.** The HIG asks for single-key commands near WASD,
  Command where a PC binding uses Control, and player-editable bindings. Keep a
  table from action to `GCKeyCode` that the player edits.

```swift
import GameController
import simd

/// WASD as a movement vector, read once per tick.
func wasd(_ keyboard: GCKeyboardInput) -> SIMD2<Float> {
    func held(_ key: GCKeyCode) -> Float {
        keyboard.button(forKeyCode: key)?.isPressed == true ? 1 : 0
    }
    let raw = SIMD2(held(.keyD) - held(.keyA), held(.keyW) - held(.keyS))
    return raw == .zero ? raw : simd_normalize(raw)
}
```

## AppKit events where Game Controller does not reach

The Metal view sits in the AppKit responder chain (`NSApplication`, `NSWindow`,
and `NSView` all inherit from `NSResponder`). To receive key events it must
accept first responder.

- **Stop the window consuming keys.** Apple's macOS game-window article says
  that AppKit and Game Controller can interact so that `NSWindow` consumes key
  events meant for Game Controller. The fix it gives is an empty
  `keyDown(with:)` on the window subclass. The default `NSResponder`
  implementation passes the event up the chain.
- **Text entry is AppKit's job.** Raw key codes do not compose CJK input,
  dead keys, or dictation. For a chat box drawn in Metal, adopt
  `NSTextInputClient` and drive it through the view's `NSTextInputContext`.
  `NSTextInput` is its predecessor, deprecated since 10.6 (`NSInputManager.h`). On macOS 14 and later, layer an
  `NSTextInsertionIndicator` over the text area to get the system caret, the
  input-language and Caps Lock accessories, and the dictation effect. Set its
  `displayMode` to `.automatic` when the field becomes first responder and to
  `.hidden` when it resigns, and move its `frame` with the caret. Where a real
  field is acceptable, such as a login or a server address, overlay an
  `NSTextField` and get all of this for free.
- **Trackpad gestures** arrive through recognizers attached to the game view.
  `NSMagnificationGestureRecognizer` (pinch, for example camera zoom) and
  `NSRotationGestureRecognizer` are continuous. `NSClickGestureRecognizer` and
  `NSPressGestureRecognizer` are discrete. `NSPressureConfiguration` gives
  Force Touch pressure behavior.
- **A local event monitor** (`NSEvent.addLocalMonitorForEvents(matching:handler:)`)
  sees events before dispatch, and returning `nil` drops the event. It never
  sees events that a nested tracking loop consumes, such as a menu or a window
  drag. Call `removeMonitor(_:)` when you are done.
- **Click to drawable pixel.** Convert the window point to the view, then to
  backing pixels, then flip y, because AppKit is bottom-up and Metal textures
  are top-down. On iOS, multiply by `contentScaleFactor` and do not flip. Apple's
  sample converts `locationInWindow` straight to backing pixels. That is
  correct only when the view fills the window. Both mappings assume the
  drawable tracks the view's backing size. A fixed `drawableSize` needs one
  more scale.

```swift
import AppKit
import MetalKit

final class GameWindow: NSWindow {
    // Empty on purpose: keeps AppKit from consuming keys Game Controller needs.
    override func keyDown(with event: NSEvent) {}
}

extension MTKView {
    /// A mouse event's location as the centre of a top-down drawable pixel.
    func drawablePixel(for event: NSEvent) -> CGPoint {
        let inView = convert(event.locationInWindow, from: nil)
        let backing = convertToBacking(inView)
        return CGPoint(x: backing.x.rounded(.down) + 0.5,
                       y: (drawableSize.height - backing.y).rounded(.down) + 0.5)
    }
}
```

## Mouse-look and pointer lock

**Mac.** Call `CGAssociateMouseAndMouseCursorPosition(0)` to disconnect the
cursor from the mouse. Events then report a constant location and carry only
deltas, so mouse-look no longer stops at a screen edge. Hide the cursor
with `NSCursor.hide()`. Every `hide()` needs a matching `unhide()`, and it
overrides `setHiddenUntilMouseMoves(_:)`. `CGWarpMouseCursorPosition(_:)`
moves the cursor without posting an event, for example back to the window
centre when you release the lock. Release the lock when the game opens a menu
or loses focus, or the player is left without a cursor. Read motion from the
event deltas or from the raw deltas of `GCMouse`.

```swift
import AppKit
import CoreGraphics

@MainActor
enum MouseLook {
    private(set) static var engaged = false

    static func engage() {
        guard !engaged else { return }
        _ = CGAssociateMouseAndMouseCursorPosition(0)
        NSCursor.hide()
        engaged = true
    }

    /// Call on menu open, window resign-key, and app deactivation.
    static func release() {
        guard engaged else { return }
        _ = CGAssociateMouseAndMouseCursorPosition(1)
        NSCursor.unhide()
        engaged = false
    }
}
```

**iPad.** Override `prefersPointerLocked` on the view controller and call
`setNeedsUpdateOfPrefersPointerLocked()` when the answer changes. It is a
request (iOS 14). The system considers it only when the scene is full screen,
with no Split View or Slide Over, and in `.foregroundActive`. It drops the lock
when those conditions end. Read the outcome from the scene's
`pointerLockState?.isLocked`, which posts `UIPointerLockState.didChangeNotification`.
Do not infer it from your own flag. While the lock holds, use `GCMouse` deltas,
as on the Mac.

**Edge gestures.** On iPhone and iPad, override
`preferredScreenEdgesDeferringSystemGestures` to let the game's gestures win at
the named edges (iOS 11, not tvOS), and call
`setNeedsUpdateOfScreenEdgesDeferringSystemGestures()` when the edges change.
Apple asks you to defer only where gameplay needs it. From iOS 17, a missing
`UIApplicationSupportsIndirectInputEvents` key means `YES`. Clicks from a
trackpad or mouse then arrive as `.indirectPointer` touches, and pinches drive
`UIPinchGestureRecognizer` with no touches behind them. A recognizer that calls
`location(ofTouch:in:)` on such an event raises an exception.

```swift
import UIKit

final class GameViewController: UIViewController {
    var mouseLook = false {
        didSet { setNeedsUpdateOfPrefersPointerLocked() }
    }

    override var prefersPointerLocked: Bool { mouseLook }
    override var preferredScreenEdgesDeferringSystemGestures: UIRectEdge { .bottom }

    /// What the system granted, which can differ from what was asked.
    var pointerIsLocked: Bool {
        view.window?.windowScene?.pointerLockState?.isLocked ?? false
    }
}
```

## Touch controls on iPhone and iPad

Neither framework exists on the Mac: the macOS SDK has no `GCVirtualController.h`
and no Touch Controller framework. Wrap both in `#if os(iOS)`.

| | Touch Controller | `GCVirtualController` |
| --- | --- | --- |
| Gate | iOS and iPadOS 26; `API_UNAVAILABLE(macCatalyst, visionos)`; absent from macOS and tvOS SDKs | iOS 15; `API_UNAVAILABLE(macos, tvos, visionos)` |
| Draws | Into your Metal pass, through `render(using:)` | A system UIKit overlay, or nothing (`hidden`, iOS 17) |
| Controls | `TCButton`, `TCThumbstick`, `TCDirectionPad`, `TCSwitch`, `TCThrottle`, `TCTouchpad` | The `GCInput…` elements you list |
| Touches | You forward each touch with an index | UIKit handles them |
| Reads as | `TCTouchController.controller`, a `GCController` | `GCVirtualController.controller`, a `GCController` |

Apple's discovery article gives the choice: with no physical pad, use Touch
Controller for a Metal game and `GCVirtualController` otherwise. Both surface a
`GCController`, so gameplay reads one input path for touch and hardware.

**Touch Controller specifics** (iOS 26, from `TCTouchController.h`):

- Check `TCTouchController.isSupported` first. Creating one on an unsupported
  device is a fatal error, not a `nil`.
- Build the descriptor from your drawable's formats. It takes a device,
  `size` (points), `drawableSize` (pixels), color, depth, and stencil pixel
  formats, and `sampleCount`. `init(mtkView:)` copies them from an `MTKView`.
  Keep `size` and `drawableSize` in sync on every resize.
- Add controls one by one (`addButton(descriptor:)`, `addThumbstick(descriptor:)`,
  and so on), or call `automaticallyLayoutControls(for:)` with `TCControlLabel`
  values such as `.leftThumbstick` and `.buttonA`. Call `connect()` to create
  the `GCController` and start drawing.
- Forward every UIKit touch with `handleTouchBegan(at:index:)`,
  `handleTouchMoved(at:index:)`, and `handleTouchEnded(at:index:)`, using a
  stable integer per touch. A `true` result means a control consumed the touch,
  so keep it out of direct-touch gameplay such as camera drag.
- **It draws only through a Metal 3 encoder.** `render(using:)` takes an
  `MTLRenderCommandEncoder`. The iOS 27.1 SDK header has no
  `MTL4RenderCommandEncoder` variant. A Metal 4 renderer therefore keeps a
  Metal 3 `MTLCommandQueue` beside its `MTL4CommandQueue`, as it would for
  MPS (`apple-metal/references/command-model.md`,
  `## Maintaining older code: Metal 3`). It draws the controls into an overlay
  texture on that queue and orders the two with an event before the Metal 4
  pass composites the overlay. The drawable then stays on the Metal 4 queue
  alone, so the present sequence in
  `apple-metal/references/display-and-upscaling.md` applies unchanged.

```swift
import Metal
import TouchController
import UIKit

/// Touch controls for a Metal 4 renderer, drawn on a Metal 3 queue into
/// overlay textures that the Metal 4 frame composites last.
@MainActor
final class TouchOverlay {
    let touch: TCTouchController
    private let queue: any MTLCommandQueue          // Metal 3, beside the MTL4CommandQueue
    private let overlays: [any MTLTexture]          // one per frame in flight; .renderTarget + .shaderRead
    private let drawn: any MTLSharedEvent
    private var frame: UInt64 = 0

    init?(device: any MTLDevice, overlays: [any MTLTexture], points: CGSize) {
        guard TCTouchController.isSupported,          // otherwise creating one is a fatal error
              let first = overlays.first,
              let queue = device.makeCommandQueue(),
              let drawn = device.makeSharedEvent() else { return nil }
        let descriptor = TCTouchControllerDescriptor()
        descriptor.device = device
        descriptor.size = points
        descriptor.drawableSize = CGSize(width: first.width, height: first.height)
        descriptor.colorPixelFormat = first.pixelFormat
        descriptor.sampleCount = 1
        touch = TCTouchController(descriptor: descriptor)
        touch.automaticallyLayoutControls(for: [.leftThumbstick, .buttonA, .buttonB, .buttonMenu])
        touch.connect()
        self.queue = queue
        self.overlays = overlays
        self.drawn = drawn
    }

    /// True when a control took the touch; gameplay should then ignore it.
    func began(_ uiTouch: UITouch, in view: UIView) -> Bool {
        touch.handleTouchBegan(at: uiTouch.location(in: view), index: uiTouch.hash)
    }

    /// Encode this frame's controls, then make the Metal 4 queue wait for them.
    /// Returns the texture the Metal 4 composite pass samples.
    func encode(before metal4Queue: any MTL4CommandQueue) -> (any MTLTexture)? {
        frame += 1
        let target = overlays[Int(frame % UInt64(overlays.count))]
        let pass = MTLRenderPassDescriptor()
        pass.colorAttachments[0].texture = target
        pass.colorAttachments[0].loadAction = .clear
        pass.colorAttachments[0].clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 0)
        pass.colorAttachments[0].storeAction = .store
        guard let buffer = queue.makeCommandBuffer(),
              let encoder = buffer.makeRenderCommandEncoder(descriptor: pass) else { return nil }
        touch.render(using: encoder)
        encoder.endEncoding()
        buffer.encodeSignalEvent(drawn, value: frame)
        buffer.commit()
        metal4Queue.waitForEvent(drawn, value: frame)   // GPU-side wait, before the composite commit
        return target
    }
}
```

The ring of overlays assumes the Metal 4 frame that samples a texture has
finished before the ring comes back to it. That holds when the ring length
equals your frames-in-flight bound. The overlay textures must also be in the
Metal 4 queue's residency set. A Metal 3 renderer passes its own final-pass
encoder to `render(using:)` and needs none of this.

**`GCVirtualController` specifics.** Build it in `viewDidLoad` from a
configuration whose `elements` lists only the inputs your code already handles.
Connect it at game start, and in the disconnect handler, when `controllers()`
is empty. Disconnect it when a controller other than `.controller` connects.
Connections are asynchronous, so the physical pad's notification can arrive
before the virtual one: compare against `.controller` instead of counting. For
custom-drawn controls (iOS 17), set the configuration's `hidden` but keep
`elements`, because they define the synthesized pad. Then feed it from your own
recognizers with `setValue(_:forButtonElement:)` and
`setPosition(_:forDirectionPadElement:)`. Apple's article roots the view
controller in `GCEventViewController`. Its code blocks are Objective-C under a
Swift label, so do not paste them into a Swift file.

```swift
import GameController

@MainActor
final class VirtualPad {
    private let pad: GCVirtualController

    init() {
        let configuration = GCVirtualController.Configuration()
        configuration.elements = [GCInputLeftThumbstick, GCInputButtonA, GCInputButtonB]
        pad = GCVirtualController(configuration: configuration)
    }

    /// Call at game start and from both connection notifications.
    func controllersChanged() {
        let all = GCController.controllers()
        if all.isEmpty {
            pad.connect(replyHandler: nil)
        } else if all.contains(where: { $0 !== pad.controller }) {
            pad.disconnect()
        }
    }
}
```

Touch-control layout rules are in `game-design.md`. They cover movement on the
left and camera on the right, 44×44 pt primary controls, and press states.

## Controller haptics

Controller rumble is Core Haptics on an engine the controller vends.
`GCController.haptics` is `nil` when the pad has none. Otherwise
`createEngine(withLocality:)` returns a `CHHapticEngine?` whose patterns play on
the actuators you name: `.default` (normally the handles), `.all`, `.handles`,
`.leftHandle`, `.rightHandle`, `.triggers`, `.leftTrigger`, and `.rightTrigger`.
`.default` and `.all` are always supported. Check others in
`supportedLocalities`.

- **Do not gate on the engine's capabilities.** For an engine from
  `createEngine(withLocality:)`, `CHHapticDeviceCapability.supportsHaptics`
  describes the host device, not the controller, so it can report no haptics
  for a pad that has them. `supportedLocalities` is the controller's own
  answer.
- **The Mac gets controller haptics.** `GCDeviceHaptics.h` declares the class
  `API_AVAILABLE(macos(11.0), ios(14.0), tvos(14.0))`, so the same
  `CHHapticPattern` code that drives an iPhone's actuator drives a DualSense or
  Xbox pad on a Mac. Apple's Core Haptics sample for controllers lists only
  iOS; the SDK wins.
- Patterns, engine lifecycle, and resets belong in `audio-and-haptics.md`.

```swift
import CoreHaptics
import GameController

/// Engines for the pad's handles and, where present, its triggers.
func rumbleEngines(for controller: GCController) -> (handles: CHHapticEngine?, triggers: CHHapticEngine?) {
    guard let haptics = controller.haptics else { return (nil, nil) }
    let handles = haptics.createEngine(withLocality: .default)
    let triggers = haptics.supportedLocalities.contains(.triggers)
        ? haptics.createEngine(withLocality: .triggers) : nil
    return (handles, triggers)
}
```

## Remapping and the Home button

Players remap controller buttons system-wide, in Settings on iOS and System
Settings on macOS. The live input you read already has the remap applied: if A
and B are swapped, `buttons[.a]` reports the physical B press. Most games
should therefore do no controller remapping of their own and just label
prompts correctly.

- **Label prompts with the element's own name and symbol.** Show
  `localizedName` and `sfSymbolsName` of the element you read. Both reflect the
  remap and the connected brand's glyphs. The header says not to cache them.
  Refresh on `GCControllerUserCustomizationsDidChangeNotification` (macOS 13 /
  iOS 16, posted on the main thread, with the controller as its object). With
  several pads, show the glyphs of the one in use.
- **A game with its own remap UI** reads `controller.input.unmapped`. The
  header spells it `unmappedInput`, and the Swift name is `unmapped`, which
  compiles. Each input's `sources` (`GCPhysicalInputSource`: `elementAliases`,
  `elementLocalizedName`, `sfSymbolsName`) describe what the player physically
  touched, even on the mapped input. `GCControllerElement.unmappedSfSymbolsName` and
  `unmappedLocalizedName` serve the same UI on the older profiles. There,
  `hasRemappedElements` together with `mappedElementAlias(forPhysicalInputName:)`
  and `mappedPhysicalInputNames(forElementAlias:)` translate names. Apple asks
  apps to send players to the system settings instead of building this.
- **System gestures on buttons.** By default the system runs its own
  recognizers, such as an Options long-press screenshot, before input reaches
  the game. Setting an element's `preferredSystemGestureState` to `.disabled`
  asks for raw input, and the docs say the system may ignore the request.
  `.alwaysReceive` is deprecated in the 27 SDKs in favor of `.disabled`.

**The Home button settings manager (OS 27).** `GCControllerHomeButtonSettingsManager`
is `NS_REFINED_FOR_SWIFT` in the headers. Its Swift spelling, from the shipped
swiftinterface, is a Swift class with a main-actor `init()`, two
`get throws` properties that return labelled tuples
(`controllerHomeButtonSystemAction` and `controllerHomeButtonInAppAction`, each
`(action:customized:)`), a `settingsUpdates` async sequence, and
`openControllerHomeButtonSettings(for:) throws`. It is macOS 27, iOS 27, and
visionOS 27, not tvOS. Calls are permitted only while a controller is
connected. An in-app action of `.defer` means the system honors the game's
request to own the Home press. The game makes that request by disabling the
Home element's system gesture. The `.disabled` cases of both action enums are
macOS only, so code that names them needs `#if os(macOS)`.

```swift
import GameController

/// Ask to own the Home/logo press, as a remote-play client might.
/// Returns whether the player's setting lets the request through,
/// or nil where the OS cannot say.
@MainActor
func requestHomeButton(_ controller: GCController) -> Bool? {
    controller.physicalInputProfile.buttons[GCInputButtonHome]?.preferredSystemGestureState = .disabled
    if #available(macOS 27, iOS 27, *) {
        let settings = GCControllerHomeButtonSettingsManager()
        guard let setting = try? settings.controllerHomeButtonInAppAction else { return nil }
        return setting.action == .defer
    }
    return nil   // 26: no settings API, and the request is only a preference
}
```

## Mac only: synthetic HID devices and racing wheels

- **Engines that read IOKit HID directly**, such as SDL-style libraries, meet
  synthetic devices from macOS 14. The system creates one synthetic HID device
  per supported controller, shaped like a wired Xbox 360 pad, beside the real
  HID device. The synthetic device is inert unless the player turns on
  "Increase controller compatibility" in a per-game customization in System
  Settings. When that setting is off, `IOHIDManagerCopyDevices` does not return
  the synthetic devices. An engine that reads both IOKit and Game Controller
  must exclude them, or a player who turned the setting on sees each pad
  twice. The only supported test is the `GCSyntheticDevice` registry
  property, `kIOHIDGCSyntheticDeviceKey`. Match it as `false` to exclude the
  synthetic devices.
- **Racing wheels are macOS 13 and later only.** The header marks them
  `API_UNAVAILABLE(ios, tvos)`. Find them with `GCRacingWheel.connectedRacingWheels`
  or the connect notifications. Call `acquireDevice()` before any input flows
  and `relinquishDevice()` when done. Read `wheelInput` with a deep
  `inputStateQueueDepth` as shown above. Mac App Store builds need the
  `com.apple.security.device.usb` entitlement.
- A sandboxed game that talks to USB or Bluetooth hardware directly, outside
  Game Controller, needs `ENABLE_RESOURCE_ACCESS_USB` or
  `ENABLE_RESOURCE_ACCESS_BLUETOOTH`. Bluetooth also needs a usage description.

```swift
import GameController
import IOKit.hid

/// HID matching that skips Game Controller's synthetic Xbox 360 devices.
func makeHIDManagerWithoutSyntheticPads() -> IOHIDManager {
    // kIOHIDManagerOptionNone is the zero value of a CF_OPTIONS type, so Swift has no name for it.
    let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(0))
    let matching: [String: Any] = [
        kIOProviderClassKey: kIOHIDDeviceKey,
        kIOHIDGCSyntheticDeviceKey: false,
    ]
    IOHIDManagerSetDeviceMatching(manager, matching as CFDictionary)
    return manager
}
```

## Where else to look

- `game-loop-and-threading.md`: the tick that calls `capture()` or drains
  `nextInputState()`, the queues and QoS behind `input.queue`, full screen, and
  cursor appearance.
- `audio-and-haptics.md`: Core Haptics patterns and engine lifecycle, and the
  platform conflicts in Apple's haptics claims.
- `game-design.md`: touch-control layout, out-of-gameplay button conventions
  (A activates, B goes back, Menu pauses, Home is reserved), and keyboard
  binding guidance.
- `apple-metal/references/command-model.md`: running a Metal 3 queue beside
  Metal 4, and events across queue kinds.
- `apple-metal/references/display-and-upscaling.md`: drawable size, and the
  Metal 4 present sequence that the touch-overlay route leaves intact.
- `apple-macos` for general AppKit responder and window behavior.
