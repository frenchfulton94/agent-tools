# Live endpoint map: apple-macos

Targets (Tasks 2–3): `mac-app-structure.md`, `mac-windows-menus-commands.md`,
`appkit-interop.md`, `mac-sandbox-and-files.md`.

## Endpoint pattern (confirmed, matches the brief's assumption)

```
https://developer.apple.com/tutorials/data/documentation/<path>.json
```

where `<path>` mirrors the human URL path under `developer.apple.com/documentation/`
(lowercase, hyphenated, exactly as Apple's own `topicSections`/`references` JSON
reports it, lowercased). `security/app-sandbox` confirmed: the dash form returns
200, the naive underscore form (`security/app_sandbox`) 301-redirects to the dash
form — probed with `curl -sI` before use, matching the brief's note.

All 25 endpoints seeded by the brief were fetched with
`curl -s -o <file> -w '%{http_code}'` and returned 200 (none of the pre-probed
list had drifted since planning). Six of those seeds are DocC *index* pages
(`role: collectionGroup`, non-empty `topicSections`): `swiftui/app-organization`,
`swiftui/scenes`, `swiftui/documents`, `swiftui/windows`, `swiftui/toolbars`,
`swiftui/focus`, plus `swiftui/appkit-integration` and `security/app-sandbox` —
eight in total. Each was fetched and its `topicSections` walked via the
`references` map to find child titles and human URLs; a macOS-relevant subset of
each was then individually fetched and confirmed 200 before being added below (46
additional fetches beyond the 25 seeds, all 200 — see the Task 1 report for the
full probe log). `appkit` was fetched per the brief but deliberately **not**
enumerated — it's a huge, mostly-2010s AppKit symbol index; the brief scopes it to
gap-checking only, not distillation depth. `bundleresources/entitlements` is a
several-hundred-entry catalog spanning every Apple platform (CarPlay, HealthKit,
Wallet, visionOS, …); only the sandbox/file/network-relevant subset was
enumerated, per the brief's "enumerate the sandbox/file entitlement children"
scoping — most of that subset actually surfaces via `security/app-sandbox`'s own
"File Access" and "Network" `topicSections` rather than `entitlements.json`'s own
sections, so the two indexes' relevant children are reported together under
`mac-sandbox-and-files.md`.

## mac-app-structure.md

- `https://developer.apple.com/documentation/swiftui/app-organization` → `https://developer.apple.com/tutorials/data/documentation/swiftui/app-organization.json` (index, enumerated below)
- `https://developer.apple.com/documentation/swiftui/scenes` → `https://developer.apple.com/tutorials/data/documentation/swiftui/scenes.json` (index, enumerated below)
- `https://developer.apple.com/documentation/swiftui/windowgroup` → `https://developer.apple.com/tutorials/data/documentation/swiftui/windowgroup.json`
- `https://developer.apple.com/documentation/swiftui/window` → `https://developer.apple.com/tutorials/data/documentation/swiftui/window.json`
- `https://developer.apple.com/documentation/swiftui/settings` → `https://developer.apple.com/tutorials/data/documentation/swiftui/settings.json`
- `https://developer.apple.com/documentation/swiftui/documentgroup` → `https://developer.apple.com/tutorials/data/documentation/swiftui/documentgroup.json`
- `https://developer.apple.com/documentation/swiftui/documents` → `https://developer.apple.com/tutorials/data/documentation/swiftui/documents.json` (index, enumerated below)
- `https://developer.apple.com/documentation/swiftui/menubarextra` → `https://developer.apple.com/tutorials/data/documentation/swiftui/menubarextra.json`
- `https://developer.apple.com/documentation/uikit/mac-catalyst` → `https://developer.apple.com/tutorials/data/documentation/uikit/mac-catalyst.json` (judgment section only — not a source for Catalyst API mechanics)

Children of `swiftui/app-organization` (macOS-relevant subset — the rest of that
index is visionOS/tvOS/watchOS-specific sample apps and iOS launch-screen keys):

- `https://developer.apple.com/documentation/swiftui/app` → `https://developer.apple.com/tutorials/data/documentation/swiftui/app.json`
- `https://developer.apple.com/documentation/swiftui/nsapplicationdelegateadaptor` → `https://developer.apple.com/tutorials/data/documentation/swiftui/nsapplicationdelegateadaptor.json`

Children of `swiftui/scenes` (macOS-relevant subset — visionOS volume/accessory,
watchOS notification-scene, and tvOS entries excluded):

- `https://developer.apple.com/documentation/swiftui/scene` → `https://developer.apple.com/tutorials/data/documentation/swiftui/scene.json`
- `https://developer.apple.com/documentation/swiftui/scenephase` → `https://developer.apple.com/tutorials/data/documentation/swiftui/scenephase.json`
- `https://developer.apple.com/documentation/swiftui/settingslink` → `https://developer.apple.com/tutorials/data/documentation/swiftui/settingslink.json`
- `https://developer.apple.com/documentation/swiftui/opensettingsaction` → `https://developer.apple.com/tutorials/data/documentation/swiftui/opensettingsaction.json`
- `https://developer.apple.com/documentation/swiftui/building-and-customizing-the-menu-bar-with-swiftui` → `https://developer.apple.com/tutorials/data/documentation/swiftui/building-and-customizing-the-menu-bar-with-swiftui.json`
- `https://developer.apple.com/documentation/swiftui/menubarextrastyle` → `https://developer.apple.com/tutorials/data/documentation/swiftui/menubarextrastyle.json`

Children of `swiftui/documents` (macOS-relevant subset — the "Deprecated"
`FileDocument`-family group and visionOS-specific launch-geometry entries
excluded):

- `https://developer.apple.com/documentation/swiftui/creating-a-document-based-app` → `https://developer.apple.com/tutorials/data/documentation/swiftui/creating-a-document-based-app.json`
- `https://developer.apple.com/documentation/swiftui/building-a-document-based-app-with-swiftui` → `https://developer.apple.com/tutorials/data/documentation/swiftui/building-a-document-based-app-with-swiftui.json`
- `https://developer.apple.com/documentation/swiftui/document` → `https://developer.apple.com/tutorials/data/documentation/swiftui/document.json`
- `https://developer.apple.com/documentation/swiftui/documentconfiguration` → `https://developer.apple.com/tutorials/data/documentation/swiftui/documentconfiguration.json`
- `https://developer.apple.com/documentation/swiftui/renamebutton` → `https://developer.apple.com/tutorials/data/documentation/swiftui/renamebutton.json`
- `https://developer.apple.com/documentation/swiftui/opendocumentaction` → `https://developer.apple.com/tutorials/data/documentation/swiftui/opendocumentaction.json`

## mac-windows-menus-commands.md

- `https://developer.apple.com/documentation/swiftui/windows` → `https://developer.apple.com/tutorials/data/documentation/swiftui/windows.json` (index, enumerated below)
- `https://developer.apple.com/documentation/swiftui/commands` → `https://developer.apple.com/tutorials/data/documentation/swiftui/commands.json`
- `https://developer.apple.com/documentation/swiftui/commandmenu` → `https://developer.apple.com/tutorials/data/documentation/swiftui/commandmenu.json`
- `https://developer.apple.com/documentation/swiftui/commandgroup` → `https://developer.apple.com/tutorials/data/documentation/swiftui/commandgroup.json`
- `https://developer.apple.com/documentation/swiftui/toolbars` → `https://developer.apple.com/tutorials/data/documentation/swiftui/toolbars.json` (index, enumerated below)
- `https://developer.apple.com/documentation/swiftui/focus` → `https://developer.apple.com/tutorials/data/documentation/swiftui/focus.json` (index, enumerated below)
- `https://developer.apple.com/documentation/swiftui/view/keyboardshortcut(_:modifiers:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/keyboardshortcut(_:modifiers:).json`

MISSING: `swiftui/scene-restoration` (404 at planning probe — restoration
coverage comes from the windows/scenes index children instead). Re-confirmed
404 during this task's fetch pass. The substitute is
`swiftui/customizing-window-styles-and-state-restoration-behavior-in-macos`,
enumerated below — it's the actual macOS window-restoration article and covers
the same ground the missing symbol page would have.

Children of `swiftui/windows` (macOS-relevant subset — this index is
heavily visionOS-weighted with volume/viewpoint/world-alignment entries for
spatial windows; those, plus the Deprecated `ControlActiveState`, are excluded):

- `https://developer.apple.com/documentation/swiftui/customizing-window-styles-and-state-restoration-behavior-in-macos` → `https://developer.apple.com/tutorials/data/documentation/swiftui/customizing-window-styles-and-state-restoration-behavior-in-macos.json`
- `https://developer.apple.com/documentation/swiftui/bringing-multiple-windows-to-your-swiftui-app` → `https://developer.apple.com/tutorials/data/documentation/swiftui/bringing-multiple-windows-to-your-swiftui-app.json`
- `https://developer.apple.com/documentation/swiftui/utilitywindow` → `https://developer.apple.com/tutorials/data/documentation/swiftui/utilitywindow.json`
- `https://developer.apple.com/documentation/swiftui/windowstyle` → `https://developer.apple.com/tutorials/data/documentation/swiftui/windowstyle.json`
- `https://developer.apple.com/documentation/swiftui/openwindowaction` → `https://developer.apple.com/tutorials/data/documentation/swiftui/openwindowaction.json`
- `https://developer.apple.com/documentation/swiftui/dismisswindowaction` → `https://developer.apple.com/tutorials/data/documentation/swiftui/dismisswindowaction.json`
- `https://developer.apple.com/documentation/swiftui/windowresizability` → `https://developer.apple.com/tutorials/data/documentation/swiftui/windowresizability.json`
- `https://developer.apple.com/documentation/swiftui/scenerestorationbehavior` → `https://developer.apple.com/tutorials/data/documentation/swiftui/scenerestorationbehavior.json`
- `https://developer.apple.com/documentation/swiftui/scenelaunchbehavior` → `https://developer.apple.com/tutorials/data/documentation/swiftui/scenelaunchbehavior.json`

Children of `swiftui/toolbars` (macOS-relevant subset — visionOS ornament and
volume-related entries excluded):

- `https://developer.apple.com/documentation/swiftui/toolbaritem` → `https://developer.apple.com/tutorials/data/documentation/swiftui/toolbaritem.json`
- `https://developer.apple.com/documentation/swiftui/toolbaritemgroup` → `https://developer.apple.com/tutorials/data/documentation/swiftui/toolbaritemgroup.json`
- `https://developer.apple.com/documentation/swiftui/toolbaritemplacement` → `https://developer.apple.com/tutorials/data/documentation/swiftui/toolbaritemplacement.json`
- `https://developer.apple.com/documentation/swiftui/customizabletoolbarcontent` → `https://developer.apple.com/tutorials/data/documentation/swiftui/customizabletoolbarcontent.json`

Children of `swiftui/focus` (macOS-relevant subset — this index is large and
mostly cross-platform; the three entries below are the ones tied to the book's
own "tracking the key window is hard" judgment and the `FocusState` mechanism it
substitutes for a working `@FocusedBinding`):

- `https://developer.apple.com/documentation/swiftui/focusstate` → `https://developer.apple.com/tutorials/data/documentation/swiftui/focusstate.json`
- `https://developer.apple.com/documentation/swiftui/focusedbinding` → `https://developer.apple.com/tutorials/data/documentation/swiftui/focusedbinding.json`
- `https://developer.apple.com/documentation/swiftui/resetfocusaction` → `https://developer.apple.com/tutorials/data/documentation/swiftui/resetfocusaction.json`

## appkit-interop.md

- `https://developer.apple.com/documentation/swiftui/appkit-integration` → `https://developer.apple.com/tutorials/data/documentation/swiftui/appkit-integration.json` (index, enumerated below)
- `https://developer.apple.com/documentation/swiftui/nsviewrepresentable` → `https://developer.apple.com/tutorials/data/documentation/swiftui/nsviewrepresentable.json`
- `https://developer.apple.com/documentation/swiftui/nsviewcontrollerrepresentable` → `https://developer.apple.com/tutorials/data/documentation/swiftui/nsviewcontrollerrepresentable.json`
- `https://developer.apple.com/documentation/appkit` → `https://developer.apple.com/tutorials/data/documentation/appkit.json` (index — fetched for gap-checking only, per the brief; NOT enumerated, it's a large legacy symbol catalog and distilling it would reintroduce ~2022-era AppKit API depth this skill deliberately excludes)

Children of `swiftui/appkit-integration` (macOS-relevant subset — the three
`NSHostingScene*`/`NSHostingSizingOptions` entries are visionOS-scene-bridging
mechanics from a later SDK than this skill targets, and were excluded):

- `https://developer.apple.com/documentation/swiftui/nshostingcontroller` → `https://developer.apple.com/tutorials/data/documentation/swiftui/nshostingcontroller.json`
- `https://developer.apple.com/documentation/swiftui/nshostingview` → `https://developer.apple.com/tutorials/data/documentation/swiftui/nshostingview.json`
- `https://developer.apple.com/documentation/swiftui/nsviewrepresentablecontext` → `https://developer.apple.com/tutorials/data/documentation/swiftui/nsviewrepresentablecontext.json`
- `https://developer.apple.com/documentation/swiftui/nsviewcontrollerrepresentablecontext` → `https://developer.apple.com/tutorials/data/documentation/swiftui/nsviewcontrollerrepresentablecontext.json`
- `https://developer.apple.com/documentation/swiftui/nsgesturerecognizerrepresentable` → `https://developer.apple.com/tutorials/data/documentation/swiftui/nsgesturerecognizerrepresentable.json`

## mac-sandbox-and-files.md

- `https://developer.apple.com/documentation/security/app-sandbox` → `https://developer.apple.com/tutorials/data/documentation/security/app-sandbox.json` (index, enumerated below; dash form confirmed 200, underscore form confirmed 301 → dash form via `curl -sI`)
- `https://developer.apple.com/documentation/security/hardened-runtime` → `https://developer.apple.com/tutorials/data/documentation/security/hardened-runtime.json`
- `https://developer.apple.com/documentation/bundleresources/entitlements` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements.json` (index, sandbox/file/network subset enumerated below)
- `https://developer.apple.com/documentation/foundation/nsurl/bookmarkdata(options:includingresourcevaluesforkeys:relativeto:)` → `https://developer.apple.com/tutorials/data/documentation/foundation/nsurl/bookmarkdata(options:includingresourcevaluesforkeys:relativeto:).json`
- `https://developer.apple.com/documentation/swiftui/view/fileimporter(ispresented:allowedcontenttypes:oncompletion:)` → `https://developer.apple.com/tutorials/data/documentation/swiftui/view/fileimporter(ispresented:allowedcontenttypes:oncompletion:).json`

Children of `security/app-sandbox`'s "Essentials", "Network", and "File Access"
`topicSections` (the "Hardware" and "App Data" sections — camera, microphone,
address book, location, calendars — are out of scope for a files/persistence
skill and were excluded):

- `https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox` → `https://developer.apple.com/tutorials/data/documentation/security/protecting-user-data-with-app-sandbox.json`
- `https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox` → `https://developer.apple.com/tutorials/data/documentation/security/accessing-files-from-the-macos-app-sandbox.json`
- `https://developer.apple.com/documentation/security/migrating-your-app-s-files-to-its-app-sandbox-container` → `https://developer.apple.com/tutorials/data/documentation/security/migrating-your-app-s-files-to-its-app-sandbox-container.json`
- `https://developer.apple.com/documentation/security/discovering-and-diagnosing-app-sandbox-violations` → `https://developer.apple.com/tutorials/data/documentation/security/discovering-and-diagnosing-app-sandbox-violations.json`
- `https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.network.client` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.security.network.client.json`
- `https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.network.server` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.security.network.server.json`
- `https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.files.user-selected.read-only` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.security.files.user-selected.read-only.json`
- `https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.files.user-selected.read-write` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.security.files.user-selected.read-write.json`
- `https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.files.downloads.read-only` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.security.files.downloads.read-only.json`
- `https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.files.downloads.read-write` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.security.files.downloads.read-write.json`

Additional children found only in `bundleresources/entitlements`'s own
"Security" and "Deprecated entitlements" sections (not cross-listed under
`security/app-sandbox`):

- `https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.app-sandbox` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.security.app-sandbox.json`
- `https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.files.all` → `https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.security.files.all.json`
