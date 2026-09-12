---
name: hardening-dokploy
description: Hardens a self-hosted Dokploy installation against a 25-control checklist mapped to SOC 2 Trust Services Criteria and ISO/IEC 27001:2022 Annex A — host SSH and Fail2Ban, UFW with ufw-docker so Docker rules stop bypassing the firewall, panel 2FA and passkeys, scoped and expiring API tokens, external secrets providers in place of raw environment variables, internal-only database credentials, encrypted and restore-tested backups, Traefik HSTS and rate limiting, and external log shipping with alerting. Use when the user asks whether their Dokploy is secure, wants it production-ready or compliance-ready, or is reviewing its exposure — including symptoms like containers reachable despite firewall rules, or departed staff retaining panel access. For scanning or signing container images, use securing-container-supply-chain; for reviewing application source code, use reviewing-code-security.
license: MIT
---

# Hardening Dokploy

Close the gap between a working Dokploy installation and a defensible one. Dokploy's own
Production Hardening Guide states the split plainly: Dokploy secures the application
layer — authentication, TLS automation, secrets referencing, audit trails — and the
operator secures everything it runs on: the host OS, the network perimeter, database
placement, and backup storage. The guide also calls itself a floor, not a finish line:
"This is a baseline. Depending on your threat model, regulatory scope, and data
sensitivity, you may need additional controls beyond what's listed here." Completing
every control below is evidence for a compliance conversation, not a claim that the
instance is fully hardened. This skill is the operator's half, organized as the
guide's own Final Checklist: 25 numbered controls, counted and reproduced in
`references/hardening-checklist.md` along with a discrepancy the guide's own prose and
its own table don't agree on (see that file).

This skill owns Dokploy's own attack surface — the panel, Traefik, secrets, and the
Docker and host settings a Dokploy installation specifically needs. Deciding what a
build type, domain, or server setting should be is `deploying-apps-to-dokploy` or
`operating-dokploy-servers`. Writing the Dockerfile or compose file, or hardening the
Docker daemon and runtime in general, is `docker-workbench:containerizing-apps` or
`docker-workbench:managing-container-runtimes` — this skill states only the settings a
Dokploy host specifically requires. Scanning, triaging, or signing container images is
`docker-workbench:securing-container-supply-chain`; reviewing application source code
is `security:reviewing-code-security`; SSO, SCIM, custom roles, and audit-log detail is
`configuring-dokploy-enterprise`; and scripting any of this is `automating-dokploy`.

## Host OS

Run this on the box before, or immediately after, installing Dokploy, as root or via
`sudo`. Dokploy's automated security check (Remote Servers → Security) validates most
of this for servers added that way — OS, UFW status and default policy, SSH key-based
auth, and Fail2Ban — but only for Ubuntu or Debian, the only families it currently
targets. The exact `sshd_config` edits, the Fail2Ban jail, the base UFW rules, and the
non-root operator setup are copy-paste commands in
`references/hardening-checklist.md`; the one below is inline because it's the trap this
skill's own trigger cases name directly.

**Docker writes directly to `iptables` and bypasses UFW's rules.** A container
published with `-p 3000:3000` stays reachable from the internet no matter what UFW
says, which is the exact symptom behind "containers are reachable despite our firewall
rules." Close it with `ufw-docker`:

```bash
sudo wget -O /usr/local/bin/ufw-docker https://github.com/chaifeng/ufw-docker/raw/master/ufw-docker
sudo chmod +x /usr/local/bin/ufw-docker
sudo ufw-docker install
sudo systemctl restart ufw
```

The VPS provider's own firewall (AWS Security Groups, DigitalOcean Firewalls) is a
second, independent way to close the same gap — it sits in front of Docker's `iptables`
rules entirely, so it works even without `ufw-docker` installed.

Keep Dokploy's own UI port, **3000**, closed to the public internet. Reach it through
Traefik on a domain instead, or behind a VPN such as Tailscale — never `ip:3000`
directly from the open internet.

## Docker

These are the Docker settings a Dokploy host specifically needs, not a general Docker
hardening guide — for the daemon and runtime themselves, use
`docker-workbench:managing-container-runtimes`; for Dockerfiles and Compose files, use
`docker-workbench:containerizing-apps`. The exact `daemon.json` is in
`references/hardening-checklist.md`: `live-restore` and `userland-proxy: false`, plus
`json-file` log rotation so a noisy container can't fill the disk.

`no-new-privileges` is not a daemon-wide setting — it's set per service, in the Docker
Compose file or the app's Advanced settings:

```yaml
security_opt:
  - no-new-privileges:true
```

The snippet itself is the same one `docker-workbench:containerizing-apps` already
teaches for any container; the Dokploy-specific fact is *where* to set it on this
platform, not the setting.

**Never expose the Docker socket over TCP** — no `dockerd -H tcp://...`, no port
2375 or 2376 — on any host Dokploy manages. Dokploy orchestrates remote servers over
SSH, not the Docker remote API, so a TCP socket isn't needed for it to work, and one
left open is unauthenticated root on the host.

Configure private registry credentials in Dokploy itself (the fields are documented
under `deploying-apps-to-dokploy`) rather than leaving `docker login` credentials in
shell history, and scope the token to pull/push only what's needed. Pin image tags in
production — avoid `:latest` — so a redeploy doesn't silently pull an untested image.

## Dokploy access

**2FA or passkeys** for every member with panel access, from Settings → Profile.
Passkeys are phishing-resistant (WebAuthn, bound to the panel's own domain) and
preferred for day-to-day sign-in; 2FA protects the password fallback. Without SSO,
there is no organization-wide "require 2FA" toggle — enrollment is per-user, so treat it
as a policy communicated and audited (via Audit Logs) rather than an enforced setting.
On an Enterprise license, forcing SSO org-wide removes the password fallback entirely,
so whatever MFA the identity provider requires becomes mandatory for everyone — see
`configuring-dokploy-enterprise`. Combine forced SSO with SCIM Provisioning so a member
who leaves the IdP loses Dokploy access automatically, rather than depending on someone
remembering to remove them — this is the direct answer to "someone left but still has
panel access."

**Least-privilege roles.** Three built-in roles: **Owner** (one per organization,
intransferable, full access), **Admin** (full access except deleting or editing another
admin or the owner), and **Member**, whose access is exactly the permissions granted:
Create/Delete Projects, Create/Delete Services, Create/Delete Environments, Access to
Traefik Files, Access to Docker, Access to API/CLI, Access to SSH Keys, and Access to
Git Providers, plus per-project or per-environment scoping, which only a Member grant
carries — restricting a contractor to one project's staging environment means a scoped
Member, not an Admin. Don't hand out Admin by default. An Enterprise license adds Custom
Roles with over 25 permission categories across
Read/Create/Update/Delete/Deploy/Cancel/Restore/Write — see
`configuring-dokploy-enterprise`.

**API/CLI tokens.** Restrict the `Access to API/CLI` permission to who actually needs
it. A token minted at `/settings/profile` never expires unless an expiration is set at
creation — always set one instead of leaving a token to stand forever. Issue a separate
token per integration (CI, webhook, script) so one can be revoked without breaking the
others, and regenerate immediately on offboarding or suspected exposure. "Our API
tokens never expire" is this control, stated as a symptom rather than a setting.

**Audit Logs**, an Enterprise feature, as the primary who-did-what trail — logins, role
changes, deployments, and infrastructure changes. The guide calls this "usually the
single most-requested control in a security review." Detail on what's captured and how
to filter it is `configuring-dokploy-enterprise`'s.

## Secrets and data

**External secrets providers instead of raw values in environment variables.** Six
providers are supported as of v0.30.0 — HashiCorp Vault/OpenBao, Infisical, AWS Secrets
Manager, Doppler, Azure Key Vault, Scaleway Secret Manager. Values are fetched at
deploy time and never stored in Dokploy's database. Setting one up, scoping its
credentials, and each provider's own reference format is
`references/secrets-providers.md`. Writing the resulting
`${{vault.<provider-name>.<ref>}}` reference into an environment editor —
alongside `${{project.X}}` and `${{environment.X}}` interpolation — is
`deploying-apps-to-dokploy`'s territory; this skill owns whether the provider exists,
how it authenticates, and which projects and environments can reach it.

**Internal-only database credentials.** Use **Internal Credentials** for anything an
application in the same network needs. Never enable **External Credentials** — a
published port — unless there's a real requirement, and if there is, restrict it with a
firewall rule or a VPN rather than leaving it open to the internet.

**Backups encrypted at rest.** Dokploy doesn't encrypt the backup archive itself, so
turn on the S3 destination's own encryption (SSE-S3 or SSE-KMS) and scope its
credentials to that one bucket.

**Test restores, not just backups.** The guide's own line: "A backup you haven't
restored isn't a backup." Schedule a periodic restore drill — that's the evidence that
actually matters, not the backup schedule itself. The restore mechanics for panel,
per-database, and volume backups belong to `operating-dokploy-servers`; this skill
owns the policy that a drill has to happen at all.

## Traefik and TLS

TLS is automatic for Applications: Let's Encrypt via `certResolver`, with an HTTP
router that redirects to HTTPS by default. **Docker Compose domains route through
Traefik labels instead and need that same redirect added explicitly** — nothing
enforces it for you there.

HSTS and rate limiting have no panel toggle today; both go through a custom middleware
on the Application's Traefik File System config. **`stsPreload` is the genuinely
hard-to-undo key** — removal needs a submission to hstspreload.org and then months for
browsers to ship the updated list. `stsSeconds` and `stsIncludeSubdomains` are
revocable, but only actively: serving `max-age=0` clears a browser's cached policy on
its next visit (RFC 6797 §6.1.1), so *silently deleting the middleware* — not the
setting itself — is the real trap, since that leaves the old policy in force until
`stsSeconds` would have lapsed anyway. What each key does, the full mechanics, and the
exact YAML — plus the note that the guide gives no worked label equivalent for Compose
services — is `references/traefik-middleware.md`.

Keep the **Traefik dashboard** off the public internet. It isn't exposed by a default
Dokploy install, and the control is confirming it stays that way rather than putting it
behind auth and opening it up.

**Isolate networks per project.** By default, applications share `dokploy-network`.
Enable **Isolated Deployments** on Compose stacks so each gets its own network and
can't reach unrelated projects by service name — the same feature that lets two
instances of one template coexist without a naming collision. Detail, and one
Swarm-restart caveat on custom installs, is in `references/traefik-middleware.md`.

## Observability

**Ship logs externally, not just to the built-in page.** Dokploy's built-in Monitoring
— the aggregated server/container metrics page — is documented as a Cloud-only
feature. The guide states the reason directly: "Dokploy's built-in Monitoring is
currently a Cloud-only feature — for self-hosted, ship container and host logs
(Docker's log driver, syslog, or a log shipper) to something outside the box you're
monitoring, so a compromised host can't erase its own trail." `operating-dokploy-servers`
covers this distinction — and the per-service Monitoring tab that is *not* Cloud-gated —
in full; this skill states log shipping as control 24 of 25 and does not repeat that
explanation.

**Audit Logs**, covered under [Dokploy access](#dokploy-access) above, are the
who-did-what trail; this section is the what's-happening-right-now signal.

**Alert on auth anomalies** — repeated Fail2Ban bans, spikes in Traefik 401/403
responses, failed Dokploy logins. Wire up a notification provider (Slack, email,
webhook) for at least deployment failures and server thresholds as a baseline signal.
Configuring which of the twelve notification providers and which of the six trigger
actions to use is `operating-dokploy-servers`'s territory; this skill only names which
anomalies are worth alerting on.

## Verify before reporting a hardening task done

Confirm each of these against real command output or the panel, not expectation:

- [ ] `ufw status verbose` shows only the intended ports, and a port published by a
      running container is actually unreachable from outside the host — not just that
      `ufw-docker` is installed
- [ ] `docker info | grep -i 'live restore'` confirms `live-restore` is active, not
      just written to the file — `docker info` has no field for `userland-proxy`, so
      `/etc/docker/daemon.json` itself is the only way to check that one
- [ ] Every member with panel access has 2FA or a passkey registered, checked
      per-member rather than assumed from one test account
- [ ] Every long-lived API/CLI token has an expiration set, and each integration holds
      its own token rather than a shared one
- [ ] A restore of the most recent backup has actually been run and verified within the
      last quarter, not only scheduled
- [ ] The Traefik dashboard returns nothing when hit from outside the host

## Where the rest lives

- `references/hardening-checklist.md` — the Shared Responsibility table, the full
  25-control Final Checklist reproduced with its section labels, the count discrepancy
  between the guide's narrative and its own table, and an illustrative, section-level
  (not per-control) SOC 2 / ISO 27001 compliance mapping — the guide's own words are
  "use it as a starting point and align the exact control IDs with your own GRC
  tooling."
- `references/traefik-middleware.md` — the HSTS and rate-limit middleware YAML, where
  it's edited, the Compose gap the guide names but doesn't show a label for, the
  Traefik dashboard control, and Isolated Deployments.
- `references/secrets-providers.md` — all six secrets providers: creating credentials,
  the panel configuration fields, each provider's own reference format, the two-layer
  access control model, and the shared security model across all six.
