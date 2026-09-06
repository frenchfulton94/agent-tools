---
name: containerizing-apps
description: Writes and fixes Dockerfiles, Compose files, and .dockerignore, and drives the build-run-debug loop for containerized apps. Use when the user wants to containerize or dockerize a project, add or edit a Dockerfile or compose.yaml, shrink an image or speed up a build, wire up multi-service local development, or work out why a container will not build, start, reach another service, or keep its data — including when they describe only the symptom ("the build takes forever", "my app can't connect to the database", "it works on my machine but not in the container").
license: MIT
---

# Containerizing Apps

Produce images that build fast, run as a non-root user, carry no secrets, and start in a known-good order. This skill covers authoring `Dockerfile`, `compose.yaml`, and `.dockerignore`, and the loop of building and running them.

To install or repair the runtime the `docker` CLI talks to, use `managing-container-runtimes` instead.

## Rebuild before you diagnose

Images do not track source files. `docker compose up -d` reuses the image that already exists, so an edit to source or to the Dockerfile has no effect until the image is rebuilt — and the logs read afterward describe the previous code.

Before reading logs or output to diagnose anything just changed, rebuild:

```bash
docker compose up -d --build                        # compose projects
docker build -t <name> . && docker run --rm <name>  # single image
```

This holds when the change looks too small to matter. Chasing a bug that a stale image is still producing costs far more than the rebuild does.

## Dockerfile shape

Multi-stage, pinned base, dependencies before source, non-root at the end:

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
RUN npm run build

FROM node:22-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --omit=dev
COPY --from=build /app/dist ./dist
USER node
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

Five things that example does, each worth carrying over when adapting it to another stack:

- **Manifest before source.** `COPY package.json`, install, then `COPY . .`. Reversed, every source edit invalidates the install layer and reinstalls every dependency.
- **A pinned tag, never `latest`.** `latest` moves underneath the project and turns a build that worked yesterday into a failure with no diff to explain it. Pin by digest (`node:22-bookworm-slim@sha256:...`) when reproducibility matters more than picking up patch releases.
- **Cache mounts for the package manager.** `--mount=type=cache` keeps the download cache across builds without baking it into a layer.
- **A separate runtime stage.** Compilers, headers, and dev dependencies stay in the build stage and never ship.
- **`USER` before `CMD`.** Root in the final stage is the default, and it is the wrong default.

Write `CMD` and `ENTRYPOINT` in exec form — a JSON array. Shell form wraps the process in `/bin/sh -c`, which becomes PID 1 and does not forward `SIGTERM`, so `docker stop` hangs for the full grace period and then kills the process without letting it shut down.

Per-language starting points — Python with uv, Go, Rust, JVM, and static frontends — are in `references/dockerfile-patterns.md`. Read it when the stack is not Node, or when a build needs system packages, private registries, or compiled extensions.

## Secrets

Never `ENV`, `ARG`, or `COPY` a secret into an image. Every layer is readable, `ARG` values appear in `docker history`, and squashing does not remove them. For a build-time credential use a secret mount, which is never persisted to a layer:

```dockerfile
RUN --mount=type=secret,id=npmtoken \
    NPM_TOKEN="$(cat /run/secrets/npmtoken)" npm ci
```

```bash
docker build --secret id=npmtoken,env=NPM_TOKEN .
```

Runtime secrets belong in `--env-file`, Compose `env_file`, or the orchestrator's secret store — supplied when the container starts, never built in.

## .dockerignore

Write one before the first build. Without it the entire directory is sent as build context, which is slow, and `COPY . .` sweeps up `.env`, `.git`, and local credentials.

```gitignore
.git
.env
.env.*
node_modules
**/__pycache__
.venv
dist
build
*.log
```

Start from `.gitignore`, then add anything the build regenerates for itself.

## Compose

Three points come up on nearly every project:

- **`depends_on` does not wait for readiness.** It waits for the container to *start*. A database that begins accepting connections five seconds later will still refuse the app's first query. Give the dependency a `healthcheck` and depend on `condition: service_healthy`.
- **`localhost` inside a container means that container.** Services reach each other by service name (`postgres:5432`). To reach a server running on the host, use `host.docker.internal`.
- **Named volumes for state, bind mounts for source.** A bind mount placed over a directory the image populated hides whatever the image put there.

Healthcheck syntax, startup ordering, profiles, `watch` for live reload, environment precedence, and multi-file overrides are in `references/compose.md`. Read it for any project with more than one service.

## Hardening the running container

The run-time defaults are permissive: root inside the namespace, a writable root filesystem, most Linux capabilities, and no resource ceiling. Three of these cost nothing to fix and need no application changes:

```yaml
    user: "10001:10001"
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
```

Never bind-mount `/var/run/docker.sock` into a container without treating that container as part of the host's trust boundary. The daemon runs as root and will mount any host path on request, so a process holding the socket is root on the host — the container boundary is gone. Tools that ask for it (CI runners, reverse proxies, monitoring agents) usually have a narrower mode, or can go through a socket proxy.

Capability dropping, read-only root filesystems with `tmpfs`, network isolation, runtime secrets as files rather than environment variables, and an order to adopt them in are in `references/hardening.md`. Read it when a container is going anywhere near production, or when the user asks about securing, hardening, or locking down a container.

## Verify

Before reporting a containerization task done, confirm each of these against real command output rather than expectation:

- [ ] The image builds: `docker build -t <name> .` (add `--no-cache` when a cached layer is the suspect)
- [ ] The container is still up seconds later, not restart-looping: `docker compose ps` or `docker ps`
- [ ] The process is not root: `docker compose exec <svc> id` prints a non-zero uid
- [ ] The service answers where it claims to: `curl` the published port
- [ ] No secret survives in the image: `docker history --no-trunc <name>` shows none

When a container fails at any of these and the cause is not immediately visible in the last few log lines, dispatch the `container-debugger` agent rather than pulling full build output and logs into this conversation.

## Gotchas

- Compose v2 ignores the top-level `version:` key and warns about it — leave it out. The default filename is `compose.yaml`; `docker-compose.yml` is still read.
- The command is `docker compose`, a subcommand. `docker-compose` is the retired v1 binary and is absent from current installs.
- On Apple Silicon, an amd64-only image gives `exec format error` or silent emulation slowness. Set `platform: linux/amd64` on that service and treat it as a stopgap.
- `EXPOSE` documents a port; it publishes nothing. Publishing is `-p` or Compose `ports`.
- A server bound to `127.0.0.1` inside a container is unreachable from outside it. Bind `0.0.0.0`.
- `docker compose down` keeps named volumes; `down -v` deletes them along with their data.
- `COPY --chown=` is cheaper than a separate `RUN chown -R`, which duplicates the whole tree into a new layer.
- Publishing binds every interface. `ports: ["127.0.0.1:5432:5432"]` keeps a debugging port on the local machine; `"5432:5432"` on a laptop exposes a database to whatever network it joins.

A symptom-to-cause table for containers that build but misbehave at runtime is in `references/troubleshooting.md`. For scanning an image for vulnerabilities, producing an SBOM, or signing images, use `securing-container-supply-chain`.
