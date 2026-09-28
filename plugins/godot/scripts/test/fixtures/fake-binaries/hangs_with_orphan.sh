#!/bin/sh
# Fake "godot" binary for test_engine.py's CRITICAL-1 regression test.
#
# It writes a diagnostic to stderr, then backgrounds a sleeping grandchild
# and exits immediately. The backgrounded child inherits this script's
# stderr pipe (job control is off in a non-interactive shell, so it stays in
# the same process group) and keeps the write end open long after this
# script itself has exited. A wrapper that kills only the immediate PID on
# timeout leaves that grandchild running and blocks forever in
# communicate(), waiting for an EOF that will never come.
#
# 30s, not e.g. 300s: long enough to still be alive when the test checks
# (everything here resolves in a few seconds when the fix works), but if the
# test process itself is ever interrupted before its own cleanup runs (a
# CI-level timeout, Ctrl-C, a crash), the leaked grandchild self-terminates
# in well under a minute instead of lingering for five.
echo "SCRIPT ERROR: fake hang for test_engine.py" >&2
sleep 30 &
echo $! > child.pid
exit 0
