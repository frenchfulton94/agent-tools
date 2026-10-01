# Live endpoint map: adaptive layout and iPhone Duo (Phase 9)

Target (Task 4): `plugins/apple-studio/skills/apple-design/references/adaptive-layout.md`.

This map is a **seed list, not an exhaustive registry**, per the CONVENTIONS.md
"Distillation maps" rule. The reference file's own header citations, not this
map, are the citation record. Expected pages that fail are recorded as
`MISSING:`.

All commands run from the catalog root as
`python3 authoring/apple-studio/pipeline/docc.py <args>`. Output went to the
session scratchpad, never the repository. Fetched 2026-09-30; every seed below
returned DocC JSON 200 unless marked `MISSING:`.

**A 200 is not evidence that a symbol ships.** Every SwiftUI and UIKit name that
the reference uses was also checked against the iPhoneOS 27.1 SDK interface and
headers (Xcode 27.1 beta). See the Task 4 report.

## Human Interface Guidelines

- `--hig designing-for-iphone-duo`
- `--hig layout`
- `--hig toolbars`
- `--hig split-views`
- `--hig designing-for-games` (followed from the Duo page's games link)
- MISSING: `--hig games` — HTTP 404. The games page slug is `designing-for-games`.

## Developer overview

- `technologyoverviews/preparing-your-app-for-iphone-duo`

## SwiftUI

- `swiftui/reservedregion`
- `"swiftui/geometryproxy/reservedregions(kind:options:layoutdirectionbehavior:)"`
- `swiftui/arrangementview`
- `"swiftui/view/arrangementviewstyle(_:)"`
- `swiftui/environmentvalues/toolbarverticaledge`
- `"swiftui/view/toolbarverticalbehavior(_:)"`
- `"swiftui/view/toolbarverticalcompressionbehavior(_:)"`
- `"swiftui/toolbarcontent/axisbehavior(_:)"`
- `"swiftui/toolbarcontent/visibilitypriority(_:)"`
- `swiftui/toolbaroverflowmenu`
- `swiftui/toolbaritemplacement/topbarpinnedtrailing`
- `"swiftui/view/presentationplacement(_:)"`
- `"swiftui/view/backgroundextensioneffect()"`

## UIKit

- `uikit/uiarrangementviewcontroller`
- `uikit/uiview/reservedregion`
- `"uikit/uiview/reservedregions(kind:options:)"`
- `uikit/uitraitcollection/verticalbaredge`
- `uikit/uiviewcontroller/preferredverticalbarbehavior`
- `uikit/uinavigationitem/pinnedtrailinggroup`
- `uikit/uinavigationitem/additionaloverflowitems`
- `uikit/uibarbuttonitem/axisbehavior-swift.property`
- `uikit/uibarbuttonitem/visibilitypriority`
- `uikit/uisheetpresentationcontroller/preferredplacement` (200, but the page has no abstract or discussion)
- `uikit/uibackgroundextensionview`
- `uikit/uiverticalbarcompressionbehavior` (200, abstract only; the property that takes it is `UINavigationItem.verticalBarCompressionBehavior`, found in the 27.1 SDK `UINavigationItem.h`)

## Tools and camera

- `xcode/device-hub`
- `avkit/choosing-a-camera-by-the-direction-it-faces`
- `avfoundation/registering-a-camera-capture-accessory-on-iphone-duo`

## Not DocC

- App Store Connect screenshot specifications —
  https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications
  (WebFetch, 2026-09-30; see `records/2026-09-30-phase9-adaptive-layout/survey/screenshot-specifications.txt`).
  Consumed by Task 5, not by `adaptive-layout.md`.

## Known rendering gaps

- The `ReservedRegion` and `UIView.ReservedRegion` pages print "There are two
  categories of reserved regions:" followed by nothing. The list is a DocC
  `termList` node, which `docc.py` does not render. The raw JSON was read
  directly: `occlusion` covers the Dynamic Island, a camera, or window
  controls; `division` covers content split at a hinge's fold. Both kinds are
  confirmed in the SDK interface.
