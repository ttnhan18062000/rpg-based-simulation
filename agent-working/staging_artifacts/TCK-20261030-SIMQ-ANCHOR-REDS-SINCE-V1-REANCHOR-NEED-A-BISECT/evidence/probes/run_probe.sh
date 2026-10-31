#!/bin/bash
# usage: run_probe.sh <sha> <scenario_key> <label>   (tree: /data/vboxuser/Work/simq_probes/trees/<sha>); same wrapper as the sweep
SHA=$1; KEY=$2; LAB=$3; T=/data/vboxuser/Work/simq_probes
for i in 1 2 3 4 5 6 7 8 9 10; do m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] && break; sleep 60; done
[ "$m" -ge 3145728 ] || { echo "PROBE_STOP memory $m"; exit 3; }
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PYTHONPATH=$T/trees/$SHA PROBE_OUT=$T/out/$LAB.jsonl
cd $T/trees/$SHA; ST=$(date +%s)
systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 /data/vboxuser/Work/rpg-based-simulation/.venv/bin/python $T/probe2.py $KEY > $T/out/$LAB.stdout 2>&1
echo "PROBE_DONE $LAB rc=$? wall_s=$(( $(date +%s)-ST )) mem_kB=$m"
ls -dt $T/trees/$SHA/data/runs/* | head -1 > $T/out/$LAB.rundir
cp $T/trees/$SHA/data/calibration/$KEY/quality_report.json $T/out/$LAB.report.json 2>/dev/null
cp $(cat $T/out/$LAB.rundir)/run_manifest.json $T/out/$LAB.run_manifest.json 2>/dev/null
cp $(cat $T/out/$LAB.rundir)/quality_scores.jsonl $T/out/$LAB.quality_scores.jsonl 2>/dev/null
