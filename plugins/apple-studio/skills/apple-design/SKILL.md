---
name: apple-design
description: Apple Human Interface Guidelines conformance for iOS/iPadOS/macOS apps - layout, typography and Dynamic Type, color and materials, navigation and modality patterns, platform idioms, accessibility, and animation judgment. Use when designing or building UI, choosing a navigation or presentation pattern, styling views, making an app feel native, or fixing accessibility, Dynamic Type, or contrast issues. Not for brand identity or custom visual styling.
---

# Apple design (native correctness)

Scope: HIG conformance only. Brand identity, custom look-and-feel, and visual
distinctiveness belong to other tooling; this skill makes screens correctly
Apple.

Read the reference for the decision at hand:
- Layout, typography, color, materials, SF Symbols → `references/hig-foundations.md`
- Navigation, modality, feedback, forms, empty states (HIG gap — no dedicated empty-states page; hig-patterns.md's empty-state coverage is HIG-sourced, folded into the Tab Bars bullet) → `references/hig-patterns.md`
- iPhone vs iPad vs Mac in one codebase → `references/platform-idioms.md`
- Layout across sizes, poses, and foldables (iPhone Duo), reserved regions, bars that move to the side → `references/adaptive-layout.md`
- Accessibility (labels, targets, contrast, motion) → `references/accessibility.md`
- Implementing design correctly in SwiftUI → `references/swiftui-design-implementation.md`
- Whether and how to animate → `references/animation-taste.md`
- Mac structure and mechanics (windows, scenes, menu bar) → `apple-macos` skill
- Animation implementation (springs, keyframes, transitions API, shader effects) → `apple-animations` skill

Rules that always apply:
- System-provided first: text styles (never fixed point sizes), semantic
  colors, system components, SF Symbols. Custom only with a stated reason.
- Every screen ships accessible: Dynamic Type, VoiceOver labels, 44pt
  targets, sufficient contrast, Reduce Motion respected. The checklist lives
  in `references/accessibility.md`.
- After building UI, verify visually: capture screenshots via the xcode-loop
  skill and review them against this skill's checklists.
- The current HIG wins over anything written here:
  https://developer.apple.com/design/human-interface-guidelines
