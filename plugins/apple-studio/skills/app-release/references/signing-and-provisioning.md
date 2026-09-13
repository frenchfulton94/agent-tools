> verified: 2026-08 against https://developer.apple.com/documentation/xcode/changing-the-bundle-identifier.md, https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices.md, https://developer.apple.com/documentation/xcode/using-the-latest-code-signature-format.md, https://developer.apple.com/documentation/xcode/sharing-your-teams-signing-certificates.md, https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles.md, https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api.md, https://developer.apple.com/support/compare-memberships/
> sources: iOS App Distribution and Best Practises v1.0.0 (judgment only), live Apple docs

# Code Signing and Provisioning

## The mental model

iOS's App Sandbox denies every app access to hardware, other apps' data, and most of the file system by default; an app has to prove who it is and what it wants before the runtime policy system grants an exception (iOS App Distribution and Best Practises, ch. 4). A *code-signed provisioning profile* is the artifact that answers the sandbox's four implicit questions — who are you, what do you want to do, can I trust you, where can you run — by binding an App ID, an entitlements list, a certificate, and (for non-App-Store builds) a device list into one CMS-signed package (TN3125: Inside Code Signing: Provisioning Profiles, https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles.md). Treat every signing error as a failure to satisfy one of those four questions, not as an opaque Xcode tantrum — it collapses most "random" signing failures into a short diagnostic checklist.

The profile's plist is a convenience view; the actual source of truth the OS checks is the `DER-Encoded-Profile` payload inside the CMS signature, which stores certificate identity as SHA-256 hashes rather than full certificates (TN3125). Don't hand-edit or hand-inspect `.mobileprovision` files as if the plist were authoritative — use `security cms -D` / `plutil -extract` to dump it when you need ground truth.

## Certificates vs App Store Connect API keys

These solve two different trust problems and are not interchangeable:

- **A signing certificate + private key (Keychain-resident, X.509)** identifies *the machine and person producing a code-signed binary*. It's what `codesign` uses to actually seal an app; without the private key in a keychain, no amount of API access lets you produce a valid signature (Sharing your team's signing certificates, https://developer.apple.com/documentation/xcode/sharing-your-teams-signing-certificates.md).
- **An App Store Connect API key** identifies *a caller of the App Store Connect API* — uploading builds, managing TestFlight, querying provisioning resources, driving `notarytool`/`altool`/`xcrun` automation. It's a JWT-signing key, not a code-signing identity, and it never touches `codesign` (Creating API keys for App Store Connect API, https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api.md).

Decision rule: use a **certificate** for anything that produces a signature (local Xcode builds, `xcodebuild archive`, notarization of the binary itself). Use an **API key** for anything that talks to App Store Connect as a service call — CI upload steps, provisioning-profile automation (Fastlane `match`/`pilot`-style tooling), TestFlight management, App Store metadata. A CI pipeline typically needs *both*: a certificate/profile pair to sign the build, and a Team API key to upload it — don't try to make one substitute for the other.

Within API keys, prefer a **Team key** for CI/automation: it's scoped by role rather than by a person's account, survives an individual leaving the team, and (unlike an Individual key) can hit provisioning endpoints, Sales/Finance access, and `notarytool` (Creating API keys for App Store Connect API). Individual keys inherit the creating user's own permissions and are meant for a developer's personal scripts, not shared pipelines. API key private keys download exactly once and Apple keeps no copy — store the `.p8` in a secrets manager immediately, never in a repo (Creating API keys for App Store Connect API).

## Automatic vs manual signing

Automatic signing is the correct default: Xcode creates and renews certificates, registers devices, and regenerates provisioning profiles behind the scenes whenever "Automatically manage signing" is checked. Reach for **manual signing** only when one of these genuinely applies — not by default "for control":

- **CI reproducibility.** A CI runner has no interactive Apple ID session and no `user interaction is not allowed` fallback (see failures below). Manual signing with a pinned certificate + profile pair (imported into an ephemeral keychain) makes builds deterministic and independent of Xcode's on-the-fly account sync.
- **Multiple targets/extensions with divergent entitlements.** Share extensions, widgets, watch companions, and app clips each need their own App ID and profile. Automatic signing handles this fine at small scale, but once entitlements diverge per-target (e.g., only one extension needs App Groups) manual profiles make the entitlement surface auditable instead of implicit.
- **Entitlements requiring Apple approval or exact profile control** — enterprise distribution, custom push topics, or entitlements not exposed as a Capabilities checkbox at all (there are more raw entitlements than there are Capabilities toggles in Xcode).
- **Team certificate-sharing constraints.** If your team restricts who can create/revoke distribution certificates (common in larger orgs), automatic signing's "just make one" behavior can silently multiply certificates. Manual signing forces explicit reuse of one team-issued distribution identity.

If none of these apply, manual signing is pure maintenance burden: it makes you the renewal cron job Xcode would otherwise be.

## Provisioning profiles

A profile binds exactly four things, and every profile type constrains a different subset of the "where" and "who can install" axes (TN3125):

| Type | Certificate | Devices | Distributed via |
|---|---|---|---|
| Development | Development cert | Explicit UDID list, required | Xcode → device, TestFlight-free |
| Ad Hoc | Distribution cert | Explicit UDID list, required (≤ device quota) | Manual `.ipa` install / MDM, outside App Store |
| App Store | Distribution cert | None — omitted entirely | App Store Connect; Apple re-signs at distribution and the shipped binary carries **no embedded profile** |

(Distributing your app to registered devices, https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices.md; TN3125)

A profile becomes invalid the instant any bound piece changes: the certificate expires or is revoked, the App ID's capabilities change, or (for Ad Hoc/Development) a bound device is disabled. Regenerating the profile is not optional cleanup — it's required before the next build will sign (iOS App Distribution and Best Practises, ch. 4). Under automatic signing Xcode does this silently on next build; under manual signing you must re-download and re-select it yourself.

Changing an app's bundle identifier does not just relabel the app — it invalidates every provisioning profile built against the old App ID, and if any build under the old bundle ID was already uploaded to App Store Connect, you cannot retarget that App Store Connect app record to a new bundle ID at all; you must create a new app record (Changing the bundle identifier, https://developer.apple.com/documentation/xcode/changing-the-bundle-identifier.md). Treat bundle ID as fixed at first upload, not a late-stage rename. If you use manual provisioning and change the bundle ID, you must separately edit the App ID inside your existing provisioning profiles (or generate new ones) to match — toggling on automatic signing is the only path where Xcode reconciles this for you (Changing the bundle identifier).

### Device registration (Development and Ad Hoc profiles)

Development and Ad Hoc profiles both require an explicit, capped device list — this is the "where can you run" axis, and it's the one axis App Store profiles skip entirely (Distributing your app to registered devices, https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices.md). Each Apple Developer Program membership has a yearly device quota per product family; disabling a device still counts it against quota until the account's renewal date, so "removing" a device from a profile doesn't free up a slot mid-year. Under automatic signing, Xcode registers a connected device the moment you build to it and folds it into the profile automatically. Under manual signing, you own both steps: register the device's UDID in the developer account (bulk upload via a device-ID file, or one at a time), then regenerate and re-download the profile — a device present in your account but absent from the *profile itself* still can't install the build.

## Entitlements

An entitlement is a reverse-DNS key/value pair (Boolean, string, or array) embedded in the code signature that declares a capability the app intends to use — `com.apple.developer.team-identifier`, `keychain-access-groups`, `application-identifier`, and so on (iOS App Distribution and Best Practises, ch. 4; TN3125). Xcode's Signing & Capabilities tab is a curated UI over a much larger entitlement surface — not every entitlement has a Capabilities checkbox, and some (custom push topics, certain enterprise/MDM entitlements) require direct Apple approval outside Xcode entirely.

The relationship to enforce mentally: the provisioning profile's `Entitlements` dictionary is an **allowlist**, not a mirror. Every entitlement your app's code signature claims must appear in the profile, but the profile can carry entitlements the app doesn't use — that's not an error (TN3125). Wildcard entries (`TEAMID.*`) are legal inside a profile's allowlist but never legal inside the app's own claimed entitlements, which must be fully explicit. When you add a capability in Xcode, Xcode updates the App ID's entitlements in your developer account *and* regenerates the local profile to match (under automatic signing) — under manual signing, both steps are on you, and skipping the App ID update while only editing the local `.entitlements` file is the single most common self-inflicted "profile doesn't support X" error.

Two separate files/settings both claim to represent "the app's entitlements," and conflating them causes real confusion: the target's `.entitlements` plist (referenced by the `CODE_SIGN_ENTITLEMENTS` build setting) is what you and Xcode edit; what actually ships is whatever `codesign` embeds in the binary at archive time, DER-encoded. If a build behaves as though a capability isn't present despite the `.entitlements` file looking correct, check that `CODE_SIGN_ENTITLEMENTS` for the active build configuration actually points at that file — per-configuration or per-target entitlements-file overrides are a common source of "it works in one scheme but not the other."

Inspect what actually got embedded in a *built* app, not just what's in the project, with:

```
codesign --display --entitlements - --xml /path/to/MyApp.app
```

Compare that output against the profile's own `Entitlements` dictionary (`plutil -extract Entitlements xml1 -o - Profile-payload.plist`) when troubleshooting an allowlist mismatch — a diff between the two is definitive; guessing from the Capabilities tab is not (TN3125).

## Classic signing failures

Diagnose these by asking which of the four bound pieces (cert, App ID/entitlements, devices, or the keychain holding the private key) is actually broken — the error text usually names it if you read past the first clause.

### Local machine / keychain failures

- **`No signing certificate "iOS Distribution" found`** (or "Apple Development") — Xcode can't find a valid cert+private-key pair matching the selected profile in any unlocked keychain. Fix: `security find-identity -v -p codesigning` to confirm what's actually present; re-download the certificate or re-import the `.p12`, making sure the private key came with it (a certificate without its private key is useless for signing — TN3125 / Sharing your team's signing certificates).
- **`errSecInternalComponent`** from `codesign` — almost always one of three causes: a locked/inaccessible keychain, an untrusted or expired signing certificate (check Keychain Access for a green "This certificate is valid" badge — an expired intermediate, such as an old WWDR Authority cert, is a common culprit), or missing partition-list access for the private key. Fix in order: `security unlock-keychain`, confirm the identity isn't expired/untrusted, then grant partition-list access (see the CI keychain setup below) (Apple Developer Forums, multiple corroborating threads on `errSecInternalComponent`).
- **Profile/certificate mismatch, e.g. `"MyApp" requires a provisioning profile with the com.apple.developer.X entitlement`, or "doesn't match the entitlements"** — the selected profile's allowlist doesn't cover an entitlement the target now claims (usually after adding a capability in Xcode without regenerating the profile). Fix: regenerate/re-download the profile after any capability change, or let automatic signing do it.
- **Expired or revoked certificate blocking archive** — profiles referencing a revoked/expired cert are simultaneously invalid; Xcode reports it against the profile, not the cert, which misleads people into re-downloading the profile instead of renewing the certificate. Fix: check `security find-identity -v -p codesigning` for a `0 valid identities found` count before touching profiles at all.

### CI / headless keychain failures

- **`User interaction is not allowed`** — `codesign`/`security` tried to unlock a keychain or prompt for keychain-item access and there's no interactive session (SSH/CI runner). This is the signature CI-specific failure. Fix: create a dedicated CI keychain, unlock it non-interactively, and set its default/search-list explicitly:
  ```
  security create-keychain -p "$KEYCHAIN_PW" build.keychain
  security unlock-keychain -p "$KEYCHAIN_PW" build.keychain
  security set-keychain-settings -lut 21600 build.keychain
  security list-keychains -d user -s build.keychain login.keychain
  security import cert.p12 -k build.keychain -P "$P12_PW" -T /usr/bin/codesign
  security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KEYCHAIN_PW" build.keychain
  ```
  The `set-key-partition-list` step is the one people forget — without it, macOS still prompts for keychain access even in a "correctly" unlocked keychain, and headless `codesign` fails with the same `User interaction is not allowed` error. These partition IDs (`apple-tool:`, `apple:`, `codesign:`) are undocumented by Apple directly, but corroborated as stable across macOS releases (not a per-OS-version moving target) across many Apple Developer Forums threads on `set-key-partition-list`.
- **`xcodebuild: error: exportArchive ... No profiles for 'com.x.y' were found`** on a fresh CI runner — automatic signing has nothing to fetch from (no signed-in Apple ID session, or an API-key-authenticated session that Xcode can't use for automatic signing the same way). Fix: switch CI to manual signing with a profile fetched via API-key-authenticated `xcodebuild -allowProvisioningUpdates` or pre-fetched and committed to a secrets store, not "sign in interactively once."
- **Keychain not found / wrong keychain search order** — CI images sometimes have a stale `login.keychain` or none at all; `codesign` silently checks the wrong keychain in the search list and reports "No signing certificate found" even though the cert was imported. Fix: always set `security list-keychains` explicitly in CI rather than relying on the default search path.
- **Certificate imported but still not found by codesign** — importing a `.p12` without `-T /usr/bin/codesign` restricts which tools may use the key without a prompt; on a headless runner that prompt never resolves. Fix: always pass `-T /usr/bin/codesign` (and `-T /usr/bin/security` if other tooling needs it) at import time.

## Free (personal team) vs paid Developer Program signing

A free Apple ID signed into Xcode gets a "Personal Team" that can create Development certificates and Development profiles for on-device debugging only. The limits are real and specific: registered App IDs are capped at 10 and expire after 7 days, registered test devices are capped at 3 per platform and expire after 7 days, and provisioning profiles themselves expire 7 days from issuance — expect to rebuild and reinstall periodically, not just once (Choosing a Membership, https://developer.apple.com/support/compare-memberships/). What a personal team categorically cannot do: create a Distribution certificate, create an Ad Hoc or App Store profile, or upload a build to App Store Connect — those all require a paid Apple Developer Program membership. When helping a developer who's currently on a free/personal team, don't propose Ad Hoc or App Store signing steps as something to attempt today; the correct guidance is that the mechanics below are the same shape once they enroll, not a different system to learn later.

## The paid team distribution path

This is the real, complete path for shipping to the App Store under a paid Apple Developer Program membership — write and reason about it in full even when only a free-tier account is available to test against, since the free tier limits what you can *verify locally*, not what a developer will actually need to do.

1. **Distribution certificate.** Generate a CSR in Keychain Access (or via `openssl`/CI tooling), submit it under *Apple Distribution* in Certificates, Identifiers & Profiles, download and install the signed cert + private key. One distribution certificate can back both App Store and Ad Hoc profiles — you don't need a separate cert per distribution channel (iOS App Distribution and Best Practises, ch. 4).
2. **App Store distribution profile.** Created against a specific App ID and the distribution certificate, with no device list — this is the only profile type that omits `ProvisionedDevices` entirely, because App Store builds don't run directly on a device from that profile; Apple strips the profile and re-signs at distribution time (TN3125).
3. **Team certificate sharing.** A distribution certificate's private key is the org's signing identity, not a personal credential — anyone holding the exported `.p12` and its password can ship software that appears to come from the team's Apple Developer account, so Apple explicitly recommends splitting the identity and its password across separate channels when handing it off (Sharing your team's signing certificates, https://developer.apple.com/documentation/xcode/sharing-your-teams-signing-certificates.md). Cloud-managed certificates (the kind automatic signing creates) sync across a team automatically through Xcode's own account sync and don't need manual export; only manually-created identities need the export/import dance. If a teammate needs a certificate they don't have the private key for, the fix is *recovery from an existing holder* (export/import), never "just generate a new certificate" — that multiplies live signing identities for no reason and complicates later revocation.
4. **Archive, distribute, upload.** With manual signing selected on the Release configuration, `Product ▸ Archive` produces an archive Xcode signs with the chosen distribution certificate + profile; `Distribute App` (or `xcodebuild -exportArchive` / `altool`/`notarytool` equivalents in CI, authenticated with a Team API key) uploads the `.ipa` to App Store Connect.
5. **Renewal discipline.** Distribution certificates expire ~1 year from issuance; every profile referencing an expired certificate goes invalid simultaneously. Track certificate expiry independently of profile expiry — a profile can look "not yet expired" while its bound certificate already is, and the resulting error surfaces against the profile, not the cert.

Four build settings govern all of the above once manual signing is on, and are the first four things to check when something doesn't sign: **Code Signing Identity** (which certificate), **Code Signing Style** (Automatic/Manual, settable per build configuration), **Development Team** (must match the team baked into both the certificate and the profile), **Provisioning Profile** (which profile gets embedded) (iOS App Distribution and Best Practises, ch. 4).

## Code signature format currency

iOS/iPadOS/tvOS 15+ and watchOS 8+ require the newer DER-encoded entitlements format in the code signature; apps signed with the older format simply fail to launch on these OS versions, with no App Store-side warning if you sideload/Ad-Hoc distribute an old-format build (Using the latest code signature format, https://developer.apple.com/documentation/xcode/using-the-latest-code-signature-format.md). Building with a current Xcode on macOS 11+ produces this format by default — this is only a live concern for Ad Hoc/Enterprise binaries built on old toolchains, since App Store/TestFlight builds get re-signed by Apple with the current format regardless of what was uploaded. Diagnose a "won't launch after install, no crash log" report by checking `codesign -dv` for `CodeDirectory v=20500` or higher and confirming DER entitlements are present (a nonzero `-7` hash entry) before assuming the bug is anywhere in app code.
