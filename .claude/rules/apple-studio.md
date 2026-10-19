---
paths:
  - "plugins/apple-studio/**"
  - "authoring/apple-studio/**"
---

# apple-studio pipeline

`authoring/apple-studio/CONVENTIONS.md` is the full contract — read it before
editing a skill or reference. Three things it covers that are easy to get wrong:

- **Live docs win over memory.** Apple's APIs churn every WWDC. Read the
  current page by appending `.md` to its documentation URL, which returns
  Markdown. A bare documentation URL returns a JavaScript shell, with
  navigation and no content. `authoring/apple-studio/pipeline/docc.py` is the
  fallback and the tool for `--children`. `WebFetch` is not a read: a small
  model summarizes the page, so a page seen only through it counts as unread.
- **A 200 on a doc page is not evidence a symbol exists.** Compilation is the
  ship gate for any API-specific claim. Swift blocks:
  `python3 authoring/apple-studio/pipeline/typecheck_snippets.py plugins/apple-studio/skills/<skill>/references/*.md`.
  Metal, C++, and Rust blocks go through `pipeline/typecheck_native.py`, and
  every other code fence must be text, shell, or config.
- **Run trigger evals through `authoring/apple-studio/pipeline/run_evals.py`**,
  not a fresh loop. `--allowedTools` does not stop an eval session writing to
  the fixture app; the driver checks the fixture's git status before, during,
  and after, attributes writes to the prompt that made them, and restores the
  tree. `.claude/rules/eval-harness.md` carries the rest of the harness rules,
  and loads only under `skills/*/evals/`.

Work happens in numbered phases — see `authoring/apple-studio/docs/plans/` for
the current one and `authoring/apple-studio/docs/deferred.md` for what earlier
phases left open.
