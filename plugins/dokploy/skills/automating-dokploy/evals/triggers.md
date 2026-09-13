# Trigger battery — automating-dokploy

Run each query in a clean session with only the description visible. Record fired / did
not fire.

Four sibling skills ship in this same plugin and every one of their
descriptions contains the word "dokploy", so the negatives below are the real test: they
name the sibling that should win instead.

## Should trigger

1. "Deploy to Dokploy from GitHub Actions."
2. "What's the API call to redeploy an app?"
3. "Authenticate the Dokploy CLI in CI."
4. "Script creating a project and three services."
5. "Set up a deploy webhook from GitLab."
6. "My webhook fires but nothing deploys and the log says Branch Not Match." *(symptom only)*
7. "Is there a CLI command for SSO settings?" *(the docs imply no; the answer is yes)*
8. "Add a nightly scheduled job."
9. "How do I list every app across all projects?"

Items 6, 7, and 9 are the ones a weak description misses. 6 names a symptom and no
feature — the fix is a branch-name mismatch between what's configured in Dokploy and
what was pushed, not a webhook-delivery problem. 7 is the sharpest positive in the whole
battery: the published CLI docs describe five command groups and none of them is `sso`,
so a description that only paraphrases the docs would answer "no" — the correct answer is
`dokploy sso`, an eleven-action group this skill's own verification confirmed on the
installed CLI. 9 never says "CLI" or "API"; it reads as a plain question about applications,
and only the phrase "across all projects" — which nothing in the panel UI answers in one
place — points at scripting `project.all` plus `application.all` rather than clicking
through project pages one at a time.

## Should not trigger (near misses)

1. "Which build type should this app use?" → `deploying-apps-to-dokploy`
2. "How do I add a remote server?" → `operating-dokploy-servers`
3. "Should API tokens expire?" → `hardening-dokploy`
4. "Write a GitHub Action to run my Jest suite." → CI, but not Dokploy
5. "Test this REST API and assert on the response." → `bruno:testing-bruno-apis`

Items 4 and 5 are the sharpest: firing on either would mean the description keys off "CI"
or "API" rather than off Dokploy. Item 4 names a CI platform and a testing framework with
no product this skill owns anywhere in it — the trap is that this skill's own description
says "CI pipelines" and "script," which is exactly the vocabulary a Jest-in-GitHub-Actions
request also uses. Item 5 names "REST API" and "response," which overlaps this skill's own
"call its API" phrase almost word for word; the only thing missing is Dokploy itself, and
`bruno:testing-bruno-apis` is the skill built for exercising an arbitrary REST API, Dokploy's
or anyone else's. Item 3 is the sharpest internal-plugin one: token expiration is an API/CLI
fact this skill's own `api-recipes.md` touches in passing (issue one token per integration,
set an expiration), but *should tokens expire* is a policy question — `hardening-dokploy`
owns the checklist that answers it, and this skill only owns how to mint and use one.

## A/B assertions

*(Not run in the paired with/without form described below — see "Recorded results" for a
single-condition run of assertions 1 and 3, which matched what's asserted here.)*

Run "my webhook fires but nothing deploys and the log says Branch Not Match" with and
without the skill. With the skill, the output should show all of:

- [ ] Branch Not Match named as a mismatch between the branch pushed and the branch
      configured on the Dokploy application, not a delivery or signature failure
- [ ] No suggestion to inspect Traefik, the domain configuration, or DNS for this symptom

Second run, "what's the API call to redeploy an app?" *(not run)* With the skill, the
output should show all of:

- [ ] The action name confirmed against `dokploy application --help` rather than derived —
      `redeploy` on the CLI is `/api/application.redeploy` — not a guessed or invented
      endpoint
- [ ] `dokploy application --help` offered as how to confirm the exact action name, since
      `redeploy` and `deploy` are both real, distinct actions on this resource

Third run, "is there a CLI command for SSO settings?" With the skill, the output should
show:

- [ ] A direct "yes," naming the `sso` resource group
- [ ] No reasoning from the published docs' five-group CLI page as if it were the whole
      surface

## Recorded results

Run 2026-09-09 against `claude --plugin-dir plugins/dokploy` in this repository's own
working directory, one query per session, `--output-format stream-json` inspected for a
`Skill` tool call. Only `deploying-apps-to-dokploy`, `operating-dokploy-servers`, and this
skill existed in the plugin at the time, so these runs test whether the description fires
— not which of all five siblings wins, which needs `hardening-dokploy` and
`configuring-dokploy-enterprise` to exist too and is Task 8's job.

| Query | Expected | Observed |
|---|---|---|
| "My webhook fires but nothing deploys and the log says Branch Not Match." (positive 6) | fires | fired, and answered from the skill's own webhook content |
| "Is there a CLI command for SSO settings?" (positive 7) | fires | fired, read `references/cli-command-map.md`, answered "Yes — `dokploy sso`" with the real action list |
| "How do I list every app across all projects?" (positive 9) | fires | fired, answered with `dokploy project all` / `/api/project.all` and the correct nesting (no separate "list all applications" endpoint) |
| "Write a GitHub Action to run my Jest suite." (negative 4) | does not fire | did not fire — no `Skill` tool call at all; the session instead read this repo's own `package.json` and `.github/workflows/test.yml` |
| "Test this REST API and assert on the response." (negative 5) | does not fire | did not fire — the session asked which API and what assertions, with no Dokploy content |
| "Should API tokens expire?" (negative 3) | does not fire (`hardening-dokploy` doesn't exist yet to fire instead) | did not fire — answered as generic token-hygiene advice, no Dokploy content |

Six for six. The two sharpest negatives (4 and 5) held despite this skill's own
description using "CI," "script," and "call its API" — the vocabulary the task brief
flagged as the risk. The remaining six positives and two negatives are unrun; sampling
more would cost real model calls per query for a rate this file already says not to
read into six data points. Full sibling-routing — whether `hardening-dokploy` wins
negative 3, or `deploying-apps-to-dokploy`/`operating-dokploy-servers` win 1 and 2 — needs
all five skills present and is deferred to Task 8, the same call
`operating-dokploy-servers` made for its own battery. The deferral is discharged by the
matrix below.

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
| "Deploy to Dokploy from GitHub Actions" | fires | fired `dokploy:automating-dokploy`, read `references/api-recipes.md`, and answered with the corrected workflow — the docs' own example mixes `uses:` and `run:` in one step |
| "Deploy this Astro site to Dokploy" | `deploying-apps-to-dokploy` wins | fired `dokploy:deploying-apps-to-dokploy`; this skill stayed out |
| "My Dokploy domain 404s after I changed it" | `deploying-apps-to-dokploy` wins | fired `dokploy:deploying-apps-to-dokploy`; this skill stayed out |
| "Install Dokploy on a new VPS" | `operating-dokploy-servers` wins | fired `dokploy:operating-dokploy-servers`; this skill stayed out |
| "Restore Dokploy onto a new server" | `operating-dokploy-servers` wins | fired `dokploy:operating-dokploy-servers`; this skill stayed out |

This is the two-sided test the six rows above could not run. "Deploy to Dokploy from
GitHub Actions" reaches this skill even though `deploying-apps-to-dokploy` opens with
"Deploys and configures applications on a self-hosted Dokploy PaaS"; "Deploy this Astro
site to Dokploy" reaches that sibling even though this description names deploying from a
pipeline. Neither over-fires on the other's shape, so the "for deciding what a setting
should be rather than how to set it" clause is doing its job in both directions.
