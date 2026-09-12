# Traefik middleware: HSTS and rate limiting

Verified: the Dokploy middleware keys, labels, and example values are from
docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance. The HSTS
semantics around them — what a browser does with the header and how a policy is revoked or
a preload entry removed — are from RFC 6797 and hstspreload.org, cited inline at each
claim.

Contents:
- [Neither is a UI toggle](#neither-is-a-ui-toggle)
- [HSTS middleware](#hsts-middleware)
- [Rate-limit middleware](#rate-limit-middleware)
- [Compose services: the gap the guide names but doesn't fill](#compose-services-the-gap-the-guide-names-but-doesnt-fill)
- [Traefik dashboard](#traefik-dashboard)
- [Isolated Deployments](#isolated-deployments)

## Neither is a UI toggle

TLS itself is automatic for domains managed through Dokploy's Applications flow — Let's
Encrypt via `certResolver`, with an HTTP router that redirects to HTTPS by default. HSTS
and rate limiting are not: the Production Hardening Guide states both go through a
custom middleware, because there is no panel toggle for either today.

## HSTS middleware

Dokploy's Applications flow writes a domain config — a `routers` + `services` block per
domain — editable from the app's **Advanced → Traefik File System** tab. Add a `headers`
middleware and reference it from the `websecure` router's `middlewares` list:

```yaml
http:
  middlewares:
    secure-headers:
      headers:
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
  routers:
    dokploy-app-name-router-websecure-1:
      middlewares:
        - secure-headers
      # ...rest of the router config Dokploy already generated
```

Edit the router block Dokploy already generated for that domain — the `# ...rest`
comment above stands in for the `rule`, `service`, `entryPoints`, and `tls` fields
already there. Don't recreate the router from scratch.

Each key, in plain terms:

- **`stsSeconds`** — how long, in seconds, a browser that has loaded this response
  should refuse to speak plain HTTP to this host. `31536000` above is one year, the
  guide's own example value.
- **`stsIncludeSubdomains`** — extends that refusal from just the domain that sent the
  header to every subdomain of it, whether or not that subdomain has ever sent the
  header itself.
- **`stsPreload`** — opts into being added to browser vendors' hard-coded HSTS preload
  lists, so the refusal applies even on a visitor's very first connection, before the
  browser has ever talked to the host at all. **This is the genuinely hard-to-undo
  key**: per [hstspreload.org's removal process](https://hstspreload.org/#removal),
  getting off the list means dropping the `preload` directive from the header (which is
  what makes the domain eligible), submitting the removal form, and then waiting for
  browser vendors to ship a new release carrying the updated list — the page's own words
  are that "it takes months for a change to reach users with a Chrome update and we cannot
  make guarantees about other browsers." Months, not a `max-age`. Getting listed in the
  first place isn't automatic from sending the header either; it requires a submission to
  the same site.

`stsSeconds` and `stsIncludeSubdomains`, by contrast, are revocable — but only
actively, never by doing nothing:

1. **Silence does not revoke.** Deleting this middleware from the router leaves the
   cached policy in force on every browser that already saw it, for whatever's left of
   `stsSeconds`. This is the real sharp edge, and it's why the setting feels
   irreversible even though it isn't.
2. **Revoking is something you serve, not something you stop serving.** Set
   `stsSeconds: 0` (a `Strict-Transport-Security: max-age=0` response) and keep serving
   it. Per [RFC 6797 §6.1.1](https://www.rfc-editor.org/rfc/rfc6797#section-6.1.1), a
   user agent that receives `max-age=0` from a Known HSTS Host ceases to regard it as
   one at all, `includeSubDomains` included — that's the documented server-side undo,
   and the corpus itself says nothing about revocation either way, so treat this
   paragraph as authored guidance carrying its own citation, not a guide claim.
3. **It only reaches browsers that come back.** One that doesn't revisit the host
   before the original `max-age` would have lapsed anyway stays under the old policy
   until it does reconnect. Revocation is prompt for active users and slow for everyone
   else — the real reason to prove out a short `stsSeconds` (hours or days) before
   adopting the guide's own one-year example, not because a year can never be undone.
4. **The parent domain that asserted `includeSubDomains` is where the undo happens.**
   Serving `max-age=0` from the domain that set the directive clears the whole entry,
   subdomains included — so a subdomain that can't yet serve HTTPS, and therefore can't
   send its own revoking header, is still recoverable from the domain where the mistake
   was made.

None of this changes the operational advice: turn `stsIncludeSubdomains` on only once
every current and near-future subdomain is actually served over HTTPS, and prove out a
short `stsSeconds` first rather than starting at a year on a parent domain covering
subdomains you don't control yet. The reason is speed of recovery, not impossibility of
recovery — a mistake reaches every returning visitor only as fast as they return.

## Rate-limit middleware

Same file, a `ratelimit` middleware:

```yaml
http:
  middlewares:
    rate-limit:
      rateLimit:
        average: 100
        burst: 50
  routers:
    dokploy-app-name-router-websecure-1:
      middlewares:
        - rate-limit
```

`average` is requests/second sustained per source; `burst` is the short spike allowed
above it. The guide gives no recommended values beyond this example — tune both to the
actual traffic pattern before relying on them.

A router's `middlewares` list can carry both names — `secure-headers` and `rate-limit`
— once each is defined.

## Compose services: the gap the guide names but doesn't fill

Docker Compose domains route through Traefik **labels** read from container metadata,
not this per-domain file, and the guide states directly that they "need the same
[HTTPS] redirect added explicitly" that Applications get by default. It does not,
however, show a worked label for that redirect, or a labeled equivalent of either
middleware above, applied to a Compose service.

Don't invent that label syntax here. `deploying-apps-to-dokploy`'s
`references/compose-services.md` documents the routing labels Dokploy's docs do show
for Compose (`traefik.enable`, the router `rule`, the entrypoint, the load-balancer
port) — confirm against that pattern and against the panel's **Preview Compose** button,
which renders the file that will actually deploy, before writing a middleware label by
hand.

## Traefik dashboard

The guide states the dashboard "isn't exposed by a default Dokploy install, and it
should stay that way unless it's behind auth and off the public network." Nothing here
turns it on; the control is confirming it stays off.

## Isolated Deployments

An alternative to manually adding `dokploy-network` to every service in a Compose file.
When enabled, Dokploy creates a network named after the application (`appName`), attaches
every service in the compose file to it, and connects Traefik to that network — so
isolation doesn't require mentioning `dokploy-network` at all. All open-source templates
ship with it enabled, and it's what lets two instances of the same template coexist:
without it, two stacks using identical service names collide on the shared network.

One documented caveat: a **custom installation** that replaces the standalone Traefik
container with a Docker service can lose its services' network references to Traefik
after a system restart, because Docker Swarm changes network references on restart —
this may need a manual redeploy to restore connectivity. The official install, and a
manual install that keeps the standalone Traefik container, don't have this issue.
