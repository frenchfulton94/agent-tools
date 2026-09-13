---
name: deploying-apps-to-dokploy
description: Deploys and configures applications on a self-hosted Dokploy PaaS — choosing a build type (Nixpacks, Railpack, Dockerfile, Buildpack, or static), connecting GitHub, GitLab, Bitbucket, Gitea, or a Docker registry, adding domains and certificates, wiring environment variables and vault-backed secrets, and releasing safely with zero-downtime, preview deployments, and rollbacks. Use when the user wants to get an application or Compose stack running on Dokploy, change how it builds, or work out why a deployed app is unreachable — including symptom-only reports like "my Dokploy domain returns 404", "Bad Gateway after deploying", or "the certificate never issued". For authoring the Dockerfile or compose file itself, use containerizing-apps; for triggering deploys from CI or scripting Dokploy, use automating-dokploy.
license: MIT
---

# Deploying Apps to Dokploy

Get a service running on a self-hosted Dokploy instance, give it a domain that resolves over HTTPS, and release changes to it without dropping requests. This skill covers the build type, the source provider, the domain, the environment variables, and the release mechanics around them.

To write the `Dockerfile`, the `compose.yaml`, or the `.dockerignore` that Dokploy then builds, use `docker-workbench:containerizing-apps`. To drive the CLI or API — triggering a deploy from CI, scripting a change across services, reading deployment logs — use `automating-dokploy`.

## Every id comes from the object model

Dokploy nests four levels: **Organizations → Projects → Environments → services**.

- An **organization** is the top-level tenant. Users, servers, registries, SSH keys, certificates, and S3 destinations belong to it.
- A **project** groups related services and owns shared environment variables.
- An **environment** isolates services inside a project. Each project starts with a default environment, and services in different environments cannot see each other.
- A **service** is an Application, a Database, or a Docker Compose stack.

An application belongs to an **environment**, not to a project directly. Every CLI and API call takes an id from this hierarchy, so a `create` call that carries the wrong level's id validates and then lands somewhere unexpected. Confirm which environment is the target before creating anything.

Shared variables follow the same nesting: environment-level values override project-level ones, and service-level values override both.

## Domain edits reach Applications immediately, and Compose services not until you redeploy

This asymmetry produces most "my domain returns 404" reports, and neither feature page states it.

| Service type | Routing mechanism | After a domain change |
|---|---|---|
| Applications (Nixpacks, Railpack, Dockerfile, Buildpack, Static) | A per-domain file in Traefik's dynamic configuration, through Traefik's file provider | Applies immediately. The file provider hot-reloads; no redeploy |
| Templates and Compose services | Traefik labels on the container, read from Docker metadata at deploy time | Keeps serving the old routing until you redeploy |

So for a template or a Compose service, every domain **add, edit, or removal** needs a redeploy. Nothing warns you: the panel saves the change, the service stays up, and the new host 404s while the old one still answers. If a Compose domain is not working, redeploy before investigating anything else.

For an Application, the same 404 means something else — check Traefik's logs, which the docs say should carry information about what is wrong.

## Four traps and the symptom each produces

**1. DNS before the domain, or the certificate never issues.** Point the `A` record at the server's IP address *first*, then add the domain in Dokploy. Added in the other order, Let's Encrypt issuance fails, and recovering means recreating the domain or restarting Traefik. Symptom: the domain resolves but has no certificate, and nothing in the deployment log mentions it.

**2. `Ports` under Advanced Settings interferes with domain routing.** Domain routing uses the domain's own `Container Port` field, which tells Traefik where to send traffic inside the container and exposes nothing. `Ports` under Advanced Settings publishes a host port for `IP:port` access, which is a different job. Leave it unset unless `IP:port` access is genuinely wanted. Symptom: the deployment succeeds, the logs look healthy, and the domain does not work.

**3. A container listening on `127.0.0.1` returns Bad Gateway.** Vite, Astro, and Vue apps default to localhost, which is unreachable from outside the container. Bind `0.0.0.0`. In Vite that is `host: true` in **both** `server` and `preview` — the preview server is what a built app runs, and setting only `server` leaves production broken:

```ts
export default defineConfig({
	preview: { host: true, port: 3000 },
	server: { host: true, port: 3000 },
});
```

Redeploy after the change. Symptom: Bad Gateway immediately after a deployment that reported success.

**4. A failing healthcheck stops routing with no domain-level symptom.** A Swarm healthcheck that never passes keeps traffic away from the container, and the domain configuration gives no hint. Either make the healthcheck pass or remove it. Symptom: the domain never works, the container appears to be running, and the domain settings are correct.

## Verify before reporting a deployment done

Confirm each of these against the panel or real command output, not expectation:

- [ ] The deployment finished, rather than a queued or in-flight build being read as done
- [ ] The domain's `Container Port` matches the port the process listens on — `80` for a Static build or any Nixpacks build with a Publish Directory, since those serve through NGINX
- [ ] HTTPS is on with the `letsencrypt` certificate, and the domain answers over `https://`
- [ ] The service was redeployed if it is a template or Compose service and its domain changed
- [ ] The process is bound to `0.0.0.0`
- [ ] No secret was pasted into the environment editor that belongs in a vault reference

## Where the rest lives

- `references/build-types.md` — the five build types with their exact fields and variables: Nixpacks and its `NIXPACKS_*` overrides, Railpack and its `RAILPACK_*` overrides and pinnable version, Dockerfile path, context, stage, build arguments and build-time secrets, Heroku and Paketo buildpacks, and Static's port-80 requirement. Read it before changing how an app builds.
- `references/providers-and-domains.md` — GitHub, GitLab, Bitbucket, Gitea, plain Git, Docker registries, and the zip and raw sources; the seven domain fields; Let's Encrypt and the HTTP-only limit on generated `traefik.me` domains; environment variables at every level; and the `${{vault.<provider-name>.<ref>}}` syntax for secrets that stay in an external manager. Read it for any domain, certificate, or secret question.
- `references/compose-services.md` — `dokploy-network`, Traefik labels written by hand, `deploy.labels` under Swarm, `expose` in preference to `ports`, the `.env` file that is written but not injected, and the redeploy requirement in context. Read it for any Compose or Stack service.
- `references/release-lifecycle.md` — zero-downtime deployment, the two kinds of rollback, preview deployments for pull requests, the going-production path that moves builds off the server, watch paths for monorepos, and patches for changing files at build time without forking upstream.
- `references/framework-recipes.md` — one table of the published framework guides: build path, build type or start command, publish directory, and domain port. Below the table, the three configuration shapes all seventeen reduce to, each with the gotcha that comes with it. Read it to place a specific framework quickly.
