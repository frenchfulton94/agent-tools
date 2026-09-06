# Troubleshooting

Contents:
- [Getting the log](#getting-the-log)
- [Build failures](#build-failures)
- [Container starts then exits](#container-starts-then-exits)
- [Tools missing after build](#tools-missing-after-build)
- [File permission problems](#file-permission-problems)
- [Ports not reachable](#ports-not-reachable)
- [Lifecycle command problems](#lifecycle-command-problems)
- [Extensions and editor problems](#extensions-and-editor-problems)
- [Slowness](#slowness)
- [Platform-specific issues](#platform-specific-issues)
- [Manual review checklist](#manual-review-checklist)

## Getting the log

Ask for the log before theorizing. Most dev container failures name their cause in
the last twenty lines.

- VS Code: **Dev Containers: Show Container Log** from the Command Palette.
- On a failed build the dialog offers **Open Folder Locally**; the log appears after
  the window reloads.
- Cloned-in-volume failures offer **Reopen in Recovery Container**, a minimal
  container where the config can be edited.
- CLI: `devcontainer up --workspace-folder .` prints everything to stdout.
- To see the config after Features and image metadata merge:
  `devcontainer read-configuration --workspace-folder .`

## Build failures

| Symptom | Cause | Fix |
|---|---|---|
| `manifest unknown` / `not found` on a Feature | Feature ID does not exist | Check the list in `features.md`. Community Features need their full publisher path |
| `manifest unknown` on the image | Bad tag, or the deprecated `mcr.microsoft.com/vscode/devcontainers/*` path | Use `mcr.microsoft.com/devcontainers/*` and a tag that exists |
| Dockerfile `COPY` fails on a repo file | `build.context` too narrow | Set `"build": { "context": ".." }` to reach the repo root |
| Dockerfile cannot find `package.json` | The Dockerfile runs before the workspace is mounted | Move the install to `postCreateCommand` |
| `exec format error` | Image is amd64-only, host is Apple Silicon | Prefer a multi-arch image; otherwise `"runArgs": ["--platform=linux/amd64"]`, accepting emulation slowness |
| No space left on device | Accumulated images and volumes | `docker system prune -a` and remove stale volumes |
| Feature install fails on a missing user | Ordering: something ran before `common-utils` created the user | Add `overrideFeatureInstallOrder` with `common-utils` first |
| Network timeouts fetching packages | Host proxy not forwarded | Pass `HTTP_PROXY`/`HTTPS_PROXY` through `containerEnv` |

## Container starts then exits

Almost always Compose. The service's command finished, so Docker stopped the
container.

```yaml
services:
  app:
    command: sleep infinity
```

`overrideCommand` defaults to `false` for Compose (and `true` for image/Dockerfile),
which is why the same config works one way and not the other. Setting
`"overrideCommand": true` in `devcontainer.json` is the alternative, but an explicit
command in the compose file is clearer.

If it exits with an image or Dockerfile base, check whether `overrideCommand` was set
to `false` and the image's own `CMD` is short-lived.

## Tools missing after build

| Symptom | Cause | Fix |
|---|---|---|
| `command not found` for a Feature-installed tool | Feature installs to the user's profile; a non-interactive shell never sourced it | Set `"userEnvProbe": "loginInteractiveShell"`, or call it via `bash -i -c` |
| `nvm: command not found` in a lifecycle command | nvm is a shell function, not a binary | `"postCreateCommand": "bash -i -c 'nvm install --lts'"` |
| Tool present in terminal, missing in a task or debug session | Same probe issue, different consumer | Same fix; or set the absolute path in `containerEnv` |
| Feature seemed to install but nothing changed | Config edited without a rebuild | **Dev Containers: Rebuild Container** |
| Manually installed tool vanished | Rebuilds reset the container | Move it into `features`, the Dockerfile, or `postCreateCommand` |

## File permission problems

| Symptom | Cause | Fix |
|---|---|---|
| New files are root-owned on the host | Container runs as root over a bind mount | Set `remoteUser` to a non-root user; under Compose also set `user:` on the service |
| Cannot write to a named volume | Fresh volumes are root-owned | `chown` in `postCreateCommand` before using it |
| `Permission denied` on `/var/run/docker.sock` | User not in the `docker` group | Use the `docker-outside-of-docker` Feature, which handles group setup |
| UID mismatch after switching machines | UID baked into the image | Leave `updateRemoteUserUID` at its default `true` |
| `NoPermissions (FileSystemError)` on Windows | Docker Desktop WSL backend with Enhanced Container Isolation | Disable ECI, or see vscode-docs issue #8278 |

## Ports not reachable

Work through in order:

1. Is the server bound to `0.0.0.0` rather than `127.0.0.1`? Forwarded ports look
   like localhost so `127.0.0.1` is usually fine, but published ports
   (`appPort`, Compose `ports`) are not — those need `0.0.0.0`.
2. Is the port in `forwardPorts`? Auto-forwarding only detects some servers.
3. Under Compose, is the target a different service? Use `"db:5432"` syntax in
   `forwardPorts`, or `network_mode: service:db`.
4. Did the local port get remapped? A collision remaps silently unless
   `requireLocalPort` is `true`. Check the Ports view for the actual local port.
5. Low ports (80, 443) may need `"elevateIfNeeded": true`.

## Lifecycle command problems

| Symptom | Cause | Fix |
|---|---|---|
| Creation hangs forever at "Running postCreateCommand" | The command does not exit — a server or watcher | Move it to a task; lifecycle commands must terminate |
| A later lifecycle command never ran | An earlier one failed, aborting the chain | Read the log for the first failure |
| `postCreateCommand` runs every start | It does not — that is `postStartCommand` | Move one-time setup to `postCreateCommand` |
| Setup runs on the wrong machine | `initializeCommand` runs on the host | Use `onCreateCommand` or `postCreateCommand` for in-container work |
| Quotes appear literally in output | Array form does not use a shell | Use the string form when shell parsing is needed |
| Editor attaches before setup finishes | `waitFor` defaults to `updateContentCommand` | `"waitFor": "postCreateCommand"` |

## Extensions and editor problems

| Symptom | Cause | Fix |
|---|---|---|
| Extensions in the config are not installed | Listed at top level instead of under `customizations.vscode` | Move them; the old top-level form is ignored |
| Extension installs but does nothing | It is a UI extension running locally | Expected for themes and similar; check the Extensions view categories |
| Extension crashes on Alpine | musl vs glibc in native code | Use a Debian or Ubuntu image variant |
| An unwanted extension keeps appearing | Pulled in by the image or a Feature | Opt out with a `-` prefix: `"-dbaeumer.vscode-eslint"` |
| Settings not applied | Same top-level vs `customizations.vscode` mistake | Move under `customizations.vscode.settings` |

## Slowness

| Symptom | Cause | Fix |
|---|---|---|
| Installs and file watching crawl on macOS/Windows | Bind mount overhead on many small files | Named volume for `node_modules`/`.venv`; see `compose-and-advanced.md` |
| Every rebuild takes minutes | Long Feature list resolved each time | Prebuild an image and reference it |
| First open is slow for everyone | No shared cache | Prebuild and push; add `build.cacheFrom` |
| Container feels starved | Docker Desktop resource limits | Raise CPU/memory in Docker Desktop; declare `hostRequirements` |

## Platform-specific issues

- **Windows containers are not supported.** Linux containers only.
- **Docker Toolbox and the Ubuntu Docker snap are not supported.** Install Docker CE
  from the official repository.
- **Line endings**: working on the same repo in Windows and in a container without
  consistent settings shows every file as modified. Configure `core.autocrlf` or add
  a `.gitattributes`.
- **SSH keys with a passphrase** can hang push/pull from inside the container. Use an
  agent, a passphrase-less key, or HTTPS.
- **OpenSSH version mismatch**: a Windows ssh-agent at 8.8 or earlier with a client at
  8.9 or later fails with `Permission denied (publickey)` even though `ssh-add -l`
  works. Upgrade Windows OpenSSH.
- **All folders in a multi-root workspace** open in one container, regardless of
  per-folder configs.

## Manual review checklist

Use when `scripts/validate_devcontainer.py` cannot be run.

- [ ] Exactly one of `image`, `build.dockerfile`, `dockerComposeFile`
- [ ] `dockerComposeFile` is accompanied by `service` and an explicit `workspaceFolder`
- [ ] Compose dev container service has `command: sleep infinity`
- [ ] Every Feature ID exists and is pinned (`:1`)
- [ ] Image tag is pinned, and uses `mcr.microsoft.com/devcontainers/*`
- [ ] Extensions and settings are under `customizations.vscode`
- [ ] `workspaceFolder` and `workspaceMount` are both set, or neither (image/Dockerfile base)
- [ ] No lifecycle command starts a long-running process
- [ ] Workspace-dependent installs are in `postCreateCommand`, not the Dockerfile
- [ ] `remoteUser` is non-root, or the base image already sets one
- [ ] No secrets are literal values; they come from `${localEnv:...}`
- [ ] Database services use a named volume for their data directory
- [ ] Ports the team needs are in `forwardPorts`
