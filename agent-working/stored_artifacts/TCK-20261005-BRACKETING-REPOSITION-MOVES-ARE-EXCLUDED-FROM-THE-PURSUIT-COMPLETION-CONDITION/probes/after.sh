#!/bin/bash
# After-change measurement (target-carrying move lifetimes, 4 worlds x 2 runs) then the scoped regression.
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
ROOT=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
P=$ROOT/agent-working/staging_artifacts/TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION/probes
for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
  for r in 1 2; do
    echo "== after $w run$r"; $PY $P/target_move_lifetimes.py $ROOT $w 2000 2>&1 | grep -E "^TARGET-MOVES|Error|Traceback" | cut -c1-1500
  done
done
cd $ROOT || exit 1
echo "== regression"
$PY -m pytest tests/unit/actions tests/unit/combat tests/unit/engine tests/unit/movement tests/unit/tactical tests/mechanic_scenarios tests/architecture -q -m "not slow" -p no:cacheprovider 2>&1 | tail -6
echo ALL-DONE
