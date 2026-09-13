---
name: swift-architecture
description: Architecture and code-structure judgment for Apple-platform apps - choosing an app architecture, state management and dependency injection in SwiftUI, module boundaries, persistence choice (SwiftData/Core Data/CloudKit/files), and working safely in existing shipped code. Use when designing a new app or feature, restructuring code, deciding where state or logic lives, choosing a persistence stack, or before large refactors.
---

# Swift app architecture

Before designing or restructuring, read the reference for the decision at hand:
- Choosing/keeping an architecture, pattern-vs-ceremony → `references/architecture-patterns.md`
- State ownership, DI, Observation → `references/state-and-di.md`
- Module/SPM decomposition → `references/module-boundaries.md`
- Storing data → `references/persistence.md`
- Changing shipped code → `references/existing-code.md`

Process: state the decision explicitly → read the matching reference → apply its
decision criteria to THIS app's size and constraints → prefer the simplest
structure the criteria allow (ceremony is a cost, not a virtue) → record
non-obvious choices in code comments only where the code cannot show the why.
