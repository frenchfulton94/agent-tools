---
name: apple-animations
description: Implementing animations and motion in SwiftUI - withAnimation and the animation modifier, the Animatable protocol, springs and timing curves, Transaction, contentTransition, PhaseAnimator, KeyframeAnimator, TimelineView, view transitions, matchedGeometryEffect, zoom navigation transitions, scrollTransition scroll effects, visualEffect, and the Metal shader effect modifiers (colorEffect, layerEffect, distortionEffect). Use when writing, tuning, or debugging animation code - springs that feel wrong, transitions that jump instead of animating, keyframed or phased sequences, scroll-driven effects, shader effects. Not for whether or how much to animate or motion taste (apple-design), reduce-motion policy (apple-design), general layout and styling (apple-design), or the build/run loop (xcode-loop).
---

# Animations & motion (implementation)

Scope: how animation code is written. Whether/when/how much to animate is
judgment and belongs to apple-design (its `animation-taste` reference);
reduce-motion policy to apple-design (its `accessibility` reference); the
build/run loop to xcode-loop.

Read the reference for the decision at hand:
- withAnimation vs .animation, springs, timing, Transaction, contentTransition → `references/animation-fundamentals.md`
- Multi-step sequences: PhaseAnimator, KeyframeAnimator, TimelineView → `references/keyframe-and-phase-animators.md`
- Transitions, matchedGeometryEffect, zoom navigation transitions → `references/transitions-and-matched-geometry.md`
- scrollTransition, visualEffect, shader effect modifiers → `references/scroll-and-visual-effects.md`
- Gesture-driven motion — drags, sheets, carousels, flick-to-dismiss → `references/fluid-interfaces.md`

Rules that always apply:
- Animate state, not side effects: drive every animation from a state
  change the framework can interpolate; imperative timers are the last
  resort (TimelineView exists for the time-driven cases).
- Scope animations with the value: prefer `.animation(_:value:)` bound to
  the changing value, or `withAnimation` at the mutation site - unscoped
  animation modifiers animate things you did not intend.
- Springs are the default feel on Apple platforms; tune with the modern
  parameterization (duration/bounce) before reaching for custom curves.
- One namespace, one source: most matchedGeometryEffect failures are two
  active sources or mismatched identity - check `isSource` and view
  identity before rewriting the layout.
- Taste questions (is this too much motion?) → apple-design; this skill
  answers how, not whether.
