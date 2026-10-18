// A vetted, non-annotated call (vDSP is not marked nonblocking in vDSP.h)
// wrapped once so the rest of the render code stays under -Wfunction-effects.
//   clang++ -std=c++20 -fsyntax-only -Wfunction-effects realtime_vdsp_wrap.cpp
#include <Accelerate/Accelerate.h>
#include <CoreAudioTypes/CoreAudioTypes.h>

static inline void scale_rt(float *buf, float gain, unsigned frames) CA_REALTIME_API {
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wfunction-effects"
    vDSP_vsmul(buf, 1, &gain, buf, 1, frames);
#pragma clang diagnostic pop
}

static void render(float *out, unsigned frames) CA_REALTIME_API {
    scale_rt(out, 0.5f, frames);
}

int main() {
    float buf[8] = {};
    render(buf, 8);
}
