# Games, controllers, and devices

Source: the [CodeWeavers Mac knowledge base](https://support.codeweavers.com/en_US/mac-knowledge-base), fetched 2026-10-17. Graphics backends and DLSS are in `advanced-settings.md`.

## Contents

- [Controllers](#controllers)
- [USB devices](#usb-devices)
- [Heroic for Epic and GOG](#heroic-for-epic-and-gog)
- [Anti-cheat](#anti-cheat)
- [Mods and add-ons](#mods-and-add-ons)

## Controllers

[Using controllers with CrossOver](https://support.codeweavers.com/en_US/troubleshooting/using-controllers-in-crossover)

- CodeWeavers regularly tests the Xbox One, Xbox Series, DualShock 4, and DualSense controllers. They "may still not work in all games".
- **The game must support Windows XInput**, and the controller must work in macOS first.
- Native Windows controller drivers "can't be installed or used in CrossOver since there is no underlying Windows OS".

Fixes, in order:

1. **Wired Sony controller not working:** **Control Panels** → **Game Controllers** → **Disable hidraw**.
2. Use a USB cable instead of Bluetooth.
3. Re-pair the controller in macOS ([PlayStation](https://support.apple.com/111100), [Xbox](https://support.apple.com/111101)).
4. Steam games: **Steam > Settings > Controller > General Controller Settings** → enable the controller's configuration, or try the generic gamepad one.
5. Still failing: [contact CodeWeavers](https://www.codeweavers.com/contact-us) with the setup details. They track these reports for future testing.

## USB devices

[Using USB devices with CrossOver](https://support.codeweavers.com/en_US/troubleshooting/using-usb-devices-with-crossover). CodeWeavers "often can't predict whether a specific USB device will be recognized", and their support team does not troubleshoot USB devices. Gamepads, joysticks, keyboards, and mice usually work, provided they work in macOS.

**Serial devices only — a "potential" workaround** that maps the device to `COM1`:

1. Unplug the device. Run `ls /dev > ~/disconnect.txt`. Plug it in, wait, run `ls /dev > ~/reconnect.txt`, then `diff ~/disconnect.txt ~/reconnect.txt`. The new entry looks like `tty.usbserial-DN014TJU`.
2. In the bottle, regedit → `HKEY_LOCAL_MACHINE\Software\Wine` → create the key `Ports` → add a string named `Com1` whose value is `/dev/tty.usbserial-…`.
3. *Command line equivalent:* `"$CX/wine" --bottle NAME --no-gui --cx-app reg.exe add 'HKLM\Software\Wine\Ports' /v Com1 /t REG_SZ /d /dev/tty.usbserial-XXXX /f`.

## Heroic for Epic and GOG

[Using Heroic with CrossOver](https://support.codeweavers.com/en_US/common-actions/heroic-games-launcher-in-crossover)

1. Create a bottle named `Heroic`, type **Windows 10 64-bit** (`--template win10_64`).
2. In that bottle's Advanced Settings, enable **DXVK**.
3. Install the [Heroic Games Launcher](https://heroicgameslauncher.com) build for the Mac's CPU. At the unverified-app warning, **Cancel**, then Control-click → **Open**.
4. Sign in to Epic or GOG. Under **Settings > Game Defaults**, select CrossOver and the bottle `Heroic`.
5. Install a game and **Play Now**. Check its compatibility database rating; "CrossOver may not be able to run them all perfectly."

## Anti-cheat

[Game anti-cheat systems with CrossOver](https://support.codeweavers.com/en_US/miscellanous/anti-cheat). Anti-cheat works "at a very low-level of the Windows operating system" and is "incompatible with CrossOver's translation layer". CodeWeavers follows the DMCA and "cannot legally work around any type of copy protection or anti-cheat technology". A game whose anti-cheat blocks it will work only if the developer changes the game.

Say so directly. Do not suggest bypasses, alternative launchers, or settings as a fix. For a game the user wants to play anyway, the options are outside CrossOver: a native or cloud version, or real Windows.

## Mods and add-ons

[Game mods and add-ons with CrossOver](https://support.codeweavers.com/en_US/miscellanous/mods-and-add-ons-with-crossover). Testing and support cover "the base version of the game title". Some mods happen to work, but none is supported, and some "may also violate a game's terms of service or intellectual property rights".

When a modded game fails, first test whether the unmodded game runs in the same bottle. Archive the bottle before adding mods, so the user can get back to a working one.
