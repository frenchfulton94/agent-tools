---
name: operating-dokploy-servers
description: Operates the Dokploy host and control panel itself — installing, updating, and uninstalling Dokploy, adding remote and dedicated build servers, Swarm cluster and build-concurrency settings, monitoring and notification providers, panel and database backups with tested restores, and symptom-first troubleshooting of the panel, logs, networking, DNS pools, volumes, and mounts. Use when the user is standing up, upgrading, moving, backing up, or repairing a Dokploy installation rather than an application running on it — including "the Dokploy panel is unreachable", "restore our instance on a new VPS", or "deployments queue and never start". For installing the container runtime underneath it, use managing-container-runtimes; for securing the installation, use hardening-dokploy.
license: MIT
---

# Operating Dokploy Servers

Keep the Dokploy installation itself — the host, the panel, Traefik, and every server it
manages — running, current, and recoverable. This skill covers installing and updating
the panel, adding remote and dedicated build servers and Swarm cluster nodes, monitoring
and notification channels, backing up and restoring the panel and its databases, and
diagnosing the panel and its infrastructure by symptom.

To install or repair the Docker runtime underneath it, use
`docker-workbench:managing-container-runtimes`. To secure a running installation, use
`hardening-dokploy`. To deploy or debug an application already running on it, use
`deploying-apps-to-dokploy`. To script any of this from the CLI or API, use
`automating-dokploy`.

## Panel backups and per-database backups are two different features

The documentation calls both "Backups" and never states the difference directly, which is
what makes them easy to conflate.

**Web Server → Backups** archives the Dokploy *installation* — the `dokploy-postgres`
database that holds Dokploy's own metadata, plus the `/etc/dokploy` directory, zipped
into one file and uploaded to an S3 destination. A database's own **Backup** tab is a
different feature entirely: it exports that one database's contents with `pg_dump`,
`mysqldump`, or the equivalent, and is configured on the database, not under Web Server.
Having one configured says nothing about the other.

Restoring a panel backup is destructive, not additive. It:

- Clears the existing `/etc/dokploy` and replaces it with the backup's contents.
- Drops the existing `dokploy-postgres` database.
- Disconnects current database users.
- Restores the database from the backup.

Restoring onto a **different host** than the one the backup came from needs four
follow-ups the restore doesn't do for you: update the server IP (Web Server → Server →
Update IP), reconfigure any git provider that referenced the old IP, update DNS records
to point at the new IP, and recreate any `traefik.me` domains, which were generated
against the old server. Skipping one of these leaves something — a build's git access, a
domain, a generated host — pointed at a server that no longer exists.

Full detail, plus volume backups (for services that don't fit a database backup at all)
and the S3 providers, is in `references/backups-and-restore.md`.

## Installing, updating, and removing the panel

Install with `curl -sSL https://dokploy.com/install.sh | sh` on a server with at least
2 GB RAM, 30 GB disk, and ports 80, 443, and 3000 free. `DOKPLOY_VERSION=canary` tracks
the development branch; a specific version installs from that release's own `install.sh`
asset rather than the always-latest main script. Update in place with
`curl -sSL https://dokploy.com/install.sh | sh -s update`.

**Dokploy does not update Traefik when it updates itself** — deliberately, to avoid
downtime for every routed service. A newer Traefik is a manual container replace, and
worth checking Traefik's release notes for breaking changes first: an incompatible
version can produce 404s on domains that worked a moment before.

Uninstalling removes the Swarm services, volumes, and network, leaves the Swarm, prunes,
and deletes `/etc/dokploy`, in that documented order. Full commands, the advanced install
variables (custom Swarm network, manual advertise address, IPVS-less kernels), and the
uninstall sequence are in `references/installation-and-updates.md`.

## Where apps run: server, remote servers, and cluster

Three options, in order of how much they cost to set up: the **Dokploy server** itself
(default, no configuration, no registry needed), **remote servers** connected over SSH
(independent, isolated from the panel and from each other, either running apps or
dedicated to building them — a registry is needed only if any of them is a build server),
and **Swarm cluster nodes** (joined to the Dokploy server's own Swarm, for replicating one
application across machines — the only option that unconditionally needs a Docker
registry, and the only one requiring same-CPU-architecture servers).

Every server — the Dokploy server and every remote or build server — has its own build
queue with its own concurrency setting, defaulting to **1**. Builds of the *same*
application or Compose service are always serialized regardless of that setting, so a
report like "deployments queue and never start" is often not a stuck queue at all: check
whether the queued builds share one service before raising concurrency, since raising it
only helps different services build in parallel.

Setup steps, the validation checklist for deployment versus build servers, cluster
requirements, and the full concurrency model are in
`references/remote-servers-and-cluster.md`.

## Monitoring and notifications

Twelve notification providers — Slack, Discord, Telegram, Microsoft Teams, Mattermost,
Lark, Email, Resend, Gotify, Ntfy, Pushover, and a generic Webhook — each with its own
form fields, not one shared shape: Slack takes a Webhook URL and a channel name, Resend
takes an API key plus From and To addresses, Pushover takes a user key, an API token, and
a priority level, and so on per provider. Six actions can trigger one: app deploy, app
build error, database backup, volume backup, Docker cleanup, and a Dokploy restart. "Send
deployment failures to Slack" is the app-build-error action routed to a Slack provider —
nothing more exotic than that.

**Dokploy's built-in Monitoring — the aggregated server/container metrics page (refresh
rates, a metrics server on port 4500, CPU/memory alert thresholds, a metrics callback
URL) — is documented as a Cloud-only feature.** The Production Hardening Guide states
this directly, as the reason to ship logs externally instead: "Dokploy's built-in
Monitoring is currently a Cloud-only feature — for self-hosted, ship container and host
logs (Docker's log driver, syslog, or a log shipper) to something outside the box you're
monitoring, so a compromised host can't erase its own trail." The Monitoring page's own
closing line — "This is feature only available on Cloud Version of Dokploy" — says the
same thing, despite that page's prerequisites confusingly describing a Remote Servers
setup step just above it. For a self-hosted instance, treat built-in threshold alerting
as absent and ship logs externally instead. The per-service graphs (CPU, memory, disk,
network) inside an application or database's own **Monitoring** tab are a separate,
narrower feature and carry no such caveat.

## Troubleshooting is symptom-first

The docs split troubleshooting into an overview plus five category pages; this skill
inverts that into symptoms, because a report never arrives labeled with a page:

- **The panel itself won't load** — disk space, a Postgres-before-Dokploy race on
  restart, or a Traefik config error, in that checking order.
- **Deployments queue and never start** — per-server concurrency, and same-service builds
  that are always serialized regardless of it (see above).
- **A domain or Compose service 404s or returns Bad Gateway** — owned by
  `deploying-apps-to-dokploy`. One operator-side fact stays here: seeing `use of closed
  network connection` in Traefik's logs during a restart is expected and needs no action.
- **Logs or monitoring go missing** — expected after moving an app to a different Swarm
  node, or a slow/low-disk remote server; remote server monitoring is a documented gap
  regardless of server health.
- **Networking or DNS breaks** — a Swarm advertise-address failure, IPVS-less kernels
  breaking service discovery, a VPS's DNS resolvers failing builds, or Docker's default
  network pools running out around 30 networks.
- **A volume mount is empty after redeploy** — AutoDeploy re-clones the repository on
  every deploy, wiping anything mounted from a repository-relative path; the fix is a
  File Mount instead.

Full symptom-to-fix detail for all of these is in `references/troubleshooting.md`.

## Verify before reporting an operations task done

Confirm each of these against real command output or the panel, not expectation:

- [ ] `docker ps` shows `dokploy`, `dokploy-postgres`, and `dokploy-traefik` all running
      (no `dokploy-redis` expected on v0.29.9+)
- [ ] After an install or update, the panel answers on its own domain over HTTPS, not
      just on `ip:port`
- [ ] After a panel restore, the server IP, any IP-based git provider config, DNS
      records, and `traefik.me` domains are updated if the restore landed on a new host
- [ ] A backup or volume backup actually restores somewhere, rather than only having run
      successfully — an unrestored backup is not verified
- [ ] A server added under Remote Servers shows every validation item green before
      anything is deployed to it

## Where the rest lives

- `references/installation-and-updates.md` — requirements, the install script and its
  environment-variable overrides (canary, a pinned version, custom Swarm network, manual
  advertise address, IPVS-less kernels, Proxmox LXC), completing setup, updating
  (including Traefik's manual-only update), and the full uninstall sequence.
- `references/remote-servers-and-cluster.md` — the three ways to run apps compared,
  remote server setup and its validation checklist, build servers, Swarm cluster
  requirements and node roles, the full concurrent-builds queue model, and the
  Dokploy-checked security baseline on a remote server.
- `references/backups-and-restore.md` — panel backups against per-database backups
  against volume backups, what each restore does and requires, the four
  different-host follow-ups, the four S3 providers' setup fields, and the hardening
  guide's line on testing restores.
- `references/troubleshooting.md` — the docs' six troubleshooting pages reorganized by
  symptom: panel unreachable, queued deployments, domains and Traefik (pointing to
  `deploying-apps-to-dokploy` for the parts owned there), missing logs or monitoring,
  networking and DNS pool exhaustion, and volumes and mounts.
