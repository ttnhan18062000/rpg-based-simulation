#!/bin/bash
# usage: go.sh <tree: base|B> <world> <seed> <ticks> <hashseed> <label> ; waits for MemAvailable >= 3 GB
R=/data/vboxuser/Work/b_runs
for i in 1 2 3 4 5 6 7 8 9 10; do m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] && break; echo "MEMLOW $m, waiting" >&2; sleep 60; done
[ "$m" -ge 3145728 ] || { echo "STOP memory stays low: $m kB"; exit 3; }
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=$5 RPG_MEASURE_CACHE=$R/cache PYTHONPATH=$R/trees/$1
cd $R/trees/$1; S=$(date +%s)
systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 /data/vboxuser/Work/rpg-based-simulation/.venv/bin/python $R/arm_child.py $2 $3 $4 $R/out/$6.json
echo "DONE $6 wall_s=$(( $(date +%s)-S )) mem_kB=$m"
