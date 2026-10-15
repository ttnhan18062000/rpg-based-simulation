#!/bin/bash
tree=$1; world=$2; seed=$3
d=/mnt/data/scratch-impl2-probe/deathproof3/$tree; mkdir -p $d
cd /mnt/data/Working/rpg-based-simulation/.claude/worktrees/$tree && PYTHONHASHSEED=0 PYTHONPATH=. /mnt/data/scratch-impl2-venv/bin/python /tmp/death_proof.py $world $seed 5000 $d/${world}_$seed.json > $d/${world}_$seed.log 2>&1
