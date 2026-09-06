---
description: Triage an Unraid server problem, capturing evidence before it is lost
argument-hint: [what is wrong, e.g. "disk 5 unmountable after power cut"]
---

Triage this Unraid problem: **$ARGUMENTS**

Work in this order. The ordering is the point — `/var/log` is a RAM disk, so a reboot destroys the evidence, and several Unraid recovery paths become unavailable once the wrong button has been pressed.

1. **Preserve evidence first.** Before suggesting any reboot, array stop, or repair, tell the user to capture ***Tools → Diagnostics*** (or run `diagnostics`, which writes to `/boot/logs`). Capture with the array started in normal mode where possible. If they have already rebooted, say what was lost and check for `/boot/logs/syslog-previous`.

2. **Establish the facts before advising.** Ask for, or read from the diagnostics: the Unraid version; whether the array is started, stopped, or in Maintenance Mode; which disks show a red X, an orange triangle, or "unmountable"; whether parity is single or dual and whether the last parity check was clean; and the filesystem on any affected disk. Do not give a procedure that depends on any of these while still guessing at them.

3. **Classify before acting.** Decide which of these it is, because the correct first move differs and some are mutually exclusive:
   - unmountable but not disabled → filesystem repair, never Format
   - disabled (red X) and emulated → verify and repair the *emulated* disk before any rebuild
   - more failures than parity covers → stop all writes, do not rebuild, escalate
   - not a disk problem at all → boot, network, Docker, VM, or licensing

4. **Check drive health** before recommending anything that stresses the array. SMART attributes 5, 187, 197, 198 and the UDMA CRC count (199), plus `smartctl -t long` on the drives involved in a rebuild.

5. **Then give the procedure**, following the skill's output contract: name the Unraid version it applies to, name the array state each step needs, and flag the irreversible step and what it destroys.

6. **Escalate honestly.** If the situation is ambiguous, or if more disks are affected than parity can cover, say so and point at the Unraid forums with the diagnostics ZIP attached rather than guessing.

Load `skills/managing-unraid-servers` references as needed — do not work from memory on device paths or version-specific procedures.
