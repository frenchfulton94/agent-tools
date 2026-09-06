# Signing and attestations

Contents:
- [What signing proves](#what-signing-proves)
- [Keyless signing](#keyless-signing)
- [Verification](#verification)
- [Key-based signing](#key-based-signing)
- [Signing in GitHub Actions](#signing-in-github-actions)
- [Attesting an SBOM](#attesting-an-sbom)
- [Enforcing at admission](#enforcing-at-admission)
- [SLSA levels](#slsa-levels)
- [Failure modes](#failure-modes)

## What signing proves

A signature binds an image digest to an identity. It proves the image came from the pipeline it claims to, and that nothing changed after the signature was made. It says nothing about whether the image is free of vulnerabilities or whether the code inside is any good — those are what scanning and review are for.

Three layers, often confused:

| Layer | Produced by | Signed? |
|---|---|---|
| SBOM attestation | `docker buildx build --sbom=true` | No |
| Provenance attestation | `docker buildx build --provenance=mode=max` | No |
| Signature | `cosign sign` | Yes |

BuildKit attestations are metadata attached to the image, not cryptographic claims. Anyone with registry push access can attach a fabricated SBOM. Signing with cosign is what makes any of it trustworthy, which is why the two are complementary rather than redundant.

## Keyless signing

Sigstore keyless signing requests a short-lived certificate bound to an OIDC identity, signs, records the signature in the Rekor transparency log, and discards the key. Nothing to store, nothing to rotate, nothing to leak.

```bash
cosign sign --yes myorg/app@sha256:<digest>
```

In CI the OIDC token comes from the platform and requires no interaction. Locally it opens a browser for Google, GitHub, or Microsoft sign-in.

**Sign the digest, never the tag.** A tag is a mutable pointer. `cosign sign myorg/app:1.4.2` resolves the tag at that moment and signs the digest it found — but nothing stops the tag being repointed at a different image afterward, leaving a valid signature next to an unsigned image under the name people deploy.

Capture the digest at build time:

```bash
digest=$(docker buildx build -t myorg/app:1.4.2 --push \
  --metadata-file meta.json . && jq -r '."containerimage.digest"' meta.json)
cosign sign --yes "myorg/app@${digest}"
```

Build and sign in the same job. A digest that travels between jobs can be substituted in transit.

## Verification

```bash
cosign verify myorg/app@sha256:<digest> \
  --certificate-identity-regexp "^https://github.com/myorg/myapp/\.github/workflows/release\.yml@refs/heads/main$" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

Both identity flags are required for the check to mean anything. Without them, or with a wildcard, verification confirms only that the image was signed by *someone with a Sigstore identity* — which includes any attacker who can run cosign. This is the most common way signing is adopted while providing no protection.

Scope the regexp as narrowly as the workflow allows: the specific repository, the specific workflow file, and the specific ref. `^https://github.com/myorg/.*` lets any workflow in the organization sign anything.

Issuer URLs: GitHub Actions `https://token.actions.githubusercontent.com`; GitLab `https://gitlab.com`; Google `https://accounts.google.com`.

## Key-based signing

Where keyless is not workable — air-gapped environments, or a policy requiring a long-lived key:

```bash
cosign generate-key-pair                  # or cosign generate-key-pair --kms awskms:///alias/signing
cosign sign --key cosign.key myorg/app@sha256:<digest>
cosign verify --key cosign.pub myorg/app@sha256:<digest>
```

Prefer a KMS-backed key (`awskms://`, `gcpkms://`, `azurekms://`, `hashivault://`) over a file. A key file in CI secrets is a long-lived credential with none of the revocation properties keyless provides.

## Signing in GitHub Actions

```yaml
permissions:
  contents: read
  packages: write
  id-token: write          # required for keyless — without it, signing fails

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - id: build
        uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          sbom: true
          provenance: mode=max

      - uses: sigstore/cosign-installer@v3
      - run: cosign sign --yes ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
```

`id-token: write` is the line most often missing. Without it the OIDC token is unavailable and cosign fails with an unhelpful message about being unable to fetch a certificate.

`docker/build-push-action` exposes the pushed digest as `steps.<id>.outputs.digest`, which is the correct thing to sign.

## Attesting an SBOM

To sign an SBOM rather than merely attach it:

```bash
syft myorg/app@sha256:<digest> -o spdx-json > sbom.json
cosign attest --yes --type spdxjson --predicate sbom.json myorg/app@sha256:<digest>
cosign verify-attestation --type spdxjson myorg/app@sha256:<digest> \
  --certificate-identity-regexp "^https://github.com/myorg/.*" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

This is the answer to the BuildKit attestation gap: the SBOM is now cryptographically bound to both the image and the identity that produced it.

`cosign attest` takes any JSON predicate, so it also carries custom claims — test results, approvals, scan reports — as verifiable attestations.

## Enforcing at admission

Signing without verification at deploy time changes nothing. The check belongs where images enter the cluster.

Kyverno:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  rules:
    - name: verify-signature
      match:
        any:
          - resources:
              kinds: [Pod]
      verifyImages:
        - imageReferences: ["ghcr.io/myorg/*"]
          attestors:
            - entries:
                - keyless:
                    issuer: https://token.actions.githubusercontent.com
                    subject: "https://github.com/myorg/myapp/.github/workflows/release.yml@refs/heads/main"
```

The Sigstore policy controller is the alternative. Either way, roll out in audit mode first — `validationFailureAction: Audit` — and read what would have been blocked before enforcing. Turning enforcement on cold reliably blocks something operationally important on day one.

Kyverno also mutates image references to digests on admission, which closes the gap where a verified tag is repointed after the check.

## SLSA levels

SLSA describes build integrity, not image contents:

| Level | Requires |
|---|---|
| 1 | Provenance exists |
| 2 | Provenance is generated by a hosted build service and signed |
| 3 | The build runs in an isolated, non-falsifiable environment |

`--provenance=mode=max` on a hosted CI runner covers Level 1 and much of Level 2. Signing that provenance closes Level 2. Level 3 requires build isolation guarantees the platform must provide — the SLSA GitHub generator, or an equivalent.

Claim a level only against the requirements, not by feature count. "We produce signed provenance from GitHub Actions" is accurate and useful; "we are SLSA 3" usually is not.

## Failure modes

- **Verification with no identity flags.** Passes for any signed image, including an attacker's. Always set both `--certificate-identity-regexp` and `--certificate-oidc-issuer`.
- **Signing the tag.** Leaves the signature attached to a digest the tag no longer points at.
- **`id-token: write` missing.** Keyless signing fails in CI with a certificate-fetch error that does not name the cause.
- **Signing in a later job than the build.** Creates a window where the digest can be substituted.
- **Attestations lost on `--load`.** The default image store drops them; the build reports success regardless. Use `--push` with the `docker-container` driver, or enable the containerd image store.
- **Deploying by tag after verifying a digest.** The verification and the deployment then refer to different things. Deploy by digest, or use an admission controller that resolves and pins.
- **Enforcement without a break-glass path.** Have a documented way to deploy during a Sigstore or registry outage, decided before it is needed rather than during an incident.
