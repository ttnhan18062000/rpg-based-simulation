#!/bin/bash
# GUARD move lifetimes, 4 worlds x 2 runs (a value when the pair matches). One simulation at a time.
# usage: measure.sh <label> [legacy]   `legacy` runs the pre-gate-4 completion logic (origin/main) on this tree.
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
HERE=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
ROOT=$HERE
ARM=$2
P=$HERE/agent-working/stored_artifacts/TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER/probes
# cd is REQUIRED: src/core/registries.py seeds content from the cwd-relative "data/content", so a different cwd silently measures a different content catalog.
cd "$HERE"
echo "== $1 ($ARM)"
for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
  for r in 1 2; do
    echo "-- $w run$r"; $PY $P/guard_move_lifetimes.py $ROOT $w 2000 $ARM 2>&1 | grep -E "^(GUARD-MOVES|HELD)|Error|Traceback" | cut -c1-900
  done
done
echo ALL-DONE
