#!/bin/bash
R=/data/vboxuser/Work/b_runs
m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "STOP mem $m"; exit 3; }
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PYTHONPATH=$R/trees/$1
cd $R/trees/$1; ST=$(date +%s)
systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 /data/vboxuser/Work/rpg-based-simulation/.venv/bin/python $R/inst.py ${W:-crowded_frontier} ${S:-42} ${T:-1000} $R/out/inst_${L:-$1}.jsonl
echo "DONE inst_${L:-$1} wall_s=$(( $(date +%s)-ST )) mem_kB=$m"
