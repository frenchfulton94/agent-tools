// vDSP real FFT scaling, measured (Task 7 finding 1).
// Build: clang -O2 fft_scaling.c -framework Accelerate -o fft_scaling
//
// 1. Forward real FFT of a unit-amplitude cosine at bin k: what magnitude lands
//    in bin k? (Mathematical unscaled DFT gives N/2; "x2" scaling gives N.)
// 2. Forward then inverse with no scaling: what factor multiplies the input?
// 3. vDSP_DFT_zrop_CreateSetup: which lengths does it accept?
#include <Accelerate/Accelerate.h>
#include <math.h>
#include <stdio.h>

static void fft_check(int log2n) {
    const int n = 1 << log2n, half = n / 2, k = 5;
    float x[4096], y[4096], re[2048], im[2048];
    for (int i = 0; i < n; i++) x[i] = cosf(2.0f * (float)M_PI * k * i / n) + 0.25f;  // DC 0.25
    FFTSetup setup = vDSP_create_fftsetup(log2n, kFFTRadix2);
    DSPSplitComplex z = { re, im };
    vDSP_ctoz((const DSPComplex *)x, 2, &z, 1, half);
    vDSP_fft_zrip(setup, &z, 1, log2n, kFFTDirection_Forward);
    printf("n=%d forward: |bin %d|=%.3f (n/2=%d, n=%d)  DC realp[0]=%.3f (0.25*n=%.1f)  imagp[0](Nyquist)=%.3f\n",
           n, k, hypotf(re[k], im[k]), half, n, re[0], 0.25f * n, im[0]);
    vDSP_fft_zrip(setup, &z, 1, log2n, kFFTDirection_Inverse);
    vDSP_ztoc(&z, 1, (DSPComplex *)y, 2, half);
    printf("n=%d round trip (no scaling): y[0]/x[0]=%.4f y[1]/x[1]=%.4f  (2n=%d)\n", n, y[0] / x[0], y[1] / x[1], 2 * n);
    vDSP_destroy_fftsetup(setup);
}

// Same measurement through the DFT API at a non-power-of-two length.
static void dft_check(int n) {
    const int half = n / 2, k = 5;
    float x[4096], y[4096], re[2048], im[2048];
    for (int i = 0; i < n; i++) x[i] = cosf(2.0f * (float)M_PI * k * i / n) + 0.25f;
    DSPSplitComplex z = { re, im };
    vDSP_ctoz((const DSPComplex *)x, 2, &z, 1, half);
    vDSP_DFT_Setup fwd = vDSP_DFT_zrop_CreateSetup(NULL, n, vDSP_DFT_FORWARD);
    vDSP_DFT_Setup inv = vDSP_DFT_zrop_CreateSetup(fwd, n, vDSP_DFT_INVERSE);
    vDSP_DFT_Execute(fwd, re, im, re, im);
    printf("DFT n=%d forward: |bin %d|=%.3f (n=%d)  DC realp[0]=%.3f\n", n, k, hypotf(re[k], im[k]), n, re[0]);
    vDSP_DFT_Execute(inv, re, im, re, im);
    vDSP_ztoc(&z, 1, (DSPComplex *)y, 2, half);
    printf("DFT n=%d round trip (no scaling): y[0]/x[0]=%.4f  (2n=%d)\n", n, y[0] / x[0], 2 * n);
    vDSP_DFT_DestroySetup(inv);
    vDSP_DFT_DestroySetup(fwd);
}

int main(void) {
    fft_check(10);
    fft_check(9);
    dft_check(480);
    int lengths[] = { 8, 16, 480, 512, 768, 1000, 1024, 1536, 1920, 2048 };
    for (unsigned i = 0; i < sizeof lengths / sizeof *lengths; i++) {
        vDSP_DFT_Setup s = vDSP_DFT_zrop_CreateSetup(NULL, lengths[i], vDSP_DFT_FORWARD);
        printf("vDSP_DFT_zrop_CreateSetup(%d) -> %s\n", lengths[i], s ? "setup" : "NULL");
        if (s) vDSP_DFT_DestroySetup(s);
    }
    return 0;
}
