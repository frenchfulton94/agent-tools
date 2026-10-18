# Task 10 report, Step 1: the direct-distribution reference (R6 pending)

Date: 2026-10-18. Branch: `apple-studio-phase10-games`. Commit `04f7345`, then fix round 1 in `facb146`. The controller writes this file from the implementer's returned text, because subagents may not write report files (ruling P10).

This dispatch covers Step 1 of Task 10 and `bundle.sh`. R6 needs a Developer ID Application certificate, and only the Account Holder can create one. It stops at R6 Step 1, a user step. Nothing was signed with any identity, nothing went to Apple, and `security find-identity` was used read-only.

## What changed

| File | Change |
|---|---|
| `plugins/apple-studio/skills/app-release/references/direct-distribution.md` | New, 565 lines (584 after fix round 1), with a Contents list (P28). Header `> verified: 2026-10 against …` (25 URLs) and `> typecheck: macos 26.0` |
| `plugins/apple-studio/skills/app-release/SKILL.md` | One routing line. The description adds "Developer ID signing and notarization for distribution outside the App Store" and a trigger clause "notarizing or packaging a Mac app as a DMG, zip, or pkg". The description is 868 characters (DESC_MAX 1024) |
| `plugins/apple-studio/skills/app-release/references/signing-and-provisioning.md` | Item 47 fix (see "Changes to signing-and-provisioning.md") and two fence labels |
| `authoring/apple-studio/pipeline/fixtures/metal-probe/bundle.sh` | New, executable. Builds release and writes `build/MetalProbe.app` |
| `authoring/apple-studio/pipeline/fixtures/metal-probe/README.md` | A table row and a closing "The app bundle (R6)" section |
| `$REC/task-10-r6/` | Evidence: help.log, bundle.log, packaging.log, submit-json.log, archs-probe/, selfcheck/, the sidecar, typecheck.log, native.log, and the scripts that write the logs |

`build/` was already gitignored by `fixtures/metal-probe/.gitignore:5`. Nothing changed there.

## The reference's sections

1. What was checked on this machine.
2. Developer ID identities: the two types, who creates them, names, listing, and an expiry and revocation table.
3. The hardened runtime: an exception entitlement table with build settings and game use cases, JIT on Apple silicon, resource entitlements, entitlements-file rules, and get-task-allow.
4. Capabilities outside the Mac App Store, and Developer ID profiles.
5. Building for Apple silicon only.
6. Signing by hand.
7. The release sequence: one-time setup (steps 1–2), then the R6 release block (steps 3–8).
8. notarytool details.
9. Choosing a container: zip, DMG, and pkg, with commands.
10. What Gatekeeper checks.
11. Notary log messages and their fixes.
12. After release: crash reports and symbols.
13. A release smoke test in code (one Swift block).
14. Classic pitfalls.
15. Where else to look.

The reference cross-references `apple-games/references/game-center-and-online.md` for the capability rule, `apple-macos/references/mac-sandbox-and-files.md`, and `apple-metal/references/cpp-and-rust.md`. Each uses the `<skill>/references/<file>.md` form (P30). SKILL.md names no other skill's file path.

## Gates and prose checks

- `typecheck_snippets.py` on direct-distribution.md and signing-and-provisioning.md: exit 0, TOTAL 1/1 (`typecheck.log`). signing-and-provisioning.md has 0 swift blocks, the same as `catalog-before.log` line 12, so there is no PASS→FAIL.
- `typecheck_native.py` on both files: exit 0, TOTAL 0/0 (`native.log`).
- Vale (`vale --config .claude/skills/controlled-engineering-english/scripts/vale/.vale.ini <file>`):
  - direct-distribution.md: 0 errors and 4 warnings. Two are table rows over 25 words, and two are "provisioning" in "provisioning profile", which is a term. An earlier draft had 13 warnings, and the prose fixes cut them to 4.
  - SKILL.md: 2 warnings before and after.
  - signing-and-provisioning.md: 78 warnings before and after.
  - Fixture README: 3 warnings before and after.
- `bun test --timeout 30000`: 542 pass, 0 fail.
- `bun run audit`: exit 0, 0 errors, 54 warnings. None are about direct-distribution.md.
- `claude plugin validate . --strict`: passed.

## Evidence (P34)

- `help.log` (`help-check.sh`): the `--help` or man-page lines behind every spelling. It covers:
  - `notarytool` 1.1.3 (42), and its store-credentials, submit (including the `-f json` choice and the single-result note), log, and history subcommands;
  - `stapler`;
  - `codesign(1)`: `--deep` deprecated for signing as of macOS 13.0, `--force-library-entitlements` and the macOS 15.0 default, `--entitlements -` with `--xml`, `--timestamp`, `runtime`, and `--check-notarization`;
  - `spctl(8)`: `--type execute|install|open`, exit 3 on denial, and no rule edits as of macOS 15.0;
  - `syspolicy_check`, `hdiutil` (including its deprecation notice), `diskutil image create from`, `ditto`, `pkgbuild`, `productbuild`, `productsign`, `pkgutil`, `security find-identity`, and `plutil`.
  - The read-only identity check is at the end. It lists one `Apple Development` identity, with the name redacted after the type. It counts 0 Developer ID Application and 0 Developer ID Installer identities.
- `bundle.log` (`bundle-check.sh`):
  - `bundle.sh` builds, and `plutil -lint` reports OK. The identifier reads back as `dev.frenchfultonjr.apple-studio.metal-probe`, and the binary is arm64.
  - `render --frames 1` printed `frame 0 ok` and `pixel 0 128 64 255`, the expected color for frame 0, and exited 0.
  - An ad hoc `codesign -s - -f -o runtime` signature verified clean (`--verify --strict --verbose=2`), and `spctl --assess` returned `rejected` with exit 3.
  - The script then runs `bundle.sh` again, so the bundle is left unsigned for R6, apart from the linker's ad hoc signature on the binary.
- `packaging.log` (`packaging-check.sh`, scratch outputs only):
  - The `ditto` zip works.
  - `hdiutil create -srcfolder … -format UDZO` works, prints a deprecation warning, and writes a UDZO image.
  - `diskutil image create from --format UDZO` writes UDZO. Without `--format`, it writes ULFO.
  - `hdiutil verify` passes on both images.
  - The unsigned `productbuild --component` works, and `pkgutil` reports "no signature".
  - No mounts are left.
- `submit-json.log` (`submit-json-check.sh`, added in fix round 1):
  - `plutil -extract <key> raw -o -` reads a JSON file and prints the string value.
  - It exits 1 on a missing key.
  - The JSON is an invented sample, so the log does not verify notarytool's output shape.
- `archs-probe/` (`run.sh` and `runs.txt`): a minimal SwiftPM executable package, built with `xcodebuild` for `generic/platform=macOS` in Release. It is not an Xcode app target.
  - Deployment target 26.0, default `ARCHS`: `x86_64 arm64`.
  - Deployment target 26.0, `ARCHS=arm64`: `arm64`.
  - Deployment target 27.0, default `ARCHS`: `arm64`.
  - Deployment target 27.0, `ARCHS=arm64 x86_64`: both slices, plus the warning "The x86_64 architecture is deprecated for your deployment target (macOS 27.0)".
  - The grep of Xcode 27.1's `macOSArchitectures.xcspec` shows `RealArchitectures = ( arm64, x86_64 )` with `ArchitectureSetting = "ARCHS_STANDARD"` at lines 22–23, and `DeploymentTargetRange = ( "10.4.4", "27" )` for x86_64.
- `selfcheck/` (`run.sh` and `runs.txt`): extracts the reference's Swift block verbatim and compiles it. Signed ad hoc with a `get-task-allow` entitlements file, it prints `true`. Signed without one, it prints `false`.
- `direct-distribution.sources.tsv`: 103 claim rows (section, claim, source).

## Findings

1. **`hdiutil create` is deprecated on macOS 27.0.1.** No notes file has this.
   - The `-help` output prints a WARNING.
   - `man hdiutil` has a DEPRECATION NOTICE that maps `create -srcfolder` to `diskutil image create from`.
   - The reference shows `diskutil image create from --format UDZO` as the main DMG command, and records the `hdiutil` form as working but deprecated.
   - `diskutil` defaults to ULFO, not the UDZO that Apple's packaging page names.
2. **ARCHS verify item resolved (task-7 item 45, g06:55).** The measurements under Evidence show:
   - Under Xcode 27.1, a 27.0 floor builds arm64 only by default.
   - A 26.0 floor still builds universal.
   - An Apple silicon-only build at the 26.0 floor needs `ARCHS = arm64`.
   - The measurement is on a SwiftPM package built through `xcodebuild`, and the reference says so.
3. **Apple silicon-only Mac App Store targeting (r01:105) is only partly sourced.**
   - The games overview (lines 186–187) is the only Apple text found.
   - Its link `/macos/submit/` now redirects to `/app-store/submitting/`, which does not describe the section. The page was fetched with curl and saved in `$TMP/r06-extra/`.
   - The reference says the App Store Connect classification is unverified, and keeps that part short.
4. **Account Holder verify item resolved (task-7 item 45, r01:57).** The account help page "Developer ID certificates", fetched with curl, gives:
   - "Required role: Account Holder".
   - Admins with the cloud-managed Developer ID certificate access role can also use cloud-managed certificates.
   - A team can hold up to five certificates of each type.
   - Developer ID profiles are valid for 18 years, and they are checked at every launch.
5. **A contradiction between Apple pages, stated in the reference.** The certificates overview says that a pkg with a trusted timestamp still installs after the Installer certificate expires. The Developer ID certificates page says that such a pkg must be re-signed.
6. **The runtime check caught a non-working snippet.** The first draft of the smoke test cast `CFDictionary` to `[String: Any]`, and it failed to compile under `swiftc`. Bridging through `NSDictionary?` fixed it. The final block passes the gate and runs correctly.
7. **Order of the R6 sequence.**
   - A `ditto -c -k --keepParent` zip step sits between the spctl negative control and `submit`. The notary service rejects a bare `.app` (r01:31), and the brief's sequence has no container step.
   - `notarytool log` needs auth: its help lists `-p, --keychain-profile`, so the log line passes it.
8. **The corrected spellings from findings 43–44 are applied.** They are:
   - `spctl --type execute`;
   - `codesign -d --entitlements - --xml`;
   - `-srcfolder`;
   - `--deep` deprecated for signing;
   - `--force-library-entitlements`;
   - the keychain name with the team name and the Team ID.
9. **Noise, not acted on:**
   - `productbuild` printed four "write: Permission denied" lines, but it wrote the pkg and exited 0.
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
| 45a (ARCHS default) | Resolved by measurement (archs-probe, on a SwiftPM package) |
| 45b (Account Holder) | Resolved from the account help page |
| 45c (Apple silicon-only targeting) | Partly sourced. Marked unverified |
| 46 (no identity) | Confirmed read-only in help.log |
| 47 | Fixed in signing-and-provisioning.md |

## Open for R6 and the controller

- R6 Step 1 (USER STEP):
  - The Account Holder creates a Developer ID Application certificate, in Xcode (Settings > Accounts > Manage Certificates > +) or in Certificates, Identifiers & Profiles.
  - The user runs reference step 1, `xcrun notarytool store-credentials "<profile name>" --apple-id "<Apple ID>" --team-id "<Team ID>"`, which prompts for the app-specific password, and then reports the profile name.
  - Reference step 2 (`security find-identity -v -p codesigning`) gives the `IDENTITY` value.
- R6 sets the six variables at the top of the release block:
  - `APP` is the fixture's `build/MetalProbe.app`, after `./bundle.sh`.
  - `ZIP` is a scratch path.
  - `PROFILE` and `IDENTITY` come from steps 1–2.
  - `SUBMIT_JSON` and `LOG` are under `$REC/raw/`.
- R6 then runs steps 3–8 verbatim, with the brief's team-confirmation STOP before step 6.
- In step 6, the `id` and `status` keys of `notarytool submit -f json` are unverified until R6. If the JSON shape differs, `plutil` exits 1 and the reference changes at Step 5 (reconcile).
- Step 8's "Notarized Developer ID" source string is expected per the task brief only, and R6 confirms or corrects it.
- Every notarization claim stays marked "R6 pending: not yet runtime-checked" until R6 runs.

## Fix round 1

The reviewer's verdict was "Needs fixes": 1 Important finding and 5 Minor. Commit `facb146` fixes all six.

- **Important: `$SUBMISSION_ID` was never assigned in the release block.**
  - Step 6 now runs `submit … --wait -f json > "$SUBMIT_JSON"`.
  - It prints the status with `plutil -extract status raw -o -`, assigns `SUBMISSION_ID="$(plutil -extract id raw -o - "$SUBMIT_JSON")"`, and calls `notarytool log "$SUBMISSION_ID" … "$LOG"`.
  - `help.log` now shows `-f json` as a documented choice, and that json gives a single result at the end (submit help lines 30–34).
  - The JSON keys are not documented, and the block's comment says `id` and `status` are unverified until R6.
  - `submit-json.log` shows that `plutil` reads JSON, prints raw strings, and exits 1 on a missing key, on an invented sample.
  - The log destination is now the variable `LOG="notary-log.json"`, and the submit result is `SUBMIT_JSON="notary-submit.json"`, so R6 points both at `$REC/raw/` without editing a command.
- **Minor 1: `IDENTITY` was set before step 2 found it, and step 1 was inside the pasted block.**
  - Steps 1–2 are now a separate "One-time setup" block, run by hand.
  - The release block covers steps 3–8, and its variables (`PROFILE`, `IDENTITY`) say they come from steps 1 and 2.
- **Minor 2: the "Notarized Developer ID" string had no Apple source.**
  - Step 8's comment now reads "Expected (task brief, not an Apple page; R6 pending)".
  - The sidecar row says "expected (task brief); R6 pending. No corpus page or help text has the string".
- **Minor 3: the probe's spec grep did not show `ArchitectureSetting`.**
  - `archs-probe/run.sh` now greps with `-e ArchitectureSetting`.
  - Only the grep step was re-run, and the last section of `runs.txt` was replaced and labelled as a re-run. It shows `ArchitectureSetting = "ARCHS_STANDARD"` at xcspec line 23, under `RealArchitectures = ( arm64, x86_64 )` at line 22.
  - The build results above that section are unchanged.
- **Minor 4: the "Measured" ARCHS table did not say what was built.** It now says it was measured on a minimal SwiftPM executable package built through `xcodebuild`, and that an Xcode app target was not tested. The sidecar row says the same.
- **Minor 5: the Vale run was not recorded.** It is now recorded under "Gates and prose checks": direct-distribution.md has 0 errors and 4 warnings, and the counts for the other edited files are listed there.
- **Verification after the round:**
  - Both gates were re-run on both references: Swift 1/1, native 0/0, exit 0.
  - Vale on direct-distribution.md: 0 errors, 4 warnings, unchanged.
  - `bun test --timeout 30000`: 542 pass, 0 fail.
  - `bun run audit`: 0 errors, 54 warnings.
  - `claude plugin validate . --strict`: passed.
  - The selfcheck Swift block is unchanged, so `selfcheck/runs.txt` still applies.
