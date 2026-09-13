> verified: 2026-08 against Xcode 27.0 beta, by execution
> sources: none (empirical)

# Xcode MCP bridge

Xcode 27 ships `xcrun mcpbridge`, a STDIO bridge between MCP clients and Xcode's own
MCP tool service. Confirmed present on this toolchain — `xcrun mcpbridge --help` prints:

```
STDIO Bridge for Xcode MCP Tools

USAGE: mcpbridge <command> [options]

COMMANDS:
  run-agent  Launch a coding agent with Xcode-provided configuration

DESCRIPTION:
    Without a subcommand, acts as a STDIO bridge between MCP (Model Context
    Protocol) clients and Xcode's MCP tool service. Reads JSON-RPC 2.0
    messages from stdin and forwards responses to stdout.
```

Re-run that exact command on any later beta before trusting this file — if it errors or the
binary is gone, mcpbridge is unavailable on that toolchain and `headless-commands.md` is the
only path; update this note when re-verified.

## Setup

1. In Xcode: **Settings → Intelligence → "Allow external agents to use Xcode tools"** must be
   enabled. Without it the bridge has nothing to connect to even if the binary works.
2. Register it as an MCP server for the agent:

   ```bash
   claude mcp add --transport stdio xcode -- xcrun mcpbridge
   ```

3. Xcode must have the target project open for project-aware operations (edits, builds tied
   to the open workspace) to work through the bridge.

## When to prefer it over headless commands

- Xcode already has the project open in this session — bridge operations share that state
  (open documents, current scheme/destination selection, live diagnostics) instead of
  spawning a fresh `xcodebuild` process.
- You want project-aware edits or refactors that go through Xcode's own indexer, not just a
  build/test invocation.

## Fallback rule

Headless CLI (`headless-commands.md`) is the default and the only option in CI or when Xcode
isn't running with the project open. Prefer it when:
- No interactive Xcode session exists (CI, background verification loops).
- The `xcode` MCP server isn't connected, or the Intelligence setting above isn't enabled.
- You need deterministic, scriptable output (exit codes, `-resultBundlePath`) rather than an
  interactive bridge session.

Don't block on the bridge — if it's unavailable or unconfigured, fall through to headless
commands without asking the user to fix Xcode settings first.
