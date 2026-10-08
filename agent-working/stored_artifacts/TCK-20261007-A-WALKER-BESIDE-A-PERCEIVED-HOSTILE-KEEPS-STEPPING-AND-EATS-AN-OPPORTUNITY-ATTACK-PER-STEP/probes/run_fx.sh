#!/bin/bash
S=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-rpg/83885e22-dae2-4b60-a6c3-d4354306a159/scratchpad
W=/mnt/data/Working/rpg-based-simulation/.claude/worktrees
cd $W/$1 && /mnt/data/Working/rpg-based-simulation/.venv/bin/python $S/oa_fix_ms.py $W/$1 $3 1500 $4 $2 > $S/fx_$2_$3_$4.out 2>&1
