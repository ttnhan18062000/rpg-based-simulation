#!/bin/bash
# post-merge check (ruling 7): base2 = origin/main c5139b410, B2 = merged B. s42 1000t x 3 worlds (hs0), then merged B crowded_frontier s42 at hs1,2,3. Then instrumented pairs for moved hashes. Sequential, resumable.
R=/data/vboxuser/Work/b_runs
for w in frontier_living_world urban_political crowded_frontier; do for arm in base2 B2; do
  L=post_${arm}_${w}_42_hs0; [ -s $R/out/$L.json ] && continue
  $R/go.sh $arm $w 42 1000 0 $L || { echo "CHAIN4_STOP at $L"; exit 1; }
done; done
for hs in 1 2 3; do L=post_B2_crowded_frontier_42_hs$hs; [ -s $R/out/$L.json ] && continue
  $R/go.sh B2 crowded_frontier 42 1000 $hs $L || { echo "CHAIN4_STOP at $L"; exit 1; }
done
echo CHAIN4_RUNS_DONE
for w in frontier_living_world urban_political crowded_frontier; do
  a=$R/out/post_base2_${w}_42_hs0.json; b=$R/out/post_B2_${w}_42_hs0.json
  [ "$(python3 -c "import json;print(json.load(open('$a'))['final_hash']==json.load(open('$b'))['final_hash'])")" = "True" ] && continue
  for arm in base2 B2; do L=postinst_${arm}_${w}_42; [ -s $R/out/inst_$L.jsonl ] && grep -q '"k": "final"' $R/out/inst_$L.jsonl && continue
    W=$w S=42 T=1000 L=$L $R/go3.sh $arm || { echo "CHAIN4_STOP at $L"; exit 1; }
  done
done
echo CHAIN4_ALL_DONE
