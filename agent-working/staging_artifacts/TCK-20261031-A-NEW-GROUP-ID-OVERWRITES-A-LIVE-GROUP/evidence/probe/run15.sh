#!/bin/bash
# 15 base runs of 6fdfdf555 (read-only group probe), 2000t, resumable (.done marker), sequential, MemAvailable >= 3 GB, stops at 110 min wall or 22:00.
T=/data/vboxuser/Work/groups_base; sha=6fdfdf555; START=$(date +%s)
order=""; for w in crowded_frontier frontier_living_world urban_political; do for s in 42 43 44 45 46; do order="$order $w:$s"; done; done
for spec in $order; do
  IFS=: read w s <<< "$spec"; lab=${w}_s${s}
  [ -f $T/out/$lab.done ] && continue
  [ "$(date +%H%M)" -ge 2200 ] && { echo "GROUPS_STOP deadline 22:00 before $lab"; exit 4; }
  [ $(( $(date +%s)-START )) -ge 6600 ] && { echo "GROUPS_STOP 110 min wall before $lab"; exit 6; }
  for i in 1 2 3 4 5 6 7 8 9 10; do m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] && break; sleep 60; done
  [ "$m" -ge 3145728 ] || { echo "GROUPS_STOP memory $m before $lab"; exit 3; }
  export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PYTHONPATH=$T/trees/$sha PROBE_OUT=$T/out/$lab.jsonl
  cd $T/trees/$sha; ST=$(date +%s)
  systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 /data/vboxuser/Work/rpg-based-simulation/.venv/bin/python $T/probe_groups.py $w $s 2000 > $T/out/$lab.stdout 2>&1
  rc=$?; echo "RUN_DONE $lab rc=$rc wall_s=$(( $(date +%s)-ST )) mem_kB=$m at=$(date +%H:%M:%S)"
  [ $rc -eq 0 ] && echo ok > $T/out/$lab.done || { echo "GROUPS_STOP rc=$rc at $lab"; exit 5; }
done
echo GROUPS_ALL_DONE
