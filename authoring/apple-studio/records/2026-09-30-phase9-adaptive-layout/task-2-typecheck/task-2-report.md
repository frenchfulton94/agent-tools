# Task 2 report: `typecheck_snippets.py` gains a per-file iOS target

## What was implemented

`authoring/apple-studio/pipeline/typecheck_snippets.py`:

1. `FRAMEWORK_HINTS` gained a `UIKit` entry (after the SwiftUI entry), matching
   `UIViewController|UIView\b|UIBarButtonItem|UINavigationItem|UITraitCollection|
   UISheetPresentationController|UIArrangementViewController`, with a WHY comment
   naming Phase 9.
2. `preamble_for`'s `BINDINGS` gained `("proxy", "GeometryProxy", "SwiftUI")`.
   `view` was left unchanged (existing snippets depend on `view: __View`).
3. Added `DIRECTIVE` regex (`^> typecheck:\s*(.*?)\s*$`), `DirectiveError`
   exception, and `ios_target(text)`, which returns the declared iOS version,
   `None` when no directive is present, or raises `DirectiveError` for a
   malformed directive or one naming an iOS version newer than the installed
   iPhoneOS SDK.
4. `run(src, extra)` -> `run(src, extra, ios=None)`. When `ios` is set, compiles
   with `-sdk <iphoneos sdk path> -target arm64-apple-ios<ios> -F <platform>/
   Developer/Library/Frameworks` (iphoneos platform path), exactly as the brief's
   Step 5.4 specifies.
5. **Ruling 7 (macOS branch, deviates from the brief's Step 5.4 text):** the
   brief's hardcoded `SDK_F = ".../Xcode-beta.app/.../MacOSX.platform/.../
   Frameworks"` no longer exists on this machine — the installed Xcode 27.1 beta
   is `/Applications/Xcode 27-1-beta.app`, a different name, so the old
   `os.path.isdir()` guard silently returned false and dropped the
   AppIntentsTesting framework path from every macOS compile. Per the
   controller's ruling, the macOS branch now derives the path instead:
   `plat = xcrun --sdk macosx --show-sdk-platform-path` -> `-F <plat>/Developer/
   Library/Frameworks`, kept only if that directory exists (same guard as
   before). The module docstring's AppIntentsTesting sentence was updated to
   match.
6. `check(code, prior="")` -> `check(code, prior="", ios=None)`; `ios` is
   threaded through the single `run(src, extra, ios)` call site used by every
   attempt in the loop.
7. `main()`: per file, `ios = ios_target(text)` runs inside a `try`; a
   `DirectiveError` prints `FILE: <path>  DIRECTIVE ERROR: <e>`, sets a
   `directive_error` flag, and `continue`s — the file's swift blocks are never
   compiled, so a malformed or too-new directive never silently falls back to
   macOS. Otherwise the FILE line also prints `target: ios <v>` or
   `target: macOS (default)`, and `ios` is passed to `check`. At the end, exit 2
   if any directive error occurred (checked first, before 0/1), else 0/1 as
   before.
8. Module docstring gained an "IOS DIRECTIVE (added Phase 9)" paragraph after
   the USAGE/exit-code line, stating the directive syntax, that it targets the
   iPhoneOS SDK, why it exists (Duo/adaptive-layout APIs are iOS-only and fail
   to typecheck on macOS), and all three exit codes.

Fixtures created under `authoring/apple-studio/pipeline/fixtures/typecheck/`:
`ios-only.md`, `macos-default.md`, `invented.md`, `bad-directive.md`,
`too-new.md`, `uikit.md` — verbatim from the brief's Step 1.

`authoring/apple-studio/pipeline/test_typecheck_snippets.sh` created verbatim
from the brief's Step 2, made executable.

`authoring/apple-studio/CONVENTIONS.md`: appended the directive paragraph to
the `pipeline/typecheck_snippets.py` bullet, verbatim from the brief's Step 8.

## TDD evidence

**RED** — `bash authoring/apple-studio/pipeline/test_typecheck_snippets.sh`,
before any script changes, saved to `red.log`:

```
FAIL ios-only.md: exit 1, want 0
...
TOTAL: 0/1 snippets typecheck clean
ok   macos-default.md -> 1
ok   invented.md -> 1
FAIL bad-directive.md: exit 1, want 2
...
FAIL too-new.md: exit 1, want 2
...
FAIL uikit.md: exit 1, want 0
...
```

Matches the brief's Step 3 expectation exactly: `ios-only.md` fails (no
directive support yet, compiles for macOS), `bad-directive.md`/`too-new.md`
exit 1 not 2, `uikit.md` exits 1.

**GREEN** — same command after implementation, saved to `green.log`:

```
ok   ios-only.md -> 0
ok   macos-default.md -> 1
ok   invented.md -> 1
ok   bad-directive.md -> 2
ok   too-new.md -> 2
ok   uikit.md -> 0
```

Confirmed separately: `bash .../test_typecheck_snippets.sh; echo EXIT=$?` ->
`EXIT=0`.

## Catalog before/after (Step 4 / Step 7)

Command (both runs): `python3 pipeline/typecheck_snippets.py
plugins/apple-studio/skills/*/references/*.md
plugins/apple-studio/skills/*/references/primers/*.md`, run against the
default toolchain (`xcode-select` -> `/Applications/Xcode.app`, Xcode 27.0,
iPhoneOS 27.0 SDK). No file in the catalog carries the new directive yet
(Task 4 adds it), so every file compiles for macOS exactly as before —
this run is a regression check on the macOS path (including Ruling 7's
framework-path change), not an iOS-directive test.

- `catalog-before.log` (captured before any script edit): `TOTAL: 31/51
  snippets typecheck clean`
- `catalog-after.log` (captured after implementation): `TOTAL: 32/51
  snippets typecheck clean`

**One flip, FAIL -> PASS** (recorded in `catalog-diff.log` per Ruling 3):

- File: `plugins/apple-studio/skills/apple-intelligence/references/
  app-intents-implementation.md`
- Snippet #3: `let definitions = IntentDefinitions(bundleIdentifier:
  "com.example.my-ap...` — was `[FAIL]`, now `[PASS:with-prior+ctx]`.
- Cause: Ruling 7. The old hardcoded Xcode-beta.app path no longer exists
  on this machine, so the AppIntentsTesting framework search path was
  silently absent from every macOS compile before this change. Deriving the
  path from `xcrun --sdk macosx --show-sdk-platform-path` restores it, and
  this snippet (which needs `AppIntentsTesting`/`IntentDefinitions`) now
  compiles. Per Ruling 3, this is an improvement, not a regression — no
  fix required.
- No PASS -> FAIL flips (full `diff <(grep -E 'PASS|FAIL' catalog-before.log)
  <(grep -E 'PASS|FAIL' catalog-after.log)` produced exactly the one line
  above).

The new `proxy`/`GeometryProxy` binding produced no flips in the current
catalog — no existing reference uses an undeclared `proxy` binding today.

## Files changed

- `authoring/apple-studio/pipeline/typecheck_snippets.py` (modified)
- `authoring/apple-studio/pipeline/test_typecheck_snippets.sh` (new)
- `authoring/apple-studio/pipeline/fixtures/typecheck/{ios-only,macos-default,
  invented,bad-directive,too-new,uikit}.md` (new)
- `authoring/apple-studio/CONVENTIONS.md` (modified)
- `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/
  task-2-typecheck/{red.log,green.log,catalog-before.log,catalog-after.log,
  catalog-diff.log,task-2-report.md}` (new)

## Self-review

- Completeness against the brief: all 9 steps done, fixtures/test/script/docs
  match the brief's interfaces (`check(code, prior, ios=None)`,
  `run(src, extra, ios=None)`, `ios_target(text) -> str | None`, exit codes
  0/1/2, directive `> typecheck: ios <major>.<minor>`).
- Ruling 7 applied only to the macOS branch of `run()`; the iOS branch and
  everything else in Step 5.4 is verbatim from the brief.
- Ruling 3 applied: the one FAIL->PASS flip was investigated, attributed to
  Ruling 7, and recorded here and in `catalog-diff.log`; confirmed no
  PASS->FAIL flips via the full diff.
- Malformed-directive (`bad-directive.md`, "iOS27") and too-new (`too-new.md`,
  "ios 99.0") paths: verified in code that `main()` raises/catches
  `DirectiveError` and `continue`s before any block is ever compiled for that
  file — there is no code path that falls back to compiling those files for
  macOS. GREEN run confirms both exit 2 with the expected message substrings.
- Style: new code carries WHY comments naming Phase 9 (UIKit hint, macOS
  framework-path derivation, directive handling in `main`), matching the
  file's existing convention (e.g. the Phase 7 CoreGraphics comment).
- Test output is pristine: GREEN log has six `ok` lines, no stray FAILs; the
  self-test's own exit code is 0.
- Xcode selection was not touched; ran throughout under the default
  `/Applications/Xcode.app` (27.0 toolchain, iPhoneOS 27.0 SDK), which
  satisfies the fixtures' `ios 27.0` directive.

## Concerns

- The catalog-wide `TOTAL` line changed (31/51 -> 32/51) rather than staying
  identical, because of the Ruling-7 framework-path fix improving one
  pre-existing snippet. This is expected and sanctioned by Ruling 3, not a
  defect, but it means Step 7's literal "identical TOTAL" expectation from the
  brief does not hold — the ruling supersedes it.
- No reference in the catalog yet declares `> typecheck: ios ...`; Task 4 is
  expected to add the directive to the Duo/adaptive-layout references that
  need it. This task only proves the mechanism works (fixtures + self-test)
  and that it does not regress the existing macOS-only catalog.
