# Trigger battery — securing-container-supply-chain

Run each query in a clean session with only the description visible. Record fired / did not fire.

## Should trigger

1. "Scan this image for vulnerabilities."
2. "Our pipeline flagged 40 CVEs in the API image. Which ones actually matter?"
3. "A customer is asking for an SBOM for our container."
4. "How do I sign our images so the cluster only runs ours?"
5. "What's SLSA and do we meet it?"
6. "Is this image safe to ship to production?"
7. "We need to prove this image came from our build pipeline."
8. "Add provenance attestations to our builds."
9. "cosign verify passes but I'm not sure it's actually checking anything."
10. "Security asked us to show what's inside our containers."

Items 6, 7, and 10 never name a tool or an artifact — they describe the business need. Those are the ones a tool-focused description misses.

## Should not trigger (near misses)

1. "Add a non-root USER to my Dockerfile." → `containerizing-apps` (authoring)
2. "How do I drop capabilities on this container?" → `containerizing-apps` (hardening reference)
3. "Should I mount the docker socket into my CI container?" → `containerizing-apps` (hardening reference)
4. "My image is 2 GB, help me shrink it." → `containerizing-apps`
5. "Docker daemon won't start." → `managing-container-runtimes`
6. "Set up SSO for our Docker Hub org." → account administration, not supply chain
7. "Scan our Python codebase for security bugs." → SAST on source, not container supply chain
8. "Rotate our AWS access keys." → secrets management, no container involved

Items 1–3 are the important negatives. They are unmistakably container security, and they belong to `containerizing-apps` and its hardening reference rather than here. The split is: **hardening is how a container runs; this skill is what is in the image and where it came from.**

## A/B assertions

Run "we have 40 CVEs in our API image, what should we do?" with and without the skill. With the skill, the response should:

- [ ] Ask for or run `quickview` before `cves`, to get the image-vs-base split
- [ ] Rank on exploitability and fixability, not CVSS severity alone
- [ ] Mention EPSS or an equivalent exploit-probability signal
- [ ] Propose a base image change before per-package updates
- [ ] Distinguish "no fix available" from "not yet fixed"
- [ ] Not propose suppressing findings to make the count drop

Run "sign our images" with and without. With the skill:

- [ ] Signs a digest, not a tag
- [ ] Includes both `--certificate-identity-regexp` and `--certificate-oidc-issuer` in the verify example
- [ ] Mentions `id-token: write` for GitHub Actions keyless signing
- [ ] Notes that signing without admission-time verification changes nothing

The identity-flags assertion is the one that matters most — a verify command without them is the common broken adoption, and it looks like it works.
