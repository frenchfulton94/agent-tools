# System Administration

Contents:
- [Boot media](#boot-media)
- [Internal boot (7.3+)](#internal-boot-73)
- [First boot and onboarding](#first-boot-and-onboarding)
- [BIOS settings](#bios-settings)
- [Licensing and device limits](#licensing-and-device-limits)
- [TPM-based licensing (7.3+)](#tpm-based-licensing-73)
- [Replacing the boot device](#replacing-the-boot-device)
- [Backing up the boot device](#backing-up-the-boot-device)
- [Updating and downgrading](#updating-and-downgrading)
- [Boot failures](#boot-failures)
- [Recovering an unknown array configuration](#recovering-an-unknown-array-configuration)
- [Diagnostics and logs](#diagnostics-and-logs)
- [SMART monitoring](#smart-monitoring)
- [UDMA CRC errors](#udma-crc-errors)
- [Unclean shutdowns and timeouts](#unclean-shutdowns-and-timeouts)
- [Notifications](#notifications)
- [Stability](#stability)
- [Command line](#command-line)
- [Unraid API](#unraid-api)
- [Wake-on-LAN](#wake-on-lan)
- [Docs links](#docs-links)

## Boot media

Unraid boots from USB flash or, from 7.3, an internal device. It loads into a root RAM filesystem; all configuration lives on the boot device in `/boot/config`.

USB boot requires a **unique hardware GUID** in programmable ROM — that GUID is the licensing identity. Drives lacking one, or reusing a GUID already registered to someone else, cannot be used and may be blacklisted.

Counterfeits are the usual cause of GUID problems, and the most-counterfeited brands are the best-known ones (SanDisk, Kingston, Samsung). The community-recommended alternatives are TeamGroup, Transcend, and PNY. Buy from reputable retailers; avoid auction sites, second-hand drives, SSDs presented as flash drives, and USB card readers or SD adapters (generic GUIDs).

Requirements: at least 4 GB, 32 GB or smaller recommended for ease of manual installs, USB 2.0 preferred over 3.0 for reliability.

**USB Creator (recommended)** — download for Windows, macOS, or Linux from unraid.net/download. Select language, release (latest stable for production), and target drive, keeping **Exclude system drives** ticked. Optional customisation sets server name, Wi-Fi, and DHCP or static IP before first boot. **WRITE** erases the drive. UEFI systems boot straight away; BIOS-only systems need the `make_bootable` script from the drive root (`make_bootable.bat` as administrator on Windows, `make_bootable_mac`, or `sudo bash ./make_bootable_linux` with the drive unmounted).

**Manual method** — format FAT32 (not exFAT or NTFS; Windows tools cannot FAT32 above 32 GB, so use Rufus), label the volume `UNRAID` in capitals, extract the release ZIP to the drive, and run `make_bootable` only if you need legacy boot.

**Unraid Installer** — a bootable installer for preparing the boot device on the target machine itself, useful for remote consoles and virtualised installs. Assets at github.com/unraid/bootable-unraid-installer: `-online.iso` and `-online.img.zip` download the OS ZIP during install; `-bundled.img.zip` already contains it. The menu offers Download ZIP, Set Internal Boot Size, Create Internal Boot, Create Flash Boot, network tools, a shell, and power controls. It refuses to overwrite its own device or the active root disk but will erase any other disk you select.

## Internal boot (7.3+)

Boots from an internal SSD, NVMe, or eMMC device instead of USB, using ZFS. Two devices create a mirrored boot set that survives one device failure; replace the failed one through the normal drive assignment flow.

Reasons to use it: USB flash media is the most failure-prone part of many builds, internal devices cannot be knocked out, and mirroring is possible. It does not make the array faster and is not needed if USB boot is working reliably.

Internal boot devices **count toward the license device limit**, both of them when mirrored.

Licensing is independent of boot method — you can boot internally and license from a USB stick. That licensing USB must be discoverable by its FAT volume label, `UNRAID` by default; a custom label needs a matching `unraidlabel=MYLABEL` kernel parameter, and labels are limited to 11 characters using A–Z, 0–9, `-`, and `_`.

If the system still boots from flash after switching, move the internal device to the top of the BIOS/UEFI boot order manually — Unraid attempts this automatically but firmware does not always cooperate. "Prohibited by secure boot policy" means Secure Boot needs disabling.

To restore a flash backup onto internal boot: restore it to a USB drive with the USB Creator, boot from that, then ***Settings → Onboarding Wizard*** → internal boot. Unraid copies the configuration across. Do not hand-place backup files into the internal boot partition.

## First boot and onboarding

Reach the WebGUI at `http://tower.local` (mDNS) or the server's IP from the router's DHCP list; or boot in GUI mode with a monitor and keyboard and sign in as `root` with no password. Set a strong root password when prompted — 12+ characters, mixed types.

The onboarding wizard (7.3+) covers server name and description, time zone, language, SSH and theme, boot method (flash, or internal single/mirrored with a chosen boot pool size), and optional preinstalled plugins. Relaunch it later from ***Settings → Onboarding Wizard***. Reboot after choosing internal boot.

Then sign in to Unraid.net from the **Get Started** panel to install a trial key, and configure storage.

## BIOS settings

- Boot device first in the boot order.
- Storage controller in **AHCI** mode, **HBA/IT mode** rather than RAID.
- **Secure Boot disabled** — Unraid does not support it.
- Hardware virtualization (Intel VT-x / AMD-V) and IOMMU (VT-d / AMD-Vi) enabled if you want VMs and passthrough.

If it will not boot, try boot order Forced-FDD → USB-HDD → USB-ZIP, toggling USB 2.0/3.0 support, toggling Fast Boot, and toggling USB keyboard support.

Many motherboards only allow selecting among 12 boot hard drives. If the flash drive is detected as a hard drive, 12 physical disks can push it off the list — configure the BIOS to treat it as removable, or disable INT 13h on an add-in HBA.

## Licensing and device limits

Perpetual licences, one per server. Starter and Unleashed include one year of updates with an optional $36/year extension; Lifetime includes updates for the life of the product. Not extending keeps your current version working forever, just without new updates.

| Tier | Parity array | Named pools | Devices per pool | Total attached devices |
|---|---|---|---|---|
| Starter | Up to 6 including parity | Up to 6 | Up to 6 | Up to 6 |
| Unleashed | Up to 30 (28 data + 2 parity) | Up to 34 | Up to 200 | Unlimited |
| Lifetime | Up to 30 (28 data + 2 parity) | Up to 34 | Up to 200 | Unlimited |

"Attached storage devices" means everything present **before array start**, except one eMMC device and one USB device. Unassigned devices count. Internal boot devices count. Devices attached *after* the array starts — a USB drive for a VM, say — do not. "Unlimited" means limited by hardware, not licence.

Upgrade paths (one-time fees): Starter → Unleashed $69, Starter → Lifetime $209, Unleashed → Lifetime $149, Basic → Unleashed $49, Plus → Unleashed $19, Basic → Plus $89, Basic → Pro $139, Plus → Pro $109. Upgrade from ***Tools → Registration*** or account.unraid.net/keys.

**Trials** run 30 days with no device limit, extendable twice by 15 days each (60 days total) from the Registration page with the array stopped. They require an internet connection at boot: the server has 30 seconds to reach the key server, and refreshing the WebGUI retries. Trials are tied to the boot device — moving to new media means starting over, and a trial configuration cannot start the array on a new device without a purchased key.

**Support policy:** two public minor series are supported at a time, and a public beta or RC counts as a public series. Older series are EOL and receive no fixes. Within a supported series use the latest patch build.

**Manual key install:** copy the key URL from account.unraid.net/keys and paste it into ***Tools → Registration → Install Key***; or drop the `.key` file into `/config` over the network and stop/start the array; or copy it into `/config` on the USB drive from another computer. Only one `.key` file may exist in `config`.

### TPM-based licensing (7.3+)

From 7.3 a licence can be bound to the motherboard's TPM 2.0 device instead of the boot device's GUID, which is more reliable than tying it to USB media. All new and replacement keys use TPM where possible.

Switch proactively at ***Tools → Registration → Move License to TPM***, which hands off to the Unraid Account site to approve the replacement. If the button is absent, Unraid could not find a TPM 2.0 device — check **Trusted Computing** in the BIOS, and leave Secure Boot disabled.

- Licensing method is independent of boot method: TPM licensing works while still booting from flash, and internal boot works with flash licensing.
- Moving to TPM blacklists the licence on the original USB device. You can move back to USB later via the normal replacement flow, or from one TPM motherboard to another via the TPM flow.
- A new motherboard is handled like a new USB device — only the original licence is blacklisted, not the board.
- BIOS updates and TPM resets should not affect the licence, since it uses the TPM identifiers. If one somehow does, replace the licence as for a new motherboard.
- No TPM header? Many older boards accept an inexpensive add-on module. Moving to TPM is optional, not required.
- TPM passed through to an Unraid VM is not supported.

Where the normal replacement flow cannot run because of hardware failure, contact Unraid support.

## Replacing the boot device

Replacing transfers the licence and **permanently blacklists the old device**.

Before replacing, check the old device for errors on another computer (Windows Scandisk or macOS Disk Utility). A single power outage can cause repairable corruption; repeated problems mean it needs replacing.

**With the USB Flash Creator:** insert the new drive, choose Operating System → **Use custom** → your backup ZIP → select the drive → Write. Swap the devices and boot. At `Invalid, missing or expired registration key` choose **Registration key**, ensure exactly one key file is in `boot/config`, then ***Tools → Registration → Replace key***, enter your email, and follow the emailed instructions.

**Manually:** prepare new media by the manual method, copy your backed-up `config` folder over it, swap, boot, and do the same Replace key flow.

The first replacement can happen any time; after that the automated route is limited to once per 12 months. For an earlier replacement, contact Unraid support with the old and new GUIDs, the licence key, and the purchase email. If you are locked out and need the server now, start a fresh trial on a new drive and contact support to move the licence.

A "keyfile is not valid" error means the key is blacklisted or is not the most recent valid key.

## Backing up the boot device

Back up after any significant configuration change, before OS upgrades and plugin installs, after adding or removing drives, and periodically. Store backups off the server — the array may be down when you need them.

**WebGUI:** ***Main*** → select the boot device → **Boot Device Backup** (on releases before 7.3.0, ***Main → Flash device → FLASH BACKUP***) → save the ZIP somewhere safe.

**Manual:** shut down, mount the device elsewhere, copy everything.

**Unraid Connect automated flash backup:** ***Settings → Management Access → Unraid API*** → **Activate** under Flash backup. After the initial backup, configuration changes sync within 1–2 minutes. It stores configuration only — not logs, not application binaries, not a full drive image. Files above 10 MB are skipped; if the repository exceeds 100 MB it is deleted and recreated. `config/shadow` and `config/smbpasswd` are deliberately excluded, as are WireGuard keys, so after restoring you must reset every password including root and regenerate every WireGuard tunnel and peer key. Docker template XML *is* included and can contain application credentials. Backups are currently stored unencrypted. Restore via Connect → Details → **Generate flash backup** → **Download flash backup** → write with the USB Creator.

Also keep a screenshot of your disk assignments after any hardware change.

## Updating and downgrading

Before updating: back up the boot device, read the release notes for the target version, update all plugins, optionally stop the array.

**7.x:** top-right menu → **Check for Update**, or ***Tools → Update OS*** → **View Changelog to Start Update** → review → **Continue** → **Confirm and start update** → reboot. **6.11–6.12:** ***Tools → Update OS*** → Check for Updates → Update → reboot.

Release branches (Stable / Next) are switched in the Unraid account app — top-right account menu → **Manage Unraid.net Account** — not inside the OS.

Release types: **Stable** for production; **RC** for final validation on test systems; **Beta** for early testing on non-production hardware. Do not linger on old betas or RCs.

**ZFS pool upgrade warnings** after moving to 7.x are informational — the pool is using older ZFS features. Upgrading the pool may prevent rolling Unraid back, so it is not urgent.

**Downgrading:** read the target version's release notes, particularly its "Rolling back" section. ***Tools → Downgrade OS*** returns you to the previously installed version if its files are still on the boot device. Otherwise, download the ZIP from the Version Archive, unzip, create a `previous` directory on the boot volume, move all `bz*` files and `changes.txt` into it, copy the new `bz*` and `changes.txt` to the root, reboot. The command-line equivalent downloads and swaps the same files under `/tmp` before rebooting.

## Boot failures

The boot sequence: BIOS/UEFI → syslinux loader (`syslinux/syslinux.cfg`, editable at ***Main → Syslinux configuration***; Memtest86+ is on the menu) → Linux core loading `bz*` files into RAM → boot volume mounts at `/boot` (must be labelled `UNRAID` in capitals; check with `df`) → plugins → WebGUI (`config/go` runs user commands here) → array mounts, shares appear, containers and autostart VMs launch.

Work through in order: use a USB 2.0 port; confirm the BIOS boot target; check the device for errors on another computer; re-extract the `bz*` files onto the boot volume; rebuild from a clean Unraid copy and restore only the `config` folder; boot into Safe Mode to rule out plugins; test with fresh media and a clean install to isolate hardware; transfer the licence to new media if needed.

For UEFI, the `EFI` folder on the boot volume must not have a trailing `~`. Renaming `EFI~` to `EFI` enables UEFI boot; the WebGUI equivalent is ***Settings → Boot device*** (7.3.0+) or ***Settings → Flash device*** (earlier).

## Recovering an unknown array configuration

If the boot device is lost and the parity assignments are unknown, use the fact that **parity disks carry no filesystem** and therefore will not mount.

1. Build new boot media and boot without assigning drives.
2. Activate a licence (trial, or transfer the existing one).
3. Identify parity: either assign every drive as a data disk and start the array — the unmountable ones are the parity disks (this invalidates parity, so it must then rebuild) — or install the **Unassigned Devices** plugin and mount each disk read-only one at a time, which preserves parity.
4. Confirm the number of unmountable drives matches your expected parity count. If there are more, stop and ask on the forums.
5. Note the serial numbers, then ***Tools → New Config*** retaining assignments where possible.
6. Assign parity and data correctly on the **Main** tab. Never assign a data disk to a parity slot.
7. Start the array. With a **single** parity disk, data disk order does not matter, and "Parity is Already Valid" may be ticked only if you are certain the same physical parity disk is in place and nothing has been written. With **dual** parity, both data order and the parity1/parity2 assignment matter, and parity must be rebuilt if either changed — so do not tick the box when parity was identified by elimination, since the odds of getting parity1 and parity2 the right way round are even.
8. Recheck each share's include/exclude settings, since disk order may have changed.
9. Run a parity check.

Do not click **Format** on anything during this.

## Diagnostics and logs

***Tools → Diagnostics*** produces an anonymised ZIP: system configuration, kernel and service logs, hardware details, and general Docker/VM configuration (no per-container detail). Attach the single ZIP to forum posts, not the extracted files. Without the WebGUI, run `diagnostics` over SSH or console — it writes to `/boot/logs`.

Capture diagnostics with the array started in normal mode where possible, and always **before rebooting**. `/var/log` is a RAM disk.

Mover logging adds file paths and names to the syslog, which then reach diagnostics — enable it only while troubleshooting Mover itself.

**Persistent logging** (***Settings → Syslog Server***):

| Method | Pros | Cons | Good for |
|---|---|---|---|
| Mirror syslog to boot drive | Captures boot events and pre-crash entries | Heavy writes wear the boot device | Days, not weeks |
| Remote syslog server | Logs on another machine | Needs an always-on server | Long-term |
| Local syslog server | Logs on the array or a pool, no boot-device wear | Less accessible after a crash | Continuous logging |

Unraid already copies the syslog to the boot device on every graceful shutdown ("Copy syslog to boot drive on shutdown", on by default and safe). Both methods produce `/boot/logs/syslog-previous` after the next boot, readable at ***Tools → Syslog → syslog-previous*** and included anonymised in diagnostics. For the local syslog server, also set **Remote syslog server** to the server's own IP (loopback) or nothing is written to the chosen share. Local and remote syslog files are **not** anonymised — review before posting them.

**Drive read performance:** `hdparm -tT /dev/sdX` gives cached and buffered read speeds; run it several times. Use physical devices, not `/dev/md1`, which includes parity work. The **DiskSpeed** container from Community Applications tests all drives at multiple offsets and produces heat maps that expose bad zones and SMR behaviour.

## SMART monitoring

Available for SATA drives, not SAS. Unraid watches key attributes and shows an orange icon on the Dashboard when one changes; clicking it lets you acknowledge, after which you are only alerted again if it worsens. Acknowledging does not fix anything.

| ID | Attribute | Action |
|---|---|---|
| 5 | Reallocated sectors | Above 0 means the drive is degrading. Growing → back up and replace |
| 187 | Reported uncorrected errors | Above 0 is serious — replace |
| 188 | Command timeout | Occasional is normal; frequent means cables or power |
| 197 | Current/pending sectors | Above 0 means unreadable areas. Not returning to 0 within days → replace |
| 198 | Uncorrectable sectors | Above 0 means data already lost — replace immediately |
| 199 | UDMA CRC errors | Cabling. Reseat SATA cables; fine if it stops climbing |

Commands: `smartctl -a /dev/sdX` (add `-d ata` or `-d nvme` if it errors), `smartctl -t short /dev/sdX`, `smartctl -t long /dev/sdX`, `smartctl -a /dev/sdX > /boot/smart_report.txt`.

## UDMA CRC errors

Attribute 199 counts failed integrity checks on the link between drive and controller — a communication problem, not usually a failing drive. Unraid retries; a successful retry costs only speed, a failed one is treated as a read error, and parity rewrites the sector if it can. If that fails the drive is disabled.

Causes, in likelihood order: loose or poorly seated SATA cables; faulty or cheap cables; power delivery problems (splitters, overloaded PSU); an unseated controller card; cable management issues (over-tight ties — use Velcro; power cables run alongside SATA data cables — cross them at 90° if they must touch; forced 90° bends in SATA cables); and rarely the drive itself.

The count is cumulative and never resets, so judge by **rate of increase**. A handful over months is unremarkable; daily or weekly increments need attention. CRC errors appearing alongside pending sectors (197) is the dangerous combination — back up immediately, run an extended SMART test, and prepare to replace.

## Unclean shutdowns and timeouts

An unclean shutdown triggers an automatic parity check at the next boot, in the mode set at ***Settings → Scheduler → Parity Check*** (non-correcting by default). Unraid tries to save diagnostics to `/log/diagnostics.zip` on the boot device.

Causes: power loss; a boot device that went read-only or missing, so the shutdown status could not be written; and open terminal or SSH sessions that Unraid waits on until the timer expires (the Dynamix Stop Shell plugin closes them automatically — but be careful with running writes).

**UPS:** connect via USB and enable ***Settings → UPS Settings***. Unraid supports apcupsd-compatible units (APC and CyberPower generally work); the NUT plugin covers others. Set the battery runtime or charge thresholds so shutdown starts with enough time to stop the array, and test by simulating an outage.

**Timeouts:**

| Setting | Default | Increase to | Location |
|---|---|---|---|
| VM shutdown | 60s | 300s if not hibernating and VMs crash | ***Settings → VM Manager → VM Shutdown*** (advanced) |
| Docker container stop | 10s | 30s if containers crash on stop | ***Settings → Docker*** (advanced) |
| General shutdown | 90s | 180s, or 300s+ with VMs | ***Settings → Disk Settings → Shutdown time-out*** |

Shutdown order: VMs in three stages, each able to consume the full VM timeout (resume paused → hibernate → shut down remaining), so VM time is timeout × 3; then Docker containers in parallel; then LXC and plugins; then array unmount and sync, 15–30 seconds.

General timeout > (VM timeout × 3) + Docker timeout + other services + 15–30s.

The real fix is **hibernation**: set VMs to Hibernate rather than Shutdown, which requires the QEMU Guest Agent in the guest (from the virtio-win ISO on Windows, `qemu-guest-agent` package on Linux, enabled via systemd). Hibernation is near-instant, preserves state, and sidesteps Windows update and unsaved-document dialogs entirely. Without it there is no genuinely safe Windows timeout. Verify by stopping a VM with applications open and confirming they are still open on restart.

Whatever you set, the timeout must fit inside the UPS runtime for power-loss shutdowns.

## Notifications

***Settings → User Preferences → Notification Settings***. Configure display style and position, which events notify (system, OS updates, plugin updates, Docker updates, language updates, array status) with per-type frequency, and delivery per severity (Notices, Warnings, Alerts) via Browser, Email, or Agents.

**SMTP:** presets for Gmail and Outlook, or custom. Ports: 465 SSL/TLS, 587 STARTTLS, 25 unencrypted. Gmail requires an app password with 2-Step Verification enabled — generate one in Google Account → Security → App passwords and use it instead of the account password; Gmail defaults are `smtp.gmail.com`, port 465, SSL/TLS yes, STARTTLS no, auth Login. Use the **TEST** button.

**Agents:** Bark, Boxcar, Discord, Gotify, ntfy.sh, Prowl, Pushbits, Pushbullet, Pushover, Pushplus, ServerChan, Slack, Telegram. Set Agent function to Enabled, supply the webhook URL or token, and map title to Subject and message to Description. Every notification goes to every enabled agent.

Enable notifications early — most Unraid data-loss stories start with an unnoticed warning.

## Stability

**RAM** is the most common cause of unexplained crashes, corruption, and failed parity checks. Memtest86+ is on the boot menu and works in both legacy and UEFI mode; run it 2–4 hours minimum, reseat and test sticks individually if it errors. XMP and AMD AMP profiles are overclocks: for a server, run at SPD speeds. Buy RAM from the motherboard's QVL, not the RAM vendor's.

**Power:** the 12 V rail must handle simultaneous spin-up of every drive, not staggered. Avoid splitters. Check cords and circuit loading.

**Thermals:** keep ambient at 18–24 °C, ventilate, clean dust, monitor temperatures.

**Plugins:** prefer containers; use Safe Mode to isolate; remove unused plugins; check compatibility before OS upgrades.

**Firmware:** keep motherboard and controller firmware current, back up configuration first.

## Command line

Open the web terminal from the top-right `>_` menu (a root shell), or connect over SSH. Find each disk's `sdX` or `nvmeX` identifier on the **Main** tab.

Storage: `lsblk`, `df -h`, `fdisk -l /dev/sdX`, `blkid /dev/sdX1` (verify the boot volume label is `UNRAID`), `blockdev --getsz /dev/sdX` (512-byte sectors, for confirming a replacement is large enough), `hdparm -I /dev/sdX`, `ls -l /dev/disk/by-id/ | grep -v part`.

Monitoring: `top` (or `htop`), `free -h`, `ps aux --sort=-%mem | head -20`, `ps aux --sort=-%cpu | head -20`.

Network: `ss -tuln` (listening ports), `ss -tup` (established with processes), `ip -c addr show`, `ip route show`, `ping -c 4 google.com`, `ethtool eth0` (link speed), `ethtool -i eth0` (driver), `ethtool -S eth0` (statistics).

System: `tail -f /var/log/syslog`, `tail -n 50 /var/log/syslog`, `powerdown` (the correct way to shut down — it stops the array properly), `diagnostics`, `use_ssl no|yes`.

CPU features: `lscpu`, and `grep -E 'lm|vmx|svm' /proc/cpuinfo` (`lm` 64-bit, `vmx` Intel VT-x, `svm` AMD-V).

**Transferring from an external SMB share:** `mkdir /work`, then `mount -t cifs //workstation/share /work -o username=youruser,iocharset=utf8` (password prompted interactively) or with `credentials=/root/.cifscredentials` (`chmod 600`) for scripts. Never put a password in the command line — it lands in shell history and process listings. `iocharset=utf8` preserves international filenames. Copy with `cp -r` or `rsync -av --progress`, then `umount /work` and `rmdir /work`. Midnight Commander (`mc`) is built in and gives a two-pane interface over the same mounts. Krusader, Double Commander, and CloudCommander are container alternatives.

Files copied as root may end up with restrictive permissions — fix with ***Tools → New Permissions***, or Docker Safe New Perms for shares involving containers.

## Unraid API

A GraphQL API, built into the OS from 7.2 and available via the Unraid Connect plugin before that. Configure at ***Settings → Management Access → API***. Authentication by API key, session cookie, or SSO/OIDC. You do not need to sign in to Unraid Connect to use the API locally.

`unraid-api` commands: `start`/`stop`/`restart` (with `--log-level trace|debug|info|warn|error|fatal`, or the `LOG_LEVEL` env var), `logs [-l lines]`, `config`, `switch-env -e production|staging`, `developer --sandbox true|false` (Apollo GraphQL sandbox at `/graphql`), `apikey --create --name <n> -r <roles> -p <permissions>`, and `sso add-user` / `sso remove-user`. Keys and OIDC providers can also be managed at ***Settings → Management Access → API Keys*** and **→ OIDC**.

`unraid-api restart` is the standard fix for Unraid Connect connection errors.

## Wake-on-LAN

Requirements: a NIC supporting WoL; WoL enabled in BIOS (look for "Wake on LAN", "PME event wake-up", "Power on by PCI/PCIe devices", and set "ErP ready" to *disabled*); mains power connected; a wired Ethernet connection — Wi-Fi WoL is not supported.

Use the **Dynamix S3 Sleep** plugin (***Settings → Sleep Settings***) for scheduling sleep, wake, and idle behaviour. Manually: find the interface and MAC with `ifconfig`, enable with `ethtool -s eth0 wol g`, sleep with `echo -n mem > /sys/power/state`. Manual settings do not persist — add `/usr/sbin/ethtool -s eth0 wol g` to `/boot/config/go`.

Not all hardware handles S3 sleep or WoL reliably; test before depending on it.

## Docs links

- https://docs.unraid.net/unraid-os/getting-started/set-up-unraid/create-your-bootable-media/
- https://docs.unraid.net/unraid-os/getting-started/set-up-unraid/internal-boot-faq/
- https://docs.unraid.net/unraid-os/getting-started/set-up-unraid/customize-unraid-settings/
- https://docs.unraid.net/unraid-os/troubleshooting/licensing-faq/
- https://docs.unraid.net/unraid-os/system-administration/maintain-and-update/changing-the-flash-device/
- https://docs.unraid.net/unraid-os/updating-unraid/
- https://docs.unraid.net/unraid-os/troubleshooting/diagnostics/capture-diagnostics-and-logs/
- https://docs.unraid.net/unraid-os/troubleshooting/common-issues/unclean-shutdowns/
- https://docs.unraid.net/unraid-os/system-administration/advanced-tools/command-line-interface/
- https://docs.unraid.net/API/
