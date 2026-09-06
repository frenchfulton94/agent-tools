# Runtime setup

Contents:
- [Docker Desktop](#docker-desktop)
- [Colima](#colima)
- [Podman](#podman)
- [Docker Engine on Linux](#docker-engine-on-linux)
- [Rootless mode](#rootless-mode)
- [daemon.json](#daemonjson)
- [Uninstalling cleanly](#uninstalling-cleanly)
- [CI environments](#ci-environments)

For OrbStack, see `orbstack.md`.

## Docker Desktop

```bash
brew install --cask docker-desktop     # macOS
winget install Docker.DockerDesktop    # Windows
```

Starting it: `open -a Docker` on macOS. It takes 20–60 seconds before the daemon answers, so an immediate `docker ps` can still fail — poll `docker version` rather than assuming the start failed.

Resources are under Settings → Resources. The VM disk image grows and never shrinks by itself; Settings → Resources → Advanced offers a disk-image size and a reset, and on macOS the image lives at `~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw`.

The commercial licence applies above a headcount and revenue threshold. Organizations past it either buy licences or move to Rancher Desktop, Colima, Podman, or OrbStack.

## Colima

CLI-only, backed by Lima. No GUI, no licence.

```bash
brew install colima docker docker-compose
colima start --cpu 4 --memory 8 --disk 100
```

`docker` here is the Homebrew CLI, which is the correct use of that formula — paired with a runtime rather than alone.

```bash
colima status
colima stop
colima delete                       # destroys the VM and everything in it
colima start --arch x86_64          # an amd64 VM on Apple Silicon
colima start --vm-type vz --mount-type virtiofs   # faster file sharing on macOS 13+
```

CPU and memory changes need a stop and start. Disk can only grow, never shrink, and `colima delete` is the only way back.

Colima also runs Kubernetes with `colima start --kubernetes`.

## Podman

Daemonless and rootless by default. `podman` is close enough to `docker` that aliasing works for most commands.

```bash
brew install podman            # macOS
sudo dnf install podman        # Fedora/RHEL
podman machine init
podman machine start
```

For tools that require a Docker socket, including Testcontainers:

```bash
podman system service --time=0 unix:///tmp/podman.sock &
export DOCKER_HOST=unix:///tmp/podman.sock
```

`podman-compose` exists but lags Compose v2. `docker compose` against a Podman socket is usually the better path.

Rootless containers cannot bind ports below 1024 without extra configuration, which surprises people running nginx on port 80.

## Docker Engine on Linux

No VM — the daemon runs directly. Install from Docker's own repository rather than distribution packages, which are often several versions behind:

```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

The group change applies at next login. `newgrp docker` picks it up in the current shell.

Membership in the `docker` group is equivalent to root on that host — the daemon runs as root and will mount any path into a container. On a shared or hardened machine, use rootless mode instead.

```bash
sudo systemctl status docker
sudo journalctl -u docker -n 50 --no-pager     # daemon logs
```

## Rootless mode

Runs the daemon as an unprivileged user. Containers cannot escalate to host root.

```bash
dockerd-rootless-setuptool.sh install
export DOCKER_HOST=unix:///run/user/$UID/docker.sock
systemctl --user enable --now docker
```

Trade-offs worth stating before recommending it: no ports below 1024 without `CAP_NET_BIND_SERVICE`, no cgroup v1 resource limits, overlay networks unavailable, and slower networking unless `slirp4netns` is swapped for `pasta`.

## daemon.json

`/etc/docker/daemon.json` on Linux; Settings → Docker Engine on Docker Desktop.

```json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" },
  "registry-mirrors": ["https://mirror.example.com"],
  "insecure-registries": ["registry.internal:5000"],
  "default-address-pools": [{ "base": "172.30.0.0/16", "size": 24 }],
  "features": { "containerd-snapshotter": true }
}
```

Two of these solve recurring problems. Log rotation is off by default, so a chatty container can fill a disk over weeks — `max-size` and `max-file` should be set on any long-lived host. And `default-address-pools` resolves the case where Docker's default bridge subnets collide with a corporate VPN and containers lose network access on VPN connect.

Apply with `sudo systemctl reload docker`. A malformed file stops the daemon from starting; `dockerd --validate` checks it first.

## Uninstalling cleanly

Leftover CLI plugins and config from a previous runtime cause "command not found" and context confusion later.

```bash
docker context ls                    # note which contexts belong to what
ls ~/.docker/cli-plugins             # stale compose/buildx plugins live here
cat ~/.docker/config.json            # credsStore and currentContext
```

Remove the app, then its context (`docker context rm <name>`) and any `DOCKER_HOST` left in `.zshrc`, `.bashrc`, or `.profile`.

## CI environments

GitHub Actions Linux runners have Docker preinstalled; use `docker/setup-buildx-action` and `docker/build-push-action` rather than raw `docker build`, since they wire up layer caching to the Actions cache.

macOS runners have no Docker. OrbStack and Colima both run headless there — Colima is the common choice because it has no licence question.

Cache the build layers explicitly or every CI build starts from nothing:

```bash
docker buildx build \
  --cache-from type=gha \
  --cache-to type=gha,mode=max \
  -t app:ci .
```

For tests that need real services, prefer Testcontainers over hand-managed Compose in CI — it handles readiness and cleanup, which is where hand-rolled CI Docker setups usually break.
