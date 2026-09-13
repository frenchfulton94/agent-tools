# HIG endpoint map: apple-design

Targets (Tasks 2–3): `hig-foundations.md`, `hig-patterns.md`, `platform-idioms.md`, `accessibility.md`, `animation-taste.md`.

## Endpoint pattern (verified 2026-08-04, differs from the brief's assumption)

The brief assumed `https://developer.apple.com/tutorials/data/documentation/design/<page>.json`.
That path 404s. The human HIG pages (`https://developer.apple.com/design/human-interface-guidelines...`)
are JS-rendered; captured the real DocC data request via a live-browser network trace
(Playwright, navigated to the HIG landing page, inspected XHR/fetch requests). The actual,
verified pattern is:

```
https://developer.apple.com/tutorials/data/design/human-interface-guidelines/<slug>.json
```

(note: `data/design/...`, not `data/documentation/design/...`; the site's DocC bundle
identifier is `com.apple.HIG` rooted at `design/Human-Interface-Guidelines`, not
`documentation/design`). Every endpoint listed below was individually probed with
`curl -s -o <file> -w '%{http_code}'` and its body parsed as JSON (`kind: "article"`
confirmed for every leaf below) — see the Task 1 report for the full probe log.

The top-level index (`.../human-interface-guidelines.json`) groups pages under six
un-titled `topicSections`: Getting started, Foundations, Patterns, Components, Inputs,
Technologies. Each of those six group pages was fetched to enumerate its own children
(`.../human-interface-guidelines/<group>.json`), which is how the leaf slugs below were
discovered — the index does not flatten grandchildren into one list.

## hig-foundations.md

- `https://developer.apple.com/design/human-interface-guidelines/layout` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/layout.json`
- `https://developer.apple.com/design/human-interface-guidelines/typography` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/typography.json`
- `https://developer.apple.com/design/human-interface-guidelines/color` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/color.json`
- `https://developer.apple.com/design/human-interface-guidelines/materials` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/materials.json`
- `https://developer.apple.com/design/human-interface-guidelines/dark-mode` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/dark-mode.json`
- `https://developer.apple.com/design/human-interface-guidelines/icons` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/icons.json`
- `https://developer.apple.com/design/human-interface-guidelines/sf-symbols` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/sf-symbols.json`
- `https://developer.apple.com/design/human-interface-guidelines/images` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/images.json`

(Foundations also lists App icons, Branding, Immersive experiences, Privacy, Right to
left, Spatial layout, Writing — not requested by the brief's bucket for this file, left
unassigned. Inclusion and Motion are in Foundations too but route to `accessibility.md`
/ `animation-taste.md` below per the brief.)

## hig-patterns.md

- `https://developer.apple.com/design/human-interface-guidelines/navigation-and-search` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/navigation-and-search.json`
- `https://developer.apple.com/design/human-interface-guidelines/modality` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/modality.json`
- `https://developer.apple.com/design/human-interface-guidelines/feedback` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/feedback.json`
- `https://developer.apple.com/design/human-interface-guidelines/entering-data` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/entering-data.json`
- `https://developer.apple.com/design/human-interface-guidelines/onboarding` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/onboarding.json`
- `https://developer.apple.com/design/human-interface-guidelines/settings` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/settings.json`
- `https://developer.apple.com/design/human-interface-guidelines/loading` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/loading.json`
- MISSING: empty-states — no such page in the current HIG index. Checked the "Patterns"
  and "Components" group listings (25 and 8 children respectively, full lists in the
  probe log) and tried slug variants `empty-states`, `empty-state`, `empty-views`,
  `empty-view` directly against the JSON endpoint — all 404. Apple's current HIG has no
  dedicated empty-state guidance page; the distiller for `hig-patterns.md` should note
  this gap rather than invent content.

(`navigation-and-search` lives under the "Components" group, not "Patterns" — its own
page carries pattern-level guidance despite the parent grouping.)

## platform-idioms.md

- `https://developer.apple.com/design/human-interface-guidelines/designing-for-ios` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/designing-for-ios.json`
- `https://developer.apple.com/design/human-interface-guidelines/designing-for-ipados` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/designing-for-ipados.json`
- `https://developer.apple.com/design/human-interface-guidelines/designing-for-macos` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/designing-for-macos.json`
- `https://developer.apple.com/design/human-interface-guidelines/windows` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/windows.json`
- `https://developer.apple.com/design/human-interface-guidelines/multitasking` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/multitasking.json`
- `https://developer.apple.com/design/human-interface-guidelines/pointing-devices` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/pointing-devices.json`
- `https://developer.apple.com/design/human-interface-guidelines/keyboards` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/keyboards.json`

(`windows` lives under the "Components" → "Presentation" group, not under "Getting
started" with the platform pages; `pointing-devices` and `keyboards` live under
"Inputs" — the brief's single "pointer-and-keyboard" bucket maps to these two distinct
pages, there is no combined page.)

## accessibility.md

- `https://developer.apple.com/design/human-interface-guidelines/accessibility` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/accessibility.json`
- `https://developer.apple.com/design/human-interface-guidelines/inclusion` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/inclusion.json`
- `https://developer.apple.com/design/human-interface-guidelines/motion` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/motion.json` (shared with animation-taste.md — Reduce Motion)

## animation-taste.md

- `https://developer.apple.com/design/human-interface-guidelines/motion` → `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/motion.json` (shared with accessibility.md — same endpoint, cite once; animation-taste.md's distiller should cross-reference accessibility.md's Reduce Motion coverage rather than duplicate it)
