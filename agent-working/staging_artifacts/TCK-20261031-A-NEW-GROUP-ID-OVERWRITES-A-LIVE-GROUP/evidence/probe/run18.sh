#!/bin/bash
# 18 timing/size runs: 3 worlds x 3 reps x {base 6fdfdf555, branch edb638b6a}, alternating base/branch within each rep (rep 2 runs branch first, so drift does not always fall on one side), s42 2000t, probe v2, audit_mode, PYTHONHASHSEED=0.
# Same CPUs (taskset -c 4-5), sequential, MemAvailable >= 3 GB, resumable (.done marker), stops at STOP_HHMM (default 2200) or 75 min of own wall.
T=/data/vboxuser/Work/groups_base; STOP=${STOP_HHMM:-2200}; START=$(date +%s); mkdir -p $T/out18
order=""; for w in crowded_frontier frontier_living_world urban_political; do for rep in 1 2 3; do if [ $rep = 2 ]; then order="$order $w:$rep:edb638b6a $w:$rep:6fdfdf555"; else order="$order $w:$rep:6fdfdf555 $w:$rep:edb638b6a"; fi; done; done
for spec in $order; do
  IFS=: read w rep sha <<< "$spec"; lab=${w}_r${rep}_$sha
  [ -f $T/out18/$lab.done ] && continue
  [ "$(date +%H%M)" -ge $STOP ] && { echo "RUN18_STOP deadline $STOP before $lab"; exit 4; }
  [ $(( $(date +%s)-START )) -ge 4500 ] && { echo "RUN18_STOP 75 min wall before $lab"; exit 6; }
  for i in 1 2 3 4 5 6 7 8 9 10; do m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] && break; sleep 60; done
  [ "$m" -ge 3145728 ] || { echo "RUN18_STOP memory $m before $lab"; exit 3; }
  export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PYTHONPATH=$T/trees/$sha PROBE_OUT=$T/out18/$lab.jsonl
  cd $T/trees/$sha; ST=$(date +%s)
  systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 /data/vboxuser/Work/rpg-based-simulation/.venv/bin/python $T/probe_groups2.py $w 42 2000 > $T/out18/$lab.stdout 2>&1
  rc=$?; echo "RUN18_DONE $lab rc=$rc wall_s=$(( $(date +%s)-ST )) mem_kB=$m at=$(date +%H:%M:%S)"
  [ $rc -eq 0 ] && echo ok > $T/out18/$lab.done || { echo "RUN18_STOP rc=$rc at $lab"; exit 5; }
done
echo RUN18_ALL_DONE
