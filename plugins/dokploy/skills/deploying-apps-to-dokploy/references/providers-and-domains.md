# Providers, domains, and secrets

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [Source providers](#source-providers)
- [Git app setup, per provider](#git-app-setup-per-provider)
- [Docker registries](#docker-registries)
- [Domain fields](#domain-fields)
- [Certificates](#certificates)
- [Path rewriting](#path-rewriting)
- [Environment variables](#environment-variables)
- [Vault-backed secrets](#vault-backed-secrets)

## Source providers

Eight sources, three of which are restricted:

| Source | Available on |
|---|---|
| GitHub, GitLab, Bitbucket, Gitea | Applications and Docker Compose |
| Git (any provider, by URL) | Applications and Docker Compose |
| Docker (an image from a registry) | Applications only |
| Drag-and-drop `.zip` | Applications only |
| Raw (a compose file typed into the editor) | Docker Compose only |

For a plain **Git** source, a public repository needs only the `HTTPS URL` and a branch
name. A private one needs an SSH key: generate an RSA key in the SSH Keys section, add
the public key to the provider account, and use the SSH URL — `git@github.com:user/repo.git`,
not the HTTPS URL. The docs call that out explicitly.

Only GitHub's integration deploys on push with no further setup. GitLab, Bitbucket,
and Gitea each carry a documented warning that Dokploy does not deploy on push by
itself — and, immediately after it, the steps that make it work: copy the service's
`Webhook URL` from its Deployments tab, add it as a repository webhook, and select push
events. So the provider connection is what lets Dokploy read the repository, and for
those three the webhook is what triggers the deploy. Automatic deployment is available
on all four; only GitHub's needs no configuring.

GitHub is also the only provider with preview deployments, and the only one whose watch
paths work without auto-deploy being set up first.

## Git app setup, per provider

- **GitHub** — create a GitHub App from the panel with a unique name, install it, and
  choose all repositories or specific ones. Automatic deployment on push is on by
  default with this method. Deployment follows the branch selected on the application:
  a push to any other branch deploys nothing. Three applications on one repository with
  three different branches is the documented way to run development, staging, and
  production.
- **GitLab** — an OAuth application at `/-/profile/applications` with the `api`,
  `read_user`, and `read_repository` scopes. Paste its `Application ID` and `Secret`
  into Dokploy along with the panel's `Redirect URI`. `Group Name` is optional and
  accepts nested groups, for example `dokploy-panel/frontend`.
- **Bitbucket** — an app password with `Account: Read`, `Workspace membership: Read`,
  `Projects: Read`, `Repositories: Read`, `Pull requests: Read`, and
  `Webhooks: Read and write`. Supply the Bitbucket username with it. `Workspace` is
  optional.
- **Gitea** — an OAuth2 application on the Gitea instance, marked as a confidential
  client, with the panel's `Redirect URI`. Paste the `Client ID` and `Client Secret`
  into Dokploy's `Application ID` and `Personal Secret` fields. `Organization Name` is
  optional.

## Docker registries

Two ways to authenticate an image pull.

Per application, on the **General** tab with `Docker` selected as the source:

| Setting | Value |
|---|---|
| **Docker Image** | The full image name, for example `nginx:latest` or `myorg/myapp:v1.0` |
| **Docker Registry URL** | The registry URL; defaults to Docker Hub when empty |
| **Docker Registry Username** | The registry username |
| **Docker Registry Password** | A password or, better, an access token |

Public images need no username or password.

Or once, organization-wide, in the Registry section — `Registry Name`, `Username`,
`Password`, an optional `Image Prefix` (which turns `my-app:latest` into
`dokploy/my-app:latest`, for the cluster feature), and `Registry URL` such as
`https://index.docker.io/v1`. Credentials stored there are reused by every application
and by remote servers, which is the reason to prefer it over per-application fields.

A configured registry is also a prerequisite for two features covered in
`release-lifecycle.md`: registry-based rollbacks, and building on a separate build
server.

## Domain fields

Seven fields on a domain:

| Field | Meaning |
|---|---|
| **Host** | The domain name, for example `api.dokploy.com` |
| **Path** | The path under the domain where the application answers |
| **Internal Path** | The path the application itself expects to receive |
| **Strip Path** | Removes **Path** from the request before forwarding |
| **Container Port** | The port inside the container that Traefik routes to |
| **HTTPS** | Enables HTTPS for the domain |
| **Certificate** | `letsencrypt` or `None` |

**`Container Port` exposes nothing.** It exists so Traefik can direct traffic to the
right port inside the container. It is a different mechanism from `Ports` under
Advanced Settings, which publishes a host port for `IP:port` access and interferes with
domain routing.

Two ways to get a Host:

- **Generated** — the dice icon next to `Host` produces a free `traefik.me` domain. Set
  `Path` to `/`, set `Container Port` to the port the app listens on, leave HTTPS off
  and `Certificate` as `None`. Good for development and testing, and no DNS work.
- **Custom** — add an `A` record at the DNS provider pointing the host at the server's
  IPv4 address, *then* add the domain in Dokploy with HTTPS on and `Certificate` set to
  `Let's Encrypt`. Adding the domain before the record exists is what breaks issuance.

For `www`, add a `CNAME` from `www` to the apex, create the domain in Dokploy with the
`www` host, and use the www-to-non-www redirect preset under Advanced → Redirects.

A Static build, or a Nixpacks build with a `Publish Directory`, needs `Container Port`
`80`, because NGINX serves the result.

## Certificates

`traefik.me` domains are HTTP only. To put HTTPS on one, download
`https://traefik.me/fullchain.pem` and `https://traefik.me/privkey.pem`, paste them into
a certificate's `Certificate Data` and `Private Key` fields, enable the domain's HTTPS
toggle, and leave the certificate provider as `None`. Those files are valid for 30 days,
so this is a development convenience and not a production certificate.

The certificate form takes a `Name`, `Certificate Data`, a `Private Key`, and optionally
a `Server`. Creating one writes the files; Traefik still has to be configured to use it.

## Path rewriting

`Internal Path` and `Strip Path` are Traefik middlewares. When both are set, Strip Path
runs first and Internal Path is applied to the result:

- Host `service.dokploy.com`, `Path` `/public`, Strip Path enabled, `Internal Path`
  `/app/v2`. A request for `/public/api/users` reaches the container as
  `/app/v2/api/users`.

An application that generates absolute URLs or redirects has to agree with whatever
rewriting is configured, or the result is a redirect loop.

## Environment variables

Variables can be declared at three levels, and are referenced across them:

- **Project-level (shared)** — available to every service in the project. Reference with
  `${{project.DATABASE_URL}}`.
- **Environment-level** — scoped to one environment, and overrides the project value.
  Reference with `${{environment.DATABASE_PASSWORD}}`.
- **Service-level** — scoped to one service, and overrides both. Reference another of
  the same service's variables with `${{DATABASE_USER}}`.

A multiline value is wrapped in double quotes inside single quotes:
`'"here_is_my_private_key"'`.

Preview deployment environments get one extra service-level variable,
`DOKPLOY_DEPLOY_URL`, holding that deployment's URL — usable as
`APP_URL=https://${{DOKPLOY_DEPLOY_URL}}`.

Compose services treat this tab differently: the values are written to a `.env` file
next to the compose file and are *not* injected into containers automatically. See
`compose-services.md`.

## Vault-backed secrets

Available from Dokploy v0.30.0. A Secrets Provider connects Dokploy to an external
secret manager, and environment variables then hold a reference rather than a value:

```
${{vault.<provider-name>.<ref>}}
```

`<provider-name>` is the name given to the provider when it was created. It is unique
per organization and may contain only letters, numbers, dashes, and underscores.
`<ref>` is provider-specific:

| Provider | Ref format | Example |
|---|---|---|
| HashiCorp Vault / OpenBao | `<path>:<field>` | `myapp/prod:DB_PASSWORD` |
| Infisical | `<SECRET_NAME>` | `DB_PASSWORD` |
| AWS Secrets Manager | `<secret-name>` or `<secret-name>:<field>` | `prod/myapp:password` |
| Doppler | `<SECRET_NAME>` | `DB_PASSWORD` |
| Azure Key Vault | `<secret-name>` | `db-password` |
| Scaleway Secret Manager | `[folder/]<secret-name>[:field]` | `prod/database:password` |

So a database password becomes:

```
DB_PASSWORD=${{vault.prod-vault.myapp/prod:DB_PASSWORD}}
```

Three properties make this the right default for anything sensitive:

- Values are fetched **at deploy time** and never stored in Dokploy's database. The
  vault stays the single source of truth, and what a panel member sees in the editor is
  the reference, not the secret.
- References work everywhere that feeds a deployment: service variables on
  applications, Compose services, and databases; project-level and environment-level
  shared variables; and build-time arguments and build secrets.
- They resolve **before** `${{project.X}}` and `${{environment.X}}` interpolation, so a
  shared variable can hold the vault reference and services can consume it through the
  ordinary project or environment syntax.

Which providers to enable, and how to scope their access, belongs to
`hardening-dokploy`.
