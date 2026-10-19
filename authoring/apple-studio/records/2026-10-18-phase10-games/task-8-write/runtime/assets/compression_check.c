// Runtime checks for assets.md, Compression section.
// Build: clang -O2 -o /tmp/x compression_check.c -lcompression
// Run:   ./compression_check <payload> [<payload> ...]
//
// 1. Which algorithms compression_stream_init accepts (buffer-only claim).
// 2. What compression_decode_buffer returns when the destination is too small.
// 3. What compression_encode_buffer returns for a tiny input with dst == src size.
// 4. Ratio and single-thread encode/decode throughput per algorithm, per payload.
#include <compression.h>
#include <mach/mach_time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { const char *name; compression_algorithm alg; } Alg;
static const Alg algs[] = {
    {"LZ4", COMPRESSION_LZ4},       {"LZ4_RAW", COMPRESSION_LZ4_RAW},
    {"ZLIB", COMPRESSION_ZLIB},     {"LZMA", COMPRESSION_LZMA},
    {"LZFSE", COMPRESSION_LZFSE},   {"LZBITMAP", COMPRESSION_LZBITMAP},
    {"BROTLI", COMPRESSION_BROTLI}, {"LZMESH", COMPRESSION_LZMESH},
    {"LZRAVEN", COMPRESSION_LZRAVEN},
};
enum { NALG = sizeof algs / sizeof algs[0] };

static double seconds(uint64_t ticks) {
    static mach_timebase_info_data_t tb;
    if (tb.denom == 0) mach_timebase_info(&tb);
    return (double)ticks * tb.numer / tb.denom / 1e9;
}

static uint8_t *slurp(const char *path, size_t *n) {
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    *n = (size_t)ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *b = malloc(*n);
    if (fread(b, 1, *n, f) != *n) { free(b); b = NULL; }
    fclose(f);
    return b;
}

int main(int argc, char **argv) {
    printf("== 1. compression_stream_init per algorithm (ENCODE / DECODE)\n");
    for (int i = 0; i < NALG; i++) {
        compression_stream s;
        compression_status e = compression_stream_init(&s, COMPRESSION_STREAM_ENCODE, algs[i].alg);
        if (e == COMPRESSION_STATUS_OK) compression_stream_destroy(&s);
        compression_status d = compression_stream_init(&s, COMPRESSION_STREAM_DECODE, algs[i].alg);
        if (d == COMPRESSION_STATUS_OK) compression_stream_destroy(&s);
        printf("%-9s encode=%s decode=%s\n", algs[i].name,
               e == COMPRESSION_STATUS_OK ? "OK" : "ERROR",
               d == COMPRESSION_STATUS_OK ? "OK" : "ERROR");
    }

    printf("\n== 2. decode into a destination 100 bytes too small\n");
    {
        size_t n = 1 << 20;
        uint8_t *src = malloc(n), *enc = malloc(n * 2), *dec = malloc(n);
        for (size_t i = 0; i < n; i++) src[i] = (uint8_t)((i * 7) ^ (i >> 5));
        for (int i = 0; i < NALG; i++) {
            size_t c = compression_encode_buffer(enc, n * 2, src, n, NULL, algs[i].alg);
            size_t full = compression_decode_buffer(dec, n, enc, c, NULL, algs[i].alg);
            size_t shortd = compression_decode_buffer(dec, n - 100, enc, c, NULL, algs[i].alg);
            printf("%-9s encoded=%zu full_decode=%zu short_decode(dst=%zu)=%zu\n",
                   algs[i].name, c, full, n - 100, shortd);
        }
        free(src); free(enc); free(dec);
    }

    printf("\n== 3. encode 16 bytes of incompressible input, dst == 16 bytes\n");
    {
        uint8_t src[16], dst[16];
        for (int i = 0; i < 16; i++) src[i] = (uint8_t)(i * 37 + 11);
        for (int i = 0; i < NALG; i++)
            printf("%-9s returned=%zu\n", algs[i].name,
                   compression_encode_buffer(dst, sizeof dst, src, sizeof src, NULL, algs[i].alg));
    }

    printf("\n== 4. ratio and throughput (best of 3, single thread, scratch buffer reused)\n");
    for (int a = 1; a < argc; a++) {
        size_t n;
        uint8_t *src = slurp(argv[a], &n);
        if (!src) { printf("cannot read %s\n", argv[a]); continue; }
        uint8_t *enc = malloc(n + n / 2 + 4096), *dec = malloc(n);
        printf("payload %s (%zu bytes)\n", argv[a], n);
        for (int i = 0; i < NALG; i++) {
            void *es = malloc(compression_encode_scratch_buffer_size(algs[i].alg) + 1);
            void *ds = malloc(compression_decode_scratch_buffer_size(algs[i].alg) + 1);
            double be = 1e9, bd = 1e9;
            size_t c = 0, d = 0;
            for (int r = 0; r < 3; r++) {
                uint64_t t0 = mach_absolute_time();
                c = compression_encode_buffer(enc, n + n / 2 + 4096, src, n, es, algs[i].alg);
                uint64_t t1 = mach_absolute_time();
                d = compression_decode_buffer(dec, n, enc, c, ds, algs[i].alg);
                uint64_t t2 = mach_absolute_time();
                if (seconds(t1 - t0) < be) be = seconds(t1 - t0);
                if (seconds(t2 - t1) < bd) bd = seconds(t2 - t1);
            }
            int ok = (d == n) && memcmp(dec, src, n) == 0;
            printf("  %-9s ratio=%.3f enc=%8.1f MB/s dec=%8.1f MB/s roundtrip=%s\n",
                   algs[i].name, c ? (double)n / c : 0.0,
                   n / be / 1e6, n / bd / 1e6, ok ? "ok" : "FAIL");
            free(es); free(ds);
        }
        free(src); free(enc); free(dec);
    }
    return 0;
}
