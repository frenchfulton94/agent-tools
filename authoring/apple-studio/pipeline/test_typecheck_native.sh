#!/bin/bash
# Self-test for typecheck_native.py: the MSL, metal-cpp, and Rust compile gates.
# Compiles for real. Needs the Metal Toolchain (`xcodebuild -downloadComponent
# MetalToolchain`), metal-cpp 26.4 in the cache (`fetch_metal_cpp.sh 26.4`), and
# network on the first run, when cargo fetches objc2-metal.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
F="$HERE/fixtures/typecheck-native"
fail=0
expect() { # expect <exit-code> <fixture> [grep-pattern] [extra args for the gate...]
  local want="$1" fx="$2" pat=""
  shift 2
  if [ $# -gt 0 ]; then pat="$1"; shift; fi
  out="$(python3 "$HERE/typecheck_native.py" "$F/$fx" "$@" 2>&1)"; rc=$?
  if [ "$rc" != "$want" ]; then echo "FAIL $fx: exit $rc, want $want"; echo "$out" | tail -8; fail=1; return; fi
  if [ -n "$pat" ] && ! grep -q -- "$pat" <<<"$out"; then echo "FAIL $fx: no '$pat' in output"; echo "$out" | tail -8; fail=1; return; fi
  echo "ok   $fx -> $rc"
}

# The cpp cases need the pinned metal-cpp in the default cache.
"$HERE/fetch_metal_cpp.sh" 26.4 >/dev/null || { echo "FAIL fetch_metal_cpp.sh 26.4"; exit 1; }

expect 0 metal-ok.md
expect 1 metal-invented.md "undeclared identifier"
expect 2 metal-no-directive.md "no '> typecheck-metal:' directive"
expect 2 metal-bad-std.md "metal9.9"
expect 0 cpp-ok.md
expect 1 cpp-invented.md "no member named"
EMPTY="$(mktemp -d "${TMPDIR:-/tmp}/typecheck-native-empty.XXXXXX")"
expect 2 cpp-missing-cache.md "not in cache" --cache "$EMPTY"   # an empty cache dir
rmdir "$EMPTY"
expect 0 rust-ok.md
expect 1 rust-invented.md "cannot find"
expect 2 rust-unresolvable.md "dependency"      # objc2-metal = "=0.0.0"
expect 2 ungated-fence.md "ungated fence language: objc"
expect 0 ungated-config-ok.md                   # P3: toml, json, text, bash, and bare fences pass; swift is not this gate's
exit $fail
