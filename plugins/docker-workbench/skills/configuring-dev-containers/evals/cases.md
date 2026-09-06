# Task Cases

Run each prompt with and without the skill, clean context per run. Grade against the
assertions with quoted evidence from the output. No benefit of the doubt: an
assertion passes only if the artifact demonstrably satisfies it.

Every case is anchored to a failure observed in unaided baseline runs — the note
under each says which.

## Case 1: Node + Postgres

> "Set up a dev container for this Express app. It needs Postgres 16 and we all need
> the same Node version."

Assertions:
- [ ] Uses `dockerComposeFile` + `service`, not a single container with Postgres
      installed via `apt` or a Feature
- [ ] The dev container service has `command: sleep infinity`
- [ ] `workspaceFolder` is set explicitly (Compose defaults it to `/`)
- [ ] Postgres data is on a named volume
- [ ] Extensions/settings appear under `customizations.vscode`, never top level
- [ ] Node version is pinned in the image tag or the Feature options
- [ ] `postCreateCommand` installs dependencies and is not a long-running process
- [ ] Response states how to rebuild after edits

*Baseline failures: single container with Postgres crammed in; missing `sleep
infinity` so the container exits; `workspaceFolder` omitted.*

## Case 2: Repair a broken config

Give the model this file and say "this won't build, fix it":

```jsonc
{
  "name": "Broken",
  "image": "mcr.microsoft.com/vscode/devcontainers/typescript-node",
  "features": {
    "ghcr.io/devcontainers/features/node": {},
    "ghcr.io/devcontainers/features/postgres:1": {}
  },
  "extensions": ["dbaeumer.vscode-eslint"],
  "settings": { "editor.formatOnSave": true },
  "postCreateCommand": "npm install && npm start"
}
```

Assertions:
- [ ] Identifies `features/postgres` as nonexistent and moves Postgres to Compose
      (or removes it), rather than leaving it or inventing options for it
- [ ] Moves `extensions` and `settings` under `customizations.vscode`
- [ ] Corrects the deprecated `mcr.microsoft.com/vscode/devcontainers/` path
- [ ] Pins the image tag and the Feature version
- [ ] Removes `npm start` from `postCreateCommand`, explaining that it must exit
- [ ] Names each fix rather than silently emitting a rewritten file

*Baseline failures: the deprecated image path and nonexistent Feature pass through
untouched; top-level `extensions` is often preserved because older training data
shows it.*

## Case 3: Symptom with no config shown

> "Our dev container works fine for me but a teammate on Linux says every file the
> container writes ends up owned by root. What's going on?"

Assertions:
- [ ] Names the cause: the container runs as root over a bind mount
- [ ] Recommends `remoteUser` (and `user:` on the service if Compose)
- [ ] Mentions `updateRemoteUserUID` or the fact that first-party images ship a
      non-root user
- [ ] Notes that existing root-owned files need a host-side `chown` — config changes
      are not retroactive
- [ ] Does not produce a whole new devcontainer.json when the question was diagnostic

*Baseline failure: correct diagnosis, but omits that already-written files stay
root-owned, so the user reports it "didn't work" after rebuilding.*

## Case 4: Scope boundary

> "Write me a Dockerfile for deploying this Flask app to production."

Assertions:
- [ ] Produces a production Dockerfile
- [ ] Does **not** create a `.devcontainer` folder or devcontainer.json
- [ ] At most one brief offer to also set up a dev container, if any

*Guards against over-application. A skill that turns every Docker request into a dev
container request is worse than no skill.*

## Case 5: Verification discipline

> "Add a dev container with Python 3.12 and the Azure CLI."

Assertions:
- [ ] Feature ID is exactly `ghcr.io/devcontainers/features/azure-cli:1`
- [ ] Runs the validator, or states plainly that it could not
- [ ] Does not claim the config was tested or "verified working" if no build ran

*Baseline failure: unaided runs assert the config "should work now" without any
check. The distinction between validated and unvalidated is the point of the verify
step.*

## Grading

Report per case: assertions passed / total, for skill and no-skill runs, with a quote
backing each judgment.

Run each case three times. Inconsistent results across reps indicate ambiguous
wording — fix with one concrete example or a tighter scope clause, not another rule.
An edit that raises the average but widens the spread is a regression.
