# Build types

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [Choosing between them](#choosing-between-them)
- [Nixpacks](#nixpacks)
- [Railpack](#railpack)
- [Dockerfile](#dockerfile)
- [Buildpack](#buildpack)
- [Static](#static)

## Choosing between them

Five build types are available on an Application. The build type decides which fields
appear in the panel and which environment variables have any effect.

| Build type | Use it for | The field that matters most |
|---|---|---|
| Nixpacks | The default. Prototyping, and any stack Nixpacks already detects | `Publish Directory`, which switches the result to NGINX |
| Railpack | The successor to Nixpacks, for the languages it supports | `Railpack Version`, to pin builds |
| Dockerfile | Full control of the build environment | `Dockerfile Path`, which is required |
| Buildpack | Migrating from Heroku, or standardising on Paketo | The Heroku version, default 24 |
| Static | Pre-built files with no build step | The domain's port, which has to be 80 |

Dokploy's own recommendation: Nixpacks for prototyping and development, Static for static
applications, and for production the going-production path that builds in CI instead of
on the deployment server (see `release-lifecycle.md`).

## Nixpacks

The default. Dokploy builds the repository as a Nixpack with no configuration.

Nixpacks reads its overrides from environment variables, set in the application's
`Environment Variables` tab. Every one is prefixed `NIXPACKS_`:

| Variable | Effect |
|---|---|
| `NIXPACKS_INSTALL_CMD` | Override the install command to use |
| `NIXPACKS_BUILD_CMD` | Override the build command to use |
| `NIXPACKS_START_CMD` | Override the command run when the container starts |
| `NIXPACKS_PKGS` | Add additional Nix packages to install |
| `NIXPACKS_APT_PKGS` | Add additional Apt packages to install, comma delimited |
| `NIXPACKS_LIBS` | Add additional Nix libraries to make available |
| `NIXPACKS_INSTALL_CACHE_DIRS` | Add directories to cache during the install phase |
| `NIXPACKS_BUILD_CACHE_DIRS` | Add directories to cache during the build phase |
| `NIXPACKS_NO_CACHE` | Disable caching for the build |
| `NIXPACKS_CONFIG_FILE` | Location of the Nixpacks configuration file, relative to the app root |
| `NIXPACKS_DEBIAN` | Enable the Debian base image, for OpenSSL 1.1 support |

For anything these do not reach, commit a `nixpacks.toml` at the repository root.

Nixpacks handles monorepos, including NX, Turborepo, and Moon Repo. The Turborepo guide
uses `NIXPACKS_TURBO_APP_NAME` alongside `NIXPACKS_BUILD_CMD` and `NIXPACKS_START_CMD`
to select one workspace out of the repository — see `framework-recipes.md`.

**`Publish Directory` changes what runs.** Nixpacks has a static builder, and Dokploy
exposes a `Publish Directory` field on top of it. Name the directory the build leaves
behind — `dist` for an Astro or Vite build, `_site` for 11ty — and Dokploy copies its
contents and serves them from an NGINX-optimised Dockerfile instead of running the
application. The consequence is easy to miss: the domain's `Container Port` then has to
be `80`, not the port the framework's dev server used.

## Railpack

Railpack is the successor to Nixpacks and supports Node.js, Python, Go, PHP, StaticFile,
and shell scripts.

Its build variables also live in the `Environment Variables` tab:

| Variable | Effect |
|---|---|
| `RAILPACK_BUILD_CMD` | Set the build step's command, overwriting whatever the provider supplied |
| `RAILPACK_START_CMD` | Set the command run when the container starts |
| `RAILPACK_PACKAGES` | Install additional Mise packages, as `pkg@version`; latest if no version is given |
| `RAILPACK_BUILD_APT_PACKAGES` | Install additional Apt packages during the build |
| `RAILPACK_DEPLOY_APT_PACKAGES` | Install additional Apt packages into the final image |

A `Railpack Version` field in the application settings pins the Railpack release used,
for example `0.15.1`. Dokploy downloads that version for the build. An invalid version
is rejected with an error, so take the value from Railpack's releases page. Pin it for
any application whose builds need to be reproducible; leave it empty to track the
current release.

## Dockerfile

Dokploy builds the repository's own Dockerfile, which puts the whole build environment
under the repository's control. Three fields:

- **`Dockerfile Path`** (required) — the path to the Dockerfile. `Dockerfile` when it
  sits at the repository root.
- **`Docker Context Path`** — the build context, `.` for the repository root.
- **`Docker Build Stage`** — the target stage in a multi-stage build, for example
  `builder`.

Selecting this build type adds two more fields to the **Environment** tab:

- **Build Time Arguments** — `ARG` values passed to the build. Use them for dependency
  versions, feature flags, and other build-time configuration.
- **Build-time Secrets** — Docker build secrets. Unlike build arguments, these do not
  survive into the final image or the build history.

Build arguments and environment variables are the wrong place for a credential, because
they persist in the image. Anything sensitive goes through Build-time Secrets. For
writing the Dockerfile itself, including the secret-mount syntax it needs, use
`docker-workbench:containerizing-apps`.

## Buildpack

Two variants:

- **Heroku** — Heroku's buildpacks, for compatibility and for migrating off Heroku. The
  Heroku version is optional and defaults to **24**.
- **Paketo** — cloud-native buildpacks.

## Static

For applications that are already built. Dokploy copies everything from the `Root`
directory, mounts it at `/usr/share/nginx/html`, and serves it from an
NGINX-optimised Dockerfile.

Use port **80** when creating the domain. This is the same requirement the Nixpacks
`Publish Directory` path carries, and getting it wrong is one of the ways a deployment
that reports success serves nothing on its domain.
