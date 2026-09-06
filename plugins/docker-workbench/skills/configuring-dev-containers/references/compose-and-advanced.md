# Compose and Advanced Configuration

Contents:
- [Docker Compose setup](#docker-compose-setup)
- [Extending an existing compose file](#extending-an-existing-compose-file)
- [Networking and localhost](#networking-and-localhost)
- [Docker inside a dev container](#docker-inside-a-dev-container)
- [Non-root users and file ownership](#non-root-users-and-file-ownership)
- [Disk performance and named volumes](#disk-performance-and-named-volumes)
- [Secrets and credentials](#secrets-and-credentials)
- [Debugger support](#debugger-support)
- [Prebuilding images](#prebuilding-images)
- [CI and automation](#ci-and-automation)
- [Dotfiles](#dotfiles)
- [The dev container CLI](#the-dev-container-cli)

## Docker Compose setup

Use Compose whenever a second service is involved. Two files:

```jsonc
// .devcontainer/devcontainer.json
{
  "name": "App with Postgres",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspaces/${localWorkspaceFolderBasename}",
  "forwardPorts": [3000, 5432],
  "postCreateCommand": "npm ci",
  "shutdownAction": "stopCompose"
}
```

```yaml
# .devcontainer/docker-compose.yml
services:
  app:
    image: mcr.microsoft.com/devcontainers/typescript-node:1-22-bookworm
    volumes:
      - ../..:/workspaces:cached
    command: sleep infinity        # required
    depends_on:
      - db
    environment:
      DATABASE_URL: postgres://postgres:postgres@db:5432/app

  db:
    image: postgres:16-bookworm
    restart: unless-stopped
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app

volumes:
  postgres-data:
```

The details that break things:

- **`command: sleep infinity`.** `overrideCommand` defaults to `false` under Compose,
  so the service keeps its own command. Once that command exits, the container stops
  and the editor disconnects. Postgres and other real services do not need this —
  only the dev container service does.
- **`service` names the service to attach to,** not the one to start. All services in
  the file start unless `runServices` narrows it.
- **Volume paths are relative to the first compose file in the array**, not to
  `devcontainer.json`. With the compose file inside `.devcontainer/`, `../..` reaches
  the repo's parent so `/workspaces/<repo>` matches the standard layout.
- **`workspaceFolder` defaults to `/`** under Compose. Always set it explicitly.
- **Named volume for the database.** Without it the data lives in the container layer
  and a rebuild silently wipes the database.
- **Reach other services by service name** (`db:5432`), not `localhost`.

## Extending an existing compose file

When the project already has a production `docker-compose.yml`, do not copy it —
layer a dev-only override:

```jsonc
"dockerComposeFile": ["../docker-compose.yml", "docker-compose.extend.yml"],
"service": "app",
"workspaceFolder": "/workspace"
```

```yaml
# .devcontainer/docker-compose.extend.yml
services:
  app:
    volumes:
      - .:/workspace:cached
    command: sleep infinity
    cap_add:
      - SYS_PTRACE
    security_opt:
      - seccomp:unconfined
```

Order matters: later files override earlier ones. This keeps the production file
untouched while giving the dev container a live mount and a command that stays up.

## Networking and localhost

By default each Compose service has its own network namespace, so `localhost` inside
the dev container is not the database. Either connect by service name (preferred), or
put the dev container on the database's namespace:

```yaml
services:
  app:
    network_mode: service:db
```

With `network_mode: service:db` the app reaches Postgres on `localhost:5432`, and
`forwardPorts` in `devcontainer.json` works for ports opened by either container. The
cost is that the service can no longer declare its own `ports`.

## Docker inside a dev container

Two Features, two different behaviors:

| Feature | What you get | When |
|---|---|---|
| `docker-outside-of-docker:1` | Docker CLI in the container, bound to the **host** daemon via the socket | Building or running app images; containers are siblings and survive the dev container. Faster, shares the host image cache |
| `docker-in-docker:1` | A **separate** nested daemon inside the container | Testing Docker itself, isolated image cache, CI parity. Slower, needs elevated privileges |

Path gotcha with docker-outside-of-docker: because the daemon is the host's, bind
mount paths in `docker run` are resolved on the **host**, not in the container. Mount
`${localWorkspaceFolder}` rather than the container path.

Testcontainers, Docker Compose from inside, and most build workflows want
docker-outside-of-docker.

## Non-root users and file ownership

The prebuilt `mcr.microsoft.com/devcontainers/*` images ship a non-root user
(`vscode`, or `node` for the Node images) and set `remoteUser` in image metadata, so
usually nothing is needed.

For a custom image, add the user via a Feature:

```jsonc
"features": {
  "ghcr.io/devcontainers/features/common-utils:1": {
    "username": "vscode",
    "userUid": "automatic",
    "userGid": "automatic"
  }
},
"remoteUser": "vscode"
```

- `remoteUser` changes who the editor, terminals, and lifecycle commands run as.
- `containerUser` changes who every process runs as, including the entrypoint.
- `updateRemoteUserUID` (default `true`) remaps the container user's UID to the host
  user's on Linux, which is what keeps bind-mounted files from becoming root-owned.
  It does not apply under Compose — there, set `user:` on the service.

Under Compose, add to the service:

```yaml
services:
  app:
    user: vscode
```

If files are already root-owned on the host, fix them from the host with
`sudo chown -R $USER:$USER .` — changing the config does not retroactively fix
ownership.

## Disk performance and named volumes

Bind mounts on macOS and Windows are slow for directories with many small files.
Dependency directories are the usual pain point. Put them on a named volume:

```jsonc
"mounts": [
  "source=${localWorkspaceFolderBasename}-node_modules,target=${containerWorkspaceFolder}/node_modules,type=volume"
],
"postCreateCommand": "sudo chown node:node node_modules && npm ci"
```

The `chown` matters: a fresh named volume is root-owned, so the install fails without
it. The same pattern works for `.venv`, `target/` (Rust), and `vendor/` (Go, PHP).

Tradeoff: those files are no longer visible on the host, so host-side tooling and IDE
indexing outside the container cannot see them.

The alternative is **Dev Containers: Clone Repository in Container Volume**, which
puts the entire repo in a Docker volume. Fastest option, but the source only exists
inside the volume — commit and push, or the work is not on the host.

## Secrets and credentials

`devcontainer.json` is committed. Never put a secret in it.

```jsonc
"remoteEnv": {
  "NPM_TOKEN": "${localEnv:NPM_TOKEN}",
  "AWS_PROFILE": "${localEnv:AWS_PROFILE}"
}
```

Git credentials are forwarded automatically when the host uses a credential manager
or an SSH agent with a loaded key. Read-only mounts for other credentials:

```jsonc
"mounts": [
  "source=${localEnv:HOME}/.aws,target=/home/vscode/.aws,type=bind,readonly"
]
```

`${localEnv:HOME}` is empty on Windows; use `${localEnv:HOME}${localEnv:USERPROFILE}`
for a config that must work on both.

Codespaces has its own encrypted secrets, surfaced as environment variables — do not
try to forward host env vars in a Codespaces-only config.

## Debugger support

ptrace-based debuggers (gdb, delve, lldb — so C, C++, Go, Rust) need extra
capabilities:

```jsonc
"capAdd": ["SYS_PTRACE"],
"securityOpt": ["seccomp=unconfined"]
```

Under Compose these go on the service as `cap_add` and `security_opt` instead. The
`cpp` and `go` base images already set them via image metadata.

## Prebuilding images

Once the Feature list is long or the Dockerfile is slow, build the image ahead of
time and reference it. First build carries the full cost; contributors get a pull.

```bash
npm install -g @devcontainers/cli

devcontainer build \
  --workspace-folder . \
  --image-name ghcr.io/<org>/<repo>-devcontainer:latest \
  --push true
```

Then the repo config collapses to:

```jsonc
{ "image": "ghcr.io/<org>/<repo>-devcontainer:latest" }
```

`devcontainer build` writes the `devcontainer.metadata` label, so settings,
extensions, `remoteUser` and Feature config travel with the image and do not need
restating.

Keep the rich config in a separate folder (`.devcontainer/build/devcontainer.json`)
used only for prebuilding, and the thin one in `.devcontainer/` for daily use.

## CI and automation

The same config can run the test suite, which is the main reason it stays honest:

```yaml
# .github/workflows/ci.yml
- uses: devcontainers/ci@v0.3
  with:
    imageName: ghcr.io/${{ github.repository }}-devcontainer
    cacheFrom: ghcr.io/${{ github.repository }}-devcontainer
    push: filter
    runCmd: npm test
```

Or with the CLI directly:

```bash
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . npm test
```

## Dotfiles

Personal shell config belongs in the user's own settings, not in the repo's config —
it is per-person and would otherwise be imposed on everyone:

```jsonc
{
  "dotfiles.repository": "user/dotfiles",
  "dotfiles.targetPath": "~/dotfiles",
  "dotfiles.installCommand": "install.sh"
}
```

That goes in VS Code user settings. When a user asks to add their zsh theme to the
project's devcontainer.json, point them here instead.

## The dev container CLI

Reference implementation of the spec; works without VS Code.

```bash
npm install -g @devcontainers/cli
```

| Command | Purpose |
|---|---|
| `devcontainer up --workspace-folder .` | Create and start |
| `devcontainer up --workspace-folder . --remove-existing-container` | Force a clean rebuild |
| `devcontainer build --workspace-folder .` | Build the image only |
| `devcontainer exec --workspace-folder . <cmd>` | Run a command inside |
| `devcontainer read-configuration --workspace-folder .` | Print the merged config, including image metadata |
| `devcontainer features publish` | Publish Features |
| `devcontainer templates publish` | Publish Templates |

`read-configuration` is the tool for "why is this setting active" — it shows the
result after image labels and Features are merged in.
