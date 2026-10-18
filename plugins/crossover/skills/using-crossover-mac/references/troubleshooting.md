# Troubleshooting

Source: the [CodeWeavers Mac knowledge base](https://support.codeweavers.com/en_US/mac-knowledge-base), fetched 2026-10-17. Each section links its article. *Measured* marks behaviour observed on CrossOver 25.1.1 rather than stated by the KB.

## Contents

- [An unlisted application will not run](#an-unlisted-application-will-not-run)
- [Wine Configuration](#wine-configuration)
- [Debug logs](#debug-logs)
- [Antivirus](#antivirus)
- [macOS file-access prompts](#macos-file-access-prompts)
- [Display: DPI and window decorations](#display-dpi-and-window-decorations)
- [Disc not detected and disc DRM](#disc-not-detected-and-disc-drm)
- [What CodeWeavers will not support](#what-codeweavers-will-not-support)

## An unlisted application will not run

[Troubleshooting unlisted applications](https://support.codeweavers.com/en_US/troubleshooting/troubleshooting-unlisted-applications-cxmac). An unlisted application has no CrossTie, so "CrossOver does not default any install details" for it. Work in this order:

1. **The [compatibility database](https://www.codeweavers.com/compatibility).** User comments, the Tips section, and the forums. Required registry keys are "often specified in the app entry".
2. **Dependencies — the Kitchen Sink.** Many unlisted applications fail for want of a Windows dependency. Download [The-Kitchen-Sink.cxarchive](https://www.codeweavers.com/xfer/Dependency_archive/The-Kitchen-Sink.cxarchive) (unlock code `demo`), then **Bottle > Import Bottle Archive**. Select the imported bottle → **Install Application into Bottle** → **Install an Unlisted Application** → choose the installer → **Install**. If it works, you still will not know which dependency mattered. If you already know the dependency, install only that.
3. **Advanced Settings** for the version in use (`advanced-settings.md`).
4. **Wine Configuration** (next section).
5. **Registry edits** — [Editing bottle registry keys](https://support.codeweavers.com/en_US/common-actions/editing-bottle-registry-keys) and WineHQ's [Useful Registry Keys](https://wiki.winehq.org/Useful_Registry_Keys). The KB's worked example is `HKEY_CURRENT_USER\Software\Wine\Direct3D`, string `renderer` = `vulkan`. In regedit: **Run Command** → `regedit` → navigate → **New > String Value** → name it → set the data. The key lives in the bottle, so it affects every application there.
6. **A debug log**, read for the missing DLLs or frameworks named in its errors.

## Wine Configuration

Select the bottle → **Control Panels** → **Wine Configuration** (*command line:* `"$CX/wine" --bottle NAME --cx-app winecfg.exe`). The KB warns that "incorrect setting changes may permanently damage the bottle" — archive first.

- **Libraries tab — DLL overrides.** CrossOver uses Wine's builtin DLLs by default. Edit an existing override (select it, then **Edit**) and choose **Native** (the Windows DLL) or **Builtin** (Wine's). To add one, type the name under **New override for library** and click **Add**, for example a DLL the application installed itself.
- **Drives tab.** `C:`, `Y:`, and `Z:` exist by default, and mounted volumes get letters automatically. A copy-protected disc may need to be mounted as `D:` before the program runs: **Add** → `D:` → the disc.
- **Applications tab — Windows version.** [Change the Windows version](https://support.codeweavers.com/en_US/miscellanous/change-the-windows-version-of-an-existing-bottle): choose the version from the dropdown → **OK**. This is the quick fix. The better fix is a new bottle of the right type, because "the application installer may set different registry keys based on that Windows version".

## Debug logs

The KB documents exactly one channel set: `+seh,+tid`. Other Wine channels exist, but the KB names none, and CodeWeavers support works from logs taken with this set.

**Running an installed program** — [Creating a debug log](https://support.codeweavers.com/en_US/troubleshooting/creating-a-debug-log):

1. Select the bottle, then the program's launcher.
2. **Run with Options** → **Create log file**.
3. Enter the channels in **Wine logging channels**, or pick them from the **+** menu. **Change** sets the save location.
4. **Run**, reproduce the problem, then close the program **and** the Run Command dialog.
5. The log is a `.cxlog` file. To send it to support, right-click → **Compress**.

**During an install** — [Debug log during installation](https://support.codeweavers.com/en_US/troubleshooting/creating-a-debug-log-during-install). Set this up before clicking **Install**:

1. The dropdown beside **Install** → **Advanced Options**.
2. Turn on **Create log file** and enter `+seh,+tid`.
3. The log path is shown in the **Log file** field. Click **Change** to move it, or **Done**.
4. **Install**.

**From the command line (measured):**

```bash
"$CX/wine" --bottle NAME --no-gui --cx-log ~/Desktop/NAME.cxlog --debugmsg +seh,+tid 'C:\Program Files\App\app.exe'
```

`--cx-log` overrides `$CX_LOG`, and `--debugmsg` overrides `$CX_DEBUGMSG`. A name ending `.gz` or `.bz2` compresses on the fly. The log starts with a `** <date>` header and a `Starting '…wineloader' …` line naming the command. After that, lines read `TID:class:channel:function message` (for example `00b4:err:hid:…`). If the program itself cannot be found, no log is written; the error goes to stderr.

**Reading it.** Delegate to the `crossover-log-triage` agent, giving it the log path and what the user did. A clean `cmd /c ver` on 25.1.1 already logs `err:hid` lines, a `winebth` driver failure, and a MoltenVK capability dump of over 100 lines. None of those is the problem, and reading the log inline spends the conversation on them.

## Antivirus

[CrossOver and antivirus software](https://support.codeweavers.com/en_US/troubleshooting/antivirus-software-eg-bitdefender-avast-and-avg-and-crossover). Antivirus "will often incorrectly flag and delete CrossOver files", because they look like Windows files. The symptom is errors while installing Windows applications.

1. If CrossOver is already damaged, remove it completely first (`bottles-and-applications.md` → *Deleting an application or CrossOver*).
2. Disable the antivirus, install CrossOver, add exceptions for `~/Applications/CrossOver`, `~/Library/Application Support/CrossOver`, and `/Applications/CrossOver.app` (adjust the last if the app was renamed), then re-enable it. If it cannot be disabled, add the exceptions before installing.
3. Avast needs the exceptions "in multiple places". The KB links vendor instructions for Bitdefender, Avast, AVG, Avira, and Norton, and encourages reporting the false positive to the vendor.

## macOS file-access prompts

[Grant CrossOver file system access](https://support.codeweavers.com/en_US/troubleshooting/grant-crossover-file-system-access). "It's safe to allow access." To grant it ahead of time, or after declining by mistake:

- macOS 13 and later: **System Settings > Privacy & Security > Files and Folders** → expand **CrossOver** → turn on the folders.
- macOS 10.15–12: **System Preferences > Security & Privacy > Privacy > Files and Folders** → check the folders under CrossOver.

## Display: DPI and window decorations

- [Reset the DPI](https://support.codeweavers.com/en_US/sound-video/reset-the-dpi-using-wine-configuration). A DPI set too high makes Wine Configuration too large to use. Open it, click the **Graphics** tab, press **Tab** five times, type `96`, press **Enter**. The DPI applies to every program in the bottle. (High Resolution Mode, which reports 192 DPI, is a separate Advanced Setting.)
- [Disable window decorations](https://support.codeweavers.com/en_US/sound-video/disable-window-decorations-in-the-mac-driver). Wine's trimming of window edges in favour of native ones is imperfect, and winecfg cannot change it. Set `HKEY_CURRENT_USER\Software\Wine\Mac Driver`, string `Decorated` = `N`, in regedit or with `reg.exe add 'HKCU\Software\Wine\Mac Driver' /v Decorated /t REG_SZ /d N /f`.

## Disc not detected and disc DRM

[CD/DVD not detected](https://support.codeweavers.com/en_US/installation-issues/my-cd-is-in-the-drive-and-the-game-doesnt-see-it). Disc DRM comes in two kinds:

- **Filesystem-based** checks ("the correct disc is in the drive"): these usually work. Mapping the disc to `D:` may be needed.
- **Mechanical "dwell angular"** checks: these "will never work on the Mac", because macOS does not give raw access to the optical drive.

The game may run fine apart from the DRM. Sometimes an official developer patch removes it. Circumventing DRM is illegal in most countries, so do not suggest it. CodeWeavers recommends buying digital, non-disc releases.

## What CodeWeavers will not support

Say these plainly. Do not invent a workaround the KB does not give.

| Area | Position | Article |
|---|---|---|
| Logs for unlisted applications | "Our support staff will not examine unsolicited logs for an unlisted application." | [Unlisted applications](https://support.codeweavers.com/en_US/troubleshooting/troubleshooting-unlisted-applications-cxmac) |
| USB devices | "Our support team is unable to troubleshoot USB devices"; serial devices have a workaround (`games-and-devices.md`) | [USB devices](https://support.codeweavers.com/en_US/troubleshooting/using-usb-devices-with-crossover) |
| Two CrossOver versions | "Entirely unsupported" | [Multiple versions](https://support.codeweavers.com/en_US/installation-issues/install-and-use-multiple-versions-of-crossover-on-mac) |
| Anti-cheat | Never worked around; only the game developer can change it | [Anti-cheat](https://support.codeweavers.com/en_US/miscellanous/anti-cheat) |
| Modded games | Testing and support cover only the base game | [Mods](https://support.codeweavers.com/en_US/miscellanous/mods-and-add-ons-with-crossover) |
| The Windows command prompt | "Almost any action you'd want to take within will be unsupported" | [Command prompt](https://support.codeweavers.com/en_US/miscellanous/use-the-windows-command-prompt-in-crossover) |

For a supported problem that remains, the KB offers [contact](https://www.codeweavers.com/contact-us) and a [TeamViewer QuickSupport session](https://support.codeweavers.com/en_US/mac-knowledge-base/screensharing-download). That session grants TeamViewer Screen Recording and Accessibility permissions, and the ID and password change each launch.
