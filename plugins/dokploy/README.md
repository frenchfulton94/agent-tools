# Dokploy

A Claude Code plugin for a self-hosted [Dokploy](https://dokploy.com) instance — the
open-source Heroku/Vercel alternative. Covers deploying and releasing applications,
operating the host and its backups, scripting the full CLI and API surface (which the
published documentation covers only in part), hardening the panel and Traefik against a
compliance-mapped checklist, and configuring the licensed SSO/SCIM enterprise tier.

## Components

| Component | Shape | Covers |
|---|---|---|
| `dokploy-guard` | Hook | A `PreToolUse` guard on `Bash` that blocks irreversible project, database, and volume removal — on the CLI or the equivalent `curl` against the API — and asks before disruptive-but-recoverable operations such as an application delete, a backup removal, a server detach, a password rotation, or an in-place `install.sh ... update` of a live panel. Fails open: absent `jq`, or an empty/malformed payload, allows the command rather than erroring. See `plugins/dokploy/scripts/dokploy-guard.sh`. |
| `deploying-apps-to-dokploy` | Skill | Getting an app running and releasing it safely: the Organizations/Projects/Environments object model, build type, git or registry provider, domain and certificate, vault-backed environment variables, zero-downtime releases, preview deployments, rollbacks, watch paths, and patches. Leads with the routing asymmetry that produces most "my domain returns 404" reports: Applications pick up domain edits immediately, Compose services keep serving the old routing until redeployed. |
| `operating-dokploy-servers` | Skill | The host and panel, not the apps on it: install, update, and uninstall, remote and dedicated build servers, Swarm cluster and build-concurrency settings, monitoring and notification providers, panel and database backups with tested restores, and symptom-first troubleshooting of the panel, logs, networking, DNS pools, volumes, and mounts. Leads with the distinction the docs let people conflate: a panel backup (Web Server → Backups) archives the Dokploy installation itself, not the same feature as a per-database backup. |
| `automating-dokploy` | Skill | The CLI/API mechanism: reading the API method a CLI action calls straight off its own `--help` line (e.g. `dokploy application deploy` is `/api/application.deploy`) rather than deriving it — a mechanical kebab-to-camel transform is wrong for 13 of the 57 resource groups and every acronym-bearing action — to reach the roughly fifty resource groups the published CLI docs only partly describe. Also authenticating with `dokploy auth` or an `x-api-key` header, discovery via `--help` and Swagger, the CI deploy recipe, git and DockerHub auto-deploy webhooks (including the "Branch Not Match" trap), scheduled jobs, and which of the guard's denied and asked commands a script cannot get past without a human. |
| `hardening-dokploy` | Skill | Dokploy's own attack surface, grouped by the layer it defends: host SSH, Fail2Ban, and UFW with `ufw-docker` so Docker's own rules stop bypassing the firewall; the Docker daemon settings a Dokploy host specifically needs; panel 2FA, passkeys, least-privilege roles, and expiring per-integration API tokens; the six external secrets providers in place of raw environment variables; internal-only database credentials and restore-tested backups; Traefik HSTS and rate-limit middleware; and external log shipping with alerting. States the guide's own baseline caveat — this is a floor, not a finish line — and maps its 25-control checklist, by guide section rather than per control, to an illustrative SOC 2 Trust Services Criteria and ISO/IEC 27001:2022 Annex A mapping: a GRC starting point, not a certification. |
| `configuring-dokploy-enterprise` | Skill | The paid tier — nothing in it observable without a license: self-hosted license-key or Enterprise Cloud activation; SSO over OIDC or SAML, leading with Microsoft Entra ID and Okta ahead of Auth0, Keycloak, and Zitadel; SCIM provisioning and the automatic-deprovisioning guarantee it buys; custom roles built from over 25 permission categories; audit logs; whitelabeling (self-hosted only); and gating a deployed application behind SSO with oauth2-proxy and Traefik. States the free/paid boundary in both directions: 2FA, passkeys, the built-in roles, and their per-project/per-environment scoping stay `hardening-dokploy`'s; this skill owns only defining a new role or connecting a licensed identity integration. |

Each skill triggers on its own from a matching request — install the plugin and never
invoke a skill by name.

## Limits

- **Mentions are denied, not just invocations.** The guard matches command substrings, so
  `git commit -m "guard dokploy project remove"`, a `gh pr create --body` that describes the
  same command, a `git log --grep` for it, a heredoc quoting it, or a `sed -i` over this
  plugin's own documentation are all denied when their text contains a guarded command. Reword
  it, or run the command yourself. A `git`/`gh` exemption was considered and rejected:
  `git rebase -x "<cmd>"` executes an arbitrary command, so exempting `git` would reopen exactly
  the bypass class that took four rounds to close.
- **`npx` invocations are not guarded.** The decision table matches `dokploy` followed by
  whitespace, so `npx --yes @dokploy/cli@0.30.6 project remove --projectId x` passes straight
  through. Use the installed `dokploy` binary for anything state-changing.
- **A pre-written script is not guarded.** `bash cleanup.sh` and `bash -c "$(cat cleanup.sh)"`
  are both allowed regardless of what the script does, because the guard reads the Bash tool's
  command string, not the bytes of any file it runs. This is structurally invisible to any
  guard that matches command text rather than executing content.
- **Documentation-derived, not instance-verified, except the CLI's own resource and
  command names.** Every reference file carries a `Verified:` line naming its source and
  date. `automating-dokploy`'s `cli-command-map.md` is the one exception, checked directly
  against `@dokploy/cli` 0.30.6's own `--help` output; every other reference file, in every
  skill, is as documented rather than as observed, including API response shapes, panel
  field names, and all of `configuring-dokploy-enterprise`, which is gated behind a paid
  license this repository has no way to activate.
- **Generic Docker and container knowledge will not be duplicated here.** `docker-workbench`
  stays the authority for Dockerfiles, Compose authoring, container runtimes, and image
  supply chain; the skills above delegate to it by name rather than re-teach it.
- **Not an MCP server and not a subagent.** Dokploy ships no MCP server — the API is `curl`
  plus an `x-api-key` header, already wrapped by the CLI — and deployment-log diagnosis is
  read through the CLI directly rather than isolated into a subagent.
- **Deciding whether to adopt Dokploy, or its Cloud-hosted offering, is out of scope.** That
  decision is already made; this plugin covers operating a self-hosted instance.

## Prerequisites

None to load the plugin itself.

To act on what it covers:

- A reachable Dokploy instance — self-hosted, with panel access or an API token.
- **`@dokploy/cli`** — `npm install -g @dokploy/cli` — for `automating-dokploy`.
- **`jq`** — for the `dokploy-guard` hook. The guard fails open (allows the command) if
  `jq` is absent, so its protection is silently off without it.
- **A paid license** — a self-hosted license key or a Dokploy Enterprise Cloud plan
  specifically, not the base Cloud tier — for every `configuring-dokploy-enterprise`
  feature.

## Install

```bash
claude plugin install dokploy@manhattan-plugin-marketplace
```

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/dokploy
claude plugin validate plugins/dokploy --strict
```

## Sources

- Dokploy documentation index — <https://docs.dokploy.com/llms.txt>
- `@dokploy/cli` — observed against version 0.30.6

## License

Proprietary — internal Manhattan University use.
