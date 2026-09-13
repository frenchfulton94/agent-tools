# Troubleshooting

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Condensed from the docs' six troubleshooting pages (an overview plus five categories),
reorganized here by symptom rather than by page, since a report never arrives labeled
with the page it belongs to.

Contents:
- [The panel is unreachable](#the-panel-is-unreachable)
- [Deployments queue and never start](#deployments-queue-and-never-start)
- [Domains and Traefik](#domains-and-traefik)
- [Logs or monitoring are missing](#logs-or-monitoring-are-missing)
- [Networking and DNS](#networking-and-dns)
- [Volumes and mounts](#volumes-and-mounts)

## The panel is unreachable

Three containers back the panel: `dokploy`, `dokploy-postgres`, and `dokploy-traefik`.
(A `dokploy-redis` container appears only on installs older than v0.29.9; self-hosted
Dokploy has not used Redis since.) `docker ps` should show all three running.

**Out of disk space.** Enough deployments can fill the disk and push the Dokploy database
into recovery mode, which blocks the UI. Free space:

```bash
docker system prune -a
docker builder prune -a
docker image prune -a
```

**All three containers running, UI still down — check logs first:**

```bash
docker service logs dokploy
docker service logs dokploy-postgres
docker logs dokploy-traefik
```

A frequent case is Postgres starting after `dokploy`, so `dokploy` never connects — its
log shows `getaddrinfo ENOTFOUND dokploy-postgres`. Fix by cycling the service, not the
whole stack:

```bash
docker service scale dokploy=0
docker service scale dokploy=1
```

**Traefik logs show a config error** (for example `field not found, node:
passHostHeader`). Restart it first — `docker restart dokploy-traefik` — and if the error
persists, the fault is in `/etc/dokploy/traefik`: a manually edited router file with a
field nested under the wrong key. `passHostHeader` belongs as a sibling of `servers:`
under the service, not inside a list item alongside a server URL.

**Still down — recreate the containers**, in this order, keeping backups current first
(recreating removes the services but not the volumes):

1. `docker service rm dokploy-postgres`, then recreate it with Docker Secrets for the
   password (see the docs' exact `docker service create` invocation).
2. Recreate `dokploy-traefik` — standalone `docker run` or `docker service create`,
   matching however it was originally run.
3. `docker service rm dokploy`, then recreate it. If `dokploy_auth_secret` doesn't exist
   (installs older than v0.29.3), create it first:
   `openssl rand -hex 32 | docker secret create dokploy_auth_secret -`.

On Proxmox LXC, add `--endpoint-mode dnsrr` to every one of these `docker service
create` commands, matching what the installer applies automatically on first install.

## Deployments queue and never start

Not necessarily broken — check whether the queued builds are all the **same**
application or Compose service first. Every server's build queue defaults to
concurrency **1**, and builds of the same service are always serialized regardless of
concurrency. Raising the server's concurrency (Settings → Deployments) only helps
*different* services build in parallel; it does nothing for a backlog of the same
service. See `remote-servers-and-cluster.md` for the full queue model.

## Domains and Traefik

The routing asymmetry between Applications and Compose services, the four domain traps,
and the fixes for them belong to `deploying-apps-to-dokploy` — this skill doesn't
re-derive that material. One fact belongs here instead, because it's about the Traefik
container's own lifecycle rather than any application's configuration:

**`use of closed network connection` during a Traefik restart is expected, not a
failure.** Log lines like these appear whenever Traefik restarts and mean nothing beyond
that:

```
ERR: error="accept tcp [::]:443: use of closed network connection" entryPointName=websecure
ERR: error="accept tcp [::]:9000: use of closed network connection" entryPointName=traefik
ERR: error="accept tcp [::]:80: use of closed network connection" entryPointName=web
```

No action follows from seeing them.

## Logs or monitoring are missing

**After changing an application's placement** (moving it to a different Swarm node) —
expected. The panel reads logs and metrics from the node it's on; if the app moved to a
worker the UI isn't running on, that node's logs and metrics aren't reachable from there.

**On a remote server specifically** — two documented causes: the server is too slow to
keep up with concurrent requests, surfacing as SSL handshake errors, or it's low on disk
space. Remote server monitoring is also a feature gap, not a bug: it's the one
documented capability remote servers don't have, for performance reasons, regardless of
server health.

## Networking and DNS

**Docker Swarm fails to initialize** with an error about not being able to identify a
system address. Assign the advertise address explicitly:

```bash
curl -sSL https://dokploy.com/install.sh | sudo ADVERTISE_ADDR=your-ip sh
```

Pass it inline as shown — an `export`ed value doesn't survive `sudo`, which resets the
environment before the script runs.

**Services can't reach each other, and the UI never comes up on port 3000**, on a
minimal or appliance-style distribution (ZimaOS, other Buildroot-based images) or a
custom kernel. Cause: Swarm's default VIP service discovery needs IPVS kernel support,
which these kernels lack. Confirm with `sudo modprobe ip_vs && lsmod | grep ip_vs`, or by
checking `/boot/config-$(uname -r)` for `CONFIG_IP_VS` and related options. Fix: switch
to DNSRR mode — `ENDPOINT_MODE=dnsrr` on a fresh install, or
`docker service update --endpoint-mode dnsrr <service>` (for both `dokploy` and
`dokploy-postgres`) on an existing one. DNSRR trades away VIP load balancing and ingress
port publishing (only `mode=host` works), so it's a fallback for broken IPVS, not a
general-purpose choice. Applications you deploy are still VIP-mode Swarm services even
under this fix — reach one from another container with `tasks.<app-name>:<port>`, not
`<app-name>:<port>`, since the `tasks.` prefix resolves straight to container IPs and
skips the broken load balancer.

**Builds fail with `Could not resolve host` or similar**, most often reported on
Hetzner Cloud's default resolvers. Every build type shows a different symptom for the
same root cause — Docker inheriting a host DNS configuration that can't resolve
recursively from inside a container: Nixpacks says `Could not resolve host: github.com`,
Railpack says `server misbehaving`, a Dockerfile build hangs on `npm ci`/`apt-get`, and
domain validation in the UI fails with `queryA ENOTFOUND` even though `nslookup` from the
host resolves fine. Fix by adding a `dns` key to `/etc/docker/daemon.json` (merge into
the existing file if one exists — don't overwrite it) and restarting Docker:

```bash
echo '{"dns": ["1.1.1.1", "8.8.8.8"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

**A deployment fails with `all predefined address pools have been fully subnetted`.**
Docker's default pools allow roughly 31 local networks, and every Compose project
creates at least one. `docker network ls | wc -l` near 30 confirms it. `docker network
prune -f` is a safe, immediate but temporary fix — it only removes networks nothing is
using. The permanent fix is larger pools in `/etc/docker/daemon.json` (again, merge, not
overwrite):

```json
{
  "default-address-pools": [
    { "base": "172.17.0.0/12", "size": 24 },
    { "base": "10.100.0.0/16", "size": 24 }
  ]
}
```

The docs' own verification example, further down the same page, shows `docker info`
reporting the first pool back as `172.16.0.0/12` rather than the `172.17.0.0/12` given in
the config snippet above. Both are the base the docs actually show — this looks like an
inconsistency in the docs themselves rather than a typo safe to silently correct, so
don't be surprised if the value you configure and the value `docker info` echoes back
don't match digit-for-digit.

Pick `base` ranges that don't overlap the VPS's own private network or any VPN in use —
`192.168.0.0/16` is a common LAN range and worth avoiding for that reason. Restarting
Docker briefly restarts every container including Dokploy itself, but `dokploy` and
`dokploy-postgres` are Swarm services and `dokploy-traefik` runs with `--restart
always`, so everything recovers on its own; existing networks and their subnets are
untouched, and nothing needs redeploying. Confirm the new pools with `docker info | grep
-A 5 "Default Address Pools"`.

## Volumes and mounts

**A mount makes the app fail to run, even though the deployment reports success.**
Swarm silently refuses to run a service with an invalid mount. Check the service under
the General Swarm section in the panel for the actual error.

**A Compose volume doesn't work as a host-path mount.** An absolute host path
(`/folder:/path/in/container`) is invalid; Dokploy stores Compose file mounts under a
per-application `/files` directory instead, so the compose file has to reference them
relatively:

```yaml
volumes:
  - "../files/my-database:/var/lib/mysql"
```

**A file or directory from the repository is empty or missing after a redeploy** — the
trigger symptom for this whole entry. AutoDeploy performs a fresh `git clone` on every
deployment, which clears the repository directory; anything mounted straight from a
repository path (`./config/app.conf`) is gone the moment the second deploy re-clones.
The fix is to stop mounting from the repository at all: copy the file's content into a
File Mount (Advanced → Mounts), then reference it from `compose.yaml` under `../files/`:

```yaml
volumes:
  - "../files/my-config.json:/etc/my-app/config"
```

This persists across every redeploy, because the File Mount lives outside the
repository checkout that AutoDeploy wipes.
