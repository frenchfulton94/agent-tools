---
name: configuring-dokploy-enterprise
description: Configures Dokploy's paid enterprise tier — activating a self-hosted licence key, single sign-on over OIDC or SAML with Microsoft Entra ID, Okta, Keycloak, Auth0, or Zitadel, SCIM provisioning and automatic deprovisioning from an identity provider, custom roles beyond Owner/Admin/Member, audit logs, whitelabeling, and gating deployed applications behind SSO with oauth2-proxy and Traefik. Use when the user wants to connect Dokploy to their identity provider, provision or deprovision panel users automatically, define a custom role with permissions beyond Owner/Admin/Member, trace who changed what, or asks which Dokploy features require a licence. For free-tier access control — 2FA, passkeys, the built-in Owner/Admin/Member roles, and scoping one of those roles to particular projects or environments — use hardening-dokploy.
license: MIT
---

# Configuring Dokploy Enterprise

Every feature this skill covers needs more than the free self-hosted tier: unlocked
self-hosted by activating a license key, or on Dokploy Cloud through an Enterprise
Cloud plan specifically — the base Cloud plans don't include SSO, SCIM, audit logs,
whitelabeling, or Application Authentication. Custom roles are the one exception with
a real nuance rather than a flat no: the docs' own edition table marks them
"Plan-dependent" on plain (non-Enterprise) Cloud, not simply unavailable. None of this
has been observed against a running instance; this repository has no license to
exercise it. Everything below is drawn from docs.dokploy.com and marked as such, and no
field name, endpoint, or setup step appears here unless the docs actually show it.
Whitelabeling and air-gapped operation are both self-hosted-only, but for different
stated reasons: the docs give one for whitelabeling — Enterprise Cloud's control plane
is shared infrastructure — and give none for air-gapped, which is a plain ❌ in the
same table with no explanation attached. Don't borrow the first reason for the second.

## The free/paid boundary — read this before anything else

The sharpest way to get this wrong is answering a free-tier question with a paywall.

**Force 2FA for every panel user** is free-tier and has no Enterprise angle at all.
There is no organization-wide "require 2FA" toggle on any tier — 2FA and passkeys are
enrolled per user from Settings → Profile, so "force" here means a policy communicated
and audited, not a setting. That's `hardening-dokploy`'s content, not this skill's. The
one place licensing does enter 2FA's story is indirect: forcing **SSO** org-wide (an
Enterprise feature, below) removes the password fallback entirely, so whatever MFA the
identity provider requires becomes mandatory for everyone — but that's SSO enforcement,
not a 2FA toggle.

**Restrict a contractor to one project's staging environment** is also free-tier,
and it's the sharper trap because it sounds exactly like the fine-grained-permissions
work this skill does own. The free tier already scopes access this precisely: any
Member's permissions can be limited to specific projects or services, and further to
specific environments inside a project — Dokploy's own "Project Permissions" feature,
documented immediately above where the Enterprise material starts on the same page.
`hardening-dokploy` names this as part of the built-in Member role. If the ask is
*"give this person access to only this project/environment,"* that's scoping a role
Dokploy already has — free, and `hardening-dokploy`'s answer.

What this skill actually owns is **defining a new role** — Enterprise Custom Roles,
built from a menu of permission categories (over 25 of them, spanning Read, Create,
Update, Delete, Deploy, Cancel, Restore, and Write) instead of the fixed Owner/Admin/
Member set. The two only look alike in English. See
`references/scim-and-roles.md#custom-roles--and-the-freepaid-boundary` for the full
category list and where the line actually falls.

**Adding a user to the org**, with no custom role or automatic provisioning involved,
is ordinary panel administration — `operating-dokploy-servers`'s territory. This skill
owns automatic provisioning and deprovisioning through SCIM, and defining custom roles,
not inviting someone through Settings → Users.

## Two ways to unlock Enterprise

- **Enterprise Self-Hosted** — a license key activated on your own instance
  (Settings → License → enter the key → Activate). You keep full control of your
  infrastructure, including air-gapped setups, and get whitelabeling. The license is
  validated daily against Dokploy's servers using only your server's IP address — no
  other data is sent.
- **Enterprise Cloud** — a custom Dokploy Cloud plan with the control plane managed by
  Dokploy. Same SSO/SCIM/custom-roles/audit-log/Application-Authentication feature set,
  no whitelabeling, no air-gapped operation.

Both include every future Enterprise feature at no extra cost. Detail on activation and
validation: `references/scim-and-roles.md#license-keys`.

## Single sign-on (OIDC or SAML)

Five providers have a dedicated setup guide: **Microsoft Entra ID** and **Okta** lead —
they're what a university identity team is most likely to already run — followed by
Auth0, Keycloak, and Zitadel. Any other OIDC/SAML-compliant provider works too,
configured manually against the same flow. Auth0, Entra ID, and Okta each document both
OIDC and SAML; Keycloak and Zitadel's guides show OIDC only.

Dokploy's own SSO overview page names just two providers in its opening sentence
("Auth0, Keycloak, or any compatible identity provider") while listing five dedicated
guides right below it — read the list, not the sentence, or a reader on Entra ID or
Okta will wrongly conclude their provider isn't supported.

Per-provider field names (Issuer URL, Client ID/Secret, Certificate, Domain), the exact
callback URL each provider's guide shows, and a real inconsistency in those callback
URLs — Zitadel's OIDC callback path doesn't match the other four providers' — are in
`references/sso-providers.md`. Confirm the callback URL Dokploy displays at setup time
for the provider actually being configured rather than assuming one provider's pattern
applies to another.

## SCIM provisioning

SCIM 2.0 automates the user *lifecycle* (who exists, whether they're active) as a
complement to SSO, which handles *authentication* — the two are independent and can be
used together or separately. Supported IdPs: Okta, Microsoft Entra ID, JumpCloud, or
any SCIM 2.0 compatible provider.

This is the direct answer to **"automatically deprovision users who leave"**: every
provisioned user lands with the Member role, and suspending or unassigning them in the
IdP deactivates (revoking sessions) or removes their Dokploy account — no manual
cleanup. Setup is a Bearer token generated per IdP connection from Settings →
SSO → Manage SCIM, pasted into the IdP's SCIM configuration alongside the endpoint URL
`https://your-dokploy-domain.com/api/auth/scim/v2`. The token is shown once; rotating it
means deleting the provider and generating a new one.

Two real limits: SCIM doesn't provision groups (no group-to-role mapping — roles stay
managed inside Dokploy), and it doesn't link to an existing account — provisioning a
user whose email already exists in Dokploy returns `409 Conflict`. Full setup for Okta
and Entra ID, the supported operations, and the user-lifecycle table:
`references/scim-and-roles.md#scim-provisioning`.

## Custom roles

Beyond Owner/Admin/Member, an Enterprise license builds named roles (e.g. `developer`,
`viewer`, `deployer`) from a permission matrix spanning over 25 categories — Users,
Projects, Services, Deployments, Backups, Secrets Providers, DNS Providers, and more —
each with its own subset of Read/Create/Update/Delete/Deploy/Cancel/Restore/Write.
Created from Settings → Custom Roles, assigned from Settings → Users. Least privilege,
clear naming, and periodic review are the docs' own stated best practices. See the
[free/paid boundary](#the-freepaid-boundary--read-this-before-anything-else) above
before reaching for this — many "restrict this person's access" requests are already
answered by the free tier's own project/environment scoping.

Full category table: `references/scim-and-roles.md#custom-roles--and-the-freepaid-boundary`.

## Audit logs

Settings → Audit Logs records every create, update, delete, login, logout, deployment,
and configuration change, each entry carrying a timestamp, the acting user's email and
role, the action type, and the affected resource and name. Filterable four ways: by
user, by name, by action, and by resource — nothing filters on the timestamp field
itself. This is the direct answer to **"who deployed to production last Tuesday"** —
filter Action = `Deployed`, then narrow by the resource's name; timestamp is a field on
each entry, not a filter control. Full field and category list:
`references/scim-and-roles.md#audit-logs`.

## Whitelabeling

For presenting the panel as something other than visibly third-party Dokploy — a
platform team fronting it for other departments, or anyone reselling it under their
own name. Self-hosted only, per the editions table (Enterprise Cloud's shared control
plane doesn't offer it). Settings → Whitelabel rebrands the application name, logos,
and favicon; injects custom CSS for appearance; edits page title, footer text, and
sidebar links; and edits error-page text — with a live preview before saving. Detail:
`references/scim-and-roles.md#whitelabeling`.

**Flag, not resolved**: a separate Cloud Plans comparison in the same corpus shows
white labeling included on Dokploy Cloud's own "Enterprise" and "Agency" plan tiers —
which contradicts the editions table this skill follows. See
`references/scim-and-roles.md#whitelabeling` for both citations side by side.

## Gating a deployed application behind SSO

Application Authentication puts an SSO login gate in front of a **deployed
application**, not the panel — this is the direct answer to **"put our internal
dashboard behind SSO login."** Built on oauth2-proxy and Traefik's `forwardAuth`
middleware: Dokploy deploys a `dokploy-forward-auth` service per server, configured
with one already-registered OIDC provider (SAML isn't supported here), and any
application domain can toggle SSO protection on independently. Requires a shared auth
domain (e.g. `auth.acme.com`) on the *same base domain* as the app being protected, and
covers **application domains only** — Compose service domains aren't supported. There
is no allow-list by email, domain, or group inside Dokploy; access control for who can
authenticate has to live on the identity provider side. Full setup, removal, and limits:
`references/sso-providers.md#application-authentication-forward-auth`.

## Which features need a license

Everything in this file needs at least an Enterprise license or plan: license
activation itself, SSO, SCIM, audit logs, whitelabeling, and Application
Authentication all show as a flat no outside Enterprise in the docs' own edition
table. Custom roles are the one item with a real exception rather than a flat no: the
same table marks them "Plan-dependent" on plain (non-Enterprise) Dokploy Cloud, so a
plain Cloud plan may already include them depending on which one. Everything in
`hardening-dokploy`'s access-control section — 2FA, passkeys, the built-in
Owner/Admin/Member roles, and per-project/per-environment scoping of them — needs no
license at all, on any tier.

## Scripting any of this

Activating a license, registering an SSO provider, generating a SCIM token, or creating
a custom role from the CLI or API is `automating-dokploy`'s job, not this skill's — it
already lists `sso`, `scim`, `custom-role`, `license-key`, `audit-log`, and
`whitelabeling` as six Enterprise-gated CLI resource groups it observed on the
installed CLI (their existence, not their licensed behavior, which is documentation-only
here too). This skill owns what each feature does and how it's configured from the
panel; that one owns the mechanism for driving it unattended.

## Verify before reporting an enterprise task done

- [ ] The request was actually free-tier (2FA, passkeys, built-in roles, or
      project/environment scoping of them) before reaching for a licensed answer
- [ ] A license or Enterprise Cloud plan is confirmed active, not assumed, before
      walking through SSO, SCIM, custom roles, audit logs, or whitelabeling setup
- [ ] A provider's callback URL was read from what Dokploy's own setup screen shows for
      that provider, not carried over from a different provider's guide
- [ ] Application Authentication is being set up on an application domain, not a
      Compose service domain

## Where the rest lives

- `references/sso-providers.md` — OIDC and SAML setup per provider (Entra ID and Okta
  first), the common Dokploy-side fields, the callback-URL table and the Zitadel
  discrepancy, the SSO-overview prose/list inconsistency, and Application
  Authentication's full setup, removal, and limits.
- `references/scim-and-roles.md` — license activation and validation, the full custom
  Role permission-category table and the free/paid boundary worked through in detail,
  SCIM setup and its supported operations and limits, audit log fields and filtering,
  and whitelabeling's customizable sections.
