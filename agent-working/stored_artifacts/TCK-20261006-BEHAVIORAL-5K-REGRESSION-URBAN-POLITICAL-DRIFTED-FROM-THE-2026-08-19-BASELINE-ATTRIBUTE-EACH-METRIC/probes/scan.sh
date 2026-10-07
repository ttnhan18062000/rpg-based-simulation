#!/bin/bash
# usage: scan.sh <idx...>  (1-based idx into first-parent list, oldest=1)
S=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation/793b1982-f9e8-4fd6-b9f3-b1e5b42a728d/scratchpad
cd /mnt/data/Working/rpg-based-simulation/.claude/worktrees/b5k-d2816ab6c
git log --first-parent --reverse --format=%h d2816ab6c..origin/main > $S/commits.txt
for i in "$@"; do
  c=$(sed -n "${i}p" $S/commits.txt)
  git checkout -q -f --detach $c || { echo "$i $c CHECKOUT_FAIL"; continue; }
  r=$(PYTHONPATH=. /mnt/data/Working/rpg-based-simulation/.venv/bin/python $S/probe5k.py audit $S/scan_$c.json 2>&1 | tail -1)
  echo "$i $c $r" >> $S/scan.log
done
echo DONE >> $S/scan.log
