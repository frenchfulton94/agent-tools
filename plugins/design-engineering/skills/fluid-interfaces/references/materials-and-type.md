# Materials, typography, and principles

The non-motion half of Apple's design language: translucency and depth,
typography, the accessibility preferences beyond reduced motion, and the eight
principles the rest of it serves.

## Contents

- [Materials and depth](#materials-and-depth)
- [Dim to focus, separate to keep flow](#dim-to-focus-separate-to-keep-flow)
- [Vibrancy and scroll edges](#vibrancy-and-scroll-edges)
- [Typography](#typography)
- [Accessibility preferences](#accessibility-preferences)
- [The eight design principles](#the-eight-design-principles)
- [Tactical rules that serve them](#tactical-rules-that-serve-them)
- [Process](#process)

## Materials and depth

Apple uses translucent materials as a floating functional layer that gives
structure without stealing focus. On the web, approximate with
`backdrop-filter`.

```css
.toolbar {
	background: rgb(255 255 255 / 0.6);
	backdrop-filter: blur(20px) saturate(180%);
	border-top: 1px solid rgb(255 255 255 / 0.4); /* bright edge = light on the material */
}
```

- **Build nav bars, toolbars, and sheets as translucent layers** with content
  scrolling underneath, rather than opaque bars consuming a fixed strip.
- **Material weight encodes hierarchy.** Darker, heavier materials separate
  structural regions such as sidebars; lighter materials draw attention to
  interactive elements. Never stack a light translucent surface on another —
  legibility collapses.
- **Bigger surfaces read as thicker**: stronger blur and a deeper shadow than
  small chips. Consider context-aware shadow — heavier over busy or text-dense
  content, lighter over a plain background.
- **Materialise, do not fade.** For a glass surface, animate blur radius and
  scale together on enter and exit, so it reads as a real material arriving
  rather than an opacity fade.

Keep blur values honest about cost: `backdrop-filter` is expensive, especially
in Safari, and expensive on every frame it is composited — not only while
animating.

## Dim to focus, separate to keep flow

A modal task pairs its surface with a dimming scrim and pushes the background
back and down. A parallel, non-blocking panel uses translucency and offset
*without* a scrim, so the flow is not broken. For stacked sheets, progressively
dim and push back each parent layer.

The choice of scrim is therefore a statement about whether the user can keep
working. Adding one to a non-blocking panel says the wrong thing.

## Vibrancy and scroll edges

**Vibrancy keeps text legible over changing backgrounds.** Over a blurred or
translucent surface, do not use flat grey text — use higher contrast, a slightly
heavier weight, and a small letter-spacing bump. Put colour on a solid layer,
never on the translucent foreground.

**Scroll edge effects, not hard dividers.** Instead of a 1px border under a
sticky header, fade a small blur or gradient mask where content meets floating
chrome, and only where floating UI actually overlaps content.

```css
.scroll-edge {
	mask-image: linear-gradient(to bottom, transparent, black 24px);
}
```

## Typography

Apple designs type to change shape with size, and the same discipline applies on
the web. From *The Details of UI Typography*.

- **Tracking is size-specific — never one value for all sizes.** Large display
  text wants *negative* tracking, since letters read too far apart as they grow;
  small text wants slightly *positive* tracking for legibility. A single
  `letter-spacing` is wrong somewhere. Tighten headings, leave body near `0`.
- **Leading tracks size inversely.** Tight on large headings, looser on body
  copy. Increase it for scripts with tall ascenders and descenders; tighten it
  for dense, information-heavy UI.
- **Build hierarchy from weight, size, and leading as a set**, not size alone.
  Weight adds presence without taking more space.
- **Respect the user's text-size setting.** Scale layout *with* the text —
  spacing in `rem` or `em`, not fixed pixels — so a larger font does not break
  the layout.
- **Default to the platform's system font** before a custom face. It already
  ships optical sizing, tracking tables, and legibility tuning. Override only
  with a reason.

```css
:root {
	font: 100%/1.5 system-ui, sans-serif;
}

.display {
	font-size: clamp(2rem, 5vw, 4rem);
	line-height: 1.05;       /* tight leading for large text */
	letter-spacing: -0.02em; /* negative tracking as it grows */
	font-optical-sizing: auto;
}
```

In a Tailwind project, express these as `@theme` tokens so the tracking and
leading travel with the size step rather than being reapplied per heading.

## Accessibility preferences

Reduced motion is one of three independent signals. Handle all three.

```css
@media (prefers-reduced-motion: reduce) {
	.sheet { transition: opacity 200ms ease; transform: none; }
}

@media (prefers-reduced-transparency: reduce) {
	.toolbar { background: Canvas; backdrop-filter: none; }
}

@media (prefers-contrast: more) {
	.toolbar { background: Canvas; border: 1px solid CanvasText; }
}
```

- **`prefers-reduced-motion: reduce`** — replace slides, springs, and parallax
  with short opacity cross-fades or static transitions. Drop elastic and
  overshoot. Keep opacity and colour changes that aid comprehension. On Svelte
  transitions this media query does nothing; branch on
  `prefersReducedMotion.current` in JavaScript instead.
- **`prefers-reduced-transparency: reduce`** — make translucent surfaces solid:
  raise the background opacity, drop the blur.
- **`prefers-contrast: more`** — near-solid backgrounds with a defined,
  contrasting border.

Also avoid full-viewport moving backgrounds, slow looping oscillations near
0.2 Hz, and abrupt brightness jumps — ease dark and light theme changes. Make
large moving objects semi-transparent while they travel, and fade big surfaces
out during a large reposition and back in once settled.

## The eight design principles

From *Principles of Great Design*. Use these as the names you reason with.

1. **Purpose.** Make with intention; decide what *not* to build. Every feature
   asks for the user's time, attention, and trust — spend that budget only where
   it pays off.
2. **Agency.** Keep people in control: offer choices, do not force one path.
   Back it with forgiveness — easy undo for slips, and a confirmation dialog
   only for genuinely destructive, irreversible actions. Overusing confirmation
   trains people to click through it.
3. **Responsibility.** Act in the user's interest. Ask for permissions at the
   right moment, only for what is needed, transparently. Anticipate misuse and
   harm — an allergy-aware recipe app must not suggest a harmful ingredient. Add
   previews, confirmations, and disclaimers; cut a feature whose risk outweighs
   its value.
4. **Familiarity.** Build on what people know. Use metaphors that are neither
   too literal nor too abstract, and honour their physics. Things that look the
   same behave the same and live in the same place, so people can predict what
   happens next. Break a familiar pattern only if you can prove it is better,
   then test it.
5. **Flexibility.** Design for different contexts, devices, and the full range
   of abilities. Adapt to the platform — a phone is quick touch, a desktop is
   deep workflows with a precise pointer — and to the situation. Where no single
   layout fits everyone, let people personalise.
6. **Simplicity, not minimalism.** Strip the unnecessary so the core purpose
   shines; burying everything in one place looks minimal but is not simple. Be
   concise and clear, use hierarchy so the most important thing is the most
   obvious, and show the common path first with advanced options one level
   deeper. Sometimes *adding* context simplifies — a scrubber that shows time
   remaining.
7. **Craft.** Uncompromising attention to detail builds trust. Nothing is
   random: every spacing, timing, and alignment value is a choice you can
   defend. Jittery scroll, misaligned icons, and layouts that break on rotation
   read as carelessness.
8. **Delight.** The result of getting the other seven right, not confetti tacked
   on top. Decide the emotion you want people to feel and reinforce it in every
   decision.

## Tactical rules that serve them

- **Feedback comes in four kinds:** status, completion, warning, error. Confirm
  meaningful actions, expose ongoing status, warn before problems, and validate
  inline rather than on submit.
- **Wayfinding.** Every screen answers: where am I, where can I go, what is
  there, how do I get out. Never trap the user.
- **Grouping and mapping.** Proximity implies relationship. Place a control near
  what it affects, and arrange controls to mirror what they change. If you need
  a label to explain a control, the mapping is weak.
- **Direct, specific labels beat safe generic ones.** Name nav items for their
  contents — "Progress", "Library" — not vague umbrellas like "Home".
  Specificity creates predictability.

## Process

- **Prototype interactively.** An interactive demo is worth a million static
  designs. You discover the interface by building and playing with it, and a
  working prototype sets a concrete bar that prevents a mediocre final
  implementation.
- **Design interaction and visuals together.** You should not be able to tell
  where one ends and the other begins. Motion is not a layer added after the
  pixels.
- **Test with real people in real context,** and review motion with fresh eyes —
  play it in slow motion or frame by frame to catch what is invisible at full
  speed.
