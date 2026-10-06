#!/bin/bash
# Before (7daef8075) vs after (fix, uncommitted) arms. One sim at a time. Sentinel ALL-DONE.
S=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/81a7dd61-eecd-4508-bf3b-49e8a0c4f583/scratchpad
W=/mnt/data/Working/rpg-based-simulation/.claude/worktrees
BEFORE=$W/remeasure-trauma-panic
AFTER=$W/trauma-panic-correction
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
P=$AFTER/agent-working/stored_artifacts/TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK/probes
exec > $S/out2.txt 2>&1
for arm in before after; do
  if [ $arm = before ]; then R=$BEFORE; PT=$P/panic_terms.py; else R=$AFTER; PT=$S/panic_terms_after.py; fi
  cd $R
  echo "=== ARM $arm $(git rev-parse --short HEAD) $R"
  for w in crowded_frontier frontier_living_world; do
    for run in 1 2; do
      echo "##### $arm $w run$run forced_brain";  $PY $P/forced_brain.py $R $w 2000 | grep -v '^EX' | cut -c1-200
      echo "##### $arm $w run$run panic_terms";   $PY $PT $R $w 2000 | grep -v '^EX' | cut -c1-200
      echo "##### $arm $w run$run combat_volume"; $PY $P/combat_volume.py $R $w 2000 | cut -c1-500
    done
  done
done
echo ALL-DONE
