#!/bin/bash
# BRACKETING lifetimes (real issued tasks) and the forced-decision split (read-only), on this tree.
# One simulation at a time; the lifetime probe runs each world twice (value if matched).
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
ROOT=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
P=$ROOT/agent-working/staging_artifacts/TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION/probes
F=$ROOT/agent-working/stored_artifacts/TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK/probes
for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
  for r in 1 2; do
    echo "== lifetimes $w run$r"; $PY $P/bracketing_lifetimes.py $ROOT $w 2000 2>&1 | grep -E "^(BRACKETING|LONGEST)|Error|Traceback" | cut -c1-700
  done
done
for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
  echo "== forced-decision split $w"; $PY $F/forced_brain.py $ROOT $w 2000 2>&1 | grep -v "^EX" | grep -E "FORCED|calls|decision\.|Error|Traceback" | tr -d '\n' | cut -c1-900; echo
done
echo ALL-DONE
