#!/bin/sh
# Reproduces every runtime claim in apple-games/references/audio-and-haptics.md.
# Usage: sh run.sh <scratch-dir>   (binaries go to the scratch dir, not the repo)
# Starts no long-running process, boots no simulator, touches no fixture.
set -u
here=$(cd "$(dirname "$0")" && pwd)
out=${1:?scratch dir}
mkdir -p "$out"

echo "== machine"
sysctl -n machdep.cpu.brand_string hw.model
sw_vers -productVersion
xcodebuild -version | head -1
clang --version | head -1

echo "== 1. vDSP real FFT scaling and DFT lengths"
clang -O2 "$here/fft_scaling.c" -framework Accelerate -o "$out/fft_scaling" && "$out/fft_scaling"
echo "exit=$?"

echo "== 2. CA_REALTIME_API diagnostics, default warnings"
clang++ -std=c++20 -fsyntax-only "$here/realtime_effects.cpp" 2>&1
echo "exit=$?"
echo "== 2b. same, -Wno-function-effects"
clang++ -std=c++20 -fsyntax-only -Wno-function-effects "$here/realtime_effects.cpp" 2>&1
echo "exit=$?"
echo "== 2c. same, -Wfunction-effects (warning lines only)"
clang++ -std=c++20 -fsyntax-only -Wfunction-effects "$here/realtime_effects.cpp" 2>&1 | grep "warning:" | sed 's|.*/||'
echo "== 2d. same, -Werror=function-effects"
clang++ -std=c++20 -fsyntax-only -Werror=function-effects "$here/realtime_effects.cpp" 2>&1 | tail -1
echo "== 2e. atomic, memset, vDSP inside CA_REALTIME_API, -Wfunction-effects"
clang++ -std=c++20 -fsyntax-only -Wfunction-effects "$here/realtime_calls.cpp" 2>&1 | grep "warning:" | sed 's|.*/||'
echo "== 2f. vDSP call wrapped under a diagnostic pragma, -Wfunction-effects"
clang++ -std=c++20 -fsyntax-only -Wfunction-effects "$here/realtime_vdsp_wrap.cpp" 2>&1
echo "exit=$?"
echo "== 2g. the reference's GainKernel block, -Wfunction-effects"
clang++ -std=c++20 -fsyntax-only -Wfunction-effects "$here/kernel_check.cpp" 2>&1
echo "exit=$?"

echo "== 1b. the reference's spectrum() block on 0.25 + 0.5*cos(bin 5)"
clang++ -std=c++20 -O2 "$here/spectrum_check.cpp" -framework Accelerate -o "$out/spectrum_check" && "$out/spectrum_check"
echo "exit=$?"

echo "== 3. Core Haptics on this Mac"
swiftc -O "$here/haptics_caps.swift" -o "$out/haptics_caps" && "$out/haptics_caps"
echo "exit=$?"
