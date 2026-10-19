> verified: 2026-10 against https://developer.apple.com/documentation/appkit/nsview/displaylink(target:selector:).md, https://developer.apple.com/documentation/appkit/nswindow/displaylink(target:selector:).md, https://developer.apple.com/documentation/appkit/nsscreen/displaylink(target:selector:).md, https://developer.apple.com/documentation/quartzcore/cadisplaylink.md, https://developer.apple.com/documentation/quartzcore/cadisplaylink/init(target:selector:).md, https://developer.apple.com/documentation/quartzcore/cadisplaylink/add(to:formode:).md, https://developer.apple.com/documentation/quartzcore/cadisplaylink/targettimestamp.md, https://developer.apple.com/documentation/quartzcore/cadisplaylink/timestamp.md, https://developer.apple.com/documentation/quartzcore/cadisplaylink/duration.md, https://developer.apple.com/documentation/quartzcore/cadisplaylink/preferredframeraterange.md, https://developer.apple.com/documentation/quartzcore/cacurrentmediatime().md, https://developer.apple.com/documentation/quartzcore/cametaldisplaylink.md, https://developer.apple.com/documentation/quartzcore/cametaldisplaylink/update/targettimestamp.md, https://developer.apple.com/documentation/quartzcore/cametaldisplaylink/update/targetpresentationtimestamp.md, https://developer.apple.com/documentation/quartzcore/optimizing-iphone-and-ipad-apps-to-support-promotion-displays.md, https://developer.apple.com/documentation/foundation/runloop/mode/common.md, https://developer.apple.com/documentation/foundation/runloop/mode/eventtracking.md, https://developer.apple.com/documentation/metal/creating-a-custom-metal-view.md, https://developer.apple.com/documentation/metal/managing-your-game-window-for-metal-in-macos.md, https://developer.apple.com/documentation/metal/managing-your-metal-app-window-in-ipados.md, https://developer.apple.com/documentation/metal/improving-your-games-graphics-performance-and-settings.md, https://developer.apple.com/documentation/metal/preparing-your-metal-app-to-run-in-the-background.md, https://developer.apple.com/documentation/metal/mtlcommandbuffer/addcompletedhandler(_:).md, https://developer.apple.com/documentation/metal/nsprocessperformanceprofile.md, https://developer.apple.com/documentation/accelerate/rotating-a-cube-by-transforming-its-vertices.md, https://developer.apple.com/documentation/appkit/nsview/makebackinglayer().md, https://developer.apple.com/documentation/uikit/uiview/layerclass.md, https://developer.apple.com/documentation/appkit/nswindow/togglefullscreen(_:).md, https://developer.apple.com/documentation/appkit/nswindowdelegate/windowdidresize(_:).md, https://developer.apple.com/documentation/appkit/nswindowdelegate/window(_:willusefullscreenpresentationoptions:).md, https://developer.apple.com/documentation/appkit/nsapplication/presentationoptions-swift.struct.md, https://developer.apple.com/documentation/appkit/nsapplication/presentationoptions-swift.struct/hidedock.md, https://developer.apple.com/documentation/appkit/nscursor.md, https://developer.apple.com/documentation/appkit/nscursor/hide().md, https://developer.apple.com/documentation/appkit/nscursor/unhide().md, https://developer.apple.com/documentation/appkit/nscursor/sethiddenuntilmousemoves(_:).md, https://developer.apple.com/documentation/coregraphics/cgassociatemouseandmousecursorposition(_:).md, https://developer.apple.com/documentation/uikit/uiviewcontroller/preferredscreenedgesdeferringsystemgestures.md, https://developer.apple.com/documentation/uikit/uiwindowscene/geometry/isinteractivelyresizing.md, https://developer.apple.com/documentation/uikit/uiwindowscenedelegate/windowscene(_:didupdateeffectivegeometry:).md, https://developer.apple.com/documentation/foundation/thread/qualityofservice.md, https://developer.apple.com/documentation/foundation/processinfo/activeprocessorcount.md, https://developer.apple.com/documentation/foundation/processinfo/thermalstate-swift.property.md, https://developer.apple.com/documentation/foundation/processinfo/thermalstate-swift.enum.md, https://developer.apple.com/documentation/foundation/processinfo/thermalstatedidchangenotification.md, https://developer.apple.com/documentation/foundation/processinfo/islowpowermodeenabled.md, https://developer.apple.com/documentation/foundation/nsnotification/name-swift.struct/nsprocessinfopowerstatedidchange.md, https://developer.apple.com/documentation/bundleresources/information-property-list/lssupportsgamemode.md, https://developer.apple.com/documentation/bundleresources/information-property-list/gcsupportsgamemode.md, https://developer.apple.com/documentation/bundleresources/information-property-list/lsapplicationcategorytype.md, https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.sustained-execution.md, https://developer.apple.com/documentation/dispatch/dispatch-semaphore.md, https://developer.apple.com/documentation/dispatch/dispatch-queue.md, https://developer.apple.com/documentation/dispatch/workloop.md, https://developer.apple.com/documentation/dispatch/dispatchqueue/concurrentperform(iterations:execute:).md, https://developer.apple.com/documentation/os/workgroups.md, https://developer.apple.com/documentation/os/os_workgroup_parallel_create.md, https://developer.apple.com/documentation/os/os_workgroup_join.md, https://developer.apple.com/documentation/os/os_workgroup_max_parallel_threads.md, https://developer.apple.com/documentation/audiotoolbox/understanding-audio-workgroups.md, https://developer.apple.com/documentation/apple-silicon/tuning-your-code-s-performance-for-apple-silicon.md, https://developer.apple.com/documentation/apple-silicon/addressing-architectural-differences-in-your-macos-code.md, https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-metal-app.md, https://developer.apple.com/documentation/xcode/diagnosing-performance-issues-early.md, https://developer.apple.com/documentation/xcode/improving-app-responsiveness.md, https://developer.apple.com/documentation/xcode/understanding-hangs-in-your-app.md, https://developer.apple.com/documentation/xcode/addressing-watchdog-terminations.md, https://developer.apple.com/documentation/xcode/testing-a-release-build.md, https://developer.apple.com/documentation/xcode/build-settings-reference.md, https://developer.apple.com/documentation/xcode/monitoring-your-metal-apps-graphics-performance.md, https://developer.apple.com/design/human-interface-guidelines/going-full-screen.md
> typecheck: macos 26.0, ios 26.0

# Game Loop and Threading: Hosting, Frame Pacing, Threads, and System State

Contents:
- Choosing the loop driver
- Hosting the Metal view
- The frame: where the simulation step sits
- Clocks and time units
- Threads and QoS
- Dispatch in an engine
- os_workgroup: what a game can create
- Thermal state, Low Power Mode, and sustained performance
- Game Mode on macOS
- Full screen, the Dock, and the cursor
- Pausing, backgrounding, and launch
- Classic pitfalls
- Where else to look

Scope: *what drives the frame, on which thread, at which priority, and how the
game reacts to the system around it*. The GPU half of the frame (queue,
allocators, argument tables, the frames-in-flight wait, commit) is
`apple-metal/references/command-model.md` `## Frame structure`. Drawables,
present, and the `CAMetalDisplayLink` delegate and render-thread mechanics are
`apple-metal/references/display-and-upscaling.md`. This file decides which
driver to use and where the simulation sits around that code; it does not
repeat it. Controller and mouse input are `input.md`; audio threads are
`audio-and-haptics.md`; HIG rules for full screen are `game-design.md`.

## Choosing the loop driver

| Driver | Who calls you, and where | Timing you get | Use it for |
|---|---|---|---|
| `MTKView` + delegate | MetalKit's timer, on the main actor | none beyond "draw now" | tools, editors, a first prototype |
| `CADisplayLink`: on Mac from `NSView`/`NSWindow`/`NSScreen.displayLink(target:selector:)`, on iPhone and iPad from `init(target:selector:)` | a target-selector call on the run loop you add it to | `timestamp`, `targetTimestamp`, `duration` | a tick with no drawable: a sim clock, a non-Metal view, a main-thread game that accepts the cost |
| `CAMetalDisplayLink` on your `CAMetalLayer` | a delegate call on the run loop you add it to, so a render thread | `targetTimestamp`, `targetPresentationTimestamp`, and the drawable | shipping games |

Ship on `CAMetalDisplayLink` (macOS 14, iOS 17) on a dedicated render thread.
It hands you the drawable together with the deadline, and it runs off the main
thread, so frame work does not compete with event delivery. Its setup,
`preferredFrameLatency`, the weak delegate, and the present rules are in
`apple-metal/references/display-and-upscaling.md`. Everything below about
frame-rate ranges applies to both display link types.

The facts that decide it:

- **`CVDisplayLink` is deprecated.** The SDK wraps all of `CVDisplayLink.h` in
  `API_DEPRECATED_BEGIN(..., macos(10.4, 15.0))`, with a message naming the
  three AppKit `displayLink(target:selector:)` methods.
  Apple's custom-view sample and its Accelerate cube sample still build on it,
  and the custom-view sample says `CADisplayLink` is unavailable on macOS. That
  was true before macOS 14 and is stale now. Do not copy either sample's loop:
  the cube sample also advances a fixed `0.02` per tick, so its speed doubles on
  a 120 Hz panel.
- **On the Mac you cannot construct a `CADisplayLink`.** `CADisplayLink.h` marks
  `displayLinkWithTarget:selector:` `API_UNAVAILABLE(macos)`. Get one from
  `NSView`, `NSWindow`, or `NSScreen` (all macOS 14). A view's or window's link
  follows it to whatever display it is on. A screen's link does not, so prefer
  the view's.
- **A hidden view stops the clock.** The `NSView` link does not fire while the
  view is hidden or on no display, and the window's link while the window is
  on no display. If the sim runs from that callback, the sim stops too, which
  is usually what you want; reset the step clock on the next callback.
- **The link retains its target, and the run loop retains the link.** A view
  that holds its own link is a retain cycle until `invalidate()`. Invalidate it
  when the view leaves its window.
- **Add the link in every mode it must fire in.** A link fires only while its
  run loop runs a mode you added it for. On the Mac the run loop switches to
  `.eventTracking` for modal mouse-drag loops, so add a main-thread link for
  both `.default` and `.eventTracking`, or a drag can stall the game. Whether a
  window's live resize is such a loop is not runtime-checked (GUI). The iOS
  snippet uses `.common`, the pseudo-mode for the run loop's common set.
- **You request a range; the system picks the rate.** Set
  `preferredFrameRateRange`. The system rounds to a factor of the display's
  maximum rate, and lowers the available rates for Low Power Mode, critical
  thermal state, and accessibility settings. The default is the display's
  maximum. A steady lower rate looks smoother than a higher one that misses.
- **iPhone needs an Info.plist key above 60 Hz.** Without
  `CADisableMinimumFrameDurationOnPhone` = `true`, Core Animation never grants a
  `CADisplayLink` more than 60 Hz on a ProMotion iPhone. iPad Pro needs no key.
  Xcode has no `INFOPLIST_KEY_` setting for it, so it goes in a hand-written
  Info.plist, which the build merges with generated keys.
- **iOS gives games priority at 30 and 60 Hz.** From iOS 15, a range that uses
  one or both values, such as `CAFrameRateRange(minimum: 30, maximum: 60,
  preferred: 60)`, gets special scheduling priority. Apple's table puts
  first-person full-motion games at 80–120 Hz preferred 120, used sparingly for
  power.
- **No timers.** The ProMotion article rules out timers and anything else that
  does not align with Core Animation's refresh cycle; a dispatch timer source is
  not a frame clock either. Use as few display links as possible, ideally one.
- **Do not spin your own loop on the main thread.** The main dispatch queue, the
  main `OperationQueue`, and the main actor are all clients of the main run
  loop, so one long item blocks the others and input delivery, and the system
  measures hangs on that run loop. (Inference from the hangs article: a `while`
  loop there reads as one continuous hang.) Let the run loop sleep between
  callbacks.

```swift
#if os(macOS)
import AppKit
import QuartzCore

/// A view backed by a CAMetalLayer, with a CADisplayLink that follows the view
/// across displays. A CAMetalDisplayLink renderer uses the same view and layer
/// but drives its own render thread instead of `onTick`.
final class GameView: NSView {
    var onTick: ((CADisplayLink) -> Void)?
    private var link: CADisplayLink?

    var metalLayer: CAMetalLayer { layer as! CAMetalLayer }

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        wantsLayer = true                       // makeBackingLayer() supplies the layer
    }

    required init?(coder: NSCoder) { fatalError("not used") }

    override func makeBackingLayer() -> CALayer {
        let layer = CAMetalLayer()
        layer.isOpaque = true                   // opaque is required for direct-to-display
        return layer
    }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        link?.invalidate()                      // the link retains self: break the cycle
        link = nil
        guard window != nil else { return }
        let link = displayLink(target: self, selector: #selector(step(_:)))
        link.preferredFrameRateRange = CAFrameRateRange(minimum: 60, maximum: 120, preferred: 120)
        link.add(to: .main, forMode: .default)
        link.add(to: .main, forMode: .eventTracking)   // keep ticking in mouse-drag loops
        self.link = link
    }

    @objc private func step(_ link: CADisplayLink) {
        onTick?(link)
    }
}
#endif
```

## Hosting the Metal view

### AppKit, the Mac default

The window recipe from Apple's macOS game-window article, with what each step
buys:

- **Window.** Titled, closable, miniaturizable, resizable; a `minSize` such as
  640×360; `isReleasedWhenClosed = false` if you keep a reference. Resizable
  does not oblige you to resize every render target.
- **Layer.** An opaque `CAMetalLayer` with RGB content, full screen, on Apple
  silicon is the condition for direct-to-display, where the display hardware
  scales the drawable at almost no cost. The drawable need not match the panel.
  Verify it in the Metal HUD (`apple-metal/references/display-and-upscaling.md`).
- **Resize.** `windowDidResize(_:)` fires on every resize, including the one
  `toggleFullScreen(_:)` causes. Set `drawableSize` there (snippet in "Full
  screen, the Dock, and the cursor").
- **Keys.** The article adds an empty `keyDown(with:)` override to the
  `NSWindow` subclass, so AppKit does not consume key events that Game
  Controller should receive. Details in `input.md`.
- **OpenGL hosting is deprecated.** `NSOpenGLView`, `NSOpenGLContext`,
  `NSOpenGLLayer`, and `NSOpenGLPixelFormat` sit in AppKit's deprecated
  symbols, along with `NSDisableScreenUpdates()`. A port replaces them with a
  `CAMetalLayer`-backed view, not a shim.
- **AppKit chrome around the game view** (settings panes, overlays) can follow
  an `@Observable` model through AppKit observation tracking; on macOS 15 it
  needs the `NSObservationTrackingEnabled` Info.plist key. Keep per-frame sim
  state out of such a model, or every tick re-runs layout.

### UIKit, on iPhone and iPad

```swift
import UIKit
import QuartzCore

final class GameView: UIView {
    var onTick: ((CADisplayLink) -> Void)?
    private var link: CADisplayLink?

    override class var layerClass: AnyClass { CAMetalLayer.self }
    var metalLayer: CAMetalLayer { layer as! CAMetalLayer }

    override func didMoveToWindow() {
        super.didMoveToWindow()
        link?.invalidate()
        link = nil
        guard window != nil else { return }
        let link = CADisplayLink(target: self, selector: #selector(step(_:)))
        // 30 and 60 Hz get game scheduling priority on iOS 15 and later.
        link.preferredFrameRateRange = CAFrameRateRange(minimum: 30, maximum: 60, preferred: 60)
        link.add(to: .main, forMode: .common)
        self.link = link
    }

    @objc private func step(_ link: CADisplayLink) {
        onTick?(link)
    }
}
```

What the iPhone and iPad host needs, iPadOS 26 changes first:

- **You cannot opt out of resizing.** `UIRequiresFullScreen` is deprecated, and
  with multitasking on, people can always resize the scene. Plan for any aspect
  ratio: letterbox with an opaque black layer, `contentsGravity =
  .resizeAspect`, and a black launch screen.
- **The scene life cycle is becoming mandatory.** Apps without it log a warning
  on iOS 26 and iPadOS 26. The next major release requires it when you build
  with the latest SDK. A game typically declares
  `UIApplicationSupportsMultipleScenes` = `false`.
- **Doc error.** The iPad window article's scene-manifest example uses a key
  named `MyCustomSceneDelegateClass`. The real key is `UISceneDelegateClassName`.
- **Do not resize mid-drag.** While `effectiveGeometry.isInteractivelyResizing`
  (iOS 26) is true, keep rendering at the old target size and do not poll the
  window size. Apply the new size when the drag ends, in
  `windowScene(_:didUpdateEffectiveGeometry:)` or
  `mtkView(_:drawableSizeWillChange:)`. The same callback fires on every move to
  another screen.
- **Pixels are points times the layer's `contentsScale`.** The iPad article reads
  the display scale from the trait collection in `viewIsAppearing(_:)`.
- **HUD and touch controls go inside the safe area.** Render edge to edge, but
  lay out controls with `safeAreaLayoutGuide` or `safeAreaInsets`, read once the
  view is in a window. A container that overlays its own controls shrinks the
  child's safe area with `additionalSafeAreaInsets`.

```swift
import UIKit

final class GameSceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?
    var applyDrawableSize: ((CGSize) -> Void)?

    func windowScene(_ windowScene: UIWindowScene,
                     didUpdateEffectiveGeometry previousEffectiveGeometry: UIWindowScene.Geometry) {
        let geometry = windowScene.effectiveGeometry
        guard !geometry.isInteractivelyResizing else { return }   // keep the old size mid-drag
        let points = geometry.coordinateSpace.bounds.size
        let scale = windowScene.traitCollection.displayScale
        applyDrawableSize?(CGSize(width: points.width * scale, height: points.height * scale))
    }
}
```

### SwiftUI, on both

SwiftUI hosts the same view through a representable. One multiplatform target
can share the `App`; use separate targets when the Mac shell is AppKit and the
iOS shell is UIKit. Keep the frame loop out of SwiftUI state: `update...View`
should do nothing per frame. On iPad and Mac, `.frame(minWidth:minHeight:)` with
`.windowResizability(.contentMinSize)` sets the minimum window size.

```swift
import SwiftUI
import QuartzCore

#if os(macOS)
struct GameSurface: NSViewRepresentable {
    let onTick: (CADisplayLink) -> Void

    func makeNSView(context: Context) -> GameView {
        let view = GameView(frame: .zero)
        view.onTick = onTick
        return view
    }

    func updateNSView(_ nsView: GameView, context: Context) {}   // no per-frame state here
}
#elseif os(iOS)
struct GameSurface: UIViewRepresentable {
    let onTick: (CADisplayLink) -> Void

    func makeUIView(context: Context) -> GameView {
        let view = GameView(frame: .zero)
        view.onTick = onTick
        return view
    }

    func updateUIView(_ uiView: GameView, context: Context) {}
}
#endif
```

## The frame: where the simulation step sits

Run the simulation in fixed steps and render at whatever rate the display
grants. Each display-link callback converts elapsed time into whole sim steps
and renders the state between the last two steps.

Which timestamp to feed it:

- **`CADisplayLink`: `targetTimestamp`.** The ProMotion article says to drive
  animation and physics from it. `timestamp` is the start of the current
  interval and can be well before your callback runs. The working budget is
  `targetTimestamp - CACurrentMediaTime()`.
- **`CAMetalDisplayLink`: `targetPresentationTimestamp`** for animation deltas,
  as its page advises. Its `targetTimestamp` is the deadline for `present()`,
  not a display time (`apple-metal/references/display-and-upscaling.md`).
- **A late callback costs the next one.** If a `CADisplayLink` callback runs past
  `targetTimestamp`, the next interval gets no callback. The accumulator absorbs
  the gap as two intervals; cap the steps per frame so a long stall slows the
  game instead of freezing it in catch-up.
- **Variable refresh.** ProMotion iPhones run 10–120 Hz and iPad Pro 24–120 Hz,
  and the system changes the rate on its own. Never derive the step from the
  nominal rate.

```swift
import QuartzCore

/// Turns display-link times into whole fixed simulation steps plus an
/// interpolation factor for rendering between the last two steps.
struct FixedStepClock {
    let step: CFTimeInterval            // seconds per simulation step, e.g. 1.0 / 120.0
    let maxStepsPerFrame: Int           // spiral-of-death guard
    private(set) var accumulator: CFTimeInterval = 0
    private var lastTime: CFTimeInterval?

    init(step: CFTimeInterval, maxStepsPerFrame: Int = 8) {
        self.step = step
        self.maxStepsPerFrame = maxStepsPerFrame
    }

    /// `time` is when the frame being built will show: `targetTimestamp` from a
    /// CADisplayLink, or `targetPresentationTimestamp` from a CAMetalDisplayLink.
    mutating func advance(to time: CFTimeInterval) -> (steps: Int, alpha: Double) {
        defer { lastTime = time }
        guard let last = lastTime else { return (0, 0) }
        accumulator += max(0, time - last)          // a skipped callback arrives as a bigger gap
        let steps = min(Int(accumulator / step), maxStepsPerFrame)
        accumulator -= Double(steps) * step
        if steps == maxStepsPerFrame, accumulator >= step {
            accumulator = 0                         // drop the backlog: slow down, don't freeze
        }
        return (steps, accumulator / step)
    }

    /// Call after a pause, a hidden view, or a return from the background.
    mutating func reset() {
        lastTime = nil
        accumulator = 0
    }
}
```

The order inside one callback, and how it meets the GPU frame in
`apple-metal/references/command-model.md`:

1. **Input.** Drain controller input queues into the sim. For a fixed step,
   drain per step, not per frame (`input.md`: `inputStateQueueDepth`,
   `nextInputState()`).
2. **Simulation steps**, zero or more, at the fixed `dt`. Fan heavy per-step work
   out to workers (see "Threads and QoS").
3. **Audio state.** A PHASE engine in manual update mode is updated here, after
   sources and the listener move, so sound matches the frame
   (`audio-and-haptics.md`).
4. **Render snapshot.** Interpolate between the last two sim states by `alpha`
   into a plain value: matrices, instance data, camera. The GPU side reads only
   this snapshot, never live sim state.
5. **GPU frame.** Hand the snapshot to `FrameLoop.encodeFrame(...)` and its
   submit, or to the `CAMetalDisplayLink` delegate's encode. The
   frames-in-flight wait (step 1 of `## Frame structure`) happens inside, *after*
   the simulation, so the CPU simulates while the GPU still draws earlier
   frames. Snapshot data is written into the frame's slot only after that wait
   (step 3 there).

```swift
import QuartzCore

/// What the GPU half reads: a value, built once per frame.
struct RenderSnapshot {
    var alpha: Float
    // interpolated transforms, instance data, camera...
}

protocol GameSimulation {
    mutating func step(dt: Double)              // drains its own input queues per step
    func snapshot(alpha: Double) -> RenderSnapshot
}

/// The GPU half: the FrameLoop encode and submit in
/// apple-metal/references/command-model.md, or the CAMetalDisplayLink delegate
/// in apple-metal/references/display-and-upscaling.md. It owns the
/// frames-in-flight wait.
protocol FrameSubmitter: AnyObject {
    func submit(_ snapshot: RenderSnapshot) throws
}

final class GameLoop<Simulation: GameSimulation> {
    private(set) var simulation: Simulation
    private var clock: FixedStepClock
    private let gpu: any FrameSubmitter

    init(simulation: Simulation, step: CFTimeInterval, gpu: any FrameSubmitter) {
        self.simulation = simulation
        self.clock = FixedStepClock(step: step)
        self.gpu = gpu
    }

    /// Call once per display-link callback with the frame's display time.
    func frame(showingAt time: CFTimeInterval) throws {
        let (steps, alpha) = clock.advance(to: time)
        for _ in 0..<steps {
            simulation.step(dt: clock.step)
        }
        try gpu.submit(simulation.snapshot(alpha: alpha))
    }

    func resume() { clock.reset() }
}
```

Two rate rules from the ProMotion article:

- **Do not scale render quality from the refresh rate inside the callback.** That
  can oscillate with GPU throttling. Keep separate, fixed settings per target
  rate and switch between them deliberately.
- **Test rate changes.** Setting `minimum`, `maximum`, and `preferred` to the same
  value forces a rate on the next callback. Test sudden and gradual changes, and
  thermal throttling, on a device.

Determinism, if you need lockstep or replay:

- simd has default, `precise`, and `fast` spellings. The default resolves to
  precise unless the target builds with `-ffast-math`, which silently switches
  every default call to the fast form. Call `simd_precise_*` in sim code, or
  keep `-ffast-math` off sim targets.
- Accelerate's sparse solvers are multithreaded by default and sum in a varying
  order. Set `VECLIB_MAXIMUM_THREADS=1` for bit-identical results.
- C and C++ float-to-int casts of out-of-range values differ between arm64,
  which saturates, and x86_64. Mixed-architecture peers can diverge. Swift
  defines one behavior. Catch it with UBSan's `float-cast-overflow`.

## Clocks and time units

- **Work in display-link seconds.** `CACurrentMediaTime()` is
  `mach_absolute_time()` converted to seconds, and the ProMotion article
  computes the frame budget as `targetTimestamp - CACurrentMediaTime()`, so the
  two share a clock. Do frame and sim arithmetic in those seconds.
- **`mach_absolute_time()` ticks are not nanoseconds.** Apple's Apple-silicon
  porting guide says to always scale them by `mach_timebase_info`, and that the
  value differs between native and Rosetta-translated processes. On this M4 Pro
  (macOS 27.0.1) the ratio is `numer = 125, denom = 3` natively: one tick is
  41.67 ns, so a tick count read as nanoseconds runs 41.7 times slow. Under
  Rosetta the same program reads `1/1`, so code that treats ticks as
  nanoseconds looks right when translated and breaks when built native.
  (Runtime-checked: `runs.txt` §1.)
- **`clock_gettime_nsec_np(CLOCK_UPTIME_RAW)`** returns nanoseconds without the
  conversion. It agreed with scaled ticks to within 41 ns over 100 ms.

```swift
import Darwin

/// Nanoseconds from mach ticks, without overflowing on long uptimes.
struct HostClock {
    private let numer: UInt64
    private let denom: UInt64

    init() {
        var info = mach_timebase_info_data_t()
        _ = mach_timebase_info(&info)
        numer = UInt64(info.numer)
        denom = UInt64(info.denom)
    }

    func nanoseconds(fromTicks ticks: UInt64) -> UInt64 {
        (ticks / denom) * numer + (ticks % denom) * numer / denom
    }

    static func nowNanoseconds() -> UInt64 {
        clock_gettime_nsec_np(CLOCK_UPTIME_RAW)
    }
}
```

## Threads and QoS

A layout that works on Mac, iPhone, and iPad:

| Thread | Runs | QoS |
|---|---|---|
| Main | AppKit or UIKit events, windows, menus, input callbacks | userInteractive (the system's) |
| Render | the `CAMetalDisplayLink` run loop: sim steps, snapshot, encode, submit | userInteractive, set by you |
| Workers | per-step and per-frame jobs: culling, animation, particles | inherit from the submitter |
| Loading and streaming | asset reads, decompression | userInitiated while a level waits, utility otherwise |
| Saves, cache warming | anything deferrable | utility or background |

The rules behind it:

- **A new `Thread` does not inherit the main thread's QoS.** On this machine a
  `Thread` started with no QoS ran at `default`. One with `qualityOfService =
  .userInteractive` set before `start()` ran at userInteractive.
  `apple-metal/references/display-and-upscaling.md`'s `RenderLoopThread` sets
  it in its initializer. Set it on every render thread you create.
  (Runtime-checked: `runs.txt` §4.)
- **QoS steers core choice.** On Apple silicon a task's QoS influences where
  the system runs it; background work is more likely to land on efficiency
  cores. Work with no QoS hurts both responsiveness and efficiency.
- **Two Apple pages disagree on raising a render thread.** The Metal
  performance article recommends priority 45 via `pthread_attr_setschedparam`
  before `pthread_create`. The Apple-silicon tuning guide says to move off
  `pthread_setschedparam`, `setpriority`, and `thread_set_policy` to QoS, for
  example `pthread_set_qos_class_self_np`. They are exclusive: on this machine a
  thread made with the priority-45 recipe reports `QOS_CLASS_UNSPECIFIED`, so it
  leaves the QoS system. Default to QoS. Try priority 45 only for the one render
  thread, and only when a Game Performance trace shows it Preempted, then
  measure both. `pthread_getschedparam` reported 31 for every QoS class, so it
  cannot confirm a thread's QoS; use `qos_class_self()`. (Runtime-checked:
  `runs.txt` §3.)
- **Do not run the render loop in a Swift `Task`.** Its frames-in-flight wait,
  `MTLSharedEvent.wait(untilSignaledValue:timeoutMS:)`, is
  `NS_SWIFT_UNAVAILABLE_FROM_ASYNC`: the SDK forbids that blocking wait in async
  code. Use a `Thread` with a run loop, as above.
- **`Task { }` in a `@MainActor` context still runs on the main actor**, so heavy
  load work there only postpones the hang. Use a `nonisolated` async function or
  `Task.detached`. A detached task inherits no priority and defaults to
  `.medium`, so pass one.
- **`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`** infers `@MainActor` on every
  unannotated declaration. Mark render and sim types `nonisolated`, or they
  cannot run on the render thread.
- **Never spin.** A spinning thread holds a core. A fast consumer spinning while a
  slow producer runs on an efficiency core makes it worse. Block on
  `os_unfair_lock`, a condition variable, or a mutex, and avoid
  `pthread_yield_np`.
- **Split work dynamically.** The scheduler places threads on cores of different
  speeds, so an even static split leaves performance-core threads idle while
  efficiency-core threads finish. `concurrentPerform(iterations:execute:)`
  balances when it gets at least three iterations per core; a custom pool must
  work-steal.
- **Size pools from the per-level counts.** `hw.perflevel0.logicalcpu` is the
  performance cores and `hw.perflevel1.logicalcpu` the efficiency cores. The
  Metal games-settings article names `hw.perflevels` for the number of core
  types; that key does not exist. The SDK's `sys/sysctl.h` names
  `hw.nperflevels`. (Runtime-checked: `runs.txt` §6.)
- **Ported lock-free code.** Apple silicon is weakly ordered. Queues and flags
  that were correct by accident under x86 ordering can race. Use explicit
  atomics with stated orders, and run Thread Sanitizer. TSan runs only on macOS
  or in Simulator, never on an iOS device, so validate threading in the Mac
  build.
- **Touching a view from the render thread** is the classic engine bug. Main
  Thread Checker flags AppKit and UIKit calls made off the main thread.

```swift
import Foundation

/// Configure a render thread (such as the RenderLoopThread in
/// apple-metal/references/display-and-upscaling.md) before starting it.
func startRenderThread(_ thread: Thread) {
    thread.name = "Render"
    thread.qualityOfService = .userInteractive   // a new Thread otherwise runs at .default
    thread.start()
}

/// Logical CPUs in one performance level: 0 is performance, 1 is efficiency.
func logicalCPUs(perfLevel: Int) -> Int {
    var value: Int32 = 0
    var size = MemoryLayout<Int32>.size
    let status = sysctlbyname("hw.perflevel\(perfLevel).logicalcpu", &value, &size, nil, 0)
    return status == 0 ? Int(value) : 0
}
```

## Dispatch in an engine

- **No private concurrent queue per subsystem.** Each one costs threads. Submit
  parallel work to the global queues, and give each serial subsystem queue
  (asset load, save, decode) a global queue as its target.
- **Never block inside work on a concurrent queue.** A blocked worker makes GCD
  spawn more threads, and enough of them exhaust the thread budget.
- **A workloop for a QoS-ordered lane.** `DispatchWorkloop` runs its
  highest-QoS pending item next instead of FIFO, so input and sim work can jump
  ahead of background jobs. `dispatch_set_qos_class_floor` sets its minimum QoS.
- **Fork-join without stalling.** Use `DispatchGroup.notify`, not `wait`, on the
  main or render thread. A main-queue `sync` from the main thread deadlocks.
- **Assert ownership cheaply.** `dispatchPrecondition(condition: .onQueue(...))`
  guards "sim state is touched only on the sim queue".
  `dispatch_get_current_queue` is deprecated; do not use it for that.
- **Metal objects made in a worker loop** need an autorelease boundary: create
  the queue with the `.workItem` autorelease frequency, or wrap the work in
  `autoreleasepool`.
- **Memory pressure.** A `DISPATCH_SOURCE_TYPE_MEMORYPRESSURE` source is the hook
  a UIKit-free engine core can use to drop caches before jetsam. Drop known
  caches; do not walk the object graph.

**The frames-in-flight semaphore and priority inversion.** Apple's rule is that
`dispatch_semaphore_wait` and `dispatch_group_wait` cannot pass the waiter's
priority to the signaler, so the waiting thread's QoS must be the same as or
lower than the signaling thread's. Thread Performance Checker flags mismatches.
What that means for each Metal path:

- **Metal 4**, this skill's default, bounds frames in flight with an
  `MTLSharedEvent` wait, not a semaphore (`apple-metal/references/command-model.md`).
- **Metal 3** signals a `DispatchSemaphore` from `addCompletedHandler(_:)`. The
  handler's page and `MTLCommandBuffer.h` say only that the driver calls it after
  the GPU finishes. Neither names a thread or a QoS. On this M4 Pro, 10 of 10
  handlers ran off the main thread, on a queue labelled
  `com.Metal.CompletionQueueDispatch`, at userInteractive, even when a utility
  thread committed. A userInteractive render thread waiting on that signal
  therefore met Apple's rule here. That is observed behavior, not contract:
  keep Thread Performance Checker on in debug runs. (Runtime-checked:
  `runs.txt` §2.)

## os_workgroup: what a game can create

A workgroup tells the scheduler that threads cooperate toward a deadline. The
header settles what a game may create:

- **Only audio interval workgroups exist.** `os/workgroup_interval.h` (lines
  44–46 in the macOS 27 SDK) says the only supported interval workgroups are
  for audio, from AudioToolbox. The `os` headers declare no interval creator.
  The one public creator, `AudioWorkIntervalCreate`, is documented for audio
  real-time threads and is unavailable from Swift. **A game cannot create an
  interval workgroup for its render or sim loop.** Do not carry the audio
  pages' start-update-finish interval pattern over to game threads; the header
  rules it out.
- **What a game can do:**
  - Join its own real-time audio threads to the audio device's workgroup, or to
    an `AudioWorkIntervalCreate` interval (`audio-and-haptics.md`).
  - Create a **parallel** workgroup for a fan-out job and join each worker to
    it. Registered threads let the scheduler place work and trade power against
    throughput.
  - Bind a `DispatchWorkloop` to a workgroup, so its worker threads join while
    they run its items.
- **Never join sim or job threads to an audio workgroup.** Normal-priority
  threads cannot join one, and the audio deadline is not yours.
- **The `os` workgroup API is callable from Swift.** The `os` overlay provides
  `WorkGroupParallel(name:)`, `join()`, `leave(token:)`, and
  `maxParallelThreads` (macOS 11, iOS 14). Only the AudioToolbox interval calls
  are Swift-unavailable.
- **The creating thread is not a member.** `os_workgroup_parallel_create`
  returns a group with no threads; each thread joins itself. The symbol page
  says to call `os_workgroup_join_self`. No such function is in the SDK. The
  call is `os_workgroup_join`, `join()` in Swift.
- **`join` fails if the thread is already in a workgroup**, and a `leave` with a
  mismatched thread, group, or token aborts the process. Leave on the thread
  that joined, with its token.
- **`maxParallelThreads` is a theoretical maximum.** It ignores current load and
  your other workgroups.
- **Workloop binding.** In C, `dispatch_workloop_set_os_workgroup` requires an
  inactive workloop and terminates the process on an active one. In Swift, pass
  the group to `DispatchWorkloop(label:attributes:autoreleaseFrequency:osWorkgroup:)`.
  Workgroup policy wins over `dispatch_workloop_set_scheduler_priority`.

```swift
import os
import Dispatch

/// A parallel workgroup for the frame's job workers, and a workloop whose
/// threads join it while they run items.
func makeJobLane() -> (group: WorkGroupParallel, lane: DispatchWorkloop)? {
    guard let group = WorkGroupParallel(name: "frame-jobs") else { return nil }
    let lane = DispatchWorkloop(label: "frame-jobs", osWorkgroup: group)
    return (group, lane)
}

/// A dedicated worker thread joins on its own thread and leaves with its token.
func runAsWorkgroupMember(_ group: WorkGroupParallel, _ work: () -> Void) {
    let token = group.join()
    defer { group.leave(token: token) }
    work()
}
```

## Thermal state, Low Power Mode, and sustained performance

- **Thermal state.** `ProcessInfo.thermalState` is `.nominal`, `.fair`,
  `.serious`, or `.critical`. You must read `thermalState` before you register
  for `thermalStateDidChangeNotification`, or the notification does not arrive.
- **Low Power Mode** (`isLowPowerModeEnabled`, iOS 9, macOS 12) reduces CPU and
  GPU performance. Observe `NSProcessInfoPowerStateDidChange` and re-read the
  property. Apple's game-settings article suggests a lower resolution, a capped
  frame rate, and lighter models, textures, and shaders.
- **The display link already reacts.** Low Power Mode and critical thermal state
  lower the available frame rates. Adapt quality in steps between fixed presets
  rather than continuously.
- **Ship presets, not every knob.** Apple suggests a few always-safe sets, such
  as a battery-and-frame-rate mode and an image-quality mode on portables,
  chosen from memory size and processor class.
- **Sustained execution.** The `com.apple.developer.sustained-execution`
  entitlement (iOS 17, macOS 15) caps burst performance so the game runs at a
  sustainable level from launch, and measurements taken early stay true. Apple
  pairs it with a Games value for `LSApplicationCategoryType`.
- **Performance profiles.** `ProcessInfo.hasPerformanceProfile(_:)` with
  `.default` or `.sustained`, `isDeviceCertified(for:)` with
  `.iPhonePerformanceGaming`, and `NSProcessInfoPerformanceProfileDidChangeNotification`
  live in Metal's `MTLDeviceCertification.h` (macOS 15, iOS 18). Their pages
  carry no usage prose. On this Mac, an unentitled process reported `.default`
  but not `.sustained`, and `isDeviceCertified(for: .iPhonePerformanceGaming)`
  returned `true`, so that call does not identify an iPhone. (Runtime-checked:
  `runs.txt` §5.)
- **Test unplugged and in Low Power Mode.** Apple's release-testing page names
  both as conditions where the OS may throttle the frame rate.

```swift
import Foundation

@MainActor
final class PowerMonitor {
    // Read thermalState before observing it, or the notification never arrives.
    private(set) var thermalState = ProcessInfo.processInfo.thermalState
    private(set) var lowPowerMode = ProcessInfo.processInfo.isLowPowerModeEnabled
    var onChange: ((ProcessInfo.ThermalState, Bool) -> Void)?
    private var observers: [any NSObjectProtocol] = []

    init() {
        let center = NotificationCenter.default
        for name in [ProcessInfo.thermalStateDidChangeNotification, .NSProcessInfoPowerStateDidChange] {
            observers.append(center.addObserver(forName: name, object: nil, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated { self?.refresh() }
            })
        }
    }

    private func refresh() {
        thermalState = ProcessInfo.processInfo.thermalState
        lowPowerMode = ProcessInfo.processInfo.isLowPowerModeEnabled
        onChange?(thermalState, lowPowerMode)   // switch presets; do not tune per frame
    }
}
```

## Game Mode on macOS

Game Mode minimizes background activity while a game runs, for steadier frame
rates. The documentation for opting in has moved, and Xcode has not caught up:

- **The key is `LSSupportsGameMode`** (macOS 26, iOS 18.6). Set it to `true` to
  make Game Mode available; set `false` for a game too light to benefit. The
  page warns that without the key, Game Mode might not turn on.
- **`GCSupportsGameMode` is the old key.** Its page lists iOS 18.0–18.6 only.
- **Xcode 27.1 writes only the old key.** Its sole build setting is
  `INFOPLIST_KEY_GCSupportsGameMode`, which writes `GCSupportsGameMode`; its
  build specification has no setting for `LSSupportsGameMode`. Put the new key
  in a hand-written Info.plist.
- **Declare a games category too.** The `LSSupportsGameMode` page does not say
  how the system decides an app is a game. A Games category is documented for
  the sustained-execution entitlement, and the key is the game's App Store
  category anyway. `public.app-category.games` and its subcategories are the
  values Xcode offers.
- **Check it live.** The Metal Performance HUD shows whether Game Mode is on
  (`apple-metal/references/gpu-debugging-and-profiling.md`). Not runtime-checked
  (GUI).

```plist
<key>LSSupportsGameMode</key>
<true/>
<key>LSApplicationCategoryType</key>
<string>public.app-category.games</string>
<!-- iPhone only: unlock display-link rates above 60 Hz -->
<key>CADisableMinimumFrameDurationOnPhone</key>
<true/>
```

## Full screen, the Dock, and the cursor

Mac full screen goes through the system: `toggleFullScreen(_:)`, the green
button, the View menu item (action `toggleFullScreen:`, target `nil`), and
Control-Command-F. Do not customize what it does; the system then handles the
camera housing on notched Macs. Do not change the display mode on entry. The
design rules are in `game-design.md`.

- **Resize the drawable in `windowDidResize(_:)`.** AppKit calls it when
  `toggleFullScreen(_:)` resizes the window.
- **Hide the Dock through the full-screen presentation options.** Games are the
  HIG's stated exception to keeping the Dock reachable. Return
  `.hideDock` from `window(_:willUseFullScreenPresentationOptions:)`. The
  options have rules: `hideDock` and `autoHideDock` are mutually exclusive,
  `hideMenuBar` requires `hideDock`, and a combination that breaks a rule raises
  an invalid-argument exception. Remove `autoHideDock` before inserting
  `hideDock`.
- **iPadOS equivalent.** Return the bottom edge from
  `preferredScreenEdgesDeferringSystemGestures` (or the `UIHostingController`
  property) so one swipe does not exit, and call
  `setNeedsUpdateOfScreenEdgesDeferringSystemGestures()` when it changes. Keep
  the default unless players exit by accident.

```swift
#if os(macOS)
import AppKit
import QuartzCore

final class GameWindowDelegate: NSObject, NSWindowDelegate {
    func window(_ window: NSWindow,
                willUseFullScreenPresentationOptions proposedOptions: NSApplication.PresentationOptions)
        -> NSApplication.PresentationOptions {
        var options = proposedOptions
        options.remove(.autoHideDock)          // exclusive with hideDock: an exception otherwise
        options.insert(.hideDock)
        return options
    }

    func windowDidResize(_ notification: Notification) {
        guard let window = notification.object as? NSWindow,
              let view = window.contentView,
              let layer = view.layer as? CAMetalLayer else { return }
        layer.drawableSize = view.convertToBacking(view.bounds.size)
    }
}
#endif
```

The cursor on the Mac (Game Controller's `GCMouse`, iPad pointer lock, and
reading deltas are `input.md`):

- **`NSCursor.hide()` and `unhide()` count.** Every `hide` needs a matching
  `unhide`; two hides and one unhide leave it hidden. `hide` overrides
  `setHiddenUntilMouseMoves(_:)`, and countering that call with `unhide` is
  undefined.
- **Mouse look.** `CGAssociateMouseAndMouseCursorPosition(0)` disconnects the
  cursor from the mouse while the app is frontmost. Events then report a
  constant location and carry X and Y deltas.
- **Release on pause.** Reconnect and unhide when the game pauses, opens a menu,
  or loses focus, so the player gets the cursor back.
- **Regions.** An `NSTrackingArea` on the game view gives entered, exited, and
  cursor-update events, to show the system cursor over a HUD and hide it over
  play.

```swift
#if os(macOS)
import AppKit
import CoreGraphics

/// Mouse-look capture: hide and disconnect together, restore together.
@MainActor
final class CursorCapture {
    private(set) var isCaptured = false

    func capture() {
        guard !isCaptured else { return }       // keep hide and unhide balanced
        NSCursor.hide()
        _ = CGAssociateMouseAndMouseCursorPosition(0)
        isCaptured = true
    }

    func release() {
        guard isCaptured else { return }
        _ = CGAssociateMouseAndMouseCursorPosition(1)
        NSCursor.unhide()
        isCaptured = false
    }
}
#endif
```

## Pausing, backgrounding, and launch

- **Pause automatically when the player switches away**, and resume where they
  left off; never leave full screen on your own. Set the display link's
  `isPaused`, release the cursor, and `reset()` the step clock on resume.
- **iOS and tvOS refuse GPU work in the background.** Stop committing when the
  app deactivates; finishing the frame being encoded is fine. Apple's
  background article then calls `waitUntilScheduled()` on each queue's last
  command buffer. That is a Metal 3 call: `MTL4CommandBuffer` has none. Under
  Metal 4, stop committing and watch commit feedback for
  `MTL4CommandQueueError.Code.notPermitted` (`apple-metal/references/command-model.md`).
- **Release what you can rebuild** when backgrounded: render targets, streamed
  textures, scene caches. A small suspended footprint is less likely to be
  jetsammed.
- **Draw a first frame fast.** iOS's watchdog kills an app that has not put
  content on screen within its launch allowance, or that stops updating because
  the main thread is busy (`0x8badf00d`). Present a loading frame, then load
  levels off the main thread. The debugger disables watchdog terminations, so
  test launches from the Home Screen with the device disconnected.
- **Saving when backgrounded** goes inside
  `beginBackgroundTask(withName:expirationHandler:)` and always ends with
  `endBackgroundTask(_:)`; an unended task gets the app terminated.

## Classic pitfalls

- Copying `CVDisplayLink` code from Apple's custom-view or Accelerate cube
  samples. It is deprecated, and the cube sample's fixed per-tick increment ties
  game speed to the refresh rate.
- Calling `CADisplayLink(target:selector:)` on the Mac. It is unavailable there;
  use `NSView.displayLink(target:selector:)`.
- Never invalidating a display link. It retains its target.
- Adding a main-thread link for `.default` only, so the game freezes during a
  live resize.
- Driving the sim from `timestamp` instead of `targetTimestamp`, or from a
  nominal 60 or 120 Hz.
- An uncapped catch-up loop: one long stall becomes a spiral of sim steps.
- Treating `mach_absolute_time()` ticks as nanoseconds. On native Apple silicon
  they are 41.67 ns each.
- Shipping an iPhone game without `CADisableMinimumFrameDurationOnPhone`, so it
  never exceeds 60 Hz.
- Starting a render `Thread` without setting its QoS. It runs at `.default`.
- Mixing priority 45 with QoS, or checking QoS with `pthread_getschedparam`.
- Running the frame loop in a Swift `Task`.
- Expecting an interval workgroup for the render loop. Only audio has them.
- Joining sim or job threads to the audio device's workgroup.
- Reading `hw.perflevels`. The key is `hw.nperflevels`.
- Setting `INFOPLIST_KEY_GCSupportsGameMode` and expecting `LSSupportsGameMode`.
- Registering for `thermalStateDidChangeNotification` before reading
  `thermalState`.
- Adding `hideDock` to options that already hold `autoHideDock`.
- Unbalanced `NSCursor.hide()` calls, or a captured cursor left captured on
  pause.
- Resizing render targets during an interactive iPad resize.

## Where else to look

- `apple-metal/references/command-model.md`: the GPU frame this loop feeds,
  frames in flight, commit feedback errors.
- `apple-metal/references/display-and-upscaling.md`: `CAMetalDisplayLink` and
  the render thread, drawables, present, direct-to-display, HDR headroom.
- `apple-metal/references/gpu-debugging-and-profiling.md`: the Metal HUD (Game
  Mode, thermal state, refresh rate) and the Game Performance template.
- `input.md`: Game Controller input queues per sim step, `GCMouse`, pointer
  lock, AppKit key events.
- `audio-and-haptics.md`: audio workgroups, real-time audio threads, PHASE
  manual update.
- `game-design.md`: the HIG's full-screen and pause rules for games.
- `apple-performance`: CPU profiling, hangs, and hitches outside the game loop.
- `swift-concurrency`: actor isolation and priority inversion in general.
- `apple-macos`: general AppKit windows, menus, and restoration.
