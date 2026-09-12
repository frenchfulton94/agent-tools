# API recipes

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [Base URL and authentication](#base-url-and-authentication)
- [Who can reach the API](#who-can-reach-the-api)
- [The documented CI recipe](#the-documented-ci-recipe)
- [GitHub Actions: the docs' own workflow](#github-actions-the-docs-own-workflow)
- [Response shape: what the docs show and what they don't](#response-shape-what-the-docs-show-and-what-they-dont)
- [Pagination](#pagination)
- [Token scoping](#token-scoping)

## Base URL and authentication

The default OpenAPI base URL is `http://localhost:3000/api`; replace the host with the
instance's own IP or domain. Every request carries the token as an `x-api-key` header:

```bash
curl -X 'GET' \
  'https://your-domain/api/project.all' \
  -H 'accept: application/json' \
  -H 'x-api-key: <token>'
```

Generate the token from `/settings/profile`, in its API/CLI section. This is the same
token `dokploy auth -u <url> -t <token>` stores for CLI use — one credential, two
interfaces.

## Who can reach the API

By default, only authenticated administrators (Owner or Admin) can reach the API or the
Swagger UI at `<host>:3000/swagger`. A Member has no access to either until an Owner or
Admin grants the `Access to API/CLI` permission, at which point they can generate their
own token and open Swagger too. The docs' own caution is worth repeating rather than
softening: "The API provides advanced functionalities. Make sure you understand the
operations you're performing to avoid unintended changes to the system."

## The documented CI recipe

Deploying from a pipeline is two calls: find the id, then act on it.

```bash
curl -X 'GET' \
  'https://your-domain/api/project.all' \
  -H 'accept: application/json' \
  -H 'x-api-key: <token>'
```

Read the target application's `applicationId` out of the response, then:

```bash
curl -X 'POST' \
  'https://your-domain/api/application.deploy' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: <token>' \
  -d '{
  "applicationId": "string"
}'
```

This is the docs' own worked example, not paraphrased — it's the one path this plugin's
design explicitly calls out as verified in writing at the documentation level. The same
two-step shape (find the id, then call the action) applies to any other resource: use
`dokploy <resource> --help` or Swagger to find the right id field name and the right
action for that resource, per `references/cli-command-map.md`.

## GitHub Actions: the docs' own workflow

For a registry other than DockerHub — which has its own webhook path, in
`references/auto-deploy-and-schedules.md` — the docs show calling `application.deploy`
from a GitHub Actions step, after a build-and-push step the excerpt doesn't reproduce in
full ("...Same as step 7 from the previous example"):

```yaml
name: Build Docker images

on:
  push:
    branches: ["main"]

jobs:
  build-and-push-dockerfile-image:
    runs-on: ubuntu-latest

    steps:
       ...Same as step 7 from the previous example

      - name: Trigger Dokploy Deployment
        uses: dokploy/dokploy-action@v1
        run: |
            curl -X 'POST' \
            'https://<your-dokploy-domain>/api/application.deploy' \
            -H 'accept: application/json' \
            -H 'x-api-key: YOUR-GENERATED-API-KEY' \
            -H 'Content-Type: application/json' \
            -d '{
                 "applicationId": "YOUR-APPLICATION-ID"
            }'
```

Reproduced exactly as the docs show it, including one thing worth flagging before copying
it: this step combines `uses:` and `run:`, which is not valid GitHub Actions syntax for a
single step — a step is one or the other. Treat this as showing *where* the
`application.deploy` call goes in a workflow, not as a copy-paste-ready step. A working
version needs either `uses: dokploy/dokploy-action@v1` alone, with whatever inputs that
Action defines (not checked here), or a plain `run:` step with the `curl` call and no
`uses:`. The docs separately point at
<https://github.com/marketplace/actions/dokploy-deployment> as a maintained Action; its
actual inputs weren't checked for this skill.

## Response shape: what the docs show and what they don't

The docs' `project.all` example returns a JSON array of project objects, each nesting its
applications and every database type as its own array (`mariadb`, `mongo`, `mysql`,
`postgres`, `redis`, `compose`). That example carries timestamps from 2024 and was not
re-run against a live instance for this skill — its field names (`projectId`,
`applicationStatus`, `databasePassword`, and the rest) are what the docs show, not what
this plugin observed.

Treat that shape as illustrative, not current. **The single reliable source for a
response's real shape is Swagger on the instance actually being scripted against** —
`<host>:3000/swagger` — because it reflects the version installed, not a docs page that
may be stale in the same way the CLI page is (see `references/cli-command-map.md`'s
`app`/`env`/`database` discrepancies). Where an endpoint's response shape matters and
Swagger hasn't been checked, say so rather than asserting field names from memory or from
this file.

## Pagination

The docs show no pagination parameters on any listing endpoint — `project.all`'s example
returns every project in one array. No page size, cursor, or offset parameter is
documented anywhere in the corpus this file was written from. If a listing action does
paginate on the version being scripted against, Swagger is where that would show up; this
file does not assert a pagination scheme that isn't documented.

## Token scoping

From Dokploy's Production Hardening Guide: API/CLI tokens are scoped to the organization,
and can optionally be given an expiration. The guide's operator-side recommendation is
specific: set an expiration on every token instead of leaving one to stand forever, issue
a separate token per integration (CI, webhook, script) so one can be revoked without
breaking the others, and regenerate immediately on offboarding or suspected exposure.
Broader hardening controls beyond API/CLI tokens — the rest of that guide's 25-control
checklist — are `hardening-dokploy`'s territory; this file states only the piece directly
relevant to minting a token for a script.
