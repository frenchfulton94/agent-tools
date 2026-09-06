---
name: code-review
description: Reviews a change for correctness, clarity, and maintainability — reading a diff, a branch, or a pull request and reporting problems with specific line references. Use when the user asks for a code review, wants feedback on a change before merging, asks whether an implementation looks right, or asks what could be improved in code they just wrote.
---

<!--
Not a shipped skill. This is a synthetic competitor for the trigger battery, present because the
battery's first partial run had a probe load an unrelated generic `code-review` skill — so that
competitor was in scope and unrecorded. Reconstructing it here makes the lineup honest: the
should-not-fire probe "Review this PR." has somewhere plausible to go other than the security skill.

Deliberately written to be a strong competitor and to say nothing about security, so that a probe
choosing it over `reviewing-code-security` is evidence about the security description rather than
about this file being a straw man.
-->
