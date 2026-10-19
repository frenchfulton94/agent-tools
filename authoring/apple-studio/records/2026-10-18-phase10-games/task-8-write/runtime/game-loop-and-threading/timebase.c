// Prints the mach timebase ratio and checks that ticks scaled by it agree with
// clock_gettime_nsec_np(CLOCK_UPTIME_RAW). Build it for arm64 and for x86_64
// (run under Rosetta) to compare native and translated processes.
#include <mach/mach_time.h>
#include <stdint.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>

int main(void) {
    mach_timebase_info_data_t tb;
    if (mach_timebase_info(&tb) != KERN_SUCCESS) {
        fprintf(stderr, "mach_timebase_info failed\n");
        return 1;
    }
#if defined(__arm64__)
    const char *arch = "arm64";
#elif defined(__x86_64__)
    const char *arch = "x86_64";
#else
    const char *arch = "other";
#endif
    printf("arch=%s numer=%u denom=%u\n", arch, tb.numer, tb.denom);

    uint64_t t0 = mach_absolute_time();
    uint64_t n0 = clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
    usleep(100000); // 100 ms
    uint64_t t1 = mach_absolute_time();
    uint64_t n1 = clock_gettime_nsec_np(CLOCK_UPTIME_RAW);

    uint64_t rawTicks = t1 - t0;
    uint64_t scaledNs = rawTicks * tb.numer / tb.denom;
    uint64_t clockNs = n1 - n0;
    printf("ticks=%llu scaled_ns=%llu clock_uptime_raw_ns=%llu\n",
           (unsigned long long)rawTicks, (unsigned long long)scaledNs,
           (unsigned long long)clockNs);
    printf("raw_ticks_as_ns_error=%.1f%%\n",
           100.0 * ((double)rawTicks - (double)clockNs) / (double)clockNs);
    return 0;
}
