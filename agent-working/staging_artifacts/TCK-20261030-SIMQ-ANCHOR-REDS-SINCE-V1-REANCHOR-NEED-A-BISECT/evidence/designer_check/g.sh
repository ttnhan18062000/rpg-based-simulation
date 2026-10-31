#!/bin/bash
T=/data/vboxuser/Work/simq_probes
export PROBE=probe4.py
$T/run_probe_x.sh a25619971 urban_political_seed42_2000t D4_a > $T/out/D4_a.runlog 2>&1; grep PROBE_DONE $T/out/D4_a.runlog
$T/run_probe_x.sh d914bace7 urban_political_seed42_2000t D4_d > $T/out/D4_d.runlog 2>&1; grep PROBE_DONE $T/out/D4_d.runlog
export PROBE=probe5.py
$T/run_probe_x.sh d914bace7 urban_political_seed123_500t P1e10_d > $T/out/P1e10_d.runlog 2>&1; grep PROBE_DONE $T/out/P1e10_d.runlog
echo G_ALL_DONE
