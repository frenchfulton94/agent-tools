**Session:** <!-- single-session | multi-session -->
**Base:** <!-- the commit before the first slice; apply fills it -->

## 1. <!-- slice title --> (<!-- tracker reference, or local -->)
<!-- Blocked by: none -->

- [ ] 1.1 <!-- acceptance criterion -->
- [ ] 1.2 <!-- acceptance criterion -->

## 2. Surface: <!-- surface --> (<!-- tracker reference, or local -->)
<!-- Only when design.md has a Presentation seam block; delete otherwise.
     Blocked by: the slice that builds the seam. Impeccable does this slice. -->

- [ ] 2.1 Built through impeccable against design.md's Presentation seam block
- [ ] 2.2 Every emitted state renders from its fixture
- [ ] 2.3 impeccable audit findings resolved, then impeccable polish run

## Ship

- [ ] code-review findings resolved in one follow-up commit per slice
- [ ] code-review-and-quality run over the whole change: critical and required findings fixed
- [ ] Shipped: a PR whose body came from the pr skill, or a direct merge (say which)
- [ ] /retro offered to the human
