# unraid-ops

Unraid server administration for Claude Code: the know-how as a skill, a guard against the documented data-loss command patterns as a hook, a triage command that captures evidence before it is lost, and a read-only MCP server that reads the server's actual state.

Built from the official documentation at [docs.unraid.net](https://docs.unraid.net) (223 pages), current through Unraid 7.3.2 with 7.4.0-beta.1 in the tree.

## Components

| Component | Shape | Why this shape |
|---|---|---|
| `skills/managing-unraid-servers` | Skill | Repeated multi-step know-how applied in the main conversation, loaded on demand across seven domain references |
| `hooks/hooks.json` + `scripts/guard_destructive_storage.py` | Hook | Two of the gates must hold even when an agent is being reasoned at by a user mid-outage. Instructions are advisory; a `PreToolUse` deny is not |
| `commands/triage.md` | Command | `/unraid-ops:triage` — a named entry point for "something is wrong", enforcing capture-before-reboot ordering |
| `.mcp.json` + `scripts/unraid_mcp_server.py` | MCP server | Access to an external system. Lets the skill read the actual server state instead of asking about it |

## Install

    claude plugin marketplace add YOUR-GITHUB-OWNER/agent-tools --scope project
    claude plugin install unraid-ops@agent-tools --scope project

`--scope project` writes to the repository's `.claude/settings.json`, which you commit so the
plugin travels with the repo instead of living on one workstation.

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/unraid-ops
claude plugin validate plugins/unraid-ops --strict
```

Verify components registered with `claude --plugin-dir plugins/unraid-ops --debug`, then `/hooks` for the guard and the skill list for the skill.

## The MCP server

Read-only access to the Unraid GraphQL API (built into Unraid 7.2+; earlier releases get it from the Unraid Connect plugin). Stdlib-only Python over stdio, so there is nothing to install.

| Tool | Returns |
|---|---|
| `system_info` | OS platform, distro, release, uptime; CPU make, brand, cores, threads |
| `array_status` | Array state, per-disk name/size/status/temperature, capacity |
| `docker_containers` | Containers with id, names, state, status, autostart |
| `introspect_schema` | The live GraphQL schema, optionally filtered to one type |
| `query` | An arbitrary GraphQL query |

The three typed queries are taken verbatim from the documented examples. The complete schema is published in Apollo Studio rather than the docs, so `introspect_schema` exists to discover real field names at runtime instead of shipping guesses.

**Mutations are refused by default.** The API can start and stop the array and control containers and VMs — precisely the destructive surface the rest of this plugin guards. Enable `allow_mutations` deliberately, or perform the action in the WebGUI.

### Setup

On the server:

```bash
unraid-api apikey --create --name claude -r admin
```

Then configure the plugin's options: `api_url` (e.g. `http://tower.local/graphql`), `api_key` (stored as a sensitive value, not in plain settings), and `insecure_tls` if the server uses the self-signed certificate Unraid generates for local access — which it does unless you have pointed `api_url` at a `myunraid.net` address.

An `http` address is fine either way. Unraid redirects to HTTPS whenever *Use SSL/TLS* is on, and the server follows that upgrade itself, so the same setting works whether or not SSL is enabled.

Tools appear under the scoped name `mcp__plugin_unraid-ops_unraid__<tool>`.

### When it cannot reach the server

Three failures are common enough that the server answers them with the fix rather than the raw error:

- **The request is redirected.** Unraid's nginx redirects HTTP to HTTPS whenever *Use SSL/TLS* is `Yes` or `Strict`, and `urllib` downgrades the POST to a GET when it follows one, so the API is never reached. The server handles redirects itself, re-sending the POST intact. Because the API key rides in a header, it follows only a redirect that stays on the same host and path and does not drop from HTTPS to plain HTTP; anything else is reported with the endpoint to put in `api_url`.
- **The certificate is rejected.** Unraid generates a self-signed certificate for local access and Python refuses it by default. The error says so plainly rather than blaming reachability, and names `insecure_tls` and the `myunraid.net` alternative.
- **`SANDBOX_DISABLED`.** Either the GraphQL sandbox is off on a build that gates the whole `/graphql` route behind it, or the request never authenticated and fell through to the playground route. The two need different fixes, so the error names both and gives a `curl` command that tells them apart. The sandbox is an interactive query console — turn it off again when you are done.

`UNAUTHENTICATED` and `FORBIDDEN` point at the key and its role (`unraid-api apikey --list`).

## The guard

Fires on every `Bash` call, judges each shell segment independently, and returns a permission decision. `deny` is reserved for patterns that are never correct on an Unraid server; `ask` is used where the same command is legitimate on a pool or unassigned device but catastrophic on an array member — the hook cannot tell which a given `/dev/sdX` is, and pretending otherwise would be worse than asking.

| Pattern | Decision | Reason |
|---|---|---|
| `/mnt/user` and `/mnt/diskN` in one segment | deny | Two views of the same files; documented corruption path |
| Repair tool against a whole disk (`xfs_repair /dev/sdb`) | deny | Array disks repair via `/dev/mdXp1` in Maintenance Mode |
| `dd of=/dev/sdX` or `of=/dev/nvmeX` | deny | The documented zeroing procedure targets `/dev/mdXp1` so parity stays valid |
| `mkfs*` | ask | Formatting an array disk erases it *and* updates parity |
| Repair tool against a raw partition (`/dev/sdb1`) | ask | Correct for pools and unassigned devices; invalidates parity on an array member |
| `btrfs check --repair` | ask | Can worsen damage; scrub and read-only check come first |
| `zpool destroy` / `labelclear` | ask | Destroys a pool |
| `wipefs /dev/*` | ask | Removes filesystem signatures |

Commands led by a read-only tool (`grep`, `ls`, `cat`, `find`, …) skip the cross-view rule, so searching across both views is not blocked.

**Known limits.** The guard is a pattern matcher, not a model of your server. It cannot tell an array member from a pool device, cannot see which disk is parity, and will not catch a destructive action taken through the WebGUI or a script it never sees. It reduces one class of mistake; it is not a safety system. Test any change to it against `scripts/` payloads before relying on it.

## Testing the bundled scripts

Both suites run without an Unraid server, from `plugins/unraid-ops`:

```bash
python3 scripts/test/test_guard.py       # 22 command patterns
python3 scripts/test/test_mcp_server.py  # 22 protocol and behaviour checks
```

The MCP suite drives the server over stdio against a fake GraphQL endpoint, so it exercises the transport, the auth header, the mutation gate and the error paths — but not the real Unraid schema.

The guard also takes a payload on stdin directly:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"cp /mnt/disk2/x /mnt/user/x"}}' \
  | python3 scripts/guard_destructive_storage.py
```

Empty output means allow. A JSON body carries the decision. The script always exits 0 — the decision travels in the body, per the `PreToolUse` contract.

## Skill evals

`skills/managing-unraid-servers/evals/` holds a 20-query trigger battery and 5 behavior cases with PASS/FAIL assertions, for A/B runs against a baseline. They are never loaded automatically.
