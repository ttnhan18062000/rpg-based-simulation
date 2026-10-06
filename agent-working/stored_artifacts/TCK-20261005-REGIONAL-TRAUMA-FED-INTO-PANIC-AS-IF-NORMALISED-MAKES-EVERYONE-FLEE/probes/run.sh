#!/bin/bash
# Read-only re-measure on b15fef405. One sim at a time. Output -> out.txt, ALL-DONE sentinel at end.
S=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/81a7dd61-eecd-4508-bf3b-49e8a0c4f583/scratchpad
ROOT=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/remeasure-trauma-panic
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
P=$ROOT/agent-working/stored_artifacts/TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK/probes
cd $ROOT
exec > $S/out.txt 2>&1
git rev-parse --short HEAD
for w in crowded_frontier frontier_living_world; do
  for run in 1 2; do
    echo "##### $w run$run forced_brain";  $PY $P/forced_brain.py $ROOT $w 2000 | cut -c1-240
    echo "##### $w run$run panic_terms";   $PY $P/panic_terms.py $ROOT $w 2000 | cut -c1-240
    echo "##### $w run$run combat_volume"; $PY $P/combat_volume.py $ROOT $w 2000 | cut -c1-600
    echo "##### $w run$run trauma_final";  $PY $P/trauma_ticks.py $ROOT $w 2000 | tail -1 | cut -c1-400
  done
  echo "##### $w CONTROL trauma-off forced_brain";  $PY $S/forced_brain_ctrl.py $ROOT $w 2000 | cut -c1-240
  echo "##### $w CONTROL trauma-off panic_terms";   $PY $S/panic_terms_ctrl.py $ROOT $w 2000 | cut -c1-240
done
echo "##### CONTROL combat_volume dungeon_crawl (nonzero expected)"
$PY $P/combat_volume.py $ROOT dungeon_crawl 2000 | cut -c1-600
echo ALL-DONE
