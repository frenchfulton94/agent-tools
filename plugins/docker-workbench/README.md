# Docker Workbench

A Claude Code plugin for setting up, using, and configuring Docker and containers,
including containerized dev environments.

## Components

| Component | Shape | Why this shape |
|---|---|---|
| `containerizing-apps` | Skill | Repeated multi-step authoring know-how applied with judgment in the main conversation |
| `managing-container-runtimes` | Skill | Same, for a distinct trigger surface — the runtime under the CLI, not the files above it |
| `securing-container-supply-chain` | Skill | Same again — what is in the image and where it came from, which is asked as a different question from either of the above |
| `configuring-dev-containers` | Skill | Same again — the inner dev loop (`devcontainer.json`, Codespaces) rather than the image you ship |
| `container-debugger` | Subagent | Build logs and container logs are large; the diagnosis is small. The classic case for isolation |
| `docker-guard` | Hook | Volume deletion is irreversible and cannot be left advisory — a skill can be reasoned around, a hook cannot |

The four skills are split rather than merged because their triggers barely overlap. "Write me a Dockerfile", "Docker won't start", "are these CVEs a problem", and "set up a dev container" want different knowledge, and a single description covering all four fires imprecisely on each. Each skill's `evals/triggers.md` lists the others' queries as should-not-trigger cases.

## Where security lives

Split across two skills, along the line between how a container runs and what is inside it:

| Topic | Home |
|---|---|
| Secret mounts, non-root `USER`, `.dockerignore`, digest pinning | `containerizing-apps` (inline) |
| Capabilities, `read_only`, `no-new-privileges`, resource limits, network isolation, the Docker socket, seccomp | `containerizing-apps/references/hardening.md` |
| Vulnerability scanning and CVE triage | `securing-container-supply-chain` |
| SBOMs, provenance, Sigstore signing, admission enforcement | `securing-container-supply-chain` |

Hardening sits with authoring because it is Dockerfile and Compose syntax — the same file, the same edit. Scanning and signing sit apart because they are asked as a separate question, usually by a different person, at a different point in the lifecycle.

## Install

```bash
claude plugin install docker-workbench@agent-tools --scope project
```

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so
the plugin travels with the repo instead of living on one workstation.

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/docker-workbench
claude plugin validate plugins/docker-workbench --strict
```

`hooks/hooks.json` invokes the guard as `bash scripts/docker-guard.sh`, so the script does not need an executable bit. Run `chmod +x scripts/docker-guard.sh` anyway if you plan to call it directly.

## The guard hook

`PreToolUse` on `Bash`. Three outcomes:

- **deny** — `docker volume rm`, `docker volume prune`, any prune with `--volumes`, `docker compose down -v`, and `rm -rf` against a runtime's data directory. These destroy state that is in no backup and no git history.
- **ask** — `docker system prune -a`, `docker image prune -a`, and unfiltered `docker buildx prune -a`. Recoverable, but machine-wide and slow to recover from.
- **allow** — everything else, silently. Scoped cleanup (`docker image prune`, `docker container prune`, `docker buildx prune --filter until=...`) passes through, so the guard never stands between anyone and reclaiming disk.

A denial is not a lecture: each reason names the safer command to run instead.

The script needs `jq`, which ships with Docker Desktop and OrbStack installs and is otherwise `brew install jq`. If `jq` is missing the guard exits 0 and allows the command — failing open, because a guard that errors on every Bash call would be worse than one that occasionally does not fire. Verify it registered with `/hooks` and that it blocks with:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"docker compose down -v"}}' \
  | bash scripts/docker-guard.sh
```

To disable the guard while keeping the rest, remove `hooks/hooks.json`.

The guard deliberately does **not** enforce security policy. Blocking socket mounts or `--privileged` would fire on legitimate patterns — Testcontainers mounts the socket routinely — and a hook with false positives gets disabled, taking the data-loss protection with it. Those risks are covered in `references/hardening.md`, where they can carry the nuance a regex cannot. Most `--privileged` and socket usage also appears in Compose files rather than Bash commands, which a `PreToolUse` Bash hook would never see.

## Sources

- Docker documentation index — <https://docs.docker.com/llms.txt>
- Dev Containers specification — <https://containers.dev>
- OrbStack documentation — <https://docs.orbstack.dev>
- Docker Scout CLI — <https://docs.docker.com/reference/cli/docker/scout/>
- Build attestations — <https://docs.docker.com/build/metadata/attestations/>
- Sigstore / cosign — <https://docs.sigstore.dev/cosign/signing/signing_with_containers/>

## License

Proprietary — internal use.
