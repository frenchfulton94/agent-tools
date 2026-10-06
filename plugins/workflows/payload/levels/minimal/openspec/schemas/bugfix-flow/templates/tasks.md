**Session:** <!-- single-session | multi-session -->

## 1. <!-- what is being fixed --> (<!-- tracker reference, or local -->)

- [ ] 1.1 Failing test at <!-- seam from diagnose.md --> reproducing the fault
- [ ] 1.2 <!-- the fix, at the agreed layer -->
- [ ] 1.3 <!-- a same-cause extra from Also found, or delete this line -->
- [ ] 1.4 Cleanup: the debug tag greps to nothing, and throwaway harnesses are deleted

<!-- A second group only when the cause spans modules, or when a symptom fix
     ships now and the cause fix follows with its own tracker issue. -->

## Ship

- [ ] The commit or PR names the hypothesis that turned out correct
- [ ] code-review findings resolved in one follow-up commit
- [ ] /retro offered to the human
- [ ] /improve-codebase-architecture offered <!-- only when there was no correct seam; delete otherwise -->
