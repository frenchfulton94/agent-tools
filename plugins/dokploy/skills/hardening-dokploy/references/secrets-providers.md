# Secrets providers

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [What a Secrets Provider does](#what-a-secrets-provider-does)
- [AWS Secrets Manager](#aws-secrets-manager)
- [Azure Key Vault](#azure-key-vault)
- [Doppler](#doppler)
- [HashiCorp Vault / OpenBao](#hashicorp-vault--openbao)
- [Infisical](#infisical)
- [Scaleway Secret Manager](#scaleway-secret-manager)
- [Access control](#access-control)
- [Security model](#security-model)

## What a Secrets Provider does

Available from Dokploy v0.30.0. A Secrets Provider connects Dokploy to an external
secret manager; values are fetched at deploy time and injected into the prepared
environment, never stored in the Dokploy database. What a member sees in the
environment editor is the reference — `${{vault.<provider-name>.<ref>}}` — not the
value.

Writing that reference into an environment editor, and how it interleaves with
`${{project.X}}` and `${{environment.X}}` interpolation, is
`deploying-apps-to-dokploy`'s territory (`references/providers-and-domains.md`). This
file covers the other half: standing a provider up, scoping its credentials, deciding
who can use it, and each provider's own reference format.

Six providers are supported, each with its own authentication model and its own
`<ref>` shape.

## AWS Secrets Manager

Dokploy authenticates with IAM credentials. Create a least-privilege policy scoped to
the secrets it should reach:

```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": ["secretsmanager:GetSecretValue", "secretsmanager:ListSecrets"],
			"Resource": "arn:aws:secretsmanager:*:*:secret:dokploy/*"
		}
	]
}
```

`ListSecrets` only powers the autocomplete; the provider still resolves references
without it.

**Configuration** (Settings → Secrets → Add Provider → AWS Secrets Manager): Name (the
identifier used in references, e.g. `aws-sm`), Region, Access Key ID / Secret Access
Key, and an optional Endpoint for VPC endpoints or API-compatible emulators (e.g.
LocalStack).

**Reference format** — the secret name, not the ARN:

```bash
API_TOKEN=${{vault.aws-sm.api-token}}

DB_PASSWORD=${{vault.aws-sm.prod/database:password}}
DB_HOST=${{vault.aws-sm.prod/database:host}}
```

Append `:<field>` to extract one key from a JSON secret; without it, the whole
`SecretString` is injected as-is. Binary secrets are not supported — only
`SecretString` values.

## Azure Key Vault

Dokploy authenticates as an **App Registration** (service principal) using the OAuth2
client credentials flow: register an app with no redirect URI needed, copy the
Application (client) ID and the Directory (tenant) ID, then create a client secret
under Certificates & secrets and copy its value immediately — it is shown once.

Grant access on the vault: the **RBAC permission model** (recommended) assigns the
**Key Vault Secrets User** role to the app; the **access policies model** grants `Get`
and `List` on secrets instead. RBAC role assignments can take a few minutes to
propagate — if Test Connection fails right after assigning the role, wait and retry.

**Configuration**: Name (e.g. `azure-kv`), Vault URI (e.g.
`https://my-vault.vault.azure.net`), Tenant ID, Client ID / Client Secret.

**Reference format** — flat secret names:

```bash
DB_PASSWORD=${{vault.azure-kv.db-password}}
STRIPE_KEY=${{vault.azure-kv.stripe-key}}
```

Azure secret names allow only letters, digits, and dashes — no underscores — so name
secrets `db-password`, not `DB_PASSWORD`.

## Doppler

The recommended token type is a **Service Token** (`dp.st.`): read-only and scoped to a
single project + config, so a leaked token only exposes that config. Generate one from
the project's config → Access tab. Personal (`dp.pt.`) and CLI (`dp.ct.`) tokens also
work, but since they aren't bound to a config, the provider form also needs the Project
and Config fields.

**Configuration**: Name (e.g. `doppler-prd`), Token, and Project/Config (only required
for personal/CLI tokens). A provider points at a single Doppler config — create one
provider per config (`doppler-dev`, `doppler-prd`) and assign each to the matching
Dokploy environments.

**Reference format** — flat secret names, autocompleted from the real secrets in the
configured config:

```bash
DATABASE_URL=${{vault.doppler-prd.DATABASE_URL}}
STRIPE_KEY=${{vault.doppler-prd.STRIPE_KEY}}
```

## HashiCorp Vault / OpenBao

Dokploy talks to the KV version 2 secrets engine. The same provider works for
**HashiCorp Vault** and **OpenBao** — their APIs are identical.

**Configuration**: Name (e.g. `prod-vault`), Vault URL (must be reachable from the
Dokploy server, e.g. `https://vault.example.com:8200`), a Token with `read` (and
`list`, for autocomplete) capabilities, KV Mount (defaults to `secret`), and an
optional Namespace for Vault Enterprise or OpenBao namespaces (e.g. `admin`).

Scope the token's policy to only what Dokploy needs, for example:

```hcl
path "secret/data/myapp/*" {
  capabilities = ["read"]
}
path "secret/metadata/*" {
  capabilities = ["list"]
}
```

**Reference format** — path and field, separated by a colon:

```bash
DB_PASSWORD=${{vault.prod-vault.myapp/prod:DB_PASSWORD}}
API_KEY=${{vault.prod-vault.shared:API_KEY}}
```

`myapp/prod` is the path inside the KV mount; `DB_PASSWORD` is the field inside that
secret.

For a quick local test, OpenBao's dev mode gives a ready-to-use server:

```bash
docker run -d --name openbao -p 8200:8200 \
  -e BAO_DEV_ROOT_TOKEN_ID=dev-token \
  -e BAO_DEV_LISTEN_ADDRESS=0.0.0.0:8200 \
  openbao/openbao:latest
```

Then create the provider with URL `http://<your-host>:8200`, token `dev-token`, and
mount `secret`. Dev mode stores everything in memory and is for testing only — never
point a real environment's secrets at it.

## Infisical

Dokploy authenticates with a **Machine Identity** using Universal Auth, the method
Infisical recommends for programmatic access. Both Infisical Cloud and self-hosted
instances are supported. Create the identity under Organization → Access Control →
Identities, add the Universal Auth method with a Client Secret, and add the identity to
the target project with a role that can read secrets.

**Configuration**: Name (e.g. `infisical-prod`), Site URL (`https://app.infisical.com`
for Cloud, or the self-hosted URL), Client ID / Client Secret, Project ID, Environment
(the Infisical environment slug, e.g. `dev`, `staging`, `prod`), and Secret Path
(defaults to `/`). A provider points at a single project + environment — create one
provider per Infisical environment and assign each to the matching Dokploy environments.

**Reference format** — flat secret names:

```bash
DB_PASSWORD=${{vault.infisical-prod.DB_PASSWORD}}
STRIPE_KEY=${{vault.infisical-prod.STRIPE_KEY}}
```

Infisical is also available as a Dokploy template, so it's possible to run Infisical
itself on Dokploy and point this provider at it.

## Scaleway Secret Manager

Dokploy authenticates with a Scaleway **API key** scoped to the project holding the
secrets, with a permission set including **SecretManagerReadOnly** (or equivalent read
access). The Secret Key is the sole credential — Dokploy sends it as the `X-Auth-Token`
header, and like other Scaleway API keys it is shown once.

**Configuration**: Name (e.g. `scaleway-sm`), Region (`fr-par`, `nl-ams`, or `pl-waw`),
Project ID, Secret Key, and an optional API URL (defaults to
`https://api.scaleway.com`; override only for API-compatible proxies or emulators).

**Reference format** — secret name, optionally folder-prefixed, optionally
field-suffixed:

```bash
API_TOKEN=${{vault.scaleway-sm.api-token}}

DB_PASSWORD=${{vault.scaleway-sm.prod/database:password}}
DB_HOST=${{vault.scaleway-sm.prod/database:host}}
```

Only the **latest enabled version** of a secret is read.

## Access control

Two independent layers gate every provider, regardless of which of the six it is.

**Project and environment assignment.** Each provider carries an assignment list of
where it may be used:

- A project selected with **no environments** enables the provider in all of that
  project's environments, including ones created later.
- Specific environments selected enable it only there.
- No assignments at all means the provider is enabled nowhere until assigned.

Enforcement happens on the server before any request reaches the vault: a reference to
a provider not enabled for the deploying project/environment fails the deployment with
a clear error, and the autocomplete in the environment editor only offers providers
enabled for that editor.

Project-level shared variables are evaluated by every environment in the project — a
project-level variable that references an environment-restricted provider breaks
deployment in the other environments. Put references to a restricted provider in
environment-level or service-level variables instead.

**Role permissions**, under the `vaultProvider` permission resource: Owners and Admins
can create, update, delete, and test providers. Members can read provider names and
secret names — this is what powers the autocomplete — but never see credentials or
secret values. On an Enterprise license, Custom Roles can grant `read`, `create`,
`update`, and `delete` on this resource individually.

## Security model

- Values never touch the Dokploy database or the UI. A member with access to a service
  sees the reference in the editor, not the value.
- Rotation requires a redeploy, since values are fetched at deploy time — rotating a
  secret in the vault takes effect on the next deployment, not immediately.
- Use least-privilege credentials on the vault side. Whoever can edit environment
  variables and deploy in an assigned project can read whatever the provider's
  credential reaches there — the same trust model as any CI/CD system holding a secret.
  Scope the credential per environment where the provider supports it (Doppler service
  tokens, Vault policies, Infisical machine identities).
- A deleted or missing secret fails the deployment with an explicit error instead of
  silently injecting an empty value.
