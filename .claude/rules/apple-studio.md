---
paths:
  - "plugins/apple-studio/**"
  - "authoring/apple-studio/**"
---

# apple-studio pipeline

`authoring/apple-studio/CONVENTIONS.md` is the full contract — read it before
editing a skill or reference. Three things it covers that are easy to get wrong:

- **Live docs win over memory.** Apple's APIs churn every WWDC. Fetch the
  current page with `authoring/apple-studio/pipeline/docc.py` — developer.apple.com
  serves a JavaScript shell, so a plain fetch returns navigation and no content.
- **A 200 on a doc page is not evidence a symbol exists.** Compilation is the
  ship gate for any API-specific claim:
  `python3 authoring/apple-studio/pipeline/typecheck_snippets.py plugins/apple-studio/skills/<skill>/references/*.md`
- **Run trigger evals through `authoring/apple-studio/pipeline/run_evals.py`**,
  not a fresh loop. `--allowedTools` does not stop an eval session writing to
  the fixture app; the driver checks the fixture's git status before, during,
  and after, attributes writes to the prompt that made them, and restores the
  tree. `.claude/rules/eval-harness.md` carries the rest of the harness rules,
  and loads only under `skills/*/evals/`.

Work happens in numbered phases — see `authoring/apple-studio/docs/plans/` for
the current one and `authoring/apple-studio/docs/deferred.md` for what earlier
phases left open.
