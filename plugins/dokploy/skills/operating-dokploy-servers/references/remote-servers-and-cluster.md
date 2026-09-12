# Remote servers and cluster

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [Three ways to run apps](#three-ways-to-run-apps)
- [Remote servers](#remote-servers)
- [Build servers](#build-servers)
- [Cluster (Swarm nodes)](#cluster-swarm-nodes)
- [Concurrent builds](#concurrent-builds)
- [Security baseline on a remote server](#security-baseline-on-a-remote-server)

## Three ways to run apps

All three use the same deployment engine; they differ in where apps run and how the
servers relate to each other.

| | Dokploy Server | Remote Servers | Swarm Nodes (Cluster) |
|---|---|---|---|
| Where apps run | Same machine as the UI | Independent servers | Nodes of a shared Swarm |
| Connection | — | SSH | Swarm join token |
| Docker registry required | No | Only for build servers | Yes |
| Isolation between servers | — | High, fully independent | Low, shared cluster |
| Replicas across servers | No | No | Yes |
| Automatic storage cleanup | Yes | Yes, configurable | No |
| Setup complexity | None | Low | High |

Start with the Dokploy Server and scale vertically (more CPU/RAM through the VPS
provider) — it covers most cases with no extra configuration. Move to Remote Servers for
isolation: production apps kept off the machine running the UI, one server per project or
region, or a dedicated build server. Move to Swarm Nodes only to replicate the *same*
application across machines with load balancing. The options combine: a common pattern is
a small server running only the Dokploy UI, with applications on remote servers, and a
Swarm node added as a remote server so it gets storage cleanup too.

## Remote servers

Two types:

- **Deployment servers** run and host applications: routing through Traefik, deployments,
  updates, volumes.
- **Build servers** only clone, build, and push an image to a registry. They run no
  containers or active processes, and currently support Applications only, not Docker
  Compose.

Setup, for either type: create an SSH key under `/dashboard/settings/ssh-keys`, add the
server with its IP, SSH port, username, and that key, confirm connectivity with
**Enter Terminal**, then run **Setup Server**. Root access is required — Dokploy does not
currently support non-root deployments — and the default shell has to be bash, since
Dokploy is developed and tested against it; a server with a different default shell needs
to be switched to bash first. Setup runs once; a later Dokploy update only needs it
rerun if the release notes say so.

**Validation.** Dokploy checks each server against a checklist and shows a green check
per item once satisfied. For a deployment server, that list is Docker, RClone, Nixpacks,
Railpack, and Buildpacks installed, Docker Swarm initialized, the Dokploy network
created, and a main directory for applications created. The docs' own prose and list
disagree on the count here — it says "the following 7 components" and then enumerates
eight — so take the enumerated list as the checklist, not the number in the sentence
introducing it. A build server skips the Swarm-and-network items, since it never runs a
container: Docker, RClone, Nixpacks, Railpack, Buildpacks, and the main directory — six
items, and here the docs' count and list agree.

**Remote server monitoring is not supported**, for performance reasons — the only
documented feature gap between a remote server and the local Dokploy server. Everything
else works the same. See `troubleshooting.md` for what "logs not loading" on a remote
server usually means instead of a missing feature.

Adding a node to a Swarm cluster is a separate path from adding a remote server — see
[Cluster](#cluster-swarm-nodes) — and Dokploy does not run automatic storage cleanup on
cluster worker/manager nodes the way it does on a remote server or the Dokploy server
itself. Add the node as a remote server too, or schedule a cleanup job, to get it back.

## Build servers

Purpose: compile on a dedicated, disposable machine instead of the deployment server, so
a resource-hungry Nixpacks or Buildpack build can't freeze production alongside it.

Setup: add the server as a **Build Type: Build Server**, run its setup (installs
Nixpacks, Railpack, Heroku Buildpacks, and Docker — no containers), then configure a
Docker registry under **Settings → Registries** and select it in the application's
**Advanced → Cluster Settings**. Enable **Custom Build Server** on the application and
pick it from the dropdown.

Flow on deploy: Dokploy connects to the build server over SSH, clones, builds, and pushes
the image to the registry; then connects to the deployment server(s), pulls, and runs.
Allow a few moments after the push for the deployment server to pull and cache the image
before it is deployable.

Disk fills up fast on a build server. Enable **Docker Cleanup** in the server settings, or
schedule a periodic `docker image prune -af` job, to keep ahead of it.

## Cluster (Swarm nodes)

Requirements: the Dokploy server as manager, at least one more server with the **same
architecture**, and a configured Docker registry — images have to be pushed somewhere the
other nodes can pull them from. Configuring the registry unlocks the Cluster section.

Two node roles: **managers** hold cluster state and schedule services; **workers** only
run containers under a manager's scheduling. **Add Node** in the panel shows the join
command for either role.

Two scaling paths, and Dokploy's own recommendation is to exhaust the first before
reaching for the second: **vertical** (more CPU/RAM on the existing server, through the
VPS provider) is faster and needs no extra configuration; **horizontal** (more servers,
joined as Swarm nodes) is what the Cluster feature is for once vertical scaling is
insufficient.

Storage on worker/manager nodes added purely as Swarm nodes is not cleaned up
automatically — see the note under [Remote servers](#remote-servers).

## Concurrent builds

The build queue is scoped **per server** — the Dokploy server and every remote or build
server each get their own independent concurrency setting and their own queue partition,
so a busy build server never blocks builds on the Dokploy server or another remote
server.

Two rules govern what runs inside one server's queue:

- Up to *N* jobs run in parallel, where *N* is that server's configured concurrency.
- Multiple builds of the **same** application or Compose service are always serialized
  (FIFO), regardless of concurrency, to avoid two builds of the same service colliding on
  the same source directory or container name.

So raising concurrency lets *different* applications on one server build at once; it does
not parallelize repeated builds of the same service. This is the reason a report like
"deployments queue and never start" is not necessarily a stuck queue — check whether the
queued builds are all the same service before assuming something is broken.

Default concurrency is **1** per server. It is configurable from **1** to **100**,
independently per server, under **Dashboard → Settings → Deployments** — a self-hosted
feature only; Dokploy Cloud manages build scheduling itself and does not expose this
setting.

## Security baseline on a remote server

Dokploy's own remote-server security check looks at UFW (installed, active, default-deny,
only the ports actually needed open), SSH (key-based only, password and PAM
authentication off), and Fail2Ban (installed, running, protecting SSH, aggressive mode).
It validates these automatically and surfaces recommendations in the panel, rather than a
bare pass/fail. Docker bypasses UFW by rewriting `iptables` directly, so a container
published with `-p` stays reachable from the internet even behind a UFW deny-all —
`ufw-docker` or the cloud provider's own firewall in front of Docker are the two fixes
the docs name. The full hardening checklist, including how these map to SOC 2 and
ISO/IEC 27001:2022, belongs to `hardening-dokploy`.
