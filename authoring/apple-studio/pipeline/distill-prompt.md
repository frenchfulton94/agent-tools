You are distilling book chapters into a reference file for a Claude Code skill.

Read: {CORPUS_FILE} lines {START}-{END} (and any other ranges listed for this topic).
Target: {REFERENCE_FILE} for the {SKILL} skill. Topic: {TOPIC}.

Extract ONLY decision-grade guidance: principles, trade-offs, decision criteria,
checklists, canonical patterns, classic mistakes. Rules:
1. WORTH-IT: skip anything a strong Swift developer (or Claude) already reliably
   knows. No tutorials, no API walkthroughs, no history. If a chapter yields
   nothing above that bar, yield nothing.
2. BASELINE: write for SwiftUI + Swift 6 strict concurrency + Swift Testing.
   Material that only applies to UIKit/Combine/XCTest/GCD goes under a
   "## Maintaining older code: <topic>" heading or is dropped.
3. CURRENCY: flag every API-specific claim with [VERIFY: <claim>] — the
   dispatcher checks these against live docs before commit. Do not flag pure
   design judgment.
4. OWN WORDS: never copy sentences from the source. Cite as (Book, ch. N).
Output: markdown body only (no header block — the dispatcher adds it),
target 100–250 lines. Dense, imperative, example-light (short Swift snippets
only where a pattern is clearer as code).
