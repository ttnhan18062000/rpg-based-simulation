#!/bin/bash
# usage: bisect2.sh <lo> <hi> <threshold>  ; quest<thr => good
S=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation/793b1982-f9e8-4fd6-b9f3-b1e5b42a728d/scratchpad
cd /mnt/data/Working/rpg-based-simulation/.claude/worktrees/b5k-d2816ab6c
lo=$1; hi=$2; thr=$3
while [ $((hi-lo)) -gt 1 ]; do
  mid=$(((lo+hi)/2)); c=$(sed -n "${mid}p" $S/commits.txt)
  git checkout -q -f --detach $c
  r=$(PYTHONPATH=. /mnt/data/Working/rpg-based-simulation/.venv/bin/python $S/probe5k.py audit $S/scan_$c.json 2>&1 | tail -1)
  echo "$mid $c $r" >> $S/bisect2.log
  q=$(echo "$r" | sed -E "s/.*'quest_active': ([0-9.]+).*/\1/")
  if python3 -c "import sys;sys.exit(0 if float('$q')<$thr else 1)"; then lo=$mid; else hi=$mid; fi
done
echo "FIRST_BAD($1,$2) $hi $(sed -n "${hi}p" $S/commits.txt)" >> $S/bisect2.log
