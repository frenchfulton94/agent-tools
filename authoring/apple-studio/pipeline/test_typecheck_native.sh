#!/bin/bash
# Self-test for typecheck_native.py: the MSL, metal-cpp, and Rust compile gates.
# Compiles for real. Needs the Metal Toolchain (`xcodebuild -downloadComponent
# MetalToolchain`), metal-cpp 26.4 in the cache (`fetch_metal_cpp.sh 26.4`), and
# network on the first run, when cargo fetches objc2-metal.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
F="$HERE/fixtures/typecheck-native"
fail=0
GATE="${NATIVE_GATE:-$HERE/typecheck_native.py}"   # override only to run the self-test against another copy
expect() { # expect <exit-code> <fixture> [grep-pattern] [extra args for the gate...]
  local want="$1" fx="$2" pat=""
  shift 2
  if [ $# -gt 0 ]; then pat="$1"; shift; fi
  out="$(python3 "$GATE" "$F/$fx" "$@" 2>&1)"; rc=$?
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
EMPTY_OUT="$(mktemp "${TMPDIR:-/tmp}/typecheck-native-race.XXXXXX")"
EMPTY="$(mktemp -d "${TMPDIR:-/tmp}/typecheck-native-empty.XXXXXX")"
expect 2 cpp-missing-cache.md "not in cache" --cache "$EMPTY"   # an empty cache dir
rmdir "$EMPTY"
expect 0 rust-ok.md
expect 1 rust-invented.md "cannot find"
expect 2 rust-unresolvable.md "dependency"      # objc2-metal = "=0.0.0"
expect 2 ungated-fence.md "ungated fence language: objc"
expect 0 ungated-config-ok.md                   # P3: toml, json, bash, and text fences pass; swift is not this gate's

# Fix round 1. A fence the Swift gate would not parse must not pass both gates silently.
expect 2 swift-case.md "swift fence the Swift gate cannot parse: \`\`\`Swift"   # invented API under ```Swift and ~~~swift
expect 2 bare-fence.md "unlabelled fence: label it text, or a gated language"
expect 2 fence-info.md "fence not in the exact form"       # ```metal title="..."
expect 2 fence-tilde.md "fence not in the exact form"      # ~~~text
expect 0 rust-prior.md                          # a with-prior pass must not leave a duplicate `use` in the context
expect 0 rust-dup-use.md                        # nor may two as-written passes that each write the same `use`
expect 2 swift-formfeed.md "swift fence the Swift gate cannot parse"   # ```swift + form feed: splitlines() would hide it from both gates

# Fix round 1. Two runs that share one `> typecheck-rust:` directive must not share a
# source file: an invented symbol has to fail every time, whatever the other run does.
for round in 1 2 3 4 5 6; do
  python3 "$GATE" "$F/rust-race-x.md" >"$EMPTY_OUT.x" 2>&1 & px=$!
  python3 "$GATE" "$F/rust-race-y.md" >"$EMPTY_OUT.y" 2>&1 & py=$!
  wait $px; rx=$?
  wait $py; ry=$?
  if [ "$rx" != 1 ] || [ "$ry" != 0 ]; then
    echo "FAIL rust-race round $round: invented exit $rx (want 1), correct exit $ry (want 0)"; fail=1
  else
    echo "ok   rust-race round $round -> invented 1, correct 0"
  fi
done
rm -f "$EMPTY_OUT" "$EMPTY_OUT.x" "$EMPTY_OUT.y"
exit $fail
