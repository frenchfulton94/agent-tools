# Runtime hardening

Contents:
- [What the defaults give you](#what-the-defaults-give-you)
- [A hardened service](#a-hardened-service)
- [Dropping capabilities](#dropping-capabilities)
- [no-new-privileges](#no-new-privileges)
- [Read-only root filesystem](#read-only-root-filesystem)
- [Running as a non-root user](#running-as-a-non-root-user)
- [Resource limits](#resource-limits)
- [The Docker socket](#the-docker-socket)
- [Privileged mode and host namespaces](#privileged-mode-and-host-namespaces)
- [Network isolation](#network-isolation)
- [Runtime secrets](#runtime-secrets)
- [seccomp and AppArmor](#seccomp-and-apparmor)
- [Applying this incrementally](#applying-this-incrementally)

## What the defaults give you

A container started with no security flags runs as root inside its namespace, with roughly fourteen Linux capabilities, a writable root filesystem, no memory or CPU ceiling, and the ability to gain privileges through setuid binaries. Namespacing separates it from the host, but a kernel exploit or a misconfigured mount crosses that boundary.

Each control below closes one of those gaps. They are independent — adopting one is worth doing without the others.

## A hardened service

```yaml
services:
  api:
    image: myorg/api:1.4.2@sha256:...
    user: "10001:10001"
    read_only: true
    tmpfs:
      - /tmp:size=64m,mode=1777
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
    networks:
      - backend

  postgres:
    image: postgres:17-alpine
    networks:
      - backend        # no host port published; only `api` can reach it

networks:
  backend:
    internal: true     # no route out to the internet
```

Nothing here requires application changes for a typical stateless web service. The parts that do need attention are `read_only` and `cap_drop: ALL`, covered below.

## Dropping capabilities

`cap_drop: [ALL]` removes everything, then add back only what the process proves it needs:

| Capability | Needed for |
|---|---|
| `NET_BIND_SERVICE` | Binding a port below 1024 |
| `CHOWN`, `SETUID`, `SETGID` | An entrypoint that changes ownership or drops privileges before exec |
| `DAC_OVERRIDE` | Reading or writing files the user does not own — usually a sign of a permissions bug worth fixing instead |

```yaml
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
```

Better than granting `NET_BIND_SERVICE`: listen on 8080 inside the container and publish it as `80:8080`. The capability then is not needed at all.

Find what a process actually uses by dropping `ALL`, running the test suite, and adding back only what the resulting errors name. `capsh --print` inside the container shows the current set.

## no-new-privileges

```yaml
    security_opt:
      - no-new-privileges:true
```

Blocks a process from gaining privileges through setuid or setgid binaries after it starts, which closes the most common local-escalation path inside a container. It has no effect on ordinary application code, so there is rarely a reason not to set it.

## Read-only root filesystem

```yaml
    read_only: true
    tmpfs:
      - /tmp:size=64m,mode=1777
      - /run:size=16m
```

An attacker who achieves code execution cannot drop a payload on disk or modify the application. Most applications need a small number of writable paths — mount each as `tmpfs` (ephemeral) or a named volume (persistent).

Common writable paths by stack: `/tmp` almost always; `/run` and `/var/run` for pid and socket files; nginx wants `/var/cache/nginx` and `/var/run`; JVM apps often want `/tmp` for its hsperfdata; Python may want a writable `__pycache__` unless `PYTHONDONTWRITEBYTECODE=1` is set.

Turn it on and read the resulting errors — they name the paths precisely. Adding a `tmpfs` per error is faster than auditing the application up front.

## Running as a non-root user

Set it in the Dockerfile so the image is safe by default rather than depending on the caller:

```dockerfile
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app
USER 10001:10001
```

Use a numeric uid in `USER`, not just a name. Kubernetes `runAsNonRoot` can only verify a numeric uid; a named user leaves it unable to confirm the container is non-root and it may refuse to start the pod.

Pick a high uid (10000+) so it cannot collide with a host user if a namespace is shared.

## Resource limits

Unbounded containers are a denial-of-service vector against their own host — one runaway process takes down every other container on the machine.

```yaml
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
        reservations:
          memory: 256M
```

Also cap the logs, or a chatty container fills the disk over weeks:

```yaml
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

Runtimes with a JVM or Node heap need the limit communicated to the runtime as well — `-XX:MaxRAMPercentage=75` or `--max-old-space-size` — or the process sizes its heap against the host's memory and is OOM-killed before its own GC reacts.

## The Docker socket

```yaml
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock   # root on the host
```

This is the single highest-impact container security mistake, and it is common because so many tools ask for it — CI runners, reverse proxies with service discovery, monitoring agents, container management UIs.

The Docker daemon runs as root and will mount any host path into a new container on request. A process with the socket can therefore start a privileged container with `/` bind-mounted and read or write anything on the host. There is no container boundary left. It is not "extra permissions"; it is root, and any code execution flaw in that container is a full host compromise.

Alternatives, in order of preference:

1. **Do not.** Most tools asking for it have a narrower mode. Traefik can read a static config file; a CI job can talk to a remote builder.
2. **A socket proxy.** `tecnativa/docker-socket-proxy` sits in front and allows only specific API endpoints, so a service-discovery tool gets `GET /containers/json` and nothing else.
3. **Rootless Docker or Podman.** The socket then grants the unprivileged user's access, not root's.
4. **Read-only mount** (`:ro`). This helps far less than it appears — the Docker API takes actions over `POST` on a socket that is still fully writable at the protocol level. Treat it as a marginal improvement, not a control.

When a tool genuinely needs it, isolate that container as tightly as everything else allows and treat it as part of the host's trust boundary in any threat model.

## Privileged mode and host namespaces

```yaml
    privileged: true       # disables essentially every container control
    pid: host              # sees and can signal every host process
    network: host          # no network namespace; binds host interfaces directly
    ipc: host
    volumes:
      - /:/host            # the entire host filesystem
```

`privileged: true` grants all capabilities, disables seccomp and AppArmor, and allows device access. It is almost never the right answer to a specific problem — a targeted `cap_add` or `devices:` entry usually is. When a container needs one device, name that device.

`network: host` also removes port isolation and makes published-port mappings meaningless, so it can quietly expose services that were supposed to be internal.

## Network isolation

A service reachable only by other containers should not publish a port. In the hardened example above, `postgres` has no `ports:` entry — `api` reaches it over the `backend` network, and nothing on the host or LAN can.

`internal: true` on a network removes its route to the outside, which contains a compromised container that would otherwise be able to exfiltrate data or fetch a second-stage payload.

Publishing binds all interfaces by default. `ports: ["127.0.0.1:5432:5432"]` limits a debugging port to the local machine instead of exposing it to the network — `"5432:5432"` on a laptop on a coffee-shop network is a listening database.

## Runtime secrets

Environment variables are visible to anything that can read `/proc/<pid>/environ`, appear in `docker inspect`, and are inherited by child processes. Compose secrets mount as files instead:

```yaml
services:
  api:
    secrets:
      - db_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

Many images support the `_FILE` convention natively (Postgres, MySQL, and most official database images). For those that do not, read the file at startup.

Whatever the mechanism, keep the secret file out of the image and out of git — `.dockerignore` and `.gitignore` both.

## seccomp and AppArmor

Docker applies a default seccomp profile that blocks around 44 syscalls, and on supported hosts a default AppArmor profile. Both are on unless disabled, and `privileged: true` disables both — which is a large part of why privileged mode is worth avoiding.

A custom profile is worth writing only for a service with an unusual threat model and a stable syscall footprint:

```yaml
    security_opt:
      - seccomp:./seccomp-profile.json
      - apparmor:my-profile
```

Never do `security_opt: [seccomp:unconfined]` to make something work. That removes the default profile entirely to fix what is nearly always one missing capability. Find the syscall instead — `strace` or the audit log will name it.

## Applying this incrementally

Retrofitting all of it at once produces a container that fails for several reasons simultaneously and is hard to debug. In order of benefit per unit of effort:

1. `no-new-privileges` and a non-root `user` — usually zero application changes
2. Resource and log limits — no application changes
3. Remove unnecessary published ports; put internal services on an internal network
4. `cap_drop: ALL`, adding back only what errors demand
5. `read_only` with `tmpfs` for the paths that need writing
6. Move secrets from environment variables to mounted files
7. Custom seccomp, only where it is genuinely warranted

Verify at each step that the service still works, and prefer a failing test to an audit — the container tells you exactly what it needs.
