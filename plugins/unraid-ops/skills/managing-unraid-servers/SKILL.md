---
name: managing-unraid-servers
description: Guidance for setting up, configuring, operating, and troubleshooting Unraid servers — the parity array, cache/ZFS/BTRFS pools, user shares and Mover, Docker containers, VMs, boot media and licensing, remote access, performance tuning, security hardening, and disk failure recovery. Use when the user mentions Unraid, an Unraid array or tower, parity disks, /mnt/user or /mnt/diskX paths, appdata or Community Applications, or asks about a NAS built on Unraid. Also use for symptoms that point at Unraid without naming it - a disk showing "unmountable" or a red X, a drive that got disabled or is being emulated, a parity check reporting sync errors, Mover not moving files, array writes stuck around 20 MB/s, a docker.img that filled up, or a server that will not boot from its USB flash drive.
license: MIT
---

# Managing Unraid Servers

Unraid is a USB- or internal-boot NAS OS built around three separate storage concepts that behave very differently: a **parity array** of independent disks, one or more **pools** (real BTRFS/ZFS RAID), and a FUSE layer called **user shares** that presents both as merged folders. Most bad Unraid advice comes from treating the array as ordinary RAID or from acting on the WebGUI's most visible button. The corrections below exist because they are the mistakes that destroy data.

Scope: this covers Unraid specifically. Generic Linux storage questions (`mdadm`, LVM, a Synology or TrueNAS box) are a different system — the parity model, device paths, and repair procedures here do not transfer.

## Confirm the version before giving a procedure

Several procedures changed between releases, and answers from older forum posts are still the most common thing on the web. Ask for the version, or check ***Tools → Registration*** / the WebGUI footer, whenever the answer would differ:

| Since | What changed |
|---|---|
| 6.12 | Array partition path is `/dev/mdXp1`; before that, `/dev/mdX` |
| 6.12 | Share storage is set by **Primary/Secondary storage + Mover action**, replacing *Use cache: Yes/No/Only/Prefer* |
| 6.12 | ZFS available for pools and for individual array disks; exclusive shares introduced |
| 7.0 | XFS repair automated in the WebGUI (**CHECK** → **FIX** → **ZERO LOG**), no options to type |
| 7.2 | Unraid API built into the OS (no plugin); RAIDZ expansion in the WebGUI; EXT4/NTFS/exFAT usable on array disks |
| 7.3 | Internal boot from SSD/NVMe/eMMC, optionally mirrored; TPM-based licensing replaces the USB GUID as the licence anchor; the WebGUI says **Boot device** where older releases said **Flash** |

## Before any operation that can lose data

These are gates, not suggestions. Each one is a documented path to permanent loss.

- **Never format an unmountable disk** unless it is brand new. Formatting erases it *and* updates parity, so the data can no longer be reconstructed. An existing disk that turned unmountable has a filesystem problem — check and repair the filesystem instead. This includes the Format prompt Unraid itself shows during a rebuild.
- **Repair the emulated disk before rebuilding.** If a disk is disabled (red X), Unraid emulates it from parity. Rebuilding copies the emulated content onto the new drive, corruption included. If the emulated disk is unmountable, the rebuilt disk will be too.
- **Repair through the Unraid device, not the raw one.** For array disks use `/dev/mdXp1` (6.12+) or `/dev/mdX` (≤6.11) with the array in **Maintenance Mode**. Running a repair tool on `/dev/sdX1` bypasses the parity layer and invalidates parity. Never target a whole disk (`/dev/sdb`), and never target a parity disk — it has no filesystem.
- **Never mix `/mnt/user/<share>` and `/mnt/diskX/<share>` in one command.** They are two views of the same files, `cp` and `rsync` cannot tell them apart, and the result is corruption or deletion. Stay entirely within one view.
- **`New Config` is not a repair tool.** It clears the array history a rebuild depends on; afterwards Unraid will not offer to rebuild the disk. Use it to change assignments, not to fix a failed drive.
- **Leave "Parity is Already Valid" unchecked** unless the assignments are certainly identical to before and nothing was written since. Checking it wrongly leaves an array that reports protection it does not have.
- **Check drive health before a rebuild.** A rebuild reads every other disk at full speed and is when second failures surface. Run a SMART extended test (`smartctl -t long /dev/sdX`) on the drives involved first.
- **Capture diagnostics before rebooting a server with a problem.** `/var/log` is in RAM; ***Tools → Diagnostics*** (or the `diagnostics` command, which writes to `/boot/logs`) is the only record afterwards.

When acting on a live server rather than advising, confirm the target device by **serial number** before any destructive command. Unraid identifies disks by serial, `sdX` letters are reassigned across reboots, and the docs attach a serial-number check to every format, rebuild, and swap.

## Corrections to carry into every answer

- **The array is not RAID.** Each data disk holds a complete, independently readable filesystem; parity disks are dedicated, not striped. So: read speed is one disk's speed, not aggregated; a data disk can never be larger than the smallest parity disk; disks of mixed sizes are fine and can be added one at a time; only the failed disk is stressed during normal operation; and `mdadm`-style RAID reasoning does not apply.
- **Pools are not covered by parity.** A pool (the default one is named `cache`) is real BTRFS or ZFS RAID living outside the array. A single-device pool has no redundancy at all, and anything on a pool is unprotected until Mover writes it to the array.
- **`root` cannot reach network shares.** Root is the WebGUI/SSH administrator only. SMB, NFS, and FTP access requires separate share users created by root.
- **Docker Compose is not natively supported.** Containers are defined by XML templates from Community Applications, stored on the boot device at `/boot/config/plugins/dockerMan/templates-user`.
- **SSDs do not belong in the array.** Unraid does not pass TRIM/Discard to array devices; SSD support there is experimental and degrades. Put SSDs in a pool or leave them unassigned.

## Where to look

Read at most the files the question actually touches.

- `references/array-and-disks.md` — adding, replacing, upgrading, or removing array disks; parity checks, sync errors, and read checks; rebuilds and emulation; parity swap; New Config; clear vs. preclear; write modes.
- `references/pools-and-filesystems.md` — cache pools, BTRFS and ZFS layout and expansion, choosing or converting a filesystem, encryption, balance and scrub, and any disk or pool showing **unmountable**.
- `references/shares-and-mover.md` — creating shares, primary/secondary storage, allocation method, split level, minimum free space, Mover behaviour and scheduling, default shares, SMB/NFS/FTP export and share security.
- `references/docker-and-vms.md` — container templates, network modes, volume and port mappings, appdata, `docker.img` problems, autostart order; VM creation, GPU and PCI passthrough, snapshots, VirtIO.
- `references/performance-tuning.md` — anything framed as slow, sluggish, or "how do I make this faster": write modes, routing hot data to pools, exclusive shares, protocol choice, Docker and VM tuning, and the power-saving trade-offs. Start here for a speed complaint rather than tuning blind.
- `references/remote-access-and-security.md` — Tailscale, WireGuard, SSL certificates and myunraid.net URLs, users and permissions, port-forwarding risk, outgoing proxies and VPN tunnels, and the hardening checklist.
- `references/system-administration.md` — boot media and internal boot, licensing and device limits, updating and downgrading, flash backup, diagnostics and syslog, SMART attributes, UPS and shutdown timeouts, notifications, the CLI and `unraid-api`.

## Gotchas

Environment facts that defy a reasonable guess:

- `/var/log` is a RAM disk. The syslog is gone after every reboot unless syslog mirroring or a syslog server is configured first.
- Files on the boot device cannot hold the execute bit. Invoke a script there through its interpreter (prefix the path with `bash`), or copy it to `/usr/local/bin` from `config/go` and set the bit there.
- `mv` between two shares under `/mnt/user` may be treated as a rename, so the file stays on its original disk no matter what the share's storage settings say. Use Mover, or copy-then-delete.
- Mover skips open files. Disable Docker and VM Manager before moving `appdata` or `system`.
- Every device attached at array start counts against the license limit, including unassigned devices and, on 7.3+, internal boot devices. Only one USB and one eMMC device are exempt.
- Split level wins over allocation method and minimum free space, so a share can report "out of space" while other array disks sit empty.
- Disks are identified by serial number, not SATA port, so drives can be moved between ports and controllers freely.
- Modern Windows refuses guest access to Public SMB shares by default, and only holds one credential set per server at a time.

## Output contract

When giving a procedure:

1. State the Unraid version the steps apply to whenever the procedure differs across releases.
2. Give steps in order, and name the array state each step requires — stopped, started, or Maintenance Mode. Most storage steps are only valid in one state.
3. Call out the irreversible step explicitly and say what it destroys.
4. For a problem the user is currently hitting, put "capture diagnostics before rebooting" first, not last.
5. Link the relevant page on `docs.unraid.net`, and for anything ambiguous or already going wrong, point at the [Unraid forums](https://forums.unraid.net/) with diagnostics attached — that is the documented escalation path.
