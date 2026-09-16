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

## After

Re-run `organizing-files-with-para` against the same root. The archived tree is
untouched input for the next scan if it is ever needed.
