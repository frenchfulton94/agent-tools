// The Metal games-settings article names `hw.perflevels` for the number of core
// types. This asks sysctlbyname for it and for `hw.nperflevels`, then for the
// per-level logical CPU counts the same article names.
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/sysctl.h>

static void query(const char *name) {
    int value = 0;
    size_t size = sizeof value;
    if (sysctlbyname(name, &value, &size, NULL, 0) == 0) {
        printf("%-26s = %d\n", name, value);
    } else {
        printf("%-26s : error %d (%s)\n", name, errno, strerror(errno));
    }
}

int main(void) {
    query("hw.perflevels");
    query("hw.nperflevels");
    query("hw.perflevel0.logicalcpu");
    query("hw.perflevel1.logicalcpu");
    query("hw.logicalcpu");
    return 0;
}
