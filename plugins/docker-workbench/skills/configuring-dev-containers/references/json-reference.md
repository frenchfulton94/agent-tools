# devcontainer.json Property Reference

Contents:
- [File location](#file-location)
- [General properties](#general-properties)
- [Image and Dockerfile properties](#image-and-dockerfile-properties)
- [Docker Compose properties](#docker-compose-properties)
- [Lifecycle scripts](#lifecycle-scripts)
- [Port attributes](#port-attributes)
- [Host requirements](#host-requirements)
- [Variables](#variables)
- [Customizations](#customizations)
- [Image metadata labels](#image-metadata-labels)

Condensed from <https://containers.dev/implementors/json_reference>. Consult that page
for anything not covered here.

## File location

Either `.devcontainer/devcontainer.json` (preferred) or `.devcontainer.json` in the
repo root. For multiple configs, use `.devcontainer/<name>/devcontainer.json` — tools
offer a picker across them.

The format is JSONC: `//` and `/* */` comments are allowed. Trailing commas are not
reliably accepted; leave them out.

## General properties

| Property | Type | Notes |
|---|---|---|
| `name` | string | Display name in the UI |
| `features` | object | Feature ID → options. See `features.md` |
| `overrideFeatureInstallOrder` | array | IDs without version tags; overrides automatic ordering |
| `forwardPorts` | array | Ports or `"service:port"` always forwarded, e.g. `[3000, "db:5432"]` |
| `portsAttributes` | object | Per-port options; see [port attributes](#port-attributes) |
| `otherPortsAttributes` | object | Defaults for ports not listed in `portsAttributes` |
| `containerEnv` | object | Env vars on the container itself; static, needs rebuild to change. Prefer this |
| `remoteEnv` | object | Env vars for the tool and its subprocesses only; changeable without rebuild |
| `containerUser` | string | User for all container processes |
| `remoteUser` | string | User for the editor and terminals; does not change the container's own user |
| `updateRemoteUserUID` | boolean | Default `true`. On Linux, aligns container UID/GID with the host user to keep bind-mount ownership sane |
| `userEnvProbe` | enum | `none`, `interactiveShell`, `loginShell`, `loginInteractiveShell` (default). Which shell files are sourced to collect env vars |
| `overrideCommand` | boolean | Run a sleep loop instead of the image's command. Defaults `true` for image/Dockerfile, `false` for Compose |
| `shutdownAction` | enum | `none`, `stopContainer` (image/Dockerfile default), `stopCompose` (Compose default) |
| `init` | boolean | Run `tini` as PID 1 to reap zombie processes |
| `privileged` | boolean | `--privileged`. Required by some Docker-in-Docker setups; a real security tradeoff |
| `capAdd` | array | e.g. `["SYS_PTRACE"]` for gdb/delve/lldb-based debugging |
| `securityOpt` | array | e.g. `["seccomp=unconfined"]` |
| `mounts` | array | Extra mounts, Docker `--mount` syntax |
| `customizations` | object | Tool-specific config; see [customizations](#customizations) |
| `hostRequirements` | object | Minimum CPU/memory/storage/GPU |

## Image and Dockerfile properties

Exactly one of `image`, `build.dockerfile`, or `dockerComposeFile`.

| Property | Notes |
|---|---|
| `image` | Registry image reference. Required when using an image |
| `build.dockerfile` | Path relative to devcontainer.json. Required when using a Dockerfile |
| `build.context` | Build context, relative to devcontainer.json. Defaults `"."`. Use `".."` to reach repo root |
| `build.args` | Build args; supports `${localEnv:...}` |
| `build.options` | Extra `docker build` flags |
| `build.target` | Multi-stage build target, e.g. `"development"` |
| `build.cacheFrom` | Image(s) to use as build cache — the mechanism for consuming a prebuilt image |
| `appPort` | Publishes ports at container creation. Prefer `forwardPorts` |
| `workspaceMount` | Overrides the default source mount. Requires `workspaceFolder` |
| `workspaceFolder` | Path opened inside the container. Requires `workspaceMount` |
| `runArgs` | Raw `docker run` args. Array form only, and quotes are not shell-processed: write `["--device-cgroup-rule=my rule"]`, not with inner quotes |

Overriding the workspace mount, both properties together:

```jsonc
"workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=cached",
"workspaceFolder": "/workspace"
```

## Docker Compose properties

| Property | Notes |
|---|---|
| `dockerComposeFile` | Path or ordered array of paths. Later files override earlier ones |
| `service` | The service the editor connects to. Required. Not "the service to start" |
| `runServices` | Subset of services to start. Defaults to all |
| `workspaceFolder` | Path to open. Defaults `"/"`, which is almost never what you want — set it |

## Lifecycle scripts

Execution order: `initializeCommand` → `onCreateCommand` → `updateContentCommand` →
`postCreateCommand` → `postStartCommand` → `postAttachCommand`.

`initializeCommand` runs on the host — in a cloud service, that host is in the cloud.
The others run inside the container from `workspaceFolder`.

Three value forms:

```jsonc
// String: parsed by /bin/sh. Use for &&, globs, $VAR
"postCreateCommand": "npm ci && npm run build"

// Array: executed directly, no shell. Quotes are preserved literally
"postCreateCommand": ["npm", "ci"]

// Object: named entries run in parallel
"postCreateCommand": {
  "deps": "npm ci",
  "hooks": "pre-commit install"
}
```

`waitFor` sets which command tools block on before connecting. Default
`updateContentCommand`. Move it to `postCreateCommand` when the editor must not
attach until setup finishes.

A failing script aborts the remaining chain.

## Port attributes

| Option | Notes |
|---|---|
| `label` | Display name in the ports view |
| `protocol` | `http` or `https`. Set `https` so cloud forwarding presents the right certificate |
| `onAutoForward` | `notify` (default), `openBrowser`, `openBrowserOnce`, `openPreview`, `silent`, `ignore` |
| `requireLocalPort` | `true` warns instead of silently remapping to a free local port |
| `elevateIfNeeded` | Auto-elevate for low ports (22, 80, 443) |

```jsonc
"portsAttributes": {
  "3000": { "label": "Web", "onAutoForward": "openPreview" },
  "5432": { "label": "Postgres", "onAutoForward": "silent" },
  "9229": { "label": "Debug", "onAutoForward": "ignore" }
}
```

Forwarding vs publishing: forwarded ports look like `localhost` to the app, so a
server bound to `127.0.0.1` still works. Published ports (`appPort`, Compose `ports`)
behave like external network traffic, so the app must bind `0.0.0.0`.

## Host requirements

```jsonc
"hostRequirements": {
  "cpus": 4,
  "memory": "8gb",
  "storage": "32gb",
  "gpu": "optional"          // true | false | "optional" | { "cores": 1, "memory": "8gb" }
}
```

Cloud services use these to pick machine size; local tools warn when unmet.

## Variables

| Variable | Where |
|---|---|
| `${localEnv:NAME}` | Host env var. Empty if unset; `${localEnv:NAME:default}` for a fallback |
| `${containerEnv:NAME}` | Container env var. Only valid inside `remoteEnv` |
| `${localWorkspaceFolder}` | Host path of the opened folder |
| `${containerWorkspaceFolder}` | Workspace path inside the container |
| `${localWorkspaceFolderBasename}` | Folder name only |
| `${containerWorkspaceFolderBasename}` | Folder name inside the container |
| `${devcontainerId}` | Stable unique ID for this dev container, survives rebuilds |

```jsonc
"remoteEnv": {
  "GITHUB_TOKEN": "${localEnv:GITHUB_TOKEN}",
  "PATH": "${containerEnv:PATH}:/workspaces/${localWorkspaceFolderBasename}/bin"
}
```

Appending to `PATH` requires `remoteEnv` with `${containerEnv:PATH}` — `containerEnv`
cannot read its own prior value. Clients may need a restart to pick up newly set host
variables.

## Customizations

Tool-scoped. VS Code's namespace:

```jsonc
"customizations": {
  "vscode": {
    "extensions": ["ms-python.python", "-dbaeumer.vscode-eslint"],
    "settings": { "python.defaultInterpreterPath": "/usr/local/bin/python" }
  }
}
```

A leading `-` opts out of an extension that the base image or a Feature would
otherwise install. Other tools define their own keys (for example `codespaces`);
unknown namespaces are ignored, so leaving them in place is harmless.

Top-level `extensions` and `settings` are the pre-2022 schema and no longer apply.

## Image metadata labels

Prebuilt images can carry their own dev container config, which merges with the
repo's `devcontainer.json` at creation time. `devcontainer build` writes this label
automatically. Manually:

```dockerfile
LABEL devcontainer.metadata='[{ \
  "capAdd": ["SYS_PTRACE"], \
  "remoteUser": "vscode", \
  "postCreateCommand": "yarn install" \
}]'
```

This is why referencing `mcr.microsoft.com/devcontainers/go:1` alone yields a working
setup — the settings ride along in the image. It also means a property you did not
write may still be in effect; check the image's own devcontainer.json when behavior
seems unexplained.
