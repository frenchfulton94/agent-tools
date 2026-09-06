# Scanning reference

Contents:
- [Docker Scout](#docker-scout)
- [Trivy](#trivy)
- [Grype and Syft](#grype-and-syft)
- [Choosing a scanner](#choosing-a-scanner)
- [Scanning things that are not images](#scanning-things-that-are-not-images)
- [Gating CI](#gating-ci)
- [SARIF and code scanning](#sarif-and-code-scanning)
- [VEX and suppressions](#vex-and-suppressions)
- [Reading a finding](#reading-a-finding)

## Docker Scout

Bundled with Docker Desktop and installable as a CLI plugin elsewhere.

```bash
docker scout quickview myapp:1.4.2          # summary, image vs base split
docker scout cves myapp:1.4.2               # full findings
docker scout recommendations myapp:1.4.2    # base image updates and what they fix
docker scout compare --to myapp:1.4.2 myapp:1.4.3
docker scout policy myapp:1.4.2 --org myorg
```

Filters that matter for triage:

| Flag | Effect |
|---|---|
| `--only-severity critical,high` | Restrict by severity |
| `--only-fixed` | Only findings with an available fix |
| `--epss --epss-score 0.5` | Add exploit-probability scores and filter on them |
| `--only-package-type npm` | Restrict to one ecosystem |
| `--ignore-base` | Exclude findings inherited from the base image |
| `--only-vuln-packages` | Collapse to the affected packages rather than every CVE |
| `--format markdown` | Output for a PR comment or ticket |
| `--exit-code` | Non-zero exit when findings match, for CI |

Reference prefixes control where the image is resolved from — `local://` skips the registry lookup, `registry://` skips the local store, `fs://` analyzes a directory of source rather than an image, and `sbom://` reads an existing SBOM file or stdin.

```bash
docker scout cves fs://.                        # source tree, no build needed
syft -o spdx-json alpine:3.20 | docker scout cves sbom://
```

`fs://` is the fastest feedback loop during development: it finds dependency CVEs before an image exists.

## Trivy

Open source, no account, broad coverage. The usual choice when Scout is unavailable or a second opinion is wanted.

```bash
trivy image myapp:1.4.2
trivy image --severity HIGH,CRITICAL --ignore-unfixed myapp:1.4.2
trivy image --exit-code 1 --severity CRITICAL myapp:1.4.2
trivy fs .                                  # source tree
trivy config .                              # Dockerfile and Compose misconfiguration
trivy image --format cyclonedx -o sbom.json myapp:1.4.2
```

`trivy config` is the part Scout does not cover: it checks the Dockerfile and Compose files themselves against misconfiguration rules — running as root, no `USER`, `latest` tags, privileged mode — rather than checking packages. Worth running alongside a package scan.

Cache the vulnerability database in CI (`~/.cache/trivy`) or every run re-downloads it.

## Grype and Syft

Anchore's pair: Syft builds the SBOM, Grype scans it.

```bash
syft myapp:1.4.2 -o spdx-json > sbom.json
grype sbom:sbom.json
grype myapp:1.4.2 --fail-on high
```

Splitting the two is useful when the SBOM is a deliverable in its own right, or when the same SBOM should be rescanned later without rebuilding — new CVEs are published against unchanged images constantly, and rescanning a stored SBOM catches those without a registry pull.

## Choosing a scanner

| Need | Tool |
|---|---|
| Fastest path with Docker Desktop already installed | Scout |
| Base image update recommendations | Scout (`recommendations`) |
| Exploit probability in triage | Scout (`--epss`) |
| No account, fully open source | Trivy or Grype |
| Dockerfile and Compose misconfiguration | Trivy (`config`) |
| SBOM as a standalone artifact | Syft |
| IaC, filesystem, and images from one tool | Trivy |

Running two scanners produces different counts. That is expected — they use different advisory sources and different matching rules — and it is not a sign either is wrong. Pick one as the gate and treat the other as a cross-check.

## Scanning things that are not images

- **Source, pre-build.** `docker scout cves fs://.` or `trivy fs .`. Catches dependency CVEs in seconds without a build.
- **A running container.** Scan the image it was created from; `docker inspect --format '{{.Image}}'` gives the digest.
- **A tarball.** `docker scout cves archive://image.tar`, or `trivy image --input image.tar`.
- **Base images before adopting one.** Scanning candidates first turns base image selection into a decision with numbers behind it.

## Gating CI

Gate on new findings rather than total count. A total-count gate fails on inherited base-image issues nobody on the team can fix and gets disabled within a month.

```yaml
- name: Scan
  uses: docker/scout-action@v1
  with:
    command: cves,recommendations
    image: ${{ steps.meta.outputs.tags }}
    only-severity: critical,high
    only-fixed: true
    exit-code: true
    ignore-base: true
```

`only-fixed` plus `ignore-base` is the combination that keeps a gate credible: it fails only on findings the team can act on today. Track everything else in a report that does not block the build.

For Trivy:

```yaml
- uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp:${{ github.sha }}
    severity: CRITICAL,HIGH
    ignore-unfixed: true
    exit-code: '1'
```

Scan the image the pipeline just built, by digest, not a tag that may have moved.

## SARIF and code scanning

Both tools emit SARIF, which surfaces findings in the GitHub Security tab with history and dismissal tracking instead of buried in build logs:

```yaml
- uses: docker/scout-action@v1
  with:
    command: cves
    image: myapp:${{ github.sha }}
    sarif-file: scout.sarif
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: scout.sarif
```

## VEX and suppressions

VEX (Vulnerability Exploitability eXchange) records that a CVE is present but not exploitable in this context, in a form tools consume.

```bash
docker scout cves --only-vex-affected myapp:1.4.2
docker scout cves --ignore-suppressed myapp:1.4.2
trivy image --vex vex.json myapp:1.4.2
```

The value is that the reasoning outlives the person who did the triage. An undocumented suppression is indistinguishable from an oversight six months later, and gets re-litigated every audit.

Every suppression should carry the CVE, the justification, and a revisit date. `vulnerable_code_not_in_execute_path` is a valid justification; "false positive" without evidence is not.

## Reading a finding

A Scout or Trivy entry gives:

- **Affected range and fixed version.** No fixed version means no upstream patch — track it, do not burn a sprint on it.
- **Severity.** From the preferred advisory source, which may be the distro maintainer rather than NVD. A distro rating of LOW alongside a CVSS of 9.8 usually means the maintainer determined their build is not affected in the way the CVSS assumes.
- **The package and its layer.** If the layer belongs to a build stage, the package should not have shipped at all — that is a Dockerfile fix.
- **EPSS, when requested.** Probability of exploitation in the next 30 days. Updated daily, so a finding parked for months should be re-checked rather than assumed static.

Trace a package to the layer that introduced it with `docker history --no-trunc <image>`, then match against the Dockerfile.
