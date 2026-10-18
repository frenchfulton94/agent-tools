# Advanced Settings by CrossOver version

Source: the three KB pages below, fetched 2026-10-17. Descriptions are quoted from them. The pages document UI toggles only. They name **no** environment variable, `cxbottle.conf` key, or `defaults` key, and **no** default graphics backend. Do not supply any of those from memory. To learn what a toggle wrote, diff `cxbottle.conf` before and after changing it.

Find the version first: `defaults read /Applications/CrossOver.app/Contents/Info.plist CFBundleShortVersionString`.

Advanced Settings are per bottle. In 25 and later, each graphics option is "used for all applications installed in the bottle", which is one more reason to keep one application per bottle.

## Contents

- [CrossOver 26 and later](#crossover-26-and-later)
- [CrossOver 25](#crossover-25)
- [CrossOver 23.7 through 24](#crossover-237-through-24)
- [What changed between versions](#what-changed-between-versions)
- [Choosing, per the KB](#choosing-per-the-kb)

## CrossOver 26 and later

[Advanced Settings in CrossOver Mac 26](https://support.codeweavers.com/en_US/miscellanous/advanced-settings-in-crossover-mac-26) (updated 2026-02-10)

**Graphics** — one backend per bottle:

| Option | KB description |
|---|---|
| Auto | "CrossOver uses the graphics backend specified in its proprietary database on a per-game basis, and uses wined3d if no backend is specified in the database." |
| DXMT | "A Metal-based implementation of Direct3D 11." |
| D3DMetal | "A graphics API translation layer from the game porting toolkit supporting DirectX 11 and DirectX 12 games." |
| DXVK | "A Vulkan-based translation layer for Direct3D 10 and 11." |
| Wine | "Wine's known implementation of Direct3D, known as wined3d." |

**Other settings:**

| Setting | KB description |
|---|---|
| DLSS | "Enable DLSS powered by MetalFX. This setting only takes effect if DLSS is enabled in the in-game settings and is only enabled for D3DMetal and DXMT. Many games run better with DLSS enabled, but some games do not." |
| MSync | "Mach semaphore-based synchronization. Some applications run with better performance with MSync enabled and some applications show no difference." |
| High Resolution Mode | Turns off pixel doubling and reports 192 DPI. "Not all applications render correctly in high-resolution mode." |

The 26 page lists no ESync and no "Default" synchronization option. It does not say whether ESync was removed or only left undocumented. If the user's 26 build shows ESync, the 25 description applies.

## CrossOver 25

[Advanced Settings in CrossOver Mac 25](https://support.codeweavers.com/en_US/miscellanous/advanced-settings-in-crossover-mac) (applies to "CrossOver 25 and later"; updated 2025-01-14)

**Graphics:** the same five options as 26 — Auto, DXMT, D3DMetal, DXVK, Wine — with the same descriptions. There is no DLSS toggle.

**Synchronization:** one of three.

| Option | KB description |
|---|---|
| Default | "Neither ESync nor MSync enabled." |
| ESync | "Eventfd-based synchronization. Some applications run with better performance with ESync enabled, some applications show no difference, and some applications are broken by ESync." |
| MSync | Mach semaphore-based. Same wording as ESync, including "some applications are broken by MSync". |

**High Resolution Mode:** as in 26.

## CrossOver 23.7 through 24

[Advanced Settings in CrossOver Mac 23.7–24](https://support.codeweavers.com/en_US/miscellanous/advanced-settings-in-crossover-237) (updated 2025-03-11)

These are separate toggles, not a backend menu. wined3d is the backend when neither graphics toggle is on.

| Toggle | KB description |
|---|---|
| D3DMetal | Game Porting Toolkit layer for DirectX 11 and 12; "used instead of DXVK or the wined3d default". |
| DXVK | Vulkan-based, Direct3D 10 and 11; "used instead of the wined3d default. Some games run better with DXVK, while others run better with wined3d." |
| ESync | As in 25: some applications improve, some do not change, and "some applications are broken by ESync". |
| MSync | The same, for MSync. |
| High-Resolution Mode | As in 25 and 26. |

All three pages carry the same note on CSMT: "Performance Enhanced Graphics (CSMT) are now enabled by default and the toggle is no longer shown in CrossOver 23.x and later." A user asking where the CSMT toggle went should hear that it is always on.

## What changed between versions

| Setting | 23.7–24 | 25 | 26 |
|---|---|---|---|
| Graphics | D3DMetal and DXVK toggles; wined3d otherwise | Menu: Auto, DXMT, D3DMetal, DXVK, Wine | Same menu |
| Auto (per-game database) | — | Added | Present |
| DXMT | — | Added | Present |
| Sync | ESync and MSync toggles | Default / ESync / MSync | MSync only on the page |
| DLSS (MetalFX) | — | — | Added; D3DMetal and DXMT only |
| High Resolution Mode | Present | Present | Present |
| Windows version | Not here: Wine Configuration → Applications | Same | Same |

A missing row on a page is not proof that the product removed the setting. The KB never announces removals.

## Choosing, per the KB

The KB gives no ranking of backends. What it does support:

- **Start from Auto** (25+). It uses CodeWeavers' per-game choice and falls back to wined3d. Check the compatibility database entry before overriding it, because a rating often names the backend that worked.
- **DirectX 12 needs D3DMetal.** It is the only option described as supporting DirectX 12. DXMT and DXVK are described for Direct3D 11 (and 10, for DXVK).
- **Treat sync modes as an experiment for each application.** The KB's own wording is that some applications get faster, some stay the same, and some break. If an application broke after a sync change, the change is the first suspect.
- **DLSS does nothing unless the game's own DLSS setting is on**, and it works only with D3DMetal or DXMT.
- **Turn High Resolution Mode off for an application that renders wrongly.** If the whole bottle renders too large, see the DPI reset in `troubleshooting.md`.
- **Heroic** (Epic and GOG): the KB's setup enables DXVK on a `Windows 10 64-bit` bottle (`games-and-devices.md`).
