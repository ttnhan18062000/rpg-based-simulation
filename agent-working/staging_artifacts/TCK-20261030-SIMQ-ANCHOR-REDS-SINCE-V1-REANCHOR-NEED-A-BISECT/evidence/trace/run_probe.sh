#!/bin/bash
# usage: run_probe.sh <sha>  (archive already exists under simq_bisect/<sha>)
SHA=$1; B=/data/vboxuser/Work/simq_bisect; T=/data/vboxuser/Work/simq_trace
cd $B/$SHA || exit 1
echo "MemAvailable_kB $(awk '/MemAvailable/{print $2}' /proc/meminfo)"
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 RPG_MEASURE_CACHE=$B/cache
STARTED=$(date +%s)
systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 /data/vboxuser/Work/rpg-based-simulation/.venv/bin/python $T/probe.py $T/$SHA.jsonl 2>&1 | tail -15
echo "TRACE_END $SHA wall=$(( $(date +%s)-STARTED ))"
