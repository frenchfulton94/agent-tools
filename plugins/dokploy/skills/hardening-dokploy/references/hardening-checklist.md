# Hardening checklist and compliance mapping

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [Shared responsibility](#shared-responsibility)
- [Host OS commands](#host-os-commands)
- [Docker Engine commands](#docker-engine-commands)
- [The 25-control checklist](#the-25-control-checklist)
- [A count discrepancy in the source](#a-count-discrepancy-in-the-source)
- [Compliance mapping](#compliance-mapping)

## Shared responsibility

The Production Hardening Guide opens by drawing a line between what Dokploy secures and
what the operator has to secure. Every control below sits on the operator's side of this
line — it is exactly the list of things Dokploy does not do for you.

| Layer | Dokploy (the product) | You (the operator) |
|---|---|---|
| Access control | 2FA, passkeys, RBAC, custom roles, SSO/OIDC/SAML, SCIM (Enterprise) | Assigning least-privilege roles, offboarding users promptly |
| API/CLI | Token-based auth scoped to your organization, optional expiration, `Access to API/CLI` permission | Who gets that permission, setting an expiration on every token, not sharing tokens across integrations |
| Secrets | Secrets Provider integration (Vault, Infisical, AWS SM, Doppler, Azure KV, Scaleway) — values never stored in the Dokploy DB when referenced this way | Operating the external vault, least-privilege vault credentials, not pasting raw secrets into env vars |
| Reverse proxy / TLS | Traefik auto-config, automatic Let's Encrypt certs, HTTP→HTTPS redirect on Applications | DNS records, custom Traefik middlewares (HSTS, rate limiting), keeping the Traefik dashboard closed |
| Docker engine | None — Dokploy is a Docker/Swarm consumer, not a daemon hardener | `daemon.json` config, socket exposure, image provenance, host-level container isolation |
| Host OS | Automated security check (OS, UFW, SSH, Fail2Ban) on servers added via Remote Servers | Patching, SSH configuration, firewall rules, non-root operator accounts |
| Database engine | Internal/external credential toggle, connection UI | Network placement (internal-only vs. exposed), engine patching if self-managed |
| Backups | Orchestrates backup/restore to your S3 destination | Bucket security, encryption at rest, retention policy, testing restores |
| Observability | Audit Logs (Enterprise), deployment notifications | Log shipping, SIEM integration, alerting on auth anomalies |

## Host OS commands

Run on the box before, or right after, installing Dokploy — as root or via `sudo`.

Automatic security patches, for the sole control (row 1, alongside the LTS choice
itself) this section would otherwise leave without a command:

```bash
sudo apt update && sudo apt install -y unattended-upgrades apt-listchanges
sudo dpkg-reconfigure -plow unattended-upgrades
systemctl status unattended-upgrades
```

SSH — confirm your key is already in `~/.ssh/authorized_keys` before touching this,
then edit `/etc/ssh/sshd_config`:

```
PubkeyAuthentication yes
PasswordAuthentication no
PermitRootLogin no
```

Reload without closing the current session — confirm a new connection works before
disconnecting:

```bash
sudo systemctl reload sshd
```

A non-standard SSH port is optional, added the same way (`Port 2222`, or another
choice, in the same file, then reload again and update the firewall rule below to
match). It reduces automated scan noise; it is not a substitute for the three settings
above, and the guide does not carry it into the numbered checklist for that reason.

Fail2Ban (or CrowdSec), jailing SSH:

```bash
sudo apt install -y fail2ban
sudo tee /etc/fail2ban/jail.local <<'EOF'
[sshd]
enabled = true
mode = aggressive
bantime = 1h
findtime = 10m
maxretry = 5
EOF
sudo systemctl enable --now fail2ban
```

Firewall allowing only 22 (or the custom SSH port), 80, and 443:

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

The `ufw-docker` commands that close Docker's own bypass of these rules are in the
SKILL body's Host OS section — they're the highest-value trap here, so they're kept
where the task starts.

A non-root user for day-to-day operations (log review, manual `docker` commands), in
the `docker` group, with root reserved for provisioning and the SSH key Dokploy itself
uses to manage the host:

```bash
sudo adduser deploy
sudo usermod -aG sudo,docker deploy
```

Copy the operator's public key into `/home/deploy/.ssh/authorized_keys` before relying
on this account to log in.

## Docker Engine commands

`/etc/docker/daemon.json` — the guide's baseline:

```json
{
  "live-restore": true,
  "userland-proxy": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart the daemon to apply it:

```bash
sudo systemctl restart docker
```

This briefly stops `dockerd`, not the containers themselves — `live-restore` keeps them
running through the restart once it's set. The log options cap `json-file` growth;
without them, a noisy container can fill the disk.

## The 25-control checklist

The guide's own words: "Each ⬜ below is one control to implement and check off;
[Section 8] collects all of them into a single table." That table — the Final
Checklist — is reproduced here in full, numbered exactly as the source numbers it.

| # | Item | Section |
|---|---|---|
| 1 | Ubuntu/Debian LTS with `unattended-upgrades` | Host OS |
| 2 | SSH: keys only, no root login, no password auth | Host OS |
| 3 | Fail2Ban/CrowdSec active on SSH | Host OS |
| 4 | Firewall limited to 22/80/443; port 3000 not public | Host OS |
| 5 | Non-root operator user with scoped sudo | Host OS |
| 6 | `daemon.json` hardened (live-restore, log rotation) | Docker |
| 7 | Docker socket never exposed over TCP | Docker |
| 8 | Registry credentials scoped and stored in Dokploy | Docker |
| 9 | 2FA or passkeys enabled for every member | Dokploy |
| 10 | SSO/OIDC configured, and forced org-wide if on Enterprise | Dokploy |
| 11 | SCIM auto-deprovisioning (if on SSO) | Dokploy |
| 12 | Roles follow least privilege / Custom Roles in use | Dokploy |
| 13 | Secrets referenced via a Secrets Provider, not raw env vars | Dokploy |
| 14 | API/CLI tokens issued per-integration, with an expiration set | Dokploy |
| 15 | Audit Logs enabled | Dokploy |
| 16 | HTTPS enforced with redirect on every domain | Traefik |
| 17 | HSTS middleware applied to public domains | Traefik |
| 18 | Traefik dashboard not publicly exposed | Traefik |
| 19 | Rate limiting on public-facing services | Traefik |
| 20 | Isolated Deployments enabled per project (Compose) | Traefik |
| 21 | Databases use Internal Credentials only | Database |
| 22 | Backups encrypted at rest in S3 | Database |
| 23 | Restore tested within the last quarter | Database |
| 24 | Logs shipped to an external system | Observability |
| 25 | Alerting on auth failures / deployment failures | Observability |

That is 25 rows, numbered 1 through 25 without a gap, and the count this skill's
description quotes ("a 25-control checklist") is this table's own count — not a
recount of the narrative bullets above it.

## A count discrepancy in the source

Counted directly: the narrative sections that precede this table (Host OS, lines
7898–7904; Docker Engine, 7985–7989; Dokploy, 8024–8029; Traefik & Networking,
8037–8042; Database, 8082–8084; Observability, 8088–8090) carry **30** separate ⬜
items between them, five more than the 25 the Final Checklist lists (lines 8096–8120).
The net of five is not five subtractions — it's **six subtractions and one addition**:

Subtracted (six bullets that don't get their own row in the Final Checklist):

- **Host OS, merged.** "Ubuntu or Debian LTS" (line 7898) and "`unattended-upgrades`
  installed and enabled" (line 7899) collapse into the checklist's single row 1,
  "Ubuntu/Debian LTS with `unattended-upgrades`."
- **Host OS, optional.** "Non-standard SSH port" (line 7901) is marked optional in the
  same sentence that raises it ("reduces automated scan noise, not a substitute for the
  above") and carries no row.
- **Docker, uncounted.** `no-new-privileges` per service (line 7986) gets no row.
- **Docker, uncounted.** Pinning image tags (line 7989) gets no row.
- **Traefik, restated.** "No Docker socket over TCP anywhere in the cluster" (line
  8042) restates the Docker section's own "never expose the Docker socket over TCP"
  (line 7987) — the guide says as much ("this is as much a networking control as a
  Docker one") — and doesn't get a second row.
- **Observability, restated.** The Observability section's own "Audit Logs" bullet
  (line 8088) restates the Dokploy section's Audit Logs item (line 8029), and likewise
  gets no second row.

Added (one bullet that becomes two rows):

- **Dokploy, split.** The single "SSO/OIDC or SAML" bullet (line 8025) — whose own text
  says to combine forced SSO with SCIM Provisioning — becomes two checklist rows: row
  10, "SSO/OIDC configured, and forced org-wide if on Enterprise," and row 11, "SCIM
  auto-deprovisioning (if on SSO)."

30, minus six, plus one, is 25 — the Final Checklist's own count, and the number this
skill's description quotes. Two of the six subtractions are worth naming as genuine
gaps rather than bookkeeping: `no-new-privileges` per service and pinning image tags
are both stated as controls in the Docker Engine section's prose, but the checklist's
three Docker rows (6–8, lines 8101–8103) cover only `daemon.json`, socket exposure, and
registry credentials. This skill still carries both settings, in the SKILL body's
Docker section, because they are sourced controls the guide itself asks for even
though its own numbered table omits them. The other four subtractions and the one
addition are pure reconciliation — no content is missing, only row count.

## Compliance mapping

The guide's Section 9 maps its own sections to SOC 2 Trust Services Criteria and
ISO/IEC 27001:2022 Annex A control families, and calls the mapping "illustrative" —
"use it as a starting point and align the exact control IDs with your own GRC tooling."
It groups by **guide section**, not by each of the 25 numbered items individually: ten
groupings against six checklist sections, because "Dokploy" splits into three groupings
below (2FA/SSO/RBAC, Secrets Providers, Audit Logs — checklist rows 9–15) and "Traefik"
and "Database" each split into two (Traefik/TLS/HSTS + Network isolation for rows
16–20; Database placement + Backups & restore testing for rows 21–23).

| Guide section | SOC 2 (Trust Services Criteria) | ISO/IEC 27001:2022 Annex A |
|---|---|---|
| Host OS (patching, SSH, firewall) | CC6.1, CC6.6 — logical & physical access, network protection | A.8.8 (vulnerabilities), A.8.20 (network security) |
| Docker engine hardening | CC6.1, CC6.8 — access control, malicious software prevention | A.8.9 (config management), A.8.20 |
| Dokploy: 2FA/SSO/RBAC | CC6.1, CC6.2, CC6.3 — access provisioning & authentication | A.5.15 (access control), A.8.5 (authentication) |
| Secrets Providers | CC6.1, CC6.7 — restricted access, data transmission | A.8.24 (cryptography), A.8.12 (data leakage prevention) |
| Audit Logs | CC7.2 — monitoring for anomalies | A.8.15 (logging), A.5.28 (evidence collection) |
| Traefik / TLS / HSTS | CC6.7 — encryption in transit | A.8.24 (cryptography), A.8.26 (application security) |
| Network isolation | CC6.6 — boundary protection | A.8.20, A.8.22 (network segregation) |
| Database placement | CC6.1, CC6.6 | A.8.20, A.5.10 (acceptable use of assets) |
| Backups & restore testing | A1.2, A1.3 — availability & recovery | A.8.13 (backup), A.5.29 (continuity) |
| Observability & alerting | CC7.2, CC7.3 — monitoring & incident response | A.8.15, A.5.24 (incident management) |

If the university is already tracking these in a GRC platform (the guide names Vanta as
an example), import this table as evidence links against the matching controls rather
than re-deriving the mapping — the control IDs above are the standard families, not any
tenant's own numbering.
