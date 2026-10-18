---
name: using-crossover-mac
description: Runs and troubleshoots Windows applications and games on a Mac with CodeWeavers CrossOver — bottles and their virtual C drives, installing listed and unlisted applications, launchers, the cxbottle/cxstart/wine command line, registry and Wine Configuration changes, Advanced Settings per CrossOver version (D3DMetal, DXMT, DXVK, wined3d, ESync, MSync, DLSS, High Resolution Mode), archiving and restoring bottles, debug logs, language, locale and keyboard fixes, and controllers, USB devices, anti-cheat and mods. Use when the user mentions CrossOver, CodeWeavers, a bottle, a .cxarchive or .cxlog file, CrossTie, or running a Windows .exe on macOS without a virtual machine. Also use for symptoms that point at CrossOver without naming it - a Windows program on a Mac that will not launch, installs with no icon, says its bottle expired, shows the wrong language or date format, ignores the Option key or a gamepad, renders too large or with broken window edges, or a game that crashes after a graphics setting change.
license: MIT
---

# Using CrossOver on a Mac

CrossOver is CodeWeavers' commercial build of Wine. It runs Windows programs directly on macOS, with no Windows licence or virtual machine. The unit of everything is the **bottle**: a self-contained Windows environment (a C: drive, a registry, a Windows version, graphics and sync settings) that one or more applications are installed into. Most CrossOver problems are solved per bottle, and most irreversible mistakes are made per bottle too.

Scope: CrossOver Mac. Parallels, VMware, and Boot Camp run real Windows and none of this applies. Plain Wine, Whisky, and Apple's Game Porting Toolkit share the engine but not CrossOver's tools, paths, or settings. Source: the [CodeWeavers Mac knowledge base](https://support.codeweavers.com/en_US/mac-knowledge-base), with command-line behaviour measured on CrossOver 25.1.1.

## Establish three facts first

1. **The CrossOver version.** Advanced Settings differ between 23.7–24, 25, and 26. Do not describe a setting before you know which one the user has.
   ```bash
   defaults read /Applications/CrossOver.app/Contents/Info.plist CFBundleShortVersionString
   ```
2. **The bottles, and which application lives in which.** Bottles live in `~/Library/Application Support/CrossOver/Bottles` by default, in `/Library/Application Support/CrossOver/Bottles` when published, or wherever `BottleDir` or `CX_BOTTLE_PATH` moved them (`references/bottles-and-applications.md` → *Where bottles live*). A directory with a `cxbottle.conf` is a bottle; its `Template` line gives the Windows version.
3. **What the compatibility database says.** Check [codeweavers.com/compatibility](https://www.codeweavers.com/compatibility) for the application before trying fixes. The rating, user comments, and Tips often name the exact setting or registry key. CodeWeavers puts this step first for every unlisted application.

## The command line

The tools ship inside the app. The KB reaches them through **Open Shell** (Option + right-click a bottle). The full path works from any shell without it:

```bash
CX="/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin"
```

| Task | Command |
|---|---|
| Run a program in a bottle | `"$CX/wine" --bottle NAME ~/Downloads/setup.exe` — a Mac path, a Windows path (`'C:\Program Files\App\app.exe'`), or a bare name (`winword.exe`). The KB's `--cx-app` form takes only the last two: given a Mac path it fails with "could not find … Is it installed?" (measured) |
| Open a document with its Windows association | `"$CX/cxstart" --bottle NAME ~/file.docx` |
| A Windows command | `"$CX/wine" --bottle NAME --no-gui --cx-app cmd.exe /c ver` |
| Read or set a registry value | `"$CX/wine" --bottle NAME --no-gui --cx-app reg.exe query 'HKCU\Software\Wine\Mac Driver'` — or `reg.exe add … /v NAME /t REG_SZ /d VALUE /f`, or `reg.exe import ~/file.reg` |
| Registry editor or Wine Configuration (opens a window) | `--cx-app regedit.exe`, `--cx-app winecfg.exe` |
| Bottle status | `"$CX/cxbottle" --bottle NAME --status` |
| Create a bottle | `"$CX/cxbottle" --bottle NAME --create --template win10_64` |
| Archive / restore / copy | `--tar ~/NAME.cxarchive` · `--restore FILE.cxarchive` · `--bottle NEW --copy NAME` |
| Debug log | add `--cx-log ~/Desktop/NAME.cxlog --debugmsg +seh,+tid` to a `wine` or `cxstart` call |
| Version | `"$CX/cxstart" --version` |

Templates on 25.1.1: `win98 win2000 winxp winxp_64 winvista winvista_64 win7 win7_64 win8 win8_64 win10 win10_64 win11_64` (the list is in `…/CrossOver/share/crossover/bottle_templates`). Use `--no-gui` for anything run without the user watching: without it, an error opens a dialog that blocks the call. `CX_BOTTLE_PATH=/some/dir` before a command points it at a different bottle folder, which keeps a test bottle away from the user's real ones.

## Before changing a bottle

- **Archive first.** `cxbottle --bottle NAME --tar ~/NAME.cxarchive`, or **Bottle > Export to Archive**. Do this before Wine Configuration changes (the KB warns they "may permanently damage the bottle"), a Windows-version change, a second CrossOver version, the Removal Tool, or anything you are unsure of. A bottle has no other undo.
- **Removing an application means deleting its bottle.** The KB states that removing one app safely while keeping the bottle "is impossible". Confirm with the user, archive, then `cxbottle --bottle NAME --uninstall` (removes its menus and associations) followed by `--delete`. Without a terminal, `--delete` skips its own confirmation and deletes at once (measured); this plugin's guard asks the user instead.
- **One application per bottle.** Registry settings and Advanced Settings apply to every application in a bottle. A fix for one program can break another.
- **Change the registry through Wine, never by editing `system.reg` or `user.reg`.** Wine writes the registry files lazily, after the call returns, so an edit to the file can be overwritten. Deleting `system.reg` makes the bottle unable to start (measured). Use `reg.exe` or `regedit`.
- **Prefer a new bottle to a changed Windows version.** The KB says installers write different registry keys per Windows version, so reinstalling into a bottle created with the right template beats changing an existing one in Wine Configuration.
- **Advanced Settings have no documented config keys.** The KB describes them only as UI toggles. To learn what a toggle wrote, copy `cxbottle.conf`, toggle the setting, and diff the two files. Do not guess key names.

## Troubleshooting order

The KB's own order for an application that will not run:

1. The compatibility database entry: rating, Tips, and comments.
2. Listed application (it has a CrossTie)? Reinstall through **Install** so the recipe applies. Unlisted? Try the Kitchen Sink dependency archive (`references/troubleshooting.md`).
3. Advanced Settings for the user's version: graphics backend first, then synchronization, then High Resolution Mode (`references/advanced-settings.md`).
4. Wine Configuration: DLL overrides, drives, Windows version. Archive first.
5. A debug log with `+seh,+tid`. Hand the `.cxlog` to the **crossover-log-triage** agent rather than reading it here: logs run to hundreds of megabytes, and most of each one is noise.

State support boundaries plainly instead of inventing workarounds. Per the KB, CodeWeavers does **not** examine unsolicited logs for unlisted applications, troubleshoot USB devices, support modded games, or support running two CrossOver versions. Nothing makes game **anti-cheat** or mechanical "dwell angular" disc DRM work. Do not suggest bypassing either; CodeWeavers cites the DMCA.

## Where to look

Read at most the file the question touches.

- `references/bottles-and-applications.md` — installing CrossOver and applications, launchers, the C: drive and drive letters, where bottles live and how to move them, archiving, deleting, published bottles and bottle hooks, multiple versions, expired bottles, missing icons, printing, the installer cache, and the Windows command prompt.
- `references/troubleshooting.md` — unlisted applications and the Kitchen Sink, Wine Configuration (DLL overrides, drives, Windows version), debug logs in the GUI and during install, antivirus, macOS file-access prompts, DPI, window decorations, and disc DRM.
- `references/advanced-settings.md` — every Advanced Setting in 23.7–24, 25, and 26, what each does, and what changed between versions.
- `references/locale-and-input.md` — application language and `LC_ALL`, CrossOver's interface language, date formats, non-English keyboard characters, and mapping Option to Alt or Command to Ctrl.
- `references/games-and-devices.md` — controllers, USB serial devices, Heroic for Epic and GOG, DLSS, anti-cheat, and mods.

## Corrections to carry into every answer

- **CrossOver needs no Windows licence and installs no Windows.** Telling the user to "install Windows drivers" is wrong: the KB says native Windows drivers cannot be installed because there is no Windows underneath.
- **Drive letters are links, not partitions.** `C:` is the bottle's `drive_c`, `Y:` is the home folder, `Z:` is `/`. They are symlinks in the bottle's `dosdevices` folder. An "expired bottle" on a valid licence is usually a missing `z:` link.
- **The KB names menus from several macOS and CrossOver eras.** *Preferences* became *Settings* by CrossOver 24, and *System Preferences > International* is today's *System Settings > General > Language & Region*. Translate to what the user's version shows.
- **One KB command is misprinted.** The fix for missing icons prints `sudo chown -R \`id -un\`:\`id -gn\` ~ chmod -R u+w ~` as one line. Present it as two commands, `sudo chown -R "$(id -un)":"$(id -gn)" ~` then `chmod -R u+w ~`. Say they act on the whole home folder, and ask before running either.
