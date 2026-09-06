# Container symptoms and causes

Contents:
- [Build failures](#build-failures)
- [Container exits immediately](#container-exits-immediately)
- [Container runs but is unreachable](#container-runs-but-is-unreachable)
- [Service cannot reach another service](#service-cannot-reach-another-service)
- [Data disappears](#data-disappears)
- [Permission errors](#permission-errors)
- [Slow builds](#slow-builds)
- [Commands for narrowing down](#commands-for-narrowing-down)

## Build failures

| Message | Cause |
|---|---|
| `failed to compute cache key: "/x" not found` | The path is excluded by `.dockerignore`, or is outside the build context |
| `exec format error` during `RUN` | Base image architecture differs from the builder. Set `--platform` or use a multi-arch tag |
| `no match for platform in manifest` | The tag has no build for this architecture |
| `COPY failed: file not found` | Relative to the build *context*, not the Dockerfile's directory. `docker build -f sub/Dockerfile .` has context `.` |
| Package installs fail only inside the build | No DNS or proxy in the build environment; or an `apt-get install` without a preceding `apt-get update` in the same `RUN` |
| `permission denied` writing during `RUN` | A `USER` earlier in the file dropped privileges. Switch back to root for the install, then drop again |

## Container exits immediately

`docker ps -a` shows the exit code; `docker logs <name>` shows what it said on the way out.

| Exit code | Meaning |
|---|---|
| 0 | The process finished. A one-shot command was used where a server was intended |
| 1 | Application error — the logs have it |
| 125 | The docker command itself was wrong |
| 126 | The entrypoint is not executable |
| 127 | The entrypoint was not found — wrong path, or a binary missing from a slim base |
| 137 | SIGKILL. Usually the memory limit; check `docker inspect <name> --format '{{.State.OOMKilled}}'` |
| 139 | Segfault, often an architecture mismatch |
| 143 | SIGTERM, a normal stop |

A container with nothing to do in the foreground exits by design. The main process has to stay in the foreground — a daemon that forks and returns ends the container with it.

## Container runs but is unreachable

Work outward in this order:

1. **Is the process listening inside?** `docker exec <name> sh -c 'netstat -tlnp 2>/dev/null || ss -tlnp'`
2. **Is it bound to `0.0.0.0`?** A process on `127.0.0.1` inside a container accepts only connections from that container.
3. **Is the port published?** `docker ps` shows the mapping. `EXPOSE` alone publishes nothing.
4. **Is the host-side port right?** `-p 8080:3000` is host 8080 to container 3000. Reversing these is the single most common mistake here.

## Service cannot reach another service

- `localhost` inside a container is that container. Use the Compose service name.
- Both services must share a network. Custom `networks:` blocks can isolate them from each other unintentionally.
- The target may be up but not ready. `depends_on: condition: service_healthy` is the fix, not a sleep.
- Reaching the *host* needs `host.docker.internal`, plus `extra_hosts: ["host.docker.internal:host-gateway"]` on Linux.
- DNS resolves service names, not container names, in Compose — unless `container_name` is set explicitly.

## Data disappears

- Anonymous volumes are recreated on `docker compose down` and after `docker run --rm`. Name every volume that holds state.
- The mount path must be where the process actually writes. `/var/lib/postgresql/data` for Postgres, `/var/lib/mysql` for MySQL — mounting one directory up stores nothing useful.
- `docker compose down -v` deletes named volumes. So does `docker volume prune`.
- Changing the Compose project name (usually by renaming the directory) points the project at a fresh set of volumes; the old data is still there under the old project prefix. `docker volume ls` shows both.

## Permission errors

Bind-mounted files keep their host ownership. A container user with a different uid cannot write them.

- Match the uid: `user: "${UID:-1000}:${GID:-1000}"` in Compose, with `UID`/`GID` exported by the shell.
- Or build the image with a user whose uid matches the host user.
- Named volumes avoid the problem entirely — Docker initializes their ownership from the image.
- On SELinux hosts, append `:z` (shared) or `:Z` (private) to the bind mount.

## Slow builds

- Check the context size first — the line `transferring context: ... MB` at the start of a build. A large number means `.dockerignore` is missing or incomplete.
- Dependency installs re-running on every build means source is copied before the manifest.
- Add `--mount=type=cache` for the package manager's cache directory.
- Emulated builds (arm64 host, amd64 image) can be an order of magnitude slower. Build natively and use `docker buildx build --platform linux/amd64,linux/arm64` only for publishing.
- `docker buildx du` shows what the build cache holds; `docker buildx prune --filter until=168h` trims it without touching images or volumes.

## Commands for narrowing down

```bash
docker logs --tail=100 -f <name>                     # what it said
docker inspect <name> --format '{{json .State}}'     # exit code, OOM flag, health
docker inspect <name> --format '{{json .Mounts}}'    # what is actually mounted
docker exec -it <name> sh                            # look around inside
docker run --rm -it --entrypoint sh <image>          # look around without starting the app
docker history --no-trunc <image>                    # layer sizes and build commands
docker stats --no-stream                             # live CPU and memory per container
docker events --since 10m                            # restarts, OOM kills, health transitions
```

For an image with no shell (`distroless`, `scratch`), attach a debug sidecar sharing its namespaces: `docker run --rm -it --pid=container:<name> --network=container:<name> nicolaka/netshoot`.
