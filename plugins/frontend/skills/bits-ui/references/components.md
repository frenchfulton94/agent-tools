# Bits UI: component index

Every component Bits UI ships, grouped by what it's for. Fetch
`https://bits-ui.com/docs/components/<slug>/llms.txt` for the full prop /
data-attribute / CSS-variable reference before implementing one — this
table exists to help you pick the right primitive and jump straight to its
docs, not to replace them.

## Overlays & floating content

| Component    | Slug           | Use it for                                                                                                                         |
| ------------ | -------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Dialog       | `dialog`       | General-purpose modal window for a focused task or piece of content.                                                               |
| Alert Dialog | `alert-dialog` | Modal that interrupts the user and requires an explicit confirm or cancel before it closes — for destructive/irreversible actions. |
| Popover      | `popover`      | Non-modal floating panel anchored to a trigger, for supplementary content or controls.                                             |
| Tooltip      | `tooltip`      | Floating hint shown on hover/focus of a trigger, for brief supplementary text — not for interactive content.                       |
| Link Preview | `link-preview` | Hover-triggered floating preview card for a link's destination.                                                                    |

## Menus & navigation

| Component       | Slug              | Use it for                                                                         |
| --------------- | ----------------- | ---------------------------------------------------------------------------------- |
| Dropdown Menu   | `dropdown-menu`   | Floating list of actions opened from a trigger (e.g. a "⋯" button).                |
| Context Menu    | `context-menu`    | Floating action menu opened via right-click / long-press.                          |
| Menubar         | `menubar`         | Horizontal bar of menus (desktop-app style), each opening a dropdown.              |
| Navigation Menu | `navigation-menu` | Accessible primary site navigation with flyout submenus.                           |
| Command         | `command`         | Searchable command-palette style list (⌘K-style interface).                        |
| Toolbar         | `toolbar`         | Horizontal group of controls (buttons, toggles, links) with roving keyboard focus. |

## Form & input

| Component    | Slug           | Use it for                                                                        |
| ------------ | -------------- | --------------------------------------------------------------------------------- |
| Button       | `button`       | Accessible button primitive with consistent press/keyboard handling.              |
| Checkbox     | `checkbox`     | Accessible checkbox, including an indeterminate state.                            |
| Radio Group  | `radio-group`  | Mutually-exclusive set of radio options with roving focus.                        |
| Switch       | `switch`       | Accessible on/off toggle switch.                                                  |
| Toggle       | `toggle`       | Single pressable on/off button (`aria-pressed`), e.g. a "bold" formatting button. |
| Toggle Group | `toggle-group` | Group of toggle buttons, single- or multi-select (e.g. text alignment controls).  |
| Select       | `select`       | Accessible dropdown for choosing one (or more) options from a list.               |
| Combobox     | `combobox`     | Searchable/filterable select backed by a text input.                              |
| Slider       | `slider`       | Draggable value/range input, single- or multi-thumb.                              |
| Rating Group | `rating-group` | Star/rating-style input for a numeric rating.                                     |
| Pin Input    | `pin-input`    | Segmented one-character-per-box input, for OTP/PIN-style codes.                   |
| Label        | `label`        | Accessible label element that correctly associates with a form control.           |

## Dates & times

All of these use `@internationalized/date` — read `references/dates.md`
before implementing any of them.

| Component         | Slug                | Use it for                                                       |
| ----------------- | ------------------- | ---------------------------------------------------------------- |
| Calendar          | `calendar`          | Full month-grid picker for a single date.                        |
| Range Calendar    | `range-calendar`    | Full month-grid picker for a date range (start + end).           |
| Date Field        | `date-field`        | Segmented, typeable date input (separate day/month/year fields). |
| Date Range Field  | `date-range-field`  | Segmented typeable input for a start/end date range.             |
| Date Picker       | `date-picker`       | Text field + popover calendar combined, for a single date.       |
| Date Range Picker | `date-range-picker` | Text field + popover calendar combined, for a date range.        |
| Time Field        | `time-field`        | Segmented, typeable time input.                                  |
| Time Range Field  | `time-range-field`  | Segmented typeable input for a start/end time range.             |

## Display & feedback

| Component    | Slug           | Use it for                                                                                                                     |
| ------------ | -------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Avatar       | `avatar`       | User/entity image with automatic loading-state fallback.                                                                       |
| Progress     | `progress`     | Determinate progress bar for a task with a known completion percentage.                                                        |
| Meter        | `meter`        | Gauge for a value within a known range (e.g. disk usage) — semantically distinct from Progress, which implies task completion. |
| Pagination   | `pagination`   | Accessible page-number navigation control.                                                                                     |
| Scroll Area  | `scroll-area`  | Custom-styled scrollbars layered over native scrolling behavior.                                                               |
| Aspect Ratio | `aspect-ratio` | Constrains content (usually media) to a fixed width/height ratio.                                                              |
| Separator    | `separator`    | Visual and semantic divider between sections of content.                                                                       |

## Disclosure & layout

| Component   | Slug          | Use it for                                                          |
| ----------- | ------------- | ------------------------------------------------------------------- |
| Accordion   | `accordion`   | Collapsible sections, single- or multi-open.                        |
| Collapsible | `collapsible` | A single show/hide section — the primitive `Accordion` is built on. |
| Tabs        | `tabs`        | Switchable panel views under a tab list.                            |

## Utilities

Not components — helper functions/components used directly or internally
by the components above. Docs at
`https://bits-ui.com/docs/utilities/<slug>/llms.txt`.

| Utility         | Slug                | What it's for                                                                                                                                                                                                                            |
| --------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Portal          | `portal`            | Renders its children into a different DOM location (usually `document.body`); every floating/modal component uses this internally, but it's exported for building custom overlays too.                                                   |
| Merge Props     | `merge-props`       | Merges multiple prop objects — including combining event handlers rather than overwriting them — the same way Bits UI merges internal props with yours. Needed when a wrapper component adds its own handlers on top of the primitive's. |
| useId           | `use-id`            | Generates a stable, SSR-safe unique ID.                                                                                                                                                                                                  |
| Bits Config     | `bits-config`       | Context provider for setting shared defaults (e.g. `Portal` target, default locale) across every Bits UI component in a subtree.                                                                                                         |
| isUsingKeyboard | `is-using-keyboard` | Reactive read of whether the user is currently navigating by keyboard, for focus-visible-style styling decisions.                                                                                                                        |

## Type helpers

Not components — TypeScript utilities for building your own wrapper
components (see SKILL.md's "Wrap primitives into your own components").
Docs at `https://bits-ui.com/docs/type-helpers/<slug>/llms.txt`.

| Type helper            | Slug                        | What it's for                                                                                                                 |
| ---------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| WithElementRef         | `with-element-ref`          | Adds a typed, bindable `ref` prop to a fully custom component, matching Bits UI's own convention.                             |
| WithoutChild           | `without-child`             | Strips the `child` render-delegation prop from a part's props type — for wrappers that shouldn't expose render delegation.    |
| WithoutChildrenOrChild | `without-children-or-child` | Strips both `children` and `child` — the type to reach for by default when wrapping a `Root`/`Content` in your own component. |
| WithoutChildren        | `without-children`          | Strips just `children` from a props type.                                                                                     |
