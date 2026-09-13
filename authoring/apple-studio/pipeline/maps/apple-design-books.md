# Chapter map: apple-design books

Targets (Tasks 2–4): `hig-foundations.md`, `hig-patterns.md`, `platform-idioms.md`,
`accessibility.md`, `swiftui-design-implementation.md`, `animation-taste.md`.

Book scope per brief (2026-08-04-phase2-design-ux/task-1-brief.md): SwiftUI by
Tutorials chapters route ONLY to `swiftui-design-implementation.md` (layout-system
judgment, styling/view-modifier judgment, custom-vs-system-component judgment,
adaptive/multiplatform layout) and `accessibility.md` (the dedicated accessibility
chapter). iOS Animations chapters route to `animation-taste.md` (animation
principles, timing, transitions); UIKit/Core-Animation-mechanics chapters are
skipped except where the underlying judgment transfers to SwiftUI — those are
marked `(Maintaining older code: candidate)`, since the source material is
UIKit/CALayer-specific even though the concept (spring physics, easing, keyframes,
custom timing curves) carries over. Both books are 2022-era (v5.0.0 / v7.0.0):
API-specific mechanics are presumptively stale and excluded; only durable judgment
is mapped. Every range start below was verified with `sed -n '<start>p'` against
the converted corpus file.

## swiftui-by-tutorials-v5-0-0.md

- L763–L952: Chapter 3, "Views and Modifiers" → "Order of Modifiers" (modifier-ordering semantics: modifiers apply in sequence, order changes the result) → swiftui-design-implementation.md
- L981–L1086: Chapter 3, "Creating a Custom Button Style" (`ButtonStyle` protocol — when to make a custom style vs. use a system one) → swiftui-design-implementation.md
- L1155–L1188: Chapter 3, "'Debugging' Dark Mode" (dark-mode-specific rendering issues to check for) → swiftui-design-implementation.md
- L1217–L1352: Chapter 3, "Adapting to the Device Screen Size" (`GeometryReader`, `previewDevice`, proportional sizing judgment) → swiftui-design-implementation.md
- L2889–L3092: Chapter 6, "Styling the TextField" → "Creating a Custom Modifier" (custom `ViewModifier` pattern, when to extract one) → swiftui-design-implementation.md
- L3711–L4602: Chapter 7: Introducing Stacks & Containers (layout-priority judgment, HStack/VStack/ZStack tradeoffs, container-view layout behavior, lazy stacks) → swiftui-design-implementation.md
- L7885–L8738: Chapter 12: Accessibility (VoiceOver, SwiftUI accessibility-by-default judgment, reducing jargon, reordering navigation, adapting to user settings, "truly testing" accessibility) → accessibility.md
- L10123–L10390: Chapter 16: Grids (fixed vs. flexible vs. adaptive `LazyVGrid`/`LazyHGrid` column judgment) → swiftui-design-implementation.md
- L12509–L12700: Chapter 21, "Building Reusable Views" → "Using a ViewBuilder" (reusable-view/custom-component composition judgment) → swiftui-design-implementation.md
- L13293–L13604: Chapter 22, "Framing the Window" → "Using the Toolbar" (macOS window sizing, Settings window, menu bar, toolbar — multiplatform-specific UI judgment) → swiftui-design-implementation.md
- L13857–L14286: Chapter 23, "Navigation in macOS" → "The Last Viewed Flight" (adapting one SwiftUI codebase's layout/navigation/frames from iOS to macOS) → swiftui-design-implementation.md
- SKIP: Chapter 1 (Introduction, generic), Chapter 2 (Getting Started — tutorial walkthrough, no durable judgment beyond what Ch3/7 already cover), rest of Chapter 3 (Neumorphism cosmetic recipe — a visual trend, not native-HIG judgment; out of this skill's native-correctness scope), Chapter 4 (Testing & Debugging — not design), Chapter 5 (Intro to Controls: Text & Image — tutorial mechanics, Accessibility-With-Fonts subsection too thin to carry on its own), rest of Chapter 6 (form-validation/keyboard mechanics), Chapters 8–9 (State & Data Flow — architecture territory, covered by `swift-architecture`'s `state-and-di.md`, not this skill), Chapter 10 (More User Input & App Storage — control tutorial walkthrough, no durable styling/layout judgment beyond Ch6/7), Chapter 11 (Gestures — interaction handling, not layout/styling/component/adaptive-layout judgment per brief's four categories), Chapter 13 (Navigation — HIG's live `navigation-and-search`/`modality` pages are the current source of truth, not a 2022 book), Chapters 14–15 (Lists / Advanced Lists — tutorial mechanics), Chapter 17 (Sheets & Alert Views — modality is a HIG-pattern topic sourced live, not from this book), Chapter 18 (Drawing & Custom Graphics — Canvas/Path mechanics for a specific pie-chart tutorial, not durable judgment), Chapters 19–20 (Animations / View Transitions & Charts — animation content is explicitly out of scope for this book per the brief; sourced from the iOS Animations book + HIG motion page instead), rest of Chapter 21 (`Timeline`/keypath/`UIViewRepresentable` integration mechanics), rest of Chapter 22 (Markdown/HTML preview mechanics, app installation), rest of Chapter 23 (build-error/crash-diagnosis mechanics specific to the tutorial project), Conclusion, front matter/license/forums/dedications/about-the-authors.

## ios-animations-by-tutorials-v7-0-0.md

- L211–L572: Chapter 1, "Your First SwiftUI Animation" → "Exploring More View Modifiers" (implicit-animation basics, the `Animation` type, timing-curve vocabulary) → animation-taste.md
- L951–L1106: Chapter 2, "Adding View Transitions" → "Interactive Animations" (transition-type judgment, purposeful vs. decorative interactive motion) → animation-taste.md
- L1357–L1414: Chapter 3, "Animation Easing" (UIKit `UIView.AnimationOptions` easing curves — the ease-in/ease-out/linear judgment transfers directly to SwiftUI's animation curves) → animation-taste.md (Maintaining older code: candidate)
- L1467–L1614: Chapter 4, "Spring Animations" → "Animating User Interactions" (spring-vs-eased-curve judgment, when a spring reads as "natural") → animation-taste.md (Maintaining older code: candidate)
- L1645–L1852: Chapter 5, "Example Transitions" → "Mixing in Transitions" (transition taxonomy: add/remove/hide-show/replace — the conceptual categories, not the UIKit API) → animation-taste.md (Maintaining older code: candidate)
- L2315–L2466: Chapter 7, "Keyframe animations" → "Calculation Modes in Keyframe Animations" (breaking a motion into discrete keyframes — concept transfers to SwiftUI's `KeyframeAnimator`) → animation-taste.md (Maintaining older code: candidate)
- L3541–L3660: Chapter 10, "Animations vs. real content" → "Best Practices" (presentation-layer-vs-model-state distinction during animation; general animation-code best practices) → animation-taste.md (Maintaining older code: candidate)
- L4207–L4348: Chapter 12, "Animation Easing" → "More Timing Options" (repeat/speed timing judgment, second easing-curve treatment) → animation-taste.md (Maintaining older code: candidate)
- L4395–L4702: Chapter 13, "Damped Harmonic Oscillators" → "Specific Layer Properties" (spring-parameter physics: mass, stiffness, damping, initial velocity — maps directly onto `Animation.spring(response:dampingFraction:)` judgment) → animation-taste.md (Maintaining older code: candidate)
- L7707–L7852: Chapter 23, "Custom Animation Timing" → "Custom Bézier Curves" (cubic-Bézier timing-curve judgment — how control points shape perceived motion) → animation-taste.md (Maintaining older code: candidate)
- SKIP: Introduction (generic), rest of Chapter 1/2 (SwiftUI-native but tutorial-mechanics: drawing a specific spinner, building a specific gallery — no additional durable judgment beyond the ranges above), Chapter 6 (View Animations in Practice — crossfade/cube/bounce recipes, dated visual-effect specific), Chapter 8–9 (Auto Layout / Animating Constraints — UIKit constraint mechanics, no animation-taste judgment), Chapter 11 (Animation Keys & Delegates — CALayer delegate/KVC mechanics, no transferable judgment), Chapter 14 (Layer Keyframe Animations & Struct Properties — redundant CALayer mechanics, already covered by Ch7's more general treatment), Chapters 15–18 (Shapes & Masks / Gradient Animations / Stroke & Path Animations / Replicating Animations — niche decorative-effect recipes), Chapters 19–21 (View Controller Transition Animations — UIKit transitioning-delegate mechanics, no judgment beyond what's already captured), Chapter 22 and rest of Chapter 23 (`UIViewPropertyAnimator` mechanics beyond the Bézier-curve section), Chapter 24–25 (interactive/`UIViewPropertyAnimator` VC transitions — mechanics), Chapters 26–27 (3D Animations — `CATransform3D`/camera/anchor-point mechanics, niche and decorative), Conclusion, front matter/license/forums/dedications/about-the-author.
