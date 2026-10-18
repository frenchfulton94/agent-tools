#!/bin/sh
# Builds build/cpp-host with clang++, the way cpp-and-rust.md's command line
# does, with no CMake. Xcode's CppHost target runs this as `build.sh $(ACTION)`.
#
#   build.sh [build | clean]
#
# metal-cpp 26.4 comes from the pipeline cache; fetch_metal_cpp.sh restores it
# (a pinned, hash-checked download) when it is missing.
set -eu
cd "$(dirname "$0")"
PIPELINE="$(cd ../../.. && pwd)"
METAL_CPP="${METAL_CPP:-$PIPELINE/tmp/metal-cpp/26.4}"

action="${1:-build}"
case "$action" in
  "" | build)
    if [ ! -f "$METAL_CPP/Metal/Metal.hpp" ]; then
      "$PIPELINE/fetch_metal_cpp.sh" 26.4
    fi
    mkdir -p build
    clang++ -std=c++20 -I "$METAL_CPP" main.cpp capture.cpp \
      -framework Foundation -framework Metal -framework CoreGraphics -o build/cpp-host
    echo "built $(pwd)/build/cpp-host" ;;
  clean)
    rm -rf build ;;
  *)
    echo "error: build.sh does not handle the action '$action'"
    exit 1 ;;
esac
