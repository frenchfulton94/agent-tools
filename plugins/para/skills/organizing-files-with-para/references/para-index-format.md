# PARA.md format

`para_index.parse_index` reads this file. It is deliberately forgiving about
whitespace and deliberately strict about heading text — and it fails
**silently**, not with an error, on anything it does not recognize. Get the
five headings right; everything else is close to free-form.

## The five headings

Exactly these, each on its own line as an H2 (`##` followed by whitespace —
`###` does not count):

- `## Projects`
- `## Areas`
- `## Resources`
- `## Never read`
- `## Never move`

Matching is case-insensitive and ignores surrounding whitespace, so
`## projects`, `##   PROJECTS`, and `## Projects` all parse the same way. A
heading that is not one of these five exact five phrases — a typo, a
singular/plural mismatch, an extra word — is not an error. The parser simply
never opens a bucket for it, and every dash-list line under it is dropped with
no warning anywhere. This is the most common way a `PARA.md` quietly stops
working: check the heading text first when a project or area stops matching.

## Entries: a dash list under a heading

Every line under a recognized heading that starts with `-` (after stripping
leading whitespace) becomes one entry. `- name` and `-name` both work; a line
that does not start with `-` is ignored, so plain prose can sit between
headings without being picked up.

## The em-dash convention

Everything after the **first** ` — ` (em dash, spaces on both sides) is a
human-readable description and is never parsed for meaning:

    - client-redesign — ship the site, due 15 October

parses to the single name `client-redesign`. Only the text before the first
` — ` is the entry; write commitments, deadlines, or reminders after it
freely.

## An entry's section IS its classification

There is no separate "type: project" field. Whichever heading a name sits
under — Projects, Areas, or Resources — is its P/A/R classification, full
stop. `scan.py` reads this directly: `index.classify(name)` returns
`1-Projects`, `2-Areas`, or `3-Resources` based only on which of the three
lists contains the name. Moving an entry between sections in the file is how
you correct a misclassification; there is nothing else to edit.

## `Never read` and `Never move` are functional, not documentation

Unlike Projects/Areas/Resources — which hold plain names matched as tokens
against file paths — entries under `## Never read` and `## Never move` are
**glob patterns**, in the same syntax as the plugin's built-in denylists
(`**/.ssh/**`, `**/*.pem`, and similarly for never-move). `scan.py` appends
them directly to its defaults before scanning:

    never_read = DEFAULT_NEVER_READ + index.never_read
    never_move = DEFAULT_NEVER_MOVE + index.never_move

So this is how a user extends either list — to keep a private folder's
contents out of the content peek, or to keep a directory from ever landing in
a plan — without touching any script. A bare filename here (`- taxes.pdf`)
only matches a file named exactly that at the scan root; to match it anywhere
in the tree, write `**/taxes.pdf`.

## Complete worked example

    ## Projects
    - client-redesign — ship the site, due 15 October
    - q4-taxes — file before the deadline

    ## Areas
    - finances — accounts stay reconciled, no end date
    - health

    ## Resources
    - cooking — recipes and technique notes

    ## Never read
    - **/*.psd
    - **/Private/**

    ## Never move
    - **/CurrentProjectAssets/**

This parses to two projects (`client-redesign`, `q4-taxes`) with `finances`
and `health` as areas, `cooking` as a resource, plus two extra never-read
patterns and one extra never-move pattern layered on top of the plugin's
defaults. `render_index` writes this same shape back out, so a round trip
through the maintaining-para-systems skill produces a file this parser reads
identically.
