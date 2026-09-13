# Chapter map: swift-architecture

Targets (Task 3): `architecture-patterns.md`, `state-and-di.md`, `module-boundaries.md`,
`persistence.md`, `existing-code.md`.

Ranges overlap intentionally where a chapter carries decision-grade material for more
than one target file — each target's distillation subagent reads only the lines listed
for it and extracts only what's relevant to its own topic.

## advanced-ios-app-architecture-v4-0-0.md

- L137–L448: Chapter 2: Which Architecture Is Right for Me? → architecture-patterns.md
- L301–L312: Chapter 2, "My app takes a long time to compile" (multi-module build-time rationale) → module-boundaries.md
- L351–L358: Chapter 2, "I'm forced to make big decisions early in a project" (deferring the database decision behind protocols) → persistence.md
- L571–L580: Chapter 3, "Xcode project targets" (Koober's Koober/KooberiOS/KooberUIKit/KooberKit Swift Package split) → module-boundaries.md
- L647–L1849: Chapter 4: Objects & Their Dependencies (DI theory: on-demand, factories, single-container, container hierarchy) → state-and-di.md
- L1849–L2867: Chapter 5: Architecture: MVVM → architecture-patterns.md
- L1891–L1926: Chapter 5, "Repository pattern" (persistence/networking facade, testability) → persistence.md
- L2867–L3909: Chapter 6: Architecture: Redux → architecture-patterns.md
- L3909–L4291: Chapter 7: Architecture: Elements, Part 1 → architecture-patterns.md
- L4291–L5309: Chapter 8: Architecture: Elements, Part 2 → architecture-patterns.md
- SKIP: Chapter 1 (Welcome), Chapter 3 body outside L571–L580 (Koober app tour, no decision-grade content beyond the package split), front matter/license/forums, Conclusion.

## app-architecture-2018-05-07.txt

(PDF text; headings recovered via page-break markers, verified with `sed -n '<line>p'`.)

- L438–L1254: Chapter 2: Overview of Application Design Patterns (5-task comparison framework: construction, updating the model, changing the view, view state, testing) → architecture-patterns.md
- L1255–L2660: Chapter 3: Model-View-Controller → architecture-patterns.md
- L2661–L3962: Chapter 4: Model-View-ViewModel + Coordinator → architecture-patterns.md
- L3963–L4501: Chapter 5: Networking (controller-owned vs. model-owned networking placement) → architecture-patterns.md
- L4502–L5760: Chapter 6: Model-View-Controller + ViewState → architecture-patterns.md
- SKIP: Chapter 1 (Introduction, generic), Chapter 7 (ModelAdapter-ViewBinder — experimental, depends on the unmaintained CwlViews framework), Chapter 8 (The Elm Architecture — experimental/uncommon; Redux is already covered from advanced-ios-app-architecture), front matter.

## design-patterns-by-tutorials-v3-0-0.md

- L1015–L1488: Chapter 4: Delegation Pattern (delegation→closures judgment) → architecture-patterns.md
- L2599–L2836: Chapter 8: Observer Pattern → architecture-patterns.md
- L3305–L3600: Chapter 10: Model-View-ViewModel Pattern → architecture-patterns.md
- L3601–L3742: Chapter 11: Factory Pattern → architecture-patterns.md
- L3743–L4064: Chapter 12: Adapter Pattern (wrapping a legacy/third-party object behind a protocol — the canonical seam for legacy coexistence) → existing-code.md
- L7273–L7808: Chapter 23: Coordinator Pattern → architecture-patterns.md
- SKIP: all other chapters (MVC, Strategy, Singleton, Memento, Builder, Iterator, Prototype, State, Multicast Delegate, Facade, Flyweight, Mediator, Composite, Command, Chain-of-Responsibility) — Obj-C-era filler or not relevant to a SwiftUI app's pattern choices, per brief. Front matter/license/forums, Conclusion.

## thinking-in-swiftui-2023-09-22.txt

(PDF text; headings verified with `sed -n '<line>p'`.)

- L108–L744: Chapter 2: View Trees (view builders, render trees, identity — identity governs when @State resets) → state-and-di.md
- L745–L2294: Chapter 3: State and Binding (State, Observable macro, ObservableObject protocol, bindings, which property wrapper for what purpose) → state-and-di.md
- L2295–L3868: Chapter 4: Layout (leaf views, view modifiers, container views, alignment — view composition/decomposition judgment) → architecture-patterns.md
- SKIP: Chapter 1 (Introduction), Chapter 5 (Environment), Chapter 6 (Animations), Chapter 7 (Advanced Layout) — out of the brief's specified scope (view trees, state, layout only).
