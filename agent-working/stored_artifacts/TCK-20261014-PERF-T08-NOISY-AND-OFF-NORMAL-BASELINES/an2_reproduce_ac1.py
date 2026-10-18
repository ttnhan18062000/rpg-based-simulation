"""AC1 reproduction script (TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES), not a maintained tool: no tests, no owner.

Reads reports/perf/<root>/<name>/{summary.json,run1..3.json} (git-ignored T08 output; the corpus records point at reports/perf/samples/*.json by samples.uri)
and prints per-run avg, min, median, p95, max, spread across the 3 runs, first/last-fifth means, lag-1 autocorrelation and block means.
Run from the repo root: python3 an2.py <root: t08|t08_retry> <name> [<name> ...]. Ran with Python 3.13.7 (system python3), 2026-10-15; stdlib only.
"""
import json,statistics as st,sys,math
root=sys.argv[1]
def pct(v,p):
    s=sorted(v);return s[max(0,math.ceil(p/100*len(s))-1)]
def bimodal(runavgs):
    s=sorted(runavgs);return (s[-1]-s[0])/s[0]
for n in sys.argv[2:]:
    sm=json.load(open(f"reports/perf/{root}/{n}/summary.json"))
    print("==",root,n,"noisy",sm.get('noisy'),"spread",sm.get('spread'))
    for i in (1,2,3):
        r=json.load(open(f"reports/perf/{root}/{n}/run{i}.json"))['result']
        s=r['samples']['tick_compute_ms']
        if s is None: s=json.load(open(r['samples']['uri']))['tick_compute_ms']
        run=sm['runs'][i-1];k=len(s)//5
        # tick-to-tick lag-1 autocorrelation and regime shifts (rolling-10 mean range)
        m=st.mean(s);v=sum((x-m)**2 for x in s) or 1
        ac=sum((s[j]-m)*(s[j+1]-m) for j in range(len(s)-1))/v
        w=max(5,len(s)//10);rm=[st.mean(s[j:j+w]) for j in range(0,len(s)-w+1,w)]
        print(f" r{i} n={len(s)} avg={m:.1f} min={min(s):.1f} med={st.median(s):.1f} p95={pct(s,95):.1f} max={max(s):.1f} cv={st.pstdev(s)/m:.2f} first20%={st.mean(s[:k]):.1f} last20%={st.mean(s[-k:]):.1f} ac1={ac:.2f} blockmean_range={min(rm):.0f}-{max(rm):.0f} load={run['loadavg_1min']} swap={run['swap_used_mb']:.0f} wall={run['wall_s']}")
