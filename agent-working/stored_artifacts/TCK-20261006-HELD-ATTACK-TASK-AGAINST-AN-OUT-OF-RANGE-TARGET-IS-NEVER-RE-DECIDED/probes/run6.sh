#!/bin/bash
S=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/81a7dd61-eecd-4508-bf3b-49e8a0c4f583/scratchpad
W=/mnt/data/Working/rpg-based-simulation/.claude/worktrees
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
exec > $S/out6.txt 2>&1
for arm in before after; do
  if [ $arm = before ]; then R=$W/remeasure-trauma-panic; else R=$W/held-attack-oor; fi
  cd $R
  for cfg in "crowded_frontier 2000 42" "frontier_living_world 2000 42"; do
    echo "##### $arm $cfg"; $PY $S/oor_streak.py $R $cfg 2>&1 | grep -E "^CORPUS|Traceback|Error" | python3 -c "
import sys,json
for l in sys.stdin:
    if l.startswith('CORPUS'):
        d=json.loads(l.split(' ',4)[4]); print({k:d.get(k,0) for k in ('oor_max_consecutive_per_entity','oor_streaks_ge3','oor_open_streaks_ge3_at_end','execute_attack.total')})
    else: print(l)"
  done
done
echo ALL-DONE
