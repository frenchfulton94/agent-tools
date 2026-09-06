# The tier guide closes the model gap — and contradicts itself against this plugin

A third usage guide (2026-08-28) supplies per-schema, per-phase model and effort for the
`advanced` eight in Claude model names, across Pro / Max 5x / Max 20x. It supersedes
[[0003-model-guidance-is-provider-split]] for model choice, and its routing content agrees
with the shipped agent pins: the four cells where premium reasoning pays — feature design
gate, feature review gate, bugfix root cause, hotfix postmortem — are exactly the two the
plugin pins plus the two that have no subagent.

**Two things it settles that were previously open.** First, the Fable question: the earlier
guide put both design gates on the top tier while the agents pin `opus`, and lesson 12 left
the choice to the reader. This one closes it — Opus 5 wins most published head-to-heads at
half the rate, and Fable carries retention and classifier strings — so the shipped pins are
right as they are and Fable is a benchmarked exception, not an upgrade. Second, the tier
axis is new material: tier changes what you can afford, never which model you can pick.

**One thing it gets wrong for this repository, and this is the durable lesson.** It
recommends `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-5` on all three tiers for cheap
subagent fan-out. That variable outranks frontmatter `model:`, so in a repo this plugin
configured it would collapse the design and review gates to Sonnet while every schema still
reads as though a stronger model had judged them. The advice is sound for an unpinned setup
and harmful here. The plugin already achieves the same saving per agent —
`code-review-spec` and `taste-preflight` are `sonnet` by design.

**Implication for future sessions:** generic Claude Code advice about burn control has to
be checked against the pins before it is repeated. A guide that assumes nothing is pinned
will confidently recommend flattening the one thing this plugin spends its complexity on.
