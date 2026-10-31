#!/bin/bash
# usage: run6.sh   -- 30 runs, resumable (a .done marker per run), sequential, MemAvailable >= 3 GB before each, stops cleanly at 22:00. Trees: $T/trees/<sha> (git archive).
T=/data/vboxuser/Work/simq_retention; a=a25619971; d=d914bace7
order="urban_political:42:$d urban_political:42:$a urban_political:43:$a urban_political:43:$d urban_political:44:$a urban_political:44:$d urban_political:45:$a urban_political:45:$d urban_political:46:$a urban_political:46:$d"
for w in crowded_frontier frontier_living_world; do for s in 42 43 44 45 46; do order="$order $w:$s:$a $w:$s:$d"; done; done
for spec in $order; do
  IFS=: read w s sha <<< "$spec"; lab=${w}_s${s}_$sha
  [ -f $T/out/$lab.done ] && continue
  [ "$(date +%H%M)" -ge 2200 ] && { echo "RETENTION_STOP deadline 22:00 before $lab"; exit 4; }
  for i in 1 2 3 4 5 6 7 8 9 10; do m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] && break; sleep 60; done
  [ "$m" -ge 3145728 ] || { echo "RETENTION_STOP memory $m before $lab"; exit 3; }
  export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PYTHONPATH=$T/trees/$sha PROBE_OUT=$T/out/$lab.jsonl
  cd $T/trees/$sha; ST=$(date +%s)
  systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 /data/vboxuser/Work/rpg-based-simulation/.venv/bin/python $T/probe6.py $w $s 2000 > $T/out/$lab.stdout 2>&1
  rc=$?; echo "RUN_DONE $lab rc=$rc wall_s=$(( $(date +%s)-ST )) mem_kB=$m at=$(date +%H:%M:%S)"
  [ $rc -eq 0 ] && echo ok > $T/out/$lab.done || { echo "RETENTION_STOP rc=$rc at $lab"; exit 5; }
done
echo RETENTION_ALL_DONE
