#!/bin/bash
# 3 extra base runs (probe v2) at 6fdfdf555, s42 2000t, after the 15 finish. Separate dir out3. Stops at 30 min of its own wall or 22:00.
T=/data/vboxuser/Work/groups_base; sha=6fdfdf555
while ! grep -qE "GROUPS_ALL_DONE|GROUPS_STOP" $T/run15.log; do sleep 20; done
grep -q GROUPS_ALL_DONE $T/run15.log || { echo "RUN3_NOT_STARTED the 15 did not finish"; exit 7; }
START=$(date +%s)
for w in crowded_frontier frontier_living_world urban_political; do
  lab=${w}_s42; [ -f $T/out3/$lab.done ] && continue
  [ "$(date +%H%M)" -ge 2200 ] && { echo "RUN3_STOP deadline 22:00 before $lab"; exit 4; }
  [ $(( $(date +%s)-START )) -ge 1800 ] && { echo "RUN3_STOP 30 min wall before $lab"; exit 6; }
  for i in 1 2 3 4 5 6 7 8 9 10; do m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] && break; sleep 60; done
  [ "$m" -ge 3145728 ] || { echo "RUN3_STOP memory $m before $lab"; exit 3; }
  export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PYTHONPATH=$T/trees/$sha PROBE_OUT=$T/out3/$lab.jsonl
  cd $T/trees/$sha; ST=$(date +%s)
  systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 /data/vboxuser/Work/rpg-based-simulation/.venv/bin/python $T/probe_groups2.py $w 42 2000 > $T/out3/$lab.stdout 2>&1
  rc=$?; echo "RUN3_DONE $lab rc=$rc wall_s=$(( $(date +%s)-ST )) mem_kB=$m at=$(date +%H:%M:%S)"
  [ $rc -eq 0 ] && echo ok > $T/out3/$lab.done || { echo "RUN3_STOP rc=$rc at $lab"; exit 5; }
done
echo RUN3_ALL_DONE
