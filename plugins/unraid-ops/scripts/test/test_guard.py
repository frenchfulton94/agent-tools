import json, subprocess
S="scripts/guard_destructive_storage.py"
cases=[
 ("cp -r /mnt/disk2/photos/ /mnt/user/photos/","deny"),
 ("rsync -av /mnt/disk2/photos/ /mnt/disk4/photos/","allow"),
 ("rsync -av /mnt/user/media/ /mnt/user/backup/","allow"),
 ("ls /mnt/user && ls /mnt/disk1","allow"),
 ("grep -r '/mnt/user' /mnt/disk1/notes.txt","allow"),
 ("xfs_repair -v /dev/sdb","deny"),
 ("xfs_repair /dev/md1p1","allow"),
 ("xfs_repair -L /dev/md1p1","allow"),
 ("xfs_repair -L /dev/sdb1","ask"),
 ("dd bs=1M if=/dev/zero of=/dev/md1p1 status=progress","allow"),
 ("dd if=/dev/zero of=/dev/sdc bs=1M","deny"),
 ("mkfs.xfs /dev/sdd1","ask"),
 ("btrfs check --repair /dev/sde1","ask"),
 ("btrfs scrub start /mnt/disk3","allow"),
 ("zpool destroy tank","ask"),
 ("zpool scrub tank","allow"),
 ("zpool status -v cache","allow"),
 ("echo hello world","allow"),
 ("smartctl -t long /dev/sdb","allow"),
 ("wipefs -a /dev/sdf","ask"),
 ("cd /mnt/user/appdata && tar czf backup.tgz .","allow"),
 ("mv /mnt/user/downloads/x /mnt/disk3/media/","deny"),
]
bad=0
for cmd,exp in cases:
    p=subprocess.run(["python3",S],input=json.dumps({"tool_name":"Bash","tool_input":{"command":cmd}}),capture_output=True,text=True)
    out=p.stdout.strip()
    got="allow" if not out else json.loads(out)["hookSpecificOutput"]["permissionDecision"]
    ok = got==exp
    if not ok: bad+=1
    print(("PASS " if ok else "FAIL ")+f"[{got:5}/{exp:5}] rc={p.returncode} {cmd[:52]}")
print("\nfailures:",bad)
