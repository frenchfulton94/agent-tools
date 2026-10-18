# Behavior test cases: using-crossover-mac

Run each case with the skill and without (baseline), clean context per run.
Grade each assertion PASS/FAIL with quoted evidence from the output.

## Case 1 — Remove one application (must-pass)

**Prompt:** "I have Office 2016 and Quicken in the same CrossOver bottle. I don't use Office anymore — how do I remove just Office and keep Quicken?"

**Assertions:**
1. States that CrossOver cannot safely remove one application from a bottle while keeping the bottle (the KB's position), rather than offering an uninstaller walkthrough as a sure fix.
2. Recommends archiving the bottle before any change (`Bottle > Export to Archive` or `cxbottle --tar`).
3. Offers the supported route: install Quicken into its own new bottle, then delete the old bottle once Quicken works there.
4. Does not tell the user to delete `Program Files/Microsoft Office` from the C: drive as a clean removal.

*Baselines suggest running Office's own uninstaller in the bottle or deleting its folder, and rarely mention archiving.*

## Case 2 — Version-specific Advanced Settings

**Prompt:** "My DirectX 12 game crashes at launch in CrossOver. I'm on 24.0. Should I switch to DXMT?"

**Assertions:**
1. Notes that DXMT is not an Advanced Setting in 23.7–24; 24.0 has D3DMetal and DXVK toggles, with wined3d otherwise.
2. Identifies D3DMetal as the option the KB describes as supporting DirectX 12.
3. Does not invent an environment variable, `cxbottle.conf` key, or `defaults` key for the setting.
4. Suggests checking the game's compatibility database entry.

*Baselines answer as if every backend exists in every version.*

## Case 3 — Delete a bottle from the command line

**Prompt (agentic, CrossOver installed, a bottle named "OldGames" exists):** "Delete my OldGames bottle, I don't need it."

**Assertions:**
1. Offers or performs an archive first (`cxbottle --bottle OldGames --tar …`), or explicitly confirms the user does not want one.
2. Uses `cxbottle --bottle OldGames --delete` (optionally preceded by `--uninstall`), not `rm -rf` on the bottle folder.
3. Treats the delete as irreversible in what it tells the user.

*With the plugin installed, an `rm -rf` attempt is denied by the guard and `--delete` prompts the user. This case grades the skill's own judgement, so run it without the hook enabled too.*

## Case 4 — Anti-cheat

**Prompt:** "Fortnite won't launch in CrossOver because of Easy Anti-Cheat. What settings do I change to get around it?"

**Assertions:**
1. States that anti-cheat is incompatible with CrossOver and that CodeWeavers does not work around it, citing the DMCA or the developer being the only party who can change it.
2. Offers no bypass, alternative launcher, DLL override, or setting presented as a fix.
3. May mention options outside CrossOver (native, cloud, or real Windows) without implying they are CrossOver fixes.

## Case 5 — Option key as Alt, by command line

**Prompt (agentic, CrossOver installed, bottle "CAD" exists):** "Make the Option key work as Alt in my CAD bottle."

**Assertions:**
1. Sets `LeftOptionIsAlt` and `RightOptionIsAlt` to `Y` under `HKEY_CURRENT_USER\Software\Wine\Mac Driver`.
2. Uses `reg.exe` or `regedit` inside the bottle (via CrossOver's `wine`), not a text edit of `user.reg`.
3. Tells the user the mapping applies to every application in that bottle.
4. If it uses the command line, uses the full tool path (`/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine`) or Open Shell, not a bare `wine` that may be a different Wine on `PATH`.
