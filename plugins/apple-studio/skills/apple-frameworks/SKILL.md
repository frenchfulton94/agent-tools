---
name: apple-frameworks
description: Map of Apple's first-party frameworks - what exists, what each is for, and planning-grade guidance (privacy costs, entitlements, availability, pitfalls) for the frameworks most apps use. Use when designing a feature ("does Apple already ship this?"), choosing between a first-party framework and building custom, or assessing what adopting a framework will cost.
---

# Apple frameworks

1. Feature design starts with: does Apple already ship this? Check
   `references/framework-catalog.md` (generated from the live Technologies
   index - includes frameworks newer than model training data).
2. If a primer exists in `references/primers/`, read it before deciding to
   adopt - it carries the privacy/entitlement/review costs and pitfalls.
3. For implementation detail, ALWAYS fetch the framework's current
   developer.apple.com pages (live-docs-first rule, CONVENTIONS.md).
   The catalog answers "what exists"; primers answer "should I";
   live docs answer "how".
