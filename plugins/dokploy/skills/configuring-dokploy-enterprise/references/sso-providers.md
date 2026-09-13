# SSO providers and Application Authentication

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [OIDC vs SAML, and which providers have which](#oidc-vs-saml-and-which-providers-have-which)
- [Common Dokploy-side fields](#common-dokploy-side-fields)
- [Callback URL patterns, and where they disagree](#callback-url-patterns-and-where-they-disagree)
- [Microsoft Entra ID (Azure AD)](#microsoft-entra-id-azure-ad)
- [Okta](#okta)
- [Auth0](#auth0)
- [Keycloak](#keycloak)
- [Zitadel](#zitadel)
- [A doc-level inconsistency worth flagging](#a-doc-level-inconsistency-worth-flagging)
- [Application Authentication (Forward Auth)](#application-authentication-forward-auth)

## OIDC vs SAML, and which providers have which

Enterprise SSO supports two protocols: OpenID Connect (OIDC) and SAML. Five providers
have a dedicated setup guide: Microsoft Entra ID (Azure AD), Okta, Auth0, Keycloak, and
Zitadel. Any other OIDC- or SAML-compliant provider works too, configured manually
against the same endpoints and flow — the docs don't walk through a sixth provider by
name, so treat the five below as the worked examples, not an exhaustive list.

Not every provider's guide covers both protocols. Auth0, Entra ID, and Okta each carry
two tabs — SSO (OIDC) and SAML. Keycloak and Zitadel's guides show only an OIDC flow;
no SAML tab exists for either. That's what the docs document, not a claim that Keycloak
or Zitadel can't do SAML at all — if a SAML setup is needed for one of those two, the
docs don't carry the steps and this file won't invent them.

## Common Dokploy-side fields

Every OIDC provider is configured the same way, from **Settings** (or **Organization** /
**Security** in Enterprise) → **Enable SSO** → **OpenID Connect**:

| Field | What goes in it |
|---|---|
| Provider | A unique name you choose for this connection, used in the callback URL path |
| Issuer URL | The provider's OIDC issuer — exact value differs per provider, see below |
| Domain | The email domain your users authenticate with (e.g. `acme.com`) — **not** the Dokploy instance's own URL |
| Client ID / Client Secret | From the application you register with the provider |
| Scopes | `openid email profile` for every provider covered here |

SAML providers (Auth0, Entra ID, Okta) instead take **Provider**, **Issuer URL** (the
IdP's Entity ID), **SSO URL**, **Certificate** (x509), **Federation Metadata XML**, and
**Domain**.

## Callback URL patterns, and where they disagree

Dokploy shows the exact callback URL to register with the provider once the connection
is being configured — read it from there rather than assuming one provider's pattern
applies to another's. The docs' own worked examples use two different OIDC patterns:

| Provider | Protocol | Callback / ACS URL shown in the docs |
|---|---|---|
| Entra ID (Azure AD) | OIDC | `https://your-dokploy-domain.com/api/auth/callback/myorg-name-azure` |
| Okta | OIDC | `https://your-dokploy-domain.com/api/auth/callback/myorg-name-okta` |
| Auth0 | OIDC | `https://your-dokploy-domain.com/api/auth/callback/myorg-name-auth0` |
| Keycloak | OIDC | `https://your-dokploy-domain.com/api/auth/callback/my-client-id` |
| Zitadel | OIDC | `https://your-dokploy-domain.com/api/auth/sso/callback/zitadel` |
| Entra ID (Azure AD) | SAML | `https://your-dokploy-domain.com/api/auth/sso/saml2/callback/myorg-name-azure-saml` |
| Okta | SAML | `https://your-dokploy-domain.com/api/auth/sso/saml2/callback/myorg-name-okta-saml` |
| Auth0 | SAML | `https://your-dokploy-domain.com/api/auth/sso/saml2/callback/myorg-name-auth0-saml` |

Four of the five OIDC guides (Entra ID, Okta, Auth0, Keycloak) use
`/api/auth/callback/<provider-name>`. **Zitadel's own guide uses
`/api/auth/sso/callback/{providerId}` instead** — an extra `/sso` segment that makes its
OIDC callback path look more like the SAML pattern than like the other four providers'
OIDC pattern. Nothing in the corpus explains the difference; it isn't a version note or
a typo call-out, it's just what each provider's page shows. Don't generalize one
provider's callback path onto another — confirm it per provider, either from this table
or, better, from what Dokploy's own SSO settings screen displays at setup time for the
provider name actually chosen.

## Microsoft Entra ID (Azure AD)

**OIDC**

1. Azure Portal → **Microsoft Entra ID** → **App registrations** → **New registration**.
   Set **Redirect URI** (Web) to a placeholder for now.
2. Register; note the **Application (client) ID** and **Directory (tenant) ID**.
3. **Certificates & secrets** → **New client secret**; note its value immediately — it
   isn't shown again.
4. Issuer URL: `https://login.microsoftonline.com/{tenant-id}/v2.0` (some setups expect
   a trailing slash; multi-tenant apps may use `common` in place of the tenant ID).
5. In Dokploy: enable SSO, choose OpenID Connect, enter Provider, the Issuer URL above,
   Domain, Client ID, Client Secret, Scopes `openid email profile`. Save.
6. Back in Azure, under **Authentication → Web → Redirect URIs**, add
   `https://your-dokploy-domain.com/api/auth/callback/<provider>`. Under **Token
   Configuration**, add the optional claims **email**, **preferred_username**, and
   **upn**.

Troubleshooting the docs name: redirect URI mismatch (must match exactly, including
protocol and path), invalid client (check the client ID/secret and that the secret
hasn't expired), wrong tenant (use the correct Directory ID, or `common` for
multi-tenant apps), and missing scopes (confirm the app registration grants `openid`,
`email`, `profile`).

**SAML**

1. Azure Portal → **Microsoft Entra ID** → **Enterprise applications** → **New
   application** → **Create your own application** (non-gallery) → **Single sign-on**
   → **SAML**.
2. Note the **Identifier (Entity ID)** and **Login URL**; download the **Certificate
   (Base64)** and the **Federation Metadata XML**.
3. In Dokploy: enable SSO, choose SAML, enter Provider, Issuer URL (Azure's Entity ID,
   e.g. `https://sts.windows.net/YOUR_TENANT_ID/`), SSO URL (Azure's Login URL), the
   certificate, the metadata XML, and Domain. Save.
4. Back in Azure, set **Identifier (Entity ID)** to the SP Entity ID Dokploy expects and
   **Reply URL (ACS)** to `https://your-dokploy-domain.com/api/auth/sso/saml2/callback/<provider>-saml`.

Troubleshooting: ACS URL mismatch, certificate format (Base64 as provided, or convert
to PEM if Dokploy expects it), and Entity ID mismatch between the two sides.

## Okta

**OIDC**

1. Okta Admin Console → **Applications** → **Create App Integration** → **OIDC – OpenID
   Connect**, **Web Application**.
2. Note the **Client ID** and **Client Secret**. Note the Okta domain and, for a custom
   authorization server, its issuer (e.g. `https://your-domain.okta.com/oauth2/default`);
   otherwise the issuer is `https://your-domain.okta.com`.
3. In Dokploy: enable SSO, OpenID Connect, Provider, Issuer URL, Domain, Client ID,
   Client Secret, Scopes `openid email profile`. Save.
4. Back in Okta, set **Sign-in redirect URIs** to
   `https://your-dokploy-domain.com/api/auth/callback/<provider>`, and add the Dokploy
   URL under **Trusted Origins** if CORS requires it.

Troubleshooting: redirect URI mismatch, invalid client (confirm the grant type includes
Authorization Code), wrong issuer (use the full authorization-server issuer URL), and
scopes not permitted by the authorization server.

**SAML**

1. Okta Admin Console → **Applications** → **Create App Integration** → **SAML 2.0**.
2. Set the **Single sign-on URL** to Dokploy's SAML ACS URL and the **Audience URI (SP
   Entity ID)** to the Dokploy instance URL.
3. From the **Sign On** tab, note the **Issuer** (Entity ID) and the **Single sign-on
   URL**; from **Signing Certificate**, download the active x509 certificate and the
   IdP metadata XML.
4. In Dokploy: enable SSO, SAML, Provider, Issuer URL, SSO URL, Certificate, Federation
   Metadata XML, Domain. Save.

Troubleshooting: ACS URL mismatch, using the certificate that actually signs assertions,
and matching the Entity ID on both sides.

## Auth0

**OIDC**: create a Regular Web Application in the Auth0 Dashboard, note Domain/Client
ID/Client Secret, then in Dokploy enable SSO → OpenID Connect with Issuer URL
`https://YOUR_AUTH0_DOMAIN/` (trailing slash required). Back in Auth0, set **Allowed
Callback URLs** to `https://your-dokploy-domain.com/api/auth/callback/<provider>`,
**Allowed Logout URLs** and **Allowed Origins** to the bare Dokploy URL.

**SAML**: in the same Auth0 application, enable the **SAML 2 Web App** add-on and set
its callback to `https://your-dokploy-domain.com/api/auth/sso/saml2/callback/<provider>-saml`.
In Dokploy, enable SSO → SAML with the add-on's Entity ID, Single Sign-On URL,
certificate, and metadata XML. Back in Auth0's add-on **Settings**, paste a JSON block
setting `audience`, `recipient`, `destination`, `signResponse: true`,
`signAssertion: true`, the `nameIdentifierFormat`, and attribute `mappings` for email,
displayName, givenName, and surname — the exact keys the docs show, reproduced here
because getting one wrong silently drops an attribute rather than erroring:

```json
{
  "audience": "https://your-dokploy-domain.com/saml/metadata",
  "recipient": "https://your-dokploy-domain.com/api/auth/sso/saml2/callback/myorg-name-auth0-saml",
  "destination": "https://your-dokploy-domain.com/api/auth/sso/saml2/callback/myorg-name-auth0-saml",
  "signResponse": true,
  "signAssertion": true,
  "nameIdentifierFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
  "nameIdentifierProbes": ["email"],
  "mappings": {
    "email": "email",
    "displayName": "name",
    "givenName": "given_name",
    "surname": "family_name"
  }
}
```

Troubleshooting (both): redirect/ACS URL mismatch, client ID/secret or certificate
format, and scopes (`openid`, `email`, `profile`) for OIDC.

## Keycloak

OIDC only, per the docs. Create a client under the target realm (**Clients → Create
client**, Client type OpenID Connect), set its **Root URL** to the Dokploy base URL,
set **Access type** to confidential and note the secret from the **Credentials** tab.
From **Realm settings → OpenID Endpoint Configuration**, note the **Issuer** (e.g.
`https://keycloak.example.com/realms/your-realm`). In Dokploy, enable SSO → OpenID
Connect with that issuer, the client ID/secret, and Domain. Back in Keycloak, set
**Valid redirect URIs** to `https://your-dokploy-domain.com/api/auth/callback/<provider>`,
and **Valid post logout redirect URIs** / **Allowed Origins** to the bare Dokploy URL.

Troubleshooting: redirect URI mismatch, client not confidential or not enabled, missing
scopes, and — Keycloak-specific — mapping `email` or `preferred_username` attributes in
Dokploy if the user's name or email doesn't come through.

## Zitadel

OIDC only, per the docs, and its own callback pattern (see above). Create a **Web**
application in a Zitadel project, authentication method **CODE** (Authorization Code
with `client_secret_basic` — PKCE is not supported for this server-side flow), and add
the redirect URI `https://your-dokploy-domain.com/api/auth/sso/callback/{providerId}`
with `{providerId}` replaced by the provider name you'll use in Dokploy. Note the
Client ID and Client Secret. The issuer is the instance's own base domain (Cloud:
`https://your-instance.zitadel.cloud`; self-hosted: your own domain) — Dokploy fetches
the OIDC discovery document from `{issuer}/.well-known/openid-configuration`
automatically. In Dokploy: **Settings → SSO → Register OIDC Provider**, enter Provider
ID (matching `{providerId}`), Issuer URL, Domains, Client ID/Secret, and leave Scopes
empty to default to `openid email profile`. Confirm the Callback URL Dokploy shows
matches the Redirect URI configured in Zitadel exactly, including the provider ID
segment.

Troubleshooting: redirect URI mismatch (exact match including the provider ID segment),
invalid client, wrong authentication method (must be CODE, not PKCE), HTTPS required in
production (Zitadel's own Development Mode is the only way around that for testing),
and the user not existing in the Zitadel project or missing the `email` scope.

## A doc-level inconsistency worth flagging

Dokploy's own SSO overview page opens with: "Enterprise supports Single Sign-On via
OpenID Connect (OIDC) and SAML. You can use Auth0, Keycloak, or any compatible identity
provider." That sentence names two providers. The same page then lists five dedicated,
step-by-step guides: Auth0, Azure AD (Microsoft Entra ID), Okta, Keycloak, and Zitadel.
Read the provider list, not the opening sentence, as the authoritative one — a reader
whose IdP is Entra ID or Okta (the two this skill leads with, since they're what a
university identity team most likely already runs) would otherwise wrongly conclude
from the prose alone that their provider isn't supported.

## Application Authentication (Forward Auth)

A separate feature from panel SSO: it puts a login gate in front of **deployed
applications**, not the Dokploy panel itself. Built on
[oauth2-proxy](https://oauth2-proxy.github.io/oauth2-proxy/) and Traefik's `forwardAuth`
middleware.

**Prerequisites**: a valid Enterprise license, and an OIDC provider already registered
under Settings → SSO — SAML providers are not supported for this feature, OIDC only. A
domain you control as the shared **auth domain** (e.g. `auth.acme.com`), pointed at the
target server. The auth domain must share the **same base domain** as any application
domain being protected (`auth.acme.com` can protect `app.acme.com`, not
`app.other.com`), because the authentication cookie is scoped to that shared base
domain.

**How it works**: Dokploy deploys a dedicated `dokploy-forward-auth` service
(oauth2-proxy) on a server, configured with one of the registered OIDC providers. Every
application domain that enables SSO protection gets a `forwardAuth` middleware pointing
at the auth domain. An unauthenticated visitor is redirected to the identity provider,
then back to the app once authenticated. This is deployed **per server**: one
oauth2-proxy instance covers every protected domain on that server, and only one auth
domain and one OIDC provider can be configured per server — different providers for
different applications means deploying on different servers.

**Setup**: Settings → SSO → Application Authentication → pick the server → set the auth
domain and its TLS/certificate settings → Deploy, choosing which OIDC provider to use →
Dokploy shows a callback URL to register with the identity provider if it isn't already
covered.

**Protecting a domain**: Application → Domains tab → shield icon next to the domain →
toggle **Protect this domain with SSO**. Enabled per domain — an application with
several domains can protect some and not others. **Docker Compose service domains are
not supported for this feature**, only application domains.

**Removing protection**: toggle the domain off from the Domains tab to stop protecting
one domain, or go to Settings → SSO → Application Authentication and click **Remove**
for the server to tear down the entire proxy — this removes the `dokploy-forward-auth`
service, and no application on that server can enable SSO protection again until it's
redeployed.

**No allow-list.** Any user who successfully authenticates against the configured
identity provider is granted access — there is no allow-list by email, domain, or group
inside Dokploy. Access control has to be enforced on the identity provider side (e.g.
restrict who can sign in to the OIDC application registered for this).
