#!/bin/bash
# usage: job2.sh <arm> <rep> <world> <seed>
SP=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-rpg/ebe7c2c8-748a-49e1-a005-a14795e94964/scratchpad
if [ "$1" = new ]; then R=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/regrowth-wiring; else R=$SP/base; fi
cd $R && /mnt/data/Working/rpg-based-simulation/.claude/worktrees/behavioral-5k-impl2/.venv/bin/python $SP/regrow_ms.py $R $3 1500 $4 "$1$2" > $SP/out2/$1_$2_$3_$4.out 2>&1
