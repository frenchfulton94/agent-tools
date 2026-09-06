# Pools and Filesystems

Contents:
- [Choosing a filesystem](#choosing-a-filesystem)
- [Setting and changing a filesystem](#setting-and-changing-a-filesystem)
- [Converting a disk while keeping its data](#converting-a-disk-while-keeping-its-data)
- [Pools](#pools)
- [BTRFS pools](#btrfs-pools)
- [ZFS pools](#zfs-pools)
- [Encryption](#encryption)
- [Unmountable disks](#unmountable-disks)
- [Checking and repairing a filesystem](#checking-and-repairing-a-filesystem)
- [ddrescue](#ddrescue)
- [Unassigned devices](#unassigned-devices)
- [Docs links](#docs-links)

## Choosing a filesystem

| Filesystem | Redundancy | Notable | Best for |
|---|---|---|---|
| XFS | None (relies on array parity) | Robust, recovers well from crashes, readable on any Linux box | Default for array disks |
| EXT4 | None | Mature, journaled, fully supported | Array disks or single-device pools |
| ZFS | Mirrors, RAIDZ1/2/3 | Checksums, snapshots, send/receive, compression | Multi-device pools, VMs, Docker, backup targets |
| BTRFS | RAID 0/1/10, and experimental 5/6 | Checksums, snapshots, flexible device add/remove | Default for pools, mixed drive sizes |
| NTFS / exFAT | None | Limited support | Importing existing drives without migrating data |

Defaults: XFS for array disks (changeable in ***Settings → Disk Settings***), BTRFS for pools when left on "auto". There is no global default setting for pools. Mixing filesystems across disks is fine — parity is filesystem-agnostic.

Multi-device pools require BTRFS or ZFS. XFS and EXT4 are only offered when a pool has a single slot.

NTFS/exFAT disks with existing data must join the array **before** any parity disk exists, or they will be zeroed.

Legacy warnings shown on the Main page: ReiserFS disks must be migrated (they will not work in future releases); disks on older XFS versions must be migrated before 2030.

## Setting and changing a filesystem

Changing a filesystem erases the disk.

1. Stop the array.
2. On the **Main** tab click the disk and choose the filesystem from the drop-down. "auto" uses the global default.
3. Start the array — the disk shows **unmountable**.
4. Confirm only the intended disks are listed, check the box, click **Format**.

To wipe a disk completely, change it to a different filesystem, format, then change it back and format again.

## Converting a disk while keeping its data

The data must be moved off and back; there is no in-place conversion.

**7.2+ (WebGUI):** stop the array → ***Settings → Global Share Settings → Emptying disk(s)***, select the disk, Apply → start the array → ***Main → Array Operation → Move*** (or wait for Mover's schedule). Mover relocates the disk's files to other array disks per share settings. Files at the root of the disk belong to no share and are not moved. Check ***Tools → System Log*** for files skipped because they were open or space ran out.

**7.0–7.1:** the equivalent is done from the command line (see the 7.0.0 release notes, "using mover to empty an array disk").

**Any version:** move files manually.

Then browse the disk under ***Main → Array Devices*** to confirm it is empty, change the filesystem and format, and move the data back.

## Pools

A pool is a named set of one or more devices outside the array. The first is usually called `cache`, but any pool can act as cache for a share. Limits by license: Starter up to 6 pools with up to 6 devices each; Unleashed and Lifetime up to 34 pools with up to 200 devices each.

Single-device pools have no redundancy — anything on them is at risk until Mover writes it to the array. If a single-device pool might grow later, format it BTRFS or ZFS from the start; XFS or EXT4 would have to be reformatted to add devices.

Set a pool's **Minimum Free Space** (click the pool on the **Main** tab → Individual Pool Settings) to at least the size of the largest file you write, ideally double. Never set it to 0. When a share reaches either its own or the pool's minimum free space, new writes go to the array instead. The setting is ignored for shares with no secondary storage.

When a share spans several volumes, Unraid merges directory listings in this order: the pool assigned to the share, then array disks disk1…disk28, then other pools.

Moving a device from one pool to another erases it when the array restarts.

## BTRFS pools

**Adding devices:** stop the array → click the pool → set **Slots** to the exact new total → assign the devices → start the array. A **Balance** starts automatically to redistribute data; watch it under the first pool device's **Balance Status**. Hours to days depending on size.

**RAID levels** (change live via **Balance Status** → select profile → **Balance**):

| Level | Protection | Efficiency | Use |
|---|---|---|---|
| Single | None | 100% | Non-critical |
| RAID 0 | None | 100% | Speed only |
| RAID 1 | 1 disk | 50% | Default; Docker/VM storage |
| RAID 10 | 1 disk | 50% | Speed plus redundancy |
| RAID 5/6 | 1–2 disks | 67–94% / 50–88% | **Experimental — avoid for anything you care about** |

**Removing a device:** the GUI supports it one device at a time and only when the pool is RAID 1 for both data and metadata — stop the array, unassign the device, start the array, then confirm under Balance Status. From the command line with the array running: `btrfs device remove /dev/sdX1 /mnt/cache` (use `/dev/mapper/sdX1` if encrypted, `nvmeXn1p1` for NVMe). Afterwards make Unraid forget the removed member: stop the array, unassign all pool devices, start the array, stop again, reassign the remaining devices, start. With one device left, convert the profile to **single**.

**Balance** fixes "no space left on device" errors when free space exists, and is needed after adding or removing devices. **Scrub** verifies checksums and repairs corrupt blocks from redundant copies — weekly on high-usage pools, monthly otherwise. Both run online.

If a balance appears stuck: filter ***Tools → Logs*** for `btrfs`, cancel the balance, restart the array, retry; run SMART tests on every pool device; ensure 10–15% free space.

## ZFS pools

A zpool is made of vdevs. **Redundancy is per vdev** — if any vdev fails, the whole pool fails.

| Profile | Redundancy | Expansion | Efficiency | Recommended width |
|---|---|---|---|---|
| Stripe | None | Add disks | 100% | Any (scratch only) |
| Mirror | 1:1 | Add more mirrors | 50% | 2 per vdev |
| RAIDZ1 | 1 disk/vdev | Add vdevs, or single-disk expansion | High | 3–6 (max 8) |
| RAIDZ2 | 2 disks/vdev | Add vdevs | Moderate | 6–12 (max 14) |
| RAIDZ3 | 3 disks/vdev | Add vdevs | Lower | 10–16 (max 20) |

Optional tuning: data disks (total minus parity) as a power of 2 aligns stripes — RAIDZ1 at 3/5/9, RAIDZ2 at 4/6/10, RAIDZ3 at 5/9/17.

**Creating:** stop the array → **Add Pool** → name it → set slots to the number of data-vdev disks → assign disks (order does not matter) → click the pool name → set filesystem to `zfs` or `zfs-encrypted` → choose the allocation profile → enable compression (recommended) → Done → start the array.

**RAIDZ expansion (7.2+, single-vdev RAIDZ1/2/3 only):** with the array running, open the pool from ***Main → Pool Devices***; if **Pool Status** shows an **Upgrade Pool** button, click it first (this blocks downgrading Unraid). Stop the array, add a slot, select a drive at least as large as the smallest in the pool, start the array. An "invalid expansion" warning means the pool still needs upgrading. On 7.1.x this was CLI-only. Mirrored pools expand by adding whole mirror pairs; multi-vdev pools by adding whole vdevs.

**Planning tip:** a two-device pool intended to grow one disk at a time should be created as RAIDZ1 rather than the default mirror.

**Importing a pool from another system:** stop the array → **Add Pool** → set slots to the *total* device count including support vdevs → assign every drive → set File System to **Auto** → Done → start the array. Unraid detects roles automatically and lists support vdevs as **Subpools**. Run a scrub afterwards. Omitting a special or dedup vdev makes the pool unimportable; omitting a log vdev costs sync-write performance; omitting a cache/L2ARC vdev costs read cache only.

**Support vdevs (subpools):** special (metadata — pool is lost without it), dedup (huge RAM cost, avoid), log/SLOG (sync writes only), cache/L2ARC (read cache), spare (not supported as of 7.1.2). Most users need none.

**ZFS on array disks (hybrid):** an individual array disk can be formatted `zfs` or `zfs-encrypted`, gaining checksums, snapshots, and send/receive while staying under array parity. A single ZFS disk detects corruption but cannot self-heal it. This is a good replication target, not a substitute for a real pool.

**RAM:** the "1 GB per TB" rule is obsolete. Unraid caps ARC at roughly 1/8 of system RAM.

**Common mistakes:** mismatched drive sizes in a RAIDZ vdev (all treated as the smallest); expecting a single ZFS array disk to behave like a pool; enabling dedup without the RAM for it; assuming redundancy is pool-wide rather than per vdev.

## Encryption

Encryption uses LUKS and is off by default. Enabling it on an existing disk erases that disk, so move data off first.

1. Stop the array. 2. Click the disk. 3. Choose the encrypted variant of the filesystem (`xfs-encrypted`, `btrfs-encrypted`, `zfs-encrypted`). 4. Apply, then format the now-unmountable disk.

All encrypted devices in a system share one key or keyfile, supplied at every array start. Store it offline. There is no recovery path if it is lost — the docs are explicit that no backdoor exists. Encryption also complicates every recovery procedure, so recommend it only where confidentiality genuinely requires it.

## Unmountable disks

Two causes only:

1. **Brand new disk** — normal; format it.
2. **Previously working disk** — filesystem corruption, usually from an unclean shutdown, a failed write, or the disk being disabled.

For case 2, do not format. Parity cannot fix a filesystem problem; a rebuild reproduces the corruption byte-for-byte onto the new drive. Repair the filesystem, which is both faster and safer than a rebuild.

If a disk is unmountable **and** disabled (red X), run the check/repair against the *emulated* disk before rebuilding.

Common messages and what they mean: "Superblock has bad magic number" (severe — repair), "Filesystem is dirty" (unclean shutdown — check), "Metadata corruption detected" (repair), "No valid BTRFS found" (check pool assignments), "wrong fs type, bad option" (wrong filesystem selected or unformatted), "Structure needs cleaning" (repair).

## Checking and repairing a filesystem

Identify the filesystem first: **Main** tab → click the disk → **File system type**.

Array state required: XFS and EXT4 need **Maintenance Mode**. BTRFS needs Normal mode for scrub, Maintenance Mode for repair. ZFS scrubs in Normal mode.

Device paths — using the wrong one either invalidates parity or destroys the disk:

| Target | Path | Parity preserved |
|---|---|---|
| Array disk, 6.12+ | `/dev/mdXp1` | Yes |
| Array disk, ≤6.11 | `/dev/mdX` | Yes |
| Encrypted array disk | `/dev/mapper/mdXp1` | Yes |
| Pool or unassigned device | `/dev/sdX1` | N/A |
| Array disk via raw partition | `/dev/sdX1` | **No — invalidates parity** |

Never target a whole disk (`/dev/sdb`), and never target a parity disk.

**XFS, WebGUI (7.0+):** click the disk → **Check Filesystem Status** → **CHECK** (no options to type). If corruption is found a **FIX** button appears; click it, then **ZERO LOG** if offered. It reports "filesystem repaired" when done.

**XFS, command line:** `xfs_repair -v /dev/mdXp1` to check, `xfs_repair /dev/mdXp1` to repair. If it asks for `-L`, rerun as `xfs_repair -L /dev/mdXp1` — normal and usually necessary.

**BTRFS:** `btrfs scrub start /mnt/diskX` (Normal mode) is the safe first move and repairs many errors automatically. Read-only check: `btrfs check --readonly /dev/mdXp1` in Maintenance Mode. `btrfs check --repair` can make things worse — only after consulting the forums, with a backup in hand.

**ZFS:** there is no fsck. `zpool scrub poolname` verifies and self-heals where redundancy exists; `zpool status -v poolname` shows health and progress; `zpool scrub -p` pauses, `-s` stops; `zpool clear poolname` clears the error state once the cause is fixed; `zpool list` lists pools.

Afterwards, stop the array and restart in Normal mode. A `lost+found` directory holds fragments that could not be fully recovered — review it before deleting. Repairs run from minutes to hours.

## ddrescue

For salvaging a failing disk when parity cannot help (multiple failures, invalid parity). Install the **ddrescue** plugin — NerdPack and Nerd Tools are deprecated.

Clone to a healthy disk at least as large, with neither mounted:

```
ddrescue -f /dev/sdX /dev/sdY /boot/ddrescue.log
```

To clone onto an array disk while preserving parity, start the array in Maintenance Mode and target the md device:

```
ddrescue -f /dev/sdX1 /dev/md# /boot/ddrescue.log
```

The logfile lets an interrupted run resume. Verify device assignments before running — the wrong destination is destroyed. Afterwards mount the clone (Unassigned Devices) and run a filesystem check. To find files hit by bad sectors without checksums, use ddrescue's fill mode to write a marker string into the bad blocks and then grep for it.

## Unassigned devices

Drives attached but not in the array or a pool. They still count toward the license device limit. The **Unassigned Devices** plugin adds mount/unmount, network sharing, auto-mount at boot, formatting, and safe removal; **Unassigned Devices Plus** adds exFAT and HFS+. Copy to and from `/mnt/disks/` rather than array paths.

## Docs links

- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/file-systems/
- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/cache-pools/
- https://docs.unraid.net/unraid-os/advanced-configurations/optimize-storage/zfs-storage/
- https://docs.unraid.net/unraid-os/troubleshooting/common-issues/data-recovery/
- https://docs.unraid.net/unraid-os/system-administration/secure-your-server/securing-your-data/
