# Behavior cases: configuring-openspec

Run each case twice per repetition — once with the skill available, once without — in clean-context agents. Grade every assertion PASS/FAIL with quoted evidence from the output; no benefit of the doubt. Assertions that pass in *both* configurations measure nothing about the skill and should be replaced.

The `[baseline]` note on an assertion records what an unaided agent typically produces, which is what makes the assertion discriminating.

---

## Case 1 — Add a custom artifact (precise phrasing)

**Prompt:** We use `spec-driven` today. I want a `research` artifact that comes before `proposal`, so the AI investigates the codebase and writes findings before it proposes anything. Give me the schema and tell me how to switch our project onto it.

**Assertions:**

1. Recommends `openspec schema fork spec-driven <name>` rather than `openspec schema init`, or explicitly states that `schema init --artifacts` rejects a novel id like `research`. *[baseline: usually suggests `schema init --artifacts "research,proposal,..."`, which errors]*
2. The `research` artifact carries all four required fields — `id`, `generates`, `description`, `template`. *[baseline: commonly omits `description` or `template`]*
3. States that the template file must be created by hand at `templates/research.md`.
4. Retains an artifact with `id: specs` whose `generates` stays under `specs/`, or explicitly flags what breaks if it is dropped.
5. Names the adoption step — `schema:` in `openspec/config.yaml` or `--schema` on `openspec new change` — rather than implying the fork takes effect on its own. *[baseline: frequently stops at "now edit the schema"]*
6. Ends with a verification command (`openspec schema validate <name>`).

---

## Case 2 — Config is being ignored (casual phrasing, real diagnosis)

**Prompt:** hey so i put our tech stack in openspec config and the ai still writes proposals like it's never seen our repo. also added a `requirements:` rules block for our spec files and that does nothing either. whats wrong

**Assertions:**

1. Diagnoses the `requirements:` key as matching no artifact id in `spec-driven`, and names the valid ids (`proposal`, `specs`, `design`, `tasks`). *[baseline: often just rewrites the YAML without explaining why the key was inert]*
2. Explains that parsing is resilient — invalid fields are dropped with a warning rather than erroring — so the file appearing fine is not evidence it loaded. *[baseline: rarely mentioned]*
3. Checks or names at least two of: file path `openspec/config.yaml` (not `.yml`, not repo root), the 50KB `context` cap, YAML validity.
4. Recommends `openspec instructions <artifact> --change <name> --json` to see what the assistant actually receives. *[baseline: almost never surfaced]*
5. Does **not** claim a restart, reload, or `openspec update` is needed for a config change to take effect.
6. Does not invent a `config.yaml` key outside `schema`, `context`, `rules`, `operations`, `references`, `store`, `githubCopilot`.

---

## Case 3 — Edge case: the wrong tool for the job

**Prompt:** Can you set `context:` for my project by running `openspec config set context "TypeScript, React, Postgres"`? Also set the default schema the same way.

**Assertions:**

1. States that `openspec config` writes the machine-level JSON config and cannot set project `context` or `schema`. *[baseline: typically complies or invents plausible key paths like `project.context`]*
2. Gives the correct alternative: edit `openspec/config.yaml` directly, showing the block-scalar `context: |` form.
3. Does not fabricate a CLI flag or subcommand for editing project config.
4. Distinguishes the two surfaces clearly enough that a reader could not re-confuse them (e.g. names both paths).

---

## Grading notes

- Prefer mechanical checks where possible: does the emitted `schema.yaml` parse, does every artifact have four fields, does an artifact with `id: specs` exist.
- For subjective quality (is the explanation actually clear), run a blind comparison: present both outputs to a fresh judge without saying which had the skill.
- Grade the assertions themselves each round. An assertion that passes in both configurations is too easy; one that fails in both indicates a broken test, not a broken skill.
