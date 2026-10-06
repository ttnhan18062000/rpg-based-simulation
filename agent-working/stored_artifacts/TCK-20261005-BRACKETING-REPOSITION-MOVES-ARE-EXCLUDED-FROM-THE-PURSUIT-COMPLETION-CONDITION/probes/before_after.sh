#!/bin/bash
# Live-mover dead-target holds, legacy completion logic vs the fix. One simulation at a time; each world twice per arm.
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
ROOT=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
P=$ROOT/agent-working/staging_artifacts/TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION/probes
for arm in legacy fixed; do
  for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
    for r in 1 2; do
      echo "== $arm $w run$r"
      if [ "$arm" = legacy ]; then A=legacy; else A=""; fi
      $PY $P/target_move_lifetimes.py $ROOT $w 2000 $A 2>&1 | grep -E "^(TARGET-MOVES|HELD)|Error|Traceback" | cut -c1-1500
    done
  done
done
echo ALL-DONE
