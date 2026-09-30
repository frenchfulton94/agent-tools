> verified: 2026-08 against https://developer.apple.com/design/human-interface-guidelines/accessibility, https://developer.apple.com/design/human-interface-guidelines/voiceover, https://developer.apple.com/design/human-interface-guidelines/buttons, https://developer.apple.com/design/human-interface-guidelines/inclusion, https://developer.apple.com/design/human-interface-guidelines/motion; re-checked 2026-09 (Phase 9: snippets reframed, accentColor → tint)
> sources: live HIG (DocC JSON); SwiftUI by Tutorials v5.0.0 (Kodeco), ch. 12 (Accessibility)
> note: the map assigns Reduce Motion to the `motion` endpoint, but that page doesn't cover the Reduce Motion setting — the obligation text here is sourced from the Accessibility page; only the visionOS motion-comfort material is motion.json-sourced. General motion taste lives in `animation-taste.md`. All SwiftUI/UIKit API symbols named below were individually confirmed against live Apple documentation JSON (exact name, signature, and platform availability) before this file was committed.

# Accessibility

Accessibility here means engineering obligations, not empathy exercises: SwiftUI ships most of the work for free (labels, traits, reading order all derive from view structure), so a review should focus on where that default breaks down — custom controls, images, decorative content, and settings-driven adaptation (Dynamic Type, Reduce Motion, Increase Contrast, VoiceOver). An interface only counts as accessible when it stays usable without sight, without fine motor control, and without hearing (HIG: Accessibility, https://developer.apple.com/design/human-interface-guidelines/accessibility).

## SwiftUI's accessibility-by-default baseline

Standard SwiftUI views (`Text`, `Button`, `Toggle`, `Slider`, `List`, …) automatically become accessibility elements: they get a default label (usually their visible text), a default value, a trait set appropriate to the control type, and a reading order that matches the view tree's declared order. This means most accessibility work is *correction*, not construction — you're fixing cases where the generated label is generic, jargon-heavy, redundant, or ordered wrong, not building accessibility support from scratch (SwiftUI by Tutorials, ch. 12).

Reach for the SwiftUI accessibility modifiers when:
- The visible content is symbols/abbreviations/numbers that mean nothing spoken aloud (e.g. a raw `"R 127"` string, a bare percentage with no unit).
- A custom-built control (not a standard `Button`/`Toggle`/etc.) has no default label, value, or trait at all.
- Adjacent views are visually one unit (an icon + its caption, a stat + its label) but would otherwise be read as separate stops.
- The visual/reading order and the logical order diverge (e.g. a floating badge that's visually first but logically secondary).

## VoiceOver: labels, values, hints, traits

Every element VoiceOver announces is built from up to four attributes — label, trait, value, hint — and each has a distinct job. Conflating them (e.g. baking "button" into the label) produces redundant or garbled speech, since traits are announced separately and automatically (HIG: VoiceOver, https://developer.apple.com/design/human-interface-guidelines/voiceover).

- `accessibilityLabel(_:)` — what the element *is*. Write it as if describing the control's purpose to someone who can't see it; never include the trait ("button", "switch") in the string, VoiceOver appends that itself.
- `accessibilityValue(_:)` — the element's *current state*, when that state isn't obvious from the label (a slider's numeric value with units, a toggle's semantic state beyond on/off). Recompute it whenever the underlying value changes — SwiftUI's diffing handles the re-announcement.
- `accessibilityHint(_:)` — optional, read only if the user pauses after the label. Use it to describe the *result* of interacting with the element, not to repeat the label.
- `accessibilityAddTraits(_:)` / `accessibilityRemoveTraits(_:)` — correct the semantic role of custom controls. A tappable `HStack` styled to look like a button needs `.isButton` added explicitly; a decorative element misidentified as interactive needs traits stripped.
- `accessibilityHidden(true)` — remove purely decorative content (background art, redundant glyphs beside already-labeled text) from the accessibility tree. Apply it *after* view-shaping modifiers like `.resizable()` on an `Image`, since some modifiers return a different view type that doesn't carry the accessibility modifier forward the same way.

```swift
struct ColorGuessRow: View {
    @State private var red = 0.5

    var body: some View {
        VStack {
            Slider(value: $red)
                .tint(.red)
                .accessibilityValue("red \(Int(red * 255))")

            Image("decorative-background")
                .resizable()
                .accessibilityHidden(true)
        }
    }
}
```

Never trust an image's *visual* recognizability as a substitute for a label — describe what the image conveys in context, not what it depicts in isolation, and skip describing images whose content is already captured by adjacent visible text (HIG: VoiceOver, https://developer.apple.com/design/human-interface-guidelines/voiceover).

## Navigation order, grouping, and rotor

VoiceOver reads elements in document/declaration order by default, which usually matches visual top-to-bottom, leading-to-trailing order in the user's active language — but visual proximity and grouping that's obvious to a sighted user (a caption under its image, a label beside its icon) is invisible to VoiceOver unless you say so explicitly (HIG: VoiceOver, https://developer.apple.com/design/human-interface-guidelines/voiceover).

- `accessibilityElement(children: .combine)` — merge a container's children into a single spoken unit when they're one semantic idea (a stat value + its unit, an image + its caption). Combining is lossy: any per-child modifiers (like a nested button's tap target) stop working once combined, so don't combine interactive children into a container that also needs to stay tappable individually.
- `accessibilitySortPriority(_:)` — override reading order for elements that are visually distant but logically should be read first (e.g. surfacing the primary interactive control before a long instructional paragraph above it). Higher values are read first; unset elements default to priority 0.
- Give every screen/section a real title/heading rather than relying on the first line of body text — VoiceOver users jump between headings as their primary orientation strategy, the same way sighted users scan for a page title.
- When content changes without a full navigation event (a live score update, a validation error appearing), post an accessibility notification so VoiceOver announces the change rather than leaving the user with a stale mental model — on iOS/macOS 17+/14+, `AccessibilityNotification.Announcement("…").post()` (from the `Accessibility` framework, not `SwiftUI` itself) is the modern path; for earlier deployment targets or UIKit code, use `UIAccessibility.post(notification:argument:)`.
- Custom rotor content (headings, landmarks, or app-specific content types) via `AccessibilityRotorEntry` and the `.accessibilityRotor(_:entries:)` view modifier (SwiftUI, iOS/macOS 16+) is worth adding to any screen with a long scrollable list — it's the VoiceOver equivalent of a sighted user visually skimming for a landmark, and skipping it forces users into linear swipe-by-swipe navigation.

## Reduce Motion

When the system Reduce Motion setting is on, an app's obligation is specific and narrow — this is the accessibility contract, not general motion taste (see `animation-taste.md` for timing/purposefulness judgment that applies regardless of this setting). Under Reduce Motion, reduce or eliminate: automatic/repetitive animations, zooming, scaling, and peripheral motion (HIG: Accessibility, https://developer.apple.com/design/human-interface-guidelines/accessibility). Concrete techniques:

- Tighten animation springs to cut bounce/overshoot rather than removing motion outright where some feedback is still needed.
- Track animations directly with the person's own gesture input rather than auto-playing a canned trajectory.
- Never animate depth/z-axis layer changes.
- Replace x/y/z-axis transitions (slides, pushes) with cross-fades.
- Avoid animating into or out of blur effects.

In SwiftUI, gate custom animations on the environment value rather than assuming the system disables everything for you — standard system transitions adapt automatically, but any custom `withAnimation`/`Animation` you author does not:

```swift
struct StatusGlyph: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        if reduceMotion {
            Image(systemName: "circle.fill")
        } else {
            Image(systemName: "circle.fill")
                .symbolEffect(.pulse)
        }
    }
}
```

A looping/auto-playing animation (a promo carousel, a decorative background loop) is the classic miss — it's exactly the "automatic and repetitive" case the setting targets, and it's easy to forget because it has no explicit trigger to gate.

visionOS carries an added comfort obligation beyond Reduce Motion itself: because immersive interfaces are more prone to inducing motion sickness, keep interface elements within the person's field of view, avoid peripheral-vision motion, and avoid letting the whole virtual world rotate or move without the person's control — this is general visionOS motion-comfort guidance, not gated on the Reduce Motion setting (HIG: Motion, https://developer.apple.com/design/human-interface-guidelines/motion; cross-reference `animation-taste.md` for the rest of this page's non-accessibility motion judgment).

## Dynamic Type and contrast

Scaling mechanics and numeric contrast minimums live in `hig-foundations.md` § Typography and Dynamic Type and § Color — don't re-derive them here. What's specific to accessibility review:

- Dynamic Type isn't optional-nice-to-have: HIG's baseline expectation is that text/icon size can enlarge by at least 200% (140% on watchOS) before you're out of compliance, whether via system Dynamic Type or an equivalent custom mechanism (HIG: Accessibility, https://developer.apple.com/design/human-interface-guidelines/accessibility). Test at the largest accessibility category, not just the largest *standard* category — the two behave very differently for constrained layouts (see hig-foundations.md § Typography and Dynamic Type for the structural fixes: stacking, column reduction, truncation rules).
- Contrast has a settings-driven escape hatch you must actually implement, not just meet by default: if your default palette doesn't clear the minimums, you must provide a higher-contrast variant when the system Increase Contrast setting is on (via the `colorSchemeContrast` environment value) — check both light and dark appearance under that setting, since Increase Contrast in Dark Mode can paradoxically *reduce* effective contrast for some color pairs (see hig-foundations.md § Color).
- Preferring system semantic colors is the accessibility argument, not just the maintenance one: they already carry their own accessible variants that respond to Increase Contrast automatically, which a hand-picked custom palette does not unless you build the variant yourself.
- Never rely on color alone to convey state (error vs. success, selected vs. unselected) — pair it with shape, icon, or text so it survives color blindness and the Differentiate Without Color setting (`accessibilityDifferentiateWithoutColor` environment value).

## Tap targets and motor accessibility

A control's hit region — not its visible glyph size — must be at least 44×44 pt so it's reliably selectable by fingertip or pointer (HIG: Buttons, https://developer.apple.com/design/human-interface-guidelines/buttons). This is a floor, not a target size to design toward visually; pad the tappable area beyond a small glyph rather than enlarging the glyph itself.

- Spacing between controls matters as much as their individual size: roughly 12 pt of padding around bezeled elements and roughly 24 pt around bezel-less elements reduces mis-taps (HIG: Accessibility, https://developer.apple.com/design/human-interface-guidelines/accessibility).
- Prefer the simplest available gesture for frequent interactions; avoid custom multi-finger/multi-hand gestures as the *only* path to core functionality — always provide a single-tap or button alternative alongside a custom gesture (e.g. an explicit dismiss button alongside swipe-to-dismiss).
- Full Keyboard Access and Switch Control are first-class input modes, not edge cases: never override system-defined keyboard shortcuts, and verify custom interactive elements are reachable and properly labeled under both — a custom control with no accessibility label is invisible to Switch Control just as it is to VoiceOver.

## Cognitive accessibility

- Prefer system-standard gestures and interactions over custom ones people must learn — every custom interaction pattern is a tax on people who process information more slowly or use assistive tech that needs more time to traverse the UI.
- Avoid time-boxed UI that auto-dismisses on a timer (toasts, transient banners with no persistent access) for anything conveying information someone might need more time to process; prefer explicit dismissal.
- Never autoplay audio/video without accessible, discoverable stop/start controls, and respect the Dim Flashing Lights setting for any video content that might contain rapid flashing (HIG: Accessibility, https://developer.apple.com/design/human-interface-guidelines/accessibility).
- If your app targets iOS/iPadOS and reasonably serves people with cognitive disabilities, design for Assistive Access compatibility: identify and preserve only core functionality, break multistep flows into one interaction per screen, and require a second, explicit confirmation for any destructive/hard-to-recover action (HIG: Accessibility, https://developer.apple.com/design/human-interface-guidelines/accessibility).

## Hearing accessibility

Never communicate essential information through audio alone. Choose the right text-based channel for the content, not the first one that comes to mind (HIG: Accessibility, https://developer.apple.com/design/human-interface-guidelines/accessibility):
- **Captions** for text synced live to audio/video (cutscenes, clips).
- **Subtitles** for translated/localized on-screen dialogue.
- **Audio descriptions** — spoken narration of visually-only information, placed in natural audio pauses.
- **Transcripts** for a complete, reviewable text record — best for long-form audio (podcasts) where people want to skim or search.

Pair any audio-cue-only feedback (success chime, error tone) with matching haptics so it lands for people who can't hear it or have muted the device. In games and spatial apps specifically, back up audio-directed attention (off-screen cues) with a visual indicator too — audio alone can't guide someone who's deaf toward off-screen action.

## Inclusive language and imagery

Distinct from technical accessibility (assistive tech support), but part of the same review lens: content and copy that assumes a narrow audience excludes people just as effectively as a missing VoiceOver label (HIG: Inclusion, https://developer.apple.com/design/human-interface-guidelines/inclusion).

- Address people directly as "you"/"your" in copy; avoid the distancing "the user"/"the player," and avoid "we"/"our" phrasing that implies a personal relationship the software doesn't have.
- Cut colloquialisms and unexplained jargon — both fail to translate and can carry exclusionary history invisible to the author.
- Default to gender-neutral phrasing and nongendered imagery/glyphs (SF Symbols' figure/person symbols) unless gender is functionally required; when it is, offer nonbinary and self-identify options rather than a binary picker.
- When depicting people, vary race, body type, age, and ability rather than defaulting to one demographic, and avoid stereotype-coded pairings (e.g. only male doctors, only female nurses).
- Use people-first phrasing for disability ("a person who is blind," not a noun that reduces someone to the condition).

## Testing methodology

- The Xcode Accessibility Inspector approximates VoiceOver but is not a substitute for it — always verify on a physical device before calling accessibility work done; the Inspector can misrepresent reading order, combined-element behavior, and gesture interaction (SwiftUI by Tutorials, ch. 12).
- Use Xcode's Environment Overrides in the debug toolbar to quickly cycle Dynamic Type size, Increase Contrast, Bold Text, On/Off Labels, and Button Shapes without leaving your dev loop — but Reduce Motion, Grayscale, and Smart Invert must be checked with the *actual* device setting; they don't reliably reflect through the override tool (SwiftUI by Tutorials, ch. 12).
- Turn on the VoiceOver screen curtain (triple-tap with three fingers) and attempt a full task blind — this is the closest a sighted developer gets to experiencing what a VoiceOver user actually encounters, and it surfaces ordering/labeling problems that reading code never will.
- Check custom elements against the full accessibility environment surface, not just VoiceOver: `dynamicTypeSize`, `accessibilityReduceMotion`, `accessibilityReduceTransparency`, `accessibilityInvertColors`, `colorSchemeContrast`, `legibilityWeight` (Bold Text), `accessibilityDifferentiateWithoutColor` are all independently togglable — a screen can pass a VoiceOver pass and still fail Bold Text or Reduce Transparency.
- VoiceOver, Voice Control, and Switch Control are each independently detectable at runtime (`UIAccessibility.isVoiceOverRunning`, `isSwitchControlRunning`, etc. on UIKit-backed platforms) — don't assume one implies the others if your logic needs to branch on which is active.

## Screen-review checklist

Apply mechanically to any screen/view under review:

1. **Dynamic Type** — at the largest accessibility text size (not just largest standard size), does the layout survive without truncation, overlap, or clipped controls? (see hig-foundations.md § Typography and Dynamic Type for the structural fix patterns)
2. **VoiceOver labels/traits** — does every interactive and informational element have a non-generic accessibility label; are purely decorative images/glyphs marked `accessibilityHidden`; do custom (non-standard) controls carry the correct trait (e.g. `.isButton`) so they announce their role; does the VoiceOver reading order match the visual/logical grouping (verify with the Accessibility Inspector or on-device, not by code inspection alone)?
3. **Tap targets** — does every tappable control have a hit region of at least 44×44 pt (60×60 pt on visionOS), including controls whose visible glyph is smaller than that?
4. **Contrast** — does every foreground/background text and icon pairing meet the numeric minimums (see hig-foundations.md § Color), checked in both light and dark appearance, and does the screen provide a compliant alternative when Increase Contrast is on?
5. **Reduce Motion** — with Reduce Motion enabled, does every custom (non-system) animation on this screen degrade to a reduced/static equivalent — no automatic looping motion, no z-axis/depth animation, no un-gated custom transitions?
6. **Keyboard/pointer support (macOS/iPadOS)** — is every interactive element reachable via Tab/Full Keyboard Access in a sensible order; is there a visibly distinct focus indicator when an element has keyboard focus; does hovering a control with a pointer produce a visible hover state? (Verify what's checkable from code/layout alone — full confirmation needs an actual keyboard/pointer pass on device.)
