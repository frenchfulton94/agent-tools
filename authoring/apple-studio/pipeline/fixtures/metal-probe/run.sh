#!/bin/bash
# Runs one runtime claim and prints its log to stdout.
#
#   run.sh r1 | r2 | r3 | r5
#
# Build first: `swift build -c release` here (R1-R3), and the two hosts (R5,
# see README.md). Traces go to the pipeline's gitignored tmp/ directory, never
# into a tracked path. Every step prints its command, its exit status, and its
# output, or a summary of it where the output is long.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(cd "$HERE/../.." && pwd)/tmp"
PROBE="$HERE/.build/release/MetalProbe"
mkdir -p "$TMP"
cd "$HERE" || exit 2

header() {
  echo "Machine: $(sysctl -n machdep.cpu.brand_string)"
  echo "OS: macOS $(sw_vers -productVersion) $(sw_vers -buildVersion)"
  echo "Toolchain: $(xcodebuild -version | head -1)"
  echo "Date: $(date '+%Y-%m-%d %H:%M %Z')"
  echo "\$TMP below is authoring/apple-studio/pipeline/tmp, the gitignored pipeline scratch"
}

# step <title> <command...>: runs the command, saves its output in $OUT,
# and sets $STATUS. The caller prints what matters from $OUT.
OUT="$TMP/step.out"
step() {
  echo
  echo "## $1"
  shift
  echo "\$ $*" | sed "s|$TMP|\$TMP|g; s|$HERE/||g"
  "$@" > "$OUT" 2>&1
  STATUS=$?
  echo "exit: $STATUS"
}

show() { sed "s|$TMP|\$TMP|g; s|$HERE/||g" "$OUT"; }

r1() {
  header
  step "Frame structure, 120 frames, no validation" "$PROBE" render --frames 120
  echo "ok lines: $(grep -c '^frame [0-9]* ok$' "$OUT")"
  echo "first: $(head -1 "$OUT")"
  grep -v '^frame [0-9]* ok$' "$OUT"
  step "Frame structure, 120 frames, API and Shader Validation, reports to stderr" \
    env MTL_DEBUG_LAYER=1 MTL_SHADER_VALIDATION=1 MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1 \
    "$PROBE" render --frames 120
  echo "ok lines: $(grep -c '^frame [0-9]* ok$' "$OUT")"
  echo "every other line:"
  grep -v '^frame [0-9]* ok$' "$OUT"
  step "The probe's compute workload" "$PROBE" compute --count 1048576
  show
}

# Runs a bash block from gpu-debugging-and-profiling.md as written, with only
# the trace name changed. bash -v echoes each line before it runs.
documented() {
  python3 "$HERE/check_verbatim.py" --block gpu-debugging-and-profiling.md "$1" \
    | sed "s|Frame.gputrace|$TRACE|g"
}

r2() {
  header
  TRACE="$TMP/probe.gputrace"
  rm -rf "$TRACE" "$TMP/nocap.gputrace" "$TMP/r2"
  mkdir -p "$TMP/r2"
  step "Capture without MTL_CAPTURE_ENABLED" "$PROBE" capture --out "$TMP/nocap.gputrace"
  show
  echo "trace written: $([ -e "$TMP/nocap.gputrace" ] && echo yes || echo no)"
  step "Capture with MTL_CAPTURE_ENABLED=1" env MTL_CAPTURE_ENABLED=1 "$PROBE" capture --out "$TRACE"
  show
  cd "$TMP/r2" || exit 2   # the blocks write fetch output to $PWD
  echo
  echo "## gpudebug: the Sessions block, verbatim (trace name changed), run in \$TMP/r2"
  documented 'gpudebug -s "$id" -c "status"' > "$TMP/r2/sessions.sh"
  bash -v "$TMP/r2/sessions.sh" 2>&1 | sed "s|$TMP|\$TMP|g"
  echo
  echo "## gpudebug: the profiling block, verbatim, after the Sessions block's first line"
  {
    documented 'gpudebug -s "$id" -c "status"' | head -1
    documented 'gpudebug -s "$id" -c "profile run --embed"'
    # The reference: "With other grouping, run go /commands/cb0 and follow the
    # listing, or find <label>." The dispatch is in its own command buffer.
    echo 'gpudebug -s "$id" -c "find add arrays"'
    echo 'gpudebug -s "$id" -c "go /commands/cb3" -c "list"'
    echo 'gpudebug -s "$id" -c "go /commands/cb3/grp0/ce0" -c "list"'
    echo 'gpudebug --terminate "$id"'
  } > "$TMP/r2/profile.sh"
  bash -v "$TMP/r2/profile.sh" 2>&1 | sed "s|$TMP|\$TMP|g"
  echo
  echo "## Files the blocks wrote"
  ls -1 "$TMP/r2"
  cd "$HERE" || exit 2

  # The same capture, but the compute pipeline is compiled after the capture
  # starts, so the trace records the MTL4Compiler call. perl's alarm stands in
  # for timeout(1), which macOS lacks: the profile otherwise never returns.
  local incapture="$TMP/probe-compile-in-capture.gputrace"
  rm -rf "$incapture"
  step "Capture with the compute pipeline compiled inside the capture" \
    env MTL_CAPTURE_ENABLED=1 "$PROBE" capture --out "$incapture" --compile-in-capture
  show
  local reports=~/Library/Logs/DiagnosticReports
  local before
  before=$(ls "$reports" | grep -c '^GPUTools')
  step "profile run on that trace, killed after 120 s" \
    perl -e 'alarm 120; exec @ARGV' gpudebug --oneshot -t "$incapture" -c "status" -c "profile run"
  show
  echo "(exit 142 is SIGALRM: the profile had not returned after 120 s)"
  # The killed client leaves its session service running; end it.
  gpudebug --terminate all > /dev/null 2>&1
  pkill -f 'GPUToolsDebugService.xpc/Contents/MacOS/GPUToolsDebugService' \
    && echo "ended the orphaned GPUToolsDebugService"
  sleep 5
  echo "new GPUTools crash reports: $(( $(ls "$reports" | grep -c '^GPUTools') - before ))"
  ls -t "$reports" | grep '^GPUTools' | head -$(( $(ls "$reports" | grep -c '^GPUTools') - before )) \
    | while read -r report; do
        python3 -I -c '
import json, sys
head, body = open(sys.argv[1]).read().split("\n", 1)
b = json.loads(body)
th = next((t for t in b["threads"] if t.get("triggered")), b["threads"][0])
names = [f.get("symbol", "?") for f in th["frames"][:2]]
print("  %s: %s, top frames %s" % (json.loads(head)["app_name"], b["exception"].get("type"), names))
' "$reports/$report"
      done
}

# xctrace_toc <trace> <process name> <label>: exports the table of contents,
# then prints the launched process, the GPU and Metal tables, and the
# command-buffer submission rows. Later rows refer to a process by id, so only
# the first rows name it in full.
xctrace_toc() {
  local trace="$1" name="$2" label="$3"
  step "xctrace export --toc, $label" xcrun xctrace export --input "$trace" --toc
  cp "$OUT" "${trace%.trace}.toc.xml"
  if [ "$STATUS" -ne 0 ]; then
    show | grep -v '^$' | head -5
    echo "(exit 138 is SIGBUS: xctrace itself crashed while it loaded the trace)"
    return
  fi
  echo "launched process:"
  grep -o '<process [^>]*type="launched"[^>]*>' "$OUT"
  echo "GPU and Metal tables: $(grep -o 'schema="[^"]*"' "$OUT" | sort -u | grep -c -i -E 'gpu|metal')"
  grep -o 'schema="[^"]*"' "$OUT" | sort -u | grep -i -E 'gpu|metal' | sed 's/^/  /'
  xcrun xctrace export --input "$trace" \
    --xpath '/trace-toc/run[@number="1"]/data/table[@schema="metal-application-command-buffer-submissions"]' \
    > "${trace%.trace}.submissions.xml" 2>&1
  local xml="${trace%.trace}.submissions.xml" id
  echo "metal-application-command-buffer-submissions rows: $(grep -c '<row>' "$xml")"
  echo "processes the table defines:"
  grep -o '<process id="[^"]*" fmt="[^"]*"' "$xml" | sed 's/^/  /'
  id=$(grep -o "<process id=\"[^\"]*\" fmt=\"$name (" "$xml" | head -1 | sed 's/.*id="\([^"]*\)".*/\1/')
  echo "references to $name (process id ${id:-none}) after its first row:" \
       "$( [ -n "$id" ] && grep -o "<process ref=\"$id\"/>" "$xml" | wc -l | tr -d ' ' || echo 0)"
}

r3() {
  header
  # xctrace relays none of the target's output unless --target-stdout is given,
  # and it never relays stderr. The probe prints its errors to stdout as well.
  # `record` exits 54 when --time-limit ends the recording, but also when the
  # target exits non-zero, so the toc's process line is the target's verdict.
  local n=1
  for template in 'Metal System Trace' 'Game Performance'; do
    local trace="$TMP/r3-$n.trace"
    rm -rf "$trace" "$TMP/r3-$n.stdout"
    step "xctrace record, $template, the brief's command plus --target-stdout" xcrun xctrace record \
      --template "$template" --time-limit 10s --output "$trace" --target-stdout "$TMP/r3-$n.stdout" \
      --launch -- .build/release/MetalProbe render --frames 100000
    show
    echo "probe stdout: $(grep -c '^frame [0-9]* ok$' "$TMP/r3-$n.stdout") ok lines, then:"
    grep -v -e '^frame [0-9]* ok$' -e '^$' "$TMP/r3-$n.stdout"
    echo "recording size: $(du -sh "$trace" | cut -f1)"
    xctrace_toc "$trace" MetalProbe "$template"
    n=$((n + 1))
  done
  # 100,000 frames take about 5 s here, so the runs above end before the time
  # limit. This run cannot finish in 1 s, so the limit ends it.
  local trace="$TMP/r3-3.trace"
  rm -rf "$trace"
  step "xctrace record, Metal System Trace, ended by --time-limit 1s" xcrun xctrace record \
    --template 'Metal System Trace' --time-limit 1s --output "$trace" \
    --launch -- .build/release/MetalProbe render --frames 10000000
  show
  echo "(exit 54: here --time-limit ended the recording, and xctrace killed the target)"
  echo "recording size: $(du -sh "$trace" | cut -f1)"
  xctrace_toc "$trace" MetalProbe "Metal System Trace, 1 s"
  for target in /usr/bin/true /usr/bin/false; do
    rm -rf "$TMP/r3-$(basename "$target").trace"
    step "xctrace record exit status for $target, which ends at once" xcrun xctrace record \
      --template 'Time Profiler' --time-limit 10s --output "$TMP/r3-$(basename "$target").trace" --launch -- "$target"
    grep -E 'ended|exited|limit' "$OUT"
  done
}

# xcodebuild output is long; keep the command the target ran and the verdict.
xcodebuild_summary() {
  grep -v '^    export' "$OUT" | grep -E '^    /bin/sh |^built |Finished|^error|warning:|\*\* [A-Z ]+ \*\*' \
    | sed "s|$TMP|\$TMP|g; s|$HERE/||g"
}

r5() {
  header
  local cpp="$HERE/cpp/build/cpp-host" rust="$HERE/rust/target/release/rust-host"
  step "The project's targets" xcodebuild -project ExternalHosts.xcodeproj -list
  sed -n '/Targets:/,/^$/p' "$OUT"
  for target in CppHost RustHost; do
    step "xcodebuild clean, $target" xcodebuild -project ExternalHosts.xcodeproj -target "$target" clean
    xcodebuild_summary
  done
  echo "cpp-host after clean: $([ -e "$cpp" ] && echo present || echo absent)," \
       "rust-host after clean: $([ -e "$rust" ] && echo present || echo absent)"
  for target in CppHost RustHost; do
    step "xcodebuild build, $target" xcodebuild -project ExternalHosts.xcodeproj -target "$target" build
    xcodebuild_summary
  done
  for host in "$cpp" "$rust"; do
    local name
    name=$(basename "$host")
    step "$name, one offscreen frame" "$host"
    show
    step "$name, API and Shader Validation, reports to stderr" \
      env MTL_DEBUG_LAYER=1 MTL_SHADER_VALIDATION=1 MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1 "$host"
    show
    rm -rf "$TMP/r5-$name.gputrace" "$TMP/r5-$name-nocap.gputrace"
    step "$name --capture without MTL_CAPTURE_ENABLED" "$host" --capture "$TMP/r5-$name-nocap.gputrace"
    show
    echo "trace written: $([ -e "$TMP/r5-$name-nocap.gputrace" ] && echo yes || echo no)"
    step "$name --capture with MTL_CAPTURE_ENABLED=1" \
      env MTL_CAPTURE_ENABLED=1 "$host" --capture "$TMP/r5-$name.gputrace"
    show
    echo "trace written: $([ -d "$TMP/r5-$name.gputrace" ] && echo yes || echo no)"
    # The reference's read-back line, with the trace name changed.
    step "gpudebug on the $name trace" gpudebug --oneshot -t "$TMP/r5-$name.gputrace" -c "list" -c "go /commands/cb0" -c "list"
    show
    local trace="$TMP/r5-$name.trace"
    rm -rf "$trace"
    step "xctrace record, Metal System Trace, $name" \
      xcrun xctrace record --template 'Metal System Trace' --output "$trace" --launch -- "$host"
    show
    xctrace_toc "$trace" "$name" "$name"
  done
}

case "${1:-}" in
  r1) r1 ;;
  r2) r2 ;;
  r3) r3 ;;
  r5) r5 ;;
  *) echo "usage: run.sh r1|r2|r3|r5" >&2; exit 2 ;;
esac
