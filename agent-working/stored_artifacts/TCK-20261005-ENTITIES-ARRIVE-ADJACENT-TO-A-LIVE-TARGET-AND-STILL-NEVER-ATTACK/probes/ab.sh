#!/bin/bash
PY=/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python
P=/tmp/claude-1000/-home-u24desktop-Working-rpg-based-simulation/4681963b-938f-48c6-9217-e11f2d9c7a12/scratchpad/obj_probe.py
for world in crowded_frontier frontier_living_world; do
  for arm in control fixed; do
    $PY $P ab_$arm $world 2000 $arm > /dev/null 2>&1
    echo "done $arm $world"
  done
done
echo ALL-DONE
