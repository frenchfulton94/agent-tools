// Two Apple pages disagree on how to raise a render thread:
//  - "Analyzing the performance of your Metal app": priority 45 through
//    pthread_attr_setschedparam before pthread_create.
//  - "Tuning your code's performance for Apple silicon": move from
//    pthread_setschedparam/setpriority/thread_set_policy to QoS classes.
// This prints the scheduler priority each QoS class yields on a new thread, and
// the QoS a thread reports after the priority-45 recipe.
#include <pthread.h>
#include <pthread/qos.h>
#include <sched.h>
#include <stdio.h>

static const char *qos_name(qos_class_t q) {
    switch (q) {
    case QOS_CLASS_USER_INTERACTIVE: return "userInteractive";
    case QOS_CLASS_USER_INITIATED: return "userInitiated";
    case QOS_CLASS_DEFAULT: return "default";
    case QOS_CLASS_UTILITY: return "utility";
    case QOS_CLASS_BACKGROUND: return "background";
    case QOS_CLASS_UNSPECIFIED: return "unspecified";
    default: return "other";
    }
}

static void *report(void *label) {
    struct sched_param sp;
    int policy = 0;
    pthread_getschedparam(pthread_self(), &policy, &sp);
    printf("%-34s qos_class_self=%-16s sched_priority=%d policy=%d\n",
           (const char *)label, qos_name(qos_class_self()), sp.sched_priority, policy);
    return NULL;
}

static void run_with_qos(qos_class_t q, const char *label) {
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_set_qos_class_np(&attr, q, 0);
    pthread_t t;
    pthread_create(&t, &attr, report, (void *)label);
    pthread_join(t, NULL);
    pthread_attr_destroy(&attr);
}

int main(void) {
    run_with_qos(QOS_CLASS_USER_INTERACTIVE, "attr qos userInteractive");
    run_with_qos(QOS_CLASS_USER_INITIATED, "attr qos userInitiated");
    run_with_qos(QOS_CLASS_DEFAULT, "attr qos default");
    run_with_qos(QOS_CLASS_UTILITY, "attr qos utility");
    run_with_qos(QOS_CLASS_BACKGROUND, "attr qos background");

    pthread_attr_t attr;
    pthread_attr_init(&attr);
    struct sched_param sp = { .sched_priority = 45 };
    int rc = pthread_attr_setschedparam(&attr, &sp);
    pthread_t t;
    pthread_create(&t, &attr, report, (void *)"attr setschedparam 45 (rc above)");
    printf("pthread_attr_setschedparam(45) rc=%d\n", rc);
    pthread_join(t, NULL);
    pthread_attr_destroy(&attr);

    pthread_create(&t, NULL, report, (void *)"plain pthread_create");
    pthread_join(t, NULL);
    report((void *)"main thread (CLI process)");
    return 0;
}
