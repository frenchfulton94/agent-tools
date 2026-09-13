# Compose and Stack services

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [Compose or Stack](#compose-or-stack)
- [The redeploy requirement](#the-redeploy-requirement)
- [Dokploy-managed domains](#dokploy-managed-domains)
- [Manual Traefik labels](#manual-traefik-labels)
- [Labels under Stack](#labels-under-stack)
- [expose, not ports](#expose-not-ports)
- [Environment variables are not injected](#environment-variables-are-not-injected)
- [Volumes that survive a deployment](#volumes-that-survive-a-deployment)
- [Overriding the compose command](#overriding-the-compose-command)

For authoring the compose file itself — service definitions, healthchecks, startup
order, named volumes against bind mounts — use `docker-workbench:containerizing-apps`.
This file covers only what Dokploy adds on top.

## Compose or Stack

Dokploy offers two configuration methods for the same file:

- **Docker Compose** — standard compose behaviour.
- **Stack** — Docker Swarm orchestration. `build` is not available, so every image has
  to be built elsewhere and pulled from a registry.

The two differ in where Traefik labels go and in how ports behave, so decide first.

## The redeploy requirement

Compose services and template-created services route through Traefik **labels**, read
from Docker container metadata at deployment. Applications route through Traefik's file
provider and hot-reload.

The consequence: every domain add, edit, or removal on a Compose service needs a
redeploy before it takes effect. Configure the domain, redeploy, wait for the
deployment to finish, then test. A 404 on a Compose domain that was just changed is
this, not a Traefik fault.

## Dokploy-managed domains

Since v0.7.0, the Domains tab works for Compose services, and this is the recommended
path. At deployment Dokploy injects the Traefik labels and network configuration into
the compose file for you. The **Preview Compose** button renders the final file that
will run, which is the way to check what was injected before deploying.

Two limits worth knowing:

- With no domains and no Isolated Deployments, the file is deployed exactly as written —
  no labels and no network changes.
- Without Isolated Deployments, Dokploy adds `dokploy-network` only to the service the
  domain names. Every other service that needs to reach it has to join
  `dokploy-network` too.

**Isolated Deployments** creates a network named after the application, attaches every
service in the file to it, and connects Traefik to that network. It removes the need to
mention `dokploy-network` at all, and it is what makes two instances of the same
template coexist — without it, two WordPress stacks collide on service names in the
shared network. All open-source templates ship with it enabled.

## Manual Traefik labels

The alternative is to write the routing yourself. Two steps: put the service on
`dokploy-network`, then add the labels.

```yaml
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    expose:
      - 3000
    networks:
      - dokploy-network
    labels:
      - traefik.enable=true
      - traefik.http.routers.frontend-app.rule=Host(`frontend.dokploy.com`)
      - traefik.http.routers.frontend-app.entrypoints=web
      - traefik.http.services.frontend-app.loadbalancer.server.port=3000

networks:
  dokploy-network:
    external: true
```

The network declaration carries `external: true` because Dokploy's installation created
it; a compose file that omits that flag creates a second, unconnected network.

The four labels, in order: enable Traefik for this service; match the host; attach the
router to the `web` entrypoint; and name the port the service listens on inside the
container. Replace the router and service identifier — `frontend-app` above — with
something unique per service, or two services will fight over one router.

## Labels under Stack

Under Stack, labels go beneath `deploy.labels` rather than directly under `labels`, and
the service needs a pre-built image:

```yaml
services:
  frontend:
    image: your-registry.com/frontend:latest
    expose:
      - 3000
    networks:
      - dokploy-network
    deploy:
      labels:
        - traefik.enable=true
        - traefik.http.routers.frontend-app.rule=Host(`frontend.dokploy.com`)
        - traefik.http.routers.frontend-app.entrypoints=web
        - traefik.http.services.frontend-app.loadbalancer.server.port=3000
```

Labels in the wrong place are silently ignored, which produces the same 404 as a
missing redeploy.

## expose, not ports

Use `expose` rather than `ports` for anything reached through a domain. `ports`
publishes on the host, where it can collide with another application or with the panel.
`expose` keeps the port on the container network, which is all Traefik needs.

Under Stack, ports are exposed automatically, so `expose` is the correct form there too
and `ports` should be dropped.

When the domain is configured through the panel rather than by hand, give it the service
name and the port the service listens on:

```yaml
domain: my-app.com
serviceName: app
port: 3000
```

A healthcheck that never passes keeps the domain from ever working, with no symptom at
the domain level. Either make it pass or remove it.

## Environment variables are not injected

Variables set in a Compose service's Environment tab are written to a `.env` file beside
the compose file. They are **not** injected into containers. Consume them explicitly,
either wholesale:

```yaml
services:
  app:
    env_file:
      - .env
```

or one at a time with `${VAR_NAME}` interpolation in the compose file. An application
reading an unset variable at runtime, after the panel clearly shows a value, is this.

## Volumes that survive a deployment

Absolute host paths are cleaned up during deployments. Use the `../files` directory
instead:

```yaml
volumes:
  - "../files/my-database:/var/lib/mysql"
```

Docker named volumes are the other option, and the only one Dokploy's Volume Backups
feature can back up. Bind mounts under `../files` cannot be backed up that way.

Files that come from the repository need to move into Dokploy's File Mounts, under
Advanced → Mounts. Auto Deploy runs `git clone` on every deployment, which clears the
repository directory, so a relative mount such as `./config/file.conf` is empty or
missing on the next deployment.

## Overriding the compose command

Dokploy runs the compose file with a command shown in the UI, and a custom command
**replaces** it rather than appending to it. Adding one flag means writing the whole
command, for example:

```
compose -p <app-name> -f <compose-path> up -d --build --remove-orphans --force-recreate
```

The command always begins with `docker`, so the string above runs as `docker compose …`.

Under Stack, with replicas and a private registry, add `--with-registry-auth`. Without
it, worker nodes cannot authenticate to the registry and fail with errors such as
"no such image" or a Docker authentication failure.
