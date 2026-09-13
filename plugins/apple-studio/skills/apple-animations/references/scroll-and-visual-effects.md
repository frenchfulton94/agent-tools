> verified: 2026-08 against https://developer.apple.com/documentation/swiftui/view/scrolltransition(_:axis:transition:).md, https://developer.apple.com/documentation/swiftui/scrolltransitionconfiguration.md, https://developer.apple.com/documentation/swiftui/view/visualeffect(_:).md, https://developer.apple.com/documentation/swiftui/view/coloreffect(_:isenabled:).md, https://developer.apple.com/documentation/swiftui/view/layereffect(_:maxsampleoffset:isenabled:).md, https://developer.apple.com/documentation/swiftui/view/distortioneffect(_:maxsampleoffset:isenabled:).md, https://developer.apple.com/documentation/swiftui/shader.md, https://developer.apple.com/documentation/swiftui/shaderlibrary.md, https://developer.apple.com/documentation/swiftui/scrolltransitionphase.md, https://developer.apple.com/documentation/swiftui/scrolltransitionconfiguration/threshold.md, https://developer.apple.com/documentation/swiftui/visualeffect.md, https://developer.apple.com/documentation/swiftui/shaderfunction.md, https://developer.apple.com/documentation/swiftui/shader/argument.md
> sources: live Apple docs (no book input; judgment layer: apple-design/animation-taste.md)

# Scroll and Visual Effects

## Scope

This file covers the Swift-side modifier surface for scroll-driven phase effects, geometry-reading visual effects, and the three shader modifiers — the parameter shapes, the wiring between Swift values and a compiled Metal function, and the decision criteria for picking among the shader modifiers. Authoring the Metal Shading Language (MSL) source itself is explicitly out of scope: every MSL function signature below is given as a name/parameter-list contract your Swift code must match, not something to learn to write here.

## Phase-Based Scroll Effects: `scrollTransition(_:axis:transition:)`

Attaches per-row/per-item motion driven purely by scroll position, without hand-rolling your own scroll-offset tracking. It applies a supplied transition, animating between phases as the content crosses into or out of the visible region of its containing scroll view (Apple docs: `View.scrollTransition(_:axis:transition:)`).

- `axis` defaults to `nil`, which uses the innermost containing scroll view's own axis (or `.vertical` if that scroll view scrolls both directions). Override it only when the axis that should drive the transition differs from the one actually scrolling — e.g. a horizontal carousel nested inside a vertical scroll view, where you want the transition to react to horizontal position even though the outer view scrolls vertically.
- `transition` closure shape: `(EmptyVisualEffect, ScrollTransitionPhase) -> some VisualEffect` — the same "proxy + driving state" pattern as `PhaseAnimator`/`KeyframeAnimator`'s content closures (see `keyframe-and-phase-animators.md`): the first argument is a stand-in for the view you chain visual-effect calls onto, the second is what tells you which effect to apply.
- The configuration governing *how* the transition interpolates (see `ScrollTransitionConfiguration` below) applies symmetrically — the same timing/threshold rules govern a view entering and leaving the visible region, not two independently-tunable directions.

### `ScrollTransitionPhase`: three discrete phases, not a free-running progress value

Confirmed against live DocC: this is a three-case enum, not a continuous `0...1` scroll-progress float (Apple docs: `ScrollTransitionPhase`):

- **`.identity`** — the view is inside the visible region.
- **`.topLeading`** — the view is approaching (or has just left past) the top edge of a vertical scroll view, or the leading edge of a horizontal one.
- **`.bottomTrailing`** — the same, at the bottom/trailing edge.

Mechanically: as a view nears an edge, SwiftUI first invokes your closure with `.topLeading` or `.bottomTrailing` (whichever edge it's approaching), then swaps to `.identity` once the view is fully inside the visible region — and the effect you return for `.identity` stays applied for the entire time the view sits fully visible, not just for an instant. That's why the canonical pattern makes `.identity` a visual no-op and puts the actual transform on the other two cases: an identity phase that changes appearance would make the row look different every time it's simply sitting on screen, not just while entering/exiting.

Two convenience accessors ride along with the phase: `isIdentity` (`Bool`, shorthand for `phase == .identity`) and `value` (`Double`, "a phase-derived value that can be used to scale or otherwise modify effects") (Apple docs: `ScrollTransitionPhase`). Confirmed exact numeric mapping from the live declaration: `value` returns `-1.0` in the `.topLeading` phase, `0` in `.identity`, and `1.0` in `.bottomTrailing` — the two edges are distinct signs of the same unit range, not a shared magnitude, so `value` can drive a signed effect (e.g. a rotation that leans one way approaching the top and the other way approaching the bottom) directly, without your closure needing to switch on `phase` first to pick a sign.

### Canonical pattern: fade/scale rows at the scroll-view edge

```swift
ScrollView {
    LazyVStack {
        ForEach(items) { item in
            RowView(item: item)
                .scrollTransition { content, phase in
                    content
                        .opacity(phase.isIdentity ? 1 : 0.3)
                        .scaleEffect(phase.isIdentity ? 1 : 0.85)
                }
        }
    }
}
```

Because the closure's default configuration is `.interactive` (see below), this reads as a row that visibly fades and shrinks in lockstep with scroll position as it nears the edge, then snaps to full appearance the instant it's inside the visible region — not a fixed-duration animation firing once a threshold is crossed.

## `ScrollTransitionConfiguration`: Timing and Visibility Threshold

Controls *how* the phase transition interpolates, independent of *what* visual effect it applies (Apple docs: `ScrollTransitionConfiguration`). Three interchangeable strategies, each a static member or function on the type:

- **`.identity`** — no interpolation; the effect snaps between phases with no animation at all (Apple docs: `ScrollTransitionConfiguration.identity`).
- **`.animated`** / **`.animated(_:)`** — discretely animates the transition once a view crosses into or out of visibility, using a supplied `Animation` (or a default one) (Apple docs: `ScrollTransitionConfiguration.animated(_:)`).
- **`.interactive`** / **`.interactive(timingCurve:)`** — the default; interpolates the effect continuously as the view is scrolled through the visible region, so the effect tracks live scroll position rather than playing a fire-and-forget animation once a boundary is crossed (Apple docs: `ScrollTransitionConfiguration.interactive(timingCurve:)`).

Reach for `.interactive` (the default) whenever the effect should feel physically tied to scroll position — the common row fade/scale case. Reach for `.animated` when you want a discrete "snap into its transitioned state" moment instead of continuous tracking, closer in spirit to a triggered `PhaseAnimator` step than a gesture-tracked value.

**Threshold** (`.threshold(_:)`, taking a `ScrollTransitionConfiguration.Threshold`) sets *where* along the hidden-to-visible progression a view counts as fully visible for the purposes of this transition (Apple docs: `ScrollTransitionConfiguration.threshold(_:)`, `ScrollTransitionConfiguration.Threshold`):

- `.visible` / `.visible(_:)` — visible once a given fraction is showing (`0` fully hidden, `1` fully visible).
- `.hidden` / `.centered` — edge cases: fully hidden, or centered within the container.
- `.inset(by:)` — shifts an existing threshold toward (positive) or away from (negative) the container's center.
- `.interpolated(towards:amount:)` — blends two thresholds together.

`.animation(_:)` retunes just the `Animation` a configuration uses without switching between `.animated`/`.interactive` outright.

## `visualEffect(_:)`: Geometry-Reading Effects Without `GeometryReader`

Applies visual effects that depend on a view's own geometry — its size, its frame in some coordinate space — without pulling in `GeometryReader`'s side effects as a container (Apple docs: `View.visualEffect(_:)`).

`GeometryReader` is a layout container: it greedily consumes all the space its parent offers, and requires you to construct the child's actual layout from inside its closure. Reaching for it purely to *read* a size and apply a rendering-only effect drags in that layout behavior even when none of it was wanted — the view's frame in its parent changes just by wrapping it in `GeometryReader`.

`visualEffect(_:)` sidesteps this: it hands the closure the same kind of `GeometryProxy` context, but the closure itself has no layout authority — it can't resize or reposition anything, only apply visual effects to the view it's attached to. Closure shape: `(EmptyVisualEffect, GeometryProxy) -> some VisualEffect` — identical "proxy + context" pattern to `scrollTransition`'s closure, just with a `GeometryProxy` standing in for the phase.

```swift
ContentView()
    .visualEffect { content, proxy in
        content.offset(proxy.size)
    }
```

The `VisualEffect` protocol is what constrains this closure to genuinely rendering-only operations rather than the full `View` modifier vocabulary (Apple docs: `VisualEffect`): color adjustments (`brightness`, `contrast`, `grayscale`, `hueRotation`, `saturation`, `opacity`), geometric transforms (`scaleEffect`, `rotationEffect`/`rotation3DEffect`/`perspectiveRotationEffect`, `offset`, `transformEffect`/`transform3DEffect`), `blur`, `blendMode`, and the three shader modifiers below. There's no `.padding()`, `.background()`, or `.frame()` available inside this closure — if a geometry-driven effect genuinely needs one of those, `GeometryReader` (or reading geometry via a preference/backing modifier) is still the right tool, not `visualEffect`.

## Shader Effect Modifiers: Color, Layer Sampling, and Distortion

Three modifiers apply a `Shader` to a view, each expecting a different MSL function signature and solving a different class of problem — picking among them is a question of which transform the shader performs, not a style preference:

- **`colorEffect(_:isEnabled:)`** — remaps each pixel's *color*, independent of its position: the shader receives the pixel's position and its existing premultiplied color and returns a new color (Apple docs: `View.colorEffect(_:isEnabled:)`). Reach for this whenever the effect only needs one pixel's own color to decide its new color — tinting, thresholding, custom color grading.
- **`distortionEffect(_:maxSampleOffset:isEnabled:)`** — remaps each pixel's *source coordinate*, leaving color untouched: the shader receives a destination position and returns the position in the source content to sample from instead (Apple docs: `View.distortionEffect(_:maxSampleOffset:isEnabled:)`). Reach for this for warps, ripples, or lens-like effects where the pixel grid is bent but nothing about color itself changes.
- **`layerEffect(_:maxSampleOffset:isEnabled:)`** — the general case: the shader receives a destination position and a sampleable `Layer` representing the view's entire rasterized output, and may read from any number of positions in that layer to compute one output pixel (Apple docs: `View.layerEffect(_:maxSampleOffset:isEnabled:)`). Reach for this when a pure color remap or pure coordinate distortion isn't expressive enough — blur-like effects, or anything mixing multiple source pixels into one destination pixel.

`maxSampleOffset` (a `CGSize`, required on the two sampling-based modifiers, absent on `colorEffect` since it never samples anywhere but the destination pixel itself) declares the furthest in each axis, in the view's own local point space (it's a `CGSize`, the same unit every other SwiftUI geometry value uses), the shader will ever reach from the destination pixel to sample source content — confirmed from Apple's own parameter description: "If the shader function samples from the layer at locations not equal to the destination position, this value must specify the maximum sampling distance in each axis, for all source pixels." Apple's docs don't state the specific failure behavior for a shader that samples beyond the declared offset, so treat the parameter as a hard contract rather than a soft hint either way: declaring it too tight risks the shader being denied source pixels it actually needs at the effect's edges, while declaring it too generously forces SwiftUI to keep a larger rasterized region prepared than the effect requires, which costs memory and rendering time — size it to the effect's real reach, not defensively large.

`isEnabled` (default `true` on all three) toggles the effect without removing the modifier from the view tree, avoiding the view-identity churn that conditionally applying/removing the modifier itself would cause. Reach for it any time the effect needs to flip based on runtime state — including Reduce Transparency/Reduce Motion-style conditional gating (see `apple-design/references/accessibility.md § Reduce Motion` for the actual gating policy; this file only covers the on/off mechanism).

All three carry the same platform-view caveat: content whose rendering is ultimately backed by an embedded AppKit/UIKit view can't render into the filtered layer these modifiers create — SwiftUI logs a warning and substitutes a placeholder image instead (Apple docs: `View.colorEffect(_:isEnabled:)`).

## `Shader` and `ShaderLibrary`: Wiring Swift Arguments Into MSL

- **`ShaderLibrary`** resolves a compiled Metal shader function by name (Apple docs: `ShaderLibrary`). `.default` is the main app bundle's compiled library; `.bundle(_:)` targets a different bundle; `init(url:)`/`init(data:)` load a precompiled Metal library directly from its contents. Resolution is dynamic-member lookup by name — `ShaderLibrary.default.myShaderName` returns a `ShaderFunction` — there's no separate registration step; the string name is matched against the compiled library's stitchable functions.
- **`ShaderFunction`** is that resolved-but-not-yet-invoked reference: a library plus a function name (Apple docs: `ShaderFunction`). Calling it like a function — `ShaderLibrary.default.myShaderName(.float(x), .float2(point))` — is `dynamicallyCall(withArguments:)` under the hood, producing a `Shader` bound to those specific argument values.
- **`Shader`** is the final package handed to `colorEffect`/`distortionEffect`/`layerEffect`: a `ShaderFunction` plus its bound arguments, constructible directly via `init(function:arguments:)` when you already have a `ShaderFunction` rather than going through the call-syntax sugar (Apple docs: `Shader`).
- **Argument passing** — each `Shader.Argument` factory maps one Swift value to one MSL parameter, and arguments must be supplied in the same order the MSL function declares them after its implicit leading parameters (`position`, and `color` or `layer` depending on the modifier) (Apple docs: `Shader.Argument`):
  - `.float(_:)`, `.float2(_:_:)` / `.float2(_:)` (from a `CGPoint`), `.float3(_:_:_:)`, `.float4(_:_:_:_:)` → MSL `float` / `float2` / `float3` / `float4`.
  - `.color(_:)` → MSL `half4`, converted to a premultiplied color in the destination color space.
  - `.floatArray(_:)` / `.colorArray(_:)` / `.data(_:)` → an MSL pointer-plus-count/size pair (e.g. `device const float *ptr, int count`) rather than a single scalar — reach for these for variable-length data instead of trying to pass a Swift array as one argument.
  - `.image(_:)` → MSL `texture2d<half>`; only one image argument is supported per `Shader`.
  - `.boundingRect` → the attached view/shape's bounding rect as `float4(x, y, width, height)`; undefined for effects with no natural bounding rect (e.g. a filter drawn into a `GraphicsContext`).
- The three modifiers require distinct MSL entry-point shapes — `colorEffect` needs `(float2 position, half4 color, args...) -> half4`, `distortionEffect` needs `(float2 position, args...) -> float2`, `layerEffect` needs `(float2 position, SwiftUI::Layer layer, args...) -> half4` — so the same shader source generally needs a distinct entry point per role rather than one function serving all three (Apple docs: `View.colorEffect(_:isEnabled:)`, `View.distortionEffect(_:maxSampleOffset:isEnabled:)`, `View.layerEffect(_:maxSampleOffset:isEnabled:)`).
- `Shader.dithersColor` controls whether a color-producing shader's output gets dither noise added before quantizing to the display's bit depth — worth enabling for shaders generating smooth gradients, where banding would otherwise be visible (Apple docs: `Shader`).
- `Shader.compile(as:)` asynchronously precompiles a shader ahead of first use, so the first frame that actually needs it doesn't stall on Metal compiling the function on the spot (Apple docs: `Shader`).
