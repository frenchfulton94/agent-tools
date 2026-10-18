# Task 10 report, Step 1: the direct-distribution reference (R6 pending)

Date: 2026-10-18. Branch: `apple-studio-phase10-games`. Commit `04f7345`. The controller writes this file from the implementer's returned text, because subagents may not write report files (ruling P10).

This dispatch covers Step 1 of Task 10 and `bundle.sh`. R6 needs a Developer ID Application certificate, and only the Account Holder can create one. It stops at R6 Step 1, a user step. Nothing was signed with any identity, nothing went to Apple, and `security find-identity` was used read-only.

## What changed

| File | Change |
|---|---|
| `plugins/apple-studio/skills/app-release/references/direct-distribution.md` | New, 565 lines, with a Contents list (P28). Header `> verified: 2026-10 against …` (25 URLs) and `> typecheck: macos 26.0` |
| `plugins/apple-studio/skills/app-release/SKILL.md` | One routing line. The description adds "Developer ID signing and notarization for distribution outside the App Store" and a trigger clause "notarizing or packaging a Mac app as a DMG, zip, or pkg". The description is 868 characters (DESC_MAX 1024) |
| `plugins/apple-studio/skills/app-release/references/signing-and-provisioning.md` | Item 47 fix (see "Changes to signing-and-provisioning.md") and two fence labels |
| `authoring/apple-studio/pipeline/fixtures/metal-probe/bundle.sh` | New, executable. Builds release and writes `build/MetalProbe.app` |
| `authoring/apple-studio/pipeline/fixtures/metal-probe/README.md` | A table row and a closing "The app bundle (R6)" section |
| `$REC/task-10-r6/` | Evidence: help.log, bundle.log, packaging.log, archs-probe/, selfcheck/, the sidecar, typecheck.log, native.log, and the scripts that write the logs |

`build/` was already gitignored by `fixtures/metal-probe/.gitignore:5`. Nothing changed there.

## The reference's sections

1. What was checked on this machine.
2. Developer ID identities: the two types, who creates them, names, listing, and an expiry and revocation table.
3. The hardened runtime: an exception entitlement table with build settings and game use cases, JIT on Apple silicon, resource entitlements, entitlements-file rules, and get-task-allow.
4. Capabilities outside the Mac App Store, and Developer ID profiles.
5. Building for Apple silicon only.
6. Signing by hand.
7. The release sequence (the R6 commands).
8. notarytool details.
9. Choosing a container: zip, DMG, and pkg, with commands.
10. What Gatekeeper checks.
11. Notary log messages and their fixes.
12. After release: crash reports and symbols.
13. A release smoke test in code (one Swift block).
14. Classic pitfalls.
15. Where else to look.

The reference cross-references `apple-games/references/game-center-and-online.md` for the capability rule, `apple-macos/references/mac-sandbox-and-files.md`, and `apple-metal/references/cpp-and-rust.md`. Each uses the `<skill>/references/<file>.md` form (P30). SKILL.md names no other skill's file path.

## Evidence (P34)

- `help.log` (`help-check.sh`): the `--help` or man-page lines behind every spelling. It covers:
  - `notarytool` 1.1.3 (42) and its store-credentials, submit, log, and history subcommands;
  - `stapler`;
  - `codesign(1)`: `--deep` deprecated for signing as of macOS 13.0, `--force-library-entitlements` and the macOS 15.0 default, `--entitlements -` with `--xml`, `--timestamp`, `runtime`, and `--check-notarization`;
  - `spctl(8)`: `--type execute|install|open`, exit 3 on denial, and no rule edits as of macOS 15.0;
  - `syspolicy_check`, `hdiutil`, `diskutil image create from`, `ditto`, `pkgbuild`, `productbuild`, `productsign`, `pkgutil`, `security find-identity`, and `plutil`.
  - The read-only identity check is at the end. It lists one `Apple Development` identity, with the name redacted after the type. It counts 0 Developer ID Application and 0 Developer ID Installer identities.
- `bundle.log` (`bundle-check.sh`):
  - `bundle.sh` builds and `plutil -lint` reports OK. The identifier reads back as `dev.frenchfultonjr.apple-studio.metal-probe`, and the binary is arm64.
  - `render --frames 1` printed `frame 0 ok` and `pixel 0 128 64 255`, which is the expected color for frame 0, and exited 0.
  - An ad hoc `codesign -s - -f -o runtime` signature verified clean (`--verify --strict --verbose=2`), and `spctl --assess` returned `rejected`, exit 3.
  - The script then ran `bundle.sh` again, so the bundle is unsigned for R6. Only the linker's ad hoc signature on the binary remains.
- `packaging.log` (`packaging-check.sh`, scratch outputs only):
  - The `ditto` zip works.
  - `hdiutil create -srcfolder … -format UDZO` works, prints a deprecation warning, and makes a UDZO image.
  - `diskutil image create from --format UDZO` makes a UDZO image. Without `--format`, it makes ULFO.
  - `hdiutil verify` passes on both images.
  - The unsigned `productbuild --component` works, and `pkgutil` reports "no signature". No mounts are left.
- `archs-probe/` (`run.sh` and `runs.txt`): a minimal SwiftPM package built with `xcodebuild` for `generic/platform=macOS` in Release.
  - At deployment target 26.0 with default `ARCHS`: `x86_64 arm64`.
  - At 26.0 with `ARCHS=arm64`: `arm64`.
  - At 27.0 with default `ARCHS`: `arm64`.
  - At 27.0 with `ARCHS=arm64 x86_64`: both slices, plus the warning "The x86_64 architecture is deprecated for your deployment target (macOS 27.0)".
  - The run also greps Xcode 27.1's `macOSArchitectures.xcspec`: `ARCHS_STANDARD` is `( arm64, x86_64 )`, and x86_64 has `DeploymentTargetRange = ( "10.4.4", "27" )`.
- `selfcheck/` (`run.sh` and `runs.txt`): extracts the reference's Swift block verbatim and compiles it. It signs ad hoc with a `get-task-allow` entitlements file, which prints `true`, and without one, which prints `false`.
- `direct-distribution.sources.tsv`: 99 claim rows (section, claim, source).

## Findings

1. **`hdiutil create` is deprecated on macOS 27.0.1.** No notes file has this. The `-help` output prints a WARNING, and `man hdiutil` has a DEPRECATION NOTICE that maps `create -srcfolder` to `diskutil image create from`. The reference shows `diskutil image create from --format UDZO` as the main DMG command and records the `hdiutil` form as working but deprecated. Note: `diskutil` defaults to ULFO, not the UDZO that Apple's packaging page names.
2. **ARCHS verify item resolved (task-7 item 45, g06:55).** Measured, as listed under Evidence. Under Xcode 27.1, a 27.0 floor builds arm64 only by default, and a 26.0 floor still builds universal. An Apple silicon-only build at the 26.0 floor needs `ARCHS = arm64`.
3. **Apple silicon-only Mac App Store targeting (r01:105) is only partly sourced.** The games overview (lines 186–187) is the only Apple text found. Its link `/macos/submit/` now redirects to `/app-store/submitting/`, which does not describe the section (fetched with curl, saved in `$TMP/r06-extra/`). The reference says the App Store Connect classification is unverified and keeps that part short.
4. **Account Holder verify item resolved (task-7 item 45, r01:57).** The account help page "Developer ID certificates", fetched with curl, says "Required role: Account Holder". It also says cloud-managed certificates are open to admins with the cloud-managed Developer ID certificate access role, and that a team can hold up to five of each type. The page adds that Developer ID profiles are valid for 18 years and are checked at every launch.
5. **A contradiction between Apple pages, stated in the reference.** The certificates overview says a pkg with a trusted timestamp still installs after the Installer certificate expires. The Developer ID certificates page says such a pkg must be re-signed.
6. **The runtime check caught a non-working snippet that the compile gate did not.** The first draft of the smoke test cast `CFDictionary` to `[String: Any]` and failed to compile under `swiftc`. Bridging through `NSDictionary?` fixed it. The final block passes the gate and runs correctly.
7. **Order of the R6 sequence.** A `ditto -c -k --keepParent` zip step sits between the spctl negative control and `submit`. The notary service rejects a bare `.app` (r01:31), and the brief's sequence has no container step. `notarytool log` needs auth: its help lists `-p, --keychain-profile`, so the log line passes it.
8. **The corrected spellings from findings 43–44 are applied.** These are `spctl --type execute`, `codesign -d --entitlements - --xml`, `-srcfolder`, `--deep` deprecated for signing, `--force-library-entitlements`, and the keychain name with team name and Team ID.
9. **Noise, not acted on:**
   - `productbuild` printed four "write: Permission denied" lines but wrote the pkg and exited 0.
   - The `ditto` zip holds AppleDouble `._` entries for extended attributes. That is Apple's documented form, so the reference keeps it. R6 shows whether the notary service cares.

## Changes to signing-and-provisioning.md

- **Item 47.** The signature-format line now says that a `CodeDirectory v=` value below 20400 needs a re-sign, and that 20500 is the page's example. Source: `using-the-latest-code-signature-format.md:34`.
- **Fence labels.** The file's two bare code fences (lines 64 and 84) are now labelled `bash`. Without the labels, `typecheck_native.py` exits 2 ("unlabelled fence"), and the Global Constraints require every fence in an edited reference to be gated or labelled.
- **The `verified:` header is not re-stamped.** CONVENTIONS does not require a re-stamp on edit, and the URL behind the fix is already in the header.

## Verify-before-stating items (task-7 report)

| Item | Status |
|---|---|
| 43 (four spellings) | Applied. Each is checked in help.log |
| 44 | `--deep` and `--force-library-entitlements` are applied. `altool` is noted as still uploading to App Store Connect. The launchctl verbs are not used in this file |
| 45a (ARCHS default) | Resolved by measurement (archs-probe) |
| 45b (Account Holder) | Resolved from the account help page |
| 45c (Apple silicon-only targeting) | Partly sourced. Marked unverified |
| 46 (no identity) | Confirmed read-only in help.log |
| 47 | Fixed in signing-and-provisioning.md |

## Open for R6 and the controller

- R6 Step 1 (USER STEP):
  - The Account Holder creates a Developer ID Application certificate, in Xcode (Settings > Accounts > Manage Certificates > +) or in Certificates, Identifiers & Profiles.
  - The user runs `xcrun notarytool store-credentials "<profile>" --apple-id "<Apple ID>" --team-id "<Team ID>"`, which prompts for the app-specific password, and reports the profile name.
- The literal log path `notary-log.json` in the reference's `notarytool log` line differs from the brief's `$REC/raw/` destination. R6 passes the `$REC/raw/` path, and Step 5 (reconcile) can make the path a variable in the reference. This is a mechanical, one-line fix (P36).
- Every notarization claim stays marked "R6 pending: not yet runtime-checked" until R6 runs.
