# Array and Disks

Contents:
- [How the array works](#how-the-array-works)
- [Starting, stopping, and Maintenance Mode](#starting-stopping-and-maintenance-mode)
- [Adding data disks](#adding-data-disks)
- [Adding and upgrading parity disks](#adding-and-upgrading-parity-disks)
- [Replacing a data disk (capacity upgrade)](#replacing-a-data-disk-capacity-upgrade)
- [Replacing a failed or disabled disk](#replacing-a-failed-or-disabled-disk)
- [Rebuilding a disk onto itself](#rebuilding-a-disk-onto-itself)
- [Parity swap](#parity-swap)
- [Removing disks](#removing-disks)
- [New Config](#new-config)
- [Parity checks and read checks](#parity-checks-and-read-checks)
- [Write modes](#write-modes)
- [Array will not start](#array-will-not-start)
- [Docs links](#docs-links)

## How the array works

Each array data disk carries its own complete filesystem and can be read on any Linux machine. Parity is computed per bit position across all data disks: parity1 is XOR (even parity); parity2 is a Reed-Solomon-style Q-parity, so the two are not interchangeable. Any single missing disk can be reconstructed with one parity disk, any two with dual parity.

Consequences worth stating to users:

- No disk may be larger than the smallest parity disk. Use the largest drives for parity.
- Dual parity disks must each be at least as large as the largest data disk, but may differ from each other.
- Changing data disk order does not invalidate parity1, but can invalidate parity2.
- Writing to a parity-protected array is four operations per write (read data, read parity, write data, write parity), so write speed is bound by the slowest drive involved.
- Array limits by license: Starter up to 6 devices including parity; Unleashed and Lifetime up to 30 (28 data + 2 parity).

## Starting, stopping, and Maintenance Mode

Stopping the array stops Docker containers and network shares, shuts down or hibernates VMs, and unmounts all devices. Nearly every disk assignment change requires the array stopped first.

**Maintenance Mode** starts the array with devices *unmounted*. It is required for XFS and EXT4 filesystem check/repair, and it speeds up rebuilds by removing user I/O. BTRFS scrub needs Normal mode; BTRFS repair needs Maintenance Mode. ZFS scrub runs in Normal mode.

## Adding data disks

A new disk added to a **parity-protected** array must be cleared (zero-filled with a clear signature) so parity stays valid. Unraid does this automatically in the background when the array starts; the array stays usable, the new disk does not. On an array with **no parity**, clearing is skipped entirely.

1. Stop the array, power down (skip if the hardware hot-swaps), install the disk, power on.
2. Assign the disk to an empty data slot. Pick the filesystem from the drop-down (XFS is the default for array disks).
3. Start the array. Clearing runs in the background if parity is present.
4. When clearing finishes the disk shows **unmountable**; check the box and click **Format**. Verify the serial number first.

**Clear vs. preclear.** Clear is Unraid's built-in background zeroing — fast, no downtime. Preclear (Unassigned Devices Preclear plugin) adds a pre-read, zeroing, and post-read verification pass to stress-test a new drive for infant mortality; it takes far longer and holds the disk offline. Do not format a precleared disk before adding it — that removes the clear signature.

Multiple disks can be added at once, but none are usable until all have cleared and been formatted.

NTFS and exFAT disks carrying existing data must be added to the array **before** any parity disk is assigned; once parity exists, every newly added data disk is zeroed regardless of format.

## Adding and upgrading parity disks

Add data disks first, then parity. Assigning a parity disk and starting the array begins a parity sync; the array stays usable but slower.

To upgrade parity to a larger disk: stop the array, install the new disk, assign it to the parity slot in place of the old one, start the array. Parity rebuilds from scratch.

During that rebuild the array is unprotected. Keep the old parity disk installed and untouched until the new sync completes. If a data disk has *already* failed, do not do this — use [parity swap](#parity-swap) instead, or the failed disk becomes unrecoverable.

## Replacing a data disk (capacity upgrade)

The replacement must be at least as large as the disk it replaces and no larger than the smallest parity disk.

1. Run a parity check and confirm zero errors. Rebuilding against invalid parity corrupts the result.
2. Fix any unmountable disk *before* starting — a rebuild will not resolve it.
3. Stop the array; unassign the target disk.
4. Start the array. Unraid emulates the missing disk. Optionally verify in Normal mode that the emulated disk mounts and looks correct, or use Maintenance Mode to block writes.
5. Stop the array; assign the replacement disk to the vacant slot.
6. Start the array to begin the rebuild. The filesystem expands to the larger capacity automatically.

Keep the original disk intact until the rebuild is verified. With single parity there is no protection during the rebuild; with dual parity one further failure is survivable, and two disks can be upgraded at once at increased risk.

## Replacing a failed or disabled disk

A **disabled** disk (red X) is one Unraid stopped writing to after a write error. It is not necessarily broken — loose cabling, power problems, and controller glitches produce the same result. Unraid emulates it from parity, so the data stays readable while the physical drive is left untouched for recovery.

| Failures | No parity | Single parity | Dual parity |
|---|---|---|---|
| 1 disk | Data lost | Rebuildable | Rebuildable |
| 2 disks | Data lost | Data lost | Rebuildable |

Diagnose first: check the syslog for drive resets (cabling), run a SMART extended test, and look at UDMA CRC error counts (attribute 199 — cabling, cumulative, never resets).

1. Verify the emulated disk mounts and its contents look right. If it is unmountable, repair the filesystem on the emulated disk before going further.
2. Stop the array; power down unless hot-swap is available.
3. Install the replacement (at least as large as the old disk, no larger than the smallest parity disk).
4. Assign it to the failed disk's slot; confirm the checkbox.
5. Optionally choose Maintenance Mode for a faster rebuild.
6. Start the array. In Normal mode the rebuild begins automatically; from Maintenance Mode, click **Sync** on the Main tab.

If Unraid offers to format the new disk during this, decline. Rebuild times run hours to more than a day.

If more disks have failed than parity can cover: stop all writes immediately, do not rebuild, and post diagnostics to the forums before touching anything.

## Rebuilding a disk onto itself

When a healthy disk was disabled by an external cause (cable, power), it can be rebuilt in place rather than replaced. Confirm first that a SMART extended test passes, the external cause is fixed, and the emulated disk shows correct content.

1. Stop the array; unassign the disabled disk.
2. Start the array so Unraid registers it as "Not installed"; verify the emulated content.
3. Stop the array; reassign the same disk to its original slot.
4. Start the array — optionally in Maintenance Mode — to rebuild the emulated content onto the physical drive.

This works for data disks and parity disks alike.

## Parity swap

Needed only when the replacement **data** disk is larger than the current parity disk. It promotes the new disk to parity and moves the old parity disk into the data slot.

Prerequisite: the disk being replaced must already be disabled. If it is healthy, unassign it and start the array once so Unraid marks it disabled.

1. Stop the array; unassign the old data drive; start the array (it shows "Not installed"); stop again.
2. Power down, install the new larger disk (preclearing recommended, formatting not needed), power on.
3. Stop the array if it auto-started.
4. Unassign the parity disk. Assign the **new** disk to the parity slot. Assign the **old parity disk** to the data slot being replaced.
5. A **Copy** button appears — "Copy will copy the parity information to the new parity disk." Confirm and click it. The array is offline for this; it takes many hours.
6. Start the array to rebuild the data disk.

Never format anything during this procedure. A parity check afterwards is optional but common.

## Removing disks

**Parity disk:** stop the array, set the slot to Unassigned, start the array. Note the loss of redundancy this causes if any data disk is already failed.

**Data disk, standard method:** move wanted data off the disk first, then screenshot the assignments, run ***Tools → New Config*** preserving current assignments, unassign the disk, and start the array **without** checking "Parity is valid". A parity sync runs; the array is vulnerable until it finishes.

**Data disk, parity-preserve method (advanced, unsupported by LimeTech):** zeroing the disk leaves parity valid because zeros do not change it. One disk at a time, all data already moved off:

1. Start the array in Maintenance Mode, click the disk, click **Erase**, then stop the array.
2. Start in Normal mode — the disk will not mount, the rest stay online.
3. Record all assignments, especially parity.
4. Optionally enable Reconstruct Write in ***Settings → Disk Settings*** to speed up zeroing, only if every drive is healthy.
5. `umount /mnt/diskX`
6. Zero it: 6.12+ `dd bs=1M if=/dev/zero of=/dev/mdXp1 status=progress`; 6.11 and earlier `dd bs=1M if=/dev/zero of=/dev/mdX status=progress`. This runs for hours — use a persistent terminal (e.g. the Tmux Terminal Manager plugin).
7. Stop the array, New Config retaining assignments, unassign the disk, check "Parity is already valid", start the array.
8. Optionally run a correcting parity check.

An alternative on 7.2+ is ***Settings → Global Share Settings → Emptying disk(s)***: select the disk, apply, start the array, and run Mover to relocate its files to other array disks according to share settings. On 7.2.0 the disk's data is hidden from user shares while flagged; from 7.2.1 the data stays visible but no new files are written to it. Files sitting at the root of the disk are outside any share and will not be moved. The flag clears when the array stops.

## New Config

***Tools → New Config*** resets the array configuration, optionally preserving current assignments. Use it for reordering, removing a disk, or recovering from assignment errors — not for rebuilding a failed disk.

Unraid tries to recognise previously used drives and keep their data. Removing a data drive invalidates parity unless the drive was zeroed. To undo: access `/boot/config` over the network, rename `super.old` back to `super.dat`, and reboot.

## Parity checks and read checks

A **parity check** reads all data disks plus parity, recomputes, and compares. Correcting mode updates parity on mismatch; non-correcting mode only logs. Only the first 100 error addresses are logged. Each sync error counts a 4 KiB block.

A **parity sync** is different: it builds parity from scratch after adding or replacing a parity disk.

A **read check** reads every sector of every disk without comparing to parity. Use it when there are no parity disks assigned, or when more disks are disabled than parity can cover.

Schedule checks in ***Settings → Scheduler***; monthly or quarterly correcting checks are the usual recommendation. After an unclean shutdown Unraid starts an automatic check using the mode set there (non-correcting by default). History is under ***Array Operations → History*** and in a text file in `/boot/config`.

Sync errors point at unclean shutdowns, failing drives, or cabling. Investigate SMART data before assuming parity was simply stale. A disk stays "valid" after a non-correcting check that found errors, deliberately — marking it invalid would leave two invalid disks after one more failure.

## Write modes

Set in ***Settings → Disk Settings → Tunable (md_write_method)***.

| Mode | Typical speed | Spins up | Notes |
|---|---|---|---|
| Read/Modify/Write (default) | 20–40 MB/s | Parity + target disk only | Lowest power and wear; best for small or occasional writes |
| Reconstruct Write ("Turbo Write") | 40–120 MB/s | All array disks | Best for bulk transfers, rebuilds, parity checks; needs every drive healthy and spinning |

Cache writes bypass both: SSD pools land around 50–110 MB/s, NVMe 250–900 MB/s, and Mover relocates to the array later.

## Array will not start

Look for the message under ***Main → Array Operation***:

- *Too many wrong and/or missing disks* — more missing disks than parity covers. Replace them one at a time; if unrecoverable, New Config.
- *Too many attached devices* — the Starter tier's 6-device limit. Stop the array, disconnect unneeded devices, start, then reconnect them for Unassigned Devices use. The limit counts everything present at array start except the boot USB.
- *Invalid or missing registration key* — install or purchase a key at ***Tools → Registration***. An "invalid key" error often means an expired trial or a blacklisted/non-unique USB GUID.
- *Cannot contact key-server* — trial licences validate online at boot with a 30-second window; refreshing the WebGUI retries. Paid licences do not need this.
- *This Unraid release has been withdrawn* — a beta/RC no longer enabled. Update to the latest stable via ***Tools → Update OS***.

## Docs links

- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/array/overview/
- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/array/adding-disks-to-array/
- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/array/replacing-disks-in-array/
- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/array/removing-disks-from-array/
- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/array/array-health-and-maintenance/
