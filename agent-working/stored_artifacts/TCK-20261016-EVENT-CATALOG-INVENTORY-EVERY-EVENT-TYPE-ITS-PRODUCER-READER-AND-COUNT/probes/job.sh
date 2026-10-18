#!/bin/bash
w=$1; s=$2
cd /mnt/data/Working/rpg-based-simulation/.claude/worktrees/evcat && PYTHONHASHSEED=0 PYTHONPATH=. /mnt/data/scratch-impl2-venv/bin/python /mnt/data/scratch-evcat/child.py $w $s 5000 /mnt/data/scratch-evcat/out/${w}_$s.json > /mnt/data/scratch-evcat/out/${w}_$s.log 2>&1
