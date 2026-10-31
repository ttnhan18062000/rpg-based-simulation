"""Width count and path tally from probe6 logs. Usage: retention_counts.py <out_dir> [--path <log.jsonl> <entity>]
Definitions (stated):
 - held project: an ALIVE entity's CURRENT project id contains 'combat_retreat' at a tick (rh record). A project is identified by (entity, project id).
 - present threat at a held tick: acting_threat_to (src/ai/goals/present_threat.py: a perceived hostile's task attacks/pursues the subject, or it hit the subject within NEED_WAKE_CADENCE ticks) OR a perceived hostile orthogonally adjacent (decision 32).
 - last present threat of a project = the last held tick with a present threat. A project that never had a present threat while held uses its first held tick as the reference and is flagged (N-ticks are counted from when it was adopted).
 - 'still active N ticks after the last present threat' = held at some tick >= last_threat + N. Projects held at the run's last tick are counted AND flagged open-at-end.
 - hp: ratio at the last held tick (end of the stale stretch).
 - Dead entities with an open project: dead entity (not alive) whose current project id is non-empty at the last tick / that has an ACTIVE project in its project map.
"""
import json, sys, glob, os, re
from collections import defaultdict
D = sys.argv[1]
def load(p):
    R = defaultdict(list)
    for l in open(p):
        r = json.loads(l); R[r["k"]].append(r)
    return R
def analyse(R, last):
    held = defaultdict(list)
    for r in R["rh"]: held[(r["e"], r["pr"])].append(r)
    projs = []
    for (e, pr), L in sorted(held.items()):
        L.sort(key=lambda r: r["t"]); T = [r["t"] for r in L if r["acting"] or r["adj"]]
        ref = max(T) if T else L[0]["t"]; never = not T
        lastheld = L[-1]["t"]; span = lastheld - ref
        projs.append(dict(e=e, pr=pr, start=L[0]["t"], end=lastheld, ref=ref, never=never, span=span, open_end=(lastheld >= last),
                          hp=L[-1]["hp"] / max(1, L[-1]["mh"]), hp_at_ref50=next((r["hp"] / max(1, r["mh"]) for r in L if r["t"] >= ref + 50), None)))
    dead_cur, dead_act, dead_all = set(), set(), set()
    final = {}
    for r in R["dead"]: final[r["e"]] = r
    for e, r in final.items():
        dead_all.add(e)
        if r["pr"]: dead_cur.add(e)
        if r["active"]: dead_act.add(e)
    return projs, dead_all, dead_cur, dead_act
if "--path" in sys.argv:
    i = sys.argv.index("--path"); R = load(sys.argv[i + 1]); ent = int(sys.argv[i + 2])
    rh = {r["t"]: r for r in R["rh"] if r["e"] == ent}; sel = defaultdict(list); sw = defaultdict(list)
    for r in R["sel"]:
        if r["e"] == ent: sel[r["t"]].append(r)
    for r in R["sw"]:
        if r["e"] == ent: sw[r["t"]].append(r)
    ticks = sorted(rh); tally = defaultdict(int); ci = defaultdict(int)
    for t in ticks:
        if t not in sel: tally["no goal-selection call this tick: the project is kept by default (no code path runs)"] += 1; continue
        for s in sel[t]:
            b = s["best"]
            if s["ci"]: ci[f"{s['ci'][0]}/{s['ci'][1]}"] += 1
            if b is None: tally["(ii) best_candidate None (every candidate < 20 or no target; intelligence.py:1588-1593): project kept"] += 1
            elif "combat_retreat" in b[0]: tally["best_candidate is COMBAT_RETREAT itself (an existing project of that kind is resumed/kept)"] += 1
            else:
                sws = sw.get(t, [])
                if not sws: tally[f"best_candidate {b[0]} but no evaluate_project_switch call logged"] += 1
                else: tally[f"best_candidate {b[0]}: evaluate_project_switch {'SWITCHED' if sws[-1]['switched'] else 'kept the current project'}"] += 1
    print(f"entity {ent}: held ticks {len(ticks)} ({ticks[0]}-{ticks[-1]}), selection calls on {len(sel)} of them\n")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]): print(f"- {v}: {k}")
    print("\nhead committed intention while selecting:", dict(ci))
    print("\nlast 4 selection calls and every evaluate_project_switch call around the end:")
    for t in ticks[-3:] + [ticks[-1] + 1]:
        for s in sel.get(t, []): print(" sel", t, s["top"], "best", s["best"], "ci", s["ci"])
    for t in sorted(sw):
        if t >= ticks[-1] - 3:
            for s in sw[t]: print(" sw", s)
    sys.exit(0)
runs = {}
for p in sorted(glob.glob(f"{D}/*.jsonl")):
    m = re.match(r"(.+)_s(\d+)_([0-9a-f]+)\.jsonl", os.path.basename(p))
    if not m: continue
    R = load(p)
    if not R["fin"]: continue
    last = R["fin"][0]["ticks"] - 1
    runs[(m[1], int(m[2]), m[3])] = (R, analyse(R, last), last)
NS = (50, 200, 1000)
print("| world | seed | commit | final state hash | retreat projects held (distinct) / entities | stale N=50 (projects/entities) | N=200 | N=1000 | open at run end | never threatened while held | dead entities | dead with a current project | dead with an ACTIVE project |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
tot = defaultdict(lambda: defaultdict(int))
for (w, s, sha), (R, (projs, dall, dcur, dact), last) in sorted(runs.items()):
    cnt = {N: [p for p in projs if p["end"] >= p["ref"] + N] for N in NS}
    ent = {N: len({p["e"] for p in cnt[N]}) for N in NS}
    row = lambda N: f"{len(cnt[N])}/{ent[N]}"
    print(f"| {w} | {s} | {sha} | {R['fin'][0]['state_hash'][:16]} | {len(projs)}/{len({p['e'] for p in projs})} | {row(50)} | {row(200)} | {row(1000)} | {sum(p['open_end'] for p in projs)} | {sum(p['never'] for p in projs)} | {len(dall)} | {len(dcur)} | {len(dact)} |")
    for key, v in (("projects", len(projs)), ("N50", len(cnt[50])), ("N200", len(cnt[200])), ("N1000", len(cnt[1000])), ("open", sum(p['open_end'] for p in projs)), ("dead", len(dall)), ("dead_cur", len(dcur)), ("dead_act", len(dact)), ("runs_with_holder", 1 if projs else 0), ("runs", 1)):
        tot[(w, sha)][key] += v
        tot[("ALL", sha)][key] += v
print("\n| world | commit | runs | runs with any retreat holder | retreat projects | stale N=50 | N=200 | N=1000 | open at run end | dead entities | dead with a current project | dead with an ACTIVE project |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for (w, sha), t in sorted(tot.items()): print(f"| {w} | {sha} | {t['runs']} | {t['runs_with_holder']} | {t['projects']} | {t['N50']} | {t['N200']} | {t['N1000']} | {t['open']} | {t['dead']} | {t['dead_cur']} | {t['dead_act']} |")
print("\n### Stale projects (N=50), per project: entity, project, held from-to, last present threat (or adoption tick if never), ticks after it, hp ratio at the last held tick\n")
print("| world | seed | commit | entity | project | held | reference tick | ticks after reference | never threatened | open at end | hp ratio at end of stretch |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for (w, s, sha), (R, (projs, *_), last) in sorted(runs.items()):
    for p in projs:
        if p["end"] >= p["ref"] + 50: print(f"| {w} | {s} | {sha} | {p['e']} | {p['pr']} | {p['start']}-{p['end']} | {p['ref']} | {p['span']} | {p['never']} | {p['open_end']} | {p['hp']:.2f} |")
