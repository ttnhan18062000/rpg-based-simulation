#!/usr/bin/env bash
# The Redis-stop drill under load (TCK-20261018-REDIS-DOWN-CAUSE-ALERT / TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD; ADR D5's one failure drill).
# A scripted manual drill, not chaos tooling: Locust holds a steady step BELOW the knee, Redis is stopped (T0), the RedisDown alert is awaited in the
# local ntfy topic (T1), Redis is started after a fixed outage (T2), the resolved message is awaited (T3), and Locust runs on for a tail.
# Every event prints a UTC timestamp and is appended to events.txt. During the run it also samples, every SAMPLE_SECONDS: the backend /health
# status, redis_up from Prometheus, and the Grafana state of RedisDown and the two API SLO rules (to show whether the SLO stays green).
# It is one heavy run: run it ALONE, after the observability stack (with the load-test key override) is up and healthy.
#
# Needs (all gitignored, never printed): docker/secrets/ntfy_topic, docker/secrets/grafana_admin_password and a READ token for the ntfy topic in
# $NTFY_READER_TOKEN_FILE (a regular ntfy user with read-only access to the topic, created with the ntfy CLI as described at the top of compose.yaml).
# The messages saved to the output directory have the topic redacted. Secrets never appear on a command line: curl reads them from its stdin config.
#
#   LOADTEST_API_KEY_HASHES="$(python3 tools/loadtest/keys.py -n 990)" docker compose -f compose.yaml -f tools/loadtest/compose.loadtest.yaml \
#       --profile observability up -d ...
#   NTFY_READER_TOKEN_FILE=/path/to/reader_token tools/loadtest/drill_redis_stop.sh
#
# Knobs (environment): LOCUST_PY (python with locust, default python3), USERS (default 10, a step below the measured knee), HEAD_SECONDS (steady
# load before T0, default 90), OUTAGE_SECONDS (default 180), TAIL_SECONDS (load after the resolved message, default 60), DETECT_TIMEOUT (default 300),
# RESOLVE_TIMEOUT (default 420), SAMPLE_SECONDS (default 5), NTFY_PORT (2586), PROMETHEUS_PORT (9090), GRAFANA_PORT (3000), LOKI_PORT (3100), BACKEND_PORT (8000).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

LOCUST_PY="${LOCUST_PY:-python3}"
USERS="${USERS:-10}"
HEAD_SECONDS="${HEAD_SECONDS:-90}"
OUTAGE_SECONDS="${OUTAGE_SECONDS:-180}"
TAIL_SECONDS="${TAIL_SECONDS:-60}"
DETECT_TIMEOUT="${DETECT_TIMEOUT:-300}"
RESOLVE_TIMEOUT="${RESOLVE_TIMEOUT:-420}"
SAMPLE_SECONDS="${SAMPLE_SECONDS:-5}"
NTFY="http://127.0.0.1:${NTFY_PORT:-2586}"
PROM="http://127.0.0.1:${PROMETHEUS_PORT:-9090}"
GRAFANA="http://127.0.0.1:${GRAFANA_PORT:-3000}"
LOKI="http://127.0.0.1:${LOKI_PORT:-3100}"
BACKEND="http://127.0.0.1:${BACKEND_PORT:-8000}"
COMPOSE=(docker compose -f compose.yaml -f tools/loadtest/compose.loadtest.yaml --profile observability)

: "${NTFY_READER_TOKEN_FILE:?set NTFY_READER_TOKEN_FILE to a file holding a read token for the ntfy topic}"
for f in "$NTFY_READER_TOKEN_FILE" docker/secrets/ntfy_topic docker/secrets/grafana_admin_password tools/loadtest/.keys.txt; do
  [ -s "$f" ] || { echo "missing or empty: $f" >&2; exit 2; }
done
TOPIC="$(tr -d '[:space:]' < docker/secrets/ntfy_topic)"
READ_TOKEN="$(tr -d '[:space:]' < "$NTFY_READER_TOKEN_FILE")"
GRAFANA_PW="$(tr -d '[:space:]' < docker/secrets/grafana_admin_password)"

OUT="tools/loadtest/runs/$(date -u +%Y%m%dT%H%M%SZ)-drill-redis-stop"
mkdir -p "$OUT"
EVENTS="$OUT/events.txt"
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
ev() { echo "$(ts) $*" | tee -a "$EVENTS"; }
# The topic is passed through the environment, not argv (a sed script with the topic in it would show in `ps`).
redact() { TOPIC="$TOPIC" python3 -c "import os, sys; t = os.environ['TOPIC']; sys.stdout.write(sys.stdin.read().replace(t, '<topic>'))"; }

ntfy_messages() { # one JSON object per line, all cached messages of the topic
  # The token and the topic (part of the URL) go through curl's stdin config (-K -), never argv, so `ps` cannot show them.
  curl -s -K - <<<"header = \"Authorization: Bearer ${READ_TOKEN}\"
url = \"${NTFY}/${TOPIC}/json?poll=1&since=all\"" || true
}
ntfy_count() { # $1 = title prefix, e.g. "[firing] RedisDown"
  ntfy_messages | python3 -c "
import sys, json
n = 0
for line in sys.stdin:
    try: m = json.loads(line)
    except ValueError: continue
    if m.get('event') == 'message' and str(m.get('title', '')).startswith(sys.argv[1]): n += 1
print(n)" "$1"
}
rule_states() { # state of the three rules of interest, one line
  # The Grafana password goes through curl's stdin config (-K -), never argv.
  curl -s -K - <<<"user = \"admin:${GRAFANA_PW}\"
url = \"${GRAFANA}/api/prometheus/grafana/api/v1/rules\"" | python3 -c "
import sys, json
want = ('RedisDown', 'ApiLatencyP95High', 'ApiErrorRateHigh')
out = []
try:
    for g in json.load(sys.stdin)['data']['groups']:
        for r in g['rules']:
            if r['name'] in want: out.append(r['name'] + '=' + r['state'] + '/' + r.get('health', ''))
except Exception: pass
print(' '.join(sorted(out)))"
}
redis_up() {
  curl -s "${PROM}/api/v1/query" --data-urlencode 'query=redis_up' | python3 -c "
import sys, json
try: print(json.load(sys.stdin)['data']['result'][0]['value'][1])
except Exception: print('na')"
}

# --- background sampler: health, redis_up, rule states every SAMPLE_SECONDS ---
echo "ts,backend_health_http,redis_up,rules" > "$OUT/samples.csv"
sampler() {
  while true; do
    h="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "${BACKEND}/health" || true)"
    echo "$(ts),${h:-000},$(redis_up),$(rule_states)" >> "$OUT/samples.csv"
    sleep "$SAMPLE_SECONDS"
  done
}

LOCUST_PID=""
SAMPLER_PID=""
cleanup() {
  [ -n "$SAMPLER_PID" ] && kill "$SAMPLER_PID" 2>/dev/null || true
  [ -n "$LOCUST_PID" ] && kill "$LOCUST_PID" 2>/dev/null || true
}
trap cleanup EXIT

TOTAL=$((HEAD_SECONDS + DETECT_TIMEOUT + RESOLVE_TIMEOUT + TAIL_SECONDS + OUTAGE_SECONDS + 120))
ev "start users=${USERS} head=${HEAD_SECONDS}s outage=${OUTAGE_SECONDS}s tail=${TAIL_SECONDS}s out=${OUT}"
ev "baseline firing_msgs=$(ntfy_count '[firing] RedisDown') resolved_msgs=$(ntfy_count '[resolved] RedisDown') rules: $(rule_states) redis_up=$(redis_up)"
sampler &
SAMPLER_PID=$!

PYTHONPATH="$REPO" LOADTEST_KEYS_FILE="$REPO/tools/loadtest/.keys.txt" "$LOCUST_PY" -m locust -f tools/loadtest/locustfile.py --headless \
  -u "$USERS" -r "$USERS" -t "${TOTAL}s" --host "$BACKEND" --csv "$OUT/locust" --csv-full-history --only-summary \
  > "$OUT/locust.log" 2>&1 &
LOCUST_PID=$!
ev "LOCUST_START pid=${LOCUST_PID}"
sleep "$HEAD_SECONDS"

base_fire="$(ntfy_count '[firing] RedisDown')"
base_res="$(ntfy_count '[resolved] RedisDown')"
ev "T0 docker compose stop redis"
"${COMPOSE[@]}" stop redis > "$OUT/compose_stop.log" 2>&1
T0_EPOCH=$(date +%s)

t1=""
while [ $(( $(date +%s) - T0_EPOCH )) -lt "$DETECT_TIMEOUT" ]; do
  if [ "$(ntfy_count '[firing] RedisDown')" -gt "$base_fire" ]; then t1=1; ev "T1 RedisDown firing message received in the ntfy topic"; break; fi
  [ $(( $(date +%s) - T0_EPOCH )) -ge "$OUTAGE_SECONDS" ] && [ -z "$t1" ] && break
  sleep "$SAMPLE_SECONDS"
done
[ -z "$t1" ] && ev "T1 not reached before the outage window ended (no firing message yet)"

# hold the outage for the full window
while [ $(( $(date +%s) - T0_EPOCH )) -lt "$OUTAGE_SECONDS" ]; do sleep "$SAMPLE_SECONDS"; done
if [ -z "$t1" ] && [ "$(ntfy_count '[firing] RedisDown')" -gt "$base_fire" ]; then t1=1; ev "T1 (late) RedisDown firing message received"; fi

ev "T2 docker compose start redis"
"${COMPOSE[@]}" start redis > "$OUT/compose_start.log" 2>&1
T2_EPOCH=$(date +%s)

t3=""
while [ $(( $(date +%s) - T2_EPOCH )) -lt "$RESOLVE_TIMEOUT" ]; do
  if [ "$(ntfy_count '[resolved] RedisDown')" -gt "$base_res" ]; then t3=1; ev "T3 RedisDown resolved message received in the ntfy topic"; break; fi
  sleep "$SAMPLE_SECONDS"
done
[ -z "$t3" ] && ev "T3 not reached within ${RESOLVE_TIMEOUT}s"

ev "tail ${TAIL_SECONDS}s of steady load"
sleep "$TAIL_SECONDS"
kill "$LOCUST_PID" 2>/dev/null || true
wait "$LOCUST_PID" 2>/dev/null || true
LOCUST_PID=""
ev "LOCUST_STOP"
kill "$SAMPLER_PID" 2>/dev/null || true
SAMPLER_PID=""

# --- captures (topic redacted) ---
ntfy_messages | redact > "$OUT/ntfy_messages.jsonl"
START_NS=$(( (T0_EPOCH - 60) * 1000000000 ))
END_NS=$(( ( $(date +%s) ) * 1000000000 ))
curl -s -G "${LOKI}/loki/api/v1/query_range" --data-urlencode 'query={container=~".*backend.*"}' --data-urlencode "start=${START_NS}" \
  --data-urlencode "end=${END_NS}" --data-urlencode 'limit=5000' --data-urlencode 'direction=forward' > "$OUT/loki_backend.json" || true
ev "captures written to ${OUT} (events.txt, samples.csv, locust*_stats*.csv, ntfy_messages.jsonl, loki_backend.json)"
ev "detection T1-T0 and recovery T3-T2 are read from the timestamps above; the record is written by hand from these files"
