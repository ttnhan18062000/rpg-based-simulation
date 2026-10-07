#!/bin/bash
S=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/81a7dd61-eecd-4508-bf3b-49e8a0c4f583/scratchpad
W=/mnt/data/Working/rpg-based-simulation/.claude/worktrees
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
exec > $S/out5.txt 2>&1
for arm in before after; do
  if [ $arm = before ]; then R=$W/remeasure-trauma-panic; else R=$W/held-attack-oor; fi
  cd $R
  echo "=== ARM $arm $(git rev-parse --short HEAD) $R"
  for cfg in "crowded_frontier 2000 42" "frontier_living_world 2000 42" "campaign 70 42" "campaign 70 1337"; do
    for run in 1 2; do
      echo "##### $arm $cfg run$run"; $PY $S/corpus_probe.py $R $cfg 2>&1 | grep -E "^CORPUS|Traceback|Error" | cut -c1-900
    done
  done
done
echo ALL-DONE
