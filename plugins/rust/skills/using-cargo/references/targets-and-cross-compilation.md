# Targets, cross-compilation, and codegen options

Contents:
- [Platform tiers](#platform-tiers)
- [Renamed and new targets](#renamed-and-new-targets)
- [Cross-compiling to Linux](#cross-compiling-to-linux)
- [Linkers](#linkers)
- [rustc codegen options (`-C`)](#rustc-codegen-options--c)
- [LTO, PGO, and coverage](#lto-pgo-and-coverage)
- [WebAssembly](#webassembly)
- [Apple](#apple)
- [Bare metal and tier 3](#bare-metal-and-tier-3)

## Platform tiers

- **Tier 1** (built and tested on every change; all have host tools): `aarch64-apple-darwin`, `aarch64-pc-windows-msvc`, `aarch64-unknown-linux-gnu`, `i686-pc-windows-msvc`, `i686-unknown-linux-gnu`, `x86_64-pc-windows-gnu`, `x86_64-pc-windows-msvc`, `x86_64-unknown-linux-gnu`.
- **`x86_64-apple-darwin` is tier 2** (with host tools), not tier 1. `aarch64-pc-windows-msvc` is tier 1.
- **Tier 2** is guaranteed to build and ships through `rustup target add`, but tests may not run. **Tier 3** ships nothing: it needs nightly `-Zbuild-std` or a locally built toolchain.
- Baselines: tier 1 Linux needs glibc 2.17+ and kernel 3.2+ (aarch64: kernel 4.1+). Windows targets need Windows 10 or Server 2016+; Windows 7 is only the tier 3 `*-win7-windows-*`. macOS needs 10.12+ (x86_64) or 11.0+ (arm64). Every musl target uses musl 1.2.5.
- `*-windows-gnu` has no maintainers and may be demoted. `*-windows-gnullvm` (UCRT and LLVM tools) is tier 2 with host tools. Cross-compiling to `*-windows-msvc` from a non-Windows host is not supported.
- Every MIPS target is tier 3.

## Renamed and new targets

- `wasm32-wasi` is gone; it is `wasm32-wasip1` (measured: "could not find specification for target "wasm32-wasi""). `wasm32-wasi-preview1-threads` is `wasm32-wasip1-threads`. Also present: `wasm32-wasip2` (tier 2, emits a component) and `wasm32-wasip3` (tier 3).
- `avr-unknown-gnu-atmega328` is now `avr-none` plus `-C target-cpu=atmega328p`.
- Sanitizer targets `x86_64-unknown-linux-gnuasan`, `-gnumsan`, `-gnutsan` (tier 2) ship an instrumented std, so a sanitized build needs no nightly: `rustup target add x86_64-unknown-linux-gnuasan`, then `cargo build --target x86_64-unknown-linux-gnuasan`. They are in rustup's list on 1.97.1 (measured). The `-Zsanitizer=` flag itself is still nightly-only.
- Also new and listed on 1.97.1: `riscv64a23-unknown-linux-gnu`, `wasm32v1-none`.

## Cross-compiling to Linux

```bash
sudo apt install gcc-aarch64-linux-gnu
rustup target add aarch64-unknown-linux-gnu
```

```toml
# .cargo/config.toml
[target.aarch64-unknown-linux-gnu]
linker = "aarch64-linux-gnu-gcc"
runner = "qemu-aarch64 -L /usr/aarch64-linux-gnu"   # lets cargo run / cargo test execute it
```

- A missing std reports `error[E0463]: can't find crate for std` with "the `T` target may not be installed" (measured). Fix it with `rustup target add T`.
- Environment equivalents: `CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER` and `_RUNNER`.
- C dependencies built by `cc` read `CC_<triple_with_underscores>`, `CXX_...`, `AR_...`, `CFLAGS_...`, `CROSS_COMPILE`, and for `cmake` `CMAKE_TOOLCHAIN_FILE_<triple>`.
- Build scripts and proc macros still need a host linker. If a cross SDK's environment script hides the host `cc`, set `[target.<host-triple>] linker` explicitly.
- Fully static Linux binaries: a `*-linux-musl` target, or `-C target-feature=+crt-static`. Docker-based `cross` (cross-rs/cross) is a community alternative.
- `--target` puts output under `target/<triple>/` and stops RUSTFLAGS from reaching build scripts and proc macros.
- Custom target JSON files are nightly-only (`-Zjson-target-spec` with build-std); their format is unstable, so pin the compiler.

## Linkers

- rustc uses `rust-lld` by default on `x86_64-unknown-linux-gnu`. Opt out with `-C linker-features=-lld` (stable on that target only; only the `-` forms are stable). A later `-C link-arg=-fuse-ld=...` wins.
- Other Linux targets use the system linker. For speed: `rustflags = ["-C", "link-arg=-fuse-ld=mold"]` (GCC 12+), or `linker = "clang"` with `-fuse-ld=/path/to/mold`.
- On cc-driver targets, pass flags to the real linker as `-C link-arg=-Wl,...`.
- `-C link-arg` and `-C link-args` from RUSTFLAGS reach every crate; build-script `rustc-link-arg-*` directives can target bins, tests, or cdylibs specifically.

## rustc codegen options (`-C`)

Set through profiles where a profile key exists; use RUSTFLAGS or `cargo rustc -- -C ...` for the rest. `rustc -C help` lists what the installed compiler accepts.

| Option | Values and notes |
|---|---|
| `opt-level` | `0` to `3`, `s`, `z`. `-O` is `opt-level=3`. |
| `debuginfo` | `0`/`none`, `line-tables-only`, `1`/`limited`, `2`/`full`, `line-directives-only`. `-g` is `2`. |
| `codegen-units` | 16 non-incremental, 256 incremental. |
| `lto` | `fat`, `thin`, `n`. Without it, thin-local LTO runs unless `codegen-units=1` or `opt-level=0`. `embed-bitcode=no` with `-C lto` aborts. |
| `panic` | `unwind`, `abort`. One `abort` crate forces the final artifact to `abort`. `immediate-abort` needs nightly (measured). |
| `target-cpu` | `native`, a CPU name (`rustc --print target-cpus`). `native` binaries may not run on other machines. |
| `target-feature` | `+avx2,-sse4.1`. Unsafe: it does not rebuild std, and mixing ABI-affecting features is undefined behaviour. Never `+soft-float` or `-sse` on x86 with the prebuilt std (segfaults). |
| `relocation-model` | `pic` (default on most targets), `static`, `pie`. To opt out of PIE use `static`, not `dynamic-no-pic`. |
| `strip` | `none`, `debuginfo`, `symbols`. Not a security measure. |
| `split-debuginfo` | `off`, `packed`, `unpacked`. Defaults: `packed` on macOS and MSVC, `off` on ELF. |
| `dwarf-version` | `2` to `5`; stable. |
| `symbol-mangling-version` | Only `v0` on stable, and it is the default (measured: v0 `_R` symbols, `legacy` needs `-Z unstable-options`). |
| `instrument-coverage` | Stable. Implies v0 mangling. Needs the profiler runtime (in official toolchains). |
| `profile-generate`, `profile-use` | PGO; see below. |
| `linker`, `linker-flavor`, `link-arg`, `link-args`, `link-self-contained` | |
| `overflow-checks`, `debug-assertions` | Default follows opt-level 0. |
| `force-frame-pointers`, `control-flow-guard` (Windows), `relro-level` (ELF; full by default), `rpath`, `prefer-dynamic`, `code-model` | |

- `rustc --print cfg --target T` shows the cfgs a target sets. `rustc --print target-list` lists built-in targets. `--print native-static-libs` (with a staticlib) prints the link line a C build needs. `--print host-tuple` prints the host triple.
- `rustc --cfg unix` is an error (`explicit_builtin_cfgs_in_flags`): built-in cfgs come only from `--target`.
- rustc's `-j`/`--jobs` family appears in the 1.99 docs but is rejected by 1.97 ("Unrecognized option: 'jobs'"); **1.98+**.

## LTO, PGO, and coverage

- **Cross-language LTO:** `RUSTFLAGS="-Clinker-plugin-lto -Clinker=clang -Clink-arg=-fuse-ld=lld" cargo build --release`. Clang's LLVM must be at least as new as rustc's (`rustc -vV`; 1.97.1 reports LLVM 22). On Windows add an explicit `--target` so the flag skips proc macros ("Linker plugin based LTO is not supported together with `-C prefer-dynamic`").
- **PGO:** build with `-Cprofile-generate=/abs/dir`, run the workload, `llvm-profdata merge -o merged.profdata /abs/dir`, rebuild with `-Cprofile-use=/abs/merged.profdata`. Use absolute paths, `--release`, an explicit `--target <host>` (so build scripts are not instrumented), and otherwise identical flags. LLVM is silent about missing profile data; add `-Cllvm-args=-pgo-warn-missing-function`. `cargo-pgo` wraps the steps.
- **Coverage:** `RUSTFLAGS="-C instrument-coverage" cargo test --tests`, then `llvm-profdata` and `llvm-cov` from `rustup component add llvm-tools-preview` (not on `PATH`; they live under the toolchain's `lib/rustlib/<host>/bin`). Default profile file name is `default_%m_%p.profraw`.

## WebAssembly

- `wasm32-unknown-unknown`: imports nothing; std exists but `println!` does nothing, `std::fs` errors, `thread::spawn` panics. Pair with `wasm-bindgen` for JavaScript. Not tested in CI.
- `wasm32-wasip1` / `wasm32-wasip2`: WASI hosts. Distinguish them with `cfg(all(target_os = "wasi", target_env = "p1"))` (measured `target_env="p1"`) or `"p2"`.
- `wasm32-unknown-emscripten`: web and C interop through `emcc`.
- `wasm32v1-none`: core and alloc only, the W3C Core 1.0 feature set, works on stable without rebuilding std.
- Default features on `wasm32-unknown-unknown` include `bulk-memory` and `nontrapping-fptoint` since 1.87 (measured, along with `multivalue`, `mutable-globals`, `reference-types`, `sign-ext`). For an engine without them, use `wasm32v1-none`, or nightly `-Ctarget-cpu=mvp -Zbuild-std`.
- Wasm targets default to `panic=abort`, so `#[test]` needs nightly `-Zpanic-abort-tests`; `-Cpanic=unwind` fails with "the crate `panic_unwind` does not have the panic strategy `unwind`" without `-Zbuild-std`.

## Apple

- Deployment target: `MACOSX_DEPLOYMENT_TARGET`, `IPHONEOS_DEPLOYMENT_TARGET`, `TVOS_`, `WATCHOS_`, `XROS_DEPLOYMENT_TARGET`. `rustc --print deployment-target` shows the default. The SDK comes from `SDKROOT` or `xcrun`.
- Simulator and Mac Catalyst: `target_env = "sim"` and `target_env = "macabi"` (1.91). On 1.97.1 `aarch64-apple-ios-sim` still sets both `target_abi="sim"` and `target_env="sim"` (measured); write new code against `target_env`.
- iOS, tvOS, watchOS, and visionOS targets are cross-compile only and need Xcode's SDKs.

## Bare metal and tier 3

- `*-none-*` targets are `#![no_std]`; `alloc` works only with your own `#[global_allocator]`. `rust-lld` is the default linker and **no linker script ships**: pass `-C link-arg=-Tlink.x` (usually from a `-rt` crate).
- Typical config: `[build] target = "thumbv7em-none-eabihf"` with `rustflags = ["-C", "link-arg=-Tlink.x"]`.
- `eabi` is the soft-float calling convention and `eabihf` the hard-float one. Never disable `fpregs` on an `eabihf` target.
- `-C target-cpu=X` enables every optional feature of that CPU; subtract with `-C target-feature=-feat`.
- Targets without atomic read-modify-write (thumbv6m, riscv32imc, and others) lack `compare_exchange` and `fetch_add`; use the `portable-atomic` crate.
- `x86_64-unknown-none` and the `*-softfloat` targets avoid FP and SIMD registers, which suits kernels.
- Tier 3 builds use nightly: `cargo +nightly build -Zbuild-std=core,alloc --target T` (needs `rustup component add rust-src`). Setting `[unstable] build-std = ["core"]` in config does nothing on stable; it is ignored silently (measured).
