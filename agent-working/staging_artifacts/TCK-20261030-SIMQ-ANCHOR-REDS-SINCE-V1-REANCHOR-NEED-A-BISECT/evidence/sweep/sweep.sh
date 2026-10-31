#!/bin/bash
# SimQ corpus sweep: a25619971 vs d914bace7 (#769). Clean git-archive trees, PYTHONHASHSEED=0, evaluate_simq.py --scenario <key> (calibrate_simq --audit-mode).
# Resumable: skips a key whose quality_report.json already exists in that tree. Sequential, wrapper, 3 GB memory floor before each run. Pairs are interleaved per key.
R=/data/vboxuser/Work/simq_sweep; REPO=/data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/rpg-ubuntu
PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python
for sha in a25619971 d914bace7; do
  [ -d $R/$sha ] || { mkdir -p $R/$sha && git -C $REPO archive $sha | tar -x -C $R/$sha; }
  git -C $REPO show d914bace7:tests/simulation_quality/fixtures/grade_anchors.json > $R/$sha/tests/simulation_quality/fixtures/grade_anchors.json   # anchors held at one copy for both trees
done
while read key; do
  for sha in a25619971 d914bace7; do
    [ -s $R/$sha/data/calibration/$key/quality_report.json ] && continue
    m=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
    if [ "$m" -lt 3145728 ]; then sleep 120; m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "SWEEP_STOP memory $m at $sha $key"; exit 3; }; fi
    export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PYTHONPATH=$R/$sha
    cd $R/$sha; ST=$(date +%s)
    systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY tools/evaluate_simq.py --scenario $key > $R/log_${sha}_$key.txt 2>&1
    echo "DONE $sha $key rc=$? wall_s=$(( $(date +%s)-ST )) mem_kB=$m"
  done
done < $R/keys.txt
echo SWEEP_ALL_DONE
