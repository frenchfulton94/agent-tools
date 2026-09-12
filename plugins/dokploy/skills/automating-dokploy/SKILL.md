---
name: automating-dokploy
description: Scripts a Dokploy instance from its CLI and REST API — the mapping that turns `dokploy application deploy` into `/api/application.deploy` and reaches the whole surface the published documentation only partly describes, authenticating with `dokploy auth` or an `x-api-key` header, discovering resources and actions from `--help` and Swagger, deploy recipes for CI pipelines, git and DockerHub auto-deploy webhooks, and scheduled jobs. Use when the user wants to deploy Dokploy from a pipeline, automate it in a script, call its API, set up a deploy webhook, or find the command for something the documentation does not list — including webhook failures reporting "Branch Not Match". For deciding what a setting should be rather than how to set it, use deploying-apps-to-dokploy or operating-dokploy-servers.
license: MIT
---

# Automating Dokploy

Drive a self-hosted Dokploy instance from a script, a CI pipeline, or a `curl` command
instead of the panel: the CLI, the REST API underneath it, discovering the surface the
published documentation doesn't mention, git and DockerHub auto-deploy webhooks, and
cron-based scheduled jobs.

For deciding *what* a build type, domain, or server setting should be, use
`deploying-apps-to-dokploy` or `operating-dokploy-servers` — this skill owns the mechanism
that applies a decision already made, not the decision itself.

## The mapping rule

The published CLI documentation describes five command groups — Application,
Authentication, Databases, Environment, Project — and never states how the CLI relates to
the API. It does, exactly: **every subcommand's own `--help` line already names the
`/api/<resource>.<method>` call it makes, both halves camelCased. Read it there — don't
derive it by hand.** A hand-rolled kebab-to-camel transform is wrong often enough, in two
independent ways, that relying on it costs more than just running `--help`.

**The resource segment camelCases too, not only the action**, for 13 of the 57 resource
groups:

```
$ npx --yes @dokploy/cli@0.30.6 docker-volume --help
...
  remove-volume [options]       dockerVolume removeVolume
```

`docker-volume remove-volume` is `/api/dockerVolume.removeVolume`, never
`/api/docker-volume.removeVolume` — the camelCase form is what the `--help` method table
shows, and the form the guard's `dockerVolume\.(removeVolume|deleteVolumeFile)` rule matches.
Nothing here ran against a live instance, so the kebab-case form is simply untested.
The rest: `audit-log`, `custom-role`, `dns-provider`, `docker-disk-usage`, `docker-image`,
`forward-auth`, `git-provider`, `license-key`, `preview-deployment`, `ssh-key`,
`vault-provider`, `volume-backups`.

**Acronyms don't capitalize the way a mechanical transform expects.** A hyphen-boundary
rule produces `Sso`, `Sshkey`, `Gpustatus`; the CLI keeps each acronym upper-case as a unit
instead:

```
$ npx --yes @dokploy/cli@0.30.6 sso --help
...
  enforce-sso [options]         sso enforceSSO

$ npx --yes @dokploy/cli@0.30.6 settings --help
...
  check-gpustatus [options]     settings checkGPUStatus
```

Both failures are silent at the CLI — it still parses, `--help` still prints something —
and only surface at the live call, or in a guard rule written against the wrong form.
There's no third rule that covers this. Read the method off `--help`; don't derive it.
Checked against all 32 of `application`'s own actions, none of which hit either problem,
the naive transform does hold — which is exactly why it's tempting, and exactly why it's
the wrong instruction to teach.

The published docs are wrong about resource names on this version in at least three
places, worked through with the exact commands run in `references/cli-command-map.md`.
Two here: they show `dokploy app create`, but 0.30.6 has no `app` resource
(`dokploy app --help` falls through to the top-level help; the real resource is
`application`, 32 actions total including `create`, `delete`, `deploy`, `redeploy`,
`stop`). They show `dokploy env pull <file>`, but the resource is `environment`, with no
`pull` or `push` action at all — its actions are `by-project-id`, `create`, `duplicate`,
`one`, `remove`, `search`, `update`. Don't carry the docs' CLI names into a script; confirm
them the way described next.

## Discover the surface yourself, don't enumerate it

Running `dokploy --help` against 0.30.6 lists 58 top-level commands: `auth` plus 57
resource groups — the whole automatable surface, not the five the docs describe. Notably
it includes `sso`, `scim`, `custom-role`, `license-key`, `audit-log`, `rollback`,
`preview-deployment`, `schedule`, `security`, `forward-auth`, `vault-provider`, and
`whitelabeling`; the full list, and which groups are enterprise-gated, is in
`references/cli-command-map.md`.

Two commands answer almost anything this skill would otherwise need to enumerate:
`dokploy --help` for every resource group, `dokploy <resource> --help` for every action on
it. Swagger at `<host>:3000/swagger` documents request shapes and is admin-only by
default, though an Owner or Admin can grant a Member the `Access to API/CLI` permission to
reach it too. Because the CLI is generated from the API, this discovery path degrades
gracefully if a future release adds, renames, or removes resources — rerun `--help` rather
than trust an enumeration written against 0.30.6.

## Authenticate

CLI:

```bash
dokploy auth -u <url> -t <token>
dokploy user session
```

`dokploy user session` reads the config `auth` just stored and confirms it's live — a real
check, unlike the docs' `dokploy verify`, which doesn't exist on 0.30.6: it's absent from
the 58-command `--help` list, and running it errors `too many arguments. Expected 0
arguments but got 1` rather than doing anything.

API: send the same token as an `x-api-key` header. Mint the token at
`/settings/profile`, in its API/CLI section; by default only an Owner or Admin can
generate one or reach Swagger, though that access can be granted to a Member. An access
token never expires unless you set an expiration when creating it — do, for any token a
script or CI job will hold.

**Use the installed `dokploy` binary, not `npx`, for anything state-changing.** This
plugin's guard hook (`${CLAUDE_PLUGIN_ROOT}/scripts/dokploy-guard.sh`) matches a Bash command against
`dokploy` followed by whitespace. `npx --yes @dokploy/cli@0.30.6 project remove --projectId x`
starts with `npx`, not `dokploy`, so it reaches a live host with none of the checks in
the next section applied. Install the binary once and call it directly:

```bash
npm install -g @dokploy/cli
dokploy application deploy --applicationId <id>
```

`npx` is fine for one-off `--help` inspection, where nothing changes state — that's how
this skill's own mapping rule and resource list were checked. Don't reach for it to run an
actual action.

## The documented CI recipe

Two calls: `project.all` (`dokploy project all`) to find the target `applicationId`, then
`application.deploy` (`dokploy application deploy --applicationId <id>`) to trigger the
build. `references/api-recipes.md` carries the docs' own worked `curl` example, a GitHub
Actions workflow that calls it, and what the docs do and don't say about response shape,
pagination, and token scoping.

## What the guard denies and asks — a script cannot get past this alone

`${CLAUDE_PLUGIN_ROOT}/scripts/dokploy-guard.sh` inspects every Bash command this plugin sees, on the CLI or the
equivalent `curl` against `/api/<resource>.<action>`, and decides one of three ways. Read
straight from the script, current as of this skill's writing:

| Decision | Commands |
|---|---|
| **Deny** | `dokploy project remove`; `dokploy {postgres,mysql,mongo,mariadb,redis,libsql} remove`; `dokploy docker-volume remove-volume`; `dokploy docker-volume delete-volume-file` |
| **Ask** | `dokploy application delete`; `dokploy backup remove`; `dokploy server remove`; `dokploy {postgres,mysql,mongo,mariadb,redis,libsql} change-password`; `install.sh ... -s update` |
| **Allow** | Everything else, including every read, `clear-deployments`, `drop-deployment`, `cancel-deployment`, and `kill-build` |

A denied command is blocked outright; an asked one stops for a human decision. Neither is
something a non-interactive script or CI job can resolve alone — **a pipeline that needs
to remove a project or database, delete an application, remove a backup, detach a server,
rotate a database password, or run `install.sh ... update` has to be run by a human**.
Build a pipeline around the allowed surface (deploy, redeploy, read-logs, and the rest) and
leave the denied and asked actions to someone at a terminal.

The guard's only exemption is a bare, whole-command `dokploy <resource> [<action>] --help`
or `-h` — the anchored `^[[:blank:]]*dokploy…` whitelist in `dokploy-guard.sh` — the action
is optional, so `dokploy project --help` is exempt too, but nothing else may be on the
line. `dokploy project remove --help` is allowed; the same string wrapped in `sh -c`,
chained with `&&`, or followed by anything else is evaluated like any other command.

## Webhooks: trigger a deploy from your git provider

Auto Deploy applies to **Applications and Docker Compose services only** — not databases,
not Templates deployed as anything else. To wire one up:

1. Toggle **Auto Deploy** in the application's general settings.
2. Copy the **Webhook URL** from the deployment logs.
3. Register that URL with the provider: GitHub, GitLab, Bitbucket, Gitea, or — for
   Applications only — DockerHub.

GitHub is the one provider that needs no webhook step at all: installing the Dokploy
GitHub App gives automatic deploy-on-push by default. The docs state, for GitLab,
Bitbucket, and Gitea, that Dokploy "doesn't support ... [a]utomatic deployments on each
push" and then, in the very next section, walk through registering exactly that as a
webhook — a contradiction in the source, not a call this skill is resolving one way
silently. Treat the walkthrough as the accurate instruction, since it's followed by working
steps and a "Clarification on Automatic Deployments" section describing the resulting
behavior, while the warning callout is not.

**Branch Not Match** is the one trap named directly: the branch pushed to must equal the
branch configured on the Dokploy application exactly, or the webhook fires and the deploy
is rejected with that message. For DockerHub, the equivalent is the image tag — it must
match what's configured, or nothing deploys.

Dokploy also runs cron-scheduled jobs against an application, a Compose service, a remote
server, or the Dokploy container itself — a separate automation path from a deploy
webhook, covered with the per-provider webhook setup in
`references/auto-deploy-and-schedules.md`.

## Verify before reporting an automation task done

- [ ] A state-changing command actually ran as `dokploy <resource> <action>`, not `npx @dokploy/cli ...`
- [ ] The action name came from `dokploy <resource> --help` on the target version, not memory
- [ ] A deny or ask guard decision was handed to a human, not retried or routed around
- [ ] A webhook's configured branch (or DockerHub tag) matches what's pushed; any script or CI token has an expiration

## Where the rest lives

- `references/cli-command-map.md` — the roughly fifty resource groups observed on
  `@dokploy/cli` 0.30.6, the two ways deriving the mapping fails, which groups are
  enterprise-gated, and where the published docs are stale beyond `app` and `env`.
- `references/api-recipes.md` — authenticated `curl` examples, a GitHub Actions workflow,
  what the docs do and do not show about response shape and pagination, and token scoping.
- `references/auto-deploy-and-schedules.md` — webhook setup per git provider, the
  DockerHub tag-match limit, and the four scheduled-job types with examples.
