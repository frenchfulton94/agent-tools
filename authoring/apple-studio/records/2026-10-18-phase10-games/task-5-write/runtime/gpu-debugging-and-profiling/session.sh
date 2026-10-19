#!/bin/bash
cd "$(dirname "$0")"
id=$(gpudebug -q -t draw.gputrace -c "list" | sed -n 's/^Session \([0-9]*\) created\./\1/p')
echo "id=$id"
gpudebug -s "$id" -c "status" | head -4
gpudebug -s "$id" -c "go /commands/cb0/grp0/re0/grp0/draw0" -c "info pipeline" | head -4
gpudebug --terminate "$id"
