# Installation and updates

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [Requirements](#requirements)
- [Installing](#installing)
- [Customizing the install](#customizing-the-install)
- [Completing setup](#completing-setup)
- [Updating](#updating)
- [Updating Traefik](#updating-traefik)
- [Uninstalling](#uninstalling)

## Requirements

At least 2 GB of RAM and 30 GB of disk space, to cover what Docker consumes during
builds. Ports 80, 443, and 3000 have to be free — the installer fails if any of them is
already in use. Tested distributions: Ubuntu 24.04 LTS, 23.10 (the one non-LTS release in
the list), 22.04 LTS, 20.04 LTS, and 18.04 LTS; Debian 12, 11, and 10; Fedora 40; CentOS 9
and 8.

Docker itself does not need to be installed first — the script installs it if it is
missing.

## Installing

```bash
curl -sSL https://dokploy.com/install.sh | sh
```

The script auto-detects and installs the latest stable release. Two environment
variables select something else instead:

```bash
export DOKPLOY_VERSION=canary && curl -sSL https://dokploy.com/install.sh | sh
export DOKPLOY_VERSION=latest && curl -sSL https://dokploy.com/install.sh | sh
```

To install an exact older version, don't use `DOKPLOY_VERSION` against the main script —
the main script always targets the latest release, and its setup may not match an older
version's. Instead use that release's own `install.sh` asset:

```bash
curl -sL https://github.com/Dokploy/dokploy/releases/download/v0.26.6/install.sh | sh
```

## Customizing the install

**Custom Swarm network**, to avoid a CIDR conflict with a cloud provider's VPC:

```bash
export DOCKER_SWARM_INIT_ARGS="--default-addr-pool 172.20.0.0/16 --default-addr-pool-mask-length 24"
curl -sSL https://dokploy.com/install.sh | sh
```

**Manual advertise address**, when the script can't detect the server's IP or Swarm
should bind a specific interface (a VPN/WireGuard IP, for example):

```bash
curl -sSL https://dokploy.com/install.sh | sudo ADVERTISE_ADDR=192.168.1.100 sh
```

Pass `ADVERTISE_ADDR` (and likewise `DOKPLOY_VERSION`, `DOCKER_SWARM_INIT_ARGS`,
`ENDPOINT_MODE`) inline as shown, not via `export` beforehand — `sudo` resets the
environment, so an exported variable never reaches the script and it silently falls back
to auto-detection.

**Kernels without IPVS support** — some minimal or appliance-style distributions (ZimaOS
and other Buildroot-based images) ship without it, which Docker Swarm's default service
discovery needs. Install with DNS round-robin instead:

```bash
curl -sSL https://dokploy.com/install.sh | sudo ENDPOINT_MODE=dnsrr sh
```

The symptom on an affected kernel: installation appears to succeed, but the UI never
becomes reachable on port 3000 and containers can resolve each other's names but not
connect. See `troubleshooting.md` for diagnosing this after the fact on an existing
install.

**Proxmox LXC** is auto-detected, and the installer applies `--endpoint-mode dnsrr`
automatically — no flag needed.

## Completing setup

Open `http://<server-ip>:3000` and create the administrator account. Then, before
anything else:

- Put a domain with HTTPS on the panel itself (see `deploying-apps-to-dokploy` for the
  DNS-before-domain and Let's Encrypt mechanics — they apply to the panel's own domain
  the same as to an application's).
- Only after that domain works, optionally disable `ip:port` access:

  ```bash
  docker service update --publish-rm "published=3000,target=3000,mode=host" dokploy
  ```

  Doing this before the domain works locks out the panel entirely.

Set the panel's timezone with:

```bash
docker service update --env-add TZ=America/New_York dokploy
```

## Updating

```bash
curl -sSL https://dokploy.com/install.sh | sh -s update
```

This is the same script, invoked with `update`, and picks up the latest stable release by
default. Two other documented forms, and they are not interchangeable:

- **Canary or latest** — the docs' own "Install/Update to Canary" and "Install/Update to
  Latest Stable" recipes both use the plain install command, not `sh -s update`:

  ```bash
  export DOKPLOY_VERSION=canary && curl -sSL https://dokploy.com/install.sh | sh
  export DOKPLOY_VERSION=latest && curl -sSL https://dokploy.com/install.sh | sh
  ```

- **A specific version** — use that release's own `install.sh` asset with `sh -s update`:

  ```bash
  curl -sL https://github.com/Dokploy/dokploy/releases/download/v0.26.6/install.sh | sh -s update
  ```

Don't combine `DOKPLOY_VERSION` with the main script to pin a version — the docs warn
against exactly this: "the main script at `dokploy.com/install.sh` always targets the
latest release, so its setup may not be compatible with older versions." `DOKPLOY_VERSION`
is documented only for canary/latest against the always-current main script; pinning a
specific version is documented only via that version's own release asset.

## Updating Traefik

Dokploy does **not** update the Traefik container when Dokploy itself is updated. That is
deliberate, to avoid unexpected downtime for every routed service. Updating it is a
manual replace of the container in place:

```bash
docker rm -f dokploy-traefik

docker run -d \
  --name dokploy-traefik \
  --restart always \
  -v /etc/dokploy/traefik/traefik.yml:/etc/traefik/traefik.yml \
  -v /etc/dokploy/traefik/dynamic:/etc/dokploy/traefik/dynamic \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -p 80:80/tcp \
  -p 443:443/tcp \
  -p 443:443/udp \
  traefik:v3.6.7

docker network connect dokploy-network dokploy-traefik
```

Check the Traefik release notes for breaking changes before picking a version — an
incompatible one can cause routing issues such as 404s on domains that worked before.

## Uninstalling

In order: remove the Swarm services, then the volumes, then the network, then leave the
Swarm, then prune, then remove the files:

```bash
docker service remove dokploy dokploy-traefik dokploy-postgres dokploy-redis
docker container remove -f dokploy-traefik
docker volume remove -f dokploy dokploy-postgres dokploy-redis
docker network remove -f dokploy-network
docker network remove -f ingress
# On every worker node, if running a Cluster:
docker service rm $(docker service ls -q)
docker system prune -a -f
docker swarm leave
# On the manager node(s):
docker swarm leave --force
docker container prune --force
docker image prune --all --force
docker volume prune --all --force
docker builder prune --all --force
docker system prune --all --volumes --force
sudo rm -rf /etc/dokploy
```

The documented uninstall still names a `dokploy-redis` service and volume. Self-hosted
Dokploy has not run Redis since v0.29.9 (see `troubleshooting.md`), so on a current
install those two `remove` commands are expected to find nothing and can be left in
place or dropped — they are harmless either way.
