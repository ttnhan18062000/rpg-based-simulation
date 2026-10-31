#!/bin/bash
# ruling 5, 1000t set: worlds smallest first x seeds 42-46 x {base,B}, PYTHONHASHSEED=0, sequential, memory-checked by go.sh, resumable, stops on first failure. Names p1000_<arm>_<world>_<seed>.json
R=/data/vboxuser/Work/b_runs
for w in ${WORLDS:-frontier_living_world urban_political crowded_frontier}; do for s in 42 43 44 45 46; do for arm in base B; do
  L=p1000_${arm}_${w}_${s}
  [ -s $R/out/$L.json ] && continue
  $R/go.sh $arm $w $s 1000 0 $L || { echo "STOP at $L"; exit 1; }
done; done; echo "WORLD_DONE $w"; done
echo BATCH1000_ALL_DONE
