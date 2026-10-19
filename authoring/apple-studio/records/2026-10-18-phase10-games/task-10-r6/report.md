# Task 10 report: the direct-distribution reference (closed without R6)

Date: 2026-10-18. Branch: `apple-studio-phase10-games`. Commits: `04f7345` (Step 1), `facb146` (fix round 1), and `e350ac8` (closed without R6, ruling P44). The controller writes this file from the implementer's returned text, because subagents may not write report files (ruling P10).

This task wrote Step 1 of Task 10 and `bundle.sh`. R6 needs a Developer ID Application certificate, and only the Account Holder of a paid team can create one. Neither of the user's teams could, so the user decided to skip R6 (P44). Nothing was signed with any identity, nothing went to Apple, and `security find-identity` and `security find-certificate` were used read-only.

## What changed

| File | Change |
|---|---|
| `plugins/apple-studio/skills/app-release/references/direct-distribution.md` | New, with a Contents list (P28): 565 lines, 584 after fix round 1, 614 at close. Header `> verified: 2026-10 against …` (25 URLs) and `> typecheck: macos 26.0` |
| `plugins/apple-studio/skills/app-release/SKILL.md` | One routing line. The description adds "Developer ID signing and notarization for distribution outside the App Store" and a trigger clause, "notarizing or packaging a Mac app as a DMG, zip, or pkg". The description is 868 characters (DESC_MAX 1024) |
| `plugins/apple-studio/skills/app-release/references/signing-and-provisioning.md` | The item 47 fix (see "Changes to signing-and-provisioning.md") and two fence labels |
| `authoring/apple-studio/pipeline/fixtures/metal-probe/bundle.sh` | New, executable. Builds release and writes `build/MetalProbe.app` |
| `authoring/apple-studio/pipeline/fixtures/metal-probe/README.md` | A table row, and a closing "The app bundle (R6)" section that notes R6 was skipped |
| `authoring/apple-studio/docs/deferred.md` | Item 24: R6 skipped |
| `$REC/task-10-r6/` | Evidence: help.log, bundle.log, packaging.log, submit-json.log, identity.log, archs-probe/, selfcheck/, the sidecar, typecheck.log, native.log, and the scripts that write the logs |

`build/` was already gitignored by `fixtures/metal-probe/.gitignore:5`. Nothing changed there.

## The reference's sections

1. What was checked on this machine.
2. Developer ID identities. It covers:
   - the two types, who creates them, and their names;
   - reading the Team ID from the certificate subject;
   - listing identities;
   - the Manage Certificates menu;
   - an expiry and revocation table.
3. The hardened runtime: an exception entitlement table with build settings and game use cases, JIT on Apple silicon, resource entitlements, entitlements-file rules, and get-task-allow.
4. Capabilities outside the Mac App Store, and Developer ID profiles.
5. Building for Apple silicon only.
6. Signing by hand.
7. The release sequence: one-time setup (steps 1–2), then the release block (steps 3–8).
8. notarytool details.
9. Choosing a container: zip, DMG, and pkg, with commands.
10. What Gatekeeper checks.
11. Notary log messages and their fixes.
12. After release: crash reports and symbols.
13. A release smoke test in code (one Swift block).
14. Classic pitfalls.
15. Where else to look.

The reference cross-references three files of other skills, each in the `<skill>/references/<file>.md` form (P30):
- `apple-games/references/game-center-and-online.md`, for the capability rule;
- `apple-macos/references/mac-sandbox-and-files.md`;
- `apple-metal/references/cpp-and-rust.md`.

SKILL.md names no other skill's file path.

## Gates and prose checks

- `typecheck_snippets.py` on direct-distribution.md and signing-and-provisioning.md: exit 0, TOTAL 1/1 (`typecheck.log`). signing-and-provisioning.md has 0 swift blocks, the same as `catalog-before.log` line 12, so no snippet went from PASS to FAIL.
- `typecheck_native.py` on both files: exit 0, TOTAL 0/0 (`native.log`).
- Vale, run as `vale --config .claude/skills/controlled-engineering-english/scripts/vale/.vale.ini <file>`:
  - direct-distribution.md: 0 errors and 4 warnings. Two warnings are table rows over 25 words. The other two flag "provisioning" in "provisioning profile", which is a term. An earlier draft had 13 warnings, and the prose fixes cut them to 4. At close the count is still 4.
  - SKILL.md: 2 warnings before and after.
  - signing-and-provisioning.md: 78 warnings before and after.
  - Fixture README: 3 warnings before and after.
  - deferred.md: 89 warnings before and after item 24.
- `bun test --timeout 30000`: 542 pass, 0 fail.
- `bun run audit`: exit 0, 0 errors, 54 warnings. None are about direct-distribution.md.
- `claude plugin validate . --strict`: passed.

## Evidence (P34)

- `help.log` (`help-check.sh`) holds the `--help` or man-page lines behind every spelling:
  - `notarytool` 1.1.3 (42), and its store-credentials, submit, log, and history subcommands. The submit lines include the `-f json` choice and the single-result note.
  - `stapler`.
  - `codesign(1)`: `--deep` deprecated for signing as of macOS 13.0, `--force-library-entitlements` and the macOS 15.0 default, `--entitlements -` with `--xml`, `--timestamp`, `runtime`, and `--check-notarization`.
  - `spctl(8)`: `--type execute|install|open`, exit 3 on denial, and no rule edits as of macOS 15.0.
  - `syspolicy_check`, `hdiutil` (with its deprecation notice), `diskutil image create from`, `ditto`, `pkgbuild`, `productbuild`, `productsign`, `pkgutil`, `security find-identity`, and `plutil`.
  - A read-only identity check from Step 1. It shows the one identity present then, with the name redacted after the type.
- `identity.log` (added at close):
  - `security find-identity -v -p codesigning` lists two `Apple Development` identities and 0 Developer ID identities.
  - For each certificate, the subject (OU = Team ID, O = team name) and the expiry, read with `security find-certificate -c … -p` into `$TMP/r06-certs/` and then `openssl x509 -noout -subject`.
  - Emails are redacted to `<Apple ID 1>` and `<Apple ID 2>`. SHA-1 hashes and the subject UID are redacted too.
- `bundle.log` (`bundle-check.sh`):
  - `bundle.sh` builds, and `plutil -lint` reports OK. The identifier reads back as `dev.frenchfultonjr.apple-studio.metal-probe`, and the binary is arm64.
  - `render --frames 1` prints `frame 0 ok` and `pixel 0 128 64 255`, the expected color for frame 0, and exits 0.
  - An ad hoc `codesign -s - -f -o runtime` signature verifies clean (`--verify --strict --verbose=2`). `spctl --assess` returns `rejected`, exit 3.
  - The script then runs `bundle.sh` again, so the bundle is unsigned apart from the linker's ad hoc signature on the binary.
- `packaging.log` (`packaging-check.sh`, scratch outputs only):
  - The `ditto` zip works.
  - `hdiutil create -srcfolder … -format UDZO` works, prints a deprecation warning, and writes UDZO.
  - `diskutil image create from --format UDZO` writes UDZO. Without `--format` it writes ULFO.
  - `hdiutil verify` passes on both images.
  - The unsigned `productbuild --component` works, and `pkgutil` reports "no signature". No mounts are left.
- `submit-json.log` (`submit-json-check.sh`): `plutil -extract <key> raw -o -` reads a JSON file, prints the string, and exits 1 on a missing key. The input is an invented sample, so the check does not verify notarytool's output shape.
- `archs-probe/` (`run.sh` and `runs.txt`): a minimal SwiftPM executable package built with `xcodebuild` for `generic/platform=macOS` in Release. It is not an Xcode app target.
  - 26.0 with default `ARCHS`: `x86_64 arm64`.
  - 26.0 with `ARCHS=arm64`: `arm64`.
  - 27.0 with default `ARCHS`: `arm64`.
  - 27.0 with `ARCHS=arm64 x86_64`: both slices, with the warning "The x86_64 architecture is deprecated for your deployment target (macOS 27.0)".
  - The xcspec grep shows `RealArchitectures = ( arm64, x86_64 )` with `ArchitectureSetting = "ARCHS_STANDARD"` at lines 22–23, and `DeploymentTargetRange = ( "10.4.4", "27" )` for x86_64.
- `selfcheck/` (`run.sh` and `runs.txt`): extracts the reference's Swift block verbatim and compiles it. Signed ad hoc with a `get-task-allow` entitlements file, it prints `true`. Signed without one, it prints `false`.
- `direct-distribution.sources.tsv`: 108 rows (header plus 107 claims), each with section, claim, and source.

## Findings

1. **`hdiutil create` is deprecated on macOS 27.0.1.** No notes file has this.
   - The `-help` output prints a WARNING, and `man hdiutil` has a DEPRECATION NOTICE that maps `create -srcfolder` to `diskutil image create from`.
   - The reference shows `diskutil image create from --format UDZO` as the main DMG command, and records the `hdiutil` form as working but deprecated.
   - `diskutil` defaults to ULFO, not the UDZO that Apple's packaging page names.
2. **The ARCHS verify item is resolved (task-7 item 45, g06:55).**
   - The measurements are listed under Evidence. Under Xcode 27.1, a 27.0 floor builds arm64 only by default, and a 26.0 floor still builds universal.
   - An Apple silicon-only build at the 26.0 floor needs `ARCHS = arm64`.
   - The measurement used a SwiftPM package built through `xcodebuild`, and the reference says so.
3. **Apple silicon-only Mac App Store targeting (r01:105) is only partly sourced.**
   - The games overview (lines 186–187) is the only Apple text found.
   - That page links `/macos/submit/`, which now redirects to `/app-store/submitting/`. The submitting page does not describe the section. It was fetched with curl and saved in `$TMP/r06-extra/`.
   - The reference says the App Store Connect classification is unverified, and keeps that part short.
4. **The Account Holder verify item is resolved (task-7 item 45, r01:57).** The account help page "Developer ID certificates", fetched with curl, says:
   - "Required role: Account Holder";
   - cloud-managed certificates are also open to admins with the cloud-managed Developer ID certificate access role;
   - a team can hold up to five certificates of each type;
   - Developer ID profiles are valid for 18 years and are checked at every launch.
5. **The Apple pages contradict each other, and the reference says so.** The certificates overview says a pkg with a trusted timestamp still installs after the Installer certificate expires. The Developer ID certificates page says such a pkg must be re-signed.
6. **The runtime check caught a snippet that did not compile.** The first draft of the smoke test cast `CFDictionary` to `[String: Any]`, and `swiftc` rejected it. Bridging through `NSDictionary?` fixed it. The final block passes the gate and runs correctly.
7. **The release sequence adds a zip step.**
   - A `ditto -c -k --keepParent` step sits between the spctl negative control and `submit`. The notary service rejects a bare `.app` (r01:31), and the brief's sequence has no container step.
   - `notarytool log` needs authentication. Its help lists `-p, --keychain-profile`, so the log line passes it.
8. **The corrected spellings from findings 43–44 are applied:** `spctl --type execute`, `codesign -d --entitlements - --xml`, and `-srcfolder`. `--deep` is marked deprecated for signing, and `--force-library-entitlements` is documented. Identity names carry the team name and the Team ID.
9. **An identity name does not carry the Team ID (found at close).**
   - On this machine, the `Apple Development` names carry the Apple ID and the IDs RTC3TK2XFJ and G4MYV6D63X. The subject OU fields hold ULQJ329QSN and 2F7J72JV48 (`identity.log`).
   - The account help says a keychain name includes the team name and Team ID. That does not hold for these certificates.
   - The reference now reads the Team ID from the subject OU. It dropped the unverified step 2 comment that "the name ends with the Team ID".
10. **Noise, not acted on:**
    - `productbuild` printed four "write: Permission denied" lines, but it wrote the pkg and exited 0.
    - The `ditto` zip holds AppleDouble `._` entries for extended attributes. That is Apple's documented form, and deferred item 24 records whether the notary service accepts it.

## Changes to signing-and-provisioning.md

- **Item 47.** The signature-format line now says that a `CodeDirectory v=` value below 20400 needs a re-sign, and that 20500 is only the page's example. Source: `using-the-latest-code-signature-format.md:34`.
- **Fence labels.** The file's two bare code fences (lines 64 and 84) are now labelled `bash`. Without the labels, `typecheck_native.py` exits 2 ("unlabelled fence"). The Global Constraints also require every fence in an edited reference to be gated or labelled.
- **The `verified:` header is not re-stamped.** CONVENTIONS does not require a re-stamp on edit, and the URL behind the fix is already in the header.

## Verify-before-stating items (task-7 report)

| Item | Status |
|---|---|
| 43 (four spellings) | Applied. Each is checked in help.log |
| 44 | `--deep` and `--force-library-entitlements` are applied. `altool` is noted as still uploading to App Store Connect. The launchctl verbs are not used in this file |
| 45a (ARCHS default) | Resolved by measurement (archs-probe, on a SwiftPM package) |
| 45b (Account Holder) | Resolved from the account help page |
| 45c (Apple silicon-only targeting) | Partly sourced. Marked unverified |
| 46 (no identity) | Confirmed read-only in help.log, and again at close in identity.log |
| 47 | Fixed in signing-and-provisioning.md |

## Open for R6 and the controller (superseded by "Closed without R6 (P44)")

As planned at Step 1:
- R6 Step 1 was a user step. The Account Holder creates a Developer ID Application certificate, then the user runs reference steps 1–2.
- R6 sets the six variables at the top of the release block and runs steps 3–8 verbatim, with the team-confirmation stop before step 6.
- The notarization claims carry a runtime-check marker. At close it reads "not runtime-checked: needs a Developer ID identity (deferred item 24)".

## Fix round 1

The reviewer's verdict was "Needs fixes", with 1 Important and 5 Minor findings. All six are fixed in `facb146`.

- **Important: `$SUBMISSION_ID` was never assigned in the release block.**
  - Step 6 now runs `submit … --wait -f json > "$SUBMIT_JSON"` and prints the status with `plutil -extract status raw -o -`.
  - It then assigns `SUBMISSION_ID="$(plutil -extract id raw -o - "$SUBMIT_JSON")"` and calls `notarytool log "$SUBMISSION_ID" … "$LOG"`.
  - `help.log` shows `-f json` as a documented choice that gives a single result at the end (submit help lines 30–34). The JSON keys are not documented, and the block's comment says so.
  - `submit-json.log` checks the `plutil` half on an invented sample.
  - The log destination is now a variable, `LOG="notary-log.json"`, and so is the submit result, `SUBMIT_JSON="notary-submit.json"`.
- **Minor 1: `IDENTITY` was set before step 2 found it, and step 1 was inside the pasted block.** Steps 1–2 are now a separate one-time setup block. The release block covers steps 3–8, and its variables say where their values come from.
- **Minor 2: "Notarized Developer ID" had no Apple source.** Step 8's comment and the sidecar row now label it as expected from the task brief only.
- **Minor 3: the probe's spec grep lacked `ArchitectureSetting`.**
  - `archs-probe/run.sh` now greps `-e ArchitectureSetting`.
  - Only the grep step was re-run. The last section of `runs.txt` was replaced and labelled as a re-run, and it shows `ArchitectureSetting = "ARCHS_STANDARD"` at xcspec line 23.
  - The build results are unchanged.
- **Minor 4: the ARCHS table did not say what was built.** It now says the measurement used a minimal SwiftPM executable package built through `xcodebuild`, and that an Xcode app target was not tested.
- **Minor 5: the Vale run was not recorded.** It is now in "Gates and prose checks".
- **Verification:** both gates passed (Swift 1/1, native 0/0, exit 0). Vale on direct-distribution.md showed 0 errors and 4 warnings. `bun test` 542/0, audit 0 errors and 54 warnings, and `claude plugin validate . --strict` passed.

## Closed without R6 (P44)

The user decided to skip real notarization for this release. Neither team offers a Developer ID Application certificate in Xcode:
- team `2F7J72JV48`, under Apple ID 1;
- team `ULQJ329QSN`, under Apple ID 2.

Most likely neither is a paid membership on which the user holds the Account Holder role. Nothing was signed with Developer ID or submitted.

**Identity facts** (`identity.log`):
- The machine has two `Apple Development` identities and no Developer ID identity.
- The certificate subjects are as follows:

| Identity name suffix | Subject OU (Team ID) | Subject O (team name) | Apple ID |
|---|---|---|---|
| G4MYV6D63X | 2F7J72JV48 | Michael Fulton Jr. | Apple ID 1 |
| RTC3TK2XFJ | ULQJ329QSN | Michael Fulton | Apple ID 2 |

**The store-credentials result.** This comes from the user's report, not from a log of the user's terminal. The user ran `notarytool store-credentials` with Apple ID 1 and team `ULQJ329QSN`, and it returned:

"Error: HTTP status code: 403. Invalid or inaccessible developer team ID for the provided Apple ID. Ensure the Team ID is correct and that you are a member of that team."

The cause was a mismatch: `ULQJ329QSN` is the team of Apple ID 2's certificate.

**Reference changes at close** (`e350ac8`):
- Every "R6 pending: not yet runtime-checked" marker now reads "not runtime-checked: needs a Developer ID identity (deferred item 24)". That covers the opening status, the release-sequence status, the step 6 comment on the JSON keys, and the step 8 comment on "Notarized Developer ID".
- The release-sequence intro no longer says R6 runs the block.
- What was checked on this machine stays stated as checked: the help-text spellings, `bundle.sh`, the ad hoc signature, the `spctl` rejection, the packaging and ARCHS logs, and the Swift smoke test.
- The Developer ID identities section gains three points:
  - Do not take the Team ID from an identity name. It gives the measured contrast and the `security find-certificate -p` and `openssl x509 -noout -subject` commands.
  - When the team cannot create Developer ID, Manage Certificates offers only "Apple Development". That happens on a free team, or when the user is not the Account Holder. The cause is sourced to the role rule on the account help page. The menu behaviour is labelled as the user's observation.
- The step 2 comment now says the Team ID is the certificate's subject OU, and that it must match step 1's team.
- Classic pitfalls gain three entries: the 403 from a mismatched Apple ID and Team ID, taking the Team ID from the identity name, and expecting Developer ID without the Account Holder role.
- The sidecar markers are reworded, and five rows were added for the new claims.
- The fixture README and `bundle.sh` each note that R6 was skipped (item 24).

**Deferred item 24** (`docs/deferred.md`) records:
- that R6 was skipped, and why;
- what stays unverified: the `id` and `status` keys of `notarytool submit -f json`, the "Notarized Developer ID" source string, the stapled `spctl` acceptance, and whether the notary service accepts the `ditto` zip with its AppleDouble entries;
- the trigger: the user has a Developer ID Application identity. Then the release block runs per the Task 10 brief's R6 sequence, including the team-confirmation stop.

**Verification at close:**
- `typecheck_snippets.py`: exit 0, 1/1.
- `typecheck_native.py`: exit 0, 0/0.
- Vale: direct-distribution.md 0 errors and 4 warnings (unchanged). deferred.md 89 warnings, unchanged from before item 24.
- `bun test --timeout 30000`: 542 pass, 0 fail.
- `bun run audit`: 0 errors, 54 warnings.
- `claude plugin validate . --strict`: passed.
- No file in this record contains either email address or the subject UIDs. (Corrected in Task 13, ruling P51. This line first said "No committed file", which was false while the spec's line 406 held one of the addresses. That line is now redacted. Evidence: `task-13-release/email-scan.log`.)
