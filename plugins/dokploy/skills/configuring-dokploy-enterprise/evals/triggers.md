# Trigger battery — configuring-dokploy-enterprise

Run each query in a clean session with only the description visible. Record fired / did
not fire.

Four sibling skills ship in this same plugin and every one of their descriptions
contains the word "dokploy", so the negatives below are the real test: they name the
sibling that should win instead. This skill's own content is entirely paid-tier and
documentation-derived — nothing in it was, or can be, observed against a running
instance — which makes the free/paid boundary the sharpest routing risk in the whole
battery, sharper than the ordinary sibling-collision risk the other four skills face.

## Should trigger

1. "Connect Dokploy to Entra ID."
2. "Set up SAML SSO for our Dokploy panel."
3. "Automatically deprovision users who leave."
4. "Who deployed to production last Tuesday?" *(audit logs)*
5. "Put our internal dashboard behind SSO login."
6. "Which Dokploy features need a licence?"
7. "Activate our licence key on the self-hosted instance."

Item 3 names no product feature by name — "deprovision" is SCIM vocabulary, but the
query itself could describe any identity system. Item 5 is the one most likely to be
misread as an application-configuration question (`deploying-apps-to-dokploy`'s
territory) rather than an identity one — the object being protected is "our internal
dashboard," which says nothing about Dokploy's own panel or SSO until "behind SSO
login" is read as Application Authentication specifically, not panel access. Item 6
tests whether the description answers a meta-question about itself rather than only
firing on feature-specific requests.

## Should not trigger (near misses)

1. "Force 2FA for every panel user." → `hardening-dokploy` (free tier)
2. "Restrict a contractor to one project's staging environment." → `hardening-dokploy` (free tier)
3. "Add a user to the org." → free-tier permissions, `operating-dokploy-servers`
4. "Set up SSO for our Svelte app hosted on Vercel." → not Dokploy at all
5. "Script role assignment from CI." → `automating-dokploy`

Items 1 and 2 are the pair this battery exists to catch, and 2 is the sharper of the
two. Item 1 fails if the description's own "2FA" absence isn't enough and something
fires on generic access-control language anyway.

Item 2 was, for one draft, an actual collision rather than a hypothetical one: this
skill's own description used to say "restrict permissions per project or environment,"
which is the free-tier capability by name, in a plugin where `hardening-dokploy`'s
description names neither roles nor scoping at all (and still doesn't — it wasn't
touched by this fix). On descriptions alone, this skill was the *only* one of the five
advertising a free feature as its own — item 2 would have failed the battery outright,
not narrowly. The fix was entirely on this skill's own description, in two places: the
"Use when" clause now says "define a custom role with permissions beyond
Owner/Admin/Member" (the paid capability, *defining*) instead of naming the free one,
and the trailing sentence now says explicitly "For free-tier access control — 2FA,
passkeys, the built-in Owner/Admin/Member roles, and scoping one of those roles to
particular projects or environments — use hardening-dokploy," disclaiming the free
capability by name rather than only naming the paid one. `hardening-dokploy`'s own
file states nothing new; an agent routing off either description alone now sees the
boundary from this skill's side, which is sufficient on its own. Item 2 stays in the
battery as a regression test for that fix, not a live failure — its vocabulary
("restrict," "one project," "one environment") is designed to probe whether the
boundary holds now that this description states it explicitly, not to catch a real gap
that's still open.

Item 3 depends on the same distinction as `hardening-dokploy`'s own "Set up SSO"
negative reversed: inviting a member with no custom role or automated provisioning
involved is ordinary panel administration, not this skill's SCIM or Custom Roles
content. Item 4 names a real host (Vercel) so the query itself, not an assumption about
it, is what rules this skill out — the application isn't running on Dokploy, so neither
panel SSO nor Application Authentication (which only gates apps Dokploy itself deploys)
applies; a Svelte app that *were* running on Dokploy behind a domain is exactly the
Application Authentication scenario this skill's own description claims, which is why
the negative needs the host named rather than left implicit. Item 5 is the internal
split every automation-adjacent skill in this plugin repeats: deciding what a custom
role should contain is this skill's; scripting the API call that assigns one is
`automating-dokploy`'s.

## A/B assertions

Run "restrict a contractor to one project's staging environment" with and without the
skill. With the skill, the output should show all of:

- [ ] Project Permissions (scoping the built-in Member role to one project and one
      environment) named as the free-tier answer, not a license requirement
- [ ] No claim that this needs an Enterprise license or a Custom Role, unless the user
      has already said the built-in Member permission categories aren't fine-grained
      enough
- [ ] If Custom Roles are mentioned at all, they're framed as *defining a new role*,
      distinct from *scoping an existing one*

Second run, "force 2FA for every panel user." With the skill, the output should show:

- [ ] No organization-wide "require 2FA" toggle claimed to exist
- [ ] 2FA and passkeys named as enrolled per user, not enforced by a setting
- [ ] Forcing SSO org-wide (Enterprise) named only as the adjacent, different lever that
      makes IdP-required MFA mandatory — not conflated with a 2FA toggle itself

Third run, "which Dokploy features need a licence?" With the skill, the output should
show all of:

- [ ] License activation, SSO, SCIM, custom roles, audit logs, whitelabeling, and
      Application Authentication named as requiring a license
- [ ] 2FA, passkeys, and the built-in Owner/Admin/Member roles (including their
      per-project/per-environment scoping) named as not requiring one

## Recorded results

The battery above was deferred from its own task: this skill did not exist on disk while
the other four skills' batteries were run, and a five-way sibling race with four of the
five present would have needed re-running once it joined them. The deferral is discharged
by the matrix below. The A/B assertion checkboxes above remain unrun — the matrix judged
which skill fired, not what the answer contained.

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
| "Wire Dokploy up to Okta" | fires | fired `dokploy:configuring-dokploy-enterprise`, read `references/sso-providers.md`, and opened by stating Okta is Enterprise-only before any setup steps |
| "Force 2FA on all panel users" | `hardening-dokploy` wins | fired `dokploy:hardening-dokploy`; this skill stayed out |
| "Restrict a contractor to one project's staging environment" | `hardening-dokploy` wins | fired `dokploy:hardening-dokploy`; this skill stayed out |
| "Is our Dokploy panel secure?" | `hardening-dokploy` wins | fired `dokploy:hardening-dokploy`; this skill stayed out |
| "Install Dokploy on a new VPS" | `operating-dokploy-servers` wins | fired `dokploy:operating-dokploy-servers`; this skill stayed out |

The three access-control rows are the whole point of this battery, and this skill stayed
out of all three. "Restrict a contractor to one project's staging environment" is the one
the plan expected to land here — custom roles are the paid answer to a request phrased
that way, and this description names them — and it went to `hardening-dokploy` instead,
which is the correct edition boundary: per-project and per-environment scoping of a
built-in Member role needs no licence. The "For free-tier access control — 2FA, passkeys,
the built-in Owner/Admin/Member roles, and scoping one of those roles to particular
projects or environments — use hardening-dokploy" clause at the end of this description is
what bought all three rows, and it earns its length.

The positive row confirms the other direction: naming an identity provider reaches this
skill, and the answer led with the licence requirement rather than walking someone through
a setup they cannot complete.
