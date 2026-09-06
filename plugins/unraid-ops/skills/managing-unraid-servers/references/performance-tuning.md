# Performance Tuning

Contents:
- [Measure before tuning](#measure-before-tuning)
- [Expected numbers](#expected-numbers)
- [Array write performance](#array-write-performance)
- [Keeping hot data off the array](#keeping-hot-data-off-the-array)
- [Read performance](#read-performance)
- [Share settings that affect speed](#share-settings-that-affect-speed)
- [Pool and filesystem choices](#pool-and-filesystem-choices)
- [Network protocol choice](#network-protocol-choice)
- [Docker performance](#docker-performance)
- [VM performance](#vm-performance)
- [Power saving vs. speed](#power-saving-vs-speed)
- [Things that cost performance for no gain](#things-that-cost-performance-for-no-gain)
- [Docs links](#docs-links)

Unraid has no single performance settings page, and the official docs cover this across many pages rather than one. Treat the numbers below as the documented shape of the system, not a benchmark promise — hardware dominates.

## Measure before tuning

Most "Unraid is slow" reports are a parity write penalty, a share pointed at the array instead of a pool, or a 1 Gb network link — not a tunable. Establish where the ceiling is first:

- **Network link speed:** `ethtool eth0` (look at Speed), plus `ethtool -S eth0` for errors. A 1 Gb link caps at roughly 110 MB/s, so any array write above ~40 MB/s is already network-bound.
- **Raw disk reads:** `hdparm -tT /dev/sdX`, run several times. Use the physical device, not `/dev/md1` — the md device includes parity work and will read low for reasons that have nothing to do with the drive.
- **All drives at once, with position detail:** the **DiskSpeed** container from Community Applications tests every drive at multiple offsets and draws heat maps, which is how you spot bad zones and SMR drives that collapse under sustained write.
- **What is actually busy:** `top` or `htop`, `free -h`, and `ps aux --sort=-%cpu | head -20`.

Compare the result against the table below before changing settings.

## Expected numbers

| Path | Typical | Why |
|---|---|---|
| Array write, Read/Modify/Write | 20–40 MB/s | Four I/O operations per write: read data, read parity, write data, write parity |
| Array write, Reconstruct Write | 40–120 MB/s | Reads all other disks instead, writes data and parity once |
| Array write, no parity | Disk speed | No parity work at all |
| SSD pool write | 50–110 MB/s | Usually network-bound on 1 Gb |
| NVMe pool write | 250–900 MB/s | Needs 2.5 Gb+ networking to show |
| Array read | One disk's speed | Files are whole on one disk; nothing is striped |

## Array write performance

***Settings → Disk Settings → Tunable (md_write_method)***:

| Mode | Speed | Spins up | Trade-off |
|---|---|---|---|
| Read/Modify/Write (default) | 20–40 MB/s | Parity + target disk only | Lowest power draw and wear; best for small or occasional writes |
| Reconstruct Write ("Turbo Write") | 40–120 MB/s | Every array disk | Best for bulk transfers, rebuilds, and parity checks; requires every drive healthy and spinning |

Reconstruct Write is the single largest array write lever. It is not free: it spins every disk for every write, so it raises power draw, heat, and wear, and it is a bad default on an array with a marginal drive — the mode reads all other disks, so a weak one is now in the path of every write.

A common pattern is leaving RMW as the default and enabling Reconstruct Write temporarily for a large ingest, a rebuild, or the zeroing step when removing a disk.

## Keeping hot data off the array

The array is for capacity; pools are for speed. Most real gains come from routing work to a pool rather than tuning the array.

- Give any write-heavy share a pool as **Primary storage** with the array as Secondary, so writes land at pool speed and Mover relocates them later. See `references/shares-and-mover.md`.
- Keep `appdata`, `system` (which holds `docker.img` and `libvirt.img`), and `domains` on a pool. Containers and VMs doing metadata-heavy work on parity-protected array disks is the most common self-inflicted slowdown.
- Never leave an active VM vdisk on a share whose Mover action would push it to the array — performance collapses when Mover relocates a running VM's disk.
- **Exclusive shares** (6.12+) remove the FUSE layer entirely: with `Permit exclusive shares` enabled, a share whose primary storage is a pool with no secondary gets a direct symlink into the pool directory. This matters on fast ZFS pools and fast networks, where FUSE itself becomes the bottleneck. Cost: both share and pool minimum-free-space settings are ignored for new files.
- Schedule Mover for off-hours (***Settings → Scheduler***) so the array write penalty lands when nobody is using the server.

## Read performance

Array reads come from one disk, at that disk's speed. There is no striping to aggregate, so no setting will make a single-file read faster than the drive holding it. This is a design consequence, not a misconfiguration — the same property is why only the failed disk matters during a failure and why mixed drive sizes are fine.

To go faster on reads, the file has to live somewhere else: a pool, or a share pinned to a pool.

## Share settings that affect speed

- **Allocation method.** High-Water (default) keeps related files together and minimises spin-ups. Most-Free balances best but causes the most drive thrashing and spin-ups — it suits sustained high-throughput work like video editing and is a poor fit for a media library. Fill-Up suits static archives.
- **Split level** keeps a directory tree on one disk, which means sequential playback or a build reads from one spinning disk instead of waking several. It also overrides allocation method and minimum free space, so an aggressive split rule can produce "out of space" while other disks sit empty.
- **Minimum free space** set to twice your largest file avoids transfers failing partway when a disk fills mid-write. Unraid cannot know a file's final size when it picks a disk. Never 0.
- **Mover logging** writes every moved file path into the syslog. Leave it off outside troubleshooting — it adds overhead and puts filenames into diagnostics.

## Pool and filesystem choices

- **ZFS** suits VM and Docker storage: checksums, snapshots, compression, send/receive. Enable compression when creating the pool. Unraid caps ARC at roughly 1/8 of system RAM, so the old "1 GB of RAM per TB" rule does not apply.
- **RAIDZ width** affects both efficiency and speed: RAIDZ1 at 3–6 devices, RAIDZ2 at 6–12, RAIDZ3 at 10–16. Optionally make the data-disk count (total minus parity) a power of 2 to align stripes — RAIDZ1 at 3/5/9, RAIDZ2 at 4/6/10, RAIDZ3 at 5/9/17.
- **Mismatched drive sizes in a RAIDZ vdev** mean every drive is treated as the smallest. Match sizes within a vdev.
- **BTRFS** needs 10–15% free space to behave. Run a **balance** when writes fail with "no space left on device" despite free space showing, and after adding or removing devices. **Scrub** weekly on high-usage pools, monthly otherwise.
- Redundancy in ZFS is **per vdev** — one failed vdev loses the whole pool, so widening a pool with an unprotected stripe vdev trades away everything.

## Network protocol choice

- **SMB** is the default and right for Windows and macOS, but slows down noticeably with many small files.
- **NFS** performs better on small-file workloads for Linux clients. If it throws "stale file handle" errors, the `fuse_remember` tunable addresses it.
- **macOS clients:** enable ***Settings → SMB → Enhanced macOS interoperability***. AFP was removed in 6.9.
- On a 1 Gb link, protocol tuning is mostly irrelevant for large sequential files — the link is the ceiling.

## Docker performance

- Keep `appdata` and `docker.img` on a pool, not the array.
- **Bridge** networking is the safe default; **host** removes the port-mapping layer where a container needs it. Custom networks (ipvlan by default since 6.11.5) give a container its own LAN IP.
- Map only the paths a container needs, at the most restrictive access mode that works — broad read/write mappings across the whole array invite unnecessary disk activity.
- Set container **autostart order** with wait values so a database is ready before the app that depends on it, rather than both racing at boot.
- Docker cannot join two networks on the same subnet, so a server flipping between wired and wireless forces a Docker restart and per-container reconfiguration. Pick one.

## VM performance

- **CPU mode:** Host passthrough for maximum performance; Emulated only when compatibility demands it.
- **Machine type:** Q35 is the Linux default and generally better for GPU passthrough. Raise the version within the same prefix after an upgrade if performance regressed — never switch prefix on an existing VM.
- **vDisk type:** RAW is fastest; QCOW2 is required for snapshots. Choose based on whether you need snapshots.
- **VirtIO** drivers for disk and network are the paravirtualised path — install them in the guest.
- **CPU pinning** (***Settings → CPU Pinning***) assigns cores to a VM, but Unraid may still use them; **isolation** dedicates them and needs a reboot, whereas pinning changes do not.
- **Memory ballooning** (set a Max Memory value) lets RAM flex, but is unavailable on VMs with PCI devices assigned.
- **Hyper-V extensions** on for Windows guests.
- **VNC feels slow** because it is VNC — set the video driver to QXL, or pass through a GPU for anything graphics-dependent.
- Sizing: utility Linux VMs 1–2 GB and 1–2 vCPU; desktops 4–8 GB and 2–4 vCPU; gaming or passthrough 8–16 GB+ and 4–8+ vCPU. Resources are only consumed while a VM runs.

## Power saving vs. speed

These pull against each other, and the right answer depends on the workload:

- **Spin-down delay** (***Settings → Disk Settings***, per-disk overrides on the Main tab) saves power and wear but adds a spin-up delay of several seconds to the first access.
- **Read/Modify/Write** spins two disks per write; **Reconstruct Write** spins all of them.
- **High-Water** allocation minimises spin-ups; **Most-Free** maximises them.
- **Dynamix S3 Sleep** with Wake-on-LAN suits a server that is genuinely idle for long stretches, at the cost of wake latency and some hardware unreliability.

A media server streaming one file at a time benefits from aggressive spin-down and High-Water. A server with continuous container activity will never spin down anyway, so the setting only adds latency.

## Things that cost performance for no gain

- **SSDs in the parity array.** Unraid does not pass TRIM/Discard to array devices, so they degrade over time. SSDs belong in pools.
- **BTRFS RAID 5/6.** Experimental. The docs say to avoid it for anything you care about.
- **A ZFS dedup vdev.** Enormous RAM cost, almost never worth it.
- **XMP / AMD AMP memory profiles.** These are overclocks. RAM is the most common cause of unexplained crashes, corruption, and failed parity checks — run at SPD speeds on a server and buy from the motherboard's QVL.
- **Mixing `/mnt/user` and `/mnt/diskX` in one command** to "skip the FUSE layer." This is a documented data-corruption path, not an optimisation.
- **Encryption enabled without a confidentiality requirement.** It adds CPU cost and complicates every recovery procedure.
- **Plugins where a container would do.** Plugins run with full filesystem access and can destabilise the system after an OS update.

## Docs links

- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/array/overview/
- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/shares/
- https://docs.unraid.net/unraid-os/advanced-configurations/optimize-storage/zfs-storage/
- https://docs.unraid.net/unraid-os/troubleshooting/common-issues/system-crashes-and-stability/
- https://docs.unraid.net/unraid-os/system-administration/advanced-tools/command-line-interface/
