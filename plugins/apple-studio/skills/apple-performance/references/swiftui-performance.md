> verified: 2026-09 against https://developer.apple.com/documentation/xcode/understanding-and-improving-swiftui-performance.md, https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro.md, https://developer.apple.com/documentation/observation/observable.md, https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app.md, https://developer.apple.com/documentation/swiftui/view/id(_:).md, https://developer.apple.com/documentation/swiftui/lazyvstack.md, https://developer.apple.com/documentation/swiftui/list.md, https://developer.apple.com/documentation/swiftui/foreach.md, https://developer.apple.com/documentation/swiftui/geometryreader.md, https://developer.apple.com/documentation/swiftui/view/ongeometrychange(for:of:action:).md, https://developer.apple.com/documentation/swiftui/equatableview.md, https://developer.apple.com/documentation/swiftui/view/equatable().md, https://developer.apple.com/documentation/observation/observationignored().md, https://developer.apple.com/documentation/swiftui/bindable.md, https://developer.apple.com/documentation/observation/observable().md
> sources: live Apple docs (no book input — the corpus predates these frameworks)
> gui-verified: 2026-09-12 against Instruments in Xcode 27.0 on an iPhone 16 Pro
> Max (iOS 27.0). The SwiftUI track's lane names come from that session, not
> from the doc, which still carries the previous names.

# SwiftUI Performance

"Why is my SwiftUI list janky" resolves to one of five causes: excessive
updates, a `body` that does too much work, identity that resets when it
shouldn't, observation coarser than it looks, or a lazy container that
stopped being lazy. This file diagnoses all five. Render loop/hitches/launch:
`responsiveness-hangs-and-hitches.md`. Trace capture, call trees,
`OSSignposter`: `profiling-workflow.md`. Memory/power/disk:
`memory-power-and-size.md`. Animation *cost* is here; *implementation* is
`apple-animations`. Actor isolation: `swift-concurrency`. State ownership:
`swift-architecture`.

## Diagnosing excessive view updates (GUI-only — the SwiftUI instrument)

No command-line substitute exists for this — the cause-and-effect graph lives
only in the Instruments GUI:

1. **Product > Profile** → **SwiftUI** template → **Record** (deferred) →
   exercise the feature → **Stop Recording**.
2. Expand the SwiftUI track. Xcode 27 names the lanes **Update Groups**,
   **Long View Body Updates**, **Long Representable Updates**, and **Other
   Long Updates** — thresholded lanes holding the updates slow enough to
   matter, not every update, and *Representable* meaning
   `UIViewRepresentable`/`NSViewRepresentable` bridges specifically. Apple's
   doc still calls these *View Body Updates*, *Platform View Updates* and
   *Other Updates*; the shipped tool is ahead of the prose, so read the lane
   names off the timeline, not off the page. Each splits by module, so
   third-party and system code read apart from yours. The template also loads
   **Hitches** and **Hangs** instruments, so missed frames sit next to the
   updates that caused them.
3. One slow update: Control-click → **Set Inspection Range and Zoom**, read
   the **Time Profiler** call tree/Flame Graph beneath it. Too few samples
   from one instance? Clear the range, Control-click `MyView.body`, **Show
   Calls Made by MyView.body** to aggregate every instance.
4. Many short updates (the more common jank shape): use **Update Groups**
   instead of chasing individual long ones — Control-click a group → **Set
   Inspection Range** → **Summary: All Updates** for which views updated and
   how often. Then hover an update, click its arrow, **Show Causes** for a
   node-and-edge graph: nodes are objects that generate or receive updates
   (view bodies, environment objects, transactions), edges are the causal
   links between them — e.g. an `@Observable` object to the body reading one
   of its properties. Click an edge and the inspector names the property that
   changed. Instruments may draw the same object in several places and
   highlights every copy when you select one, so a node appearing twice is
   presentation, not two objects.

Watch for a round trip that leaves your code and comes back — your object, a
system node, then your body again: your code produced an event only your own
code needed, but SwiftUI mediated the hop. Cut the hop instead (see
`onGeometryChange` below). Cheaper first check before any of this:
`Self._printChanges()` at the top of `body` logs which property triggered
that evaluation — undocumented, debug-only, not for shipping code.
It is **underscored and undocumented** — no DocC page exists for it — so it
carries no availability guarantee and should never ship in committed code. It
does compile on this toolchain (Swift 6.4 / Xcode 27.0, verified 2026-09-02);
treat that as "works today", not as API.

## Structural identity and `.id()` misuse

SwiftUI assigns **structural identity** implicitly from a view's type and its
position in the tree (including branch position inside `if`/`switch`).
`.id(_:)` overrides that with **explicit identity**: per Apple, "when the
proxy value specified by the `id` parameter changes, the identity of the view
— for example, its state — is reset." A changed `.id()` destroys and
rebuilds the view rather than updating it — discarding `@State`, in-flight
animations, ancestor-held scroll position, and all subview state beneath it.

The classic own-goal: using `.id()` as a "force a refresh" hammer.

```swift
import SwiftUI

// BEFORE: .id() resets identity on every keystroke
struct SearchScreenBad: View {
    @State private var query: String = ""
    var items: [String]
    var body: some View {
        List(items, id: \.self) { Text($0) }
            .id(query) // wrong: drops scroll position + row state per keystroke
    }
}

// AFTER: filter the data, let List keep its identity
struct SearchScreenGood: View {
    @State private var query: String = ""
    var items: [String]
    var filtered: [String] { query.isEmpty ? items : items.filter { $0.contains(query) } }
    var body: some View {
        List(filtered, id: \.self) { Text($0) }
    }
}
```

`.id()` is correct when a full reset is the goal: swapping to a genuinely
different document, resetting a form after submit, forcing a transition to
restart instead of interpolate. The test is intent — use it to *discard*
state on purpose, never as a stand-in for an untracked dependency.

## Expensive `body` computation

`body` runs far more than intuition suggests — any changed read dependency
recomputes it, and it must finish inside the frame budget or it causes the
hitches covered in `responsiveness-hangs-and-hitches.md`. Apple's guidance:
keep initializers, `body`, `onAppear`, `onChange`, and any state-mutating
modifier cheap. Move real computation into the model, cache the result, have
`body` read the cache:

```swift
import SwiftUI

@Observable
final class ReportModel {
    var rows: [Double] = []
    var total: Double = 0
    func recompute() { total = rows.reduce(0, +) }
}

// body reads a precomputed value — no work happens during view update.
struct ReportGood: View {
    var model: ReportModel
    var body: some View { Text("Total: \(model.total)") }
}
```

`recompute()` runs off the render path, wherever the data actually changes.
Scheduling heavy work is `swift-concurrency`'s call; where the cached value
lives is `swift-architecture`'s — this file only owns that it isn't `body`.

The other body-cost trap: closures stored on a view. One that captures
`self` — explicitly, or implicitly via any of the view's own properties —
forces SwiftUI to recompute its result whenever *any* property on the view
changes, not just the one the closure uses. For a closure that builds a
child view, call it once in the initializer and store only the result;
don't mark it `@escaping`. Action closures (`Button`'s action) and
parameterized closures (`ForEach`'s content builder) are exempt, but can
still over-update for other reasons covered above.

## Observation granularity

`@Observable` tracks at property level: a view depends only on the properties
its `body` actually reads, and updates only when one of those changes — not
on any change anywhere in the object. This is the improvement over
`ObservableObject`, whose `@Published` properties broadcast to every observer
on any published change, read or not (migrating old code: see
`swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro`).

That granularity is easy to destroy by reading through a computed property
that touches several fields — the computed property becomes the dependency,
invalidating on a change to *any* field it touches, wanted or not:

```swift
import SwiftUI

@Observable
final class Settings {
    var displayName: String = ""
    var themeColor: String = "blue"
    var lastSyncedAt: Date = .now
}

// BAD: dependency is `summary`, spanning 3 fields — lastSyncedAt ticking
// on every background sync now invalidates this view too.
struct HeaderBad: View {
    var settings: Settings
    var summary: String { "\(settings.displayName) — \(settings.themeColor)" }
    var body: some View { Text(summary) }
}

// GOOD: body reads exactly the two fields it displays, directly.
struct HeaderGood: View {
    var settings: Settings
    var body: some View {
        Text("\(settings.displayName) — \(settings.themeColor)")
    }
}
```

Other granularity rules worth knowing cold:

- A global/singleton read directly in `body` still creates a real dependency
  — the object needn't be stored on the view. Reading a *collection*
  (`List(books)`) depends only on its structure (insert/delete/move), not on
  any element's fields — row closures push per-field dependency down to each
  row's own `body`, so the list itself doesn't re-run when one `title` changes.
- A view that reads none of an observable object's properties in `body`
  forms **no dependency** and never updates for it — an object can pass
  through several intermediate views for free as long as those layers don't
  read it. Don't "helpfully" extract a field into an intermediate view's own
  body just to pass it down; pass the unread reference through instead.
- `@ObservationIgnored` opts one property out of tracking entirely (a cache,
  a counter); `@Bindable` gets a `Binding` to a mutable `@Observable`
  property (`TextField`/`Toggle`) without `ObservableObject` wrappers.

## Lazy containers in long lists

`LazyVStack`/`List` create child views only for the visible region plus a
small buffer — that's the entire case for them over `VStack`+`ForEach` in a
plain `ScrollView`. Patterns that quietly defeat this laziness:

- **A `GeometryReader` per row**, or wrapping the whole scroll region. Apple
  flags a layout reader that "recalculates scroll geometry for the views it
  contains, including for updates that don't result in any scroll changes"
  as a direct cause of excessive updates — one per row forces layout work
  per realized row. Prefer `onGeometryChange(for:of:action:)` scoped to one
  derived value, gated on a real threshold rather than every pixel moved.
- **Non-constant view count per `ForEach` element.** Lazy containers query
  elements assuming each produces a *constant* number of child views; a bare
  `if` inside the closure breaks that. Wrap the branch in a `Group`/`VStack`
  so it always yields one view — `-LogForEachSlowPath YES` catches this
  at runtime.
- **Row identity churn.** Rows match across updates by `Identifiable` id; one
  regenerated per render, or derived from array index across a reorder,
  reads as delete-plus-insert — full rebuild instead of reuse, and lost
  row-local `@State`. Same structural/explicit-identity split as `.id()`
  above, applied per row.
- **`.equatable()` as a targeted firewall**, once profiling names a specific
  row body re-running wastefully for inputs that didn't meaningfully change
  — not as a default. `EquatableView` "prevents its child updating if its
  new value is the same as its old value":

  ```swift
  import SwiftUI

  struct Point3: Equatable { var x: Double; var y: Double; var z: Double }

  struct ExpensiveGlyph: View, Equatable {
      var point: Point3
      var body: some View { Text("\(point.x), \(point.y), \(point.z)") }
  }

  struct Scene3D: View {
      var point: Point3
      var body: some View { ExpensiveGlyph(point: point).equatable() }
  }
  ```

## Which Instruments template answers which question

| Question | Template / lane | GUI-only? |
|---|---|---|
| Which view updated, how often, from where | **SwiftUI** — the Long View Body / Long Representable / Other Long Updates lanes | Yes |
| One update's body ran too long — what ran | **SwiftUI** selection → **Time Profiler** call tree | Yes |
| Many short updates, cumulatively costly | **SwiftUI** → **Update Groups** | Yes |
| What caused this update to fire | **SwiftUI** → **Show Causes** graph | Yes |
| Frame missed deadline vs. app just slow | Hitches lane — `responsiveness-hangs-and-hitches.md` | Yes |
| General CPU hot path, not SwiftUI-specific | Time Profiler — `profiling-workflow.md` | Partial (`xctrace` covers capture) |
| Memory growth tied to view/model lifetime | Allocations/Leaks — `memory-power-and-size.md` | Yes |

## Classic pitfalls

- `.id()` as a "force refresh" hammer instead of finding the missing read
  dependency — `.id(UUID())` means every update is a full reset.
- A computed property spanning several `@Observable` fields as the only
  thing `body` touches — silently collapses per-field granularity to
  whole-object.
- `GeometryReader` for anything but "I need my own size," especially
  wrapping a scrollable container's children instead of one leaf.
- An `@escaping` closure stored on a view when it only builds a child view
  once — call it in `init`, store the result instead.
- `if`/`switch` directly inside a `ForEach` closure feeding a lazy
  container — non-constant view count, silent fast-path loss; verify with
  `-LogForEachSlowPath YES`.
- Treating a quiet recording as proof of anything — the SwiftUI instrument
  only shows what happened during interactions performed while recording.
