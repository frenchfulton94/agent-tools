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

# The last commit before Task 6 changed the references. The "as previously
# written" steps run that version's text, to log the failures behind each fix.
PRE_FIX=6c6d834
REFDIR=plugins/apple-studio/skills/apple-metal/references
pre_fix_reference() {   # pre_fix_reference <file.md> <dest>
  git -C "$HERE" show "$PRE_FIX:$REFDIR/$1" > "$2"
}

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
  # Task 9's workload. /usr/bin/time -p prints the wall time.
  step "sim, 2,000 normal ticks" /usr/bin/time -p "$PROBE" sim --ticks 2000
  show
  step "sim, 200 ticks through plantedSlowStep" /usr/bin/time -p "$PROBE" sim --ticks 200 --slow
  show
  step "plantedSlowStep is a symbol in the release binary" nm "$PROBE"
  grep plantedSlowStep "$OUT"
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
  echo "## gpudebug: the profiling block as previously written ($PRE_FIX), in a new session"
  echo "(a plain profile run, then the same session's profile load, and the one-step path)"
  pre_fix_reference gpu-debugging-and-profiling.md "$TMP/r2/pre-fix-gpu-debugging.md"
  {
    documented 'gpudebug -s "$id" -c "status"' | head -1
    python3 "$HERE/check_verbatim.py" --block "$TMP/r2/pre-fix-gpu-debugging.md" \
      'gpudebug -s "$id" -c "profile run"' | sed "s|Frame.gputrace|$TRACE|g"
    echo 'gpudebug -s "$id" -c "go /performance" -c "go commands" -c "list"'
    echo 'gpudebug -s "$id" -c "profile load"'
    echo 'gpudebug -s "$id" -c "go /performance" -c "go commands" -c "list"'
    echo 'gpudebug -s "$id" -c "go /performance/commands"'
    echo 'gpudebug --terminate "$id"'
  } > "$TMP/r2/pre-fix-profile.sh"
  bash -v "$TMP/r2/pre-fix-profile.sh" 2>&1 | sed "s|$TMP|\$TMP|g"
  echo
  echo "## gpudebug: the profiling block, verbatim, after the Sessions block's first line"
  {
    documented 'gpudebug -s "$id" -c "status"' | head -1
    documented 'gpudebug -s "$id" -c "profile run --embed"'
    # With a profile loaded, the one-step path under /performance.
    echo 'gpudebug -s "$id" -c "go /performance/commands"'
    echo 'gpudebug -s "$id" -c "go /performance/shaders"'
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
  step "Browsing that trace: list, find, info, fetch" gpudebug --oneshot -t "$incapture" \
    -c "go /commands" -c "list" -c "find opaque" \
    -c "go /commands/cb0/grp0/re0/grp0/draw0" -c "info" \
    -c "fetch color0 --out $TMP/r2/compile-in-capture-draw0.png"
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
  # xctrace passes none of the target's output through unless --target-stdout
  # is given; the last steps below check where stdout and stderr go. The exit
  # steps check what `record`'s exit status means: the toc's launched-process
  # element, not that status, is the target's verdict.
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
    if [ "$STATUS" -ne 0 ]; then
      xctrace_toc "$trace" MetalProbe "$template, second attempt"
    fi
    n=$((n + 1))
  done
  # The runs above end when the probe finishes or when the 10 s limit is
  # reached, whichever comes first. This run cannot finish in 1 s.
  local trace="$TMP/r3-3.trace"
  rm -rf "$trace"
  step "xctrace record, Metal System Trace, ended by --time-limit 1s" xcrun xctrace record \
    --template 'Metal System Trace' --time-limit 1s --output "$trace" \
    --launch -- .build/release/MetalProbe render --frames 10000000
  show
  echo "recording size: $(du -sh "$trace" | cut -f1)"
  xctrace_toc "$trace" MetalProbe "Metal System Trace, 1 s"
  for target in /usr/bin/true /usr/bin/false; do
    trace="$TMP/r3-$(basename "$target").trace"
    rm -rf "$trace"
    step "xctrace record exit status for $target, which ends at once" xcrun xctrace record \
      --template 'Time Profiler' --time-limit 10s --output "$trace" --launch -- "$target"
    show
    step "xctrace export --toc, $target" xcrun xctrace export --input "$trace" --toc
    grep -o '<process [^>]*type="launched"[^>]*>' "$OUT"
  done
  # Where the target's stdout and stderr go, with and without --target-stdout.
  local probe_cmd='echo TO-STDOUT; echo TO-STDERR >&2'
  rm -rf "$TMP/r3-streams" && mkdir -p "$TMP/r3-streams"
  step "xctrace record, a target that writes one line to stdout and one to stderr" xcrun xctrace record \
    --template 'Time Profiler' --time-limit 10s --output "$TMP/r3-streams/plain.trace" \
    --launch -- /bin/sh -c "$probe_cmd"
  echo "xctrace's own stdout and stderr:"
  show
  step "the same, with --target-stdout" xcrun xctrace record \
    --template 'Time Profiler' --time-limit 10s --output "$TMP/r3-streams/redirected.trace" \
    --target-stdout "$TMP/r3-streams/target.out" --launch -- /bin/sh -c "$probe_cmd"
  echo "xctrace's own stdout and stderr:"
  show
  echo "the --target-stdout file:"
  cat "$TMP/r3-streams/target.out"
}

# xcodebuild output is long; keep the command the target ran and the verdict.
xcodebuild_summary() {
  grep -E '^    export (ACTION|CONFIGURATION)\\=' "$OUT"
  grep -v '^    export' "$OUT" | grep -E '^    /bin/sh |^built |Finished|^error|warning:|\*\* [A-Z ]+ \*\*' \
    | sed "s|$TMP|\$TMP|g; s|$HERE/||g"
}

# The RustHost target with the argument string and script as they were before
# Task 6 ($PRE_FIX), in a throwaway copy of the project under $TMP. The copy
# runs the old script from $TMP against the fixture's crate. `quoted` puts
# "$(ACTION)" in double quotes.
r5_pre_fix() {
  local old="$TMP/r5-pre-fix"
  rm -rf "$old" && mkdir -p "$old"
  pre_fix_reference cpp-and-rust.md "$old/cpp-and-rust.md"
  python3 "$HERE/check_verbatim.py" --block "$old/cpp-and-rust.md" '#!/bin/sh' > "$old/xcode-cargo.sh"
  echo
  echo "## The pre-fix xcode-cargo.sh, from $PRE_FIX"
  grep -n -E 'Arguments:|action=|config=' "$old/xcode-cargo.sh"
  for variant in unquoted quoted; do
    local args='$(ACTION) $(CONFIGURATION)'
    [ "$variant" = quoted ] && args='\"$(ACTION)\" $(CONFIGURATION)'
    mkdir -p "$old/$variant/ExternalHosts.xcodeproj"
    python3 - "$HERE/ExternalHosts.xcodeproj/project.pbxproj" "$old/$variant/ExternalHosts.xcodeproj/project.pbxproj" \
      "$old/xcode-cargo.sh $args" "$HERE/rust" <<'PY'
import sys
src, dst, args, workdir = sys.argv[1:]
text = open(src).read()
new = text.replace('buildArgumentsString = "xcode-cargo.sh $(CONFIGURATION) $(ACTION)";',
                   'buildArgumentsString = "%s";' % args)
new = new.replace('buildWorkingDirectory = "$(PROJECT_DIR)/rust";',
                  'buildWorkingDirectory = "%s";' % workdir)
assert new.count(args) == 1 and workdir in new, "pbxproj did not change as expected"
open(dst, "w").write(new)
PY
    grep 'buildArgumentsString = ".*xcode-cargo' "$old/$variant/ExternalHosts.xcodeproj/project.pbxproj" \
      | sed "s|$TMP|\$TMP|g; s/^[[:space:]]*/argument string in the copy: /"
    step "xcodebuild build, RustHost, pre-fix arguments, $variant" \
      xcodebuild -project "$old/$variant/ExternalHosts.xcodeproj" -target RustHost build
    xcodebuild_summary
  done
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
  r5_pre_fix
  # The fixed script's error paths, from a shell, with the new argument order.
  step "xcode-cargo.sh from a shell, unknown action" sh rust/xcode-cargo.sh Release install
  show
  step "xcode-cargo.sh from a shell, no cargo on PATH" env CARGO= PATH=/usr/bin:/bin sh rust/xcode-cargo.sh Release
  show
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
