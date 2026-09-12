# CLI command map

Verified: observed against @dokploy/cli 0.30.6 on 2026-09-09.

Contents:
- [The mapping rule](#the-mapping-rule)
- [Two ways deriving it fails](#two-ways-deriving-it-fails)
- [Where the published docs are stale](#where-the-published-docs-are-stale)
- [All resource groups observed](#all-resource-groups-observed)
- [Enterprise-gated groups](#enterprise-gated-groups)
- [Reading a resource's own help](#reading-a-resources-own-help)

## The mapping rule

Read the API method straight off `--help`; do not derive it. The `@dokploy/cli` package is
a generated client for Dokploy's API, and every subcommand's own `--help` description
already names the `/api/<resource>.<method>` call it makes, both halves camelCased.
Captured directly from `npx --yes @dokploy/cli@0.30.6 application --help`:

```
Usage: dokploy application [options] [command]

application commands

Commands:
  cancel-deployment [options]        application cancelDeployment
  ...
  deploy [options]                   application deploy
  ...
  read-logs [options]                application readLogs
  ...
```

`dokploy application deploy` is `/api/application.deploy`; `dokploy application read-logs`
is `/api/application.readLogs`; `dokploy application cancel-deployment` is
`/api/application.cancelDeployment`. Every one of `application`'s 32 actions checked
against this rule during verification held without exception — and that's the resource
where it's safe to notice the pattern (single-word resource, no acronyms). It isn't
elsewhere, in two independent ways below.

## Two ways deriving it fails

A hand-rolled kebab-to-camel transform gets `application`'s actions right and is wrong
elsewhere on the CLI, silently: the command still parses and `--help` still prints
something, so nothing catches the mistake until the live call, or a guard rule, is
compared against it.

**1. The resource segment camelCases too, not only the action.** Thirteen of the 57
resource groups have a multi-word kebab-case name, and every one of them camelCases on the
API side the same way an action would:

```
$ npx --yes @dokploy/cli@0.30.6 docker-volume --help
...
  delete-volume-file [options]  dockerVolume deleteVolumeFile
  remove-volume [options]       dockerVolume removeVolume
```

`docker-volume remove-volume` is `/api/dockerVolume.removeVolume`, never
`/api/docker-volume.removeVolume` — the camelCase form is what the `--help` method table
above shows, and it is the form the guard's `dockerVolume\.(removeVolume|deleteVolumeFile)`
rule in `dokploy-guard.sh` is written against. How a live server answers the kebab-case
spelling was never tested; nothing here ran against a running
instance. Affected: `audit-log`, `custom-role`, `dns-provider`, `docker-disk-usage`,
`docker-image`, `docker-volume`, `forward-auth`, `git-provider`, `license-key`,
`preview-deployment`, `ssh-key`, `vault-provider`, `volume-backups`.

**2. Acronyms don't capitalize the way a mechanical transform expects.** A hyphen-boundary
rule would produce `Sso`, `Sshkey`, `Gpustatus`; the CLI keeps each acronym upper-case as a
unit instead:

```
$ npx --yes @dokploy/cli@0.30.6 sso --help
...
  enforce-sso [options]              sso enforceSSO
  show-sign-in-with-sso [options]    sso showSignInWithSSO

$ npx --yes @dokploy/cli@0.30.6 settings --help
...
  check-gpustatus [options]          settings checkGPUStatus
  clean-sshprivate-key [options]     settings cleanSSHPrivateKey

$ npx --yes @dokploy/cli@0.30.6 server --help
...
  with-sshkey [options]              server withSSHKey
```

There's no third rule that covers both of these reliably. Read the method off `--help`;
don't derive it.

## Where the published docs are stale

The CLI section of docs.dokploy.com describes five command groups, and on 0.30.6 three of
its five resource names are wrong, not merely incomplete:

- The docs show `dokploy app create`, `dokploy app delete`, `dokploy app deploy`,
  `dokploy app stop`. Running `dokploy app --help` on 0.30.6 does not error — it silently
  falls through to the top-level help, because there is no `app` resource. The resource is
  `application`.
- The docs show `dokploy env pull <file>` and `dokploy env push <file>`. Running
  `dokploy env --help` on 0.30.6 falls through the same way. The resource is
  `environment`, and it has no `pull` or `push` action at all — its actions are
  `by-project-id`, `create`, `duplicate`, `one`, `remove`, `search`, and `update`.
- The docs show `dokploy database postgresql create`, `dokploy database mongodb create`,
  and so on for a combined `database` resource. Running `dokploy database --help` falls
  through the same way `app` and `env` do — there is no `database` resource. This one is
  wrong three ways at once: no `database` resource exists; `postgresql` and `mongodb` are
  `postgres` and `mongo` on the real CLI; and `delete` is `remove`. The six real resources
  are `postgres`, `mysql`, `mongo`, `mariadb`, `redis`, and `libsql`, each its own
  top-level group.

Of the two documented groups left, `auth` is named correctly. `project`'s own documented
commands (`create`, `info`, `list`) don't match 0.30.6 either: the resource has no `info`
or `list` action; the equivalents are `one` and `all`.

None of this is a criticism of trying to keep docs current against a CLI this size — it's
the reason to check `--help` on the version actually installed rather than carry any
enumeration, including this one, forward without re-checking it.

## All resource groups observed

`npx --yes @dokploy/cli@0.30.6 --help` lists 58 top-level commands: `auth` — the
authentication command itself, taking `-u`/`-t` flags rather than a further action — and
57 resource groups, each taking a kebab-case action per the mapping rule. That is "roughly
fifty," the figure the published docs' five-group section gives no hint of:

```
admin, ai, application, audit-log, backup, bitbucket, certificates, cluster, compose,
custom-role, deployment, destination, dns-provider, docker, docker-disk-usage,
docker-image, docker-volume, domain, environment, forward-auth, gitea, github, gitlab,
git-provider, libsql, license-key, mariadb, mongo, mounts, mysql, network, notification,
organization, overview, patch, port, postgres, preview-deployment, project, redirects,
redis, registry, rollback, schedule, scim, security, server, settings, ssh-key, sso,
stripe, swarm, tag, user, vault-provider, volume-backups, whitelabeling
```

A few worth knowing exist, since they answer questions the docs don't cover as CLI
surface: `rollback` (registry-based rollback to a specific deployment), `preview-deployment`
(pull-request preview deploys), `schedule` (the cron job feature), `forward-auth` (the
oauth2-proxy behind Application Authentication, which gates *deployed applications* behind
SSO rather than the panel — see `configuring-dokploy-enterprise`), `security` (panel-level
access controls), `docker-volume` (raw volume file read/write, not just database backups),
and `vault-provider` (external secrets providers).

## Enterprise-gated groups

Six resource groups exist on the CLI and were confirmed to respond to `--help` with a real
action list, but every action inside them requires a paid license (a self-hosted license
key or a Dokploy Cloud plan) to actually run — activating or configuring them, not merely
discovering them, is `configuring-dokploy-enterprise`'s job:

| Group | Actions observed | Covers |
|---|---|---|
| `sso` | `add-trusted-origin`, `delete-provider`, `enforce-sso`, `get-trusted-origins`, `list-providers`, `one`, `register`, `remove-trusted-origin`, `show-sign-in-with-sso`, `update`, `update-trusted-origin` | OIDC/SAML identity providers |
| `scim` | `delete-provider`, `generate-token`, `list-providers` | SCIM provisioning |
| `custom-role` | `all`, `create`, `get-statements`, `members-by-role`, `remove`, `update` | Roles beyond Owner/Admin/Member |
| `license-key` | `activate`, `deactivate`, `get-enterprise-settings`, `have-valid-license-key`, `update-enterprise-settings`, `validate` | Self-hosted license activation |
| `audit-log` | `all` | Organization audit trail |
| `whitelabeling` | `get`, `get-public`, `reset`, `update` | Rebranding the panel |

Existence of these groups is what this file verifies. Their behavior — what a valid
license unlocks, what each SSO provider's setup requires — is documentation-derived and
covered in `configuring-dokploy-enterprise`, not here; this plugin has no license to run
them against a live instance.

## Reading a resource's own help

`dokploy <resource> --help` is the discovery step this whole file is a snapshot of.
Running it against any resource not listed above, or against this same list on a later
CLI version, is the way to confirm an action name before scripting it — not this
reference, once the installed version has moved past 0.30.6.
