#!/bin/bash
# Phase 9 Duo probe: capture one state after a pose change made in Device Hub.
# Poses cannot be set from the command line (Task 8 discovery), so a person
# sets the pose and runs this once per state. It screenshots both integrated
# displays and records which one is active.
# Usage: capture.sh <simulator-udid> <out-dir> <state-name>
set -euo pipefail
# Same toolchain as run.sh; xcode-select may point at an older Xcode.
export DEVELOPER_DIR="/Applications/Xcode 27-1-beta.app/Contents/Developer"
UDID="$1"; OUT="$2"; STATE="$3"
mkdir -p "$OUT"
sleep 2
xcrun simctl io "$UDID" screenshot --display=1 "$OUT/$STATE.outer.png"
xcrun simctl io "$UDID" screenshot --display=3 "$OUT/$STATE.inner.png"
{
  echo "== $STATE $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  xcrun devicectl device info displays --device "$UDID" --timeout 30 2>&1 \
    | grep -E "^▿|currentOrientation|backlightState|Main display"
} >> "$OUT/capture-states.log"
echo "captured $STATE"
