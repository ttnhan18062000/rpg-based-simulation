#!/usr/bin/env bash
. "$(dirname "$0")/lib.sh"
EXPR='sum(rate(prometheus_sd_refresh_failures_total{job="alloy"}[5m]))+(sum(rate(loki_write_batch_retries_total{job="alloy"}[5m])) or vector(0))+sum(rate(loki_write_dropped_entries_total{job="alloy"}[5m]))'
aborted(){ [ -f $R/guard.abort ] && { ev "ABORT FILE PRESENT"; exit 3; }; }
snap(){ ev "$1 | $(state) | expr=$(pq "$EXPR") | up=$(pq 'up{job="alloy"}')"; }
# wait <pattern> <limit_s> <label>
wait_for(){ local t0=$(date +%s); while [ $(( $(date +%s)-t0 )) -lt $2 ]; do aborted; s=$(state); snap "$3 +$(( $(date +%s)-t0 ))s"; case "$s" in *"$1"*) return 0;; esac; sleep 30; done; return 1; }
ev "CASE quiet start"
for i in $(seq 1 12); do aborted; snap "quiet $i"; sleep 60; done
ev "CASE recreate start"
T1=$(docker logs platform-jsonprobe-1 2>&1 | wc -l); ev "probe lines emitted so far=$T1 sent=$(pq 'loki_write_sent_entries_total{job="alloy"}')"
docker compose --profile observability up -d --force-recreate alloy >$R/recreate.log 2>&1; ev "alloy recreated"; sleep 90
T2=$(docker logs platform-jsonprobe-1 2>&1 | wc -l)
curl -s -G http://127.0.0.1:3100/loki/api/v1/query_range --data-urlencode 'query={container="platform-jsonprobe-1"}' --data-urlencode limit=5000 --data-urlencode "start=$(date -d '-15 min' +%s)000000000" | python3 -c "
import json,sys,collections
c=collections.Counter()
for s in json.load(sys.stdin)['data']['result']:
  for v in s['values']: c[json.loads(v[1])['tick']]+=1
ticks=sorted(c); exp=set(range(ticks[0],ticks[-1]+1))
print('loki distinct ticks',len(c),'range',ticks[0],ticks[-1],'missing',sorted(exp-set(c)),'duplicated',[t for t,n in c.items() if n>1])" | tee -a $R/events.txt
ev "probe lines emitted at end=$T2 sent_after_recreate=$(pq 'loki_write_sent_entries_total{job="alloy"}')"
ev "CASE 403 start"
C="docker compose -f compose.yaml -f $R/override-403.yaml --profile observability"
$C up -d --force-recreate docker-socket-proxy alloy >$R/c403.log 2>&1; ev "proxy NETWORKS=$(docker inspect platform-docker-socket-proxy-1 --format '{{range .Config.Env}}{{println .}}{{end}}' | grep NETWORKS)"
wait_for 'LogShippingErrors=firing' 1200 403 && ev "403 FIRED" || ev "403 DID NOT FIRE"
ev "403 restore"; docker compose --profile observability up -d --force-recreate docker-socket-proxy alloy >$R/restore.log 2>&1; ev "proxy $(docker inspect platform-docker-socket-proxy-1 --format '{{range .Config.Env}}{{println .}}{{end}}' | grep NETWORKS)"
wait_for 'LogShippingErrors=inactive' 900 403restore && ev "403 resolved" || ev "403 NOT resolved"
ev "CASE stopped start"; docker compose --profile observability stop alloy >/dev/null 2>&1
wait_for 'LogShippingErrors=firing' 1800 stopped && ev "stopped FIRED" || ev "stopped DID NOT FIRE"
docker compose --profile observability start alloy >/dev/null 2>&1; ev "alloy started"
wait_for 'LogShippingErrors=inactive' 900 stoppedrestore && ev "stopped resolved" || ev "stopped NOT resolved"
ev "CASE loki-unreachable start"; docker compose --profile observability stop loki >/dev/null 2>&1
wait_for 'LogShippingErrors=firing' 1500 loki && ev "loki FIRED" || ev "loki DID NOT FIRE"
docker compose --profile observability start loki >/dev/null 2>&1; ev "loki started"
wait_for 'LogShippingErrors=inactive' 1200 lokirestore && ev "loki resolved" || ev "loki NOT resolved"
ev "ALL CASES DONE"
