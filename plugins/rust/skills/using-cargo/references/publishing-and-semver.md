# Publishing, registries, and SemVer

Contents:
- [Before publishing](#before-publishing)
- [What goes into the `.crate`](#what-goes-into-the-crate)
- [cargo publish](#cargo-publish)
- [Yanking](#yanking)
- [Owners](#owners)
- [Alternate registries and credentials](#alternate-registries-and-credentials)
- [SemVer: what is a breaking change](#semver-what-is-a-breaking-change)

This plugin's hook asks the user before `cargo publish` without `--dry-run`, `cargo yank`, and `cargo owner --add/--remove`. `--dry-run`, `cargo package`, and `cargo owner --list` run without a prompt.

## Before publishing

- crates.io requires `description` and `license` or `license-file`. It also wants `repository`, `readme`, `keywords` (at most 5), and `categories` (at most 5, valid slugs). `documentation` defaults to the docs.rs page.
- Every dependency needs a `version`. A path-only dependency fails packaging (measured: "all dependencies must have a version requirement specified when packaging"). A dev-dependency without `version` is stripped instead.
- crates.io allows dependencies only from crates.io.
- Names are first come, first served, at most 64 characters, ASCII; `-` and `_` count as the same name.
- Run `cargo package --list` to see exactly which files ship, then `cargo publish --dry-run` (`-n`), which packages and verify-builds without uploading.
- Missing `license-file` or `readme` files are errors at package time (1.81).

## What goes into the `.crate`

- `Cargo.toml` is normalized: workspace inheritance resolved, `[patch]`, `[replace]`, and `[workspace]` removed. The original ships as `Cargo.toml.orig`.
- `Cargo.lock` is always included (since 1.84), for libraries too (measured on a fresh `--lib`). `--exclude-lockfile` (1.87) omits it. Dependents never use it; `cargo install --locked` does.
- `.cargo_vcs_info.json` records the git commit and `path_in_vcs` on a best-effort basis; it proves nothing about provenance.
- `include`/`exclude` decide the rest; with `include` set, `.gitignore` is not consulted. crates.io limits a `.crate` to 10 MB.
- `cargo package` writes `target/package/<name>-<version>.crate` and verify-builds an extracted copy. Since 1.93, `cargo publish` no longer leaves the `.crate` behind; use `cargo package` when you need the file.

## cargo publish

- It checks `package.publish`, packages and verifies, uploads, then **waits until the version appears in the index**. A timeout in that wait does not undo the upload.
- A version can never be overwritten or deleted. Publishing an existing version fails fast (1.83).
- **Multi-package publishing** (stable 1.90): `cargo publish --workspace` or `-p a -p b` publishes in dependency order. It is **not atomic**: a server error part-way leaves some crates published.
- Registry selection: `--registry NAME`; otherwise the single registry in `package.publish`; otherwise `registry.default`; otherwise crates.io.
- `--token` is soft-deprecated (1.92) and hidden from `--help`. Authenticate with `cargo login` (reads the token from stdin) or `CARGO_REGISTRY_TOKEN` / `CARGO_REGISTRIES_<NAME>_TOKEN`.
- `--no-verify` skips the verify build; `--allow-dirty` permits uncommitted changes.
- Release hygiene from the Cargo Book: a changelog entry and a git tag per version. Tools: `cargo-release`, `release-plz`, `cargo-smart-release`.

## Yanking

- `cargo yank --version 1.0.1 [crate]` (or `crate@1.0.1`); `--undo` reverses it. `--vers` is the old spelling.
- A yank removes nothing. The version stays downloadable, existing lockfiles keep using it, and only new resolution skips it. If no compatible version remains, dependents without a lockfile fail to resolve (`"=1.5.0"` errors; `"1.5.0"` moves to 1.5.1 if it exists).
- **Publish the fixed compatible version first, then yank.**
- Yank for an accidental publish, an unintended breaking change, or a badly broken release. For a security issue, publish a RustSec advisory. For leaked credentials, revoke them immediately; a yank cannot recall them. For legal or personal-data problems, contact crates.io (help@crates.io).

## Owners

- `cargo owner --add LOGIN`, `--remove LOGIN`, `--list`. A user is invited and must accept; teams are `github:org:team`.
- A user owner can publish, yank, and add or remove owners, including the one who added them. A team owner can publish and yank but not manage owners.
- Adding a team needs the `read:org` OAuth scope and the organization's approval of crates.io as a third-party app; the error otherwise mentions "could not find the github team".

## Alternate registries and credentials

```toml
# .cargo/config.toml
[registries.internal]
index = "sparse+https://registry.example.com/index/"   # sparse; a plain https:// URL means git
credential-provider = "cargo:token"

[registry]
global-credential-providers = ["cargo:token", "cargo:macos-keychain"]
```

- Depend with `{ version = "1", registry = "internal" }`; publish with `cargo publish --registry internal`, or set `publish = ["internal"]` so crates.io can never receive it.
- crates.io uses the sparse protocol by default (1.70).
- **A registry that requires authentication must have a credential provider configured**; Cargo refuses to store such a token in plaintext implicitly.
- Built-in providers: `cargo:token` (plaintext `$CARGO_HOME/credentials.toml`, and the only provider that reads `*_TOKEN` environment variables), `cargo:macos-keychain`, `cargo:wincred`, `cargo:libsecret`, `cargo:token-from-stdout <cmd>`. In `global-credential-providers`, **later entries take precedence**. A provider path containing spaces needs a `[credential-alias]`.
- `cargo logout` removes the local token but does not revoke it on the server.
- Git dependencies over SSH need a running `ssh-agent`; HTTPS needs a git credential helper. Cargo's built-in SSH ignores `~/.ssh/config`; set `net.git-fetch-with-cli = true` for anything beyond the basics. The docs contradict each other on the `@revoked` known_hosts marker: the changelog says Cargo 1.68.2 added support for it (and marks GitHub's leaked RSA key as revoked), while the Git Authentication page still says it is unsupported. `@cert-authority` is unsupported either way. Use `net.git-fetch-with-cli` when you depend on either marker.

## SemVer: what is a breaking change

Pre-1.0, `0.y.z` treats a change of `y` as major and of `z` as minor; any `0.0.z` change is major.

**Major:**
- Renaming, moving, or removing a public item, including putting it behind a new `cfg`.
- Adding any field, public or private, to a struct whose fields are all public (struct literals break). In a tuple struct, also any change that shifts a public field's index. Adding an enum variant without `#[non_exhaustive]`, or a field to a variant.
- Adding `#[non_exhaustive]` to an existing enum, variant, or struct with no private fields.
- Adding a trait item without a default; changing any trait item's signature, even to a generic one; adding an item that makes the trait not dyn compatible (e.g. an associated `const`); adding a type parameter without a default.
- Tightening generic bounds. Changing a function's arity. Making a safe function `unsafe`.
- Layout of a `repr(C)`, `repr(transparent)`, or `repr(<int>)` type: removing the repr, reordering public `repr(C)` fields, changing the integer, adding `repr(packed)` or `repr(align)`. A default-repr type has no layout guarantee, so its size changing is not breaking.
- Capturing more generic parameters in return-position `impl Trait`. In edition 2024 an RPIT captures every in-scope lifetime by default, so a narrower `use<..>` you write is a commitment.
- Removing a Cargo feature, removing a feature from another feature's list (e.g. from `default`) when that removes functionality, moving existing code behind a new feature, dropping `no_std` support, adding a dependency that requires nightly.

**Possibly breaking (usually accepted as minor):** adding a defaulted trait item or an inherent method (name ambiguity, or an inherent method silently shadowing a trait method), adding a type parameter to a function (breaks turbofish callers), removing an optional dependency that downstream might enable as a feature (avoid by using `dep:`), raising `rust-version`, narrowing supported platforms.

**Minor:** adding public items; adding or removing private fields when one already exists; adding `repr(C)` or `repr(transparent)` to a default-repr type; loosening bounds; adding defaulted type parameters; generalizing a parameter in a way that still accepts the old type (`&dyn Trait` to `&T where T: Trait + ?Sized`); making an `unsafe fn` safe (free and inherent functions only); adding a Cargo feature; changing features on a dependency; new lints firing in users' code (`#[deprecated]`, `#[must_use]`).

Mitigations (the `designing-rust-apis` skill covers designing for them from the start): `#[non_exhaustive]` and constructors from the first release; sealed traits; `#[deprecated]` before removal; re-export a renamed item under its old name; the "semver trick" of publishing a point release of the old major that re-exports the new major's types.
