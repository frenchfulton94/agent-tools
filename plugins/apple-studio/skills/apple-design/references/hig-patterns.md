> verified: 2026-09 against https://developer.apple.com/design/human-interface-guidelines/navigation-and-search, https://developer.apple.com/design/human-interface-guidelines/search-fields, https://developer.apple.com/design/human-interface-guidelines/sidebars, https://developer.apple.com/design/human-interface-guidelines/tab-bars, https://developer.apple.com/design/human-interface-guidelines/token-fields, https://developer.apple.com/design/human-interface-guidelines/modality, https://developer.apple.com/design/human-interface-guidelines/feedback, https://developer.apple.com/design/human-interface-guidelines/entering-data, https://developer.apple.com/design/human-interface-guidelines/onboarding, https://developer.apple.com/design/human-interface-guidelines/settings, https://developer.apple.com/design/human-interface-guidelines/loading; re-checked 2026-09 against https://developer.apple.com/documentation/swiftui/view/sensoryfeedback(_:trigger:).md for the layered-feedback mechanism addition (Phase 7 Task 2); re-checked 2026-09 (Phase 9: pointer to adaptive-layout.md); re-checked 2026-10 against https://developer.apple.com/design/human-interface-guidelines/alerts, https://developer.apple.com/design/human-interface-guidelines/action-sheets, https://developer.apple.com/documentation/swiftui/view/confirmationdialog(_:ispresented:titlevisibility:actions:message:).md, https://developer.apple.com/documentation/swiftui/buttonrole/destructive.md, https://developer.apple.com/documentation/swiftui/button/init(_:role:action:).md for the destructive-action confirmation (Phase 9 final review), compiled against the macOS 27.0 SDK
> sources: live HIG (DocC JSON)
> note: HIG has no dedicated empty-states page as of 2026-08 (4 slug variants probed, all 404; full Patterns and Components indexes checked) — not covered here, not invented.

# HIG Patterns

## Navigation: Sidebar vs. Tab Bar vs. Split View

Choose sidebar or tab bar by space budget and hierarchy depth, not preference.

- A sidebar (`NavigationSplitView`) needs generous vertical and horizontal space. Use it when an app exposes many top-level areas or nested collections (folders, playlists, projects).
- A tab bar is more compact and wins when you'd rather devote screen space to content than to persistent chrome.
- On iPad specifically, prefer a tab bar first. Reach for the `sidebarAdaptable` `TabView` style only once an app has more top-level areas than a fixed tab bar can hold — that style lets people convert between tab bar and sidebar instead of forcing the choice at design time.
(HIG: Sidebars, https://developer.apple.com/design/human-interface-guidelines/sidebars; Tab Bars, https://developer.apple.com/design/human-interface-guidelines/tab-bars)

Cap sidebar hierarchy at two visible levels.

- Deeper data needs a genuine split view (sidebar + content list + detail), not more sidebar nesting.
- If you must show two levels, group them under short, descriptive labels and collapse extra depth behind disclosure controls.
- Never hide the sidebar by default — people need to discover it before they can choose to collapse it.
(HIG: Sidebars)

Size tab bars for restraint.

- Weigh each additional tab against how often people actually need that section; fewer tabs is genuinely easier to navigate.
- When custom tab selection is offered, default to five or fewer tabs to preserve continuity between compact and regular layouts.
- Avoid letting a tab overflow into a "More" list — hidden tabs are effectively undiscoverable.
- Never disable or hide a tab because its content happens to be empty. Keep it present and explain the empty state inline instead; inconsistent tab availability reads as an unstable app.
- Reserve badges strictly for information that actually warrants interrupting attention. Overuse erodes their signal.
- A tab bar is for navigating between top-level sections only — route in-context actions through a toolbar instead.
(HIG: Tab Bars)

Where bars move to a vertical edge — iPhone Duo's outer display and landscape inner display — item order, overflow, and toolbar-versus-tab-bar compression are in `adaptive-layout.md` § Bars that adapt to space.

## Search

Placement should match the app's intent, not just available chrome space.

- A dedicated search tab suits content-rich, browse-and-discover apps — it gives room to surface suggestions, recent searches, and categories before anyone types, which supports exploration.
- A button-style search entry that jumps straight to a focused field with the keyboard up suits a fast, transient lookup that returns people to what they were doing.
- Inline search local to one list is right when the scope is local to that content and position itself should communicate "this searches only what's below it."
- On iPad/Mac: toolbar-trailing placement suits split-view apps where results should stay visible alongside a selection in the detail pane; sidebar-top placement suits filtering the navigation structure itself (as Settings does). SwiftUI's `.searchable(text:placement:)` has a `SearchFieldPlacement` case for each: `.toolbar` and `.sidebar`, plus `.navigationBarDrawer` for the iOS/iPadOS default and `.automatic` to let the system decide.
(HIG: Search Fields, https://developer.apple.com/design/human-interface-guidelines/search-fields; SearchFieldPlacement, https://developer.apple.com/documentation/swiftui/searchfieldplacement.md)

Filter live, and default broad.

- Start filtering as the person types rather than waiting for a submit action — perceived responsiveness matters more than exact-match precision.
- Default a scope bar to the broadest scope and let people narrow it, rather than starting narrow.
- A scope bar filters within an already-run search; a token represents one discrete, editable search term (a specific contact, an attribute). Pair token suggestions with search suggestions, since people won't otherwise discover tokens exist.
(HIG: Search Fields)

## Modality: Sheets, Full-Screen, and Alerts

Modal presentation (`.sheet`, `.fullScreenCover`, alerts) exists to force a narrow, distinct task or deliver something people must act on — not as a default container for "one more screen."

- Justify every modal with a concrete benefit: confirming or adjusting a just-completed action, an immersive task like editing, or information that truly must interrupt.
- If a modal task grows a multi-view hierarchy inside itself, keep it to one linear path. Nested navigation inside a modal is exactly where people lose track of how to get back out, and it starts to feel like a separate app bolted onto yours.
- Prefer full-screen presentation (`.fullScreenCover`) over a sheet when content is genuinely immersive or a multistep task (photo/video editing, markup) — it minimizes distraction better than a partial sheet.
(HIG: Modality, https://developer.apple.com/design/human-interface-guidelines/modality)

Never stack modals.

- Let one fully dismiss before presenting the next; concurrent modal views compound the cognitive cost of remembering what was suspended underneath.
- Alerts are the one exception — they can appear above any other modal content — but never show two alerts at once.
- Always give an obvious, platform-conventional dismissal (swipe-down or toolbar button, depending on platform), and title the modal so people can identify its task at a glance.
- Gate dismissal with a confirmation only when closing would cause unexpected, irreversible loss of user-generated content. Don't add confirmation friction to expected, reversible dismissals.
(HIG: Modality)

Confirm a destructive action in proportion to what it destroys.

- Do not confirm a common destructive action that people can undo, such as deleting one email. People mean to discard that data, and they can get it back. Confirm an uncommon destructive action that people cannot undo, because they may have started it by accident. § Feedback and Loading has the same rule for warnings in general. (HIG: Alerts § Best practices, https://developer.apple.com/design/human-interface-guidelines/alerts)
- To offer choices about an action that people started on purpose, prefer an action sheet to an alert. An action sheet can offer other choices about the action, such as saving a draft instead of deleting it. An alert can only confirm or cancel, and people usually read an alert as news of a problem. In SwiftUI, present an action sheet with `confirmationDialog(_:isPresented:titleVisibility:actions:)`. (HIG: Action sheets, https://developer.apple.com/design/human-interface-guidelines/action-sheets; Alerts § iOS, iPadOS)
- In an action sheet, give each destructive choice `role: .destructive`, so that the system styles it as destructive. The dialog includes a dismiss action by default, and a button with `role: .cancel` replaces it. In a regular size class on iOS, the dialog is a popover that a tap outside dismisses. (HIG: Action sheets; `confirmationDialog`)
- In an alert, the HIG keeps the destructive style for a destructive button that people did not deliberately choose. When people choose Empty Trash, the alert's Empty Trash button stays in the default style. Always include a Cancel button with a destructive action, and do not make Cancel the default button. (HIG: Alerts § Buttons)
- Title the destructive button with its result, such as "Delete" or "Erase", not "OK". On iOS, the dialog shows only the `Text` label of each button and omits any other label content. (HIG: Alerts § Buttons; `confirmationDialog`)

```swift
struct DeleteProjectButton: View {
    @State private var isConfirming = false

    var body: some View {
        Button("Delete Project", role: .destructive) {
            isConfirming = true
        }
        .confirmationDialog(
            "Delete this project?",
            isPresented: $isConfirming,
            titleVisibility: .visible
        ) {
            Button("Delete Project", role: .destructive) {
                // Delete the project here.
            }
        } message: {
            Text("This deletes every file in the project. You can't undo this action.")
        }
    }
}
```

## Feedback and Loading

Match the delivery mechanism to the stakes of the information — there's no single default.

- Passive, in-place status (a badge, an inline count) suits information people can check on their own schedule.
- Alerts are for information significant enough to justify interrupting, and lose their power fast if overused for routine status.
- Warn before an action only when data loss would be unexpected and irreversible. Don't warn on loss that's the plainly expected outcome of the action just taken (deleting a file doesn't need a confirmation every time).
- Confirm success only for actions significant enough that people would otherwise wonder — routine actions are assumed to succeed silently; reserve confirmation for things like a completed payment.
- When a command can't execute, say why specifically, not just that it failed.
- Layer feedback across more than one channel (color, text, sound, haptics) so it reaches people regardless of context — silenced device, VoiceOver, or not looking at the screen. `.sensoryFeedback(_:trigger:)` (iOS 17+) is the SwiftUI mechanism for the haptic/audio channel specifically: attach it to a view with a feedback type and an `Equatable` value, and it fires when that value changes — the same trigger-on-value-change shape as `.animation(_:value:)`, but for haptics/sound instead of motion (confirmed against live `View.sensoryFeedback(_:trigger:)` DocC).
(HIG: Feedback, https://developer.apple.com/design/human-interface-guidelines/feedback)

For loading, the target is that people never consciously notice waiting.

- Show something immediately — placeholder content, not a blank screen. A blank screen reads as broken, not as "still loading."
- Choose determinate progress (`ProgressView(value:)`) whenever remaining time is actually estimable; a real percentage lowers perceived wait more than a spinner. Fall back to indeterminate (`ProgressView()`) only when duration is genuinely unknown.
- If a wait is unavoidably long, give people something to do with the time (tips, hints, background-loadable content) rather than a static spinner — and size that filler to roughly match your real load-time estimate, since running out of content mid-wait undercuts the effect as much as under-filling it does.
- Load in the background and keep the rest of the interface usable while you do, rather than blocking interaction on load completion.
- On watchOS, skip indeterminate spinners altogether. An animated indicator implies people must keep watching, which fights the platform's quick-glance expectation; use a brief loading indicator only for waits of a second or two, and otherwise reassure people you'll notify them when done.
(HIG: Loading, https://developer.apple.com/design/human-interface-guidelines/loading; Feedback)

## Entering Data (Forms)

Before asking someone to type anything, ask whether you can get it another way.

- Pull from system settings, a granted permission (location, calendar), or a prior entry, and prefill or default rather than prompting.
- When text entry is unavoidable, be explicit about the expected format via placeholder text or a label — a "username@company.com" placeholder beats a bare "Email" label alone.
- Prefer selection controls (picker, menu) over free text whenever the answer space is enumerable; choosing is faster and more accurate than typing, even when a keyboard is available.
- Support paste and drag-and-drop as first-class entry paths, not just typing.
(HIG: Entering Data, https://developer.apple.com/design/human-interface-guidelines/entering-data)

Validate as people type, not only on submit.

- Surface an error the moment it's detectable, especially for numeric fields, where a formatter can both restrict input and shape its display (decimal places, percentage, currency). This avoids the frustrating pattern of discovering every mistake at once after finishing a long form.
- Gate progression (a Next/Continue button) on required fields being valid, rather than letting people advance and fail later.
- Use a secure field (`SecureField` in SwiftUI) for sensitive input, and never prepopulate a password field under any circumstance — always require explicit entry or biometric/keychain auth.
(HIG: Entering Data)

## Onboarding

Default to teaching through the product itself, not a bolted-on flow.

- People retain "try the action" far better than "read about the action."
- Prefer contextual, in-place tips scoped to a single feature (TipKit-style) over one upfront tutorial — a tip lets someone learn one thing while making real progress, instead of front-loading everything before they've done anything.
- If a prerequisite flow is genuinely necessary, keep it short and make it skippable. If someone skips it on first launch, never resurface it unprompted — keep it reachable later (help, account, or settings area) instead.
- Scope onboarding strictly to your app's own concepts; don't spend it re-teaching system-level gestures or platform basics.
(HIG: Onboarding, https://developer.apple.com/design/human-interface-guidelines/onboarding)

Sequence onboarding's surrounding mechanics deliberately.

- Onboarding begins only after launch is fully complete — never treat it as part of the launch sequence itself.
- Don't let onboarding stall on a large download; bundle enough content in the initial install, or schedule background asset downloads, so onboarding doesn't sit waiting on the network.
- If you use a splash screen, keep it on-screen barely long enough to register — not as a branding beat.
- Defer non-essential setup and customization behind sane defaults so most people can start using the app with zero configuration.
- Fold a permission request into onboarding only if the app is functionally useless without it (and use that moment to explain the benefit); otherwise defer the request to the first moment the relevant feature is actually used.
- Hold ratings and purchase prompts until after real engagement. Asking before value is demonstrated reads as presumptuous and performs worse.
(HIG: Onboarding)

## Settings

Settings exist for the minority who need to deviate from good defaults.

- Design defaults good enough that most people never open the settings screen at all.
- Every additional setting is a cost — it makes the surface harder to scan and the app feel less approachable. Treat "should this be a setting" as a real question, not a default yes.
(HIG: Settings, https://developer.apple.com/design/human-interface-guidelines/settings)

Route each setting to where its change frequency and scope say it belongs, rather than centralizing everything.

- Put settings people adjust often, or that only affect the screen they're on (visibility toggles, sort order, filters), directly in that screen's own UI. Burying a frequently-touched, task-scoped option in a separate settings area disconnects cause from visible effect and forces an unnecessary context switch.
- Reserve your app's custom settings area for general, infrequently-changed options that affect the whole experience (interface style, save behavior, account details).
- Reserve the system Settings app for only the most rarely touched options, ideally with a direct-open button from within your app.
- Never duplicate a systemwide setting (accessibility accommodations, Dark Mode, scroll behavior) inside your own settings surface — it implies your app might not honor the system choice, which is confusing even when untrue. Detect systemwide state instead of asking for it again.
(HIG: Settings)

On macOS, honor the platform's settings-window conventions precisely.

- Put the settings item in the App menu, not a toolbar button (which would steal space from frequent commands) — SwiftUI's `Settings{}` scene wires the Cmd-, shortcut and the App menu item automatically once you give it a view; you don't hand-roll either.
- Use a fixed, non-customizable toolbar across panes so the settings surface stays predictable; group panes with `TabView` inside the scene rather than building custom pane-switching.
- Retitle the window to the active pane, and reopen to whichever pane was last viewed rather than always resetting to the first — this is on you to implement (persist the selection, e.g. via `@SceneStorage`), it isn't automatic scene behavior.
(HIG: Settings; Settings scene, https://developer.apple.com/documentation/swiftui/settings.md)
