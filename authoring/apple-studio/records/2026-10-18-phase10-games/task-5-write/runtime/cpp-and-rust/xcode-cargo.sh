#!/bin/sh
# Build Tool: /bin/sh   Arguments: xcode-cargo.sh $(ACTION) $(CONFIGURATION)
set -eu
CARGO="${CARGO:-$(command -v cargo || true)}"
if [ -z "$CARGO" ]; then
  echo "error: cargo is not on this build's PATH; set CARGO to an absolute path"
  exit 1
fi
action="${1:-build}"
config="${2:-Debug}"
case "$action" in
  "" | build)
    if [ "$config" = "Release" ]; then exec "$CARGO" build --release; fi
    exec "$CARGO" build ;;
  clean)
    exec "$CARGO" clean ;;
  *)
    echo "error: xcode-cargo.sh does not handle the action '$action'"
    exit 1 ;;
esac
