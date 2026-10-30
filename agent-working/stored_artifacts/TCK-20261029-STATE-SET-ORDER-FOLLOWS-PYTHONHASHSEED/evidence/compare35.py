"""Outcome-drift comparison, base vs B, per world over seeds 42-46 (rpg-planner ruling 4). Usage: compare35.py [ticks]"""
import json, sys, collections
R = "/data/vboxuser/Work/b_runs/out"; T = sys.argv[1] if len(sys.argv) > 1 else "5000"
WORLDS = ("frontier_living_world", "urban_political", "crowded_frontier"); SEEDS = range(42, 47)
def load(arm, w, s):
    try: return json.load(open(f"{R}/p{T}_{arm}_{w}_{s}.json"))
    except FileNotFoundError: return None
def facts(d):
    deaths = collections.Counter(v[1] for v in d["final"].values() if not v[0])
    alive = sorted(int(k) for k, v in d["final"].items() if v[0])
    return {"deaths": deaths, "alive": alive, "counters": d.get("counters") or {}}
def tol(m): return max(1, 0.05 * m)
verdict_stop = False; moved = []
for w in WORLDS:
    sums = {k: collections.defaultdict(lambda: [0, 0]) for k in ("deaths", "counters")}; alive_n = [0, 0]; missing = []
    for s in SEEDS:
        a, b = load("base", w, s), load("B", w, s)
        if a is None or b is None: missing.append(s); continue
        fa, fb = facts(a), facts(b)
        hm = a["final_hash"] != b["final_hash"]
        if hm: moved.append((w, s))
        same_alive = fa["alive"] == fb["alive"]
        print(f"{w} s{s}: hash {'MOVED' if hm else 'same'} ({a['final_hash'][:8]} -> {b['final_hash'][:8]}); alive set {'same' if same_alive else 'DIFFERENT'} ({len(fa['alive'])}/{len(fb['alive'])}); deaths {'same' if fa['deaths']==fb['deaths'] else 'DIFFER'}; counters {'same' if fa['counters']==fb['counters'] else 'DIFFER'}")
        for k in ("deaths", "counters"):
            for key in set(fa[k]) | set(fb[k]):
                sums[k][key][0] += fa[k].get(key, 0) or 0; sums[k][key][1] += fb[k].get(key, 0) or 0
        alive_n[0] += len(fa["alive"]); alive_n[1] += len(fb["alive"])
    if missing: print(f"  {w}: MISSING seeds {missing}"); continue
    bad = []
    for k in ("deaths", "counters"):
        for key, (m, n) in sorted(sums[k].items()):
            if abs(n - m) > tol(m): bad.append((k, key, m, n))
    if abs(alive_n[1] - alive_n[0]) > tol(alive_n[0]): bad.append(("alive_total", "-", alive_n[0], alive_n[1]))
    print(f"  {w}: 5-seed sums outside max(1, 5%): {bad if bad else 'none'}"); verdict_stop |= bool(bad)
print("MOVED-HASH SEEDS needing the instrumented first-difference attribution:", moved)
print("VERDICT:", "STOP (value outside tolerance)" if verdict_stop else "PASS on values (attribution of moved seeds still required)")
