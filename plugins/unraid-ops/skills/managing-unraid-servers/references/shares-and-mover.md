# Shares and Mover

Contents:
- [User shares vs. disk shares](#user-shares-vs-disk-shares)
- [Creating and deleting shares](#creating-and-deleting-shares)
- [Primary and secondary storage](#primary-and-secondary-storage)
- [Mover](#mover)
- [Allocation method](#allocation-method)
- [Split level](#split-level)
- [Minimum free space](#minimum-free-space)
- [Included and excluded disks](#included-and-excluded-disks)
- [Default shares](#default-shares)
- [Exclusive shares](#exclusive-shares)
- [Network export and security](#network-export-and-security)
- [Users](#users)
- [Time Machine shares](#time-machine-shares)
- [Docs links](#docs-links)

## User shares vs. disk shares

**User shares** are a FUSE layer at `/mnt/user` that merges same-named top-level folders across array disks and pools into one view. Directories appear merged; each individual file still lives whole on one device. Any top-level folder created manually on a disk automatically becomes a user share with default settings.

**Disk shares** expose a single device: `/mnt/disk1`, `/mnt/disk2`, `/mnt/cache`, `/mnt/<poolname>`. They are disabled by default; enable them in ***Settings → Global Share Settings***.

Both are views of the same underlying files. Never copy or move between them in one operation — `cp` and `rsync` cannot tell that `/mnt/user/media/file` and `/mnt/disk3/media/file` are the same file, and the result is corruption or deletion. Stay entirely inside one view:

- Between user shares: `cp /mnt/user/share1/file /mnt/user/share2/file`
- From an external drive: mount it with Unassigned Devices and copy from `/mnt/disks/…`
- Verify a local copy with `rsync -c`

`/mnt/user0` (array-only, excluding pools) is deprecated and may be removed.

The boot device is not a disk share. To reach it over the network it is exported as a share historically named `flash` (the WebGUI labels the device **Boot device** on 7.3.0+); it is mounted at `/boot`.

## Creating and deleting shares

***Shares → Add Share***. Set the name, then optionally minimum free space, primary and secondary storage, allocation method, split level, included/excluded disks, and Mover action.

Share names are case-sensitive on disk even though SMB is not — avoid names differing only in case. `homes`, `global`, and `printers` are disallowed (Samba reserves them). A new share is **not** exported to the network until export settings are configured.

A share containing data cannot be deleted. Empty it first (File Manager, network access, or `rm -rf /mnt/user/<share>/*` with Docker and VM services stopped), then tick **Delete** on the share page.

## Primary and secondary storage

**6.12 and later.** Every share sets:

- **Primary storage** (required) — where new files are written first. Any pool, or the array. Default is `cache`.
- **Secondary storage** (optional) — where new files go when primary drops below its minimum free space, and the other end of Mover's transfer. If primary is a pool: None, Array, or another pool. If primary is the Array: None, or an eligible pool.
- **Mover action** — the direction: *Primary → Secondary* or *Secondary → Primary*.

Allocation method, split level, and included/excluded disks apply only when the array is one of the two locations; they are meaningless for pools.

**6.11 and earlier** used a single **Use cache for new files** setting, and this is what most older forum posts describe:

| Old setting | Behaviour | 6.12+ equivalent |
|---|---|---|
| Yes | Write to cache, Mover pushes to array | Primary = cache, Secondary = array, Mover cache → array |
| No | Write straight to array, Mover does nothing | Primary = array, Secondary = none |
| Only | Cache only; writes fail when full | Primary = cache, Secondary = none |
| Prefer | Write to cache, Mover pulls back from array | Primary = cache, Secondary = array, Mover array → cache |

## Mover

Mover transfers files between primary and secondary storage on a schedule set in ***Settings → Scheduler → Mover Settings***; the default is nightly. ***Main → Array Operation → Move*** runs it immediately.

Behaviour worth knowing:

- **Open files are skipped.** Turn off Docker and VM Manager in **Settings** before moving `appdata`, `system`, or `domains`, or those files silently stay put.
- Mover only acts on files inside user shares. Files at the root of a disk belong to no share and are never moved.
- Enable **Mover logging** in Mover Settings to log every file moved, visible in ***Tools → System Log***. Leave it off otherwise — it puts file paths and names into the syslog, which then appear in diagnostics.
- Parity must be valid before moving files array → cache.

**Moving a share from a pool to the array:** stop Docker and VM Manager → set Primary = the pool, Secondary = Array, Mover action = cache → array → **Move Now** → verify the pool is empty via the folder icon on the **Main** tab → re-enable services.

**Moving array → pool:** same, with Mover action array → cache. To pin a share to a pool afterwards, set Secondary = None.

**Moving between two pools:** there is no direct path. Run pool1 → array, then array → pool2. Or stop the services and `rsync` between `/mnt/pool1/share` and `/mnt/pool2/share` directly, verifying before deleting the originals.

**Why files end up in the wrong place:** `mv` between two shares under `/mnt/user` can be optimised into a rename, since both sit on the same mount point. The file never leaves its original disk or pool no matter what the share settings say. Use Mover, copy-then-delete, or move the file over the network.

## Allocation method

Applies when writing to the array. Decides which data disk receives a new file.

**High-Water (default, recommended).** Fills disks down to switch points based on half the largest drive's capacity. With 8 TB, 3 TB and 2 TB drives: first pass fills the 8 TB until 4 TB free; second pass fills 8 TB and 3 TB until 2 TB free; third pass fills all until 1 TB free. Keeps related files together and minimises spin-ups. Best for media libraries and mixed drive sizes.

**Most-Free.** Picks the disk with the most free space each time. Maximises balance, causes the most drive thrashing and spin-ups. Suits high-throughput work like video editing.

**Fill-Up.** Writes to disks in numeric order until each hits minimum free space. Requires minimum free space to be set, or writes fail with "disk full". Suits static archives and identical drive sizes.

## Split level

Controls how deep a folder tree may be split across disks. Level 1 is the share root.

- **Automatically split any directory** (default) — Unraid creates whatever folders it needs on whichever disk it picks. Best for downloads and loosely structured data.
- **Automatically split only top level** — first-level subfolders may be created anywhere; deeper files follow their parent folder's disk. Keeps each movie or TV show on one disk.
- **Automatically split top 'N' levels** — same idea, N levels deep.
- **Manual** — files only go where the parent directory already exists; no new directories are created.

Split level takes priority over both minimum free space and allocation method. That is why a share can throw "out of space" while other disks are nearly empty — the split rule forbade moving to them.

## Minimum free space

The amount of free space a device must retain to remain eligible for new files. Unraid cannot know a file's final size when it picks a disk, so a disk that fills mid-transfer produces a "disk full" error.

Set it to **twice the size of your largest file** (8 GB files → 16 GB). New shares default to 10% of disk capacity. Accepts KB/MB/GB/TB.

Pools have their own separate minimum free space, set on the **Main** tab under Individual Pool Settings. Whichever floor is reached first applies. Never set either to 0.

Updating an existing file (a growing backup image, a VM vdisk) does not trigger redistribution, so those can still fill a disk over time.

## Included and excluded disks

Restrict which array disks a share may write to. Configure one or the other, never both. With neither set, every disk permitted in ***Settings → Global Share Settings*** is eligible.

Selection order: included disks → excluded disks → split level → allocation method.

These affect **new writes only**. Existing files on now-excluded disks remain fully readable.

## Default shares

Created automatically once Docker or VM Manager starts:

- `appdata` — working files and configuration for each Docker container
- `system` — `docker.img` and `libvirt.img`
- `domains` — VM virtual disks (vdisks)
- `isos` — installation ISOs and driver images for VMs

All default to cache/pool-preferred for performance. Do not change permissions on `appdata`, `system`, or `domains` — it breaks containers and VMs. `isos` is the one meant to be reachable over the network, for adding installation media.

Do not put active VM vdisks on a share whose Mover action would push them to the array; performance collapses when Mover relocates a running VM's disk.

## Exclusive shares

Introduced in 6.12. When ***Settings → Global Share Settings → Permit exclusive shares*** is Yes, and a share's primary storage is a pool with secondary set to None (and the share exists nowhere else), Unraid replaces the FUSE path with a symlink straight into the pool directory. I/O bypasses the FUSE layer entirely, which matters for fast ZFS pools on fast networks. The Shares page flags **Exclusive access: Yes**.

Restrictions: both the share and pool minimum-free-space settings are ignored for new files. NFS export blocked exclusivity before 7.2; from 7.2 exclusive shares may be NFS-exported.

## Network export and security

Per share, at the bottom of the share settings page, for each enabled protocol:

**Export** — *Yes* (visible when browsing), *Yes (Hidden)* (reachable by name only), *No* (not accessible via that protocol).

**Security** — *Public* (anyone reads and writes), *Secure* (anyone reads, named users write), *Private* (named users only).

Protocol choice:

| Protocol | Default | Good for | Watch out for |
|---|---|---|---|
| SMB | Enabled | Windows and macOS, printers, VM storage | Slower with many small files |
| NFS | Disabled | Linux/Unix, small-file workloads | Needs extra tooling on Windows; the `fuse_remember` tunable addresses "stale file handle" errors |
| FTP | Disabled | Legacy or cross-platform transfers | Plaintext credentials; users must be listed in ***Settings → FTP*** or the service will not start |

AFP was removed in 6.9. For Macs, enable ***Settings → SMB → Enhanced macOS interoperability***.

Modern Windows (10 1709+, 11, Server 2019+) blocks guest access to Public SMB shares. Create user accounts rather than enabling insecure guest logons. Windows also holds only one credential set per server — to use two different accounts, connect to one share by hostname and the other by IP, which Windows treats as separate servers.

If files copied as root over the terminal end up with restrictive permissions, run ***Tools → New Permissions***, or Docker Safe New Perms for shares involved with containers.

## Users

Two kinds, and they do not overlap:

- **root** — the single administrator. Full WebGUI, SSH, and Telnet access. Supports SSH key authentication. **Cannot access SMB, NFS, or FTP shares.**
- **Share users** — created and managed by root at ***Users → Shares Access***. Access shares over SMB/NFS/FTP only. No WebGUI, SSH, or Telnet.

Usernames: lowercase, under 30 characters (a Windows limit). Per-share access is set on the user's edit page or the share's security section; existing shares can be adjusted but new ones cannot be added from the user page.

Deleting a user is immediate and permanent.

**Resetting a forgotten root password** needs physical access to the boot device and another computer. Root only: shut down, mount the boot device elsewhere, edit `/config/shadow` and change the `root:$…:15477:0:99999:7:::` line to `root::15477:0:99999:7:::`, save, reboot, set a new password. All users: delete `/config/shadow` and `/config/smbpasswd` instead. Anyone with physical access to the boot media can do this — keep it secure.

## Time Machine shares

1. ***Settings → SMB***: **Enable SMB** = Yes (requires the array stopped) and **Enhanced macOS interoperability** = Yes.
2. Create a user share. Set **Minimum free space** to `1` (1 KB) so Time Machine does not fail as disks fill, keep **Enable copy-on-write** on Auto, set **SMB export** to **Yes (Time Machine)**, and optionally set a Time Machine volume size.
3. On the Mac: Finder → ⌘K → `smb://<server-ip>/<share>` → authenticate → System Settings → Time Machine → Select Disk.

For several Macs, create one Unraid user and one share per machine (`tm-larry`, `tm-curly`) with private security, so backups and quotas stay separate. If Sequoia (15.x) gives intermittent failures, the Time Machine Docker container is the documented fallback.

## Docs links

- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/shares/
- https://docs.unraid.net/unraid-os/using-unraid-to/manage-storage/apple-time-machine/
- https://docs.unraid.net/unraid-os/system-administration/secure-your-server/user-management/
- https://docs.unraid.net/unraid-os/system-administration/secure-your-server/security-fundamentals/
