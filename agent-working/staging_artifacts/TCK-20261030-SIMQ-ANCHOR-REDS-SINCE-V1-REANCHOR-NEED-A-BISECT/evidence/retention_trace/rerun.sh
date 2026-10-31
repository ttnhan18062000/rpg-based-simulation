#!/bin/bash
# one re-run of urban_political s42 2000t at d914bace7 with the extended probe6 (capacity/escalation/resume logs, work_kind), output in out_rerun/
T=/data/vboxuser/Work/simq_retention
for i in 1 2 3 4 5 6 7 8 9 10; do m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] && break; sleep 60; done
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PYTHONPATH=$T/trees/d914bace7 PROBE_OUT=$T/out_rerun/urban_political_s42_d914bace7.jsonl
cd $T/trees/d914bace7; ST=$(date +%s)
systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 /data/vboxuser/Work/rpg-based-simulation/.venv/bin/python $T/probe6.py urban_political 42 2000 > $T/out_rerun/stdout.txt 2>&1
echo "RERUN_DONE rc=$? wall_s=$(( $(date +%s)-ST )) mem_kB=$m at=$(date +%H:%M:%S)"
