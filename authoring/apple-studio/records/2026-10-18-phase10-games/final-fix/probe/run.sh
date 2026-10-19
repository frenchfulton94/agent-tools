#!/bin/bash
# Phase 10 final fix, F1: build and run the sendOverDTLS probe.
#
# usage: run.sh <build-dir> [long]
#
# Without `long`: every short case, in order (about 40 s). With `long`: the
# d742a42 branches against the two peers that never answer, with a 180 s
# deadline, run in parallel; each case's output is printed when all end.
#
# Extracts the ```swift block that defines sendOverClassicDTLS from the
# reference, compiles it verbatim with instrumented.swift and main.swift, and
# runs every case. Each case has a deadline inside the probe, and perl's alarm
# kills the process if the probe itself hangs. Writes nothing outside
# <build-dir>; the log goes to stdout.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../../../../.." && pwd)"
ref="$root/plugins/apple-studio/skills/apple-games/references/game-center-and-online.md"
build="${1:?usage: run.sh <build-dir> [long]}"
mode="${2:-short}"
mkdir -p "$build"

python3 -I - "$ref" "$build/snippet.swift" <<'PY'
import re, sys
text = open(sys.argv[1]).read()
blocks = re.findall(r"```swift\n(.*?)```", text, re.S)
hits = [b for b in blocks if "func sendOverClassicDTLS" in b]
assert len(hits) == 1, f"expected one block, found {len(hits)}"
open(sys.argv[2], "w").write(hits[0])
PY

echo "== build"
echo "reference: plugins/apple-studio/skills/apple-games/references/game-center-and-online.md"
echo "snippet sha256: $(shasum -a 256 "$build/snippet.swift" | cut -d' ' -f1)"
xcrun swiftc -swift-version 6 -target arm64-apple-macos26.0 \
    -module-name dtlsprobe -o "$build/dtls-probe" \
    "$build/snippet.swift" "$here/instrumented.swift" "$here/main.swift"
echo "build: ok (swiftc -swift-version 6 -target arm64-apple-macos26.0)"
sw_vers

run() {
    echo
    echo "== $*"
    set +e
    perl -e 'alarm shift; exec @ARGV' 30 "$build/dtls-probe" "$@"
    echo "exit: $?"
    set -e
}

if [ "$mode" = long ]; then
    for f in original26 original27; do
        for e in refused blackhole; do
            perl -e 'alarm shift; exec @ARGV' 200 "$build/dtls-probe" "$f" "$e" plain 180 \
                > "$build/long-$f-$e.log" 2>&1 &
        done
    done
    wait
    for f in original26 original27; do
        for e in refused blackhole; do
            echo; echo "== $f $e plain 180"; cat "$build/long-$f-$e.log"
        done
    done
    exit 0
fi

# The bug: both d742a42 branches against a peer that leaves them waiting.
run original26 unresolvable plain 8
run original27 unresolvable plain 8
run original27 unresolvable cancel-after-1s
# A framework fault: the OS 27 send, started in a task that is already
# cancelled, never resumes. The fixed function checks cancellation first.
run original27 unresolvable precancelled 4
# The fixed function (send timeout 2 s), each peer shape, both branches.
run fixed26 unresolvable plain
run fixed26 refused plain
run fixed26 blackhole plain
run fixed26 blackhole cancel-after-1s
run fixed26 unresolvable precancelled
run fixed27 unresolvable plain
run fixed27 refused plain
run fixed27 blackhole plain
run fixed27 blackhole cancel-after-1s
run fixed27 unresolvable precancelled
# The verbatim snippet. On this macOS 27 machine sendOverDTLS takes the OS 27
# branch. sendOverClassicDTLS, called alone, has no deadline: it ends only on
# .failed or on cancellation, so the second case shows a 1 s cancel ending it.
run verbatim unresolvable plain
run verbatim blackhole plain
run verbatim blackhole cancel-after-1s
run verbatim unresolvable precancelled
run verbatimClassic unresolvable plain 4
run verbatimClassic blackhole cancel-after-1s
