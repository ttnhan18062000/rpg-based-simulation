#!/bin/bash
# usage: run1.sh arm world
cd /mnt/data/Working/rpg-based-simulation/.claude/worktrees/spawn-faction-impl2
S=/tmp/claude-1000/-mnt-data-Working/8ea8f4de-cf36-4e62-9986-b49e98bc85aa/scratchpad
[ "$1" = before ] && export NOFIX=1
PYTHONPATH=. /mnt/data/Working/rpg-based-simulation/.venv/bin/python $S/zones_ab.py $2 10000 $S/arms/$1/$2.jsonl > $S/arms/$1/$2.log 2>&1
