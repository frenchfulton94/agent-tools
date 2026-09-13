# Live endpoint map: apple-animations

Targets (Tasks 2–3): `animation-fundamentals.md`, `keyframe-and-phase-animators.md`,
`transitions-and-matched-geometry.md`, `scroll-and-visual-effects.md`.

Phase 5 is the first phase with no books map of its own. Animation judgment already
lives in `plugin/skills/apple-design/references/animation-taste.md` (see the
cross-map note at the end of this file); the remainder of the animation-adjacent
book material was SKIPped during Phase 2 planning as non-durable (tutorial
mechanics or content explicitly deferred to the animation book + HIG motion page —
see `pipeline/maps/apple-design-books.md`). This map is a **seed list, not an
exhaustive registry**, per the CONVENTIONS.md "Distillation maps" rule: it
enumerates dispatch-time starting points, distillers may follow narrower pages
under an enumerated parent when the fetch actually succeeds (DocC JSON 200), and
the reference files' own header citations — not this map — are the citation
record. Expected-but-missing pages are recorded below as `MISSING:`.

## Endpoint pattern

```
https://developer.apple.com/tutorials/data/documentation/<path>.json
```

where `<path>` mirrors the human URL path under `developer.apple.com/documentation/`
(lowercase, hyphenated, exactly as Apple's own `topicSections`/`references` JSON
reports it).

All 26 endpoints seeded by the brief were fetched with
`curl -s -o <file> -w '%{http_code}'` on 2026-08-05 and returned 200 (none of the
pre-probed list had drifted since the 2026-08-04 planning pass). Of those 26,
exactly one is a DocC *index* page (`role: collectionGroup`, non-empty
`topicSections`): `swiftui/animations`. The other 25 are `role: symbol` leaf pages,
confirmed via each fetched JSON's `metadata.role` — no other seed needed
enumeration.

`swiftui/animations` was fetched and its `topicSections` walked via the
`references` map to find child titles and human URLs. 53 additional children were
individually fetched and confirmed 200 before being added below (see the Task 1
report for the full probe log). Two groups of children were deliberately **not**
added, matching the macOS map's precedent of excluding out-of-scope/deprecated
index children:

- The "Deprecated types" section (`AnimatableModifier`) — deprecated, superseded by
  the `Animatable` protocol already seeded.
- `watchOS-Apps/updating-watchos-apps-with-timelines` (under "Updating a view on a
  schedule") — a watchOS-specific complication article; `TimelineView` itself and
  its supporting types (`TimelineSchedule`, `TimelineViewDefaultContext`) are
  seeded/added below, but this platform-specific tutorial article is out of scope
  for a general SwiftUI animations skill.

No expected-but-missing pages were found while enumerating `swiftui/animations` —
zero `MISSING:` entries in this map.

## animation-fundamentals.md

- `https://developer.apple.com/documentation/swiftui/animations` → `https://developer.apple.com/tutorials/data/documentation/swiftui/animations.json` (index, enumerated below)
- `https://developer.apple.com/documentation/swiftui/animation` → `https://developer.apple.com/tutorials/data/documentation/swiftui/animation.json`
- `https://developer.apple.com/documentation/swiftui/withanimation(_:_:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/withanimation(_:_:).json`
- `https://developer.apple.com/documentation/swiftui/view/animation(_:value:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/animation(_:value:).json`
- `https://developer.apple.com/documentation/swiftui/animatable` → `https://developer.apple.com/tutorials/data/documentation/swiftui/animatable.json`
- `https://developer.apple.com/documentation/swiftui/spring` → `https://developer.apple.com/tutorials/data/documentation/swiftui/spring.json`
- `https://developer.apple.com/documentation/swiftui/transaction` → `https://developer.apple.com/tutorials/data/documentation/swiftui/transaction.json`
- `https://developer.apple.com/documentation/swiftui/contenttransition` → `https://developer.apple.com/tutorials/data/documentation/swiftui/contenttransition.json`

Children of `swiftui/animations` filed under this reference (the "Adding
state-based animation to an action/view", "Creating custom animations", "Making
data animatable", "Moving an animation to another view", and content-transition
entries from "Defining transitions" — all mechanics that belong with the
fundamentals of triggering, customizing, and transacting an animation rather than
with keyframes, matched-geometry transitions, or shaders):

- `https://developer.apple.com/documentation/swiftui/withanimation(_:completioncriteria:_:completion:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/withanimation(_:completioncriteria:_:completion:).json`
- `https://developer.apple.com/documentation/swiftui/animationcompletioncriteria` → `https://developer.apple.com/tutorials/data/documentation/swiftui/animationcompletioncriteria.json`
- `https://developer.apple.com/documentation/swiftui/view/animation(_:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/animation(_:).json`
- `https://developer.apple.com/documentation/swiftui/view/animation(_:body:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/animation(_:body:).json`
- `https://developer.apple.com/documentation/swiftui/customanimation` → `https://developer.apple.com/tutorials/data/documentation/swiftui/customanimation.json`
- `https://developer.apple.com/documentation/swiftui/animationcontext` → `https://developer.apple.com/tutorials/data/documentation/swiftui/animationcontext.json`
- `https://developer.apple.com/documentation/swiftui/animationstate` → `https://developer.apple.com/tutorials/data/documentation/swiftui/animationstate.json`
- `https://developer.apple.com/documentation/swiftui/animationstatekey` → `https://developer.apple.com/tutorials/data/documentation/swiftui/animationstatekey.json`
- `https://developer.apple.com/documentation/swiftui/unitcurve` → `https://developer.apple.com/tutorials/data/documentation/swiftui/unitcurve.json`
- `https://developer.apple.com/documentation/swiftui/animatablevalues` → `https://developer.apple.com/tutorials/data/documentation/swiftui/animatablevalues.json`
- `https://developer.apple.com/documentation/swiftui/animatablepair` → `https://developer.apple.com/tutorials/data/documentation/swiftui/animatablepair.json`
- `https://developer.apple.com/documentation/swiftui/vectorarithmetic` → `https://developer.apple.com/tutorials/data/documentation/swiftui/vectorarithmetic.json`
- `https://developer.apple.com/documentation/swiftui/emptyanimatabledata` → `https://developer.apple.com/tutorials/data/documentation/swiftui/emptyanimatabledata.json`
- `https://developer.apple.com/documentation/swiftui/withtransaction(_:_:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/withtransaction(_:_:).json`
- `https://developer.apple.com/documentation/swiftui/withtransaction(_:_:_:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/withtransaction(_:_:_:).json`
- `https://developer.apple.com/documentation/swiftui/view/transaction(_:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/transaction(_:).json`
- `https://developer.apple.com/documentation/swiftui/view/transaction(value:_:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/transaction(value:_:).json`
- `https://developer.apple.com/documentation/swiftui/view/transaction(_:body:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/transaction(_:body:).json`
- `https://developer.apple.com/documentation/swiftui/entry()` → `https://developer.apple.com/tutorials/data/documentation/swiftui/entry().json`
- `https://developer.apple.com/documentation/swiftui/transactionkey` → `https://developer.apple.com/tutorials/data/documentation/swiftui/transactionkey.json`
- `https://developer.apple.com/documentation/swiftui/view/contenttransition(_:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/contenttransition(_:).json`
- `https://developer.apple.com/documentation/swiftui/environmentvalues/contenttransition` → `https://developer.apple.com/tutorials/data/documentation/swiftui/environmentvalues/contenttransition.json`
- `https://developer.apple.com/documentation/swiftui/environmentvalues/contenttransitionaddsdrawinggroup` → `https://developer.apple.com/tutorials/data/documentation/swiftui/environmentvalues/contenttransitionaddsdrawinggroup.json`
- `https://developer.apple.com/documentation/swiftui/placeholdercontentview` → `https://developer.apple.com/tutorials/data/documentation/swiftui/placeholdercontentview.json`

## keyframe-and-phase-animators.md

- `https://developer.apple.com/documentation/swiftui/phaseanimator` → `https://developer.apple.com/tutorials/data/documentation/swiftui/phaseanimator.json`
- `https://developer.apple.com/documentation/swiftui/keyframeanimator` → `https://developer.apple.com/tutorials/data/documentation/swiftui/keyframeanimator.json`
- `https://developer.apple.com/documentation/swiftui/keyframetrack` → `https://developer.apple.com/tutorials/data/documentation/swiftui/keyframetrack.json`
- `https://developer.apple.com/documentation/swiftui/timelineview` → `https://developer.apple.com/tutorials/data/documentation/swiftui/timelineview.json`

Children of `swiftui/animations` filed under this reference ("Creating
phase-based animation", "Creating keyframe-based animation", and "Updating a view
on a schedule" `topicSections`, minus the excluded watchOS article noted above):

- `https://developer.apple.com/documentation/swiftui/controlling-the-timing-and-movements-of-your-animations` → `https://developer.apple.com/tutorials/data/documentation/swiftui/controlling-the-timing-and-movements-of-your-animations.json`
- `https://developer.apple.com/documentation/swiftui/view/phaseanimator(_:content:animation:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/phaseanimator(_:content:animation:).json`
- `https://developer.apple.com/documentation/swiftui/view/phaseanimator(_:trigger:content:animation:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/phaseanimator(_:trigger:content:animation:).json`
- `https://developer.apple.com/documentation/swiftui/view/keyframeanimator(initialvalue:repeating:content:keyframes:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/keyframeanimator(initialvalue:repeating:content:keyframes:).json`
- `https://developer.apple.com/documentation/swiftui/view/keyframeanimator(initialvalue:trigger:content:keyframes:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/keyframeanimator(initialvalue:trigger:content:keyframes:).json`
- `https://developer.apple.com/documentation/swiftui/keyframes` → `https://developer.apple.com/tutorials/data/documentation/swiftui/keyframes.json`
- `https://developer.apple.com/documentation/swiftui/keyframetimeline` → `https://developer.apple.com/tutorials/data/documentation/swiftui/keyframetimeline.json`
- `https://developer.apple.com/documentation/swiftui/keyframetrackcontentbuilder` → `https://developer.apple.com/tutorials/data/documentation/swiftui/keyframetrackcontentbuilder.json`
- `https://developer.apple.com/documentation/swiftui/keyframesbuilder` → `https://developer.apple.com/tutorials/data/documentation/swiftui/keyframesbuilder.json`
- `https://developer.apple.com/documentation/swiftui/keyframetrackcontent` → `https://developer.apple.com/tutorials/data/documentation/swiftui/keyframetrackcontent.json`
- `https://developer.apple.com/documentation/swiftui/cubickeyframe` → `https://developer.apple.com/tutorials/data/documentation/swiftui/cubickeyframe.json`
- `https://developer.apple.com/documentation/swiftui/linearkeyframe` → `https://developer.apple.com/tutorials/data/documentation/swiftui/linearkeyframe.json`
- `https://developer.apple.com/documentation/swiftui/movekeyframe` → `https://developer.apple.com/tutorials/data/documentation/swiftui/movekeyframe.json`
- `https://developer.apple.com/documentation/swiftui/springkeyframe` → `https://developer.apple.com/tutorials/data/documentation/swiftui/springkeyframe.json`
- `https://developer.apple.com/documentation/swiftui/timelineschedule` → `https://developer.apple.com/tutorials/data/documentation/swiftui/timelineschedule.json`
- `https://developer.apple.com/documentation/swiftui/timelineviewdefaultcontext` → `https://developer.apple.com/tutorials/data/documentation/swiftui/timelineviewdefaultcontext.json`

## transitions-and-matched-geometry.md

- `https://developer.apple.com/documentation/swiftui/anytransition` → `https://developer.apple.com/tutorials/data/documentation/swiftui/anytransition.json`
- `https://developer.apple.com/documentation/swiftui/transition` → `https://developer.apple.com/tutorials/data/documentation/swiftui/transition.json`
- `https://developer.apple.com/documentation/swiftui/view/matchedgeometryeffect(id:in:properties:anchor:issource:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/matchedgeometryeffect(id:in:properties:anchor:issource:).json`
- `https://developer.apple.com/documentation/swiftui/navigationtransition` → `https://developer.apple.com/tutorials/data/documentation/swiftui/navigationtransition.json`
- `https://developer.apple.com/documentation/swiftui/view/navigationtransition(_:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/navigationtransition(_:).json`
- `https://developer.apple.com/documentation/swiftui/view/matchedtransitionsource(id:in:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/matchedtransitionsource(id:in:).json`

Children of `swiftui/animations` filed under this reference ("Synchronizing
geometries", the transition-taxonomy part of "Defining transitions" excluding the
content-transition entries filed above, "Defining matched transitions", and
"Defining navigation transitions" `topicSections`):

- `https://developer.apple.com/documentation/swiftui/matchedgeometryproperties` → `https://developer.apple.com/tutorials/data/documentation/swiftui/matchedgeometryproperties.json`
- `https://developer.apple.com/documentation/swiftui/geometryeffect` → `https://developer.apple.com/tutorials/data/documentation/swiftui/geometryeffect.json`
- `https://developer.apple.com/documentation/swiftui/namespace` → `https://developer.apple.com/tutorials/data/documentation/swiftui/namespace.json`
- `https://developer.apple.com/documentation/swiftui/view/geometrygroup()` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/geometrygroup().json`
- `https://developer.apple.com/documentation/swiftui/view/transition(_:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/transition(_:).json`
- `https://developer.apple.com/documentation/swiftui/transitionproperties` → `https://developer.apple.com/tutorials/data/documentation/swiftui/transitionproperties.json`
- `https://developer.apple.com/documentation/swiftui/transitionphase` → `https://developer.apple.com/tutorials/data/documentation/swiftui/transitionphase.json`
- `https://developer.apple.com/documentation/swiftui/asymmetrictransition` → `https://developer.apple.com/tutorials/data/documentation/swiftui/asymmetrictransition.json`
- `https://developer.apple.com/documentation/swiftui/view/matchedtransitionsource(id:in:configuration:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/matchedtransitionsource(id:in:configuration:).json`
- `https://developer.apple.com/documentation/swiftui/matchedtransitionsourceconfiguration` → `https://developer.apple.com/tutorials/data/documentation/swiftui/matchedtransitionsourceconfiguration.json`
- `https://developer.apple.com/documentation/swiftui/emptymatchedtransitionsourceconfiguration` → `https://developer.apple.com/tutorials/data/documentation/swiftui/emptymatchedtransitionsourceconfiguration.json`
- `https://developer.apple.com/documentation/swiftui/anynavigationtransition` → `https://developer.apple.com/tutorials/data/documentation/swiftui/anynavigationtransition.json`
- `https://developer.apple.com/documentation/swiftui/crossfadenavigationtransition` → `https://developer.apple.com/tutorials/data/documentation/swiftui/crossfadenavigationtransition.json`

## scroll-and-visual-effects.md

- `https://developer.apple.com/documentation/swiftui/view/scrolltransition(_:axis:transition:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/scrolltransition(_:axis:transition:).json`
- `https://developer.apple.com/documentation/swiftui/scrolltransitionconfiguration` → `https://developer.apple.com/tutorials/data/documentation/swiftui/scrolltransitionconfiguration.json`
- `https://developer.apple.com/documentation/swiftui/view/visualeffect(_:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/visualeffect(_:).json`
- `https://developer.apple.com/documentation/swiftui/view/coloreffect(_:isenabled:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/coloreffect(_:isenabled:).json`
- `https://developer.apple.com/documentation/swiftui/view/layereffect(_:maxsampleoffset:isenabled:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/layereffect(_:maxsampleoffset:isenabled:).json`
- `https://developer.apple.com/documentation/swiftui/view/distortioneffect(_:maxsampleoffset:isenabled:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/distortioneffect(_:maxsampleoffset:isenabled:).json`
- `https://developer.apple.com/documentation/swiftui/shader` → `https://developer.apple.com/tutorials/data/documentation/swiftui/shader.json`
- `https://developer.apple.com/documentation/swiftui/shaderlibrary` → `https://developer.apple.com/tutorials/data/documentation/swiftui/shaderlibrary.json`

None of these eight seeds is a DocC index (`role: symbol` confirmed for all eight
via the fetched JSON's `metadata.role`), and `swiftui/animations`'s own
`topicSections` contain no scroll-transition or Metal-shader-effect entries — that
API surface lives outside the `animations` collection group. No enumeration
performed for this reference; no additional children to add.

## Cross-map note: judgment lives elsewhere

Judgment ranges for animation taste (when to animate, easing/duration choices,
spring-vs-eased-curve calls, keyframe/Bézier restraint) live in
`pipeline/maps/apple-design-books.md`'s Phase 2 entries for
`ios-animations-by-tutorials-v7-0-0.md`, already distilled into
`plugin/skills/apple-design/references/animation-taste.md`. Distillers writing the
four reference files above read `animation-taste.md` itself for tone and
boundary — they do not re-distill the underlying book; this map's endpoints are
strictly for API mechanics (what the types/modifiers do, their signatures and
parameters), not design judgment.
