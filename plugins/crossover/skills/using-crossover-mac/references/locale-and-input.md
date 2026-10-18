# Language, locale, and keyboard

Source: the [CodeWeavers Mac knowledge base](https://support.codeweavers.com/en_US/mac-knowledge-base), fetched 2026-10-17. Several of these articles use older macOS pane names (*System Preferences*, *International*, *Language & Text*). On current macOS they are under **System Settings > General > Language & Region**.

## Contents

- [A Windows application in a different language](#a-windows-application-in-a-different-language)
- [CrossOver's own interface language](#crossovers-own-interface-language)
- [Wrong date or number format](#wrong-date-or-number-format)
- [Keys that type nothing in a non-English locale](#keys-that-type-nothing-in-a-non-english-locale)
- [Option as Alt, Command as Ctrl](#option-as-alt-command-as-ctrl)

## A Windows application in a different language

[Set a Windows application's language](https://support.codeweavers.com/en_US/languagelocale-settings/set-windows-application-to-use-a-different-language-than-the-os-default). By default a bottle takes its language and formats from macOS. To override one bottle:

1. **Open C: Drive**, go up one level, and open `cxbottle.conf` (it sits beside `drive_c`).
2. Under `[EnvironmentVariables]` (the section already exists in a new bottle, *measured*), add:
   ```ini
   "LC_ALL" = "ru_RU.UTF-8"
   ```

Only locales present in macOS's legacy locale set work: `af_ZA am_ET be_BY bg_BG ca_ES cs_CZ da_DK de_AT de_CH de_DE el_GR en_AU en_CA en_GB en_IE en_NZ en_US es_ES et_EE eu_ES fi_FI fr_BE fr_CA fr_CH fr_FR he_IL hr_HR hu_HU hy_AM is_IS it_CH it_IT ja_JP kk_KZ ko_KR lt_LT nl_BE nl_NL no_NO pl_PL pt_BR pt_PT ro_RO ru_RU sk_SK sl_SI sr_YU sv_SE tr_TR uk_UA zh_CN zh_HK zh_TW`. The KB says others, such as `es_MX` and `es_GT`, "will not work at present".

## CrossOver's own interface language

- [Set CrossOver's language](https://support.codeweavers.com/en_US/languagelocale-settings/how-to-set-crossover-to-use-a-different-language-than-the-os): **Language & Region** → **Applications** → **+** → **CrossOver** → choose the language → **Add**, then relaunch CrossOver. Repeat to switch back.
- [CrossOver is in a different language](https://support.codeweavers.com/en_US/languagelocale-settings/crossover-is-in-a-different-language): check the order of the preferred languages. CrossOver recognises **English** but not "British English" or "American English". For an English interface, plain **English** must be first, or second directly under a regional English.

## Wrong date or number format

[Why is my date format wrong?](https://support.codeweavers.com/en_US/languagelocale-settings/why-is-my-date-format-wrong)

- CrossOver follows the macOS **Region** preset. If the formats were customised by hand, it "will probably not" follow them. Choose a preset region instead.
- Some Windows applications ignore the formats and follow the system's primary language. Make sure the language list includes the regional variant at the top, for example **Australian English** rather than plain English.
- To set the formats inside the bottle: regedit → `HKEY_CURRENT_USER\Control Panel\International`.

## Keys that type nothing in a non-English locale

[Typing non-English keyboard characters](https://support.codeweavers.com/en_US/languagelocale-settings/i-am-in-a-non-english-locale-and-some-characters-on-my-keyboard-do-not-produce-characters-in-windows-applications-can-this-problem-be-solved). This happens in locales with no direct Mac-to-CrossOver mapping; the KB names Hungarian and Norwegian "among others". Fixes, in the KB's order:

1. Set **Region** to the matching country, so that location and language form a matched pair (for example Hungary with Hungarian).
2. Launch CrossOver from Terminal with the locale each time:
   ```bash
   LC_ALL=hu_HU.UTF-8 /Applications/CrossOver.app/Contents/MacOS/CrossOver &
   ```
3. The KB's permanent option, `defaults write ~/.MacOSX/environment LC_ALL hu_HU.UTF-8` followed by logging out, uses a legacy macOS mechanism that current macOS may ignore. Prefer the per-bottle `LC_ALL` in `cxbottle.conf` above, which needs nothing outside the bottle.

## Option as Alt, Command as Ctrl

[Remap the Option key to be the Alt key](https://support.codeweavers.com/en_US/miscellanous/Remap%20the%20Option%20key%20to%20be%20the%20Alt%20key). By default CrossOver maps **Command** to Windows **Alt**. To change that for one bottle, set these strings under `HKEY_CURRENT_USER\Software\Wine\Mac Driver`:

| Effect | Values |
|---|---|
| Option acts as Alt | `LeftOptionIsAlt` = `Y`, `RightOptionIsAlt` = `Y` |
| Command acts as Ctrl | `LeftCommandIsCtrl` = `Y`, `RightCommandIsCtrl` = `Y` |

The KB route is **Run Command** → `regedit` → **Registry > Import Registry File** → `OptionIsAlt.reg` (or `CommandIsCtrl.reg`) from `Y:\Downloads`. It also accepts setting the values by hand. Every application in the bottle gets the new mapping. *Command line (measured):*

```bash
for v in LeftOptionIsAlt RightOptionIsAlt; do
  "$CX/wine" --bottle NAME --no-gui --cx-app reg.exe add 'HKCU\Software\Wine\Mac Driver' /v "$v" /t REG_SZ /d Y /f
done
```
