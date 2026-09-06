# Behavior test cases: managing-unraid-servers

Run each case with the skill and without (baseline), clean context per run.
Grade each assertion PASS/FAIL with quoted evidence from the output.

## Case 1 — Unmountable disk (must-pass set)

**Prompt:** "Disk 5 in my Unraid array came back unmountable after a power cut. The GUI is offering me a Format button. Server's on 7.2. What do I do?"

**Assertions:**
1. Advises **against** formatting, and says why in terms of data loss plus parity being updated so reconstruction becomes impossible.
2. Recommends a filesystem check/repair as the first action.
3. Names the correct array state for the repair (Maintenance Mode for XFS/EXT4) rather than leaving it unstated.
4. Uses the Unraid-managed device path for a 7.2 array disk (`/dev/mdXp1`), or directs the user to the WebGUI CHECK/FIX flow — not `/dev/sdX1` and not a whole-disk path.
5. Mentions capturing diagnostics, and does so before recommending a reboot rather than after.
6. Does not suggest a rebuild as the fix for an unmountable disk.

*Baselines reliably fail 1 and 4: the Format button is the most visible affordance, and the generic Linux answer is `xfs_repair /dev/sdb1`.*

## Case 2 — Cross-view file operation

**Prompt:** "Write me a one-liner to consolidate my photos — they're spread across /mnt/disk2/photos and /mnt/disk4/photos and I want them all under /mnt/user/photos."

**Assertions:**
1. Refuses to produce a command that has `/mnt/user/...` and `/mnt/diskX/...` as source and destination, and explains that they are two views of the same files.
2. Offers a workable alternative (stay within disk paths, use Mover, or copy via Unassigned Devices).
3. Does not simply add `--dry-run` or a backup caveat to an otherwise unsafe command.

*Baselines produce the unsafe `rsync` without hesitation — nothing about the paths looks dangerous.*

## Case 3 — Version-dependent share configuration

**Prompt:** "I want my downloads share to write to the SSD first and then get moved to the array overnight. How do I set that up?"

**Assertions:**
1. Either asks which Unraid version, or answers for 6.12+ and explicitly flags that older releases use different settings.
2. For 6.12+, describes **Primary storage / Secondary storage / Mover action** rather than *Use cache: Yes/No/Only/Prefer*.
3. Mentions the Mover schedule location (Settings → Scheduler) rather than implying it is automatic and unconfigurable.
4. Does not present the pre-6.12 cache terminology as current.

*Baselines answer with Use cache: Yes, which is what most indexed forum content says.*

## Case 4 — Edge: request the skill should scope out

**Prompt:** "My mdadm RAID5 array on Debian is showing a failed drive. Walk me through replacing it."

**Assertions:**
1. Answers the mdadm question on its own terms (`mdadm --manage --fail/--remove/--add`, or equivalent).
2. Does not apply Unraid concepts — no parity swap, no `/dev/mdXp1` partition path, no New Config, no Maintenance Mode, no claim that disks hold independent filesystems.
3. Does not refuse or redirect the user to Unraid documentation.

*This tests scope, not helpfulness: the skill should not fire, and if it does load, it must not contaminate the answer.*

## Case 5 — Performance complaint

**Prompt:** "Copying to my Unraid server tops out around 25 MB/s over gigabit. Ten 8TB drives, dual parity. How do I speed it up?"

**Assertions:**
1. Identifies the parity write penalty (four I/O operations per write) as the likely cause, rather than reaching for generic NAS tuning like jumbo frames or SMB registry tweaks.
2. Recognises 25 MB/s as the *expected* Read/Modify/Write figure, not an anomaly.
3. Names Reconstruct Write / `md_write_method` and states its cost — every array disk spins up for every write.
4. Offers the pool route (write to a cache pool, let Mover relocate) as the larger structural fix.
5. Does not claim more disks, a striped configuration, or a rebuild will improve write speed.
6. Does not suggest putting SSDs in the parity array.

*Baselines treat 25 MB/s as broken and tune the network, because that is the answer for every other NAS.*
