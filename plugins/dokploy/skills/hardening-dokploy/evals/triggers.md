# Trigger battery — hardening-dokploy

Run each query in a clean session with only the description visible. Record fired / did
not fire.

Four sibling skills ship in this same plugin and every one of their descriptions
contains the word "dokploy", so the negatives below are the real test: they name the
sibling that should win instead. Two more negatives point outside the plugin entirely,
at the collision the spec calls the sharpest in the whole design: this skill's own
source guide contains generic Docker hardening advice that `docker-workbench` already
owns.

## Should trigger

1. "Is our Dokploy instance secure?"
2. "Harden this before we put student data on it."
3. "Review our Dokploy exposure for SOC 2."
4. "Should the panel be on the public internet?"
5. "Our API tokens never expire." *(symptom only)*
6. "Someone left the org but still has panel access." *(symptom only)*
7. "Docker containers are reachable despite UFW rules." *(symptom only — the ufw-docker bypass)*
8. "Add HSTS and rate limiting to our Traefik."
9. "Move these environment variables into Vault."

Items 5–7 are the ones a weak description misses, because each names a symptom and no
control by that name: 5 is API/CLI tokens created with no expiration, which the guide
states should always be set; 6 is the absence of SCIM auto-deprovisioning (or, without
an IdP, no organization-wide way to force 2FA, so an offboarded member's access is a
manual step someone has to remember); 7 is Docker writing directly to `iptables` and
bypassing UFW, the exact failure `ufw-docker` exists to close. Item 9 is the one most
likely to be misrouted to `deploying-apps-to-dokploy`, since that skill's own
`providers-and-domains.md` documents the `${{vault.<provider-name>.<ref>}}` reference
syntax — the split is that the sibling owns writing the reference into an environment
variable, and this skill owns whether a provider exists, how it authenticates, and who
can use it.

## Should not trigger (near misses)

1. "Scan this image for CVEs." → `docker-workbench:securing-container-supply-chain`
2. "Sign our images with cosign." → `docker-workbench:securing-container-supply-chain`
3. "Review this Express route for injection." → `security:reviewing-code-security`
4. "Write a hardened Dockerfile." → `docker-workbench:containerizing-apps`
5. "Install Dokploy." → `operating-dokploy-servers`
6. "Set up SSO." → `configuring-dokploy-enterprise`
7. "Harden this Ubuntu box for our internal wiki — no Dokploy anywhere." → not Dokploy at all

Items 1 and 2 are the sharpest pair, because this skill's own source guide (the
Production Hardening Guide) shares a "shared responsibility" table with the exact
vocabulary those queries use — registries, pinned tags, image provenance — and the
guide's Docker Engine section sits one page away. Firing on either would mean the
description keys off "image" and "vulnerability" rather than off the settings a Dokploy
host itself needs (`daemon.json`, socket exposure, `no-new-privileges`). Item 4 is the
companion case in the opposite direction: writing a new Dockerfile is
`containerizing-apps`'s job start to finish, even though this skill's checklist mentions
pinned tags and `no-new-privileges` as settings a Dokploy host requires. Item 7 is the
one negative that isn't a sibling or cross-plugin redirect: it names almost every noun
this skill's description uses — SSH, Fail2Ban, UFW, firewall — but never Dokploy, the
panel, or Traefik, and tests whether the description over-fires on generic
host-hardening language alone. Keeping it despite naming no winning skill is
deliberate, not an oversight: every other negative above has a named sibling to fall
back on if the description over-fires, and this is the one case that doesn't, which
makes it the sharpest test of over-firing in the set.

## A/B assertions

Run "Docker containers are reachable despite UFW rules" with and without the skill. With
the skill, the output should show all of:

- [x] Docker named as writing directly to `iptables`, bypassing UFW rather than a UFW
      misconfiguration
- [x] `ufw-docker` named as the fix, not a suggestion to reconfigure UFW's own rules
- [x] No claim that closing the port in UFW alone resolves it

Confirmed in the "with the skill" condition recorded below (positive 7); the "without"
half of this A/B pair was not run.

Second run, "scan this image for CVEs." With the skill, the output should show:

- [ ] No CVE scanning, triage, SBOM, or signing content from this skill
- [ ] A pointer to `docker-workbench:securing-container-supply-chain` for the actual task

Third run, "should the panel be on the public internet?" With the skill, the output
should show all of:

- [ ] Port 3000 named as the panel's own port, and that it should stay closed to the
      public internet
- [ ] Traefik on a domain, or a VPN, named as the two ways to reach it instead
- [ ] No claim that Dokploy's built-in Monitoring will show an attacker who reaches the
      panel directly — that page is a Cloud-only feature on self-hosted, per
      `operating-dokploy-servers`

## Recorded results

Run 2026-09-09 against `claude --plugin-dir plugins/dokploy` in this repository's own
working directory, one query per session, `--output-format stream-json` inspected for a
`Skill` tool call. All five skills named in this plugin's design exist on disk by the
time this battery ran except `configuring-dokploy-enterprise`, so these runs test
whether the description fires and, for the two image-scanning negatives the task
specifically calls out, whether the sharpest collision holds — not the full five-way
sibling race, which is Task 8's job.

| Query | Expected | Observed |
|---|---|---|
| "Scan this image for CVEs." (negative 1) | does not fire | did not fire — read "image" literally as a picture and asked for an attachment, so this run doesn't exercise the container-image collision at all |
| "Sign our images with cosign." (negative 2) | does not fire | did not fire — no `Skill` tool call; the session reasoned about the repo instead (see caveat below) and explicitly named `securing-container-supply-chain`, unprompted, as "the right home for cosign signing guidance rather than hardening-dokploy" |
| "Docker containers are reachable despite UFW rules." (positive 7) | fires | fired `dokploy:hardening-dokploy`, and answered with the `iptables`-bypass explanation and the exact `ufw-docker` install commands from the skill |
| "Is our Dokploy instance secure?" (positive 1) | fires | fired `dokploy:hardening-dokploy`, loaded the checklist, and asked for host access or panel-by-panel answers to actually evaluate it rather than asserting a status it couldn't check |
| "Set up SSO." (negative 6) | does not fire | did not fire; the session found `configuring-dokploy-enterprise` named in this plugin's own README roadmap and reported that it's the intended skill but doesn't exist on disk yet |

Three for three on firing, and both image-scanning negatives held, but read the first
two rows with a caveat: **these sessions ran with this repository itself as the working
directory**, mid-task, with the very files this task was writing sitting uncommitted on
disk. "Scan this image for CVEs" never reached a routing decision at all — it was read
as a request to scan an attached photo. "Sign our images with cosign" triggered
repo-aware reasoning ("this repo doesn't build container images... I see
`hardening-dokploy` is new/untracked... there's already a `securing-container-supply-chain`
skill") rather than a plain routing decision a user's own project would produce. The
outcome (no `hardening-dokploy` firing, correct sibling named) is the right answer
either way, but it is not a clean test of the description in isolation the way
positives 1 and 7 are. The remaining six positives and five negatives are unrun.
Nothing above should be read as a rate.

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
| "Is our Dokploy panel secure?" | fires | fired `dokploy:hardening-dokploy`, beating `operating-dokploy-servers`, whose description owns the panel |
| "Force 2FA on all panel users" | fires, not `configuring-dokploy-enterprise` | fired `dokploy:hardening-dokploy`; the enterprise sibling stayed out, and the answer said there is no organization-wide 2FA toggle on the free tier and named forcing SSO as the separate Enterprise lever |
| "Restrict a contractor to one project's staging environment" | fires, not `configuring-dokploy-enterprise` | fired `dokploy:hardening-dokploy`; answered with a scoped **Member**, named Admin as bypassing scoping, and reached per-integration expiring tokens as the API/CLI half |
| "Wire Dokploy up to Okta" | `configuring-dokploy-enterprise` wins | fired `dokploy:configuring-dokploy-enterprise`; this skill stayed out |
| "Write a Dockerfile for this app" | `docker-workbench:containerizing-apps` wins | fired `docker-workbench:containerizing-apps`; no dokploy skill fired |
| "Scan our images for CVEs" | `docker-workbench:securing-container-supply-chain` wins | fired `docker-workbench:securing-container-supply-chain`; no dokploy skill fired |

Two things resolve here that the 2026-09-09 rows above left open.

**The image-scanning negative is now genuinely exercised.** The earlier run of "Scan this
image for CVEs" never reached a routing decision — the session read "image" as a picture
and asked for an attachment — and the cosign run produced repo-aware reasoning rather than
a routing decision, because both ran with this repository as the working directory. Run in
an empty directory with `docker-workbench` loaded, "Scan our images for CVEs" routes
straight to `docker-workbench:securing-container-supply-chain` with no
`hardening-dokploy` firing. The caveat attached to negatives 1 and 2 above is discharged;
the collision the spec called the sharpest in the design holds.

**Free-tier access control stays here, both times it was contested.** The two rows that
name a control the enterprise sibling also discusses — forcing 2FA, and scoping someone
to one project's environment — both landed on this skill. The plan originally expected the
scoping row to go to `configuring-dokploy-enterprise`, since custom roles are the paid
answer to "restrict a contractor"; the free per-project scoping clause in this skill's
own description, and the matching "For free-tier access control ... use hardening-dokploy"
clause at the end of the sibling's, held it here instead. The answer it produced was a
worked scoped-Member walkthrough, which is why the single clause at `SKILL.md`'s
least-privilege paragraph was left a clause rather than expanded into a section.
