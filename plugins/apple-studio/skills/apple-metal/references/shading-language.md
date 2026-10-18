> verified: 2026-10 against https://developer.apple.com/documentation/metal/writing-reusable-gpu-functions-with-generic-pointers.md, https://developer.apple.com/documentation/metal/mtlcompileoptions.md, https://developer.apple.com/documentation/metal/mtlcompileoptions/languageversion.md, https://developer.apple.com/documentation/metal/mtlcompileoptions/mathmode.md, https://developer.apple.com/documentation/metal/mtlcompileoptions/mathfloatingpointfunctions.md, https://developer.apple.com/documentation/metal/mtlcompileoptions/fastmathenabled.md, https://developer.apple.com/documentation/metal/mtlcompileoptions/preserveinvariance.md, https://developer.apple.com/documentation/metal/mtlcompileoptions/requiredthreadsperthreadgroup.md, https://developer.apple.com/documentation/metal/mtlcompileoptions/floatingpointconversionroundingmode.md, https://developer.apple.com/documentation/metal/mtllanguageversion.md, https://developer.apple.com/documentation/metal/mtllanguageversion/version4_0.md, https://developer.apple.com/documentation/metal/mtllanguageversion/version4_1.md, https://developer.apple.com/documentation/metal/mtlmathmode.md, https://developer.apple.com/documentation/metal/mtlmathmode/fast.md, https://developer.apple.com/documentation/metal/mtlmathmode/relaxed.md, https://developer.apple.com/documentation/metal/mtlmathmode/safe.md, https://developer.apple.com/documentation/metal/mtlmathfloatingpointfunctions.md, https://developer.apple.com/documentation/metal/mtlfloatingpointconversionroundingmode.md, https://developer.apple.com/documentation/metal/mtlcomputepipelinestate/threadexecutionwidth.md, https://developer.apple.com/documentation/metal/mtlcomputepipelinestate/maxtotalthreadsperthreadgroup.md, https://developer.apple.com/documentation/metal/mtldevice/maxthreadsperthreadgroup.md, https://developer.apple.com/documentation/metal/mtl4computepipelinedescriptor/requiredthreadsperthreadgroup.md, https://developer.apple.com/documentation/metal/mtldevice/makelibrary(source:options:).md, https://developer.apple.com/documentation/metal/mtldevice/makelibrary(url:).md, https://developer.apple.com/documentation/metal/mtldevice/makedefaultlibrary().md, https://developer.apple.com/documentation/metal/mtldevice/supportsfamily(_:).md, https://developer.apple.com/documentation/metal/mtlgpufamily/apple7.md, https://developer.apple.com/documentation/metal/creating-threads-and-threadgroups.md, https://developer.apple.com/documentation/metal/indexing-argument-buffers.md, https://developer.apple.com/documentation/apple-silicon/porting-your-metal-code-to-apple-silicon.md, https://developer.apple.com/documentation/xcode/build-settings-reference.md, https://developer.apple.com/documentation/xcode/reducing-shader-bottlenecks.md
> sources: msl-4.1, metal-feature-set-tables-2026-05, metal-by-tutorials-5e
> typecheck: macos 26.0
> typecheck-metal: metal4.1

# Metal Shading Language: versions, address spaces, precision, SIMD

Contents:
- Pick the language version first
- Migrating to 4.1: two silent breaks
- Address spaces
- Types and layout: what bites when CPU and GPU share a struct
- Fast math is the default, and it is a contract
- SIMD-groups and quad-groups
- Threadgroup memory, barriers, and atomics
- Textures and samplers in shader code
- Function kinds and linkage
- Runtime gates in Swift
- Maintaining older code: Metal 3

Scope: the shader source itself. Which language version you compile, how pointers
and address spaces work, what the types cost, what fast math is allowed to assume,
and how threads inside a threadgroup cooperate. Other files own the neighbours:

- `pipelines-and-render-passes.md`: function constants as a pipeline-compile
  strategy, `[[early_fragment_tests]]`, depth outputs, vertex amplification,
  offline GPU binaries.
- `apple-gpu-tbdr.md`: imageblocks, tile functions, raster order groups.
- `compute-and-gpu-driven.md`: dispatch sizing, mesh and object functions, ray
  tracing, tensors and Metal Performance Primitives, shader-side ICB encoding.
- `resources-and-memory.md`: buffer and texture storage, argument buffers on the
  host side.
- `gpu-debugging-and-profiling.md`: shader logging, validation, source symbols.

Every MSL block in this file compiles with `-std=metal4.1`. The blocks that need
4.1 are labelled; the rest compile at 4.0 too.

## Pick the language version first

| MSL | OS releases it pairs with | Base | Note |
|---|---|---|---|
| 4.1 | iOS, iPadOS, macOS, tvOS, visionOS 27 | C++17 | `MTLLanguageVersion.version4_1` is macOS 27 / iOS 27 in the SDK |
| 4.0 | the 26 releases | C++17 | the Metal 4 floor; `.version4_0` is macOS 26 / iOS 26 |
| 3.2 | iOS 18, macOS 15, visionOS 2 | C++14 | every feature new in 3.2 or later is Apple silicon only |
| 3.0 | iOS 16, macOS 13 | C++14 | first unified `-std=metal3.0`; earlier versions use `ios-metal2.4` / `macos-metal2.4` |

The decision:

- **Deployment target 26: compile everything at 4.0 and stay off 4.1 features.**
  This is what Xcode already does. `MTL_LANGUAGE_REVISION` defaults to
  `UseDeploymentTarget`, which passes no `-std` at all, and the compiler then
  derives the version from the deployment target. Measured with the Xcode 27
  toolchain: `-mmacosx-version-min=26.0` yields `__METAL_VERSION__` 400, and 15.0
  yields 320.
- **Deployment target 27: 4.1 is the default.** Adopt it deliberately (see the
  migration section below), because it changes the meaning of existing code.
- **Supporting 26 while using 4.1 on 27: ship two libraries,** one built at each
  version, and pick one at runtime with `#available(macOS 27.0, iOS 27.0, *)`. The
  compiler does not stop you from building `-std=metal4.1` against a 26 deployment
  target (it compiled without complaint here), so the guard is yours to write.

Three places pick the version, and two of them default to the newest:

- **Xcode build:** `MTL_LANGUAGE_REVISION`, with values from `Metal11` through
  `Metal32`, `Metal40`, and `Metal41`. Pin `Metal40` or `Metal41` when the default
  is not what you want.
- **Command line (CMake, cargo `build.rs`, make):** `xcrun metal -std=metal4.0`.
  The spec says `-std=` must be given. The Xcode 27 compiler accepts its absence,
  and with no `-std` and no minimum-OS flag it compiles as 4.1 (measured:
  `__METAL_VERSION__` 410). An external build that omits both silently produces
  OS 27 code.
- **Runtime source compile:** `MTLCompileOptions.languageVersion`. Its page says
  Metal uses the most recent version by default, and a probe on macOS 27.0.1 read
  4.1. A tool shader compiled at runtime therefore lands on the other side of the
  4.1 ABI boundary from an app library built at 4.0. Set the version explicitly.

```swift
func shaderCompileOptions() -> MTLCompileOptions {
    let options = MTLCompileOptions()
    // Match every library, dynamic library, and binary archive this one links with.
    if #available(macOS 27.0, iOS 27.0, *) {
        options.languageVersion = .version4_1
    } else {
        options.languageVersion = .version4_0
    }
    return options
}

func compileToolShader(_ source: String, on device: any MTLDevice) throws -> any MTLLibrary {
    try device.makeLibrary(source: source, options: shaderCompileOptions())
}
```

Keep shipping shaders in `.metal` files. Xcode compiles those at build time into
the default library (`device.makeDefaultLibrary()`). A shader kept in a Swift
string fails only at runtime, so a missing semicolon becomes a launch failure.
`makeLibrary(source:options:)` also has no header search path; the source can
include only the Metal standard library.

### What 4.1 adds

The spec's "what's new" appendix has no 4.1 section. The delta is spread through
the body as "Metal 4.1 and later" tags, and the generic-pointer feature appears
only in Apple's article, not in the 2026-06-04 spec. Collected:

- generic pointers, `addrspace_cast`, and the `is_*_addrspace()` queries;
- placement `new` (`<metal_common>`, with `thread`, `threadgroup`, and `device`
  forms; the type spells its space, as in `new (p) device int(7)`);
- `memory_order_acquire`, `_release`, and `_acq_rel`; `mem_flags` overloads of the
  atomic functions; `memory_order` and `thread_scope` arguments on
  `threadgroup_barrier` and `simdgroup_barrier`;
- `atomic_float` add and subtract on `threadgroup` memory (device-only before);
- `interleave` / `deinterleave` (Morton order) for `uchar`, `ushort`, `uint` pairs;
- texture `read` with a `sampler` argument for clamp-to-edge, integer texel
  offsets (-8 to +7) on reads and atomics, and 2×1 / 1×2 `block_read`;
- 2-bit, FP4, and FP8 packed numeric formats, `tensor_blockwise`, and
  `get_stride_bytes` (see `compute-and-gpu-driven.md`);
- `function_id` in ray intersection results;
- `-fmetal-rtz-fp-conversion`, which switches float-to-float narrowing from
  round-to-nearest-even to round-toward-zero for parity with other APIs.
  `MTLCompileOptions.floatingPointConversionRoundingMode` (OS 27, default
  `.toNearestEven`) describes the same narrowing; no page states that they are
  one switch.

Hardware floors still apply on top of the language version. From the Feature Set
Tables' "Metal feature availability by GPU family": acquire/release atomics, block
reads, clamp-to-edge reads, and integer offsets need Apple7. Atomics on cube and
cube-array textures and ICB raster and depth-stencil state need **Apple10** (A19,
M5), although the spec labels both plain "Metal 4". The tables win.

## Migrating to 4.1: two silent breaks

**The ABI boundary.** 4.1 changes function-name mangling. Linking a 4.0 binary
with a 4.1 binary misbehaves at runtime, and neither the compiler nor the linker
reports it. This covers metallibs, dynamic libraries, binary archives, and plain
IR. The language version decides the ABI, not the compiler version: a newer
compiler emitting `-std=metal4.0` links cleanly with older 4.0 output. Rule: one
language version per set of things that link together, including runtime-compiled
libraries (see above) and pipeline binaries in archives.

**Member functions change meaning.** In 4.0 a member function with no address
space on `this` gets an implicit `thread`. In 4.1 the same `this` becomes generic.
Source keeps compiling either way. To freeze 4.0 behaviour before you switch, let
the compiler pin each unannotated member to `thread`. The command rewrites the
file in place, so commit or copy it first:

```bash
xcrun metal -std=metal4.0 -Wmetal-addr-spaces -Xclang -fixit -fsyntax-only Shaders.metal
```

`-fsyntax-only` stops before linking, so the command exits 0. The spec's own form,
`-Xclang -fixit -Xclang -fix-what-you-can -Wmetal-addr-spaces`, does the same job.

```metal
struct Particle {
    float3 position;
    float3 velocity;

    // Pinned to thread memory under every language version.
    void integrate(float dt) thread { position += velocity * dt; }

    // 4.0: implicit `thread` this. 4.1: generic this. -Wmetal-addr-spaces flags it.
    float speed() const { return length(velocity); }
};
```

## Address spaces

Entry-point rules (unchanged by 4.1):

- A vertex or fragment function's pointer and reference arguments are `device`
  or `constant`. A kernel's may also be `threadgroup` or
  `threadgroup_imageblock`. Missing the space on an entry-point resource is a
  compile error even in 4.1.
- Program-scope variables must be `constant` and initialised with a constant
  expression; `static` is allowed only on them, and `thread_local` does not exist.
- `constant` for data every invocation reads the same way (uniforms, per-draw
  parameters); `device` for data invocations index differently (per-vertex
  arrays, per-instance transforms, anything written). The minimum `constant`
  buffer offset alignment is 4 B on every Apple family ("GPU implementation
  limits by family"), so a uniform ring buffer can sub-allocate tightly.
- MSL cannot size an array passed by pointer. Pass `constant Light* lights`
  together with a count in your parameters struct.
- The compiler assumes separate `device` buffer arguments of one function never
  overlap. Binding two overlapping views of one `MTLBuffer` to two arguments
  breaks that contract. Program-scope buffer bindings (MSL 3.2, Apple6) carry no
  such assumption and need explicit binding indices.

### Generic pointers (MSL 4.1)

A pointer with no space qualifier may point into `thread`, `threadgroup`, or
`device` memory. One helper replaces the overload set that 4.0 needed; for a
member operator taking one other operand, covering three spaces took nine
overloads plus three for a nullary member. `constant`, `threadgroup_imageblock`,
`ray_data`, and `object_data` are not covered and still need explicit qualifiers.

```metal
#if __METAL_VERSION__ >= 410
// MSL 4.1: one definition serves thread, threadgroup, and device pointers.
inline void accumulate(float* total, const float* value) { *total += *value; }
#else
// MSL 4.0: one overload per combination the call sites use.
inline void accumulate(thread float* total, const thread float* value) { *total += *value; }
inline void accumulate(device float* total, const thread float* value) { *total += *value; }
#endif
```

When one path inside a generic function needs a concrete space, cast. This block
needs 4.1:

```metal
inline void add_count(int* counter, int amount) {
    // addrspace_cast checks at runtime and yields nullptr on a mismatch.
    if (device int* d = addrspace_cast<device int*>(counter)) {
        atomic_fetch_add_explicit(reinterpret_cast<device atomic_int*>(d), amount,
                                  memory_order_relaxed);
    } else if (is_threadgroup_addrspace(counter)) {
        // static_cast is unchecked: only after a test, or when you know the space.
        *static_cast<threadgroup int*>(counter) += amount;
    } else {
        *counter += amount;
    }
}
```

- Concrete to generic is implicit. `static_cast` to a concrete space is unchecked:
  a wrong guess is undefined behaviour, and Shader Validation catches it during
  development. `addrspace_cast` is checked and returns `nullptr`. The
  `is_thread_addrspace()`, `is_device_addrspace()`, and
  `is_threadgroup_addrspace()` tests return `false` for null.
- **Cost.** Usually none: the compiler resolves the space statically. Across a
  dynamic library, or for a pointer loaded from an argument buffer, it branches
  at runtime on the real space. Each branch is cheap but adds up in an inner loop,
  and generic pointers can raise register pressure on some GPUs. For a hot call
  site, add a concretely qualified overload; it also compiles under 4.0.
- **Shared headers.** In 4.1 a struct with a pointer member (`Light* lights;`)
  has one definition for C++ and MSL. 4.0 forced `device Light*` on the MSL side.
  Guard the host-only parts with `#ifndef __METAL_VERSION__` (for example, alias
  `float3` to `simd::float3`).

### Coherence across threadgroups

Device memory is only threadgroup-coherent by default. A write from one
threadgroup is not guaranteed visible to another, even after a barrier, because
a barrier only orders its own threadgroup. Communicating across threadgroups in
one dispatch (single-pass reductions, persistent work queues) needs a
`coherent(device)` buffer or a `memory_coherence_device` texture (MSL 3.2;
"Memory coherence for textures and buffers in shaders", Apple6) plus
acquire/release atomics. Without the qualifier the code compiles and returns
stale data some of the time.

## Types and layout: what bites when CPU and GPU share a struct

- **`float3` is 16 bytes, 16-aligned.** So is `int3`; `half3` is 8. `float3x3`
  is 48 bytes because each column pads. A Swift struct of three `Float`s is 12.
  Two fixes: declare the Swift side with `SIMD3<Float>` (stride 16, measured), or
  declare the MSL side with `packed_float3` (12 bytes, 4-aligned; a storage type
  that converts to `float3` on load). Size buffers and vertex strides with
  `MemoryLayout<T>.stride`, never `.size`.

```metal
struct Light {
    float3 position;
    float3 color;
    float  intensity;
};
static_assert(sizeof(float3) == 16, "float3 pads to four components");
static_assert(sizeof(packed_float3) == 12, "packed storage form");
static_assert(sizeof(float3x3) == 48, "columns pad too");
static_assert(sizeof(Light) == 48, "36 bytes of data, 16-byte alignment");
```

```swift
struct Light {
    var position: SIMD3<Float>
    var color: SIMD3<Float>
    var intensity: Float
}

// .size is 36; .stride is 48 and matches MSL's sizeof(Light).
func lightBufferLength(count: Int) -> Int {
    MemoryLayout<Light>.stride * count
}
```

- **One header for both languages.** Keep CPU-visible structs and binding-index
  enums in a C header that Swift (through the bridging header) and MSL both
  include. Add `#include <stdbool.h>` before declaring `bool` fields. For a
  struct of resources, branch on `__METAL_VERSION__`: MSL sees
  `array<texture2d<float>, N>`, the host sees `MTLResourceID textures[N]` (Swift
  imports the fixed array as a tuple). Pointer fields are `constant T*` in MSL and
  `uint64_t` GPU addresses on the host. Shader-only structs such as `VertexOut`
  go in a shader-only header.
- **Argument-buffer IDs.** `[[id(n)]]` indices must be unique and increasing,
  and gaps are allowed. Unannotated members take the previous highest ID plus one,
  and arrays and nested structs consume a range. That numbering matters for
  `MTLArgumentEncoder`. Encoding Tier 2 buffers directly from the host uses the
  plain C struct layout, so match `MemoryLayout` instead.
- **No `double`, no `long long`.** `long`/`ulong` are 64-bit; `size_t` and
  `ptrdiff_t` are 64-bit and may not appear in entry-point arguments. Literal
  suffixes: `0.5h` (half), `0.5bf` (bfloat), `0.5f`.
- **`half` and `bfloat` never mix.** Neither converts implicitly to the other, so
  cast one side. `bfloat` converts implicitly only to `float`. It needs MSL 3.1 and
  Apple6 (`MTLDataType.bfloat` row).
- **Conversions.** `static_cast` never saturates, and float-to-int sends NaN to
  0. `as_type<T>` reinterprets bits and needs equal sizes (`float4` to `float3` is
  legal, both 16 bytes).
- **Integer traps.** Division by zero and `INT_MIN / -1` give an unspecified
  value, with no trap. `%` is undefined for a zero divisor or any negative operand.
  Shift counts use only the low log2(bits) bits, so a 32-bit `x << 33` shifts by 1.
- **Swizzle writes are read-modify-write of the whole vector.** Two threads
  writing different components of one shared vector race. Give each thread its
  own element.
- **Porting conventions.** Matrices are column-major (`float4x4(a, b, c, d)`
  takes columns), and matrix-product summation order is unspecified, so results
  can differ in the last bit across GPUs. NDC is left-handed with visible z from 0
  to 1; viewport and texture origins are top-left. Fragment `[[position]].xy` is
  in drawable pixels, not points, and the shader cannot query the target size.

### C++ subset

- MSL 4.0+ is C++17-based: `if constexpr`, structured bindings, and fold
  expressions need `-std=metal4.0` or later. Lambdas arrived in 3.2.
- Still absent: virtual functions, inheritance, exceptions, RTTI and
  `dynamic_cast`, `new`/`delete` (except 4.1 placement `new`), `goto`,
  `thread_local`. Include `<metal_stdlib>`, never the C++ standard library.
- Recursion is allowed only in kernel context (MSL 2.4+), and entry points cannot
  be overloaded.
- Templated entry points emit code only when explicitly instantiated; name each
  instance with `[[host_name("...")]]`. A function inside a namespace is looked up
  from the API by its qualified name (`outer::inner::shade`).
- Gate source on `__METAL_VERSION__`, encoded MajorMinorPatch: 4.1 is 410 and
  4.0 is 400. Platform checks need an explicit `#include <TargetConditionals.h>`
  (`TARGET_OS_OSX`, `TARGET_OS_IOS`, `TARGET_OS_VISION`); `<metal_stdlib>` does not
  pull it in.

## Fast math is the default, and it is a contract

Shaders compile with fast math unless you say otherwise. Under it the compiler
may assume no value is ever NaN or ±INF, ignore the sign of zero, use
reciprocals, reassociate, and fuse across statements. An `x / y` where `y` can be
zero is therefore undefined program behaviour, not "returns INF".

| Mode | `-fmetal-math-mode=` | `MTLMathMode` | Keeps INF/NaN | Use when |
|---|---|---|---|---|
| fast | `fast` (default) | `.fast` | no | the usual graphics path |
| relaxed | `relaxed` | `.relaxed` | yes | INF sentinels, NaN guards, `isinf` checks; Apple4+ ("Relaxed math") |
| safe | `safe` | `.safe` | yes, no result-changing transforms | deterministic simulation, lockstep netcode, golden-image tests |

`-fmetal-math-fp32-functions=fast|precise` (`MTLCompileOptions.mathFloatingPointFunctions`)
separately picks the fp32 library implementations. From Apple4 the fast ones
still honour INF and NaN. The legacy `-ffast-math` means fast + fast, and
`-fno-fast-math` means safe + precise.

Defaults, and where the documentation disagrees:

- **Xcode:** `MTL_FAST_MATH` is `YES`, which derives `MTL_MATH_MODE = FAST` and
  `MTL_MATH_FP32_FUNCTIONS = FAST`. Apple's *Reducing shader bottlenecks* article
  tells you to opt in to `-ffast-math` for speed, but it is already on. The real
  decision runs the other way: turn it down where a shader needs IEEE behaviour.
- **Runtime compiles:** `MTLMathMode.relaxed`'s page calls `relaxed` the
  Apple-silicon default, and the SDK header says the default depends on the
  language version. A runtime probe on an M4 Pro (macOS 27.0.1) read `.fast` for a
  fresh `MTLCompileOptions` with the language version set to 3.1, 4.0, or 4.1.
  Runtime wins: assume fast and set `mathMode` explicitly.
- `fastMathEnabled` is deprecated (macOS 15 / iOS 18). Use `mathMode` and
  `mathFloatingPointFunctions`. Setting the old Bool maps `true` to fast + fast and
  `false` to safe + precise.

Prefer narrowing the region over turning fast math off for the whole library:

```metal
// Only this function body keeps IEEE semantics.
float safe_ratio(float numerator, float denominator) {
    #pragma METAL fp math_mode(safe)
    return denominator == 0.0f ? 0.0f : numerator / denominator;
}

// Per call: metal::precise and metal::fast override the library-wide choice.
float accurate_angle(float x) { return precise::sin(x) + fast::cos(x); }
```

- `#pragma METAL fp math_mode(...)` and `#pragma METAL fp contract(off|on|fast)`
  are valid at file or namespace scope or at the start of a compound statement.
  `-ffp-contract=off` disables fused multiply-add contraction globally. Use it
  when two pipelines must compute the same value bit-exactly.
- Fast fp32 accuracy to design around: `sin`/`cos` keep their error bound only on
  [-π, π], so range-reduce first. `pow(x, y)` is `exp2(y * log2(x))` and breaks for
  negative `x`. `atan2` is undefined when either input is 0, and `fmod` is
  undefined. Division holds 2.5 ulp only for |y| between 2^-126 and 2^126.
  Precise forms are correctly rounded for `+ - * /`, `sqrt`, and `fma`.
- `fmax`/`fmin` return the non-NaN operand; `fmedian3` treats NaN as missing.
- `[[invariant]]` on a vertex position is ignored unless the library is built
  with `-fpreserve-invariance`, or `MTLCompileOptions.preserveInvariance = true`
  at runtime (the spec misnames the class "MTLCompilerOptions"). A depth prepass
  that reruns the position math in a second pipeline needs it.

### When to use `half`

`half` arithmetic is correctly rounded and its transcendentals are within 1 ulp
from Apple4. The win is register pressure and bandwidth, not only ALU speed: large
or dynamically indexed per-thread arrays spill to device memory and show up as
buffer traffic. Use `half` and `packed_half3` for colours, normals, and lighting
intermediates whose range allows it, and keep positions, depth, and accumulated
sums in `float`. Float-to-half rounds ties-to-even and can produce half
denormals; fast math never changes conversion accuracy.

## SIMD-groups and quad-groups

- **Never hardcode 32.** SIMD width varies between GPUs. In the shader, take
  `[[threads_per_simdgroup]]` (`[[thread_execution_width]]` is an alias). On the
  host, read `threadExecutionWidth` from the compute pipeline state after
  creating it, and make threadgroup sizes a multiple of it.
- SIMD-group built-ins (`[[thread_index_in_simdgroup]]`,
  `[[simdgroup_index_in_threadgroup]]`, `[[simdgroups_per_threadgroup]]`, and the
  quad forms) must all be `ushort` or all `uint` within one function. A SIMD-group
  is always 1D, whatever the threadgroup shape. The mapping is stable for a
  dispatch and across dispatches with the same launch parameters, and only the
  last SIMD-group may be short.
- SIMD-group functions exchange registers without threadgroup memory or barriers.
  Their element type excludes `bool`, `bfloat`, `long`, and `ulong`.
- `simd_all(e)` looks only at active lanes; `simd_ballot(e).all()` also requires
  every lane to be active. A `simd_vote` holds 64 bits, and on narrower SIMD widths
  the top bits are undefined, so mask before you compare.
- In a fragment function, quad lanes 0 to 3 are the upper-left, upper-right,
  lower-left, and lower-right of the 2×2 block. Helper lanes exist to supply
  derivatives; their buffer and texture stores and atomics have no effect.
  `simd_is_helper_thread()` may not compile outside fragment code.
- Derivatives (`dfdx`, `dfdy`, `fwidth`) are undefined in non-uniform control
  flow. Since MSL 2.3, `discard_fragment` does not make flow non-uniform: the
  fragment keeps running for derivatives, but its outputs and later writes are
  dropped. Writes made before the discard persist.
- `simdgroup_matrix` (`simdgroup_float8x8` and friends, Apple7) is cooperative:
  every call must be under SIMD-group-uniform control flow, and the lane-to-element
  mapping is unspecified. The 4.1 spec now points matrix work at tensors and Metal
  Performance Primitives (`compute-and-gpu-driven.md`).

Hardware gates ("Metal feature availability by GPU family"):

| Feature | Family |
|---|---|
| SIMD barrier | Apple2 |
| quad-scoped permute | Apple4 |
| quad-scoped ballot, SIMD-scoped permute (shuffle, broadcast) | Apple6 |
| SIMD- and quad-scoped reductions (`simd_sum`, `simd_prefix_exclusive_sum`, `quad_sum`), SIMD-group matrix multiply | Apple7 |
| SIMD shift-and-fill (`simd_shuffle_and_fill_down`) | Apple8 |

Every Metal 4 device is Apple7 or later, so on the Metal 4 path only shift-and-fill
needs a check.

## Threadgroup memory, barriers, and atomics

- Threadgroup memory is at most 32 KB per threadgroup on Apple4 and later, and
  allocation lengths align to 16 B ("GPU implementation limits by family"). In a
  tile function it shares one on-chip pool with the imageblock
  (`apple-gpu-tbdr.md`). Kernel, mesh, and object functions allocate it, and it
  lives only as long as the threadgroup.
- **Barriers are required even when the threadgroup is one SIMD-group wide.**
  Apple GPUs reorder memory operations aggressively; a missing barrier corrupts
  data without any error.
- Apple's *Porting your Metal code to Apple silicon* article shows
  `threadgroup_barrier(mem_device)` and `simd_barrier(mem_threadgroup)`. Neither
  compiles: the flag is `mem_flags::mem_device`, the function is
  `simdgroup_barrier`, and the section it cites is 6.10.1 in MSL 4.1, not 6.8.1.
- `mem_flags`: `mem_none` (execution only), `mem_device`, `mem_threadgroup`,
  `mem_texture` (orders `read_write` texture access), `mem_threadgroup_imageblock`,
  `mem_object_data`.
- On Apple silicon a thread that has returned no longer holds up a barrier, so
  early-out threads do not deadlock. But if any thread executes a barrier inside a
  branch or loop iteration, every live thread in the group must execute it too.
- `texture.fence()` orders only one thread's own write-then-read on a
  `read_write` texture. It is not a cross-thread barrier.
- **Atomics.** A counter many threads bump must be an atomic type; a plain
  `device int` loses updates, and differently on each run. `atomic_float` needs
  MSL 3.0 and Apple7 ("Floating-point atomics"); 64-bit atomics need Apple9 (Apple8
  has `ulong` min and max on macOS only).
- **Acquire/release in 4.1 needs the `mem_flags` overload.** Measured against the
  shipped headers: the three-argument `atomic_*_explicit` forms accept only
  `memory_order_relaxed`. The compiler rejects any other order "if no 'mem_flags'
  argument is provided". The spec still carries an older sentence saying relaxed
  is the only order for non-fence atomics; that is true of the three-argument form
  and false of the four-argument one. Apple7.

This kernel needs 4.1. It is a single-pass sum in which the last threadgroup to
finish adds the partials. It compiles at 4.1, and on an M4 Pro under macOS
27.0.1 it returned the exact sum of 2^20 ones in 20 of 20 runs:

```metal
kernel void single_pass_sum(device const float* input [[buffer(0)]],
                            coherent(device) device float* partials [[buffer(1)]],
                            device atomic_uint* finished [[buffer(2)]],
                            device float* result [[buffer(3)]],
                            constant uint& count [[buffer(4)]],
                            threadgroup float* scratch [[threadgroup(0)]],
                            uint gid [[thread_position_in_grid]],
                            uint group [[threadgroup_position_in_grid]],
                            uint groups [[threadgroups_per_grid]],
                            ushort lane [[thread_index_in_simdgroup]],
                            ushort simd_id [[simdgroup_index_in_threadgroup]],
                            ushort simds [[simdgroups_per_threadgroup]]) {
    // Out-of-range threads contribute zero instead of returning before the barrier.
    float v = simd_sum(gid < count ? input[gid] : 0.0f);
    if (lane == 0) scratch[simd_id] = v;
    threadgroup_barrier(mem_flags::mem_threadgroup);
    if (simd_id != 0) return;
    float group_sum = simd_sum(lane < simds ? scratch[lane] : 0.0f);
    if (lane != 0) return;
    partials[group] = group_sum;
    // Release this group's partial; the last arrival acquires everyone else's.
    uint done = atomic_fetch_add_explicit(finished, 1u, memory_order_acq_rel,
                                          mem_flags::mem_device);
    if (done == groups - 1) {
        float total = 0.0f;
        for (uint i = 0; i < groups; ++i) total += partials[i];
        *result = total;
    }
}
```

The host must zero `finished` before each dispatch, and the threadgroup memory at
index 0 must hold one `float` per SIMD-group. Do not replace the counter with a
spin-wait on other threadgroups. The spec promises independent forward progress
only between SIMD-groups of one threadgroup, and makes no such promise across
threadgroups.

## Textures and samplers in shader code

- **The `constexpr sampler` defaults are a trap:** `filter::nearest`,
  `mip_filter::none` (only mip 0 is ever read, so generated mips do nothing and
  receding surfaces shimmer), `address::clamp_to_edge`, and
  `compare_func::never`. Spell out what you want. Inline samplers count against
  the 16 sampler slots per stage, the same limit as API samplers.

```metal
constexpr sampler trilinear_repeat(filter::linear, mip_filter::linear,
                                   address::repeat, max_anisotropy(8));
```

- An in-shader sampler sets only addressing, filtering, coordinate
  normalisation, comparison, anisotropy, `lod_clamp`, `reduction` (min/max), and
  `bias`. Sampler `bias` and min/max `reduction` need **Apple10** ("Sampler LOD
  bias", "Sampler minimum and maximum reduction").
- The access qualifier gates the calls: `sample` and `gather` need
  `access::sample`; `write` needs `write` or `read_write`. Depth textures take
  only `float` and never `write`. MSAA textures are `read`-only. Sparse textures
  cannot be bound `write` or `read_write`. The element type must match the format
  class (`half` or `float` for normalised formats, `uint` or `ushort` for unsigned
  integer, `int` or `short` for signed).
- Outside fragment functions, implicit-LOD `sample` reads LOD 0. In compute, pass
  `level(...)` or `gradient2d(...)` explicitly.
- `is_null_texture(t)` tests an empty slot, which is how one material shader
  handles "value or texture" without a pipeline variant. Calling anything else on
  a null texture is undefined.
- MSL 4.1 adds `read(sampler, int2 coord, int2 offset = 0, uint lod = 0)` for
  clamp-to-edge reads with signed coordinates, and `block_read<W, H>` returning
  `block_color` for 2×1 or 1×2 blocks. There is no `block_read` for 3D textures.
- Texture atomics need `R32Uint`/`R32Sint` (MSL 3.1, Apple6). `ulong` min and max
  need `RG32Uint`. Cube and cube-array atomics are Metal 4 in the spec but Apple10
  in the tables.

## Function kinds and linkage

- Attribute spellings `[[vertex]]`, `[[fragment]]`, `[[kernel]]` (MSL 2.3 and
  later; the bare keywords still work), `[[visible]]`, `[[stitchable]]`,
  `[[intersection(...)]]`, `[[object]]`, `[[mesh]]`. Kernels, object functions,
  and mesh functions return `void`. Entry points reach each other's code only
  through `[[visible]]` functions.
- `[[user_annotation("...")]]` (MSL 4.0) attaches a string readable through
  reflection.
- **`[[required_threads_per_threadgroup(x, y, z)]]` (MSL 4.0)** on a kernel must
  match the pipeline descriptor's `requiredThreadsPerThreadgroup` if that is set,
  or pipeline creation fails. The spec places the host property on `MTLDevice`;
  that is wrong. The SDK declares it on `MTLCompileOptions`,
  `MTLComputePipelineDescriptor`, `MTL4ComputePipelineDescriptor`, and the tile
  pipeline descriptors, all macOS 26 / iOS 26, and every dispatch's
  `threadsPerThreadgroup` must then equal it. The `MTL4ComputePipelineDescriptor`
  page says pipelines that use cooperative tensors must set it.
  `[[max_total_threads_per_threadgroup(n)]]` above the device limit also fails
  pipeline creation. `maxThreadsPerThreadgroup` on `MTLDevice` is for a trivial
  shader only, so size from the pipeline state's `maxTotalThreadsPerThreadgroup`.
- Binding attributes: `[[buffer(n)]]` (buffers, acceleration structures,
  intersection function tables, tensors), `[[texture(n)]]`, `[[sampler(n)]]`,
  `[[threadgroup(n)]]`. In Metal 4 the index is the argument-table slot you fill
  with `setAddress(_:index:)`, `setTexture`, or `setSamplerState`
  (`command-model.md`). Unannotated arguments take the first free index for their
  class, and duplicates are errors unless function constants keep them apart.
- `[[stage_in]]`: one per function, and its members must be scalars or vectors
  (no packed types, matrices, or nested structs). Vertex-to-fragment matching is
  by `[[user(name)]]` if present, otherwise by name and exact type, so `float3`
  against `half3` fails to link. Integer varyings must be `[[flat]]`. A
  vertex-only output such as `[[clip_distance]]` needs a separate fragment input
  struct without it. Fragment input is capped at 124 scalar components on Apple4
  and later.
- Program-scope built-ins (MSL 3.1): declare `uint2 gid
  [[thread_position_in_grid]];` once at file scope and helpers can read it without
  a parameter. They work in dynamic libraries only from MSL 3.2.
- Function constants: `constant bool use_shadows [[function_constant(0)]];`,
  scalar or vector types, indices 0 to 65535, tested with
  `is_function_constant_defined`. An argument or struct member tagged
  `[[function_constant(name)]]` exists only when the constant is true. When to
  prefer them over macros is in `pipelines-and-render-passes.md`.
- Post-tessellation vertex functions (`[[patch(...)]]`, `patch_control_point`)
  exist only in the Metal 3 programming model; the Metal 4 column of the tables
  omits tessellation. Port to mesh shading (`compute-and-gpu-driven.md`).

## Runtime gates in Swift

The language version gates compilation; the GPU family gates execution. Check
the family once at startup and choose pipelines accordingly:

```swift
struct ShaderFeatureSupport {
    let simdShiftAndFill: Bool
    let cubeTextureAtomics: Bool
    let samplerBiasAndReduction: Bool

    init(device: any MTLDevice) {
        simdShiftAndFill = device.supportsFamily(.apple8)
        cubeTextureAtomics = device.supportsFamily(.apple10)
        samplerBiasAndReduction = device.supportsFamily(.apple10)
    }
}

func simdWidth(of pipeline: any MTLComputePipelineState) -> Int {
    pipeline.threadExecutionWidth
}
```

Other family floors that change shader choices (all "Metal feature availability
by GPU family"): global built-ins and bindings, memory coherence, and shader
logging need Apple6; query texture LOD (`calculate_clamped_lod`) needs Apple8,
with some Apple7 devices exposing it through `supportsQueryTextureLOD`.

## Maintaining older code: Metal 3

Snippets in this section compile at the file's macOS 26.0 floor; they are not compile-checked against earlier OS releases.

**When it applies.** A13 (Apple6) and older run only the Metal 3 programming
model, and an OS before 26.0 has no MSL 4.0. On those, the newest language is
MSL 3.2 (OS 18 / macOS 15), which is C++14-based, and every 3.2 feature is Apple
silicon only.

**How to gate.** Build a second library at `MTL_LANGUAGE_REVISION = Metal32` (or
`-std=metal3.2`) from sources that avoid 4.x features, and load it when the device
is below Apple7. The shader side keeps the same binding attributes; only the host
binding API differs (`command-model.md`).

```swift
enum ShaderLibraryError: Error { case missingMetal3Library }

func loadShaderLibrary(device: any MTLDevice) throws -> any MTLLibrary {
    if device.supportsFamily(.apple7), let library = device.makeDefaultLibrary() {
        return library
    }
    guard let url = Bundle.main.url(forResource: "Shaders-metal3", withExtension: "metallib") else {
        throw ShaderLibraryError.missingMetal3Library
    }
    return try device.makeLibrary(URL: url)
}
```

**Mapping.**

| Metal 4 shader feature | Metal 3 path |
|---|---|
| C++17 constructs | C++14 equivalents; guard with `#if __METAL_VERSION__ >= 400` |
| `[[required_threads_per_threadgroup]]` | `[[max_total_threads_per_threadgroup]]`, and size dispatches from the pipeline state |
| tensors, Metal Performance Primitives | `simdgroup_matrix` (Apple7) or MPS on a Metal 3 queue |
| `vertex_value`, sampler `bias`/`reduction` | none (Apple10 anyway) |
| `memory_order_seq_cst` on atomics | `atomic_thread_fence` (MSL 3.2) around relaxed atomics |
| generic pointers and other 4.1 features | explicit address-space overloads |
| mesh shading replacing tessellation | post-tessellation vertex functions remain available |
| `[[buffer(n)]]` filled through an argument table | the same index filled with `setVertexBuffer` and friends |

Keep the two libraries' binaries apart. A Metal 3 library is a separate language
version, and the ABI rule above applies to anything you link across versions.
