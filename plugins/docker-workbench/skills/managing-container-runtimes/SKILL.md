---
name: managing-container-runtimes
description: Installs, selects, configures, and repairs the container runtime behind the docker CLI — OrbStack, Docker Desktop, Colima, Podman, or Docker Engine — covering contexts, resource limits, daemon settings, registry login, and disk reclamation. Use when Docker is not installed or not running, when "Cannot connect to the Docker daemon" or a socket permission error appears, when choosing or switching between runtimes, when containers are consuming too much RAM, disk, or battery, or when the user mentions OrbStack, Docker Desktop, Colima, or a Docker VM.
license: MIT
---

# Managing Container Runtimes

The `docker` CLI is a client. It does nothing on its own — it talks to a daemon, which on macOS and Windows lives inside a Linux VM supplied by OrbStack, Docker Desktop, Colima, Rancher Desktop, or Podman. Most "Docker is broken" reports are about that layer, not about any image or Compose file.

To write or fix Dockerfiles and Compose files, use `containerizing-apps` instead.

## Diagnose before installing anything

`Cannot connect to the Docker daemon at unix:///var/run/docker.sock` most often means a runtime that is installed and simply stopped. Installing a second runtime on top of it creates a conflict that is harder to unpick than the original problem.

Run this first, and read all four answers before proposing anything:

```bash
docker version                     # client vs server; server absent = no daemon reachable
docker context ls                  # which endpoint the CLI is pointed at
docker info --format '{{.ServerVersion}} {{.OperatingSystem}}' 2>&1
ls /Applications 2>/dev/null | grep -iE 'orbstack|docker|rancher'; command -v colima limactl podman
```

A client version with no server version means a daemon is not running. Start what is already installed:

| Installed | Start with |
|---|---|
| OrbStack | `orb start` (or open the app) |
| Docker Desktop | `open -a Docker` on macOS; start the service on Windows |
| Colima | `colima start` |
| Podman | `podman machine start` |
| Linux Engine | `sudo systemctl start docker` |

On macOS, `brew install docker` installs the CLI only — no daemon, no VM. It produces exactly this error and no amount of reinstalling the CLI fixes it. The runtime is a separate install: `brew install --cask orbstack` or `brew install --cask docker-desktop`.

## Choosing a runtime

| Runtime | Platform | Notes |
|---|---|---|
| OrbStack | macOS | Fast start, low idle CPU and battery drain, automatic container domains. Free for personal use; paid for commercial |
| Docker Desktop | macOS, Windows, Linux | The reference implementation. Paid for larger organizations |
| Rancher Desktop | macOS, Windows, Linux | Open source, includes k3s |
| Colima | macOS, Linux | CLI-only, free, no GUI |
| Podman | Linux, macOS, Windows | Daemonless, rootless by default |
| Docker Engine | Linux | The daemon directly, no VM |

Only one should own `/var/run/docker.sock` at a time. When two are installed, `docker context ls` shows which one the CLI is using, and mixed results across terminal sessions usually mean a `DOCKER_HOST` set in one shell profile and not another.

Detailed OrbStack usage — container domains, volume access from Finder, `orb` commands, migration from Docker Desktop — is in `references/orbstack.md`. Read it whenever OrbStack is the runtime in use, because several of its features change the right answer to ordinary questions like "how do I reach this service".

Installation, daemon configuration, rootless mode, and CI setup for the other runtimes are in `references/runtime-setup.md`.

## Contexts

A context is a named daemon endpoint. Switching runtimes is switching context, not reinstalling:

```bash
docker context ls                    # * marks the active one
docker context use orbstack
docker context use desktop-linux
DOCKER_CONTEXT=colima docker ps      # one command against another endpoint
```

`DOCKER_HOST` overrides the selected context entirely. When `docker context use` appears to have no effect, an inherited `DOCKER_HOST` is the reason — check the shell profile.

## Reclaiming disk

Container disk usage grows mostly from build cache and unused images, not from anything the user can see. Check before deleting:

```bash
docker system df            # images, containers, volumes, build cache
docker system df -v         # per item, so the large ones are identifiable
```

Then remove in increasing order of aggression, stopping as soon as enough is recovered:

```bash
docker buildx prune --filter until=168h    # build cache older than a week
docker image prune                          # dangling images only
docker container prune                      # stopped containers
```

Volumes hold databases and other state that exists nowhere else — no backup, no git history. Delete a volume only by name, only after checking what it belongs to, and only with the user's explicit go-ahead:

```bash
docker volume ls
docker volume inspect <name>
```

`docker system prune -a --volumes` deletes across every project on the machine, including ones unrelated to the current task. Reach for a scoped alternative instead; the plugin's guard hook blocks the unscoped forms.

## Configuring resources

The VM's CPU, memory, and disk allocation is per-runtime:

- **OrbStack** — Settings, or `orb config set memory_mib 8192`. Memory is allocated on demand, so a high ceiling costs little when idle.
- **Docker Desktop** — Settings → Resources, or `~/Library/Group Containers/group.com.docker/settings-store.json`.
- **Colima** — set at creation: `colima start --cpu 4 --memory 8 --disk 100`. Changing memory or CPU needs a restart; growing the disk needs `colima start --disk N` after a stop.
- **Linux Engine** — no VM. Limit per container with `--memory` and `--cpus`, or globally through cgroup settings.

Per-container limits belong in Compose (`deploy.resources.limits`) and apply regardless of runtime.

## Registry authentication

```bash
docker login                                    # Docker Hub
docker login ghcr.io -u <user> --password-stdin # other registries
```

Pipe the token via `--password-stdin`; a token passed as `--password` lands in shell history. Credentials are stored per the `credsStore` in `~/.docker/config.json`, which on macOS should be `osxkeychain`. Anonymous Docker Hub pulls are rate-limited by IP, so `toomanyrequests` on a shared network or in CI usually means an unauthenticated pull rather than an actual problem with the image.

## Verify

After any runtime change, confirm the daemon is genuinely serving before moving on:

```bash
docker version    # a server section is present
docker run --rm hello-world
```

Report which runtime and context answered, since that is the fact the next session needs.

## Gotchas

- Two runtimes installed at once is the usual cause of "it worked yesterday". `docker context ls` settles it in one command.
- On Linux, `permission denied` on the socket means the user is not in the `docker` group. Group membership applies at next login, not immediately — `newgrp docker` for the current shell.
- Adding a user to the `docker` group grants root-equivalent access to the host. Rootless mode is the alternative when that matters.
- The Docker Desktop VM's disk image never shrinks on its own. Deleting images frees space inside the VM but not on the host until the disk is compacted or reset.
- `docker` and `orb`, `colima`, or `podman machine` manage different layers. Stopping a container is not stopping the VM, and a stopped VM still holds its disk allocation.
