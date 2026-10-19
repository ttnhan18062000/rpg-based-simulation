#!/usr/bin/env bash
# Memory sampler for load and drill runs. usage: sample_stats.sh <outdir> [interval_seconds=5]   (stop it by creating <outdir>/sample_stats.stop or by killing its PID)
# Writes, every INTERVAL seconds:
#   <outdir>/docker_stats.csv : utc,container,mem_mib,cpu_pct   (`docker stats --no-stream` of every platform-* container: usage without the reclaimable file cache)
#   <outdir>/cgroup_mem.csv   : utc,container,current_mib,anon_mib,active_file_mib,inactive_file_mib,file_mib,peak_mib,limit_mib   (cgroup v2 memory.current, memory.stat anon and file, memory.peak, for ALL platform-* containers)
# anon is the memory the process really holds; file is page cache the kernel reclaims, so a memory.peak sitting exactly at the limit can be cache only. Judge a limit on anon + active_file, not memory.peak. Never matches processes by pattern.
set -uo pipefail
OUT="${1:?usage: sample_stats.sh <outdir> [interval]}"; INTERVAL="${2:-5}"
mkdir -p "$OUT"; rm -f "$OUT/sample_stats.stop"
echo "utc,container,mem_mib,cpu_pct" > "$OUT/docker_stats.csv"
echo "utc,container,current_mib,anon_mib,active_file_mib,inactive_file_mib,file_mib,peak_mib,limit_mib" > "$OUT/cgroup_mem.csv"
to_mib() { awk -v v="$1" 'BEGIN{printf "%.1f", v/1048576}'; }
while [ ! -f "$OUT/sample_stats.stop" ]; do
  now="$(date -u +%H:%M:%S)"
  docker stats --no-stream --format '{{.Name}} {{.MemUsage}} {{.CPUPerc}}' 2>/dev/null | grep '^platform-' | while read -r name usage _ _ cpu; do
    mem="${usage%%/*}"; case "$mem" in *GiB) v="$(awk -v x="${mem%GiB}" 'BEGIN{printf "%.1f", x*1024}')";; *MiB) v="${mem%MiB}";; *KiB) v="$(awk -v x="${mem%KiB}" 'BEGIN{printf "%.1f", x/1024}')";; *) v="$mem";; esac
    echo "${now},${name},${v},${cpu%\%}" >> "$OUT/docker_stats.csv"
  done
  for name in $(docker ps --format '{{.Names}}' 2>/dev/null | grep '^platform-'); do
    cid="$(docker inspect "$name" --format '{{.Id}}' 2>/dev/null)" || continue
    d="/sys/fs/cgroup/system.slice/docker-${cid}.scope"
    [ -r "$d/memory.current" ] || continue
    cur="$(cat "$d/memory.current")"; peak="$(cat "$d/memory.peak" 2>/dev/null || echo 0)"
    anon="$(awk '$1=="anon"{print $2}' "$d/memory.stat")"; file="$(awk '$1=="file"{print $2}' "$d/memory.stat")"
    actf="$(awk '$1=="active_file"{print $2}' "$d/memory.stat")"; inactf="$(awk '$1=="inactive_file"{print $2}' "$d/memory.stat")"
    lim="$(docker inspect "$name" --format '{{.HostConfig.Memory}}')"
    echo "${now},${name},$(to_mib "$cur"),$(to_mib "${anon:-0}"),$(to_mib "${actf:-0}"),$(to_mib "${inactf:-0}"),$(to_mib "${file:-0}"),$(to_mib "$peak"),$(to_mib "$lim")" >> "$OUT/cgroup_mem.csv"
  done
  sleep "$INTERVAL"
done
