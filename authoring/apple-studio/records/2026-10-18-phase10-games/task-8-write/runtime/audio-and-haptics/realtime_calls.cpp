// Which everyday render-path calls does -Wfunction-effects accept inside a
// CA_REALTIME_API function? Build:
//   clang++ -std=c++20 -fsyntax-only -Wfunction-effects realtime_calls.cpp
#include <Accelerate/Accelerate.h>
#include <CoreAudioTypes/CoreAudioTypes.h>
#include <atomic>
#include <cstring>

static std::atomic<float> gGain{0.5f};

static void uses_atomic(float *out, unsigned frames) CA_REALTIME_API {
    const float g = gGain.load(std::memory_order_relaxed);
    for (unsigned i = 0; i < frames; i++) out[i] *= g;
}

static void uses_memset(float *out, unsigned frames) CA_REALTIME_API {
    std::memset(out, 0, frames * sizeof(float));
}

static void uses_vdsp(float *out, unsigned frames) CA_REALTIME_API {
    const float g = 0.5f;
    vDSP_vsmul(out, 1, &g, out, 1, frames);
}

int main() {
    float buf[8] = {};
    uses_atomic(buf, 8);
    uses_memset(buf, 8);
    uses_vdsp(buf, 8);
}
