# Live endpoint map: fluid interfaces (Phase 7)

Target (Task 1): `plugin/skills/apple-animations/references/fluid-interfaces.md`.

**No books map, and there will not be one.** The corpus is spent and holds nothing
on gesture physics; `pipeline/convert.sh` is dormant until new books arrive. This
reference is live-docs plus two non-doc sources recorded at the end of this file.

This map is a **seed list, not an exhaustive registry**, per the CONVENTIONS.md
"Distillation maps" rule: it enumerates dispatch-time starting points, distillers may
follow narrower pages under an enumerated parent when the fetch actually succeeds
(DocC JSON 200), and the reference file's own header citations — not this map — are
the citation record. Expected-but-missing pages are recorded below as `MISSING:`.

## Endpoint pattern

```
https://developer.apple.com/tutorials/data/documentation/<path>.json
```

where `<path>` mirrors the human URL path under `developer.apple.com/documentation/`.

**UIKit's deceleration pages carry a DocC disambiguation suffix.** The struct and the
property share the name `decelerationRate`, so the undisambiguated path 404s and the
`-swift.struct` / `-swift.property` forms are the real pages. Recorded below as
`MISSING:` because the obvious guess looks like a dead page.

## Probe status

30 seeds probed at spec time (2026-09-12,
`.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/probe/01-children.log` through
`06-rubberband-deceleration.log`) and **re-probed at Task 1 execution time: all 30
still 200, zero changed class.** The `--children` listings of `DragGesture.Value`,
`Spring`, `ScrollTargetBehavior`, `ScrollTargetBehaviorContext`, and `Animation` were
re-walked and diffed against the probe logs: **no child present at probe time is
absent now.** Evidence:
`.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/task-1-reprobe.log`.

## Seeds: what the gesture hands you

- `https://developer.apple.com/documentation/swiftui/draggesture/value` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/DragGesture/Value.json` (index, children enumerated)
- `https://developer.apple.com/documentation/swiftui/draggesture/value/velocity` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/DragGesture/Value/velocity.json`
- `https://developer.apple.com/documentation/swiftui/draggesture/value/predictedendtranslation` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/DragGesture/Value/predictedEndTranslation.json`
- `https://developer.apple.com/documentation/swiftui/draggesture/value/predictedendlocation` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/DragGesture/Value/predictedEndLocation.json`
- `https://developer.apple.com/documentation/swiftui/gesturestate` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/GestureState.json`
- `https://developer.apple.com/documentation/swiftui/buttonstyleconfiguration/ispressed` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/ButtonStyleConfiguration/isPressed.json`
- `https://developer.apple.com/documentation/swiftui/view/sensoryfeedback(_:trigger:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/View/sensoryFeedback(_:trigger:).json`

## Seeds: springs that receive the handoff

- `https://developer.apple.com/documentation/swiftui/spring` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring.json` (index, children enumerated)
- `https://developer.apple.com/documentation/swiftui/spring/init(duration:bounce:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/init(duration:bounce:).json`
- `https://developer.apple.com/documentation/swiftui/spring/init(mass:stiffness:damping:allowoverdamping:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/init(mass:stiffness:damping:allowOverDamping:).json`
- `https://developer.apple.com/documentation/swiftui/spring/init(response:dampingratio:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/init(response:dampingRatio:).json`
- `https://developer.apple.com/documentation/swiftui/spring/init(settlingduration:dampingratio:epsilon:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/init(settlingDuration:dampingRatio:epsilon:).json`
- `https://developer.apple.com/documentation/swiftui/spring/update(value:velocity:target:deltatime:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/update(value:velocity:target:deltaTime:).json`
- `https://developer.apple.com/documentation/swiftui/spring/value(target:initialvelocity:time:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/value(target:initialVelocity:time:).json`
- `https://developer.apple.com/documentation/swiftui/spring/velocity(target:initialvelocity:time:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/velocity(target:initialVelocity:time:).json`
- `https://developer.apple.com/documentation/swiftui/spring/force(target:position:velocity:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/force(target:position:velocity:).json`
- `https://developer.apple.com/documentation/swiftui/spring/force(fromvalue:tovalue:position:velocity:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/force(fromValue:toValue:position:velocity:).json`
- `https://developer.apple.com/documentation/swiftui/spring/settlingduration(target:initialvelocity:epsilon:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/settlingDuration(target:initialVelocity:epsilon:).json`
- `https://developer.apple.com/documentation/swiftui/spring/settlingduration(fromvalue:tovalue:initialvelocity:epsilon:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Spring/settlingDuration(fromValue:toValue:initialVelocity:epsilon:).json`
- `https://developer.apple.com/documentation/swiftui/animation/spring(response:dampingfraction:blendduration:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Animation/spring(response:dampingFraction:blendDuration:).json`
- `https://developer.apple.com/documentation/swiftui/animation/interactivespring(response:dampingfraction:blendduration:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Animation/interactiveSpring(response:dampingFraction:blendDuration:).json`
- `https://developer.apple.com/documentation/swiftui/animation/interpolatingspring(_:initialvelocity:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/Animation/interpolatingSpring(_:initialVelocity:).json`

## Seeds: scroll targets and boundaries

- `https://developer.apple.com/documentation/swiftui/scrolltargetbehavior` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/ScrollTargetBehavior.json`
- `https://developer.apple.com/documentation/swiftui/scrolltargetbehaviorcontext` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/ScrollTargetBehaviorContext.json` (index, children enumerated — `velocity` is the one place SwiftUI hands over release velocity for a scroll view)
- `https://developer.apple.com/documentation/swiftui/scrollbouncebehavior` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/ScrollBounceBehavior.json`
- `https://developer.apple.com/documentation/swiftui/view/scrollbouncebehavior(_:axes:)` → `https://developer.apple.com/tutorials/data/documentation/SwiftUI/View/scrollBounceBehavior(_:axes:).json`

## Seeds: UIKit deceleration constants (in scope only as constants)

- `https://developer.apple.com/documentation/uikit/uiscrollview/decelerationrate-swift.struct` → `https://developer.apple.com/tutorials/data/documentation/UIKit/UIScrollView/DecelerationRate-swift.struct.json`
- `https://developer.apple.com/documentation/uikit/uiscrollview/decelerationrate-swift.struct/normal` → `https://developer.apple.com/tutorials/data/documentation/UIKit/UIScrollView/DecelerationRate-swift.struct/normal.json`
- `https://developer.apple.com/documentation/uikit/uiscrollview/decelerationrate-swift.struct/fast` → `https://developer.apple.com/tutorials/data/documentation/UIKit/UIScrollView/DecelerationRate-swift.struct/fast.json`
- `https://developer.apple.com/documentation/uikit/uiscrollview/decelerationrate-swift.property` → `https://developer.apple.com/tutorials/data/documentation/UIKit/UIScrollView/decelerationRate-swift.property.json`

**All four pages are value-free.** `normal` and `fast` carry an abstract and nothing
else — Apple's current documentation does not publish the numbers. Re-confirmed at
Task 1 execution time; see `task-1-reprobe.log`. This is why the reference records a
measurement rather than a citation.

## MISSING

```
MISSING: UIKit/UIScrollView/DecelerationRate          -> 404 (use -swift.struct)
MISSING: UIKit/UIScrollView/DecelerationRate/normal   -> 404 (use -swift.struct/normal)
```

Both 404 at probe time and still 404 at Task 1 execution time. Nothing else on the
seed list changed class.

## NON-DOC SOURCE

Finding 1 has no doc page behind it. The projection constant is not documented
anywhere on developer.apple.com; it is legible only in the shipped interface, which
carries inlinable property bodies:

```
/Applications/Xcode-beta.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS27.0.sdk/System/Library/Frameworks/SwiftUI.framework/Modules/SwiftUI.swiftmodule/arm64e-apple-ios.swiftinterface
```

Read `DragGesture.Value.velocity` there for the body that yields the 0.25 s figure.
The same file is the negative evidence for Finding 3: `rubber`, `resistance`, and
`overscroll` each return zero hits, so there is no public rubber-banding API to find.

Second non-doc source: the deceleration rates themselves
(`normal` = 0.998, `fast` = 0.99), measured at runtime on an iOS 27.0 simulator.
The measurement itself is
`.superpowers/sdd/2026-09-12-phase7-fluid-interfaces/probe/07-deceleration-measured.log`
— compiled for the simulator, booted, read at runtime, simulator shut down.
Measuring beat citing because the doc pages above publish no values.

The reference file cites this interface in its short form, `iPhoneOS27.0.sdk
SwiftUI.swiftinterface`, not the absolute path above: `plugin/` ships to users, and
an `/Applications/Xcode-beta.app/...` path is beta-specific and machine-specific.
The absolute path belongs here, in dev-time tooling.

## OUT OF SCOPE (Phase 7)

```
OUT OF SCOPE (Phase 7): UIKit/UIScrollView beyond the deceleration constants
OUT OF SCOPE (Phase 7): Metal and graphics-pipeline smoothness
```

`UIScrollView` itself, its delegate protocol, and its content-inset and paging
behavior are UIKit maintenance material; CONVENTIONS.md admits legacy material only
under a `## Maintaining older code:` heading, and nothing here needs one. The
deceleration constants are in scope solely as the input to the projection formula.

Frame-level smoothness is a technique row in the spec's table with no API behind it.
Its measurement side already belongs to `apple-performance`
(`references/responsiveness-hangs-and-hitches.md`); the Metal and graphics-pipeline
route to a steady frame rate is a different subject from gesture motion and is not
opened here.

## Cross-map note

API mechanics for `Animation`, `Spring`, and `Transaction` are already seeded by
`pipeline/maps/apple-animations-live.md` and distilled into
`animation-fundamentals.md`. This map seeds only what that file does not cover: what
a gesture hands you, what SwiftUI projects from it, and where the handoff into a
spring goes wrong. Motion taste stays in
`plugin/skills/apple-design/references/animation-taste.md`.
