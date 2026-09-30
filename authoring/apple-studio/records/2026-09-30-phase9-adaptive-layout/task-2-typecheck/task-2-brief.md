### Task 2: `typecheck_snippets.py` gains a per-file iOS target

**Files:**
- Modify: `$AS/pipeline/typecheck_snippets.py` (`run`, `check`, `main`, `FRAMEWORK_HINTS`, `preamble_for`)
- Create: `$AS/pipeline/fixtures/typecheck/{ios-only.md,macos-default.md,invented.md,bad-directive.md,too-new.md,uikit.md}`
- Create: `$AS/pipeline/test_typecheck_snippets.sh`
- Modify: `$AS/CONVENTIONS.md` (§ Pipeline tooling, the `typecheck_snippets.py` bullet)

**Interfaces:**
- Produces: header directive `> typecheck: ios <major>.<minor>`; exit codes 0 (all clean), 1 (a snippet failed), 2 (directive malformed or SDK older than directive). `check(code, prior, ios=None)`, `run(src, extra, ios=None)`, `ios_target(text) -> str | None`. Tasks 4 and 7 rely on the directive.

- [ ] **Step 1: Write the fixtures.** Each is a tiny markdown file. The fixtures use 27.0 APIs, so this task runs on the installed 27.0 SDK.

`ios-only.md`, `invented.md`, and `macos-default.md` share one snippet, with one character changed in `invented.md` (`ToolbarOverflowMenuu`) and the directive line removed in `macos-default.md`:

````markdown
> typecheck: ios 27.0

```swift
struct OverflowProbe: View {
    var body: some View {
        Text("Body")
            .toolbar {
                ToolbarOverflowMenu {
                    Button("Print", systemImage: "printer") {}
                }
            }
    }
}
```
````

`bad-directive.md`: the same snippet with the header `> typecheck: iOS27`.
`too-new.md`: the same snippet with the header `> typecheck: ios 99.0`.
`uikit.md`:

````markdown
> typecheck: ios 27.0

```swift
final class ProbeViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
    }
}
```
````

- [ ] **Step 2: Write the failing test.** Create `$AS/pipeline/test_typecheck_snippets.sh`:

```bash
#!/bin/bash
# Self-test for typecheck_snippets.py's iOS directive. Needs an installed
# iPhoneOS SDK >= 27.0; compiles for real, so allow ~1 minute.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
F="$HERE/fixtures/typecheck"
fail=0
expect() { # expect <exit-code> <fixture> [grep-pattern]
  out="$(python3 "$HERE/typecheck_snippets.py" "$F/$2" 2>&1)"; rc=$?
  if [ "$rc" != "$1" ]; then echo "FAIL $2: exit $rc, want $1"; echo "$out" | tail -5; fail=1; return; fi
  if [ -n "${3:-}" ] && ! grep -q "$3" <<<"$out"; then echo "FAIL $2: no '$3' in output"; fail=1; return; fi
  echo "ok   $2 -> $rc"
}
expect 0 ios-only.md                        # iOS-only API passes under the directive
expect 1 macos-default.md "unavailable in macOS"   # same code, no directive: macOS, fails
expect 1 invented.md "cannot find"          # invented symbol still fails under iOS
expect 2 bad-directive.md "expected 'ios <major>.<minor>'"
expect 2 too-new.md "older than the directive"
expect 0 uikit.md                           # UIKit hint imports UIKit
exit $fail
```

- [ ] **Step 3: Run it to verify it fails.** `bash $AS/pipeline/test_typecheck_snippets.sh`. Expected: `ios-only.md` fails with exit 1 (no directive support, compiles for macOS), `bad-directive.md` and `too-new.md` exit 1 not 2, `uikit.md` exits 1. Save output to `task-2-typecheck/red.log`.

- [ ] **Step 4: Record the whole-catalog baseline before changing the script.**

```bash
python3 $AS/pipeline/typecheck_snippets.py plugins/apple-studio/skills/*/references/*.md plugins/apple-studio/skills/*/references/primers/*.md > $AS/records/2026-09-30-phase9-adaptive-layout/task-2-typecheck/catalog-before.log 2>&1; tail -1 $AS/records/2026-09-30-phase9-adaptive-layout/task-2-typecheck/catalog-before.log
```

Expected: a `TOTAL: <ok>/<n>` line. Record it; Step 7 compares against it.

- [ ] **Step 5: Implement.** In `$AS/pipeline/typecheck_snippets.py`:

  1. Add to `FRAMEWORK_HINTS`, after the SwiftUI entry:

```python
    # Added Phase 9 for the iOS directive. UIKit snippets only make sense in a
    # file that declares `> typecheck: ios <version>`; on macOS UIKit does not
    # exist and every one of them fails.
    ("UIKit",           r"\b(UIViewController|UIView\b|UIBarButtonItem|UINavigationItem|UITraitCollection|UISheetPresentationController|UIArrangementViewController)"),
```

  2. Add to `preamble_for`'s `BINDINGS`: `("proxy", "GeometryProxy", "SwiftUI"),`. Do **not** rebind `view`; existing snippets depend on `view: __View`. UIKit snippets in references are written as full declarations instead (see Task 4).

  3. Add, above `run`:

```python
DIRECTIVE = re.compile(r"^> typecheck:\s*(.*?)\s*$", re.M)

class DirectiveError(Exception):
    pass

def ios_target(text):
    """Return the iOS version a reference declares, or None for the macOS default."""
    m = DIRECTIVE.search(text)
    if not m:
        return None
    v = re.fullmatch(r"ios (\d+\.\d+)", m.group(1))
    if not v:
        raise DirectiveError(f"bad directive {m.group(1)!r}: expected 'ios <major>.<minor>'")
    want = v.group(1)
    have = subprocess.run(["xcrun", "--sdk", "iphoneos", "--show-sdk-version"],
                          capture_output=True, text=True).stdout.strip()
    as_tuple = lambda s: tuple(int(x) for x in s.split("."))
    if not have or as_tuple(have) < as_tuple(want):
        raise DirectiveError(f"installed iPhoneOS SDK {have or '(none)'} is older than the directive ios {want}")
    return want
```

  4. Change `run(src, extra)` to `run(src, extra, ios=None)`. When `ios` is set, replace the macOS `-F` framework path with the iOS SDK and target:

```python
        if ios:
            sdk = subprocess.run(["xcrun", "--sdk", "iphoneos", "--show-sdk-path"],
                                 capture_output=True, text=True).stdout.strip()
            plat = subprocess.run(["xcrun", "--sdk", "iphoneos", "--show-sdk-platform-path"],
                                  capture_output=True, text=True).stdout.strip()
            fw = ["-sdk", sdk, "-target", f"arm64-apple-ios{ios}",
                  "-F", f"{plat}/Developer/Library/Frameworks"]
        else:
            SDK_F = "/Applications/Xcode-beta.app/Contents/Developer/Platforms/MacOSX.platform/Developer/Library/Frameworks"
            fw = ["-F", SDK_F] if os.path.isdir(SDK_F) else []
```

  5. Change `check(code, prior="")` to `check(code, prior="", ios=None)` and pass `ios` to every `run(src, extra, ios)` call.

  6. In `main`, per file: call `ios = ios_target(text)` inside `try`; on `DirectiveError as e`, print `FILE: <path>  DIRECTIVE ERROR: <e>` and remember to exit 2. Print `target: ios <v>` or `target: macOS (default)` on the FILE line. Pass `ios` to `check`. At the end, exit 2 if any directive error occurred, else 0/1 as today.

  7. Add to the module docstring, after USAGE: a paragraph stating the directive, its format, the exit codes, and that it was added in Phase 9 because the Duo APIs include iOS-only symbols that fail on the macOS default.

- [ ] **Step 6: Run the test to verify it passes.** `bash $AS/pipeline/test_typecheck_snippets.sh | tee $AS/records/2026-09-30-phase9-adaptive-layout/task-2-typecheck/green.log`. Expected: six `ok` lines, exit 0.

- [ ] **Step 7: Prove no regression on files without the directive.** Re-run Step 4's command into `catalog-after.log`. Expected: the identical `TOTAL:` line, and `diff <(grep -E 'PASS|FAIL' catalog-before.log) <(grep -E 'PASS|FAIL' catalog-after.log)` prints nothing.

- [ ] **Step 8: Document the directive.** In `$AS/CONVENTIONS.md`, append to the `pipeline/typecheck_snippets.py` bullet (after "…is the ship gate for any API-specific claim."):

```markdown
  A reference whose APIs are iOS-only declares `> typecheck: ios <major>.<minor>`
  in its header block; the script then compiles that file against the iPhoneOS
  SDK. Without the directive a file compiles for macOS, which is correct for
  cross-platform SwiftUI and wrong for UIKit or iOS-only SwiftUI. A malformed
  directive, or one newer than the installed SDK, exits 2 rather than falling
  back. (Amended 2026-09-30, Phase 9.)
```

- [ ] **Step 9: Commit.**

```bash
git add $AS/pipeline/typecheck_snippets.py $AS/pipeline/test_typecheck_snippets.sh $AS/pipeline/fixtures/typecheck $AS/CONVENTIONS.md $AS/records/2026-09-30-phase9-adaptive-layout/task-2-typecheck
git commit -m "Phase 9 Task 2: per-file iOS target for the snippet ship gate

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

