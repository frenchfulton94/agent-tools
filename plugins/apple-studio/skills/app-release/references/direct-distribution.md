> verified: 2026-10 against https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution.md, https://developer.apple.com/documentation/security/customizing-the-notarization-workflow.md, https://developer.apple.com/documentation/security/resolving-common-notarization-issues.md, https://developer.apple.com/documentation/security/hardened-runtime.md, https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.allow-jit.md, https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.allow-unsigned-executable-memory.md, https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles.md, https://developer.apple.com/documentation/xcode/creating-distribution-signed-code-for-the-mac.md, https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution.md, https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases.md, https://developer.apple.com/documentation/xcode/preparing-your-app-for-distribution.md, https://developer.apple.com/documentation/xcode/sharing-your-teams-signing-certificates.md, https://developer.apple.com/documentation/xcode/signing-a-daemon-with-a-restricted-entitlement.md, https://developer.apple.com/documentation/xcode/configuring-command-line-tools-settings.md, https://developer.apple.com/documentation/xcode/installing-the-command-line-tools.md, https://developer.apple.com/documentation/xcode/build-settings-reference.md, https://developer.apple.com/documentation/xcode/locating-a-missing-debug-symbol-file.md, https://developer.apple.com/documentation/xcode/acquiring-operating-system-symbol-information.md, https://developer.apple.com/documentation/xcode/resetting-access-to-protected-resources-in-macos.md, https://developer.apple.com/documentation/apple-silicon/porting-just-in-time-compilers-to-apple-silicon.md, https://developer.apple.com/documentation/technologyoverviews/games-technologies.md, https://developer.apple.com/help/account/reference/supported-capabilities-macos, https://developer.apple.com/help/account/certificates/create-developer-id-certificates, https://developer.apple.com/help/account/certificates/certificates-overview, https://developer.apple.com/help/account/certificates/cloud-managed-certificates
> typecheck: macos 26.0

# Direct Distribution: Developer ID, Notarization, and Gatekeeper

Scope: shipping a Mac app or game outside the Mac App Store. That starts with
the Developer ID identities, the hardened runtime, and `notarytool` and
`stapler`. Then come the zip, DMG, and pkg containers, and the checks
Gatekeeper runs on a player's Mac. It also covers the capabilities a Developer ID build loses, and
building for Apple silicon only. Certificates against API keys, profile types,
entitlements as an allowlist, and CI keychains are in
`signing-and-provisioning.md`. Team API keys for CI are in
`ci-release-automation.md`. The App Sandbox against the hardened runtime is in
`apple-macos/references/mac-sandbox-and-files.md`.

## Contents

- What was checked on this machine
- Developer ID identities
- The hardened runtime
- Capabilities outside the Mac App Store
- Building for Apple silicon only
- Signing by hand
- The release sequence
- notarytool details
- Choosing a container
- What Gatekeeper checks
- Notary log messages and their fixes
- After release: crash reports and symbols
- A release smoke test in code
- Classic pitfalls
- Where else to look

## What was checked on this machine

Every command spelling in this file was checked on 2026-10-18 against its
`--help` text or man page. The machine ran macOS 27.0.1 and Xcode 27.1, with
`notarytool` 1.1.3 (42). The zip, DMG, and unsigned pkg commands ran here.
So did an ad hoc signature of an app bundle, the architecture builds, and the
Swift smoke test. Those results are marked "Measured".

**The notarization steps are R6 pending: not yet runtime-checked.** This
machine had no Developer ID identity when the file was written. Nothing here
was signed with Developer ID, submitted, stapled, or accepted by Gatekeeper.

## Developer ID identities

There are two Developer ID certificate types:

| Certificate | Signs | Keychain name |
|---|---|---|
| Developer ID Application | Apps, other bundles, Mach-O binaries, command-line tools, and disk images | `Developer ID Application: <Team Name> (<Team ID>)` |
| Developer ID Installer | Installer packages (flat pkg) | `Developer ID Installer: <Team Name> (<Team ID>)` |

Apple's pages write the name as `Developer ID Application: <Team ID>`. The
account help says the keychain name holds the team name and the Team ID.
Match on the Team ID. When two names collide, sign with the identity's SHA-1
hash.

**Only the Account Holder creates a Developer ID certificate.** The account
help gives the required role as Account Holder. The one exception is a
cloud-managed certificate, which an Admin with the cloud-managed Developer ID
certificate access role can also use. A team can hold up to five Application
and five Installer certificates. Create one in Xcode (Settings > Accounts >
team > Manage Certificates > +) or in Certificates, Identifiers & Profiles
(Certificates > + > Developer ID). The notarization page says the Account
Holder must *sign* with Developer ID. Read that as "create": a teammate signs
with an identity the Account Holder exported as a `.p12`. Send the file and
its password over different channels, as `signing-and-provisioning.md`
explains.

List the identities before you sign:

```bash
security find-identity -v -p codesigning   # Developer ID Application identities
security find-identity -v                  # also lists Developer ID Installer identities
```

Apple's packaging page says the `codesigning` policy hides installer
identities, so a pkg build looks for its identity with the second form.

Expiry and revocation work differently for each artifact:

| Event | App with no profile | App with a Developer ID profile | Installer pkg |
|---|---|---|---|
| Certificate expires | Keeps installing and running, if the certificate was valid when the app was built. New builds need a new certificate | Same, but the profile is also checked at every launch | The certificates overview says a pkg with a trusted timestamp still installs. The Developer ID page says an expired-certificate pkg must be re-signed. Re-sign before expiry |
| Profile expires | Not applicable | **The app no longer launches.** Profiles made after 2017-02-22 are valid for 18 years | Not applicable |
| Certificate revoked | No new installs, and installed copies stop launching | Same | No new installs |
| Program membership lapses | Shipped builds still download and run | Same | Same |

## The hardened runtime

Notarization requires the hardened runtime on every app and command-line
executable. In Xcode, add the Hardened Runtime capability, which sets
`ENABLE_HARDENED_RUNTIME`. A manual signature passes `--options runtime`
(`-o runtime`). The runtime blocks code injection, dylib hijacking, and
process-memory tampering. Each block lifts with one Boolean exception
entitlement. All of them default to false. Write only the ones you set to
true, and leave the others out of the file.

| Exception entitlement | Build setting | When a game needs it |
|---|---|---|
| `com.apple.security.cs.allow-jit` | `RUNTIME_EXCEPTION_ALLOW_JIT` | A JIT scripting VM or emulator core. It allows write-and-execute memory only through `mmap()` with `MAP_JIT` |
| `com.apple.security.cs.allow-unsigned-executable-memory` | `RUNTIME_EXCEPTION_ALLOW_UNSIGNED_EXECUTABLE_MEMORY` | Rarely. It drops the `MAP_JIT` limits, and Apple warns it exposes the app to memory exploits. Move old DRM to `allow-jit` |
| `com.apple.security.cs.disable-library-validation` | `RUNTIME_EXCEPTION_DISABLE_LIBRARY_VALIDATION` | Loading mods, plug-ins, or drivers that another team signed |
| `com.apple.security.cs.allow-dyld-environment-variables` | `RUNTIME_EXCEPTION_ALLOW_DYLD_ENVIRONMENT_VARIABLES` | Almost never in a shipped build |
| `com.apple.security.cs.disable-executable-page-protection` | `RUNTIME_EXCEPTION_DISABLE_EXECUTABLE_PAGE_PROTECTION` | Almost never |
| `com.apple.security.cs.debugger` | `RUNTIME_EXCEPTION_DEBUGGING_TOOL` | Only for a debugger that attaches to other processes |

A JIT without `allow-jit` does not always crash. It can fall back to its
interpreter with no error, which shows up only as lost frame time. Apple
silicon enforces write-xor-execute for every app, with or without the
hardened runtime. The current pattern adds
`com.apple.security.cs.jit-write-allowlist` and writes code only inside a
callback passed to `pthread_jit_write_with_callback_np()`. The porting page,
https://developer.apple.com/documentation/apple-silicon/porting-just-in-time-compilers-to-apple-silicon.md,
has the full rules.

Resource entitlements also apply under the hardened runtime. Voice chat needs
`com.apple.security.device.audio-input` and an `NSMicrophoneUsageDescription`
purpose string. The camera needs `com.apple.security.device.camera`, and
Apple events need `com.apple.security.automation.apple-events`.

Rules for the entitlements file:

- **Entitlements go on main executables only.** Frameworks, dylibs, and
  in-process plug-ins take the host's entitlements. A plug-in host must claim
  every entitlement and purpose string its plug-ins need.
- **XML, ASCII, no BOM, no comments, LF line endings.** A binary plist makes
  the notary service report "Embedded entitlements are invalid". Check the
  file with `plutil -lint`, and convert it with `plutil -convert xml1`.
- **Strip `com.apple.security.get-task-allow`.** New macOS projects set
  `CODE_SIGN_INJECT_BASE_ENTITLEMENTS = YES`, which injects it so the debugger
  can attach. Xcode's archive and export strip it. A pipeline that signs build
  products directly sets the setting to `NO` for the distribution build only.
- **Start from what the development build claims.** Change
  `com.apple.developer.aps-environment` from `development` to `production`,
  and delete `get-task-allow`:

```bash
codesign -d --entitlements - --xml "$DEV_APP" | plutil -convert xml1 -o - -
```

The notary pages show `--entitlements :-`. Current `man codesign` documents
`--entitlements -` with `--xml` or `--der`, so use the form above.

## Capabilities outside the Mac App Store

Apple's macOS capability table has a separate column for Developer ID:
https://developer.apple.com/help/account/reference/supported-capabilities-macos.
For a game, three rows decide the architecture. **Game Center, In-App
Purchase, and Sign in with Apple are not available to a Developer ID build.**

| Developer ID | Capabilities |
|---|---|
| Not available | Game Center, In-App Purchase, Sign in with Apple, HomeKit, WeatherKit, Shared with You, Messages Collaboration, Sensitive Content Analysis, Managed App Installation UI, Low Latency HLS, HLS Interstitial Previews |
| Available | iCloud (CloudKit, iCloud documents, key-value storage), Push notifications, App groups, Keychain sharing, Associated domains, Apple Pay, Network extensions, Personal VPN, System Extension, Time Sensitive and Communication Notifications, Maps, Hardened runtime, App Sandbox, and others |

`apple-games/references/game-center-and-online.md` states the same rule, and
gives the replacements for each Game Center feature.

**A restricted entitlement needs an embedded Developer ID profile.** On macOS
a provisioning profile is optional, also for the Mac App Store, except for
TestFlight. A Mac app needs one only when it claims a restricted entitlement.
iCloud and push are restricted (`com.apple.developer.*`). The unrestricted
ones are `com.apple.security.get-task-allow`,
`com.apple.security.application-groups`, the App Sandbox entitlements, and the
hardened-runtime entitlements. A Developer ID profile has these properties:

- It carries `ProvisionsAllDevices` and no device list.
- It sits at `MyGame.app/Contents/embedded.provisionprofile`. The extension
  is `.provisionprofile` on macOS, not `.mobileprovision`.
- Gatekeeper checks it at every launch. If it expires, the app stops
  launching.
- An Xcode-archived bundle carries a *development* profile. A manual pipeline
  copies the Developer ID profile over it. Each app extension has its own
  profile.
- Copying a profile in breaks the signature seal. Sign again afterwards.

A standalone executable, such as a dedicated game server or a helper tool,
has no place for a profile. It cannot claim a restricted entitlement unless
you wrap it in an app-shaped bundle
(`X.app/Contents/{Info.plist, MacOS/X, embedded.provisionprofile}`). Apple's
daemon page gives the Xcode recipe.

**Privacy grants do not move between the two channels.** macOS keys privacy
grants (microphone, camera, and others) on the code's designated requirement.
The default designated requirements of a Mac App Store build and a Developer
ID build are incompatible. A player who has both grants microphone access
twice, unless both builds are signed with compatible custom requirements
(`codesign -r <file>`). Between test builds, reset one app with
`tccutil reset All <bundle-id>`.

## Building for Apple silicon only

Apple's games overview tells Mac game developers to target the Mac App
Store's "Apple silicon-only apps" section. It says to do that by targeting
Macs with M1 or later. Its link, https://developer.apple.com/macos/submit/,
now redirects to https://developer.apple.com/app-store/submitting/. That page
(read 2026-10-18) does not describe the section. No other page this file cites
explains how App Store Connect classifies an app as Apple silicon only.
Treat the classification as unverified, and control what you can: the
architectures in the binary.

**Measured with Xcode 27.1**, building a Release configuration for a generic
macOS destination:

| `MACOSX_DEPLOYMENT_TARGET` | `ARCHS` | Slices built |
|---|---|---|
| 26.0 | default | `x86_64 arm64` |
| 26.0 | `arm64` | `arm64` |
| 27.0 | default | `arm64` |
| 27.0 | `arm64 x86_64` | `x86_64 arm64`, with the warning "The x86_64 architecture is deprecated for your deployment target (macOS 27.0)" |

- **A 26.0 floor builds Intel by default.** Set `ARCHS = arm64` for an Apple
  silicon-only build. Xcode's macOS architecture spec still defines
  `ARCHS_STANDARD` as `arm64, x86_64`.
- **A 27.0 floor drops Intel by default.** The porting page says to add
  `x86_64` to `ARCHS` when you need Intel at that floor. The measurement
  agrees, and Xcode warns that the slice is deprecated.
- Check what shipped with `lipo -archs MyGame.app/Contents/MacOS/MyGame`.
- Xcode 27 does not run on Intel Macs. Rosetta stays general-purpose
  through macOS 27, and after that Apple keeps only a subset for older games.

## Signing by hand

There are three routes to distribution-signed Mac code:

1. **An Xcode app target.** Archive, then export with the Developer ID
   method (Organizer, or `xcodebuild archive` then `xcodebuild -exportArchive`).
2. **A non-app product built with Xcode.** Archive, copy the parts out, and
   sign them by hand.
3. **An External Build System or Aggregate target** (cargo, CMake, make).
   Xcode archives it as a "Generic Xcode Archive", which Organizer cannot
   notarize. Sign by hand and use `notarytool`.
   `apple-metal/references/cpp-and-rust.md` covers that build. An app target
   also becomes a Generic Xcode Archive when a dependency has
   `SKIP_INSTALL = NO`. Set Skip Install to Yes on every embedded target.

In Organizer, Distribute App offers the **Direct Distribution** preset, which
notarizes a Developer ID app. The Custom **Developer ID** method offers Upload
(notarize) or Export. **Copy App** exports with no signature, so it is no use
for direct distribution.

Rules for a manual signature:

- **Copy code with `ditto`, never `cp`.** `ditto` keeps the symlinks that
  framework bundles depend on.
- **Sign inside out.** Sign dependencies before what depends on them: a
  framework, then an app extension, then the app. `file <binary>` tells a
  main executable (`Mach-O … executable`) from a library.
- **Never sign with `--deep`.** `man codesign` marks it deprecated for
  signing as of macOS 13.0. It applies one set of options and entitlements to
  every nested item, and it misses code in data locations. `--deep` stays
  correct for *verifying*.
- **No entitlements on library code.** As of macOS 15.0, `codesign` does not
  embed entitlements in a library signature unless you pass
  `--force-library-entitlements`. Do not pass it: Apple says entitlements on
  a framework make the signature invalid.
- **Pass `-f` to replace a signature** and `-i <identifier>` for code that is
  not a bundle. Never run `codesign` under `sudo`, because it reads your
  user keychain.
- **Always pass `--timestamp`.** Xcode adds a secure timestamp only on
  archive and export. Without the flag, `codesign` falls back to a
  system-specific default that may timestamp only some signatures. The only
  server macOS accepts is `timestamp.apple.com`, so the signing machine needs
  the internet. `codesign -dvv <path>` prints `Timestamp=<date>` when a
  secure timestamp is present, and `Signed Time` when it is absent.

```bash
IDENTITY="Developer ID Application: <Team Name> (<Team ID>)"
codesign -s "$IDENTITY" -f --timestamp "MyGame.app/Contents/Frameworks/Engine.framework"
codesign -s "$IDENTITY" -f --timestamp -o runtime -i "com.example.mygame.server" "MyGame.app/Contents/MacOS/game-server"
codesign -s "$IDENTITY" -f --timestamp -o runtime --entitlements MyGame.entitlements "MyGame.app"
```

Before you submit, run Apple's pre-flight check. It runs the notary
service's checks locally:

```bash
codesign -vvv --deep --strict "MyGame.app"
syspolicy_check notary-submission "MyGame.app"
```

## The release sequence

These are the commands for one app, in order. R6, the Phase 10 runtime
check, runs them verbatim. Set the four variables first. The `IDENTITY`
value comes from step 2, and `SUBMISSION_ID` comes from the `id:` line that
step 6 prints.

**R6 pending: not yet runtime-checked.** Each spelling matches its `--help`
text or man page on this machine. The expected results are from Apple's
pages and from those help texts.

```bash
APP="MyGame.app"
ZIP="MyGame.zip"
PROFILE="<keychain profile name>"
IDENTITY="Developer ID Application: <Team Name> (<Team ID>)"

# 1. Once per machine: store notary credentials in the keychain.
#    Without --password, notarytool asks for the app-specific password.
xcrun notarytool store-credentials "$PROFILE" --apple-id "<Apple ID>" --team-id "<Team ID>"

# 2. Find the Developer ID Application identity and its Team ID.
security find-identity -v -p codesigning

# 3. Sign with the hardened runtime and a secure timestamp, then verify.
codesign --force --sign "$IDENTITY" --options runtime --timestamp "$APP"
codesign --verify --strict --verbose=2 "$APP"

# 4. Negative control. Signed but not notarized: expect "rejected" (exit 3).
spctl --assess -vv --type execute "$APP"

# 5. The notary service takes a zip, a DMG, or a pkg. It rejects a bare .app.
ditto -c -k --keepParent "$APP" "$ZIP"

# 6. Submit and wait, then fetch the log, also when the status is Accepted.
xcrun notarytool submit "$ZIP" --keychain-profile "$PROFILE" --wait
xcrun notarytool log "$SUBMISSION_ID" --keychain-profile "$PROFILE" notary-log.json

# 7. Staple the ticket to the app (a zip cannot be stapled), then check it.
xcrun stapler staple "$APP"
xcrun stapler validate "$APP"

# 8. Expect "accepted" with source "Notarized Developer ID".
spctl --assess -vv --type execute "$APP"
```

After step 7, zip the stapled app again if you ship a zip: the zip from step
5 holds the app without its ticket. For an app with entitlements, add
`--entitlements <file>` to step 3. For an app with nested code, sign it inside
out first, as the previous section shows.

## notarytool details

- **`altool` no longer notarizes.** It stopped working with the notary
  service on 2023-11-01. The service also refuses uploads from Xcode 13 and
  earlier. `altool` still uploads to App Store Connect.
- **Three ways to authenticate,** on `submit`, `log`, `history`, `info`, and
  `wait`:
  - a keychain profile: `--keychain-profile <name>` (`-p`);
  - an App Store Connect API key: `--key <.p8> --key-id <id> --issuer <uuid>`.
    `--issuer` is required for a Team key and must be left out for an
    Individual key;
  - an Apple ID: `--apple-id … --team-id … --password <app-specific password>`.
- **`store-credentials` on CI.** It validates the credentials before it saves
  them (`--validate` is the default). `--keychain <path>` writes to a CI
  keychain file. `--sync` puts the profile in iCloud Keychain, and it cannot
  be combined with `--keychain`.
- **`--wait` is off by default.** Without it, `submit` returns after the
  upload. `--timeout` ends only the local wait, and the service keeps
  working. Resume with `xcrun notarytool wait <id>` or `info <id>`.
  `history` lists the team's submissions.
- **`log` always writes pretty-printed JSON**, to stdout or to the optional
  output path. `-f` does not change it. Read it on every submission, also on
  `Accepted`: each issue has `severity`, `path`, and `message`, and the top
  level has `status`, `statusSummary`, and `ticketContents`.
- **The tools ship without Xcode.** The Command Line Tools package has
  `notarytool`, `stapler`, and `codesign_allocate`, but not `xcodebuild`. A
  signing-only CI image can sign and notarize an artifact built elsewhere,
  but it cannot archive or export.
- **Pin the toolchain per command** with `env DEVELOPER_DIR="<path>" xcrun
  notarytool …`. That needs no `sudo`, unlike `xcode-select --switch`.
- **Expect minutes.** Most submissions finish within 5 minutes, and 98% within
  15. Apple asks for at most 75 notarizations a day. Keep non-executable files
  out of `Contents/MacOS/`, and check a DMG with `hdiutil verify` first.
- **CI firewalls.** Uploads go to
  `notary-submissions-prod.s3-accelerate.amazonaws.com`, or to
  `notary-submissions-prod.s3.us-west-2.amazonaws.com` with
  `--no-s3-acceleration`. `stapler` fetches tickets from CloudKit on port 443.
  The customizing-the-workflow page lists the IP ranges.
- **Software that already shipped** needs no rebuild. Submit the DMG, pkg, or
  zip you released, then staple it. A relaxed acceptance for old software does
  not mean Gatekeeper accepts it, so read the log and test.

## Choosing a container

| Container | Signed | Stapled | Use it for |
|---|---|---|---|
| Zip | No. Files outside the code signature are open to tampering | No. Staple the app, then zip it | A quick download of one app |
| DMG | Yes, with the **Application** identity | Yes | One bundle, such as a typical game |
| Flat pkg | Yes, with the **Installer** identity (required) | Yes | Several components, fixed install locations, or install scripts |

**Sign every container that supports a signature, inside out (app, then pkg,
then DMG). Notarize only the outermost one, and staple what the player
downloads.** The service issues a ticket for every nested item. Without a
staple, Gatekeeper on an offline Mac may block the install or launch.
`stapler` writes into the file, so the file must be writable.

```bash
# Zip
ditto -c -k --keepParent "MyGame.app" "MyGame.zip"

# DMG: stage a folder, build a UDZO image, sign it with the Application identity
ditto "MyGame.app" "dmg-stage/MyGame.app"
diskutil image create from --format UDZO --volumeName "MyGame" dmg-stage "MyGame.dmg"
codesign -s "Developer ID Application: <Team Name> (<Team ID>)" --timestamp -i "com.example.mygame.dmg" "MyGame.dmg"

# pkg: one app, installed in /Applications
productbuild --sign "Developer ID Installer: <Team Name> (<Team ID>)" --component "MyGame.app" /Applications "MyGame.pkg"
pkgutil --check-signature "MyGame.pkg"
```

- **`hdiutil create` is deprecated on macOS 27.** Measured: `hdiutil create
  -srcfolder dmg-stage -volname MyGame -format UDZO -ov MyGame.dmg` still
  writes a valid UDZO image, and prints a warning that names
  `diskutil image create from`. Apple's packaging page still shows `hdiutil`
  and spells the flag `-srcFolder`. `hdiutil create -help` spells it
  `-srcfolder`.
- **`diskutil image create from` defaults to ULFO (lzfse).** Measured. Pass
  `--format UDZO` to get the zlib image that Apple's packaging page names.
  `hdiutil verify` passes on both.
- **pkg variants.** For a component package from an `xcodebuild` destination
  root, use `pkgbuild --root <root> --identifier <id> --version <v>
  --install-location <path> --sign <identity> <out.pkg>`.
  `pkgbuild --analyze --root <root> <plist>` writes a component plist
  template. To merge several packages, run `productbuild --synthesize
  --package <a.pkg> <distribution.xml>`, then `productbuild --distribution
  <distribution.xml> --package-path <dir> --sign <identity> <out.pkg>`. To
  sign an existing package, run `productsign --sign <identity> <in.pkg>
  <out.pkg>`. `pkgbuild` timestamps by default with a Developer ID identity.
- **A signed pkg checks out** when `pkgutil --check-signature` shows "Signed
  with a trusted timestamp" and a chain that starts "1. Developer ID
  Installer:".
- **Games with large data.** Notarize only a pkg that holds the
  executables. Put the bulk data in a folder beside it, put both in a DMG
  that you do not notarize, and staple the pkg.
- **The Mac App Store takes a pkg,** signed with the Mac Installer
  Distribution identity, never a DMG or a zip.

## What Gatekeeper checks

On a player's Mac, Gatekeeper checks a quarantined download for a valid
Developer ID signature and a notarization ticket. It reads the ticket from
the staple, or online when nothing is stapled. With a ticket, the first
launch shows the dialog that says Apple checked the app. Notarization is an
automated malware and signature scan, not App Review.

| Check | Command | Result |
|---|---|---|
| Can this app run? | `spctl --assess -vv --type execute <app>` | Exit 0 means accepted; exit 3 means rejected. `--raw` prints a plist |
| Can this pkg install? | `spctl --assess -vv --type install <pkg>` | The same exit codes |
| Is it ready for the notary service? | `syspolicy_check notary-submission <app>` | The notary service's checks, run locally |
| Will it launch after distribution? | `syspolicy_check distribution <app>` | Gatekeeper, XProtect, and provisioning-profile checks. `--json` for scripts |
| Is a ticket available? | `codesign --verify --check-notarization <app>` | Forces an online ticket lookup |
| Is the ticket stapled? | `xcrun stapler validate <path>` | Checks the stapled ticket |

`spctl --type` takes `execute`, `install`, or `open` (documents). The
resolving page writes `--type exec`; use the man page's spelling. **As of
macOS 15.0, `spctl` no longer edits the rule database or global state,** so a
script that disables Gatekeeper with `spctl` fails. Measured: an ad hoc
signed bundle with the hardened runtime returns `rejected` and exit 3.

Test the release on a Mac other than the build machine:

- a fresh install, and an upgrade over an older version, both in place and in
  a new location;
- a second copy of the same version in another folder;
- another user account, and a guest or non-admin user;
- **a first launch without moving the app** out of the zip or DMG location.
  Gatekeeper translocates it to a random path on that launch, so
  `Bundle.main.bundleURL` changes, and paths to files beside the bundle break.
  Test the second launch and a moved copy too. Keep game data inside the
  sealed bundle or in Application Support.

## Notary log messages and their fixes

| Log message | Cause | Fix |
|---|---|---|
| The signature of the binary is invalid. | The code is unsigned, or it changed after signing | Sign inside out, last change first; never edit a bundle after signing |
| The binary is not signed with a valid Developer ID certificate. | A Mac App Distribution, Apple Development, ad hoc, or self-signed identity | Sign with Developer ID Application |
| The signature does not include a secure timestamp. | `--timestamp` missing, or the server could not be reached | Pass `--timestamp`; give the signer the internet |
| The executable requests the com.apple.security.get-task-allow entitlement. | A debug-signed build | `CODE_SIGN_INJECT_BASE_ENTITLEMENTS = NO` for distribution, or export through Xcode |
| The executable does not have the hardened runtime enabled. | `-o runtime` missing on an executable | Add it on the app and every command-line tool |
| The binary uses an SDK older than the 10.9 SDK. | An old prebuilt binary | Rebuild it |
| Embedded entitlements are invalid: syntax error near line 1 | A binary plist was embedded | `plutil -convert xml1`, then sign again |

From macOS 10.15.4, a process whose embedded entitlements cannot be parsed
aborts at launch with an AMFI error. A bad entitlements file is a launch
failure, not only a notarization failure.

## After release: crash reports and symbols

Organizer's crash reports, feedback, and metrics exist only for TestFlight and
App Store builds. A Developer ID game gets none of them, so it collects its
own crash reports.

- **Keep every shipped `.xcarchive`.** A binary and its `.dSYM` pair only by
  build UUID. Without the archive, a release cannot be symbolicated.
- Find a dSYM with `mdfind "com_apple_xcode_dsym_uuids == <UUID>"`, and
  confirm it with `dwarfdump --uuid <dSYM>`. Write the UUID from the crash
  report as 36 uppercase characters with hyphens. Spotlight must index the
  folder.
- **macOS has no OS-symbol download.** Symbolicate a player's report in Xcode
  on a Mac that runs the same macOS version as the report.

## A release smoke test in code

A distribution build must not claim `get-task-allow`. This check reads the
running build's own signature, so a test or a debug menu can assert it:

```swift
import Foundation
import Security

/// True when the running code's signature claims get-task-allow, as a
/// development build does. A Developer ID release must return false.
func signatureClaimsGetTaskAllow() -> Bool {
    var code: SecCode?
    guard SecCodeCopySelf([], &code) == errSecSuccess, let code else { return false }
    var staticCode: SecStaticCode?
    guard SecCodeCopyStaticCode(code, [], &staticCode) == errSecSuccess,
          let staticCode else { return false }
    var info: CFDictionary?
    guard SecCodeCopySigningInformation(staticCode, [], &info) == errSecSuccess,
          let signing = info as NSDictionary?,
          let entitlements = signing[kSecCodeInfoEntitlementsDict] as? [String: Any]
    else { return false }
    return entitlements["com.apple.security.get-task-allow"] as? Bool ?? false
}
```

`kSecCodeInfoEntitlementsDict` is a generic key in `SecCode.h`, so the
default flags return it. The key is absent when the code claims no
entitlements, and then the function returns false. Measured: an ad hoc build
signed with `get-task-allow` returns true, and the same build signed without
an entitlements file returns false.

## Classic pitfalls

- **Planning Game Center, In-App Purchase, or Sign in with Apple for a
  Developer ID build.** They are not available. See
  `apple-games/references/game-center-and-online.md`.
- **Submitting a bare `.app`.** Zip it with `ditto -c -k --keepParent`.
- **Stapling the zip.** You cannot staple a zip. Staple the app, then zip it
  again.
- **Stapling a standalone binary.** It gets a ticket online, but there is no
  place to staple one. Gatekeeper must reach the network to find it.
- **Signing with `--deep`.** Deprecated for signing since macOS 13.0, and it
  puts the app's entitlements on every nested item.
- **Leaving a development profile in the bundle** after a manual export, or
  copying in the Developer ID profile after signing.
- **Reading `Accepted` as clean.** The log can carry warnings that become
  errors on the next submission.
- **Assuming the Mac App Store and Developer ID builds share privacy
  grants.** They do not by default; players grant access again.
- **A Developer ID profile left to expire.** The app stops launching on every
  player's Mac.

## Where else to look

- `signing-and-provisioning.md`: certificates against API keys, profile
  types, entitlements as an allowlist, CI keychains, signature-format checks.
- `ci-release-automation.md`: Team API keys, `xcodebuild -exportArchive`, CI
  pipelines.
- `apple-macos/references/mac-sandbox-and-files.md`: the App Sandbox, which
  the Mac App Store requires and Developer ID makes optional.
- `apple-games/references/game-center-and-online.md`: what a Developer ID game
  uses in place of Game Center.
- `apple-metal/references/cpp-and-rust.md`: cargo and CMake builds behind an
  External Build System target.
- The Notary API (REST), https://developer.apple.com/documentation/notaryapi.md,
  for a pipeline that must not depend on Xcode tools.
