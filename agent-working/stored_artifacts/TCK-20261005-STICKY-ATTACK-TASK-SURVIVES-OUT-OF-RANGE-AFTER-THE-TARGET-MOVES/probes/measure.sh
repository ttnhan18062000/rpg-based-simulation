#!/bin/bash
# Pre-change OUT_OF_RANGE measurement. One simulation at a time; each world run twice (value if matched).
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
ROOT=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
P=$ROOT/agent-working/staging_artifacts/TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES/probes
for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
  for r in 1 2; do
    echo "== $w run$r"; $PY $P/oor_probe.py $ROOT $w 2000 2>&1 | grep -E "^OOR-PROBE|Error|Traceback"
  done
done
echo ALL-DONE
