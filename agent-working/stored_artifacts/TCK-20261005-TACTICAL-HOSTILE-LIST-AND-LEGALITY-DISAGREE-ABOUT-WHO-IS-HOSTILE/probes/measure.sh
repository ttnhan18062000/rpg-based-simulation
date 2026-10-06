#!/bin/bash
# Hostility-predicate comparison. One simulation at a time; each world run twice (value if matched).
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
ROOT=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace
P=$ROOT/agent-working/staging_artifacts/TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE/probes
for w in crowded_frontier frontier_living_world urban_political dungeon_crawl; do
  for r in 1 2; do
    echo "== $w run$r"; $PY $P/hostility_probe.py $ROOT $w 2000 2>&1 | grep -E "^HOSTILITY-PROBE|^ROW|Error|Traceback" | cut -c1-420
  done
done
echo ALL-DONE
