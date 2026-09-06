---
name: securing-container-supply-chain
description: Scans container images for vulnerabilities, triages CVE findings into what actually needs fixing, and produces and verifies supply-chain attestations — SBOMs, build provenance, and Sigstore signatures. Use when the user asks whether an image is safe to ship, has a scan report or CVE list to act on, needs an SBOM for a customer or compliance requirement, wants to sign images or verify signatures before deploy, or is asked about SLSA, attestations, or image provenance — including when they only say "security scan our containers", "we got flagged for a vulnerability", or "prove this image came from our pipeline".
license: MIT
---

# Securing the Container Supply Chain

Two separate jobs: knowing what is inside an image and whether any of it is exploitable, and proving where the image came from. This skill covers scanning, CVE triage, SBOMs, provenance, and signing.

For hardening how a container *runs* — capabilities, read-only filesystems, the Docker socket — use `containerizing-apps`, whose hardening reference covers it. For writing the Dockerfile itself, use `containerizing-apps` as well.

## Scan before triage, triage before fixing

A first scan of an ordinary image commonly returns dozens to hundreds of findings. Handing that list to someone as "the security work" is not useful — most of it is neither exploitable nor fixable at the application level.

```bash
docker scout quickview myapp:1.4.2    # totals, plus base image contribution
docker scout cves myapp:1.4.2         # the findings themselves
```

Read `quickview` first. It splits the count between the image and its base, and that split decides the strategy: findings concentrated in the base are fixed by changing the base, not by touching the application.

## Severity is not urgency

Sorting by CVSS and starting at the top wastes effort on unreachable code while leaving exploited-in-the-wild mediums in place. Rank on three signals together:

- **Exploitability.** `docker scout cves --epss --epss-score 0.5 myapp:1.4.2` adds EPSS, an estimated probability of exploitation in the next 30 days. A LOW with a high EPSS outranks a CRITICAL in a code path nothing reaches.
- **Fixability.** `--only-fixed` hides everything with no fixed version available. Those are real but not actionable this sprint; they belong in a tracked exception, not in today's work.
- **Reachability.** A CVE in a library the application never calls, or in a build-stage tool that never shipped, is a finding rather than a risk. Multi-stage builds eliminate whole classes of these — verify the package is actually in the final image before spending time on it.

Say which of the three drove each decision when reporting. "Deferred: no fix available upstream" and "deferred: not reachable" are different commitments with different review dates.

## The fix hierarchy

Work down this list; each step fixes more findings for less effort than the one below it.

1. **Update or change the base image.** `docker scout recommendations myapp:1.4.2` names the base updates and what each would clear. Moving `node:22-bookworm` to `node:22-bookworm-slim`, or to a distroless or hardened base, often removes most OS-level findings at once because the packages are simply absent.
2. **Update the application dependency.** Standard lockfile work, verified by rescanning.
3. **Remove the package.** Build tools that reached the runtime stage are a multi-stage build error, and deleting them fixes the finding permanently.
4. **Accept with a recorded reason.** Only after 1–3. Record the CVE, why it is not exploitable here, and a date to revisit.

Rescan after every change rather than assuming the fix landed:

```bash
docker scout compare --to myorg/myapp:1.4.2 myorg/myapp:1.4.3
```

Scanner flags, other scanners (Trivy, Grype), SARIF output, CI gating, and VEX are in `references/scanning.md`. Read it when wiring scanning into a pipeline or when Scout is unavailable.

## Attestations

An SBOM lists what an image contains; provenance records how it was built. Both attach to the image as metadata:

```bash
docker buildx build --sbom=true --provenance=mode=max -t myorg/app:1.4.2 --push .
```

`mode=max` records the full build — arguments, source, and materials — where the default `mode=min` records only the essentials. Use `max` for anything shipped externally.

Two facts about this that cost people time:

- **Attestations are silently lost with the default image store.** Building with the default `docker` driver, or with `--load`, discards them. Use the `docker-container` driver with `--push`, or enable the containerd image store. The build succeeds either way and says nothing, so verify rather than assume.
- **BuildKit attestations are not cryptographically signed.** Anyone with push access to the registry can attach a tampered SBOM. They are useful for inspection and inventory; they are not proof. Proof requires signing, below.

Read them back:

```bash
docker buildx imagetools inspect myorg/app:1.4.2 --format "{{json .SBOM.SPDX}}"
docker buildx imagetools inspect myorg/app:1.4.2 --format "{{json .Provenance.SLSA}}"
```

## Signing

Sigstore keyless signing binds an image to the CI workflow identity that built it, with no private key to store or rotate:

```bash
cosign sign --yes myorg/app@sha256:<digest>
```

Sign the **digest**, never the tag. A tag is mutable — signing `:1.4.2` signs whatever that tag pointed at during the signing call, and the tag can be repointed afterward.

Verification names the identity that is allowed to have signed:

```bash
cosign verify myorg/app@sha256:<digest> \
  --certificate-identity-regexp "^https://github.com/myorg/myapp/.github/workflows/.*" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

A verification without both identity flags, or with a wildcard identity, checks only that *somebody* signed the image. That is close to no check at all, and it is the usual way signing gets adopted without providing any protection.

CI workflow examples, key-based signing, verifying attestations, and admission-time enforcement with Kyverno or the Sigstore policy controller are in `references/signing.md`.

## Verify

Before reporting supply-chain work done, confirm each against real output:

- [ ] The image was rescanned after the fix and the count moved: `docker scout compare --to <old> <new>`
- [ ] Every remaining finding is either fixed, deferred with a recorded reason, or shown unreachable
- [ ] Attestations survived the push: `docker buildx imagetools inspect <image> --format "{{json .SBOM.SPDX}}"` returns content, not null
- [ ] The signature verifies with both `--certificate-identity-regexp` and `--certificate-oidc-issuer` set
- [ ] The deployment references the image by digest, not by tag

Report the before-and-after counts by severity rather than "vulnerabilities fixed". A number that moved from 41 to 12 with 9 deferred is a report; "hardened the image" is not.

## Gotchas

- Scanning a tag scans whatever that tag resolves to right now. Pin to a digest when a result needs to be reproducible.
- `docker scout` needs a Docker Hub login for policy evaluation and organization features; anonymous use covers local scanning only.
- A scanner reports the packages it can identify. Vendored code, statically linked binaries, and hand-copied libraries are invisible to it, so a clean scan is not an empty risk surface.
- Alpine and distroless images produce far fewer findings largely because they contain fewer packages, not because the remaining ones are safer. That is still a real reduction in attack surface — just do not read the count as a quality score.
- Provenance is on by default at `mode=min` for `docker buildx build`; SBOM is not. Omitting `--sbom=true` yields an image with provenance and no SBOM, which looks like partial success and is easy to miss.
- A base image update fixes findings only after a rebuild without cache for that layer. `--pull` on the build ensures the newer base is actually fetched.
