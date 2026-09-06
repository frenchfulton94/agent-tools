# Features and Base Images

Contents:
- [First-party Features](#first-party-features)
- [Feature options](#feature-options)
- [Install order](#install-order)
- [First-party base images](#first-party-base-images)
- [Choosing image vs Feature](#choosing-image-vs-feature)
- [Community Features](#community-features)
- [Writing your own Feature](#writing-your-own-feature)

## First-party Features

Published from `github.com/devcontainers/features`. The full ID is
`ghcr.io/devcontainers/features/<name>:1`. This is the complete first-party set —
an ID not on this list is either a community Feature or does not exist.

| Name | Installs |
|---|---|
| `anaconda` | Anaconda distribution |
| `aws-cli` | AWS CLI v2 |
| `azure-cli` | Azure CLI |
| `common-utils` | zsh, Oh My Zsh, a non-root user, common shell tooling |
| `conda` | Conda package manager |
| `copilot-cli` | GitHub Copilot CLI |
| `desktop-lite` | Lightweight desktop + VNC, for GUI apps and browser tests |
| `docker-in-docker` | A Docker daemon inside the container |
| `docker-outside-of-docker` | Docker CLI wired to the host daemon via socket |
| `dotnet` | .NET SDK |
| `git` | Git built from source (newer than distro packages) |
| `git-lfs` | Git Large File Storage |
| `github-cli` | `gh` |
| `go` | Go toolchain plus common Go tools |
| `hugo` | Hugo static site generator |
| `java` | JDK via SDKMAN, optional Maven/Gradle |
| `kubectl-helm-minikube` | kubectl, Helm, Minikube |
| `nix` | Nix package manager |
| `node` | Node.js via nvm, plus npm/yarn/pnpm |
| `nvidia-cuda` | CUDA toolkit and cuDNN |
| `oryx` | Microsoft Oryx build system |
| `php` | PHP and Composer |
| `powershell` | PowerShell |
| `python` | Python via a managed install, plus pip tooling |
| `ruby` | Ruby via rvm |
| `rust` | Rust via rustup, plus cargo tooling |
| `sshd` | An SSH server inside the container |
| `terraform` | Terraform, plus optional TFLint and Terragrunt |

Always pin the major version (`:1`). Unpinned resolves to latest and will change
under the project without warning.

## Feature options

Each Feature declares its own options; pass them as the object value. Common ones:

```jsonc
"features": {
  "ghcr.io/devcontainers/features/node:1": {
    "version": "22",           // "lts", "latest", or a major/exact version
    "nodeGypDependencies": true
  },
  "ghcr.io/devcontainers/features/python:1": {
    "version": "3.12",
    "installTools": true       // pylint, flake8, black, mypy, pipx
  },
  "ghcr.io/devcontainers/features/java:1": {
    "version": "21",
    "installMaven": true,
    "installGradle": false
  },
  "ghcr.io/devcontainers/features/go:1": { "version": "1.23" },
  "ghcr.io/devcontainers/features/common-utils:1": {
    "installZsh": true,
    "username": "vscode",
    "upgradePackages": true
  },
  "ghcr.io/devcontainers/features/docker-in-docker:1": { "moby": true },
  "ghcr.io/devcontainers/features/terraform:1": {
    "version": "latest",
    "tflint": "latest"
  }
}
```

`{}` accepts every default and is the right call when you have no version constraint.
Option names are per-Feature and not guessable — read the Feature's README on GitHub
when you need one that isn't listed here.

## Install order

Features resolve their own order from the `installsAfter` field each one declares, so
in almost every case you should leave ordering alone. Override only when you have
observed a real ordering failure:

```jsonc
"overrideFeatureInstallOrder": [
  "ghcr.io/devcontainers/features/common-utils",
  "ghcr.io/devcontainers/features/node"
]
```

Entries are IDs without the version tag. `common-utils` creates the non-root user, so
anything that installs into that user's home has to come after it — this is the one
ordering conflict that shows up in practice.

## First-party base images

Published at `mcr.microsoft.com/devcontainers/<name>`. Source:
`github.com/devcontainers/images`.

| Image | Notes |
|---|---|
| `base-debian`, `base-ubuntu`, `base-alpine` | OS only; add everything via Features |
| `javascript-node` | Node + npm/yarn |
| `typescript-node` | Node + TypeScript + ESLint |
| `python` | Python + pip tooling |
| `go` | Go + common tooling |
| `java`, `java-8` | JDK + Maven/Gradle |
| `dotnet` | .NET SDK |
| `rust` | Rust + cargo tooling |
| `cpp` | GCC/Clang, CMake, debugger prerequisites |
| `php`, `ruby`, `jekyll` | Respective runtimes |
| `anaconda`, `miniconda` | Data science stacks |
| `universal` | Many languages preinstalled; large, used by Codespaces defaults |

Tags encode version and distro: `mcr.microsoft.com/devcontainers/python:1-3.12-bookworm`.
Pin at least the language version. The bare name floats and will move under you.

These images already set `remoteUser` (`vscode` or `node`) and ship `sudo`, so you
usually do not need to configure a user yourself.

## Choosing image vs Feature

The base image should be the project's primary language; Features cover everything
else. A TypeScript service that also needs the AWS CLI and Terraform:

```jsonc
{
  "image": "mcr.microsoft.com/devcontainers/typescript-node:1-22-bookworm",
  "features": {
    "ghcr.io/devcontainers/features/aws-cli:1": {},
    "ghcr.io/devcontainers/features/terraform:1": {}
  }
}
```

Not two language images — you cannot have two. For polyglot repos, take
`base-ubuntu` and add each language as a Feature, or use `universal`.

Features run at container creation, so a long Feature list slows first build. Once
the list grows past four or five, prebuild an image instead
(see `compose-and-advanced.md`).

## Community Features

Browse the index at <https://containers.dev/features>. Common publishers include
`ghcr.io/devcontainers-contrib/features/*` (now largely migrated to
`ghcr.io/devcontainers-extra/features/*`). Treat these as third-party code that runs
at build time with full privileges: pin the version, and read `install.sh` before
adding one to a shared repo.

There is no first-party Feature for databases. Postgres, Redis, MySQL and friends
belong in Docker Compose as separate services, not installed into the dev container.

## Writing your own Feature

A Feature is a folder with `devcontainer-feature.json` and `install.sh`:

```
src/my-tool/
├── devcontainer-feature.json
└── install.sh
```

```jsonc
// devcontainer-feature.json
{
  "id": "my-tool",
  "version": "1.0.0",
  "name": "My Tool",
  "options": {
    "version": { "type": "string", "default": "latest", "description": "Version to install" }
  },
  "installsAfter": ["ghcr.io/devcontainers/features/common-utils"]
}
```

`install.sh` runs as root at build time; options arrive as uppercased environment
variables (`VERSION`). Publish to any OCI registry:

```bash
devcontainer features publish ./src --namespace <org>/<repo>
```

Start from `github.com/devcontainers/feature-starter`, which includes the publish
workflow and a test harness.
