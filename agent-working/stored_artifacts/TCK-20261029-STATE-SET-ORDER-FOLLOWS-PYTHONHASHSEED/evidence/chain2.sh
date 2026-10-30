#!/bin/bash
# instrumented 1000t pairs: urban_political s42-46, crowded_frontier s43-46 (crowded s42 already has one). Sequential, resumable.
R=/data/vboxuser/Work/b_runs
for pair in urban_political:42 urban_political:43 urban_political:44 urban_political:45 urban_political:46 crowded_frontier:43 crowded_frontier:44 crowded_frontier:45 crowded_frontier:46; do
  w=${pair%%:*}; s=${pair##*:}
  for arm in base B; do
    L=inst1000_${arm}_${w}_$s; [ -s $R/out/inst_$L.jsonl ] && grep -q '"k": "final"' $R/out/inst_$L.jsonl && continue
    W=$w S=$s T=1000 L=$L $R/go3.sh $arm || { echo "CHAIN2_STOP at $L"; exit 1; }
  done
done
echo CHAIN2_ALL_DONE
