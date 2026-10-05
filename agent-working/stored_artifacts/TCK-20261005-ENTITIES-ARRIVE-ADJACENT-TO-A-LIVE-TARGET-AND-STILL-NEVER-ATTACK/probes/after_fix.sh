#!/bin/bash
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
S=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/4681963b-938f-48c6-9217-e11f2d9c7a12/scratchpad
R=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
for w in crowded_frontier frontier_living_world; do
  echo "=== $w dispatch"; $PY $S/dispatch_probe.py $R $w 2000 2>&1 | grep -A6 "DISPATCH-PROBE" | grep -v "^ROW" | cut -c1-200
done
echo "=== crowded_frontier adjacency"; $PY $S/adj_probe.py $R crowded_frontier 2000 2>&1 | grep -A12 "ADJ-PROBE" | grep -v "^SAMPLE" | cut -c1-200
echo ALL-DONE
