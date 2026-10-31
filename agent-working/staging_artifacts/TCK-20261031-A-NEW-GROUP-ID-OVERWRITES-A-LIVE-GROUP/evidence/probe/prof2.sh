#!/bin/bash
# Profiled pair for frontier_living_world s42 2000t: 100t control first (stop if it fails or the mirror mismatches), then base 6fdfdf555 and branch edb638b6a.
# Cores 4-5, MemAvailable >= 3 GB, stop at 22:00 or 40 min of own wall. Each hash must equal its run18 hash.
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; START=$(date +%s); O=$T/outprof
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
run() { # label sha world ticks noprof
  local lab=$1 sha=$2 w=$3 n=$4
  [ "$(date +%H%M)" -ge 2200 ] && { echo "PROF_STOP deadline 22:00 before $lab"; exit 4; }
  [ $(( $(date +%s)-START )) -ge 2400 ] && { echo "PROF_STOP 40 min wall before $lab"; exit 6; }
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "PROF_STOP memory $m before $lab"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  PROBE_OUT=$O/$lab.jsonl PROF_OUT=$O/$lab PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/profile_run.py $w 42 $n > $O/$lab.stdout 2>&1
  rc=$?; echo "PROF_DONE $lab rc=$rc wall_s=$(( $(date +%s)-ST )) mem_kB=$m at=$(date +%H:%M:%S)"; [ $rc -eq 0 ] || { echo "PROF_STOP rc=$rc at $lab"; exit 5; }
}
run control_branch_lifecycle_100t edb638b6a lifecycle_full_coverage_world 100
$PY - <<PYEOF
import json,sys
r=json.loads(open("$O/control_branch_lifecycle_100t.jsonl").read().splitlines()[-1]); mi=r["mirror"]
ok = mi["n_pred_not_actual"]==0 and mi["n_actual_not_pred"]==0 and r["touch"] and r["forms"] is not None and len(r["pool"])>=99 and r["sites"] and r["phases"]
print("PROF_CONTROL", "OK" if ok else "FAILED", "mirror ticks",mi["ticks"],"predicted",mi["predicted"],"actual",mi["actual"],"pred_not_actual",mi["n_pred_not_actual"],"actual_not_pred",mi["n_actual_not_pred"],"forms",len(r["forms"]),"dissolutions",len(r["dissolutions"]),"dis_other",len(r["dis_other"]),"coop",r["coop"],"touch_keys",sorted(r["touch"]),"sites",len(r["sites"]),"phases",len(r["phases"]))
sys.exit(0 if ok else 9)
PYEOF
[ $? -eq 0 ] || { echo "PROF_STOP control failed or mirror mismatch"; exit 9; }
run base_frontier_living_world_s42 6fdfdf555 frontier_living_world 2000
run branch_frontier_living_world_s42 edb638b6a frontier_living_world 2000
$PY - <<PYEOF
import json
exp={"base":"93a1944fe116","branch":"85fcc03d4ee9"}
for lab in ("base","branch"):
    r=json.loads(open("$O/%s_frontier_living_world_s42.jsonl"%lab).read().splitlines()[-1]); h=r["state_hash"][:12]
    print("PROF_HASH",lab,h,"expected",exp[lab],"MATCH" if h==exp[lab] else "MISMATCH")
PYEOF
echo PROF_ALL_DONE
