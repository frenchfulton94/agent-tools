---
name: xcode-loop
description: Build, test, run, and screenshot Apple-platform apps from the command line or via Xcode's MCP bridge. Use when the user asks to build or run an iOS/macOS app, run its tests, boot a simulator, capture app screenshots, or verify that a Swift change actually works.
---

# Xcode build/test/run loop

Two drive modes. Pick per session:
1. **Xcode MCP bridge** — if the `xcode` MCP server is connected and Xcode has the project open, prefer it. See `references/mcpbridge.md`.
2. **Headless CLI** — the default and the only CI option. Follow `references/headless-commands.md` exactly; every command there was verified on Xcode 27.

Core loop for verifying a change: build → run tests with a result bundle → parse the bundle → if UI-relevant, install+launch in a booted simulator and screenshot.

Rules:
- Discover schemes/destinations with the discovery commands first; never guess scheme names.
- Mac-target destinations (window/scene/menu-bar structure and mechanics) are covered by the `apple-macos` skill, not here.
- Always pass `-quiet` for builds; full logs only when diagnosing a failure.
- On failure, show the actual `error:` lines, not a summary of them.
- Screenshots: boot → bootstatus → install → launch → `simctl io booted screenshot` (iPhone Duo: pass `--display`; see references/headless-commands.md § 9).
- Builds, tests and runs; it does not explain *why* something is slow — profiling,
  hangs, memory growth and launch time are the `apple-performance` skill.
