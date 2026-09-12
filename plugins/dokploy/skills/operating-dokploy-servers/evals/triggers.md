# Trigger battery — operating-dokploy-servers

Run each query in a clean session with only the description visible. Record fired / did
not fire.

Four sibling skills ship in this same plugin and every one of their
descriptions contains the word "dokploy", so the negatives below are the real test: they
name the sibling that should win instead.

## Should trigger

1. "Install Dokploy on a fresh Ubuntu VPS."
2. "Upgrade our Dokploy to the latest release."
3. "Add a second server for builds."
4. "Back up Dokploy itself, not just the databases."
5. "Restore our Dokploy instance onto a new VPS."
6. "The Dokploy panel is unreachable but the apps are up." *(symptom only)*
7. "Deployments queue and never start." *(symptom only)*
8. "Docker ran out of address space on the host." *(symptom only — network pools)*
9. "A volume mount is empty after redeploy." *(symptom only)*
10. "Send deployment failures to Slack."

Items 6–9 are the ones a weak description misses, because each names a symptom and no
feature: 6 is the panel-versus-apps split (the docs describe `dokploy`, `dokploy-postgres`,
and `dokploy-traefik` as three separate containers, and their documented
connection-failure case is specific to `dokploy` losing its route to `dokploy-postgres`,
not to app containers or Traefik), 7 is per-server build concurrency defaulting to 1 with
same-service builds always serialized, 8 is Docker's
default address-pool exhaustion once roughly 30 networks exist, and 9 is a file mounted
from the repository being wiped by AutoDeploy's `git clone` on every redeploy. Item 10 is
the one most likely to be misrouted to `automating-dokploy`, since it names a delivery
mechanism (Slack) rather than a panel feature — the split is that this skill owns which
provider and action to configure in the panel, and `automating-dokploy` owns scripting
around deploys, not notification setup.

## Should not trigger (near misses)

1. "Install Docker on this VPS." → `docker-workbench:managing-container-runtimes`
2. "Harden this Dokploy host." → `hardening-dokploy`
3. "My app's domain 404s." → `deploying-apps-to-dokploy`
4. "Script a nightly backup from CI." → `automating-dokploy`
5. "Set up SCIM." → `configuring-dokploy-enterprise`
6. "Restore a Postgres dump into my local dev database." → not Dokploy
7. "Back up my VPS to S3 and test restoring the snapshot." → not Dokploy

Item 6 is the sharpest negative: it shares two words with this skill's core scenario
("restore" and "database"), and firing on it would mean the description keys off backup
vocabulary rather than off Dokploy. Item 3 is the sharpest internal one — a 404 is exactly
the kind of "the panel/app is broken" report this skill's symptom list is built to catch,
but the fix lives in the application's own domain configuration, which
`deploying-apps-to-dokploy` already owns end to end. Item 4 depends on the same
distinction as positive 10: a *scripted* nightly backup is a CI/API scenario that
`automating-dokploy` owns, while configuring the schedule and destination inside the panel
is this skill's job. Item 7 is the one negative that isn't a sibling redirect at all — it
names generic server-operations vocabulary (VPS, S3, snapshot, restore) that overlaps
almost every noun this skill's description uses, but never says Dokploy, panel, or
anything Dokploy-specific. It exists because every other negative here routes to a named
sibling by testing a *specific* Dokploy feature that belongs elsewhere; this one instead
tests whether the description over-fires on bare infrastructure-ops language with no
Dokploy signal at all — the failure mode none of items 1–6 can catch, since they all
contain the word "Dokploy" themselves.

## A/B assertions

Run "back up Dokploy itself, not just the databases" with and without the skill. With the
skill, the output should show all of:

- [ ] `Web Server → Backups` named as a distinct panel feature from per-database backups
- [ ] `dokploy-postgres` and `/etc/dokploy` named as what gets archived, zipped to an S3
      destination
- [ ] No suggestion to use the per-database Backup tab for this

Second run, "restore our Dokploy instance onto a new VPS." With the skill, the output
should show all of:

- [ ] The restore named as destructive — it replaces `/etc/dokploy`, drops
      `dokploy-postgres`, and disconnects existing database users
- [ ] All four post-restore follow-ups named: server IP, git provider configuration that
      referenced an IP, DNS records, and traefik.me domains
- [ ] No claim that restoring is safe to run against a live, already-correct instance
      without a plan for the disconnect

Third run, "deployments queue and never start." With the skill, the output should show:

- [ ] Per-server build concurrency named, defaulting to 1
- [ ] Builds of the same application or Compose service named as always serialized, even
      at higher concurrency — not a bug, so raising concurrency alone will not unblock a
      queue of the same service's builds

## Recorded results

The battery above was deferred from its own task: a prior run against
`deploying-apps-to-dokploy` alone (see that skill's `evals/triggers.md`) cost real model
calls per query, and running this one before all five skills coexisted in the plugin would
have needed re-running anyway. The deferral is discharged by the matrix below, which
covers this skill's routing against all four siblings. The A/B assertion checkboxes above
remain unrun — the matrix judged which skill fired, not what the answer contained.

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
| "Install Dokploy on a new VPS" | fires | fired `dokploy:operating-dokploy-servers` |
| "Restore Dokploy onto a new server" | fires | fired `dokploy:operating-dokploy-servers`, read `references/backups-and-restore.md`, and led with the panel-backup prerequisite rather than a per-database backup |
| "Deploy this Astro site to Dokploy" | `deploying-apps-to-dokploy` wins | fired `dokploy:deploying-apps-to-dokploy`; this skill stayed out |
| "Is our Dokploy panel secure?" | `hardening-dokploy` wins | fired `dokploy:hardening-dokploy`; this skill stayed out |
| "Deploy to Dokploy from GitHub Actions" | `automating-dokploy` wins | fired `dokploy:automating-dokploy`; this skill stayed out |

"Is our Dokploy panel secure?" is the row that matters here, because this skill's
description owns the panel outright — "the Dokploy host and control panel itself" — and
the query names it. The word "secure" carried it to the sibling, which is the split the
two descriptions are written to produce.
