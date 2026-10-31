#!/bin/bash
# waits for the 1000t set, then: 5000t s42 pairs (urban_political, crowded_frontier), then instrumented 1000t pairs for FLW s43-46. Sequential; resumable by skipping existing outputs.
R=/data/vboxuser/Work/b_runs
until grep -q "BATCH1000_ALL_DONE" $R/batch1000_r2.log || grep -q "^STOP" $R/batch1000_r2.log; do sleep 30; done
grep -q "^STOP" $R/batch1000_r2.log && { echo "CHAIN_ABORT: 1000t batch stopped"; exit 1; }
for w in urban_political crowded_frontier; do for arm in base B; do
  L=p5000_${arm}_${w}_42; [ -s $R/out/$L.json ] && continue
  $R/go.sh $arm $w 42 5000 0 $L || { echo "STOP at $L"; exit 1; }
done; echo "WORLD5000_DONE $w"; done
for s in 43 44 45 46; do for arm in base B; do
  L=inst1000_${arm}_frontier_living_world_$s; [ -s $R/out/inst_$L.jsonl ] && continue
  W=frontier_living_world S=$s T=1000 L=$L $R/go3.sh $arm || { echo "STOP at $L"; exit 1; }
done; done
echo CHAIN_ALL_DONE
