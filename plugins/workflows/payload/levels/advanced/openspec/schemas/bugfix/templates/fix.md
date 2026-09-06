## Fix Design

<!-- Smallest change at the root cause, not the symptom. Alternatives rejected
and why. -->

## Fix Layer

<!-- Cause or symptom, decided openly with reasoning. Symptom fix: state what
the proper cause fix requires, so the choice is inherited, not the surprise. -->

## Spec Delta

<!-- Spec covered the case, code disagreed -> "No delta owed; regression test
holds the line." Spec was SILENT about the case that broke -> that silence is
the bug behind the bug: ADDED requirement whose scenario is the reproduction
made permanent (the common outcome). Spec proved wrong -> MODIFIED, copying
the entire block header included (archive matches by header). -->

## Regression Guard

<!-- The reproduction test turns green; new coverage that closes the escape
gap; treatment of same-class hits. -->

## Risk & Rollback

<!-- What could this fix break; how it reverts. -->
