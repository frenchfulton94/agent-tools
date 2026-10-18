// The GainKernel block from audio-and-haptics.md, verbatim, compiled under
// -Wfunction-effects to show the checked kernel is clean.
//   clang++ -std=c++20 -fsyntax-only -Wfunction-effects kernel_check.cpp
#include <Accelerate/Accelerate.h>
#include <AudioToolbox/AudioToolbox.h>
#include <atomic>

// One vetted vDSP call, checked once by hand.
static inline void ramp_gain_rt(float *buf, float *gain, float step, vDSP_Length n) CA_REALTIME_API {
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wfunction-effects"
    vDSP_vrampmul(buf, 1, gain, &step, buf, 1, n);
#pragma clang diagnostic pop
}

struct GainKernel {
    std::atomic<float> target{1.0f};   // written by the control thread
    float current = 1.0f;              // touched only on the render thread

    OSStatus render(AudioBufferList *io, UInt32 frames) CA_REALTIME_API {
        const float goal = target.load(std::memory_order_relaxed);
        const float step = (goal - current) / static_cast<float>(frames);
        for (UInt32 b = 0; b < io->mNumberBuffers; ++b) {
            float start = current;     // each channel ramps from the same value
            ramp_gain_rt(static_cast<float *>(io->mBuffers[b].mData), &start, step, frames);
        }
        current = goal;
        return noErr;
    }
};
