# Compose reference

Contents:
- [Baseline file](#baseline-file)
- [Healthchecks and startup order](#healthchecks-and-startup-order)
- [Environment precedence](#environment-precedence)
- [Volumes and mounts](#volumes-and-mounts)
- [Networking between services](#networking-between-services)
- [Live reload with watch](#live-reload-with-watch)
- [Profiles](#profiles)
- [Multi-file overrides](#multi-file-overrides)
- [Hardened service](#hardened-service)
- [Everyday commands](#everyday-commands)

## Baseline file

No `version:` key. Compose v2 ignores it and emits a warning.

```yaml
name: myapp

services:
  api:
    build:
      context: .
      target: runtime
    ports:
      - "3000:3000"
    env_file:
      - .env
    environment:
      DATABASE_URL: postgres://app:secret@postgres:5432/app
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: app
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s

volumes:
  pgdata:
```

The top-level `name` fixes the project name. Without it the project is named after the containing directory, so renaming or cloning the directory orphans the existing volumes and containers.

## Healthchecks and startup order

`depends_on` in its short list form only orders container *starts*. Use the long form with a condition:

| Condition | Waits until |
|---|---|
| `service_started` | The container has started. The default, and rarely what is wanted |
| `service_healthy` | The container's own `healthcheck` reports healthy |
| `service_completed_successfully` | The container exited 0 — for migration and seed jobs |

Healthcheck notes:

- `test` in `CMD` form is exec'd directly; `CMD-SHELL` runs through a shell, which is what allows pipes and `||`.
- `start_period` suppresses failures during boot instead of counting them toward `retries`. Without it a slow-starting service can burn through its retries and be marked unhealthy while still coming up.
- The check runs *inside* the container, so it can only use tools the image ships. `curl` is absent from most slim and Alpine images; use `wget -qO- --spider`, the language runtime, or a purpose-built healthcheck binary.

A one-shot migration gate:

```yaml
  migrate:
    build: .
    command: ["npm", "run", "migrate"]
    depends_on:
      postgres:
        condition: service_healthy

  api:
    depends_on:
      migrate:
        condition: service_completed_successfully
```

## Environment precedence

Highest wins:

1. `docker compose run -e VAR=...`
2. Shell environment, when the value is interpolated as `${VAR}`
3. The service's `environment:` block
4. The service's `env_file:` list, later files overriding earlier ones
5. The project `.env` file
6. `ENV` in the image's Dockerfile

The project `.env` beside the compose file feeds `${VAR}` interpolation *into the compose file itself*. That is a different job from `env_file:`, which passes variables into the container. Conflating the two is the usual cause of a variable that is visibly set and still missing at runtime.

## Volumes and mounts

```yaml
    volumes:
      - pgdata:/var/lib/postgresql/data   # named volume — state
      - ./src:/app/src                    # bind mount — source
      - /app/node_modules                 # anonymous volume — shadow the bind
```

The third line is the standard fix for a bind-mounted source tree hiding dependencies the image installed: it re-shadows `node_modules` with container-side content.

Bind mounts cross the host filesystem boundary and are slower than named volumes on macOS and Windows. Keep databases and caches in named volumes and bind-mount only what needs editing.

## Networking between services

Compose puts every service on a default network where the service name resolves. `postgres:5432` works from the `api` container; `localhost:5432` does not, because `localhost` inside a container is that container.

- `ports:` publishes to the host. Two services can talk to each other without it.
- `expose:` is documentation only and does nothing functional in Compose v2.
- `host.docker.internal` resolves to the host from inside a container. On Linux this requires `extra_hosts: ["host.docker.internal:host-gateway"]`; on Docker Desktop and OrbStack it is present already.
- Custom networks isolate groups of services; a service on no shared network with another cannot reach it at all.

## Live reload with watch

`docker compose watch` syncs or rebuilds on file change, replacing hand-rolled bind-mount-plus-nodemon setups:

```yaml
    develop:
      watch:
        - action: sync
          path: ./src
          target: /app/src
        - action: rebuild
          path: package.json
```

`sync` copies changed files into the running container. `rebuild` rebuilds the image and restarts the service — use it for anything that changes the dependency set. `sync+restart` sits between the two, for config files a process reads only at boot.

## Profiles

Services with a `profiles:` key stay dormant unless their profile is requested:

```yaml
  seed:
    build: .
    command: ["npm", "run", "seed"]
    profiles: ["tools"]
```

`docker compose up` skips it; `docker compose --profile tools up` includes it. Good for seeders, admin UIs, and load generators that should not run in an ordinary `up`.

## Multi-file overrides

`compose.yaml` plus `compose.override.yaml` merge automatically. Naming files explicitly disables that:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

Later files win. Scalars are replaced; sequences such as `ports` and `volumes` are *appended*, not replaced — an override that adds a port mapping gets both. Use `!reset` or `!override` on a key to replace a sequence outright.

## Hardened service

The security-relevant keys, gathered in one place. Each is explained in `hardening.md`; this is the shape they take in a Compose file.

```yaml
services:
  api:
    image: myorg/api:1.4.2@sha256:...
    user: "10001:10001"
    read_only: true
    tmpfs:
      - /tmp:size=64m,mode=1777
    cap_drop: [ALL]
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits: { memory: 512M, cpus: "1.0" }
    logging:
      driver: json-file
      options: { max-size: "10m", max-file: "3" }
    secrets: [db_password]
    networks: [backend]

networks:
  backend:
    internal: true

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

Adopt these one at a time. `read_only` and `cap_drop: [ALL]` are the two that need application-specific adjustment; the rest usually apply unchanged.

## Everyday commands

```bash
docker compose up -d --build          # build and start in background
docker compose ps                     # status, health, published ports
docker compose logs -f --tail=50 api  # follow one service
docker compose exec api sh            # shell in a running container
docker compose run --rm api npm test  # one-off in a fresh container
docker compose config                 # print the fully merged, interpolated file
docker compose down                   # stop and remove; named volumes survive
```

`docker compose config` is the fastest way to settle an argument about which override or `.env` value actually applied — it prints the file Compose is really using.
