---
name: configuring-dev-containers
description: Sets up, configures, and debugs development containers — devcontainer.json, Features, lifecycle commands, Docker Compose setups, and the dev container CLI. Use when the user wants to containerize a dev environment, add or fix a .devcontainer folder, choose a base image or Feature, get "Reopen in Container" or Codespaces working, or debug a container that fails to build, exits immediately, is missing tools, writes root-owned files, or won't forward a port. Also use when the user describes the symptom without naming dev containers — "works on my machine", "new hires lose two days to setup", "pin the toolchain for the whole team", "everyone needs the same Node and Postgres versions".
license: MIT
---

# Configuring Dev Containers

Produce a `.devcontainer/` configuration that builds on the first try and gives every contributor the same toolchain. The spec is at [containers.dev](https://containers.dev); the VS Code implementation is the Dev Containers extension, and the same files drive GitHub Codespaces and the `devcontainer` CLI.

Done means: the config builds, the expected tools are on `PATH` inside the container, and the user knows the one command to rebuild after an edit.

## Start here: pick the base

Ask what the project needs to run, then pick exactly one base. Every config has `image`, `build.dockerfile`, or `dockerComposeFile` — never two.

| Situation | Base | Why |
|---|---|---|
| One language or runtime, no external services | `image` + `features` | Fastest startup, no build step, cache-friendly. Start here by default. |
| Needs system packages, a compiled tool, or a custom `apt` set | `build.dockerfile` | Layers are cached, so rebuilds are fast. Runs *before* the workspace is mounted. |
| Needs a database, queue, or any second service | `dockerComposeFile` + `service` | The only supported multi-container path. |

Prefer an existing image plus Features over a hand-written Dockerfile. Writing `RUN apt-get install nodejs` when `ghcr.io/devcontainers/features/node:1` exists costs build time and misses the version-pinning the Feature does for you.

## The canonical config

Write `.devcontainer/devcontainer.json` in this shape. It is JSONC — comments are legal.

```jsonc
{
  "name": "My Project",
  "image": "mcr.microsoft.com/devcontainers/typescript-node:1-22-bookworm",

  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },

  "forwardPorts": [3000],
  "portsAttributes": {
    "3000": { "label": "Web app", "onAutoForward": "notify" }
  },

  "postCreateCommand": "npm ci",

  "customizations": {
    "vscode": {
      "extensions": ["dbaeumer.vscode-eslint"],
      "settings": { "editor.formatOnSave": true }
    }
  },

  "remoteUser": "node"
}
```

Rules that make it build:

- Pin the Feature major version with `:1`. Unpinned IDs resolve to `latest` and break silently on a major bump.
- Pin the image tag (`:1-22-bookworm`, not bare or `:latest`) so a rebuild six months from now produces the same environment.
- Every VS Code extension and setting goes under `customizations.vscode`. Top-level `extensions` and `settings` keys are from the pre-2022 schema and are ignored now.
- Base images live at `mcr.microsoft.com/devcontainers/<stack>`. The older `mcr.microsoft.com/vscode/devcontainers/<stack>` path is deprecated.
- Use only real Feature IDs. `references/features.md` has the full first-party list — check it rather than guessing, since a plausible-looking ID that doesn't exist fails the build with an unhelpful manifest error.

## Lifecycle commands

Choosing the wrong hook is the most common functional bug. Order of execution, first to last:

| Property | Runs | Use it for |
|---|---|---|
| `initializeCommand` | On the **host**, before the container exists | Host-side prep only — creating a `.env`, checking a mount path. Never container setup. |
| `onCreateCommand` | In container, once at creation | Setup that can be baked into a prebuilt image; no user secrets available. |
| `updateContentCommand` | In container, after `onCreate`, when source updates | Dependency installs that prebuilds should refresh. |
| `postCreateCommand` | In container, once, after the workspace is mounted | The default choice: `npm ci`, `pip install -r requirements.txt`, `bundle install`. |
| `postStartCommand` | Every container start | Starting a background service, re-seeding scratch state. |
| `postAttachCommand` | Every time a tool attaches | Per-session shell niceties. |

Three constraints:

- **The command must exit.** A long-running server in `postCreateCommand` hangs container creation forever. Start servers from a task or terminal instead.
- **A failure stops the chain.** If `postCreateCommand` fails, `postStartCommand` and everything after it are skipped. Chain with `&&` only when a later step truly depends on an earlier one.
- **String form goes through `/bin/sh`; array form does not.** Use the string form when you need `&&`, globs, or `$VAR`. Version managers like nvm need an interactive shell: `"bash -i -c 'nvm install --lts'"`.

## Rebuilding

Editing any file in `.devcontainer/` does nothing until the container is rebuilt — tell the user this explicitly, because a reload is not enough. In VS Code: **Dev Containers: Rebuild Container** from the Command Palette. From the CLI: `devcontainer up --workspace-folder . --remove-existing-container`.

## Verify before reporting done

Never hand over a devcontainer.json that has not been checked. In order:

1. If you can execute code, run `python3 scripts/validate_devcontainer.py .devcontainer/devcontainer.json`. It catches the deprecated schema keys, unknown Feature IDs, missing/duplicate bases, and non-exiting lifecycle commands. Otherwise walk the checklist in `references/troubleshooting.md`.
2. If Docker is available, actually build it: `devcontainer build --workspace-folder .` (install with `npm install -g @devcontainers/cli`). A config that has never been built is a guess.
3. State which of these you ran. If you could not build, say so rather than implying the config is tested.

## Where to look

- `references/features.md` — the canonical first-party Feature and image IDs, common options, and install ordering. Read it whenever you are about to write a `features` block or choose an image.
- `references/json-reference.md` — the full property tables, `${...}` variables, port attributes, and host requirements. Read it for any property not shown above.
- `references/compose-and-advanced.md` — Docker Compose wiring, Docker-in-Docker, non-root users, named volumes for `node_modules`, secrets, prebuilt images, and CI. Read it when the answer involves a second service, permissions, disk performance, or publishing an image.
- `references/troubleshooting.md` — symptom-to-cause table. Read it first whenever the user reports a container that is already failing.

Starter configs live in `assets/`: `starter-node.jsonc`, `starter-python.jsonc`, `starter-go.jsonc`, and the pair `starter-compose-postgres.jsonc` + `starter-compose-postgres.yml`. Copy one and edit it rather than writing from a blank file; each is already correct on the points above.

## Gotchas

Environment facts that defy a reasonable guess:

- A Dockerfile runs **before** the workspace is mounted, so it cannot read `package.json`, lockfiles, or anything else in the repo. Workspace-dependent installs belong in `postCreateCommand`.
- Under Docker Compose the service must be given a command that stays alive (`sleep infinity`), or the container exits the moment its entrypoint finishes.
- `workspaceFolder` and `workspaceMount` must be set together for image and Dockerfile bases. Setting one alone silently mounts to the wrong place.
- On Linux, files a root container writes into a bind mount are root-owned on the host. Set `remoteUser` to a non-root user; the prebuilt images ship one (`node`, `vscode`).
- On macOS and Windows, bind-mounted `node_modules` and `.venv` are slow enough to notice. `references/compose-and-advanced.md` covers the named-volume fix.
- Alpine images work, but some VS Code extensions with native code fail on musl. Prefer the Debian/Ubuntu variants unless image size is the binding constraint.
- Secrets never go in `devcontainer.json` — it is committed. Pull from the host with `"${localEnv:MY_TOKEN}"`.

## Not this skill

Attaching to an already-running container that has no config, or writing a production `Dockerfile`, are different tasks — a dev container optimizes for the inner loop (tools, debuggers, shell), a production image for a small runtime surface. Say so and handle the actual request rather than producing a devcontainer.json.
