#!/bin/bash
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
NEW=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
P=$NEW/agent-working/staging_artifacts/TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK/probes
OLD=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/base-control-544b
for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
  echo "== CONTROL main-544b $w"; $PY $P/combat_volume.py $OLD $w 2000 2>&1 | grep "^COMBAT-VOLUME"
  echo "== FIX run1 $w"; $PY $P/combat_volume.py $NEW $w 2000 2>&1 | grep "^COMBAT-VOLUME"
  echo "== FIX run2 $w"; $PY $P/combat_volume.py $NEW $w 2000 2>&1 | grep "^COMBAT-VOLUME"
done
echo "== FLEE-GATE (fix tree)"
for w in crowded_frontier frontier_living_world; do
  echo "-- brain_adj $w"; $PY $P/brain_adj.py $NEW $w 2000 2>&1 | tail -15 | cut -c1-220
  echo "-- panic_terms $w"; $PY $P/panic_terms.py $NEW $w 2000 2>&1 | tail -15 | cut -c1-220
done
echo ALL-DONE
