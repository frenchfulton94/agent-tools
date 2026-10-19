// The spectrum() block from audio-and-haptics.md, verbatim, with a test main.
//   clang++ -std=c++20 -O2 spectrum_check.cpp -framework Accelerate -o spectrum_check
#include <Accelerate/Accelerate.h>
#include <cmath>

// Magnitudes of one windowed block of n real samples (n = 1 << log2n).
// setup, re, im, and mag are preallocated; mag has n/2 entries.
static void spectrum(FFTSetup setup, vDSP_Length log2n, const float *windowed,
                     float *re, float *im, float *mag) {
    const vDSP_Length n = vDSP_Length(1) << log2n, half = n / 2;
    DSPSplitComplex z = { re, im };
    vDSP_ctoz(reinterpret_cast<const DSPComplex *>(windowed), 2, &z, 1, half);
    vDSP_fft_zrip(setup, &z, 1, log2n, kFFTDirection_Forward);
    const float dc = re[0];
    im[0] = 0.0f;                         // imagp[0] held Nyquist, not part of bin 0
    vDSP_zvabs(&z, 1, mag, 1, half);
    const float scale = 1.0f / float(n);  // forward is x2 the textbook DFT: |X|/n is amplitude
    vDSP_vsmul(mag, 1, &scale, mag, 1, half);
    mag[0] = std::fabs(dc) * scale * 0.5f; // DC comes back as 2 x sum: mean = dc / 2n
}

#include <cstdio>
// Feed 0.25 + 0.5*cos(bin 5) with a rectangular window: expect mag[0]=0.25, mag[5]=0.5.
int main() {
    const vDSP_Length log2n = 10, n = 1024;
    static float x[1024], re[512], im[512], mag[512];
    for (vDSP_Length i = 0; i < n; i++) x[i] = 0.25f + 0.5f * std::cos(2.0f * float(M_PI) * 5.0f * float(i) / float(n));
    FFTSetup setup = vDSP_create_fftsetup(log2n, kFFTRadix2);
    spectrum(setup, log2n, x, re, im, mag);
    std::printf("mag[0]=%.4f (expect 0.25)  mag[5]=%.4f (expect 0.5)  mag[6]=%.4f\n", mag[0], mag[5], mag[6]);
    vDSP_destroy_fftsetup(setup);
}
