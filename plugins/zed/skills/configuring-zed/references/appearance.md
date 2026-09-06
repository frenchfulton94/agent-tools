# Appearance

Live docs: overview `https://zed.dev/docs/appearance.md` · themes `https://zed.dev/docs/themes.md` · icon themes `https://zed.dev/docs/icon-themes.md` · every visual setting with its current default `https://zed.dev/docs/visual-customization.md`. Theme and icon-theme _names_ come from the installed extensions, so read them from the selectors rather than assuming a theme is installed.

Contents:

- [Themes](#themes)
- [Theme overrides](#theme-overrides)
- [Local themes](#local-themes)
- [Fonts](#fonts)
- [UI chrome](#ui-chrome)
- [Settings profiles](#settings-profiles)

## Themes

`theme` and `icon_theme` each accept either a name or a mode object:

```json
{
	"theme": { "mode": "system", "light": "One Light", "dark": "One Dark" },
	"icon_theme": { "mode": "system", "light": "Zed (Default)", "dark": "Zed (Default)" }
}
```

`mode` is `"system"`, `"light"`, or `"dark"`. `theme selector: toggle` (`cmd-k cmd-t`) previews themes live and writes the choice to settings; `icon theme selector: toggle` does the same for icons. `cmd-k cmd-shift-t` flips light/dark — the first flip converts a bare string `theme` into the object form with default light and dark values, which then need setting to the user's actual pair.

More themes install as extensions (`zed: extensions`, or the gallery at `https://zed.dev/extensions?filter=themes`). Since these are app-level settings, they only work in user settings, not `.zed/settings.json`.

## Theme overrides

`theme_overrides` patches a named theme without forking it — UI colors at the top level, syntax captures under `syntax`, and the indent/bracket rainbow palette under `accents`:

```json
{
	"theme_overrides": {
		"One Dark": {
			"editor.background": "#333",
			"syntax": {
				"comment": { "font_style": "italic" },
				"string": { "color": "#00AA00" }
			},
			"accents": ["#ff0000", "#ff7f00", "#ffff00"]
		}
	}
}
```

The key must match the theme name exactly, and overrides apply only while that theme is active — a light/dark pair needs an entry for each. Valid attribute names are whatever the theme's own JSON defines; the bundled One themes at `assets/themes/one/one.json` in the Zed repo are the readable example. Syntax capture names (`comment`, `comment.doc`, `string`, `function`, …) are listed under syntax highlighting in `https://zed.dev/docs/extensions/languages.md`.

`accents` feeds `indent_guides.coloring: "indent_aware"` and `colorize_brackets`, both off by default.

## Local themes

A theme JSON dropped into `~/.config/zed/themes/` (Windows: `%APPDATA%\Zed\themes\`) appears in the theme selector after a reload — no extension packaging needed. The Theme Builder at `https://zed.dev/theme-builder` produces that JSON from an existing theme. Packaging one for distribution is a different path: `https://zed.dev/docs/extensions/themes.md`.

## Fonts

Four independent font surfaces, so "change the font" usually means more than one key:

| Surface        | Settings                                                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Editor buffers | `buffer_font_family`, `buffer_font_size`, `buffer_font_weight`, `buffer_line_height`, `buffer_font_features`, `buffer_font_fallbacks` |
| Interface      | `ui_font_family`, `ui_font_size`, `ui_font_weight`, `ui_font_features`, `ui_font_fallbacks`                                           |
| Terminal       | `terminal.font_family`, `terminal.font_size`, `terminal.line_height`                                                                  |
| Agent panel    | `agent_ui_font_size`, `agent_buffer_font_size`                                                                                        |

Two sentinel values are worth knowing: `".ZedMono"` and `".ZedSans"` select the bundled fonts, and `".SystemUIFont"` selects the platform UI font. Line heights take `"comfortable"`, `"standard"`, or `{ "custom": 1.5 }`.

Ligatures are an OpenType feature, so they're disabled per surface rather than by a dedicated setting:

```json
{ "buffer_font_features": { "calt": false, "cv01": 7 } }
```

Font features and fallbacks apply on macOS and Windows.

## UI chrome

Nearly every visible element has a settings block, and the current keys and defaults are best read from `https://zed.dev/docs/visual-customization.md` rather than recalled. The groups worth knowing by name when translating a request:

`tab_bar` and `tabs` (tab strip, close buttons, file icons, git status) · `toolbar` (breadcrumbs, quick actions) · `status_bar` and the `button` key inside each panel's block (status-bar icons) · `title_bar` · `scrollbar` and `minimap` · `gutter` and `relative_line_numbers` · `indent_guides` · `show_whitespaces` with `whitespace_map` · `soft_wrap`, `wrap_guides`, `show_wrap_guides` · `cursor_shape`, `cursor_blink`, `current_line_highlight` · `git.inline_blame` · panel blocks `project_panel`, `outline_panel`, `git_panel`, `terminal`, `agent`, `debugger`, `collaboration_panel`, each with `dock`, `default_width`/`default_height`, and `button` · workspace-level `active_pane_modifiers`, `bottom_dock_layout`, `centered_layout`, `resize_all_panels_in_dock`.

Panel visibility is a runtime toggle, not a setting: the `button` keys only control the status-bar icons.

## Settings profiles

`profiles` defines named settings bundles applied temporarily from `settings profile selector: toggle` — useful for presenting, screenshots, or a distraction-free writing mode:

```json
{
	"profiles": {
		"Presenting": {
			"settings": { "buffer_font_size": 20, "ui_font_size": 18, "theme": "One Light" }
		},
		"Writing": {
			"settings": { "tab_bar": { "show": false }, "toolbar": { "breadcrumbs": false } }
		},
		"Clean Slate": { "base": "default", "settings": { "theme": "Ayu Dark" } }
	}
}
```

`base` is `"user"` (layer on the user's settings, the default) or `"default"` (ignore user customizations and layer on Zed's defaults).
