#!/bin/bash
S=/tmp/claude-1000/scratch27
case $1 in arm1) R=$S/arm1;; arm2) R=$S/arm2;; arm3) R=$S/arm3;; arm4) R=$S/arm4;; arm5) R=$S/arm5;; esac
cd $R && /mnt/data/Working/rpg-based-simulation/.claude/worktrees/behavioral-5k-impl2/.venv/bin/python $S/chain_ms.py $R $2 5000 $3 $1 > $S/out/$1_$2_$3.out 2>&1
