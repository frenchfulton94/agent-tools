# Digital bankruptcy

When a tree has drifted past the point where sorting it is worth the effort,
the supported move is to declare bankruptcy: move everything into
`4-Archives/<today's date>` and re-run the sixty-second setup.

## Why this is safe

Nothing is deleted. Everything stays exactly where search can find it. The
archive is a resting place, not a wastebasket — which is the whole reason the
plugin has no delete verb.

## When to offer it

- `0-Inbox` has grown for several upkeep passes running.
- `PARA.md` no longer resembles what the user is working on.
- The user says some version of "I've lost track of this".

Offer it. Do not perform it unprompted — it is still a plan, it still needs
approval, and it still writes a manifest.

## The plan itself

A bankruptcy plan is an ordinary plan, not a special case: one group (or a
few, if you split by top-level folder), `destination: 4-Archives/<today's
date>`. Follow `../../organizing-files-with-para/references/plan-format.md`
for the group schema and the sequential-`id` convention (`g1`, `g2`, …) — the
same rules apply here as to any other plan `apply.py` runs.

`4-Archives/<today's date>` is a destination you choose by hand; it is not
something `scan.py` produces. The scanner's own age-based clusters land in
`4-Archives/<year-of-last-use>` instead. `apply.py` does not distinguish the
two — it accepts whatever destination the plan names — so nothing stops a
bankruptcy plan from using either convention, but `<today's date>` is what
marks a folder as "archived by bankruptcy" rather than "archived by age" when
someone reads the tree later.

## After

Re-run `organizing-files-with-para` against the same root. The archived tree is
untouched input for the next scan if it is ever needed.
