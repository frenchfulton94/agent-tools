#!/bin/bash
# Self-test for typecheck_snippets.py's target directive (ios, macos, and
# multi-target). Needs an installed iPhoneOS SDK >= 27.0 and a macOS SDK >= 27.0;
# compiles for real, so allow a few minutes.
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
expect 2 bad-directive.md "expected '<macos|ios>"
expect 2 too-new.md "older than the directive"
expect 0 uikit.md                           # UIKit hint imports UIKit
# Phase 10: the macOS target and the multi-target directive.
expect 0 macos-floor-ok.md                              # MTL4CommandQueue under macos 26.0
expect 1 macos-floor-too-old.md "only available in macOS 26"   # same code, macos 15.0
expect 2 macos-too-new.md "older than the directive"    # macos 99.0 > the installed SDK
expect 0 multi-target.md                                # an NSView and a UIView snippet, macos 26.0, ios 26.0
expect 1 multi-target-invented.md "cannot find"
# Phase 10 Task 13 (ruling P50): a block with `#if os(` compiles on every
# declared target. Its iOS branch is empty code on macOS, so passing one target
# proves nothing about the other.
expect 0 multi-target-wrapped-ok.md "PASS.*@ ios 26.0"
expect 0 multi-target-wrapped-ok.md "PASS.*@ macos 26.0"
expect 1 multi-target-wrapped-broken.md "inventedDisplayScale"
exit $fail
