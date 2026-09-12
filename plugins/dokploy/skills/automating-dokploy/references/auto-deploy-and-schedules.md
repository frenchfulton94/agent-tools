# Auto-deploy webhooks and scheduled jobs

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [What Auto Deploy applies to](#what-auto-deploy-applies-to)
- [Setting up a webhook](#setting-up-a-webhook)
- [GitHub is the exception](#github-is-the-exception)
- [A contradiction in the docs for GitLab, Bitbucket, and Gitea](#a-contradiction-in-the-docs-for-gitlab-bitbucket-and-gitea)
- [DockerHub: Applications only, and the tag must match](#dockerhub-applications-only-and-the-tag-must-match)
- [Branch Not Match](#branch-not-match)
- [Deploying via API instead of a webhook](#deploying-via-api-instead-of-a-webhook)
- [Scheduled jobs](#scheduled-jobs)

## What Auto Deploy applies to

Auto Deploy is valid for **Applications** and **Docker Compose** services only. It is not
a feature of standalone databases.

## Setting up a webhook

1. Toggle **Auto Deploy** in the general tab of the application (or Compose service)
   settings.
2. Locate the **Webhook URL** in the deployment logs.
3. Add that URL to the source repository's webhook settings on the chosen provider —
   GitHub, GitLab, Bitbucket, Gitea, or DockerHub — and set it to trigger on push events.

Every deployment triggered this way is tracked with full build logs, the same as a manual
deploy.

## GitHub is the exception

Installing the Dokploy GitHub App and authorizing it gives automatic deploy-on-push with
no separate webhook step: the docs state that by default, using this connection method,
"you will have Automatic deployments on each push you make to your repository."

## A contradiction in the docs for GitLab, Bitbucket, and Gitea

Each of these three providers' own doc page carries a warning callout stating Dokploy
"doesn't support [GitLab/Bitbucket/Gitea] Automatic deployments on each push you make to
your repository" — and is immediately followed by a "Setup Automatic Deployments" section
that walks through registering a push-triggered webhook, plus a "Clarification on
Automatic Deployments" section describing exactly how that automatic behavior works
(branch-scoped, per application). The two statements contradict each other, and the
corpus does not resolve which is authoritative.

Treat the walkthrough as the operative instruction: it is followed by a working procedure
and a description of resulting behavior, while the warning callout is not followed by
anything that supports it. In practice, this means GitLab, Bitbucket, and Gitea reach
auto-deploy the same way — a manually registered webhook — while GitHub's App connection
does it without one.

## DockerHub: Applications only, and the tag must match

DockerHub auto-deploy is available for Applications only, not Compose services. Setup:

1. Go to the application's **Deployments** tab and copy the **Webhook URL**.
2. In the DockerHub repository, open the **Webhooks** tab, name the webhook, and paste the
   URL.
3. Every push to that DockerHub repository now triggers a deployment in Dokploy — but only
   if the pushed **Tag** matches the tag configured in Dokploy.

## Branch Not Match

For every Git-based provider, the branch configured on the Dokploy application must equal
the branch actually pushed to. A mismatch does not fail silently — the docs name the
specific error: **"Branch Not Match."** This is the single most direct explanation for "my
webhook fires but nothing deploys": the webhook delivery succeeded, and Dokploy rejected
the push because the branch didn't match, not because the webhook itself is broken.

One repository can back multiple Dokploy applications — for example development, staging,
and production — each pointed at its own branch, each triggering independently on a push
to that branch.

## Deploying via API instead of a webhook

A webhook is provider-initiated; the alternative is to trigger a deploy from your own
script or CI job, covered in `references/api-recipes.md` and the SKILL body's CI recipe:
`project.all` (or `dokploy project all`) to find the `applicationId`, then
`application.deploy` (or `dokploy application deploy`) with it. This is the same
`application.deploy` action a webhook calls internally — the difference is what triggers
it, not what it does.

## Scheduled jobs

Schedule Jobs run automated tasks on a cron expression; each run writes a log entry with
output and status. Four job types:

| Type | Runs where | Mechanism |
|---|---|---|
| **Application** | Inside the application's own container | `docker exec -it <container_id> <command>` |
| **Compose** | Inside a service in the Compose stack | Same `docker exec` mechanism, targeting a service container |
| **Server** | Directly on a remote server's host | A bash script with access to anything installed on that host |
| **Dokploy Server** | Inside the Dokploy container itself | A bash script with access to the Docker socket (`docker ps`, `docker image prune`, `docker system prune`). The docs state only that these jobs "do not execute directly on the host system" — not what filesystem access, if any, the container has beyond the socket |

The target container must be running for an Application or Compose job to execute.

Two examples straight from the docs:

```bash
#!/bin/bash
docker system prune --force
```

Scheduled every 15 minutes (`*/15 * * * *`), this is a Dokploy Server job that cleans up
unused Docker resources from inside the Dokploy container.

```bash
#!/bin/bash
backup_date=$(date +%Y%m%d_%H%M%S)
backup_file="database_${backup_date}.backup"
container_name=$(docker ps --filter "name=clickhouse" --format "{{.Names}}")
docker exec -it $container_name clickhouse-client --query "BACKUP DATABASE mydb TO '/backups/$backup_file'"
```

A Dokploy Server job backing up a database engine Dokploy doesn't natively support (here,
ClickHouse) by shelling into its container.

**Caveat for Compose jobs:** don't change the `COMPOSE_PROJECT_NAME` environment variable
on a service a scheduled job targets — Dokploy uses it to identify which project the job's
container belongs to.

Best practices the docs state directly: test a command or script manually before
scheduling it, handle errors inside the script rather than assuming the job will retry,
and account for the resource impact of whatever runs on a schedule.
