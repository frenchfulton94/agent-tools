# Working notes

## Stated preferences

- **Teammates first, author second.** Lessons assume no OpenSpec knowledge. Author-level
  detail goes in a clearly marked `Appendix` block at the end of a lesson, never inline —
  a newcomer must be able to stop at the recall check and still have the win.
- **Full coverage over brevity.** All thirteen lessons, all twelve schemas driven end to
  end. Approved 2026-08-28 in preference to a ten- or eight-lesson trim.
- **Nothing goes public without a deliberate act — and that act has now been taken.**
  The package was written on the assumption that Pages stayed disabled, because this
  repository is private, the org is on the Team plan, and a published Pages site on that
  plan has **no access control**. That was a decision for a person in repo settings, and on
  2026-08-28 it was made: Pages is enabled with Source: GitHub Actions, and the site is live
  and world-readable at
  <https://frenchfulton94.github.io/agent-tools/>. Anyone with the URL
  can read every lesson. Write accordingly — there is no longer a private-by-default
  backstop between a sentence in a lesson and the public internet.

## Conventions this workspace follows

- One shared stylesheet, [`assets/lesson.css`](./assets/lesson.css). No lesson carries its
  own `<style>` block, and every colour is a token defined in the `:root` blocks at the top
  of that file — a re-brand replaces that block and touches nothing below it.
- **The brand pass changed more than tokens, and the two changes are worth knowing.**
  First, type: the original draft used a serif for headings, which inverts this
  system's signature. Figtree now carries every heading at weight 650 with negative
  tracking, and Sentient is confined to lesson prose and decks, where editorial serif is
  correct. Second, the asides: six callouts each carried a 3px coloured side rule, which
  spends the StatCallout's one signature on scaffolding. They now differentiate by surface
  (`--ground-sunk` / `--ground-mist` / a dark green band) plus a full hairline plus label
  colour — the system's own separation mechanism. `brand-lint --strict` flagged both.
- The `.stop` callout is a declared dark band (`data-background="dark"` in the markup), so
  the strongest signal in the package is the institution speaking rather than a louder
  colour. Sixteen of them across the lessons and cards.
- Dark viewer preference resolves to the brand's own dark band — `--green-deep` canvas,
  white text, mint muted, gold-soft accents — rather than an invented dark palette.
- Quizzes use [`assets/quiz.js`](./assets/quiz.js) with the markup contract documented at
  the top of that file. Answers must be equal in word count and near-equal in characters;
  [`assets/check-answers.mjs`](./assets/check-answers.mjs) checks this across every lesson
  and is run by hand, not in CI.
- **Tables break out of the prose measure.** A 36rem column reads well and is far too
  narrow for a five-column table — measured, the tier table's first two columns were being
  handed 68px and 85px while the third took 422px. `.scroll` is therefore wider than the
  text column and centred on the same axis, resolving to 100% on the wide reference pages
  and on phones, where the table scrolls inside its box instead.
- **`.col-label` on a `th`, for a label column starved beside a paragraph column.** It has
  to be `width`, not `min-width`: min-width does not apply to table cells in auto layout
  and is silently ignored — verified by measuring both. Add it only after measuring a
  column, and only for short labels; genuine prose wrapping to four lines is a table doing
  its job, not a bug. Nine columns across the twenty pages needed it.
- **[`assets/check-structure.mjs`](./assets/check-structure.mjs) proves element nesting.**
  Written after a scripted edit using `/<th([^>]*)>/` matched `<thead>` and replaced five
  opening tags, losing those tables' header rows while every other check still passed.
  Tag *counting* cannot do this job here, because closing tags are often split across
  lines (`</strong\n>`); this walks a stack. Run it after any scripted edit to the HTML.
- Every claim about plugin behaviour carries a citation to a source path with a line number
  where one helps. A claim that cannot cite source or an attached guide does not go in.
- Where a secondary document disagrees with source, the lesson teaches source and names the
  disagreement in a `Drift` aside. Silently preferring source teaches the fact but not the
  habit.
- The workspace root is not the site root. `site/build.mjs` publishes exactly
  `index.html`, `lessons/`, `reference/`, `assets/` — this file, `MISSION.md`,
  `RESOURCES.md`, and `learning-records/` stay working files. Adding a fifth publishable
  thing means editing that script's `PUBLISH` list, which is the point.
- Lessons cite plugin source by relative path so a checkout reads correctly; the build
  rewrites those to blob URLs and **fails** if any link would 404 on the deployed site.
  Keep citing relatively and let the build handle it.
- **Merging is publishing.** `.github/workflows/pages.yml` deploys on push to `main`,
  path-filtered to `plugins/workflows/learn/**`, `docs/install.html`, the brand assets, and
  the workflow file. The trigger shipped commented out, on the reasoning that publishing
  should be one deliberate act per publish; it was enabled on 2026-08-28, once Pages was on
  and dispatching by hand after every merge was the only thing standing between a correct
  repository and a stale site. What that trades away is real and worth naming: the only gate
  left is pull request review, and there is no longer a window in which a merged mistake has
  not yet reached the public site. Review the lessons as published copy, not as drafts.
  `workflow_dispatch` remains for a redeploy or for rolling back by dispatching an older ref.
- **Renaming a lesson breaks its live URL.** A Pages deploy replaces the whole artifact;
  nothing of the previous deploy survives, so the old path starts returning 404 the moment
  the workflow runs. This first bit on 2026-08-28, when
  `0005-the-four-things-setup-cannot-do.html` became
  `0005-the-five-things-setup-cannot-do.html` — the lesson is built as a count, an added
  human step made it five, and fudging the title to keep the filename would have been the
  worse trade. It was accepted knowingly: the site had been public for hours and nobody had
  been pointed at it yet. Weigh it again next time, and prefer a redirect stub only if a
  real reader could plausibly hold the old link — one costs a permanent entry in
  `build.mjs`'s `PUBLISH` set for a transient problem.

## Deliberate omissions

- No lesson teaches writing a new schema. `configuring-openspec` owns that, and the mission
  puts it out of scope.
- No lesson explains what happens inside superpowers, mattpocock, impeccable, or
  agent-skills. Lessons teach the handoff point and name the skill; the far side is the
  pack's own documentation.
- The first `compass_artifact` guide's DeepSeek model table is never reproduced, not even as
  a comparison. Reproducing it in a Claude Code lesson would put twelve wrong model IDs in
  front of a newcomer, and the guide's own caveats section says the vocabulary diverges. The
  second one (subscription tiers) *is* Claude and supplies the real table — that is where
  lesson 12's `advanced` rows come from.
- No absolute usage numbers are quoted anywhere. The tier guide's hours-per-week and
  tokens-per-window figures are dated or third-party, so the lessons teach the routing
  consequences and point at `/usage` instead. Do not let a future edit paste those numbers
  in: they read as authoritative and are not.

## Open questions for the learner

- **Which subscription tier is the department on?** Lesson 12 teaches all three, because
  nothing in the repository records the answer. Pro changes real behaviour — `opusplan` for
  planning-heavy schemas, and Opus-at-xhigh standing in for Fable at the feature gates,
  which is what the plugin already pins. Once known, record it and the lesson can lose two
  of its three tier rows.
- Which level is the default for a new internal repo? The lessons teach the ladder
  but do not pick for the team. Once decided, record it as a learning record and add
  one line to lesson 02.
- Is `openspec config profile` set to a custom selection on team machines? It is
  machine-global, so it is a department decision rather than a per-repo one, and lesson 05
  currently teaches the decision rather than the answer.
