> verified: 2026-08 against https://developer.apple.com/documentation/xcode/getting-started-with-xcode-cloud.md, https://developer.apple.com/documentation/xcode/about-continuous-integration-and-delivery-with-xcode-cloud.md, https://developer.apple.com/documentation/xcode/setting-up-your-project-to-use-xcode-cloud.md, https://developer.apple.com/documentation/xcode/configuring-your-first-xcode-cloud-workflow.md, https://developer.apple.com/documentation/xcode/making-dependencies-available-to-xcode-cloud.md, https://developer.apple.com/documentation/xcode/configuring-xcode-cloud-for-your-team.md, https://developer.apple.com/documentation/xcode/sharing-custom-aliases-across-xcode-cloud-workflows.md, https://developer.apple.com/documentation/xcode/sharing-environment-variables-across-xcode-cloud-workflows.md, https://developer.apple.com/documentation/xcode/setting-the-next-build-number-for-xcode-cloud-builds.md, https://developer.apple.com/documentation/xcode/including-notes-for-testers-with-a-beta-release-of-your-app.md, https://developer.apple.com/documentation/xcode/developing-a-workflow-strategy-for-xcode-cloud.md, https://developer.apple.com/documentation/xcode/xcode-cloud-workflow-reference.md, https://developer.apple.com/documentation/xcode/creating-a-workflow-that-builds-your-app-for-distribution.md, https://developer.apple.com/documentation/xcode/understanding-infrastructure-validation-builds.md, https://developer.apple.com/documentation/xcode/source-code-management-setup.md, https://developer.apple.com/documentation/xcode/configuring-requirements-for-merging-a-pull-request.md, https://developer.apple.com/documentation/xcode/writing-custom-build-scripts.md, https://developer.apple.com/documentation/xcode/environment-variable-reference.md, https://developer.apple.com/documentation/xcode/distributing-your-xcode-cloud-builds-through-testflight.md, https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases.md, https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api.md, https://developer.apple.com/documentation/appstoreconnectapi/generating-tokens-for-api-requests.md, https://developer.apple.com/documentation/appstoreconnectapi/identifying-rate-limits.md, https://developer.apple.com/documentation/appstoreconnectapi/xcode-cloud-workflows-and-builds.md, `xcodebuild -help` (Xcode 27.0, local), https://github.com/actions/runner-images
> sources: iOS App Distribution and Best Practises v1.0.0 (judgment only), live Apple docs, `xcodebuild -help` (Xcode 27.0, empirical)
> note: the GitHub Actions YAML sketch is doc-derived — assembled from the `xcodebuild`/export flags documented above plus standard GitHub Actions syntax — and has not been executed in real CI. This project's free-tier Apple Developer account cannot produce a Distribution certificate, an App Store provisioning profile, or an upload-scoped API key, so no signed archive/export/upload could be run end-to-end to verify it; treat the YAML as a validated-syntax starting point, not pre-tested automation.

# CI/CD and Release Automation

## Why automate the release pipeline at all

A manual release (archive in Xcode, hand-craft App Store Connect metadata, screenshot every locale by hand, submit) works exactly until it doesn't — the moment a step is skipped under deadline pressure is the moment a bad build ships. Automating the build-to-App-Store path pays off in five durable ways, independent of which tooling you pick (iOS App Distribution and Best Practises, ch. 12):

- **Validation by testing** — an automated pipeline runs the test suite (and can run static analysis before compiling) on every release build, not just "when someone remembers to."
- **Consistency** — a script is a recipe a machine executes identically every time; it can't forget a build configuration, a provisioning profile, or accidentally ship an unfinished feature the way a distracted human can.
- **Shared, explicit knowledge** — the steps needed to build and ship the app move out of one developer's head and into a script anyone on the team can read and run, which matters most exactly when the original author is unavailable.
- **Frequent builds** — a low-friction build process means testers and users get changes sooner, and when something breaks, a small frequent diff is far easier to bisect than three months of accumulated change.
- **The on-ramp to CI** — once a build is scriptable, the natural next step is to stop running that script by hand and let a server run it on every push — this is the transition from "build automation" to "continuous integration" proper.

## Xcode Cloud: the default recommendation

Xcode Cloud is Apple's own CI/CD system, integrated directly into Xcode and App Store Connect, and it should be the starting assumption for any team shipping an app built with Xcode — not a fallback after evaluating third-party services (Getting started with Xcode Cloud, https://developer.apple.com/documentation/xcode/getting-started-with-xcode-cloud.md). It combines Git-based source control, Apple's cloud build infrastructure, and TestFlight into one system, so it can build and test your code automatically, build for the App Store, and distribute new versions to testers — all without you standing up or maintaining a build server (About continuous integration and delivery with Xcode Cloud, https://developer.apple.com/documentation/xcode/about-continuous-integration-and-delivery-with-xcode-cloud.md).

**When Xcode Cloud alone is sufficient**: for the common case — a team building an app or framework for Apple platforms, hosting on GitHub/GitHub Enterprise, Bitbucket Cloud/Server, or GitLab/self-managed GitLab, wanting build/test/archive/TestFlight automation — Xcode Cloud is not just adequate, it is the lower-effort and better-integrated choice, since it eliminates signing/environment setup that a self-managed pipeline makes you own by hand (see below). Reach for a self-managed path only when one of the specific gaps in the next section applies; don't default to GitHub Actions "because that's what web teams use."

### Setup prerequisites and the SCM connection

Xcode Cloud requires: enrollment in the Apple Developer Program, Xcode 15+, your Apple Account added in Xcode's Accounts settings, and an app record in App Store Connect (or the role/permission to create one — App Manager, Admin, or Account Holder, or Developer with the Create Apps permission) (Setting up your project to use Xcode Cloud, https://developer.apple.com/documentation/xcode/setting-up-your-project-to-use-xcode-cloud.md). Your project must use a consistent (not dynamically generated) Xcode project or workspace, shared schemes with the archive action enabled for the scheme you want Xcode Cloud to build, automatic signing, and a bundle identifier set directly in Signing & Capabilities rather than only via an `.xcconfig` override (Setting up your project to use Xcode Cloud). Xcode Cloud needs a continuous HTTPS (port 443) connection to your Git repository; the authorization flow is native to your SCM provider, and self-hosted providers (e.g., Bitbucket Server, GitHub Enterprise) need firewall allow-listing for Xcode Cloud's published IP ranges (Source code management setup, https://developer.apple.com/documentation/xcode/source-code-management-setup.md). Required SCM permissions vary by provider: administrator on Bitbucket, organization-owner (or admin, if no org) on GitHub, maintainer on GitLab (Setting up your project to use Xcode Cloud). On a team, the first project onboarded to a given SCM provider needs an admin to grant that provider-level connection once; every subsequent project on the same provider reuses it (Configuring Xcode Cloud for your team, https://developer.apple.com/documentation/xcode/configuring-xcode-cloud-for-your-team.md).

Private dependencies (Swift packages, Git submodules) need the same SCM connection extended to their host, and Xcode Cloud deliberately does **not** perform automatic Swift package resolution in CI — it resolves strictly from a committed `Package.resolved` (do not `.gitignore` it), so forcing automatic resolution via a build script produces undefined, flaky builds (Making dependencies available to Xcode Cloud, https://developer.apple.com/documentation/xcode/making-dependencies-available-to-xcode-cloud.md). CocoaPods is pre-installed in the build image; third-party tools not already present (e.g., a dependency manager beyond SwiftPM/CocoaPods) are installed via Homebrew from a `ci_post_clone.sh` script — note the build environment does not grant `sudo` (Making dependencies available to Xcode Cloud).

### Workflows: the unit of automation

A **workflow** is Xcode Cloud's configuration object, made of: general metadata, an Xcode/macOS version pin for the temporary build environment, **start conditions** (what triggers a build — branch changes, pull-request changes, tag creation, or a schedule), **actions** (build, analyze, test, archive — one workflow can chain several), and optional **post-actions** (custom notifications, TestFlight distribution) (Configuring your first Xcode Cloud workflow, https://developer.apple.com/documentation/xcode/configuring-your-first-xcode-cloud-workflow.md; Xcode Cloud workflow reference, https://developer.apple.com/documentation/xcode/xcode-cloud-workflow-reference.md). Auto-cancel is on by default per start condition, so five rapid pushes to a branch collapse into one build for the latest commit rather than queuing five (Xcode Cloud workflow reference) — leave this on unless you have a specific reason every intermediate commit must be verified independently.

Xcode Cloud clones your repo into a private, ephemeral, isolated VM per build and never persists your source (Configuring your first Xcode Cloud workflow). Build artifacts (logs, exported archive/binary/framework, test result bundles with UI-test screenshots) are retrievable for **30 days only** — for any workflow that ships to the App Store, download and archive these yourself rather than treating App Store Connect/Xcode Cloud as long-term storage (Configuring your first Xcode Cloud workflow).

A durable workflow-strategy judgment: don't try to build one workflow that does everything. Split by cadence and purpose instead — e.g., a lightweight build+unit-test workflow on every branch push, a separate longer-running comprehensive-test workflow on a schedule, and a distribution workflow gated on tag creation or a release branch (Developing a workflow strategy for Xcode Cloud, https://developer.apple.com/documentation/xcode/developing-a-workflow-strategy-for-xcode-cloud.md). Restrict editing (Admin/App Manager only) on any workflow whose correctness gates a release, and duplicate a workflow before making risky changes to it rather than editing the production workflow in place (Developing a workflow strategy for Xcode Cloud). Use **custom aliases** to pin an Xcode/macOS version once and apply it across multiple workflows, so a version bump is a one-place edit instead of an N-workflow edit (Sharing custom aliases across Xcode Cloud workflows, https://developer.apple.com/documentation/xcode/sharing-custom-aliases-across-xcode-cloud-workflows.md); the same sharing model applies to environment variables (Sharing environment variables across Xcode Cloud workflows, https://developer.apple.com/documentation/xcode/sharing-environment-variables-across-xcode-cloud-workflows.md).

For build/test invocation mechanics inside a workflow — the underlying `xcodebuild build`/`xcodebuild test` semantics, destination strings, and result-bundle parsing — see xcode-loop's `headless-commands.md`; Xcode Cloud drives the same actions under the hood, just orchestrated for you.

### Environments and signing — the thing Xcode Cloud takes off your plate

This is the concrete reason Xcode Cloud is the default: it uses your team's **cloud-managed signing certificates**, provisions and renews them automatically, and re-signs archives at export time without you ever touching a `.p12`, a keychain, or a provisioning-profile download — the entire signing-failure class documented in `signing-and-provisioning.md` (`errSecInternalComponent`, `User interaction is not allowed`, keychain search-order problems) simply doesn't arise, because there's no headless keychain to manage. A distribution workflow should still explicitly select **Clean** builds in the Environment section (no cached derived data) — required for external TestFlight/App Store distribution builds, at the cost of longer build times (Creating a workflow that builds your app for distribution, https://developer.apple.com/documentation/xcode/creating-a-workflow-that-builds-your-app-for-distribution.md; Xcode Cloud workflow reference).

Custom (including secret) environment variables live in a workflow's Environment section and are available to custom build scripts; marking one "Keep value redacted" masks it in logs — use this for any API key or token a build script needs (Xcode Cloud workflow reference). Custom build scripts come in three fixed hook points — `ci_post_clone.sh`, `ci_pre_xcodebuild.sh`, `ci_post_xcodebuild.sh` — placed in a top-level `ci_scripts` directory next to the project, must be executable with a shebang (Xcode Cloud defaults to running non-executable/shebang-less scripts under `zsh`, which can silently break a bash-authored script), cannot `sudo`, and cannot write files that persist to later scripts or artifacts (Writing custom build scripts, https://developer.apple.com/documentation/xcode/writing-custom-build-scripts.md). Predefined environment variables like `CI_XCODEBUILD_ACTION`, `CI_PULL_REQUEST_NUMBER` (present only when a PR start condition triggered the build), and `CI_ARCHIVE_PATH` (present only during an archive action) let a script branch on what triggered it or what stage it's in; test-action scripts see every variable re-exposed with a `TEST_RUNNER_` prefix, which `xcodebuild` requires for a test runner process to see it under its original name (Environment variable reference, https://developer.apple.com/documentation/xcode/environment-variable-reference.md).

Xcode Cloud runs **infrastructure validation builds** in the background against some workflows to test its own new features against real projects — these consume build minutes and duplicate outbound calls your build scripts make to external services (a real concern if a script pings a webhook or increments an external counter), but never appear in results, never upload anywhere, and don't compromise source privacy. Opt out per-product or per-workflow in App Store Connect's Users and Access > Xcode Cloud settings if a script's side effects can't tolerate duplication (Understanding Xcode Cloud infrastructure validation builds, https://developer.apple.com/documentation/xcode/understanding-infrastructure-validation-builds.md).

### TestFlight distribution directly from CI

Set up distribution once with Set Up Distribution in Xcode's Cloud pane (creates or confirms the App Store Connect app record), then add a TestFlight post-action to a distribution workflow — internal-only, or internal+external/App-Store-eligible, per archive-action setting (Distributing your Xcode Cloud builds through TestFlight, https://developer.apple.com/documentation/xcode/distributing-your-xcode-cloud-builds-through-testflight.md; Creating a workflow that builds your app for distribution). External testing and App Store release both still route through beta app review / app review respectively — Xcode Cloud automates the build and delivery, not the review gate (Creating a workflow that builds your app for distribution). Give testers real per-build context by committing a `WhatToTest.<locale>.txt` file under a `TestFlight` folder next to the project (or generate it dynamically from `ci_post_xcodebuild.sh`, e.g. from the last few `git log` messages) — Xcode Cloud picks it up automatically and populates TestFlight's "What to test" field (Including notes for testers with a beta release of your app, https://developer.apple.com/documentation/xcode/including-notes-for-testers-with-a-beta-release-of-your-app.md).

Build numbering is automatic and monotonic per Xcode Cloud product starting at `1`, which satisfies iOS/iPadOS/tvOS/visionOS/watchOS's "unique version+build combination" rule even across a lower build number on a new version. **Mac apps are the one exception**: App Store Connect requires a Mac app's build number to strictly increase across versions too, so an existing Mac app moving to Xcode Cloud must set a custom starting build number (Admin/App Manager role required, configured in App Store Connect's Xcode Cloud Settings > Build Number tab) rather than letting Xcode Cloud restart from `1` (Setting the next build number for Xcode Cloud builds, https://developer.apple.com/documentation/xcode/setting-the-next-build-number-for-xcode-cloud-builds.md).

### PR gating and team scale

Xcode Cloud can start a build on every pull-request change and post status back to your SCM provider; GitHub and Bitbucket expose this as status checks / code insights you can mark **required** before merge is allowed — GitLab and self-managed GitLab only display status, they don't offer a merge-blocking gate (a GitLab platform limitation, not an Xcode Cloud one) (Configuring requirements for merging a pull request, https://developer.apple.com/documentation/xcode/configuring-requirements-for-merging-a-pull-request.md). You can require the whole build to pass, or just a specific action (e.g., require archive to succeed but allow merging with failing tests on a feature branch) — a real judgment call about how strict pre-merge gating should be per branch (Configuring requirements for merging a pull request).

When Xcode Cloud alone stops fitting — most commonly, a large team that needs custom dashboards over build data, integration with a non-Apple back-end CI/CD system, or programmatic creation of many workflows across many apps — the App Store Connect API exposes Xcode Cloud products, workflows, builds, artifacts, and SCM resources directly, so you can read build state and start new builds from your own tooling instead of only from Xcode/App Store Connect's UI (Xcode Cloud Workflows and Builds, https://developer.apple.com/documentation/appstoreconnectapi/xcode-cloud-workflows-and-builds.md). This is still "Xcode Cloud," just automated at the API layer — it is not the same decision as moving to a self-managed CI system.

## The self-managed path: `xcodebuild` + a generic CI runner

Reach for a non-Apple CI system only when a specific structural need exists — not as a default:

- You already run GitHub Actions (or another CI) for a backend/monorepo and want iOS builds in the same orchestration rather than a second system to babysit.
- You need Linux/cross-platform CI as part of the same pipeline (e.g., a shared Swift package that also targets Linux, or a monorepo with non-Apple services).
- Multi-repo orchestration that doesn't fit Xcode Cloud's one-product-per-workflow model — e.g., a release train that must coordinate an iOS app build against artifacts produced by unrelated repos.

Everything below is the complete mechanical path for that case, expressed as `xcodebuild` invocations any CI runner can execute — build and test steps are unchanged from ordinary local development (see xcode-loop's `headless-commands.md` for the underlying `xcodebuild build`/`test` commands); archive and export are the two steps a release pipeline adds on top.

### `xcodebuild archive` then `-exportArchive`

`xcodebuild archive -scheme <scheme> -destination 'generic/platform=iOS' -archivePath <path>.xcarchive` produces a signed `.xcarchive` — this is the CI equivalent of Xcode's Product ▸ Archive (Distributing your app for beta testing and releases, https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases.md). `-exportArchive -archivePath <path>.xcarchive -exportPath <dir> -exportOptionsPlist <plist>` then re-signs and repackages that archive per the plist's configuration — this is the CI equivalent of Organizer's Distribute App (verified against local Xcode 27.0's `xcodebuild -help`, same command family the xcode-loop reference verifies build/test against).

`ExportOptions.plist` is where every export decision lives; at the judgment level, the keys that matter are:

- **`method`** — what kind of export this is: `app-store-connect` (App Store/TestFlight; `app-store` is a deprecated alias), `release-testing` (Ad Hoc; `ad-hoc` deprecated), `enterprise`, `debugging` (`development` deprecated — the default if omitted), `developer-id`, or `validation`. This is the single most consequential key — it determines which signing identity class and provisioning profile type are even legal.
- **`signingStyle`** — `automatic` or `manual`. If the archive itself was manually signed and you export with `automatic`, Xcode will create profiles/cloud certificates as needed but will **not** register new devices or app IDs — a common source of "why didn't it just work" confusion when switching styles between archive and export.
- **`provisioningProfiles`** — manual signing only: a dict mapping each executable's bundle identifier (or in-archive path) to the exact profile name/UUID to use. This is where a multi-target app (extensions, widgets) with divergent entitlements gets explicit, auditable profile assignment instead of Xcode guessing.
- **`teamID`** — overrides the team used at export if it differs from the team used to archive.
- **`destination`** — `export` (default: write the `.ipa` to `exportPath` only) or `upload` (push straight to App Store Connect as part of the same `-exportArchive` invocation) — `upload` is what lets a CI job go straight from archive to App Store Connect in one step without a separate upload tool.
- **`testFlightInternalTestingOnly`** — when `true`, blocks the resulting build from ever being used for external TestFlight or App Store release; a sane default for pull-request and development-branch builds so a stray CI build can't accidentally go external.

(Full key list verified locally: `xcodebuild -help`, Xcode 27.0, "Available keys for -exportOptionsPlist" section — this schema is not published as a `developer.apple.com` DocC page; the canonical source is Xcode's own `-help` output, which is why it's cited here as a command rather than a URL.)

### App Store Connect API keys for non-interactive signing and upload

A CI runner has no interactive Apple ID session, so automatic-signing flows that depend on one (or on `notarytool`/`altool`-style interactive auth) don't work headlessly. The fix is a **Team API key**: generate it in App Store Connect (Users and Access ▸ Integrations ▸ App Store Connect API, Team Keys), which yields a Key ID, an Issuer ID, and a `.p8` private key file downloadable exactly once — store it in your CI secrets manager immediately, since Apple keeps no copy and re-downloading is not possible (Creating API keys for App Store Connect API, https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api.md). This is the same distinction `signing-and-provisioning.md` draws between certificates and API keys — a Team key doesn't sign the binary, it authenticates you *as a caller* of Apple's tooling and services; here that means feeding it to `xcodebuild` itself, not just to a REST client.

`xcodebuild` accepts the key directly via three flags: `-authenticationKeyPath <path-to-.p8>`, `-authenticationKeyID <key-id>`, `-authenticationKeyIssuerID <issuer-id>` — pass these alongside `-allowProvisioningUpdates` on `archive` (so xcodebuild can fetch/refresh profiles non-interactively) and on `-exportArchive` (so a `destination: upload` export can authenticate the upload) (verified locally: `xcodebuild -help`, Xcode 27.0 — flag descriptions for `-allowProvisioningUpdates`/`-authenticationKeyPath`/`-authenticationKeyID`/`-authenticationKeyIssuerID`). If you instead call the App Store Connect API directly (rather than through `xcodebuild`), the key signs a JWT you attach as a bearer token: build a JWT header (`alg: ES256`, your Key ID as `kid`), a payload (`iss` = Issuer ID for Team keys, `iat`/`exp` timestamps, `aud: appstoreconnect-v1`), sign it with the `.p8`, and send it as `Authorization: Bearer <token>` (Generating tokens for API requests, https://developer.apple.com/documentation/appstoreconnectapi/generating-tokens-for-api-requests.md). Keep token lifetime short — most endpoints reject a token lived over 20 minutes; only scoped, GET-only tokens against specific resources can live up to six months — and reuse one signed token across multiple requests within its lifetime rather than minting a fresh one per call (Generating tokens for API requests). Every API response carries an `X-Rate-Limit` header (`user-hour-lim`/`user-hour-rem` on a rolling hour); a 429 with `RATE_LIMIT_EXCEEDED` means back off and retry later, not retry immediately (Identifying rate limits, https://developer.apple.com/documentation/appstoreconnectapi/identifying-rate-limits.md).

### A minimal GitHub Actions release job

The sketch below is assembled from the documented `xcodebuild`/export flags above and standard GitHub Actions syntax — it has **not** been executed in a real CI run. This project's Apple Developer account is free-tier, which cannot produce a Distribution certificate, an App Store provisioning profile, or an App Store Connect API key with upload scope (see `signing-and-provisioning.md`'s free-vs-paid section) — so there is no way to drive a real signed archive/export/upload through actual CI from this environment to verify the job end-to-end. Treat this as a documentation-accurate starting point that a team with a paid membership must validate against their own bundle ID, scheme, and team ID before trusting it in production — not as pre-tested automation.

```yaml
name: Release Build

on:
  push:
    tags:
      - 'release/*'

jobs:
  archive-and-export:
    runs-on: macos-15
    timeout-minutes: 60
    env:
      SCHEME: MyApp
      PROJECT: MyApp.xcodeproj
      TEAM_ID: ABCDE12345
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Select Xcode version
        run: sudo xcode-select -s /Applications/Xcode_26.3.app/Contents/Developer

      - name: Install App Store Connect API key
        env:
          ASC_KEY_ID: ${{ secrets.ASC_KEY_ID }}
          ASC_KEY_P8_BASE64: ${{ secrets.ASC_KEY_P8_BASE64 }}
        run: |
          mkdir -p "$HOME/private_keys"
          echo "$ASC_KEY_P8_BASE64" | base64 --decode > "$HOME/private_keys/AuthKey_${ASC_KEY_ID}.p8"

      - name: Archive
        env:
          ASC_KEY_ID: ${{ secrets.ASC_KEY_ID }}
          ASC_ISSUER_ID: ${{ secrets.ASC_ISSUER_ID }}
        run: |
          xcodebuild archive \
            -project "$PROJECT" \
            -scheme "$SCHEME" \
            -configuration Release \
            -destination 'generic/platform=iOS' \
            -archivePath "$RUNNER_TEMP/MyApp.xcarchive" \
            -allowProvisioningUpdates \
            -authenticationKeyPath "$HOME/private_keys/AuthKey_${ASC_KEY_ID}.p8" \
            -authenticationKeyID "$ASC_KEY_ID" \
            -authenticationKeyIssuerID "$ASC_ISSUER_ID"

      - name: Write ExportOptions.plist
        run: |
          cat > "$RUNNER_TEMP/ExportOptions.plist" <<PLIST
          <?xml version="1.0" encoding="UTF-8"?>
          <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
          <plist version="1.0">
          <dict>
            <key>method</key>
            <string>app-store-connect</string>
            <key>signingStyle</key>
            <string>automatic</string>
            <key>teamID</key>
            <string>${TEAM_ID}</string>
            <key>destination</key>
            <string>upload</string>
          </dict>
          </plist>
          PLIST

      - name: Export and upload to App Store Connect
        env:
          ASC_KEY_ID: ${{ secrets.ASC_KEY_ID }}
          ASC_ISSUER_ID: ${{ secrets.ASC_ISSUER_ID }}
        run: |
          xcodebuild -exportArchive \
            -archivePath "$RUNNER_TEMP/MyApp.xcarchive" \
            -exportPath "$RUNNER_TEMP/export" \
            -exportOptionsPlist "$RUNNER_TEMP/ExportOptions.plist" \
            -allowProvisioningUpdates \
            -authenticationKeyPath "$HOME/private_keys/AuthKey_${ASC_KEY_ID}.p8" \
            -authenticationKeyID "$ASC_KEY_ID" \
            -authenticationKeyIssuerID "$ASC_ISSUER_ID"

      - name: Upload build logs as artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: export-logs
          path: ${{ runner.temp }}/export
```

Signing here is entirely secret-driven — no `.p12`, no certificate password, and no embedded provisioning profile ever touch the YAML or the repo; only the API key's `.p8` (base64-encoded in a GitHub Actions secret), Key ID, and Issuer ID do, matching the certificate-vs-API-key split in `signing-and-provisioning.md`. The `macos-15` runner and `Xcode_26.3.app` path are real, currently-valid values — GitHub's `macos-14` image is deprecated, and `macos-15` currently preinstalls both a legacy Xcode 16.0–16.4 lineup (16.4 as the image's own default) and a newer Xcode 26.0.1–26.3 lineup; `26.3` is pinned explicitly here, not the image's 16.4 default, because this repo's own baseline is Xcode 27 (see `xcode-loop`'s `headless-commands.md`) and 26.3 is the closest preinstalled major version to that baseline — pinning the older default would risk CI-only compile failures against Swift 6/modern-toolchain code that builds fine locally (`actions/runner-images` repository, https://github.com/actions/runner-images, `macos-15-Readme.md`). `MyApp`/`MyApp.xcodeproj`/`ABCDE12345` are still placeholders a team must swap for their own scheme, project, and team ID, and both the runner-image label and the Xcode version should be re-checked against that repository's current READMEs before trusting them long-term — GitHub retires macOS images and rotates default/available Xcode versions on its own schedule independent of this file, and pinning the wrong one can silently reintroduce either a stale-tooling risk or a baseline mismatch with the rest of this plugin.

### Fastlane, acknowledged and out of scope

Fastlane is a widely-used, mature toolkit (`match` for certificate/profile sync, `pilot` for TestFlight, `deliver` for App Store metadata) that many self-managed pipelines use instead of hand-rolled `xcodebuild`/API-key scripting; this file deliberately doesn't document its mechanics, per this repo's decision to treat the book's Fastlane-authoring chapters as presumptively stale tooling — consult Fastlane's own docs (https://docs.fastlane.tools/) if you choose it.

## Release-pipeline principles

**CI as single source of truth.** The point of running builds on a server rather than a laptop isn't just automation — it's that the server, not any one developer's machine, becomes the arbiter of "does this actually build and pass." A CI server pinned to specific Xcode/macOS versions removes "works on my machine" as a category of bug: if your laptop fails to build but CI succeeds, the problem is local; if CI fails, that's the real signal (iOS App Distribution and Best Practises, ch. 14). CI's build-server/job/trigger model is universal across providers: a trigger (push, PR, schedule) fires a job (a script, e.g. build+test) on a build server (iOS App Distribution and Best Practises, ch. 14).

**Provider taxonomy, mapped concretely.** The book's three-tier CI taxonomy maps directly onto the two paths in this file: **full-service** (point-and-click, guided, less customizable) = Xcode Cloud; **managed** (the provider runs the hardware, you supply the build script) = GitHub Actions (or CircleCI, Bitrise, etc.); **self-managed/manual** (you also run the build server itself) = your own Mac mini acting as a runner, e.g. via a self-hosted GitHub Actions runner or Xcode Server (iOS App Distribution and Best Practises, ch. 14). Full-service costs you customizability; self-managed costs you the ongoing burden of keeping a physical or virtual build machine patched, provisioned, and available — pick the tier by how much control you actually need, not by default.

**CD is CI plus distribution.** Continuous integration tells you whether the code is good; continuous delivery/deployment adds the jobs that get a validated build into testers' or reviewers' hands automatically — for iOS, that's signing, provisioning, and a TestFlight (or App Store) upload bolted onto an existing CI workflow, typically triggered on merge to a release branch (iOS App Distribution and Best Practises, ch. 15). A CD pipeline is only as useful as your team's visibility into its state — surface build status somewhere ambient (a Slack channel, an email digest, a physical build-status display) so a red build gets fixed immediately rather than discovered days later (iOS App Distribution and Best Practises, ch. 15).

**Environment separation for sensitive data.** Teams handling sensitive back-end data (financial, health, etc.) shouldn't test against production — the standard pattern is development/staging/production back-end environments, with the app's environment selected via build configuration and a build-setting-driven base URL (plus, if needed, a distinct bundle ID/app icon/product name per environment so a tester can't mistake a staging build for production) (iOS App Distribution and Best Practises, ch. 15). This is a judgment call proportional to risk, not a mandate for every app — a small consumer app with no sensitive back-end may reasonably run everything against one environment.

**Framework-per-team decomposition at scale.** Beyond a certain team size, a single shared codebase becomes a coordination bottleneck (merge conflicts, broken builds) even with CI in place. The durable fix is architectural, not process: split the app into a thin shell plus one framework per team (and one for genuinely shared code), resolved via a dependency manager (Swift Package Manager, CocoaPods) — each team then compiles only its own framework against stable versions of the others, which also cuts compile time (iOS App Distribution and Best Practises, ch. 15). The same decomposition extends across platforms (iOS/macOS/watchOS, even Android) for genuinely shared, typically non-Swift logic.

**The methodology this all draws from.** Much of this release-pipeline judgment (separating config from code, keeping deploys fast and reversible, treating the build as a reproducible artifact) traces back to the Twelve-Factor App methodology (https://12factor.net/) — written for web apps, only partially applicable to iOS, but worth reading directly as the underlying frame rather than re-deriving it piecemeal. The broader practice this all sits inside is DevOps: development and operations treated as one continuous discipline rather than a wall between "write the code" and "ship and run it" (iOS App Distribution and Best Practises, ch. 16).

## Release checklist

Treat a release checklist as required infrastructure, not optional rigor — the Checklist Manifesto framing applies directly: if surgical teams need a checklist to catch known failure modes under pressure, a release process with just as many small, easy-to-skip steps needs one too (iOS App Distribution and Best Practises, ch. 8). A release page that records what shipped, when, and why is worth keeping even for a team of one — it turns "when did we ship this feature" from an archaeology exercise into a lookup (iOS App Distribution and Best Practises, ch. 8). Synthesizing the book's worked example (Appendix B) into a durable, tooling-agnostic checklist for the smoke-test window between approval and release:

1. **Verify every backend dependency is actually in production** — not just working in staging. This is the single most cited "how did that ship" failure: a build that expects a new response shape from a service still on the old shape crashes on launch for every user (iOS App Distribution and Best Practises, ch. 8; Appendix B).
2. **Verify feature flags on both sides** — the back-end flags for anything this release depends on, and the app-side flags gating what should actually be visible at launch.
3. **Redeem a promo code (or otherwise obtain a real download) and smoke-test the exact shipping build** — not a dev build, not the archive before re-signing — including confirming any debug/internal menu is not reachable in the release build.
4. **Tag the release in git** (e.g. `git tag vX.Y.Z`) and push the tag, then merge the release branch back to main — this is what makes "what shipped" reconstructable from source control alone, independent of App Store Connect's own history.
5. **Notify stakeholders across every channel that actually needs to know** — internal team channels, whoever owns external comms, and TestFlight testers if the release also went to them — release completion is a communication event, not just a technical one.
