# Remote Access and Security

Contents:
- [Choosing a remote access method](#choosing-a-remote-access-method)
- [Tailscale](#tailscale)
- [Tailscale for Docker containers](#tailscale-for-docker-containers)
- [WireGuard](#wireguard)
- [Unraid Connect](#unraid-connect)
- [SSL and WebGUI access](#ssl-and-webgui-access)
- [Port forwarding risk](#port-forwarding-risk)
- [Outgoing traffic](#outgoing-traffic)
- [Security checklist](#security-checklist)
- [Docs links](#docs-links)

## Choosing a remote access method

Never expose the WebGUI directly to the internet. In order of preference:

| Method | Use when | Requires |
|---|---|---|
| **Tailscale** | Default recommendation for full remote management | Plugin + free Tailscale account; no port forwarding |
| **WireGuard** | Custom routing, server-to-server or LAN-to-LAN tunnels, no third party | UDP 51820 forwarded, or UPnP |
| **Unraid Connect (sign-in only)** | Dashboard monitoring and supported actions across several servers | Unraid.net account, myunraid.net certificate |
| **Unraid Connect Remote Access** | You specifically need public browser access to the full WebGUI | WAN port forwarding or UPnP — treat as a last resort |
| **Router VPN** | Your router already provides one | Router-dependent |

Signing in to Unraid Connect is *not* the same as enabling Connect Remote Access. The first keeps an outbound connection with restricted API access; the second publishes the WebGUI to the internet.

## Tailscale

A WireGuard-based peer-to-peer overlay network (a "tailnet"), maintained as an official Unraid plugin under a technology partnership, with native certificate support from Unraid 7. Free accounts cover 3 users and 100 devices.

Before adding the server, consider renaming the tailnet, enabling MagicDNS, and enabling HTTPS certificates. Machine names in HTTPS certificates are published in a public certificate ledger — pick names you are willing to disclose.

Setup:

1. Install the official **Tailscale** plugin from the Apps tab.
2. ***Settings → Tailscale → Settings***, enable **Advanced View**, click **Reauthenticate**, sign in.
3. Click **Connect** to join the tailnet.
4. ***Settings → Management Access*** now shows Tailscale URLs for the WebGUI.
5. ***Settings → Tailscale*** shows the tailnet name and IP for reaching shares and containers.
6. Optionally enable **Include Tailscale peers in /etc/hosts** so the server can resolve other tailnet devices by hostname.

**Subnet routing** — to reach the server by its normal LAN IP, or reach other LAN devices: ***Settings → Tailscale*** → Reauthenticate → **Advertise Routes** → add `192.168.0.12/32` (just the server) or `192.168.0.0/24` (the whole LAN) → Apply → then approve the route in the Tailscale admin console under **Machines**.

## Tailscale for Docker containers

Each container can become its own tailnet device, so access can be shared per container rather than per server. Unraid automates the plumbing: it extracts the container's original Entrypoint and CMD, injects `tailscale_container_hook`, passes the originals plus Tailscale variables through the run command, starts the Tailscale client inside the container, then hands off to the original entrypoint.

1. Docker tab → edit the container → enable **Use Tailscale**.
2. Give it a unique **Tailscale hostname** (an HTTPS certificate is generated and published publicly for this name).
3. Decide whether it acts as an exit node, uses an exit node, and whether it may also reach the LAN.
4. Leave **Userspace Networking** at its automatic value unless there is a specific need.
5. Optionally enable Tailscale SSH.
6. Optionally enable **Serve** (HTTPS URL reachable only inside the tailnet) or **Funnel** (HTTPS URL reachable from the public internet — neither adds an authentication layer, so the container must secure itself).
7. Apply, then check the log for the "To authenticate, visit…" link.

Userspace networking enabled = container cannot initiate connections to other tailnet devices or use Tailscale DNS, but stays reachable on both URLs. Disabled = full tailnet access and Tailscale DNS, but the original WebUI URL may not work. Exit nodes always have it enabled; containers using an exit node always have it disabled.

Network type compatibility: `host` cannot use Tailscale integration at all; `bridge` works, with the original WebUI URL available only when userspace networking is enabled; `eth0`/`br0`/`bond0` expose both URLs either way.

This does not work with every container — anything with custom networking or strict isolation may break. Test on something non-critical first.

If the log shows "Couldn't detect persistent Docker directory for .tailscale_state", pick a mapped path, enable Tailscale **Show advanced settings**, set the **State directory** to `/that-path/.tailscale_state`, and restart.

## WireGuard

Built into Unraid. Choose it over Tailscale for custom VPN routing, persistent server-to-server or LAN-to-LAN tunnels, integration with existing network infrastructure, or maximum throughput with minimum overhead.

Prerequisites: a dynamic DNS name if the public IP changes (Cloudflare, No-IP, DuckDNS); UPnP enabled in ***Settings → Management Access***, or UDP port 51820 manually forwarded to the server; a WireGuard client on each device.

1. ***Settings → VPN Manager*** → name the tunnel → **Generate Keypair**. Store the private key like a password.
2. Set **Local endpoint** to your DDNS hostname if using one. Keep port 51820 unless it clashes.
3. Confirm port forwarding (UPnP or manual, same port inside and out).
4. Toggle **Active**, and **Autostart** to bring it up at boot.
5. **Add Peer** → name it → choose the connection type (usually *Remote access to LAN*) → **Generate Keypair** → optionally a preshared key → Apply. Letting Unraid generate the keys produces complete client configs, including a QR code for mobile.

Connection types available: remote access to server, remote access to LAN, server-to-server, LAN-to-LAN, server hub-and-spoke, LAN hub-and-spoke, VPN-tunnelled access for Docker, and remote tunnelled access (route all client traffic through the server).

**DNS:** mDNS names like `tower.local` do not work over the tunnel. Use IPs or FQDNs, or switch VPN Manager to Advanced mode and set **Peer DNS Server** to your router's IP or a public resolver. This matters most for remote tunnelled access.

**Complex networks** — reaching Docker containers with their own IPs or VMs with strict networking requires all three of: **Use NAT** = No in the tunnel config, a static route on the router for the tunnel network (e.g. `10.253.0.0/24`) pointing at the server, and ***Settings → Docker Settings → Host access to custom networks*** = Enabled. Partial combinations silently break things — NAT=Yes with host access enabled, or NAT=No without the static route, both leave parts of the network unreachable.

**Troubleshooting.** WireGuard is silent by design, so work the checklist: tunnel active on both ends ("active" is not "connected"); DDNS resolving to the current public IP and set as Local endpoint; the right UDP port forwarded; clients holding the latest config after any server-side change; changes saved before distributing configs. Then: test the first client on cellular rather than Wi-Fi; generate traffic (ping) to trigger a handshake; disable battery/data saver on mobile clients; ensure client and server subnets differ; set Cloudflare DDNS records to *DNS only*, not *Proxied*; remember some networks block UDP entirely and WireGuard has no TCP fallback; check in Advanced mode that the local tunnel network pool does not overlap anything.

Adding a peer can briefly drop the tunnel — keep local access available. If the WebGUI becomes unreachable because of WireGuard autostart, delete `/boot/config/wireguard/autostart` from the boot device and reboot.

## Unraid Connect

A plugin (Unraid 6.10+) giving a cloud dashboard at connect.myunraid.net across all your servers: online status, license type, uptime, OS version and update availability, storage totals, CPU/memory/temperature, notifications, and flash backup status. Supported actions include starting and stopping arrays, Docker and VM control, parity checks and scrubs, flash backup, diagnostics download, notification acknowledgement, reboot and shutdown, and license management.

Install from the Apps tab, then click the Unraid logo top-right → **Sign In** with Unraid.net credentials. It needs a myunraid.net certificate (***Settings → Management Access*** → **Provision**).

Data transmitted: hostname, description and icon; keyfile details and flash GUID; local access URL and LAN IP (only with a certificate installed); remote access URL and WAN IP (only if remote access is on); Unraid version and uptime; plugin and API versions; array size and usage as numbers only; counts of containers and VMs. Only the most recent update is retained, and nothing is shared with third parties beyond what certificate provisioning requires.

Sign out at ***Settings → Management Access → Unraid Connect → Account Status***. Uninstalling deletes local flash backup files, marks cloud backups for removal (purged after 30 days), disables remote access — remove the router port forward yourself — and signs the server out. It does not revert the access URL; use `use_ssl` or the Management Access settings for that.

Connection errors: `unraid-api restart` from a terminal.

## SSL and WebGUI access

Parameters: **Server name** (***Settings → Identification***, default `tower`), **Local TLD** (***Settings → Management Access***, default `local`), **Use SSL/TLS**, HTTP port 80, HTTPS port 443, certificate type, and a unique 40-character hash assigned to your server.

| Certificate | Result |
|---|---|
| Self-signed | Encrypted, but browsers warn every time |
| Myunraid.net | Browser-trusted, no warnings; URL is `https://<lan-ip-with-dashes>.<hash>.myunraid.net` |
| Custom | Your own or a wildcard cert; you manage DNS and renewal |

**Use SSL/TLS** values: *No* (plain HTTP, no redirect), *Yes* (redirects to `https://<servername>.<localTLD>`, works with the internet down), *Strict* (redirects to the myunraid.net URL — inaccessible if DNS is unavailable). Redirects only trigger when starting from an HTTP URL.

To provision a myunraid.net certificate: ***Settings → Management Access*** → **Provision**.

**Custom certificates:** set Local TLD to the certificate's domain, upload to `/boot/config/ssl/certs/<servername>_unraid_bundle.pem`, and ensure the certificate covers `<servername>.<localTLD>` or `*.<localTLD>` in the Subject or a Subject Alternative Name (SANs supported from 6.10.3). A certificate that does not match the server URL is deleted and replaced with a default.

**DNS rebinding protection** on many routers blocks public DNS names resolving to LAN IPs and causes provisioning to fail. Click OK, wait 2–5 minutes, retry; if it persists, allow rebinding for `myunraid.net` in the router and allow time for propagation.

**Locked out because DNS or the internet is down:** log in via SSH, Telnet, or a local keyboard and run `use_ssl no` (plain HTTP) or `use_ssl yes` (self-signed HTTPS). Restore **Strict** once DNS is back.

## Port forwarding risk

Only forward ports you understand and need.

| Port(s) | Service | Risk | Instead |
|---|---|---|---|
| 80 / 443 | WebGUI | Management interface exposed; brute force | Tailscale or VPN |
| 445 | SMB | Shares exposed; theft or deletion | VPN |
| 111 / 2049 | NFS | Same as SMB | VPN |
| 22 / 23 | SSH / Telnet | Console access; credential theft | SSH keys or VPN; never forward Telnet |
| 57xx | VNC for VMs | Unauthorised VM console access | Tailscale or VPN |

If you find a forwarding rule you cannot explain, remove it and watch for breakage. Never place the server in the router's DMZ — that exposes every port regardless of password strength.

## Outgoing traffic

Three options, in ***Settings***:

- **Outgoing Proxy Manager** — routes only Unraid's own HTTP requests through a proxy. Add name, URL, and credentials, Apply, select it, Apply again. Reopen any web terminals or SSH sessions afterwards. Plugins using PHP `curl_init()` pick it up automatically; `file_get_contents()` does not. Prefer `curl` over `wget` in scripts. Legacy Proxy Editor plugin settings and `community.applications/proxy.cfg` are imported automatically on upgrade to 7.0+.
- **Tailscale exit nodes** — ***Settings → Tailscale → Use Exit Node***. The exit node can be another server, a container, or any tailnet device; Tailscale also resells Mullvad exit nodes.
- **WireGuard tunnels to a commercial VPN** — ***Settings → VPN Manager → Import Config***, upload the provider's config, name it, Apply, set Active. For per-container routing keep the default peer type *VPN tunneled access for Docker*, note the tunnel name (`wg0`, `wg1`), and set affected containers' Network Type to **Custom: wgX**, adding `--dns=8.8.8.8` in Extra Parameters if the provider supplies no DNS. For system-wide routing only one tunnel can be active at a time, Unraid ignores DNS settings in the imported config so set a reliable resolver yourself, and you may need to disable the tunnel for OS updates and plugin installs. Test with a Firefox container against whatismyipaddress.com and dnsleaktest.com.

## Security checklist

- Set a strong root password (Unraid enforces no complexity rules of its own). The Dynamix Password Validator plugin gives live feedback.
- Apply least privilege: create per-purpose share users, grant read-only where write is not needed, review and remove unused accounts.
- Set sensitive shares to **Private**. Unraid shares default to publicly readable and writable, which means any compromised device on the LAN — including IoT devices — can read, delete, or encrypt them.
- Set the boot device's SMB export to **No**. If it must be shared, make it **Private** with a strong password, and disable it when not in use. It holds configuration and licensing.
- Keep the OS, plugins, and containers updated; enable update notifications in ***Settings → Notifications***.
- Files on the boot device cannot be executable. Run scripts through an interpreter, or copy them to `/usr/local/bin` from `config/go` and set the execute bit there.
- Review installed plugins periodically — they run with full filesystem access.

## Docs links

- https://docs.unraid.net/unraid-os/system-administration/secure-your-server/security-fundamentals/
- https://docs.unraid.net/unraid-os/system-administration/secure-your-server/tailscale/
- https://docs.unraid.net/unraid-os/system-administration/secure-your-server/wireguard/
- https://docs.unraid.net/unraid-os/system-administration/secure-your-server/securing-your-connection/
- https://docs.unraid.net/unraid-os/system-administration/secure-your-server/secure-your-outgoing-comms/
- https://docs.unraid.net/unraid-connect/overview-and-setup/
