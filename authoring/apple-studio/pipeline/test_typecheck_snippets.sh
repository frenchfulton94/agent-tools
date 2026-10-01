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
