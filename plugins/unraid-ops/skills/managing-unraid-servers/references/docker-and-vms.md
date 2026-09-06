# Docker and VMs

Contents:
- [How Unraid runs Docker](#how-unraid-runs-docker)
- [Community Applications](#community-applications)
- [Container configuration](#container-configuration)
- [Autostart order and dependencies](#autostart-order-and-dependencies)
- [Managing running containers](#managing-running-containers)
- [Scheduling container actions](#scheduling-container-actions)
- [Docker troubleshooting](#docker-troubleshooting)
- [Plugins vs. containers](#plugins-vs-containers)
- [VM requirements](#vm-requirements)
- [Creating a VM](#creating-a-vm)
- [VM advanced options](#vm-advanced-options)
- [VM snapshots](#vm-snapshots)
- [PCI and GPU passthrough](#pci-and-gpu-passthrough)
- [VM troubleshooting](#vm-troubleshooting)
- [Docs links](#docs-links)

## How Unraid runs Docker

Containers and their images live in a single BTRFS-formatted virtual disk image, `docker.img`, in the `system` share (keep it on a pool for speed). Each container's working data belongs **outside** that image, in the `appdata` share — that is what makes the image safely disposable.

Container configuration is saved as XML templates on the boot device at `/boot/config/plugins/dockerMan/templates-user`, which is how **Previous Apps** can rebuild everything after the image is recreated.

Docker Compose is not natively supported.

Lime Technology supports the Docker subsystem itself; individual community containers are supported by their maintainers.

## Community Applications

The **Apps** tab, added by the Community Applications plugin — a catalogue of 2,000+ community containers and plugins. Install it from the Apps tab on a fresh server.

- **Install:** open the app tile → **Install**. Keep the window open until it finishes.
- **Remove:** Apps → *Installed Apps* filter → **Actions** → **Uninstall**.
- **Reinstall:** Apps → *Previous Apps* filter. Saved settings are reapplied automatically.
- **Action Center** (inside the Apps tab) flags updates, deprecated apps, incompatible apps, and blacklisted apps.

Support routes: Apps → Installed Apps → **Support**, or the container icon on the Docker/Dashboard tab → **Support**. Where a maintainer offers Discord, that is usually preferred over the forum.

Read the description and check the maintainer before installing anything that will be given access to the array, a pool, or sensitive data. CA moderation is basic vetting, not a guarantee.

## Container configuration

**Network type:**

| Type | Behaviour |
|---|---|
| Bridge (default) | Internal Docker network; only mapped ports are reachable. Safest and most common. |
| Host | Shares the server's network stack; any port, but conflicts are your problem. |
| None | No network access. |
| Custom (macvlan / ipvlan) | Container gets its own LAN IP and appears as a separate device. |

ipvlan has been the shipped default for custom networks since 6.11.5, and is what to switch to (***Settings → Docker***, advanced view) if the syslog shows macvlan call traces. Some routers (Fritzbox port forwarding) and network management tools (Ubiquiti) behave better with macvlan; on 6.12.4+ there is a better solution than the old two-NIC workaround.

If the server is on Wi-Fi: custom networks are forced to ipvlan, host access to custom networks must be disabled, and containers cannot use `br0`, `bond0`, or `eth0`. Docker cannot join two networks on the same subnet, so switching between wired and wireless means restarting Docker and reconfiguring every container. Pick one and stay on it.

**Volume mappings:** each maps a host path to a container path.

- Container paths are case-sensitive and start with `/`.
- Configure the application using the **container** path, not the host path — `/mnt/user/media` mapped to `/unraid_media` means the app is told `/unraid_media`.
- Application data belongs in `/mnt/user/appdata/<app>` mapped to `/config`, so it survives updates and reinstalls.
- Host paths are created automatically if missing — unexpected new folders on the server usually mean a typo in a mapping.
- For unassigned-device host paths, set the access mode to a **Slave** option.
- Use the most restrictive access mode (read-only vs. read/write) the container can work with.

**Port mappings:** on a bridge network, change only the **host** port — three containers all using 8000 internally can map to 8000, 8001, 8002. Leave the container port alone unless the application explicitly supports changing it. On a host network there is no mapping; avoid duplicate ports.

**Environment variables:** common ones are `TZ=America/New_York`, `PUID=99` and `PGID=100` (file ownership), `UMASK=022`, and app-specific keys. Prefer variables over baking values into images.

## Autostart order and dependencies

Toggle **Auto-Start** per container on the Docker tab. To control order: unlock the list with the padlock icon, drag containers into the desired order, switch to **Advanced View**, and set a **wait** value in seconds in the AutoStart column for any container that needs the previous one fully ready.

Order matters for databases before their applications, and VPN containers before anything routed through them. There is no built-in test — stop everything and start containers manually in the planned order, watching logs.

## Managing running containers

Click a container icon on the **Docker** or **Dashboard** tab for WebUI, Console, Stop, Pause, Restart, Logs, Edit, Remove, Project Page, Support, and More Info. Edits apply on save.

Health indicator: green = healthy, yellow = running but failing its health check, white = no health check defined (common and usually fine — health checks are the image author's choice).

CLI equivalents, using the name shown on the Docker tab:

```bash
docker start "container-name"
docker stop "container-name"
docker restart "container-name"
docker ps --filter "name=container-name"
docker logs "container-name"
```

## Scheduling container actions

Unraid has no built-in scheduler for containers. Install the **User Scripts** plugin, then ***Settings → User Scripts***: create a script per schedule (several containers can share one), pick a preset schedule or supply a cron expression (`0 3 * * 1` = 03:00 every Monday), and Apply.

## Docker troubleshooting

**Recreating `docker.img`** — the fix for a corrupted image, usually caused by a full pool or an unclean shutdown. Container settings survive because they live in templates on the boot device, and data survives because it lives in `appdata`.

1. ***Settings → Docker*** → **Enable Docker** = No → Apply.
2. Tick the option to delete the Docker vdisk → Apply.
3. Confirm the path and filename for the new image; keep the default size unless you know otherwise.
4. **Enable Docker** = Yes → Apply. Unraid creates and formats a fresh BTRFS image.
5. Apps → **Previous Apps** → select the containers → install. Settings are reapplied.

Verify mapped host paths still exist with correct permissions afterwards — bad mappings and permissions are the usual cause of a container failing to start post-restore.

**Custom networks do not survive image deletion.** Record them first with `docker network ls` (ignore `bridge`, `host`, `none`), then recreate each with `docker network create <name>` and repoint the containers. Host access to custom networks is toggled in ***Settings → Docker***.

**After an Unraid upgrade:** a one-time container migration can make the first start slow — wait it out. Errors like "layers from manifest don't match image configuration" mean the image needs recreating as above.

**Logs:** the Logs icon on the Docker tab, or `docker logs <name> > /path/log.txt`. Standard diagnostics contain only general Docker configuration, no per-container detail, so attach container logs separately when asking for help.

## Plugins vs. containers

Plugins integrate directly with Unraid OS and the WebGUI; containers are isolated. Prefer a container whenever the function does not need OS-level integration — plugins have full filesystem access, can destabilise the system after an OS update, and need manual compatibility checking. Reserve plugins for hardware, storage, and WebGUI features that genuinely cannot be containerised, and install them from the Apps tab where they get extra vetting.

Before upgrading Unraid, read the release notes for plugin-related warnings. CA only offers plugins believed compatible with the running release, but it will not remove already-installed incompatible ones.

**Safe Mode** loads Unraid without any plugins — the first diagnostic step when the system became unstable after a plugin install or update. Preferred method: ***Main → Array Operation*** → tick **Reboot in safe mode** → **Reboot** (no monitor needed). Alternative: choose **Unraid OS Safe Mode** at the boot menu.

## VM requirements

The **VMs** tab only appears when the hardware qualifies. Check ***Info*** in the top menu for HVM (Intel VT-x / AMD-V) and IOMMU (Intel VT-d / AMD-Vi) status; both must also be enabled in the motherboard BIOS.

| | Minimum | Recommended for passthrough |
|---|---|---|
| CPU | 64-bit, 4 cores, 2.4 GHz | 8+ cores, 3.0 GHz+ |
| Virtualization | HVM | HVM + IOMMU |
| RAM | 8 GB | 16 GB+ |
| Storage | SSD/NVMe for vdisks | High-end NVMe |
| GPU | — | NVIDIA RTX (better passthrough compatibility than AMD) |

Rough sizing: utility Linux VMs 1–2 GB and 1–2 vCPU; desktop VMs 4–8 GB and 2–4 vCPU; gaming or GPU-passthrough VMs 8–16 GB+ and 4–8+ vCPU. Resources are consumed only while a VM runs.

AMD GPUs are harder to pass through than NVIDIA, and some recent models (RX 7000/9000 series) may not work at all. AMD cards also commonly fail to restart a VM after shutdown because of function-level reset problems — ejecting the GPU inside Windows before shutdown is the usual workaround.

Under the hood: KVM plus QEMU, managed by libvirt, with VM XML stored in `libvirt.img` in the `system` share. Virtual disks live in `domains`, installation media in `isos`. VNC (built-in NoVNC) provides console access; VirtIO supplies paravirtualised disk and network drivers; VirtFS (9p) shares host filesystems with Linux guests.

**Networking:** `virbr0` is a libvirt-managed private NAT with its own DHCP — VMs reach the internet and the host but are invisible to the LAN, and mDNS does not traverse NAT. `br0` is a public bridge putting VMs directly on the LAN with their own IPs. On a Wi-Fi-connected server, use `virbr0`: Wi-Fi interfaces support only one MAC address, so public bridges are unavailable. Enable bridging in ***Settings → Network Settings***, then set the default in ***Settings → VM Manager*** (advanced view).

## Creating a VM

Preparation: enable virtualization and IOMMU in BIOS; put ISOs (and, for Windows, the VirtIO drivers ISO from the virtio-win project) in `isos`; point ***Settings → VM Manager*** at the VirtIO ISO and pick a default bridge. Keep active vdisks on a pool, never on a share whose Mover action would drag them to the array.

***VMs → Add VM***, then: choose a template (or Custom) → name and description → Autostart → OS type → CPU cores → initial memory → OS install ISO → primary vDisk location, size, and type → graphics (VNC, or a physical GPU for passthrough, plus a USB keyboard and mouse) → sound card (needed for HDMI audio over a passed-through GPU) → USB devices → **Create VM**.

USB devices must be attached before the VM starts; hot-plugging is unsupported, and the Unraid boot device cannot be assigned.

**User templates (7.1+):** edit a VM → **Create/Modify template** → name it. It then appears under User Templates on the Add VM screen, and can be exported, downloaded, and imported on another server.

## VM advanced options

Switch to **Advanced View** on the Add/Edit VM page.

- **CPU mode** — Host passthrough for maximum performance, Emulated for maximum compatibility.
- **Machine type** — `i440fx` is the Windows default; `Q35` is the Linux default and generally better for GPU passthrough. Keep the prefix when updating the version (`i440fx-2.5` → `i440fx-2.7`), never switch prefix on an existing VM.
- **BIOS type** — OVMF (UEFI) is required for Windows 8+, modern Linux, and GPU passthrough; SeaBIOS for legacy guests. **Settable only at creation time.**
- **vDisk type** — RAW is fastest; QCOW2 supports snapshots.
- **Memory ballooning** — set a Max Memory value; unavailable on VMs with PCI devices assigned.
- **Hyper-V extensions** — enable for Windows guests.
- **VirtFS (9p)** mappings for host/guest filesystem sharing on Linux guests.
- **CPU pinning** (***Settings → CPU Pinning***) — pinning assigns cores but Unraid may still use them; isolation dedicates them and requires a reboot. Pinning changes do not.

**Virtual GPU sharing:** set Graphics Card to **Virtual**, then VM console video driver to **VirtIO(3D)** for VirGL (Linux guests only, no physical monitor output, incompatible with Windows and standard NVIDIA plugins) or **QXL** for multi-screen and configurable video memory.

**Expanding a vDisk:** stop the VM → VMs tab → expand the VM → click the **Capacity** value → enter the new size (`100G`) → Enter. Then extend the partition inside the guest (Windows Disk Management; Linux `fdisk` / `pvresize` / `lvextend` / `resize2fs`). Shrinking is not supported.

## VM snapshots

Snapshots create an overlay file capturing all changes made after the point of capture; the VM then runs against the original disk plus the overlay. Requires QCOW2 vdisks. Metadata lives in `/etc/libvirt/qemu/snapshotdb/<VM_name>/`; the data sits alongside the VM files.

Create: VMs tab → expand the VM → **Snapshots** → **Create Snapshot** → name it. The **Memory dump** checkbox is not preselected: ticking it captures live RAM (full running state, larger and slower); leaving it clear produces a disk-only, crash-consistent snapshot (smaller and faster, unsaved in-memory data lost).

Operations:

- **Revert** — return to the snapshot state; everything after it is lost. Stop the VM first.
- **Block Commit** — write the overlay's changes back into the original disk. "Pivot" switches the VM back to the original disk; "Delete" removes the overlay. Both ticked is the usual choice.
- **Block Pull** — merge the original disk into the overlay so the overlay becomes standalone.
- **Remove** — delete the overlay without committing; post-snapshot changes are lost.

Useful before OS updates, before installing software, and at project milestones. Not a substitute for backups.

## PCI and GPU passthrough

Bind the device to `vfio-pci` first so Unraid releases it:

1. ***Tools → System Devices***.
2. Review the PCI device list and IOMMU groups. Devices in use by Unraid (disk controllers, NICs) cannot be selected.
3. Tick the device, plus its associated audio device when binding a GPU.
4. **Bind Selected to VFIO at Boot**.
5. Reboot.

Bound devices then appear under **Other PCI Devices** when editing a VM.

Notes: uninstall the old VFIO-PCI Config plugin if present — the function is built in. To reset all bindings, delete `/boot/config/vfio-pci.cfg` and reboot. Recheck bindings after any hardware change. Binding your only GPU means Unraid will not reach the local GUI.

When IOMMU groups do not separate cleanly, ***Settings → VM Manager → PCIe ACS override*** (Downstream or Both) splits them, at some stability risk. `vfio_iommu_type1.allow_unsafe_interrupts=1` in `syslinux.cfg` is a further step to take only with fully trusted guests.

**Manual ROM injection** — a last resort for GPUs that will not initialise (black screen). Download the matching ROM from the TechPowerUp VGA BIOS database, store it in `isos` or `domains`, stop the VM, edit its XML, and add a `<rom file='/mnt/user/isos/gpu_roms/your_gpu.rom'/>` line inside the GPU's `<hostdev>` block. Try BIOS and VM configuration changes first.

## VM troubleshooting

- **Black screen after start** — set the BIOS primary display to the iGPU, update motherboard and GPU firmware, switch SeaBIOS → OVMF, change machine type i440fx → Q35, then consider ROM injection.
- **Stuck at UEFI shell** — enter `fs0:`, then `cd efi/boot`, then `bootx64.efi` (try `fs1:` if `fs0:` fails). Recurring cases mean the boot order or boot device is wrong.
- **"Failed to set IOMMU for container: operation not permitted"** — IOMMU group conflict; use PCIe ACS override, then unsafe interrupts only if necessary.
- **"Invalid machine type"** — edit the VM and click Apply without changes to refresh it.
- **"Cannot get interface MTU" / network errors after upgrade** — repoint every VM to `br0` and set `br0` as the default bridge in VM Manager.
- **Poor performance after upgrade** — raise the machine type to the newest revision of the same prefix.
- **Slow or broken VNC** — set the VNC video driver to QXL; Cirrus or vmvga as fallbacks.
- **VM will not start** — verify the ISO and vDisk paths first.

**Shutdown behaviour matters for array health.** Configure VMs to **Hibernate** rather than Shutdown (***Settings → VM Manager → VM Shutdown***, advanced view), which requires the QEMU Guest Agent installed in the guest. Windows dialogs and in-progress updates can hold a shutdown open indefinitely; when the timeout expires Unraid force-kills the VM, risking guest corruption. Appliance VMs that cannot install the agent need longer timeouts instead. See `references/system-administration.md` for the timeout arithmetic.

## Docs links

- https://docs.unraid.net/unraid-os/using-unraid-to/run-docker-containers/overview/
- https://docs.unraid.net/unraid-os/using-unraid-to/run-docker-containers/managing-and-customizing-containers/
- https://docs.unraid.net/unraid-os/troubleshooting/common-issues/docker-troubleshooting/
- https://docs.unraid.net/unraid-os/using-unraid-to/create-virtual-machines/overview-and-system-prep/
- https://docs.unraid.net/unraid-os/using-unraid-to/create-virtual-machines/vm-setup/
- https://docs.unraid.net/community-applications/
