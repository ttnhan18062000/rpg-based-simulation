#!/usr/bin/env bash
# Abort watcher for a stack run. usage: stack_guard.sh <rundir> [real|dry]
# Every GUARD_INTERVAL seconds (default 60; the first line at once) it appends "<UTC> avail=<MiB> swap=<MiB> mode=<mode> thresholds=<a>/<b>" to <rundir>/guard.log.
# Trigger: MemAvailable < MIN_AVAIL_MIB (default 1500) or swap used > MAX_SWAP_MIB (default 7500), or a reading that is empty or not a number (logged as READ FAIL; fail safe).
# Real mode on trigger: kills the PID in <rundir>/locust.pid (if present), runs `docker compose <COMPOSE_ARGS> down` (never -v), writes <rundir>/guard.abort.
# Dry mode prints "WOULD DOWN ..." and exits without touching anything (use it with a huge MIN_AVAIL_MIB to prove the trigger path before a run).
# It stops when <rundir>/guard.stop exists. It never matches processes by pattern: only the PID file.
# COMPOSE_ARGS defaults to "--profile observability"; set COMPOSE_ARGS="-f compose.yaml -f <override> --profile observability" when an override is in use
# (then export whatever variables the override requires before starting this script).
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" || exit 2
RUN="${1:?usage: stack_guard.sh <rundir> [real|dry]}"; MODE="${2:-real}"
MIN_AVAIL_MIB="${MIN_AVAIL_MIB:-1500}"; MAX_SWAP_MIB="${MAX_SWAP_MIB:-7500}"
COMPOSE_ARGS="${COMPOSE_ARGS:---profile observability}"
mkdir -p "$RUN"; rm -f "$RUN/guard.stop" "$RUN/guard.abort"
while [ ! -f "$RUN/guard.stop" ]; do
  a=$(awk '/MemAvailable/{print int($2/1024)}' "${MEMINFO_FILE:-/proc/meminfo}" 2>/dev/null); w=$(free -m 2>/dev/null | awk '/Swap:/{print $3}')
  echo "$(date -u +%T) avail=${a} swap=${w} mode=${MODE} thresholds=${MIN_AVAIL_MIB}/${MAX_SWAP_MIB}" >> "$RUN/guard.log"
  # Fail safe: an empty or non-numeric reading is a trigger (a blind watcher is worse than an abort).
  trig=0
  case "$a" in ''|*[!0-9]*) trig=1; echo "$(date -u +%T) READ FAIL avail='${a}'" >> "$RUN/guard.log";; esac
  case "$w" in ''|*[!0-9]*) trig=1; echo "$(date -u +%T) READ FAIL swap='${w}'" >> "$RUN/guard.log";; esac
  if [ "$trig" = 0 ] && { [ "$a" -lt "$MIN_AVAIL_MIB" ] || [ "$w" -gt "$MAX_SWAP_MIB" ]; }; then trig=1; fi
  if [ "$trig" = 1 ]; then
    if [ "$MODE" = dry ]; then echo "$(date -u +%T) WOULD DOWN avail=${a} swap=${w}" | tee -a "$RUN/guard.log"; exit 0; fi
    echo "ABORT $(date -u +%T) avail=${a} swap=${w}" > "$RUN/guard.abort"
    [ -s "$RUN/locust.pid" ] && kill "$(cat "$RUN/locust.pid")" 2>/dev/null
    # shellcheck disable=SC2086
    docker compose $COMPOSE_ARGS down > "$RUN/guard.down.log" 2>&1
    exit 0
  fi
  sleep "${GUARD_INTERVAL:-60}"
done
