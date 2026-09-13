# Trigger battery — deploying-apps-to-dokploy

Run each query in a clean session with only the description visible. Record fired / did not fire.

Four sibling skills ship in this same plugin and every one of their descriptions
contains the word "dokploy", so the negatives below are the real test: they name the
sibling that should win instead.

## Should trigger

1. "Deploy this Next.js app to our Dokploy server."
2. "Switch this app from Nixpacks to a Dockerfile build."
3. "Add api.example.edu to this Dokploy app with HTTPS."
4. "My Dokploy domain returns 404." *(symptom only)*
5. "Bad Gateway right after a successful deploy." *(symptom only)*
6. "The certificate never issued for the domain I just added." *(symptom only)*
7. "How do I point env vars at our Vault instead of pasting secrets?"
8. "Set up preview deployments for pull requests."
9. "Roll back to the previous release."
10. "Only rebuild when the `apps/web` directory changes." *(watch paths, never named)*
11. "Our Compose stack's new domain isn't taking effect." *(symptom only — the redeploy requirement)*

Items 4–6, 10, and 11 are the ones a weak description misses. Each names a symptom and
no feature: 4 and 11 are the routing asymmetry between Applications and Compose
services, 5 is a container bound to `127.0.0.1`, 6 is a domain added before its DNS
record existed, and 10 is watch paths under a description a user would never guess.

## Should not trigger (near misses)

1. "Write a multi-stage Dockerfile for this Node API." → `docker-workbench:containerizing-apps`
2. "Trigger a Dokploy deploy from GitHub Actions." → `automating-dokploy`
3. "Install Dokploy on a fresh VPS." → `operating-dokploy-servers`
4. "Is our Dokploy panel exposed?" → `hardening-dokploy`
5. "Connect Dokploy to Entra ID." → `configuring-dokploy-enterprise`
6. "Deploy this app to Vercel." → not Dokploy at all
7. "Deploy this to our Kubernetes cluster." → not Dokploy at all

Items 6 and 7 are the sharpest negatives: both are unmistakably deployment, and firing
on either would mean the description keys off "deploy" rather than off Dokploy. They
test that from two angles. Item 6 names a competing managed platform. Item 7 names no
product at all and describes self-hosted infrastructure the user owns, which is the
situation Dokploy is in — so it is the harder of the two. Item 2 is the sharpest
internal one, since choosing a build type and triggering a build from CI both read as
deployment work; the split is that this skill owns which setting to choose and
`automating-dokploy` owns the mechanism that applies it.

## A/B assertions

Run "our Dokploy Compose stack returns 404 on the domain I added an hour ago" with and
without the skill. With the skill, the output should show all of:

- [ ] The Applications-versus-Compose routing split named, not a generic Traefik debug loop
- [ ] A redeploy prescribed as the fix, and stated as required for every domain add, edit, or removal
- [ ] No suggestion to edit Traefik's dynamic configuration files by hand for a Compose service

Second run, "deploy this Vite app to Dokploy and give it a domain". With the skill, the
output should show all of:

- [ ] `host: true` set in both `server` and `preview` in the Vite config, with Bad Gateway named as the symptom it prevents
- [ ] The DNS record pointed at the server before the domain is added in Dokploy, with certificate issuance named as what breaks otherwise
- [ ] `Container Port` set on the domain rather than `Ports` under Advanced Settings
- [ ] Port `80` when the build publishes a directory through NGINX, rather than the app's dev port

Third run, "put our database password in Dokploy": the skill should reach for
`${{vault.<provider-name>.<ref>}}` against an external secret manager rather than
pasting the value into the environment editor.

## Recorded results

Run 2026-09-09 against `claude --plugin-dir plugins/dokploy` in a fresh working
directory, one query per session, `--output-format stream-json` inspected for a `Skill`
tool call. Only this skill existed in the plugin at the time, so these runs test whether
the description fires — not which sibling wins, which needs all five and is Task 8's job.

| Query | Expected | Observed |
|---|---|---|
| "My Dokploy domain returns 404." (positive 4) | fires | fired |
| "Bad Gateway right after a successful deploy." (positive 5) | fires | fired |
| "In our Dokploy app, only rebuild when the apps/web directory changes." (positive 10, with context) | fires | fired |
| "Only rebuild when the apps/web directory changes." (positive 10, verbatim) | fires | **did not fire** |
| "Deploy this app to Vercel." (negative 6) | does not fire | did not fire |
| "Deploy this to our Kubernetes cluster." (negative 7) | does not fire | did not fire |

The verbatim form of positive 10 is a real gap and is recorded rather than papered over.
It names no platform, no provider, and no product, so nothing in it distinguishes Dokploy
watch paths from a stale-build or CI-caching question. Adding "rebuild" or "watch" to the
description would buy that query at the cost of firing on every incremental-build
question in every repository, which is a worse trade. The same query fires as soon as one
word of Dokploy context is present. Treat it as a positive that depends on session
context, not on the description alone.

The remaining eight positives and five negatives are unrun. Nothing above should be
read as a rate.

### The five-way sibling matrix (Task 8)

Run 2026-09-10, one query per clean session, in an empty working directory outside this
repository — the isolation some of the earlier runs lacked. Both plugins were loaded, so
the cross-plugin rows had a real winner available to them rather than passing by nothing
firing:

```bash
claude -p "<query>" \
  --plugin-dir plugins/dokploy --plugin-dir plugins/docker-workbench \
  --setting-sources project --output-format stream-json --verbose
```

`--setting-sources project`, in a directory with no project settings, leaves only these
two plugins' skills in the lineup. The session `init` event listed all five dokploy
skills and all four docker-workbench skills, so every row had all nine to choose from.
Each row was judged on the `Skill` tool call in the JSON stream, not on the prose of the
answer. All eleven rows of the matrix matched expectation, so no description was changed.

| Query | Expected | Observed |
|---|---|---|
| "Deploy this Astro site to Dokploy" | fires | fired `dokploy:deploying-apps-to-dokploy` |
| "My Dokploy domain 404s after I changed it" | fires | fired `dokploy:deploying-apps-to-dokploy` |
| "Install Dokploy on a new VPS" | `operating-dokploy-servers` wins | fired `dokploy:operating-dokploy-servers`; this skill stayed out |
| "Deploy to Dokploy from GitHub Actions" | `automating-dokploy` wins | fired `dokploy:automating-dokploy`; this skill stayed out |
| "Write a Dockerfile for this app" | `docker-workbench:containerizing-apps` wins | fired `docker-workbench:containerizing-apps`; no dokploy skill fired |
| "Scan our images for CVEs" | `docker-workbench:securing-container-supply-chain` wins | fired `docker-workbench:securing-container-supply-chain`; no dokploy skill fired |

"Deploy to Dokploy from GitHub Actions" is the sharp one for this skill, because it opens
with the same verb and names the same product: the row turns entirely on the "for
triggering deploys from CI or scripting Dokploy, use automating-dokploy" clause at the end
of this description, and on the CI clause in the sibling's. It held. The 404 row confirms
the symptom-only phrasing still reaches this skill when a sibling that owns "the panel is
unreachable" is present in the lineup, which the earlier single-skill run could not test.
