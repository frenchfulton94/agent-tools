# Trigger battery: managing-unraid-servers

## Should trigger (10)

1. "disk3 is showing unmountable in the webgui and it wants me to format it, is that right?"
2. "I want to swap my 4TB data drive for a 12TB one but my parity is only 8TB."
3. "What's the safest way to move my appdata off the cache pool before I reformat it?"
4. "My tower won't come up after I added a second HBA — it gets to the login prompt but no web interface."
5. "Been running a media server on this box for two years, want to add a ZFS pool for VMs without disturbing the array. Where do I start?"
6. "The mover ran overnight but appdata is still sitting on cache. Why?"
7. "Parity check finished with 47 sync errors. Should I be worried?"
8. "Can you write me a script to rsync /mnt/disk4/photos into /mnt/user/photos and then delete the originals?"
9. "How do I get to my NAS webgui from work without opening port 443 on my router?"
10. "my docker.img filled up and now nothing starts. do i lose all my container configs if i delete it"

## Should not trigger (10) — near-misses

1. "My mdadm RAID5 array is degraded, how do I rebuild it?" (generic Linux software RAID, different model entirely)
2. "How do I expand a ZFS pool on TrueNAS Scale?" (ZFS, but a different NAS OS with different tooling)
3. "Set up a Docker container for Plex on my Ubuntu server." (Docker, no Unraid)
4. "What's the difference between RAID 5 and RAID 6?" (storage theory question, no server to manage)
5. "Recommend a NAS for a home media library — should I build or buy?" (purchasing advice, not administration)
6. "Fix this Tailscale ACL policy file." (Tailscale, but the config is the subject, not an Unraid server)
7. "My Synology says a drive is degraded, what now?" (different vendor, different procedures)
8. "How does XFS journaling work?" (filesystem internals, not an operation on a server)
9. "Write a bash script that emails me when a disk hits 90% full." (generic scripting, no Unraid specifics)
10. "Compare Proxmox and ESXi for a home lab." (hypervisor comparison; Unraid runs VMs but isn't the subject)

## Notes on the negatives

The valuable ones here are 1, 2, and 7 — they share vocabulary (array, degraded, rebuild, ZFS pool) with real Unraid work but describe systems where this skill's device paths, parity model, and repair procedures would be actively wrong. Negative 6 tests that a tool name mentioned in the skill doesn't pull it in on its own.
