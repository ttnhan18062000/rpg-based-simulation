#!/bin/bash
# usage: runab.sh arm world
cd /mnt/data/Working/rpg-based-simulation/.claude/worktrees/symmetric-legality-impl2
SC=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation/3f65a0a8-5b41-4704-82d5-c64a0d15d761/scratchpad
[ "$1" = before ] && export BEFORE=1
PYTHONPATH=. /mnt/data/Working/rpg-based-simulation/.venv/bin/python $SC/combat_ab.py $2 ${TICKS:-10000} $SC/arms/$1/$2.json > $SC/arms/$1/$2.log 2>&1
