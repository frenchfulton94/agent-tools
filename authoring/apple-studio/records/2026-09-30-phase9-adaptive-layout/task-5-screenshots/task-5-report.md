# Task 5 Report: iPhone Duo screenshot sizes

## Status
COMPLETED

## Fetched Values
Successfully fetched screenshot specifications from Apple Developer documentation:
- **Outer display:** 1398 × 2034 pixels or 2034 × 1398 pixels
- **Inner display:** 2007 × 2853 pixels or 2853 × 2007 pixels
- **Upload availability note:** Support for uploading assets for iPhone Duo in App Store Connect will be available later this year.

All fetched values match the expected values in the brief.

## Edits Made

### File: `plugins/apple-studio/skills/app-release/references/app-store-submission.md`

**Line 1 (verified line):**
Appended to the end of the `> verified:` line:
```
; re-checked 2026-09 against https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications (Phase 9: iPhone Duo sizes)
```

**Line 101 (Screenshots per required device class bullet):**
Appended to the end of the bullet:
```
 iPhone Duo adds two size classes, one per display: outer 1398 × 2034 px (portrait) and inner 2007 × 2853 px (portrait), with their landscape equivalents. As of 2026-09 App Store Connect cannot yet accept Duo uploads, so check the specification page before planning a Duo screenshot set (https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications). Capture each display in the poses `apple-design`'s `adaptive-layout.md` § Checking a layout on iPhone Duo lists.
```

## Gate Results
All three gates passed successfully:
- ✅ `bun test`: 198 pass, 0 fail (55 pre-existing advisory warnings)
- ✅ `bun run audit`: 0 errors, 55 warnings (all pre-existing)
- ✅ `claude plugin validate . --strict`: Validation passed

## Files Changed
1. Modified: `plugins/apple-studio/skills/app-release/references/app-store-submission.md`
   - Added iPhone Duo screenshot size guidance to the file
2. Created: `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-5-screenshots/fetch.txt`
   - Documentation of fetched values
3. Created: `authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-5-screenshots/task-5-brief.md`
   - Task brief (already present in records)

## Commit
- Commit SHA: 97e1ea8
- Message: "Phase 9 Task 5: iPhone Duo screenshot sizes"
- Includes Co-Authored-By trailer for Claude Haiku 4.5

## Concerns
None. The task completed successfully. All gates passed and the referenced `adaptive-layout.md` section already exists in the codebase.

## Fix round 1: Commit the task report

The task report file was not included in the initial commit. Fixed by committing the report file separately.

**Command run:**
```bash
git status --short -- authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-5-screenshots/
```

**Pre-commit status output:**
```
?? authoring/apple-studio/records/2026-09-30-phase9-adaptive-layout/task-5-screenshots/task-5-report.md
```

**Commit 2 (fix):**
```
Phase 9 Task 5 fix 1: commit the task report
```
