cd /data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/platform
R=$(cat /tmp/claude-1000/*/*/scratchpad/RUN)
PW=$(tr -d '[:space:]' < docker/secrets/grafana_admin_password)
ev(){ echo "$(date -u +%FT%TZ) $*" | tee -a $R/events.txt; }
state(){ curl -s -K - <<<"user = \"admin:$PW\"
url = \"http://127.0.0.1:3000/api/prometheus/grafana/api/v1/rules\"" | python3 -c "
import json,sys
print(' '.join(r['name']+'='+r['state']+'('+(r['health'])+')' for g in json.load(sys.stdin)['data']['groups'] for r in g['rules'] if r['name'] in ('LogShippingErrors','TargetDown')))"; }
pq(){ curl -s --data-urlencode "query=$1" http://127.0.0.1:9090/api/v1/query | python3 -c "
import json,sys
d=json.load(sys.stdin)['data']['result']; print([ (r['metric'].get('job',''),r['value'][1]) for r in d])"; }
alloyapi(){ docker compose exec -T alloy bash -c "exec 3<>/dev/tcp/localhost/12345; printf 'GET $1 HTTP/1.0\r\n\r\n' >&3; cat <&3"; }
