#!/bin/bash
# Held-task exposure per action kind, 4 worlds x 2 runs (a value when the pair matches). One simulation at a time.
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
ROOT=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
P=$ROOT/agent-working/stored_artifacts/TCK-20261005-ACTION-HANDLERS-MAY-RETURN-BARE-NO-OPS-THAT-HOLD-THE-TASK/probes
# cd is REQUIRED: src/core/registries.py seeds content from the cwd-relative "data/content", so a different cwd silently measures a different content catalog.
cd "$ROOT"
echo "== $1"
for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
  for r in 1 2; do
    echo "-- $w run$r"; $PY $P/handler_exposure.py $ROOT $w 2000 2>&1 | grep -E "^HANDLER-EXPOSURE|Error|Traceback|No such file"
  done
done
echo ALL-DONE
