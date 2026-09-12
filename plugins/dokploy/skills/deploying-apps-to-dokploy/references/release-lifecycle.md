# Release lifecycle

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [Zero-downtime deployment](#zero-downtime-deployment)
- [Rollbacks](#rollbacks)
- [Preview deployments](#preview-deployments)
- [Going production](#going-production)
- [Resource limits](#resource-limits)
- [Watch paths](#watch-paths)
- [Patches](#patches)
- [Deployment history](#deployment-history)

## Zero-downtime deployment

By default a new deployment stops the running container and starts the new one, and
because both are initialising at once the domain returns Bad Gateway. A healthcheck is
what removes that gap: Swarm waits for the new container to report healthy before
sending it traffic.

Two prerequisites, both easy to miss:

1. The application answers on a health route — conventionally `/health`, returning 200.
2. `curl` exists inside the image. Alpine-based images do not ship it, and the
   healthcheck below fails on every attempt without it.

Set the healthcheck under Advanced → Cluster Settings → Swarm Settings:

```json
{
  "Test": ["CMD", "curl", "-f", "http://localhost:3000/health"],
  "Interval": 30000000000,
  "Timeout": 10000000000,
  "StartPeriod": 30000000000,
  "Retries": 3
}
```

Those durations are nanoseconds: `30000000000` is 30 seconds. Three retries pass before
Swarm switches to the new container.

## Rollbacks

Two independent mechanisms, and choosing between them is the point:

| | Swarm automatic | Registry-based |
|---|---|---|
| Trigger | A failed healthcheck during deployment | A person clicking Rollback |
| Reaches | The immediately previous version | Any previous deployment |
| Needs | A healthcheck and an Update Config | A configured Docker registry |

**Swarm automatic.** Add the healthcheck above, then set Update Config in the same Swarm
Settings panel:

```json
{
  "Parallelism": 1,
  "Delay": 10000000000,
  "FailureAction": "rollback",
  "Order": "start-first"
}
```

An unhealthy new container now reverts to the previous one on its own. This only fires
on healthcheck failure — a deployment that is healthy but wrong stays deployed.

**Registry-based.** Enable it under Deployments → Rollback Settings and select a
registry. Dokploy then tags and pushes every deployment's image, links each deployment
record to its tag, and puts a Rollback button beside each entry. That is what makes
rolling back to an arbitrary earlier release possible. After clicking Rollback, the
image has to be pulled first: the container does not appear in the Logs tab
immediately, and waiting a few seconds is expected rather than a failure.

## Preview deployments

A per-pull-request deployment, for applications using the GitHub integration. Disabled
by default.

- Domains are generated as `traefik.me` hosts by default, with no configuration. The
  default port is 3000 and the default cap is 3 preview deployments per application.
- For a custom domain, configure `*.mydomain.com` and point a wildcard DNS record at the
  server. Dokploy generates hosts following the pattern
  `preview-${appName}-${uniqueId}.traefik.me`.
- A preview is created when a pull request is opened **against the target branch
  configured on the application**. A pull request aimed anywhere else creates nothing,
  which is the usual reason a team sees no previews at all.
- Label filters narrow this further: name one or more labels and only pull requests
  carrying at least one of them get a preview. An empty field means every pull request.
- Each new commit to the pull request rebuilds the preview, and closing or merging the
  pull request cleans it up.
- **Rebuild** (the hammer icon) re-runs the build on the existing code, for picking up
  changed environment variables or retrying a failed build without a new commit.
- Security and redirect configuration on the application is inherited by its previews.
- Reference the generated host from the preview's own environment variables with
  `${{DOKPLOY_DEPLOY_URL}}`.

Dokploy recommends against enabling previews on public repositories, because anyone
able to open a pull request can then run a build on the server.

## Going production

The documented production path moves the build off the deployment server. Nixpacks and
Heroku buildpack builds are resource-hungry: they can time out, and they can freeze a
small VPS, taking every application on it down.

Two options. Adding CPU, RAM, and disk is the expensive one. Building in CI is the
recommendation:

1. Build the image in CI — GitHub Actions, GitLab CI, Gitea Actions — and push it to a
   registry.
2. Set the application's `Source Type` to `Docker` and give it the image name and tag.
3. Deploy. The server pulls and runs; it never builds.
4. Add a domain with the port the image listens on.

Keep it deploying automatically afterwards. Docker Hub can call the application's
webhook URL, found on the Deployments tab, and fires only when the pushed tag matches
the one configured in Dokploy. Any other registry uses the API instead — a `POST` to
`/api/application.deploy` with an `x-api-key` header and the `applicationId`. Both, and
the branch-matching trap that comes with webhooks, belong to `automating-dokploy`.

The same page combines this with the healthcheck and Update Config above, so the server
only ever pulls and switches containers.

## Resource limits

Memory and CPU limits are set under Advanced → Resources, and Dokploy passes the value
straight to the Docker API without parsing units.

- Memory is **raw bytes**: `268435456` is 256 MB, `1073741824` is 1 GB. `1024m` is read
  as 1024 bytes, below Docker's minimum of roughly 6 MB, and the deployment fails with
  a generic Swarm error.
- CPU is **nanoCPUs**: `1000000000` is one core, `500000000` is half a core. `1.5` is
  read as 1 nanoCPU and fails the same way.
- Keep each reservation at or below its limit.

Redeploy after changing resources, or the change does not apply.

## Watch paths

Watch paths scope which changed files trigger a rebuild — the answer to "only rebuild
when `apps/web` changes" in a monorepo. They work on applications and Compose services,
and take an array of patterns:

- `src/*` rebuilds on any change inside `src/`.
- `src/index.js` watches one file.

Supported patterns include `**` for any depth, `*.js` extensions, negations (`!a/*.js`,
`*!(b).js`), extended globs (`+(x|y)`, `!(a|b)`), POSIX classes
(`[[:alpha:][:digit:]]`), brace expansion (`foo/{1..5}.md`, `bar/{a,b,c}.js`), regex
character classes (`foo-[1-5].js`), and regex alternation (`foo/(abc|xyz).js`).

Supported providers are GitHub, GitLab, Bitbucket, and Git — the last one only against
GitHub, GitLab, Bitbucket, or Gitea repositories. With GitHub the feature works with no
configuration; every other provider needs auto-deploy configured first.

## Patches

Patches apply file-level changes to the cloned repository during the build: after the
clone, before the build step, on every build. They are the way to change a file the
build needs without forking upstream or committing the change.

Three operations, all from the Patches section of the application settings: edit an
existing file, create a new file, or mark a file for deletion. Each patch names its
target path and its operation.

Two limits:

- A patch is persistent and applies to every future build. An obsolete patch keeps
  modifying builds until it is removed.
- An edit patch whose target file does not exist in the repository fails the build.

The source repository is never modified; patches exist only inside the build.

## Deployment history

The Deployments tab keeps the last 10 deployments, with live build output while one
runs. Queued deployments can be cancelled; a deployment already in progress cannot.
