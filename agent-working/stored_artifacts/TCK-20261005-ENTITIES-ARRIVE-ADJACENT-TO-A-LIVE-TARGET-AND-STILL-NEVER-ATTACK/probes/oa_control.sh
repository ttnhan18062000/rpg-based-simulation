#!/bin/bash
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
S=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/4681963b-938f-48c6-9217-e11f2d9c7a12/scratchpad
OLD=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/lane-a-tactical-path-batch
for w in dungeon_crawl urban_political; do
  echo "== BEFORE (#342 head) $w"; $PY $S/combat_volume.py $OLD $w 2000 2>&1 | grep "^COMBAT-VOLUME"
done
echo ALL-DONE
