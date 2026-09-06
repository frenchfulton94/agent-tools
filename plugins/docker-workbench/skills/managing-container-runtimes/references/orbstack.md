# OrbStack

Contents:
- [Install and migrate](#install-and-migrate)
- [Container domains](#container-domains)
- [HTTPS](#https)
- [Volumes and file access](#volumes-and-file-access)
- [The orb command](#the-orb-command)
- [Networking](#networking)
- [Linux machines](#linux-machines)
- [Kubernetes](#kubernetes)
- [What changes versus Docker Desktop](#what-changes-versus-docker-desktop)

OrbStack is a macOS-only Docker Desktop replacement. It ships the Docker Engine, the `docker` CLI, and Compose, so ordinary Docker commands work unchanged — but several of its features change the *best* answer to common questions, particularly around reaching services and inspecting volumes.

Docs: <https://docs.orbstack.dev>

## Install and migrate

```bash
brew install --cask orbstack
```

Opening the app is the whole installation. It offers to migrate existing Docker Desktop images, containers, and volumes on first run; migration copies rather than moves, so Docker Desktop's data survives if the migration is reverted.

Docker Desktop should be quit before starting OrbStack — both want `/var/run/docker.sock`.

Updating from the CLI needs the greedy flag, since Homebrew otherwise defers to the app's own updater:

```bash
brew upgrade --greedy orbstack
```

## Container domains

Every container gets `<container-name>.orb.local`. Compose services get `<service>.<project>.orb.local`, where the project name is the directory name unless a top-level `name:` says otherwise.

A Compose project `shop` with services `api` and `postgres` is reachable at:

- `api.shop.orb.local`
- `postgres.shop.orb.local:5432`

**Port numbers are unnecessary for web services.** OrbStack probes the container's listening ports on first connection to find which one speaks HTTP, so `http://api.shop.orb.local` works with no published port and no `-p` flag. That probe appears in application logs with an `OrbStack-Server-Detection` user agent — it is not a stray request worth investigating.

When a container runs several servers and the wrong one is picked, set the port explicitly:

```yaml
    labels:
      - dev.orbstack.http-port=8080
```

Custom domains, under `.local` only, and wildcards:

```yaml
    labels:
      - dev.orbstack.domains=shop.local,*.shop.local
```

This is what makes local layouts mirror production — `api.example.dev` in production, `api.example.local` locally.

`http://orb.local` lists every running container with links.

Domains depend on "Allow access to container domains & IPs" in Settings → Network. If a domain does not resolve, check that before anything else.

## HTTPS

Every container domain also answers over HTTPS with a locally trusted certificate, generated and installed automatically. Changing `http://` to `https://` is the entire setup — no mkcert, no reverse proxy, no certificate volume mounts.

## Volumes and file access

Volume and image contents are browsable from macOS at `~/OrbStack/docker`, and through the OrbStack tab in Finder. Inspecting what a database volume actually contains does not require starting a container.

Mount volumes by name, never by that path:

```bash
docker run -v pgdata:/var/lib/postgresql/data postgres:17   # correct
docker run -v ~/OrbStack/docker/volumes/pgdata:/... postgres:17   # wrong
```

Bind mounts of Mac paths work as they do elsewhere, but cross the host boundary and are slower than named volumes. Keep databases and caches in named volumes.

OrbStack adds volume operations Docker lacks:

```bash
orb docker volume clone source-vol dest-vol      # copy-on-write, near-instant
orb docker volume export my-volume out.tar.zst   # backup or hand to a colleague
orb docker volume import out.tar.zst
```

The clone is the safe way to experiment with a migration against real data: clone, point a throwaway container at the clone, leave the original untouched.

## The orb command

```bash
orb                      # start OrbStack
orb start
orb stop
orb restart docker       # restart just the Docker engine
orb status
orb top                  # live CPU, memory, disk, network
orb config set memory_mib 8192
orb config set setup.use_admin false   # stop admin permission prompts
orb create ubuntu devbox               # create a Linux machine
orb list
```

`orb` with no arguments starts OrbStack, which makes it the right first move when `docker version` reports a client but no server. `orb --help` and `orbctl --help` cover the rest.

OrbStack runs headless without the GUI, which is what makes it usable in CI on macOS runners. Auto-update does not work headless; update through Homebrew.

## Networking

Container IPs are directly reachable from macOS — no port publishing needed to `curl` a container. VPNs, DNS, IPv6, `ping`, and `traceroute` work against containers without configuration.

`host.docker.internal` resolves to the Mac from inside containers, as on Docker Desktop.

## Linux machines

Full distros alongside containers, sharing the same VM:

```bash
orb create ubuntu devbox
orb -m devbox            # shell into it
ssh orb                  # SSH, for editor Remote-SSH extensions
```

Mac files appear inside at their original paths and under `/mnt/mac`; Linux files appear on the Mac under `~/OrbStack`. The SSH agent is forwarded automatically, and `mac <command>` runs a macOS command from inside Linux.

`orb create --isolated` builds a machine with no access to Mac files — the right shape for running untrusted code or an unattended agent.

## Kubernetes

A single-node cluster, off by default, enabled in Settings. Standard `service.namespace.svc.cluster.local` names resolve; LoadBalancer and Ingress services are reachable at `*.k8s.orb.local`, and the API server at `k8s.orb.local`.

## What changes versus Docker Desktop

| Task | Docker Desktop answer | OrbStack answer |
|---|---|---|
| Reach a service | Publish a port, use `localhost:<port>` | `<service>.<project>.orb.local`, no port |
| Local HTTPS | mkcert plus a reverse proxy | Change `http://` to `https://` |
| Inspect volume contents | Run a container with the volume mounted | Open `~/OrbStack/docker` |
| Copy a volume | `docker run` with `tar` through a pipe | `orb docker volume clone` |
| Start the daemon | `open -a Docker` | `orb start` |
| Change memory | Settings → Resources | `orb config set memory_mib N` |
| Adjust settings | GUI only for most | `orb config` from the CLI |

Do not direct an OrbStack user to Docker Desktop's Settings → Resources panel; it does not exist for them. Check which runtime is active with `docker context ls` before giving GUI instructions.
