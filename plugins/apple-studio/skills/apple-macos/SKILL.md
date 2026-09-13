---
name: apple-macos
description: Building proper native Mac apps with SwiftUI - app and scene structure (WindowGroup, Window, Settings, DocumentGroup, MenuBarExtra), document-based and menu bar apps, window management and restoration, the menu and commands system, keyboard shortcuts, toolbars, focus, AppKit interop via NSViewRepresentable and coordinators, App Sandbox, entitlements, security-scoped bookmarks, and file-access patterns. Also owns which-Mac-path judgment (native SwiftUI vs Mac Catalyst vs iPad app on Apple silicon). Use when structuring a Mac app, adding scenes, menus, commands, or shortcuts, wrapping AppKit views, or debugging sandbox and file-access behavior. Not for look-and-feel or HIG judgment (apple-design), distribution and signing (app-release), or iOS-only work.
---

# Native macOS (structure and mechanics)

Scope: how a proper Mac app is built. Look/feel/HIG judgment belongs to
apple-design; distribution and signing to app-release; the build/run loop
to xcode-loop.

Read the reference for the decision at hand:
- Which Mac path, scene types, document/menu-bar app shapes, lifecycle → `references/mac-app-structure.md`
- Windows, menus, commands, shortcuts, toolbars, focus → `references/mac-windows-menus-commands.md`
- SwiftUI falls short on Mac, AppKit escape hatches → `references/appkit-interop.md`
- Sandbox, entitlements, scoped bookmarks, file access → `references/mac-sandbox-and-files.md`

Rules that always apply:
- A Mac app is judged by its menus, shortcuts, and windows - wire the
  commands system early, not as polish.
- Design with the sandbox on from day one: retrofitting entitlements and
  scoped bookmarks onto an existing file model is rework.
- Reach for AppKit interop only after checking the current SwiftUI surface
  (appkit-interop.md's decision framework) - the gap list shrinks; verify
  against live docs before wrapping.
- Mac users expect restoration - windows, sizes, state. If it vanishes on
  relaunch, that is a bug, not a nicety.
- Look/feel and idiom questions → apple-design; shipping and signing →
  app-release.
