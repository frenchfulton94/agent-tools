# Curation reference

Contents:
- [Placement](#placement)
- [Overlap](#overlap)
- [Whether it belongs at all](#whether-it-belongs-at-all)
- [When a plugin should split](#when-a-plugin-should-split)
- [Dead weight](#dead-weight)

Curation is the half of maintenance no validator reaches. A catalog can pass every structural check
and still be worse than it was last month — because a skill landed in the wrong plugin, because two
descriptions now compete for the same request, or because nothing was ever removed.

## Placement

A plugin is an install decision. Everything inside it arrives together, so the question is not "which
plugin is this skill most similar to" but **"would someone who installs that plugin want this?"**

Similarity and shared purpose diverge more often than they look like they would. A skill for linting
brand CSS resembles the web-development skills technically, and belongs with the brand plugin,
because the person installing for brand work is the person who needs it — and the person installing
for TypeScript does not want brand tooling arriving alongside their type-error help.

When no existing plugin shares that reason, that is the case for a new plugin. The skill being new is
not. A new plugin costs a manifest, a registration, a README row, a version line to keep in sync, and
a decision every future contributor has to make; carry that cost only when the audience genuinely
differs.

Signals the placement is wrong:

- The plugin's description needs a new clause to cover the addition, and the clause does not fit the
  sentence.
- The skill's likely users would install this plugin for that skill alone.
- Explaining the grouping to someone requires the word "also".

## Overlap

Two skills whose descriptions would both plausibly fire on one request is a routing defect. The user
gets whichever the model picks, and the choice is neither stable nor visible.

Diagnose from the descriptions alone, read cold, with no knowledge of the bodies. Write the request
that ought to reach each skill, then check whether the other's description also claims it.

The fix is usually a scope clause in one description, not a merge — the meta-skills in this
marketplace show the pattern, each closing by naming the sibling that owns adjacent work. Merge only
when both skills genuinely do the same job, which is rarer than overlap suggests.

An overlap between a repo-local skill and a shipped one is still an overlap. Both load in a session
in that repository, whatever the scan boundaries of the tests say.

## Whether it belongs at all

Two questions, in order. `authoring-skills` owns the first — is a skill the right form, against a
memory file for a one-line convention, a hook for a rule that must hold every time, or a subagent for
verbose isolated work.

The second is catalog-level and is the one that gets skipped: **is a marketplace the right
distribution channel?** Content that only makes sense inside one repository — knowing that
repository's test suite, its directory names, its release ritual — belongs in that repository's
`.claude/`, not in a plugin other people install. Shipping it wastes an install decision on people it
cannot help, and dilutes the plugin it lands in.

The reverse is also worth catching: a repo-local skill that would help anyone with a similar problem
is a candidate to move into a plugin, at the price of generalizing it away from any one repository.

## When a plugin should split

Not by size. A plugin with many skills serving one audience is fine. Split when the audiences have
separated — when a real user wants half of it and would be worse off receiving the other half.

Splitting is a rename in disguise: existing installs break. It needs `renames` entries and a release
note, and it is worth doing well before the plugin becomes something people depend on, or not at all.

## Dead weight

The deletion pass is last in the audit for a reason — it is the one that gets dropped when the list
runs long, and the only one that makes the catalog smaller.

- A skill nobody triggers. Usually a description problem rather than a value problem; check that
  before removing anything.
- A skill whose job the model now does unprompted. Skills written against older model behavior can
  degrade output by over-constraining it, and deletion is a legitimate fix.
- A plugin with one skill that would sit comfortably inside another.
- Documentation promising something that no longer ships, or that never did.

Removing is a real change: version bump, `renames` entry when a plugin goes, README row removed, and
a note saying what replaces it.
