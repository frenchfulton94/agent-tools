# Task 0 report: Opening sweep and charter amendment

## What was done

1. **Confirmed branch preconditions** (Step 1): `git branch --show-current`
   returned `phase9-adaptive-layout`; `git merge-base --is-ancestor ea4995c
   HEAD` exited `0`.

2. **Wrote the scan script** (Step 2):
   `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch_scan.py`,
   copied verbatim from the brief — the method unchanged from deferred.md
   item 1 (Phase 6, Phase 7).

3. **Ran the scan** (Step 3), scoped to `since=2026-09-12` (the Phase 7
   measurement date), output tee'd to
   `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch.log`:

   ```
   transcripts scanned: 2168
   excluded invocations by project: {'-Users-michaelfrenchfultonjr-Projects-StudioFixture': 60}
   genuine non-fixture invocations since 2026-09-12: 0
   ```

4. **Applied the pre-taken decision rule** (Step 4): genuine count is 0, so
   the "no skill is cut" branch applies regardless. (Even had the count been
   non-zero, no real feature has shipped through the plugin yet, so the
   skill gate's precondition remains unmet either way.) Appended to
   `authoring/apple-studio/docs/deferred.md` item 1, after the Phase 7
   decision-rule paragraph:

   > **Phase 9 measurement (2026-09-30).** This re-runs the Phase 6/7 scan,
   > scoped to sessions since 2026-09-12 (the prior measurement date). It
   > found 2,168 transcripts and **0** genuine non-fixture invocations of an
   > `apple-studio:*` skill. All 60 excluded invocations came from a single
   > project directory, `StudioFixture`. Evidence:
   > `records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch.log`.
   >
   > **Decision rule applied unchanged, not improvised:** the precondition —
   > a shipped real feature — remains unmet, so **no skill is cut this phase,
   > regardless of the count.**

   (The long single sentence in the brief's implied phrasing was split in
   two to stay under the 25-word CEE sentence-length rule; content is
   unchanged from what the scan produced.)

5. **Amended the charter** (Step 5): inserted after line 193 of
   `authoring/apple-studio/docs/specs/2026-08-03-apple-studio-design.md`
   (the `> rationale stands.` line closing the Phase 7 block), verbatim from
   the brief:

   ```
   >
   > **Amended 2026-09-30 (Phase 9).** Phase 8 shipped the catalog migration,
   > not ML, and did not amend the line above. ML remains the one outstanding
   > long-tail item. Phase 9 is on-demand work: adaptive layout and iPhone Duo —
   > see docs/specs/2026-09-30-phase9-adaptive-layout-design.md.
   ```

6. **Recorded verified headers** (Step 6):
   `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/headers.log`
   holds the `head -1` of `platform-idioms.md` (verified: 2026-08) and
   `hig-patterns.md` (verified: 2026-09) — matches the brief's expectation.
   No edits made to either file; Task 4 re-stamps them.

7. **Checked prose with Vale** (Step 7):
   `vale --config .claude/skills/controlled-engineering-english/scripts/vale/.vale.ini
   authoring/apple-studio/docs/deferred.md
   authoring/apple-studio/docs/specs/2026-08-03-apple-studio-design.md`.
   - The deferred.md addition (lines ~126-135) produced one G-S1
     sentence-length warning on first pass; fixed by splitting the sentence
     ("This re-runs the Phase 6/7 scan... It found 2,168 transcripts and...").
     Re-run: zero warnings on the added lines.
   - The charter addition (lines 195-198) produced two warnings, both
     `Dictionary: use 'change' instead of 'Amended'/'amend'` — the waived
     "amend" warning, expected since every prior amendment block in this
     file uses the same heading convention. No other warning on those lines.
   - All other warnings in both files are on pre-existing lines I did not
     touch (confirmed by scoping grep to the added line ranges) and are out
     of scope per the brief ("judge other warnings only on lines you added").

## Files changed

- `authoring/apple-studio/docs/deferred.md` — item 1 append (Phase 9
  measurement paragraph).
- `authoring/apple-studio/docs/specs/2026-08-03-apple-studio-design.md` —
  charter amendment after line 193.
- New:
  `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-0-sweep/killswitch_scan.py`,
  `killswitch.log`, `headers.log`, `task-0-report.md` (this file).

## Self-review

- Diffed both doc edits against the brief's exact text: charter insertion
  matches verbatim, including the blank `>` line and blockquote markers.
  deferred.md content matches the required fields (scan window, transcripts
  scanned, genuine count, excluded counts by project, evidence path); only
  wording of the connecting sentence was split for line length, not
  substance.
- Confirmed no skill/agent files, plugin manifests, or version files were
  touched — this task is bookkeeping only, as specified.
- Confirmed the scan script matches the brief's script byte-for-byte (no
  edits made to the logic, exclusion list, or output format).
- Confirmed `killswitch.log` contains only the three summary lines the
  script printed (no per-hit lines, since genuine count is 0) — no
  transcript content leaked into the log.
- Re-checked the `EXCLUDE` tuple catches `StudioFixture` and the
  `agent-tools`/`apple-studio` self-referential projects; the actual hits
  were all in `StudioFixture`, consistent with Phase 6/7's finding.

## Concerns

- None blocking. One judgment call: I split one added sentence in
  deferred.md to satisfy the 25-word CEE rule; the split is a phrasing
  choice, not a content change, and I believe it still matches the brief's
  intent ("stating: the scan window ... transcripts scanned, the genuine
  count, the excluded counts by project, and the evidence path").
- **Commit trailer deviation.** The brief's commit message specifies
  `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
  My harness instructions for this session mandate
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` for commits made
  from here, and state this replaces any earlier/other attribution
  guidance. I used the subject and body exactly as the brief specifies but
  substituted the correct trailer for the model that actually did this
  work (Sonnet 5, not Opus 5.5), since a false attribution seemed worse
  than a literal mismatch with the brief. Flagging for the controller in
  case the brief's trailer was deliberate for a reason I'm not seeing.
