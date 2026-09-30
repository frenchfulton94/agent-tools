### Task 5: iPhone Duo screenshot sizes in `app-release`

**Files:**
- Modify: `plugins/apple-studio/skills/app-release/references/app-store-submission.md:1,101`

**Interfaces:**
- Consumes: `survey/screenshot-specifications.txt`.

- [ ] **Step 1: Re-check the source.** WebFetch `https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications` with the prompt "Quote the iPhone Duo screenshot sizes and any note about upload availability." Expected: outer 1398 × 2034 / 2034 × 1398, inner 2007 × 2853 / 2853 × 2007, and a note that uploads come later. If anything differs, use the fetched values and record the difference in `task-5-screenshots/fetch.txt`.

- [ ] **Step 2: Edit.** After the bullet at line 101 (`- **Screenshots per required device class.** …`), append to that bullet: ` iPhone Duo adds two size classes, one per display: outer 1398 × 2034 px (portrait) and inner 2007 × 2853 px (portrait), with their landscape equivalents. As of 2026-09 App Store Connect cannot yet accept Duo uploads, so check the specification page before planning a Duo screenshot set (https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications). Capture each display in the poses \`apple-design\`'s \`adaptive-layout.md\` § Checking a layout on iPhone Duo lists.`

   Append to the file's `verified:` line: `; re-checked 2026-09 against https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications (Phase 9: iPhone Duo sizes)`.

- [ ] **Step 3: Gates and commit.**

```bash
bun test && bun run audit && claude plugin validate . --strict
git add plugins/apple-studio/skills/app-release/references/app-store-submission.md $AS/records/2026-09-30-phase9-adaptive-layout/task-5-screenshots
git commit -m "Phase 9 Task 5: iPhone Duo screenshot sizes

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

