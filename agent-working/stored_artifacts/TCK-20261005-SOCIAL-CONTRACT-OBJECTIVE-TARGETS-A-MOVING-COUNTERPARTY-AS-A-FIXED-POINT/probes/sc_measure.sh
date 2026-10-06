#!/bin/bash
# cd is REQUIRED: content seeds from the cwd-relative data/content.
R=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
cd "$R" || exit 1
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
S=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/c3c03123-6c20-4694-bb97-f41faaa98a72/scratchpad
echo "== branch $(git branch --show-current) $(git rev-parse --short HEAD)"
for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
  echo "-- $w"; $PY $S/social_contract_exposure.py $R $w 2000 2>&1 | grep -E "^SOCIAL-CONTRACT-EXPOSURE|Error|Traceback|No such file" | cut -c1-2500
done
echo ALL-DONE
