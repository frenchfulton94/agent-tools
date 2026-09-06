# Dockerfile patterns by stack

Contents:
- [Python with uv](#python-with-uv)
- [Python with pip](#python-with-pip)
- [Go](#go)
- [Rust](#rust)
- [JVM](#jvm)
- [Static frontend](#static-frontend)
- [System packages](#system-packages)
- [Private registries](#private-registries)
- [Base image selection](#base-image-selection)

Every example assumes `# syntax=docker/dockerfile:1` on line one, which enables cache mounts, secret mounts, and heredocs.

## Python with uv

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

FROM python:3.13-slim-bookworm AS runtime
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=build --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The two-step `uv sync` is the cache trick: dependencies resolve in a layer that only `uv.lock` and `pyproject.toml` can invalidate, so editing source does not reinstall them. Bind mounts for the lockfiles avoid copying them into the layer at all.

## Python with pip

```dockerfile
FROM python:3.13-slim-bookworm AS runtime
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
USER app
CMD ["python", "-m", "app"]
```

Set `PYTHONUNBUFFERED=1` when logs need to appear promptly — Python block-buffers stdout when it is not a terminal, which makes a container look hung.

## Go

Static binary, scratch or distroless final stage:

```dockerfile
FROM golang:1.24-bookworm AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -ldflags="-s -w" -o /out/app ./cmd/app

FROM gcr.io/distroless/static-nonroot
COPY --from=build /out/app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```

`CGO_ENABLED=0` is what makes the binary run on `scratch` and `distroless/static`. With cgo on, use `distroless/base` instead — the binary needs libc.

## Rust

```dockerfile
FROM rust:1-bookworm AS build
WORKDIR /src
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs && \
    cargo build --release && rm -rf src
COPY . .
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    touch src/main.rs && cargo build --release

FROM gcr.io/distroless/cc-nonroot
COPY --from=build /src/target/release/app /app
ENTRYPOINT ["/app"]
```

The dummy-`main.rs` step compiles dependencies in a layer that only the manifests invalidate. `cargo-chef` does the same thing more thoroughly on large workspaces.

## JVM

```dockerfile
FROM eclipse-temurin:21-jdk AS build
WORKDIR /src
COPY gradlew settings.gradle build.gradle ./
COPY gradle ./gradle
RUN ./gradlew --no-daemon dependencies
COPY src ./src
RUN ./gradlew --no-daemon bootJar

FROM eclipse-temurin:21-jre-alpine
RUN adduser -D -u 10001 app
COPY --from=build /src/build/libs/*.jar /app.jar
USER app
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/app.jar"]
```

`MaxRAMPercentage` matters in containers: without it the JVM sizes the heap against a fraction of what it detects and can be OOM-killed by the container limit before its own GC ever feels pressure.

## Static frontend

Build with Node, serve with nginx. The Node layer never ships:

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

A single-page app needs `try_files $uri $uri/ /index.html;` in that nginx config, or every deep link 404s on refresh.

## System packages

Combine update, install, and cleanup in one `RUN`. Split across layers, the cleanup deletes files the earlier layer already committed and the image does not shrink:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
```

`--no-install-recommends` typically removes a large fraction of an apt install. On Alpine, `apk add --no-cache` handles the equivalent in one flag.

Build-only dependencies (compilers, `-dev` headers) belong in a build stage, not installed and then removed in the runtime stage.

## Private registries

Pass credentials with a secret mount so they never reach a layer:

```dockerfile
RUN --mount=type=secret,id=netrc,target=/root/.netrc \
    pip install --extra-index-url https://private.example.com/simple mypkg
```

```bash
docker build --secret id=netrc,src=$HOME/.netrc .
```

For SSH-based dependency fetches, `RUN --mount=type=ssh` forwards the agent: `docker build --ssh default .`

## Base image selection

| Base | Size | Use when |
|---|---|---|
| `-slim` (Debian) | Moderate | Default. glibc, apt available, few surprises |
| `-alpine` | Small | Size matters and the stack has no glibc or wheel dependency |
| `distroless` | Small | Production runtime, no shell wanted in the image |
| `scratch` | Minimal | A fully static binary and nothing else |
| Full (`node:22`, `python:3.13`) | Large | Build stages only |

Alpine uses musl rather than glibc. For Python that means many packages have no prebuilt wheel and compile from source, which is slower to build and often produces a *larger* image than `-slim`. Measure before assuming Alpine is the smaller choice.

`distroless` and `scratch` have no shell, so `docker exec ... sh` will not work — debug by adding a temporary `-debug` variant stage rather than changing the production base.
