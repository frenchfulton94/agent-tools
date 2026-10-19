// Does CA_REALTIME_API make clang flag non-realtime work? (OS 27 SDK)
// Build: clang++ -std=c++20 -fsyntax-only realtime_effects.cpp
//        clang++ -std=c++20 -fsyntax-only -Wno-function-effects realtime_effects.cpp
#include <CoreAudioTypes/CoreAudioTypes.h>
#include <cstdlib>
#include <mutex>
#include <vector>

static std::mutex gLock;
static float gGain = 0.5f;

// Clean kernel: no allocation, no locks.
static void render_clean(float *out, unsigned frames) CA_REALTIME_API {
    for (unsigned i = 0; i < frames; i++) out[i] *= gGain;
}

// Each line below is something a render callback must not do.
static void render_dirty(float *out, unsigned frames) CA_REALTIME_API {
    void *p = std::malloc(64);                   // allocation
    std::lock_guard<std::mutex> guard(gLock);    // lock
    std::vector<float> scratch(frames);          // allocation via a container
    out[0] = scratch.empty() ? 0.0f : 1.0f;
    std::free(p);
}

int main() {
    float buf[8] = {};
    render_clean(buf, 8);
    render_dirty(buf, 8);
}
