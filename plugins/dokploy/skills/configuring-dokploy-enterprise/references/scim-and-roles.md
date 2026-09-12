# License keys, custom roles, SCIM, audit logs, and whitelabeling

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [License keys](#license-keys)
- [Custom roles — and the free/paid boundary](#custom-roles--and-the-freepaid-boundary)
- [SCIM provisioning](#scim-provisioning)
- [Audit logs](#audit-logs)
- [Whitelabeling](#whitelabeling)

## License keys

Two separate ways to unlock Enterprise, not one:

| | Enterprise Self-Hosted | Enterprise Cloud |
|---|---|---|
| Activation | A license key on your own instance | A custom Dokploy Cloud plan |
| Control plane | You manage it | Dokploy manages it |
| Whitelabeling | Included | Not included — shared control-plane infrastructure |
| Air-gapped / private networks | Supported | Not supported |

Both flavors include SSO, SCIM provisioning, custom roles, audit logs, and Application
Authentication, and both automatically pick up every future Enterprise feature at no
extra cost. Plain (non-Enterprise) Dokploy Cloud does not include SSO, SCIM, audit
logs, or Application Authentication at all — only an Enterprise Cloud plan does; custom
roles specifically are "plan-dependent" on plain Cloud per the docs' own edition table,
not a flat yes or no.

**Activating a self-hosted key**: Settings → License (or Organization → License in
Enterprise), enter the key, click **Activate**. The instance then has Enterprise
features for the license's duration.

**How validation works**: the license is checked daily against Dokploy's own servers.
The docs are specific about what's sent: "The only data used for validation is the IP
address of your server" — nothing else is sent or stored for validation. If the
server's IP changes, contact Dokploy.

Scripting activation, deactivation, or checking license status from the CLI or API —
`license-key activate`, `deactivate`, `have-valid-license-key`,
`get-enterprise-settings`, `update-enterprise-settings`, `validate` — is
`automating-dokploy`'s territory; its `references/cli-command-map.md` already lists
this resource group's actions as one of six Enterprise-gated CLI groups (alongside
`sso`, `scim`, `custom-role`, `audit-log`, and `whitelabeling`), observed against the
installed CLI without a license to actually run them.

## Custom roles — and the free/paid boundary

**The free tier already does per-project and per-environment scoping.** Every Member's
access can be limited to specific projects or services, and further to specific
environments within a project — this is the docs' own "Project Permissions" feature,
documented in the free Roles & Permissions material, one section above where the
Enterprise material starts. `hardening-dokploy` owns this: its Least-privilege-roles
guidance names "per-project or per-environment scoping" as part of what the built-in
Member role already offers. If the request is "give this person access to only this
one project" or "only this one environment," that's scoping an *existing* role —
free, and not this skill's job.

**What Enterprise adds is defining a new role.** Custom Roles let an Enterprise license
holder go beyond the three built-in roles (Owner, Admin, Member) and build a named role
from a menu of permission categories, each with its own subset of actions drawn from
Read, Create, Update, Delete, Deploy, Cancel, Restore, and Write. The docs describe this
as "over 25 permission categories" — the category list below has 29 entries as
enumerated in the docs, which is consistent with that description, not a stronger claim
than it.

The permission categories, reproduced from the docs' own enumeration:

| Category | Actions offered |
|---|---|
| Users | Read, Create, Update, Delete |
| Projects | Create, Delete |
| Services | Create, Read, Delete |
| Environments | Create, Read, Delete |
| Docker | Read |
| SSH Keys | Read, Create, Delete |
| Git Providers | Read, Create, Delete |
| Traefik Files | Read, Write |
| API / CLI | Read |
| Volumes | Read, Create, Delete |
| Deployments | Read, Deploy, Cancel |
| Service Environment Variables | Read, Write |
| Project Shared Environment Variables | Read, Write |
| Environment Shared Environment Variables | Read, Write |
| Servers | Read, Create, Delete |
| Registries | Read, Create, Delete |
| Certificates | Read, Create, Delete |
| Backups | Read, Create, Update, Delete, Restore |
| Volume Backups | Read, Create, Update, Delete, Restore |
| Schedules | Read, Create, Update, Delete |
| Domains | Read, Create, Delete |
| S3 Destinations | Read, Create, Delete |
| Notifications | Read, Create, Update, Delete |
| Tags | Read, Create, Update, Delete |
| Logs | Read |
| Monitoring | Read |
| Audit Logs | Read |
| Secrets Providers | Read, Create, Update, Delete |
| DNS Providers | Read, Create, Update, Delete |

**Creating a role**: Settings → Custom Roles → Create Role → name it (the docs'
examples: `developer`, `viewer`, `deployer`, `project-admin`) → select permissions →
Save.

**Assigning it**: Settings → Users → select the user → change their role to the custom
role → Save. Access applies immediately.

**Best practices the docs state**: least privilege (a developer who only deploys
doesn't need user or certificate management), clear names describing what the role can
do, and periodic review as the team and workflows change.

A worked example of a resource that already has per-action custom-role granularity
today: DNS provider management is gated by a `dnsProvider` permission resource where
Owners and Admins get full create/update/delete/test access, Members get read-only,
and — with an Enterprise license — a custom role can grant each of `read`, `create`,
`update`, `delete` independently. Every create, update, and delete on a DNS provider is
also recorded in the Audit Log, which is the pattern Enterprise access control and
Enterprise audit logging follow together across the rest of the categories above too.

Scripting role creation, updates, or assignment — `custom-role create`, `update`,
`remove`, `get-statements`, `members-by-role`, `all` — is `automating-dokploy`'s
territory, not this skill's; this skill owns what a role can do and how to build one
from the panel.

## SCIM provisioning

SCIM (System for Cross-domain Identity Management, 2.0) automates the user *lifecycle*
— who exists and whether they're active — as a complement to SSO, which handles
*authentication*. They're independent: SCIM can be used with or without SSO configured.
Supported identity providers: Okta, Microsoft Entra ID, JumpCloud, or any SCIM 2.0
compatible IdP.

**Configure Dokploy**:

1. Settings → SSO → **Manage SCIM**.
2. Copy the SCIM 2.0 endpoint URL: `https://your-dokploy-domain.com/api/auth/scim/v2`.
3. Under **Generate token for a new provider**, choose a lowercase provider ID
   (letters, numbers, dashes — e.g. `okta`, `entra`) and click **Generate**.
4. Copy the Bearer token — **it is shown only once**. To rotate it later, delete the
   provider and generate a new one; there is no in-place rotation.

Multiple SCIM providers can coexist (one per IdP connection). Deleting a provider stops
the IdP from syncing but does not remove users it already provisioned.

**Configure the identity provider** — generally two values: the SCIM endpoint URL as
the Base/Tenant URL, and OAuth Bearer Token auth using the token Dokploy generated.

- **Okta**: app integration → **Provisioning** tab → SCIM connector base URL = the
  Dokploy endpoint; unique identifier field for users = `userName`; authentication =
  HTTP Header with the Bearer token; under **Provisioning to App**, enable **Create
  Users**, **Update User Attributes**, **Deactivate Users**; assign users to the app.
- **Microsoft Entra ID**: Enterprise applications → your app → **Provisioning** →
  Provisioning Mode **Automatic** → Tenant URL = the Dokploy endpoint, Secret Token =
  the Bearer token → **Test Connection** → save → assign users.
- Any other SCIM 2.0 IdP: point it at the same endpoint URL and authenticate the same
  way.

**Supported operations** (the SCIM 2.0 User resource):

| Operation | Endpoint | Effect |
|---|---|---|
| Provision | `POST /Users` | Create a user, add to the organization |
| List / filter | `GET /Users` | List provisioned users, supports `filter` |
| Read | `GET /Users/{id}` | Fetch one user |
| Replace | `PUT /Users/{id}` | Replace a user's attributes |
| Update | `PATCH /Users/{id}` | Partial update, including activate/deactivate |
| Deprovision | `DELETE /Users/{id}` | Remove the user from the organization |

Discovery endpoints (`/ServiceProviderConfig`, `/Schemas`, `/ResourceTypes`) are also
available for IdP auto-detection.

**User lifecycle**:

| Action in the IdP | Effect in Dokploy |
|---|---|
| Assign / provision | User created, added as **Member** |
| Update profile | Attributes updated |
| Suspend (`active: false`) | Marked Deactivated, sessions revoked |
| Reactivate (`active: true`) | Access restored |
| Unassign (`DELETE`) | Removed from the organization |

Every provisioned user lands with the **Member** role — this is the deprovisioning
guarantee "someone left the IdP and lost Dokploy access automatically" is built on, and
it answers "automatically deprovision users who leave" directly: suspend or unassign in
the IdP, and Dokploy revokes sessions or removes the account. The docs name no sync
cadence for this — don't add one that isn't there.

**Limitations, stated directly in the docs**:

- **No group provisioning.** The Groups resource isn't supported, so there's no
  group-to-role mapping — roles are still managed inside Dokploy. Broader access than
  Member needs a manual role change or a custom role.
- **Existing users aren't linked.** SCIM only creates new users; provisioning a user
  whose email already exists in Dokploy returns `409 Conflict`.
- **Tokens are shown once** and can't be rotated in place.

## Audit logs

Settings → Audit Logs. Every entry captures:

| Field | Description |
|---|---|
| Timestamp | When the action occurred |
| User | Email of the user who performed it |
| Action | `Created`, `Updated`, `Deleted`, `Deployed`, `Login`, `Logout` |
| Resource | Type affected (`application`, `Custom Role`, `Settings`, `Session`, `Domain`, etc.) |
| Name | The resource's own name or identifier |
| Role | The acting user's role at the time |
| Metadata | Additional context when available |

**What's logged**: authentication (logins, logouts, sessions); user management
(creating, updating, removing users, role changes); custom roles; projects and services
(create, update, deploy, delete for applications, databases, Compose stacks); domains;
environment variables (service, project, and environment level); settings (org
settings, whitelabel configuration, version updates); infrastructure (servers,
registries, certificates, SSH keys, S3 destinations); backups and schedules; notification
providers; secrets provider connections; DNS provider connections.

**Filtering**: exactly four dimensions, per the docs — by user, by name (a specific
resource's name), by action type, by resource type. Timestamp is a field captured on
every entry, not a fifth filter; the docs don't describe a date-range control.

**Use cases the docs name**: security investigations (who changed what, and when),
compliance evidence for SOC 2, GDPR, and internal policy, debugging (tracing a
deployment failure back to the change that caused it), and general team visibility.

This is the direct answer to "who deployed to production last Tuesday" — filter by
Action = `Deployed`, then by the resource's name if more than one deploy needs
narrowing down.

## Whitelabeling

**Self-hosted only.** Enterprise Cloud does not include it — the docs' own reason is
that the control plane there is shared infrastructure. Settings → Whitelabel.

**A contradiction in the source, named rather than resolved.** Two tables give opposite
answers. The "Editions at a glance" table and the "Key differences between the two
Enterprise flavors" table both mark Whitelabeling ❌ for Enterprise Cloud, the second one
with the shared-infrastructure reason attached. But the separate **Cloud Plans**
comparison — Dokploy Cloud's own Hobby/Startup/Enterprise/Agency tiers — marks "White
labeling" ✅ for its Enterprise and Agency plans. Nothing in the corpus reconciles the
two. This file follows the editions table, because that's the table the Enterprise
material itself points to and the one the license-keys table above already matches —
but a Dokploy Cloud customer on an Enterprise or Agency plan whose own dashboard shows
whitelabeling available should trust what they see over either table.

| Section | Customizes |
|---|---|
| Branding | Application Name (replaces "Dokploy" everywhere), Application Description (login/onboarding tagline), Logo URL, Login Page Logo URL, Favicon URL (`.ico`, `.png`, `.svg`) |
| Appearance | A Custom CSS editor injecting global styles; **Load Default Styles** seeds it with the base theme's CSS variables to edit from |
| Metadata & Links | Page Title, Footer Text, Support URL, Documentation URL |
| Error Pages | Error Page Title, Error Page Description |

A **Live Preview** panel at the bottom of the settings page shows logo, application
name, button styles, and footer text before saving. **Reset to Defaults** reverts every
whitelabel setting; **Save Changes** applies them.

**Best practices the docs state**: high-resolution (2×) logos, SVG where possible for
clean scaling; sufficient color contrast in custom CSS; testing the login page,
dashboard, and key workflows after applying changes; always previewing before saving.
