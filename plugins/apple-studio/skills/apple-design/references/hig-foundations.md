> verified: 2026-08 against https://developer.apple.com/design/human-interface-guidelines/layout, https://developer.apple.com/design/human-interface-guidelines/typography, https://developer.apple.com/design/human-interface-guidelines/color, https://developer.apple.com/design/human-interface-guidelines/materials, https://developer.apple.com/design/human-interface-guidelines/dark-mode, https://developer.apple.com/design/human-interface-guidelines/icons, https://developer.apple.com/design/human-interface-guidelines/sf-symbols, https://developer.apple.com/design/human-interface-guidelines/images
> sources: live HIG (DocC JSON)

# HIG Foundations

## Layout

Prefer system layout guides and safe areas over custom geometry — safe areas exist specifically to
dodge device features you can't predict per-model (Dynamic Island, camera housings, rounded corners),
and hand-rolled insets rot the moment Apple ships new hardware dimensions.

- When content doesn't span the full window (e.g. a detail view beside a sidebar/inspector), don't
  fake the "content behind controls" look by manually painting background under the chrome — use a
  background-extension effect (`View.backgroundExtensionEffect()`) so content visually continues
  under the Liquid Glass control layer without you owning that math.
- Custom layout is justified when the system's default reading-order stacking actively fights your
  hierarchy — but even then, keep the *judgment* (top/leading = most important, respecting RTL)
  rather than the specific pixel values, since those come from layout guides. Justify custom
  margins/spacing only for grouping semantics (showing relatedness), not just to tighten default
  spacing.
- iPadOS: defer collapsing to a compact layout for as long as the window can still fit the full-width
  version — design full-screen first, treat compact as the fallback, not the default. In split views,
  collapse tertiary columns (inspectors) before primary navigation as the window narrows.
- macOS: never place must-see controls or information at the bottom edge of a window — see
  `platform-idioms.md` § Windows and multitasking behavior for why (window dragging) and the full rule.
- When display context changes (aspect ratio, external display, z-axis movement in visionOS), scale
  artwork rather than changing its aspect ratio — cropping/letterboxing beats distortion.

(HIG: Layout, https://developer.apple.com/design/human-interface-guidelines/layout)

## Typography and Dynamic Type

Dynamic Type support that's "on" but naïve still breaks layouts. The real work is deciding what
*doesn't* scale.

- Not all content is equally important: scale primary reading content but pin secondary/transient
  elements (tab bar titles, timestamps, in-game hit-damage numbers) at a fixed size — growing
  everything uniformly just relocates the crowding problem.
- At large accessibility sizes, horizontally-constrained inline layouts (glyph + label + timestamp in
  a row) crowd and truncate. Fix this structurally, not cosmetically: switch to a stacked layout
  (secondary items below/above the text), and reduce multicolumn text to fewer columns as size
  increases.
- Truncation is a last resort, not a default: at the largest accessibility size, aim to expose as
  much text as you do at the largest *standard* size. Only truncate inside scrollable regions if
  there's a separate detail view to read the rest — never truncate a value with no escape hatch.
- Leading is a layout lever, not just an aesthetic one: loosen it for long-form/wide-column reading,
  tighten it to fit multi-line text in constrained containers like list rows — but never tighten past
  three lines, where it just hurts readability without buying room.
- Meaningful (non-decorative) interface icons must grow with Dynamic Type too — SF Symbols do this
  automatically; custom vector icons need you to size them off the same text-style metric.
- Keep hierarchy position stable across font sizes — primary elements stay near the top of the view
  even at the largest accessibility size, so people don't lose their anchor as things reflow.
- Avoid Ultralight/Thin/Light system font weights generally; if you must use a thin custom font,
  compensate with larger sizes than the platform minimums — thin weights are a legibility tax that
  worsens as point size drops.

(HIG: Typography, https://developer.apple.com/design/human-interface-guidelines/typography)

Use `Font.Design` constants (`.default`, `.serif`, etc.) to reach system fonts rather than embedding
San Francisco or New York as bundled files — the system-font route keeps you on the variable-font
pipeline (dynamic optical sizing, correct tracking at every point size) for free:

```swift
Text("Balance").font(.system(.title, design: .serif))  // New York, not an embedded font
```

Custom fonts are a commitment, not a drop-in: they don't get Dynamic Type or Bold Text accessibility
support automatically the way system fonts do — you must explicitly wire both up yourself, and verify
legibility at your custom font's minimum recommended sizes per weight/style before shipping it
anywhere body text appears. (HIG: Typography,
https://developer.apple.com/design/human-interface-guidelines/typography)

## Color

**Default to system semantic colors; only define a custom color when the semantic set genuinely has
no fit for your meaning** (brand accent, a status you own). Semantic colors are named by purpose, not
appearance — never repurpose one for something else (don't use `separator` as a text color, don't use
`secondaryLabel` as a background); the underlying values shift release-to-release and the abuse will
silently break.

- If you do define a custom color, you owe it four variants: light, dark, and an increased-contrast
  variant for each — and you owe this even in a single-appearance-mode app, because Liquid Glass
  adaptivity can still pull from the other mode's value. Budget for this cost before reaching past
  system colors.
- Contrast is a hard number, not a vibe: minimum 4.5:1 for any foreground/background pair; for custom
  combinations, target 7:1, especially at small text sizes — system colors already clear this bar,
  which is the practical argument for using them. Dark Mode has a trap: turning on Increase Contrast
  *in* Dark Mode can sometimes *reduce* effective contrast between dark text and a dark background —
  verify empirically, don't assume the setting always helps. (HIG: Dark Mode,
  https://developer.apple.com/design/human-interface-guidelines/dark-mode)
- Dark Mode colors are not simple photographic negatives of light-mode colors — some invert, some
  don't — so don't derive dark variants programmatically from light ones; author them intentionally
  per the semantic color's purpose. iOS/iPadOS also layer base vs. elevated background colors to
  signal depth (elevated = popovers/sheets/foreground window in multitasking); prefer system
  background colors specifically to keep that distinction legible. (HIG: Dark Mode,
  https://developer.apple.com/design/human-interface-guidelines/dark-mode)
- Liquid Glass color is a scarce resource: apply color to the glass background (not to symbols/text
  on it) to mark a primary action, the way the system tints the Done button — restrict that treatment
  to one control at a time. If your app already has a colorful background or rich content, prefer a
  monochromatic toolbar/tab bar over an accent color that fights for attention; save the brand accent
  for apps with mostly monochromatic content.
- Color space is a legibility/fidelity decision, not a preference: use Display P3 (16 bpc, PNG) for
  photos, video, and status indicators where richer saturation carries meaning. P3 usually degrades
  gracefully on sRGB displays, but two visually-similar P3 colors can become indistinguishable there,
  and P3 gradients can visibly clip — that's the specific case for providing a separate sRGB-tuned
  variant, not a blanket rule. This isn't a distinct SwiftUI API: an asset catalog Named Color (or
  image set) carries a `display-gamut` attribute per appearance, so you add the sRGB variant
  alongside the P3 one in the same set and reference it the normal way (`Color("name")`) — the
  catalog picks the right variant at runtime. (Asset Catalog Format Reference: Named Color,
  https://developer.apple.com/library/archive/documentation/Xcode/Reference/xcode_ref-Asset_Catalog_Format/Named_Color.html)
- macOS: a sidebar icon given a deliberate fixed color is the one exception to the system overriding
  your accent color when someone picks a non-multicolor accent setting — a fixed color there carries
  semantic meaning, not just theming.
- If people can pick colors in your app, route that through the system color picker (`ColorPicker`)
  instead of building a custom one — one of the few places a hand-rolled control is strictly worse
  than the default, since people already have saved colors there shared across apps.

(HIG: Color, https://developer.apple.com/design/human-interface-guidelines/color)

## Materials and Liquid Glass

Liquid Glass belongs to the controls/navigation layer, not the content layer — using it for
content-layer surfaces (app backgrounds, cards) muddles the exact hierarchy it exists to create. The
one carve-out: a transient interactive element in content (a slider or toggle) can pick up a Liquid
Glass appearance momentarily while someone is actively engaging it. Use standard materials, not
Liquid Glass, for content-layer differentiation.

- Choosing between the regular and clear Liquid Glass variants is a legibility call: use regular when
  the background is unpredictable or the control carries meaningful text (alerts, sidebars,
  popovers) — it actively blurs/dims to protect legibility. Use clear only for controls floating over
  intentionally rich media (photo/video) where the background should stay dominant. If you use clear
  over bright content with no built-in dimming layer (e.g. from AVKit playback controls), add a
  ~35%-opacity dark dimming layer yourself, or legibility suffers.
- Pick a standard material by contrast need, not by the color it happens to impart — appearance
  shifts with system settings (Reduce Transparency, Increase Contrast, accent color), so a material
  chosen for "looks good now" breaks under those settings. Thicker/more-opaque materials suit
  text-heavy or fine-detail content needing strong contrast; thinner/more-translucent materials suit
  places where people should keep visual context of what's behind them.
- Custom controls that adopt Liquid Glass should do so sparingly, only on the most important
  functional elements — overusing the effect across many custom controls competes with the
  underlying content it's supposed to foreground.
- visionOS has no Dark Mode setting at all — its `glass` material adapts continuously to the
  luminance of whatever's physically/virtually behind it, so don't force a fixed light/dark
  treatment there. Prefer translucency over opaque fills in visionOS windows generally — opacity
  reads as constricting people's awareness of their physical surroundings, a cost 2D platforms don't
  have.
- macOS: only add transparency to a custom component's background when the component is in a neutral
  (non-colored) state and already has a visible bezel/background — this lets it participate in
  desktop tinting (window backgrounds picking up the desktop picture's color under the graphite
  accent setting) without the component's own color fluctuating unpredictably as the window moves.

(HIG: Materials, https://developer.apple.com/design/human-interface-guidelines/materials; HIG: Dark
Mode, https://developer.apple.com/design/human-interface-guidelines/dark-mode)

## Icons and SF Symbols

- Weight-match symbols to adjacent text deliberately — SF Symbols ship in the same nine weights as
  San Francisco specifically so a symbol at Regular sits flush with Regular body text. To give a
  symbol more or less visual emphasis than the text *without* breaking that weight match, change its
  **scale** (small/medium/large), not its weight — scale is the lever designed for relative emphasis
  at a fixed point size.
- Choose a rendering mode by what it needs to communicate, not by default: hierarchical for
  depth/layering within one color; multicolor only for symbols with intrinsic real-world color
  meaning (leaf = green, trash.slash = red — and only where the system symbol already defines that
  mapping); palette when you need 2+ independent colors across layers; monochrome as the safe default
  elsewhere. Regardless of mode, use system-provided colors so the symbol adapts to vibrancy, Dark
  Mode, and accessibility contrast settings automatically.
- Variable color communicates *change over time* (signal strength, playback progress), not
  depth/hierarchy — that's hierarchical rendering's job. Conflating the two produces a symbol whose
  visual language contradicts itself.
- Optical vs. geometric centering: asymmetric icons (e.g. a download arrow with more visual weight at
  the bottom) look wrong when centered geometrically in their bounding box. Fix this by adding
  padding into the asset itself so geometric centering of the *asset* produces optical centering of
  the *icon* — don't eyeball-nudge it at each call site.
- Default to a vector format (PDF/SVG) for custom interface icons so the system scales them for you
  at every resolution — PNG (reserved for app icons and shaded/textured art) requires hand-supplying
  every scale factor and doesn't hold up under the same reuse.
- Reach for a custom icon over an SF Symbol only when: (a) no symbol/composition of symbols fits the
  concept, or (b) you specifically need visual continuity with other custom icons already in your
  interface (all custom icons in an app must share size, detail level, stroke weight, and perspective
  — mixing custom and system icons inconsistently is worse than going fully custom or fully system).
  SF Symbols that depict actual Apple products/features are legally locked: you can display them but
  can't customize them, and can't use any symbol (or confusingly similar image) in an app icon, logo,
  or other trademarked use.
- Don't build selected/unselected icon pairs for standard system components (toolbars, tab bars,
  buttons) — the system already renders the selected-state appearance for you; a hand-authored
  duplicate asset is wasted work that can drift out of sync with the system's own treatment over
  time. Every custom icon still needs an accessibility label wired up (VoiceOver has nothing to read
  otherwise), independent of whether the icon communicates its meaning visually.

(HIG: Icons, https://developer.apple.com/design/human-interface-guidelines/icons; HIG: SF Symbols,
https://developer.apple.com/design/human-interface-guidelines/sf-symbols)

## Images and asset variants

- Design bitmap assets at 1x and scale up for @2x/@3x rather than designing at high-res and scaling
  down; for vector control points, snap to whole values at 1x so the shape stays cleanly aligned to
  the pixel grid at 2x/3x (both are exact multiples of 1x — non-integer 1x values won't be).
- Embed a color profile with every image asset — without it, the same file can render with visibly
  different color on different displays, since the display has nothing telling it how to interpret
  the numbers. (HIG: Color, https://developer.apple.com/design/human-interface-guidelines/color)

(HIG: Images, https://developer.apple.com/design/human-interface-guidelines/images)
