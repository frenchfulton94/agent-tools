> verified: 2026-08 against https://developer.apple.com/documentation/swiftui/uiviewrepresentable.md, https://developer.apple.com/documentation/swiftui/uiviewcontrollerrepresentable.md, https://developer.apple.com/documentation/swiftui/uihostingcontroller.md, https://developer.apple.com/documentation/swiftui/navigationstack.md
> sources: Design Patterns by Tutorials (single mapped chapter — Adapter pattern; the rest of this file's scope is engineering judgment plus the live docs above, honestly not attributed to the book corpus)

# Working safely in an existing shipped app

Most Apple-platform code you touch professionally isn't greenfield. It's a shipped app with
real users, partial test coverage, and architecture decisions nobody in the room made. The
goal here isn't purity — it's changing behavior without breaking what already works, and
leaving the code slightly more tractable than you found it.

Coverage note: the corpus for this file has exactly one relevant chapter, and it covers a
single technique — the Adapter pattern. Everything about refactor sequencing, seam-finding
judgment, and UIKit/SwiftUI coexistence below is engineering judgment and current Apple
documentation, not book material. Where a claim traces to the corpus, it's cited; where it
isn't cited, treat it as judgment to weigh against your own codebase's specifics, not as an
authoritative rule.

## Finding seams in code that wasn't designed for one

A "seam" is a place you can change behavior without editing the surrounding code — Michael
Feathers' term for it, and the concept holds regardless of source. Legacy Apple codebases
rarely have seams built in; you have to insert them.

**Protocol-wrap the concrete type you don't want to depend on directly.** If a view model,
view controller, or service reaches directly into a third-party SDK, a singleton, or another
team's module, define a narrow protocol that describes only the calls your code actually
makes, then either extend the existing type to conform or write a thin adapter class that
holds the legacy type privately and translates its calls and outputs into your own types
(Design Patterns by Tutorials, ch. 12). This is the single highest-leverage move available in
an existing codebase: it inverts the dependency without touching the legacy type's internals,
it's invisible to every other caller until you choose to change them, and it gives you exactly
one place to absorb a future SDK or API change instead of N call sites. Reach for it when
there's a real, foreseeable reason the wrapped type might change or need substituting — not
reflexively on every external dependency; an adapter around something that will never move is
pure indirection tax with no payoff (Design Patterns by Tutorials, ch. 12).

Two ways to build the adapter, same trade-off as any indirection layer:
- **Extension conformance** (`extension LegacyType: NewProtocol { ... }`) — less code, but the
  legacy type's original API stays visible and callable, so nothing stops a future caller from
  reaching around the seam.
- **Wrapper class** holding the legacy type as a private property — more boilerplate, but the
  legacy API is genuinely hidden; callers can only see the protocol.

Prefer the wrapper when you actually want the seam enforced (e.g., you intend to swap
implementations or mock it in tests); prefer the extension when you're just naming an existing
capability and don't need to hide anything.

**Identify module boundaries before you extract modules.** You don't need a Swift package
split to get the benefit of a boundary — you need the *shape* of one: a small set of types
that talk to the rest of the app only through a handful of entry points, with no back-channel
access to internals. Look for existing seams along feature lines (a tab, a flow, a screen
family) where imports already cluster — if `Feature/` files only import `Shared/` and never
reach into `OtherFeature/` internals, that boundary already exists conceptually even if it's
all one target. Naming and enforcing that boundary with `internal` access control (or a real
SPM target later) is cheap once you've found it, and expensive to invent from scratch after
the code has grown cross-cutting dependencies.

**Pin behavior before you touch it, if the codebase allows it.** Before refactoring code with
no tests, write a characterization test that asserts what the code *currently* does — not what
it should do — so a refactor that accidentally changes behavior fails loudly instead of
shipping silently. This is only a strategy note; the mechanics of writing the test belong to
the swift-testing skill. If the code is genuinely untestable as structured (hard singletons,
UIKit lifecycle coupling, no injection points), the adapter/protocol-wrap move above is often
the prerequisite that makes a characterization test possible at all — you may need to seam it
before you can pin it.

## Incremental refactor strategy

**Default to strangler-fig migration, not rewrite.** Write new code against the target
architecture (SwiftUI/Observation/async-await, or whatever the project's baseline is), leave
old code exactly as it is until a real change forces you into it, and let the new pattern grow
by displacement rather than replacement. The old and new coexist for as long as it takes —
weeks or years — and the app ships the whole time. A big-bang rewrite freezes feature work,
compounds risk into one enormous merge, and routinely rediscovers requirements the old code
encoded but nobody documented.

**A full rewrite is rarely the right call.** It's justified when the existing architecture
*actively blocks* required new behavior — e.g., a single massive view controller makes a
mandated feature structurally impossible to add safely, or a data layer can't support a
required offline/sync model no matter how it's patched. It is not justified because the old
code is unfashionable, uses UIKit instead of SwiftUI, or offends taste. "This is old" is not a
requirement; "we cannot ship X without restructuring this" is. If you can't name the specific
future feature or defect the current structure blocks, you're proposing a rewrite for
aesthetic reasons, and that's a much harder sell to whoever owns the shipping schedule than to
yourself.

**Calibrate the Boy Scout rule to the size of the errand you're actually running.** Improve
what you touch — rename the misleading variable, extract the tangled conditional, delete the
dead branch you tripped over — but only inside the diff you're already making for the real
reason you opened the file. A one-line bug fix that balloons into a 40-file architectural
refactor is scope creep wearing a virtue as a costume: it delays the actual fix, multiplies
review surface, and multiplies the chance of introducing an unrelated regression. If the file
needs more than local cleanup, that's a separate, explicitly-scoped refactor task — write it
down and do it as its own change, not smuggled inside today's fix.

## Maintaining older code: UIKit and SwiftUI coexistence

Most production Apple codebases spend years with both frameworks present. Neither direction —
UIKit hosting SwiftUI, or SwiftUI hosting UIKit — is inherently correct; the direction should
follow which framework owns the *screen's navigation and top-level state*, decided per screen,
not per app.

**SwiftUI embedding a UIKit view or view controller** (the common shape for adopting SwiftUI
piecemeal inside a UIKit-navigated app, or for reusing a UIKit component SwiftUI has no
equivalent for — a `PDFView`, a custom `UICollectionView` layout, a camera control) uses
`UIViewRepresentable` or `UIViewControllerRepresentable`. You implement `makeUIView(context:)` /
`makeUIViewController(context:)` to construct the legacy view once, when the representable is
first created, and `updateUIView(_:context:)` / `updateUIViewController(_:context:)` — which
Apple's documentation describes as called at appropriate times by the system — to push new
SwiftUI state into it as that state changes. For anything needing delegate callbacks or
target-action wiring back out of the UIKit type, implement `makeCoordinator()`: Apple's
documentation is explicit that the system does not automatically forward changes from your
UIKit view or view controller into SwiftUI, and that a `Coordinator` returned from
`makeCoordinator()` is the documented mechanism for forwarding target-action and delegate
messages back into SwiftUI.

**UIKit embedding a SwiftUI view** (the common shape when a UIKit app adopts SwiftUI
screen-by-screen, keeping the existing `UINavigationController`/`UITabBarController` shell)
uses `UIHostingController(rootView:)`, which Apple's documentation says to use "like you would
any other view controller, by presenting it or embedding it as a child view controller" —
including pushing it onto a `UINavigationController` like any standard `UIViewController`.
Update the SwiftUI content by reassigning `rootView` (or,
more idiomatically, by having `rootView` hold a reference to an `@Observable` model the
hosting controller and the rest of UIKit both write to).

**Never let both sides own the same piece of state.** The most common bug at this boundary is
a UIKit delegate and a SwiftUI `@State`/`@Observable` property independently tracking the same
fact, drifting out of sync because only one side's write triggers the other's read. Pick one
owner — usually whichever side owns the screen's overall data flow — and make the other side a
pure consumer that reads through the `Coordinator` (SwiftUI-hosts-UIKit direction) or through
the shared observable model (UIKit-hosts-SwiftUI direction). If neither framework's state
storage is authoritative, put the source of truth in a plain Swift type that both sides
reference, and treat both `@State` and the UIKit property as caches of it, not as owners.

**Navigation coexistence — decide per screen which shell owns navigation.** Two shapes show up
in practice:
- A `UINavigationController`-driven app hosting SwiftUI screens: each SwiftUI screen is a leaf
  wrapped in a `UIHostingController` and pushed normally; the SwiftUI screen has no
  `NavigationStack` of its own and delegates "go to next screen" back out to UIKit (typically
  via a closure or the Coordinator pattern) rather than trying to navigate internally.
- A SwiftUI `NavigationStack`-driven app hosting UIKit screens: the UIKit screen is wrapped in
  `UIViewControllerRepresentable` and pushed as a `NavigationStack` destination like any other
  SwiftUI view. Practical caution, not documented Apple guidance: Apple's NavigationStack
  documentation doesn't address UIKit interop directly, but `NavigationStack` maintains its own
  navigation state (either internally or via the path binding you give it), and a
  `UINavigationController` maintains its own view controller stack independently — so if the
  wrapped UIKit view controller also drives its own `UINavigationController` push/pop, you now
  have two independent navigation stacks that can each believe they own the current screen and
  the back button. Treat that combination as a smell to design around rather than a confirmed,
  documented failure mode.

Decide the direction per screen by asking which side already owns the *entry point* to that
screen. Migrating a leaf screen at the end of a UIKit flow into SwiftUI (host SwiftUI in
UIKit) is low-risk and the standard first move. Converting the flow's *root* controller to
SwiftUI (so the flow becomes `NavigationStack`-driven and hosts remaining UIKit leaves) is a
bigger, riskier step — usually the last thing you do in a given flow, once most of its screens
are already SwiftUI, not the first.

## Maintaining older code: Combine coexistence

Treat Combine-dependent legacy code the same way you'd treat any other legacy dependency:
wrap it behind a boundary so the rest of the app doesn't need to know Combine is there. A
service that currently exposes a `Publisher` can sit behind a protocol whose method returns an
`AsyncSequence`, a plain callback, or backs an `@Observable` type — the calling code depends on
that boundary type, not on Combine's operators or subscription lifecycle. This is the same
adapter move as wrapping any other legacy object: the win is that everything on the SwiftUI
side of the boundary is written as if Combine never existed, and the Combine code stays
quarantined to one adapter until it's convenient to actually rewrite it (or never, if it's
never touched again — see below). The operator-level mechanics of bridging a `Publisher` to
`async`/`await` or `AsyncSequence` are covered in depth by the swift-concurrency skill; this
file only covers the architectural decision to isolate the dependency, not how to bridge it.

## When not to touch it

Not every legacy corner is a refactor target, and treating "old" as synonymous with "bad" is
its own anti-pattern. Leave code alone when all of the following hold: it works correctly
today, it changes rarely (check its edit history if unsure), and no planned feature touches
its area. Refactoring it anyway spends real time and reintroduces regression risk into
something that was stable, for a payoff nobody will collect. The cost/risk calculation that
justifies a refactor is "we are about to pay to work in this code anyway, or its current shape
is actively causing defects" — not "this offends the current style guide." Modernization has
a real ongoing carrying cost too (review time, retraining muscle memory, risk of the rewrite
itself introducing bugs); spend it where a concrete, near-term need will cash it back in, not
as a background tax on stable code.
