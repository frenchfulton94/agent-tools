# Coverage, and tests on other targets

## Code coverage with `-C instrument-coverage`

`-C instrument-coverage` is a **stable** rustc flag. The profiler runtime ships with rustup toolchains. Do not reach for nightly `-Z profile` or `-Z instrument-coverage`, which are the older forms.

```bash
rustup component add llvm-tools          # llvm-profdata and llvm-cov
RUSTFLAGS="-C instrument-coverage" cargo test --tests
```

- Each instrumented test binary writes `default_<signature>_<n>_<pid>.profraw`. The files land in the **package root**, because that is the tests' working directory. The default pattern has been `default_%m_%p.profraw` since 1.65. If you override `LLVM_PROFILE_FILE`, keep `%m` and `%p`, or the binaries overwrite each other.
- The LLVM tools are **not on PATH**. They live in `$(rustc --print sysroot)/lib/rustlib/<host-triple>/bin/`. `cargo-binutils` wraps them, and `cargo llvm-cov` (a third-party crate) wraps the whole workflow. The tools must match rustc's LLVM version, which `rustc -vV` shows.
- Merge and report:
  ```bash
  llvm-profdata merge -sparse default_*.profraw -o tests.profdata
  llvm-cov report --instr-profile=tests.profdata \
    --object target/debug/deps/<crate>-<hash> --object target/debug/deps/<test>-<hash> \
    --ignore-filename-regex='/.cargo/registry'
  ```
- List the test binaries for `--object` with:
  `cargo test --tests --no-run --message-format=json | jq -r 'select(.profile.test == true) | .filenames[]' | grep -v dSYM`
- Doctest coverage needs nightly rustdoc (`-Z unstable-options --persist-doctests`), and its line numbers are known to be wrong (issue #79417).
- `#[coverage(off)]` is nightly-only. Stable rejects it with `` E0658 the `#[coverage]` attribute is an experimental feature `` (measured, issue #84605).
- `-C instrument-coverage` turns on v0 symbol mangling. Use `rustfilt` (`cargo install rustfilt`) as `--Xdemangler`.

## Running tests for a non-host target

- **A runner.** Set `[target.<triple>] runner = "qemu-aarch64 -L /usr/aarch64-linux-gnu"` in `.cargo/config.toml`, or `CARGO_TARGET_<TRIPLE_UPPER_UNDERSCORED>_RUNNER`. After that, `cargo test --target <triple>` runs each test binary under the runner. If qemu-user cannot run a dynamically linked binary, link it statically with `RUSTFLAGS="-C target-feature=+crt-static"`.
- **Build here, run there.** Run `cargo test --target <triple> --no-run`, then take the paths from the `Executable unittests src/lib.rs (target/<triple>/debug/deps/<name>-<hash>)` lines and copy them to the device. Pass filters and libtest flags as process arguments, such as `./name-hash --exact mod::test --test-threads 1`.
- **Doctests when cross-compiling** have been stable since Cargo 1.89. They run with `--target` like other tests, so they need the runner too.
- **`panic = "abort"` targets.** All wasm targets by default, UEFI, and most bare-metal targets ship a std built with `panic = "abort"`. libtest needs unwinding, so ordinary `#[test]` does not work there on stable. The options are nightly `-Z panic-abort-tests`, a custom test framework, or testing the logic on the host. On `wasm32-unknown-unknown`, `println!` does nothing, so failures are silent. The docs recommend testing wasm compatibility on `wasm32-wasip1` instead.
- `--no-run` with `--message-format=json` gives each binary's path in its `executable` field, which is the reliable input for scripts.
