# apple-studio

Studio-quality Apple app development — distilled architecture, concurrency,
testing, design, release, on-device intelligence, and performance guidance for
SwiftUI and Swift 6 apps.

## Install

    claude plugin marketplace add frenchfulton94/agent-tools --scope project
    claude plugin install apple-studio@agent-tools --scope project

Or for local testing, from the marketplace root:

```bash
claude --plugin-dir plugins/apple-studio
claude plugin validate plugins/apple-studio --strict
```

## Components

| Component | Shape | Covers |
|---|---|---|
| `swift-architecture` | Skill | App architecture, state and dependency injection in SwiftUI, module boundaries, persistence choice, working safely in shipped code |
| `swift-concurrency` | Skill | Actor isolation, `Sendable`, structured concurrency, cancellation, migrating GCD and Combine to async/await |
| `swift-testing` | Skill | The Swift Testing framework, what to test at each layer, protocol-based doubles without a mocking framework |
| `apple-design` | Skill | Human Interface Guidelines conformance — layout, Dynamic Type, color and materials, navigation and modality, platform idioms, accessibility |
| `apple-animations` | Skill | SwiftUI motion — springs and timing, `Transaction`, phase and keyframe animators, transitions, `matchedGeometryEffect`, scroll effects, shader modifiers |
| `apple-macos` | Skill | Native Mac apps — scene structure, windows and restoration, menus and commands, AppKit interop, sandbox and entitlements |
| `apple-frameworks` | Skill | What Apple ships and what each framework costs — privacy, entitlements, availability, pitfalls — with primers for the sixteen most apps use |
| `apple-intelligence` | Skill | On-device generative AI — Foundation Models sessions, guided generation, tool calling, guardrails and refusals, App Intents |
| `apple-performance` | Skill | Why an app is slow and how to measure it — Instruments templates, `xctrace`, signposts, hangs against hitches, launch time, MetricKit |
| `app-release` | Skill | Signing and provisioning, TestFlight, App Store submission, privacy manifests, version and build numbering, push notifications, Xcode Cloud |
| `xcode-loop` | Skill | Build, test, run, and screenshot from the command line or Xcode's MCP bridge |
| `track_swift_edits.sh` | PostToolUse hook | Records that Swift files were edited this session |
| `stop_gate.sh` | Stop hook | Requires a green build before a session ends, if Swift files were edited |

## The Stop hook

This is the only plugin in the catalog that can block a session from ending.
Detection is scoped to the `Edit`, `Write`, and `MultiEdit` tools: a Swift file
touched through `Bash` — `sed -i`, a heredoc, `git apply` — sets no marker, and
the gate passes silently. Within that scope, if a Swift file was edited and an
Xcode project sits in the working directory or one of its two parent
directories (three directories checked in total), `stop_gate.sh` builds the
first scheme and blocks on failure, reporting up to five compiler errors.

It fails open everywhere it can: no `jq`, no project, no scheme, or a
destination that does not apply to the project all let the session end
normally. The timeout is 180 seconds.

## Why this is its own plugin

Everything here serves one person: someone writing a native Apple app. That
audience shares nothing with the catalog's web and infrastructure plugins — a
SvelteKit developer installing `frontend` has no use for provisioning profiles,
and someone shipping to the App Store does not want Tailwind guidance arriving
alongside their signing help.

`design-engineering`'s `fluid-interfaces` skill covers the same Apple motion
principles for the web and Svelte. The two are separated by platform, not by
topic.

## Provenance

Authored by Michael French Fulton Jr. Built over eight phases against live
Apple documentation, the shipped SDK's `.swiftinterface` files, and runtime
measurement on Xcode 27 / macOS 27 / Swift 6.4. The distillation pipeline,
design specs, and phase plans live in `authoring/apple-studio/`.

## License

MIT.
