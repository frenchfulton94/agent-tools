# Bottles and applications

Source: the [CodeWeavers Mac knowledge base](https://support.codeweavers.com/en_US/mac-knowledge-base), fetched 2026-10-17. Each section links its article. Command-line equivalents marked *measured* were run on CrossOver 25.1.1; everything else is the KB's GUI procedure.

## Contents

- [Installing CrossOver](#installing-crossover)
- [Installing an application](#installing-an-application)
- [Running an .exe and creating a launcher](#running-an-exe-and-creating-a-launcher)
- [The C: drive and drive letters](#the-c-drive-and-drive-letters)
- [Where bottles live](#where-bottles-live)
- [Archiving and restoring](#archiving-and-restoring)
- [Deleting an application or CrossOver](#deleting-an-application-or-crossover)
- [Published bottles and bottle hooks](#published-bottles-and-bottle-hooks)
- [Running two CrossOver versions](#running-two-crossover-versions)
- [Expired bottle](#expired-bottle)
- [Icons not created after install](#icons-not-created-after-install)
- [Terminal and the Windows command prompt](#terminal-and-the-windows-command-prompt)
- [Printing](#printing)
- [Installer cache and user agent](#installer-cache-and-user-agent)
- [Hybrid Windows/Mac discs and mapped drives](#hybrid-windowsmac-discs-and-mapped-drives)

## Installing CrossOver

[Installing CrossOver Mac](https://support.codeweavers.com/en_US/getting-started/installing-crossover)

1. Download from the account's **My Downloads**, or the 14-day fully functional trial.
2. Open the download (unzip if it arrives as a `.zip`) and choose **Move to Applications Folder** when CrossOver offers.
3. Register: **Try Now** (trial), **Unlock with Purchase Info** (account email and password), or **Enter an Activation Code** (third-party purchase). After a trial, **CrossOver > Unlock CrossOver**.

If antivirus software is installed, add its exceptions before installing (`troubleshooting.md` → *Antivirus*).

## Installing an application

**Listed** applications have a CrossTie, an install recipe in CrossOver's database. [Installing a listed application](https://support.codeweavers.com/en_US/getting-started/installing-a-listed-application):

1. **Install**, search for the application, click its tile.
2. If CrossOver cannot download the installer itself, **Edit** → browse to it → **Choose Installer**.
3. **Install**. CrossOver creates the bottle and runs the installer. Defaults are usually right. **Restart Now** inside a Windows installer does not reboot the Mac.

**Unlisted** applications have no recipe and "may not run correctly or at all". [Installing an unlisted application](https://support.codeweavers.com/en_US/getting-started/installing-an-unlisted-application):

1. **Install** → **Install an Unlisted Application** (top right).
2. **Edit** → choose the installer → **Choose Installer**.
3. **Edit** for the bottle → name it and pick a bottle type → **Done**.
4. **Install**. If no launcher appears afterwards, create one (next section).

*Command line (measured):* create the bottle, then run the installer in it.

```bash
"$CX/cxbottle" --bottle MyApp --create --template win10_64 --description "MyApp"
"$CX/wine" --bottle MyApp ~/Downloads/setup.exe
```

## Running an .exe and creating a launcher

[Launching a Windows .exe](https://support.codeweavers.com/en_US/common-actions/launching-a-windows-exe-file-cxmac) · [Creating a launcher](https://support.codeweavers.com/en_US/common-actions/creating-a-launcher-for-a-windows-application)

- Portable programs need no install: **Bottle > New Bottle** (name, type, **Create**), select the bottle, **Run Command** → **Browse** → the `.exe` → **Run**.
- Install finished but no icon: select the bottle → **Run Command** → **Browse** (opens the C: drive; start in `Program Files`) → the `.exe` → **Run** to test it → **Save Command as a Launcher**. With several `.exe` files, expect trial and error.

## The C: drive and drive letters

[Opening a bottle's C: drive](https://support.codeweavers.com/en_US/common-actions/opening-a-bottles-c-drive) · [Browsing files](https://support.codeweavers.com/en_US/common-actions/browsing-files-in-a-windows-application)

- **Bottle Actions > Open C: Drive** opens it in Finder. `Program Files` holds applications, `ProgramData` CrossOver-specific data, `Users` links to the home folder, `Windows` registry files and system settings.
- Every bottle gets three letters: `C:` = the bottle, `Y:` = the Mac home folder, `Z:` = `/` (external drives under `Z:\Volumes`). In a Windows file dialog, **Documents** and **Desktop** are the Mac's own.
- *Measured:* the letters are symlinks in `<bottle>/dosdevices` — `c: -> ../drive_c`, `y: -> $HOME`, `z: -> /`.

## Where bottles live

[Change where CrossOver stores bottles](https://support.codeweavers.com/en_US/common-actions/change-the-bottle-directory-in-crossover-mac) · [Advanced configuration](https://support.codeweavers.com/en_US/troubleshooting/advanced-crossover-mac-configuration)

| Location | How it is set |
|---|---|
| `~/Library/Application Support/CrossOver/Bottles` | The default, per user |
| `/Library/Application Support/CrossOver/Bottles` | Published bottles, shared by all users |
| Any folder | **CrossOver > Settings > System Integration > Bottle Folder** (CrossOver 24+; **Reset** reverts) |
| Any folder | `defaults write com.codeweavers.CrossOver BottleDir /path` (undo with `defaults delete com.codeweavers.CrossOver BottleDir`; CrossOver Games uses `com.codeweavers.CrossOverGames`) |
| Published bottles elsewhere | `defaults write com.codeweavers.CrossOver ManagedBottleDirs /path` |
| One or more folders | In the app bundle's `Contents/SharedSupport/CrossOver/etc/CrossOver.conf`, under `[EnvironmentVariables]`: `"CX_BOTTLE_PATH"="/Users/${USER}/Bottles"`. Colon-separate several; new bottles go in the first |

Caveats from the KB:

- An external bottle drive must be APFS or macOS Extended (Journaled), "otherwise you risk bottle corruption".
- Never point `BottleDir` at the published-bottle folder, and never at a network volume ("significant performance issues").
- Changing the setting does not move existing bottles. Move them yourself, or archive and restore.
- `CX_BOTTLE_PATH` for all users at once is described as a CrossOver Mac Pro feature. Editing the app bundle's conf also invalidates its signature (`Running two CrossOver versions`) and may be lost when CrossOver updates.
- *Measured:* `CX_BOTTLE_PATH=/dir` in the environment of a single command overrides the folder for that command only.

## Archiving and restoring

[Archiving and restoring a bottle](https://support.codeweavers.com/en_US/common-actions/archiving-and-restoring-a-bottle)

- Archive: select the bottle → **Bottle > Export 'NAME' to Archive** → **Save**. Produces a `.cxarchive`.
- Restore: **Bottle > Import Bottle Archive** → the `.cxarchive` → **Restore**.
- *Command line (measured):* `"$CX/cxbottle" --bottle NAME --tar ~/NAME.cxarchive` (a fresh win10_64 bottle took 24 s and 113 MB); restore with `--restore FILE.cxarchive`, which per `cxbottle --help` does not install menus — follow it with `--bottle NAME --install`.
- A bottle hook in the bottle's own `scripts.d` travels with the archive and runs on restore.

## Deleting an application or CrossOver

[Removing a Windows application](https://support.codeweavers.com/en_US/common-actions/deleting-a-windows-application) · [CrossOver Removal Tool](https://support.codeweavers.com/en_US/getting-started/using-the-crossover-removal-tool)

- **An application cannot be removed on its own.** The KB: "Removing an application safely from a bottle while keeping that bottle intact is impossible." Right-click the bottle → **Delete Bottle** → **Delete**. Irreversible. Archive first.
- *Command line:* `"$CX/cxbottle" --bottle NAME --uninstall` then `--delete`. `cxbottle --help` says to uninstall before deleting. Measured: without a terminal, `--delete` deletes at once even without `--force` — its confirmation prints "cxmessage standin was called." and the bottle is gone.
- **The Removal Tool deletes CrossOver, all of its files, and every bottle.** Archive each bottle worth keeping first. To run it: unzip `CrossOver_RemovalTool.zip`, then Control-click → **Open** past the security warning.
- Manual uninstall: trash `~/Library/Application Support/CrossOver` (this holds the default bottle folder), every `~/Library/Preferences/com.codeweavers*` file, `~/Applications/CrossOver` if present, and the app.

## Published bottles and bottle hooks

[Advanced CrossOver Mac configuration](https://support.codeweavers.com/en_US/troubleshooting/advanced-crossover-mac-configuration) — "Most users will not need" this.

- **Publish:** install into a new bottle, remove private data (cached passwords, user names), **Bottle > Publish Bottle**, keep the default name `published_NAME`, enter an admin password. Each user who opens it gets a *stub bottle* of the same name holding their customizations, with symlinks back to the published files. Changes reach users only after **Bottle > Update Published Bottle**.
- **Distribute:** copy the published bottle to the same path (`/Library/Application Support/CrossOver/Bottles`) on the other Mac and run CrossOver once. Copying `~/Library/Preferences/com.codeweavers.CrossOver.plist` copies preferences.
- **Drive label or serial:** Wine Configuration → **Drives** → select the letter → set label and serial → **Apply**. Or create `.windows-label` and `.windows-serial` text files in the folder's root.
- **Hooks:** executable shell scripts in `~/Library/Application Support/CrossOver/support/scripts.d` (all of one user's bottles) or `scripts.d` at the top of a bottle. They are named `nn.name`, where `nn` is two digits setting the order and `name` has no dot or tilde (for example `10.remap_drive`). They receive `CX_ROOT`, `CX_BOTTLE`, and `WINEPREFIX` (the bottle path). The first argument is the event: `create TEMPLATE`, `restore`, `upgrade-from OLD_VERSION` (runs after the upgrade), `pre-create-stub` / `create-stub PUBLISHED_PREFIX`, `pre-update-stub` / `update-stub PUBLISHED_PREFIX`. Template names are `win98 win2000 winxp winvista win7 win8 win10 win11`, with `_64` for 64-bit.

## Running two CrossOver versions

[Installing multiple versions](https://support.codeweavers.com/en_US/installation-issues/install-and-use-multiple-versions-of-crossover-on-mac) — "Setting this up is entirely unsupported."

1. Archive every working bottle. A newer version can alter a bottle so the older one cannot use it.
2. **Get Info** on the old app and rename it (for example `CrossOver8.app`); confirm it still launches.
3. Install the new version as `CrossOver.app`. Updates overwrite only that one.
4. In the **old** app's `Contents/SharedSupport/CrossOver/etc/CrossOver.conf`, under `[BottleDefaults]` / `[EnvironmentVariables]`, set `"CX_BOTTLE_PATH"="/Users/{USER}/Library/Application Support/CrossOver/OtherBottles"`, with `{USER}` replaced by the account name.
5. "The bundle's signature is no longer valid" → Control-click → **Open**.

## Expired bottle

[How to fix an expired bottle](https://support.codeweavers.com/en_US/miscellanous/fixing-an-expired-bottle)

1. **CrossOver > About CrossOver** for the version; compare with [your Downloads page](https://www.codeweavers.com/account/downloads).
2. Downloads lists an older version → the licence does not cover this one; a new licence is needed.
3. Downloads lists this version → the bottle has most likely lost its `Z:` link. Create any new bottle → **Open C: Drive** → **Column View** → `dosdevices` → copy `z/`. Paste it into the expired bottle's `dosdevices`. Delete the temporary bottle afterwards.
4. *Measured equivalent:* `z:` is a symlink to `/`, so `ln -s / "<bottle>/dosdevices/z:"` recreates it. Check with `ls -la "<bottle>/dosdevices"` first.

## Icons not created after install

[Application icons not created](https://support.codeweavers.com/en_US/miscellanous/application-icons-are-not-being-created-after-windows-programs-are-installed-in-crossover-mac) — the cause is wrong ownership or permissions on the home folder.

1. Fix ownership and permissions. The KB prints both commands run together on one line; they are two separate commands:
   ```bash
   sudo chown -R "$(id -un)":"$(id -gn)" ~
   chmod -R u+w ~
   ```
   Both act on the entire home folder. Explain that and get the user's approval before running them.
2. Then either recreate the bottles and reinstall, or keep them: **Programs > Run Command** → **Debug Options** → **Open Shell** → `cxassoc --bottle 'NAME' --install` for each bottle. The KB notes the first shell window can be misconfigured; close it and open a second.

## Terminal and the Windows command prompt

[Run a Windows app from Terminal](https://support.codeweavers.com/en_US/miscellanous/run-a-windows-app-from-terminal) · [Windows command prompt](https://support.codeweavers.com/en_US/miscellanous/use-the-windows-command-prompt-in-crossover)

- **Open Shell:** Control-click the bottle and hold **Option**; **Run Command** becomes **Open Shell**. It sets the environment and starts in the bottle's `drive_c`. Then `wine --cx-app winword.exe`, or `wine cmd` for a command prompt, where "almost any action … will be unsupported".
- The full tool path works without Open Shell (SKILL.md → *The command line*).

## Printing

[Printing with PDFwriter](https://support.codeweavers.com/en_US/miscellanous/printing-documents-from-applications-within-crossover) — when a print job does not translate to the Mac printer (more common with non-PostScript inkjets):

1. Install [RWTS-PDFwriter v3.1](https://github.com/rodyager/RWTS-PDFwriter/releases/download/v3.1/RWTS-PDFwriter.pkg); choose the PDF folder when asked (default: Documents).
2. Print to **PDFwriter** from the Windows application, then open the PDF in Preview and print it there.

## Installer cache and user agent

- [Clearing the installer cache](https://support.codeweavers.com/en_US/common-actions/clearing-crossovers-installer-cache): CrossOver keeps the installers it downloaded, including a corrupt one. **CrossOver > Preferences** (Settings in newer versions) → **Installer Assistant** → **Clear**, then reinstall.
- [Changing the browser user agent](https://support.codeweavers.com/en_US/common-actions/how-to-change-your-user-agent-on-mac): for sites that serve the Windows installer only to Windows browsers. Safari: **Advanced** → show the **Develop** menu → **Develop > User Agent**. Firefox: `about:config` → `general.useragent.override` (a String) set to a Windows user agent; **Reset** reverts.

## Hybrid Windows/Mac discs and mapped drives

[Mounting the Windows side of a hybrid disc](https://support.codeweavers.com/en_US/miscellanous/how-do-you-mount-the-windows-partition-of-a-hybrid-windowsmac-dvd)

1. `mkdir cd`. In **Disk Utility**, select the mounted Mac side, click **Info**, and read **Disk Identifier**. Drop the trailing `s1`/`s2` to get the whole-disc device (example: `disk2s1s2` → `disk2s1`).
2. `mount -t cd9660 -r /dev/disk2s1 cd`, install from it with CrossOver, then `umount cd` before ejecting.

[Mapping a drive](https://support.codeweavers.com/en_US/miscellanous/mapping-a-drive-or-external-volume): CrossOver gives mounted volumes a letter automatically. When a program wants a letter it lacks (often copy protection wanting `D:`): Wine Configuration → **Drives** → **Add** → a letter → **Browse** → `Volumes` → the volume → **Apply**. Per bottle.
