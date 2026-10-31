#!/bin/bash
T=/data/vboxuser/Work/simq_probes
a=a25619971; d=d914bace7
while read lab sha key; do
  [ -s $T/out/$lab.done ] && continue
  $T/run_probe.sh $sha $key $lab > $T/out/$lab.runlog 2>&1 || { echo "PROBES_STOP at $lab"; exit 1; }
  grep PROBE_DONE $T/out/$lab.runlog
  echo ok > $T/out/$lab.done
done <<LIST
P1_a $a urban_political_seed123_500t
P1_d $d urban_political_seed123_500t
P2_a $a generated_frontier_3_42_seed456_200t
P2_d $d generated_frontier_3_42_seed456_200t
P3_a $a urban_political_seed42_500t
P3_d $d urban_political_seed42_500t
P4_a $a urban_political_selfmodel_execution_probe_seed42_200t
P4_d $d urban_political_selfmodel_execution_probe_seed42_200t
P1_d2 $d urban_political_seed123_500t
LIST
echo PROBES_ALL_DONE
