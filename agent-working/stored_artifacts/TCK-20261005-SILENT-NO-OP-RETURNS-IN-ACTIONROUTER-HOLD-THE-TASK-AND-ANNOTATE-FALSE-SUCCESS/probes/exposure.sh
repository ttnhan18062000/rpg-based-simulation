#!/bin/bash
# Corpus exposure to posture-withheld dispatches. Pass a label as $1 (before|after). One simulation at a time, each run twice.
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
ROOT=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
P=$ROOT/agent-working/staging_artifacts/TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS/probes
echo "== $1"
for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
  for r in 1 2; do
    echo "-- $w run$r"; $PY $P/withheld_exposure.py $ROOT $w 2000 2>&1 | grep -E "^WITHHELD-EXPOSURE|Error|Traceback"
  done
done
echo ALL-DONE
