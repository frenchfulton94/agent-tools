import Metal
func f(e: any MTLSharedEvent) async -> Bool { e.wait(untilSignaledValue: 1, timeoutMS: 1) }
func g(e: any MTLSharedEvent) async { await e.valueSignaled(1) }
