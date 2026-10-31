"""Offline answers from two profile_run outputs: analyze_profile.py <base.jsonl> <branch.jsonl>
 (a) formations by entities that were ghosts on base; (b) churn; (1) formation-pool and ghost series; (2) churn split with end reasons; (3) see the profile rows."""
import json, sys, collections
b, r = (json.loads(open(p).read().splitlines()[-1]) for p in sys.argv[1:3])
init_b, init_r = set(b["initial_ids"]), set(r["initial_ids"]); both_init = init_b & init_r; ghosts = set(b["ghost_ids"])
print("initial entity ids: base", len(init_b), "branch", len(init_r), "common", len(both_init), "| base ghost ids", len(ghosts), "initial on both", len(ghosts & both_init), "later-born", len(ghosts - init_b))
for lab, d in (("base", b), ("branch", r)):
    forms = d["forms"]; dis = d["dissolutions"]
    by_g = [f for f in forms if set(f[2]) & ghosts]; by_gi = [f for f in forms if set(f[2]) & ghosts & both_init]
    print(f"\n=== {lab}: hash {d['state_hash'][:12]} formations {len(forms)} dissolutions {len(dis)} events {d['events']} alive {d['alive']}")
    print(f"(a) formations with a base-ghost member {len(by_g)}; with one that is an initial id on both trees {len(by_gi)}; distinct base-ghost entities forming {len(set().union(*[set(f[2]) & ghosts for f in forms]) if forms else set())}")
    # last dissolution tick per member set, with reasons
    last_dis = {}; hist = collections.Counter(); reasons_churn = {10: collections.Counter(), 50: collections.Counter()}
    c10 = c50 = new = 0; sets = collections.Counter()
    ev = sorted([(x[0], 0, x) for x in dis] + [(f[0], 1, f) for f in forms], key=lambda z: (z[0], z[1]))  # dissolutions before formations in a tick
    for t, kind, x in ev:
        if kind == 0:
            last_dis[tuple(x[2])] = (t, x[4]); continue
        k = tuple(x[2]); sets[k] += 1
        ld = last_dis.get(k)
        if ld is None: new += 1; continue
        gap = t - ld[0]
        if gap <= 10: c10 += 1; reasons_churn[10][tuple(ld[1])] += 1
        if gap <= 50: c50 += 1; reasons_churn[50][tuple(ld[1])] += 1
        if gap > 50: new += 1
    top = sets.most_common(5)
    print(f"(2) same membership re-forming <=10 ticks after it dissolved: {c10}; <=50: {c50}; no prior dissolution of that membership or >50 ticks: {new}; distinct memberships {len(sets)}; top5 {top} share {sum(c for _, c in top)/max(len(forms),1):.2f}")
    print("    end reason of the dissolution before a <=10 re-form:", dict(reasons_churn[10]))
    print("    end reason of the dissolution before a <=50 re-form:", dict(reasons_churn[50]))
    # lifetime vs reason
    form_by_id = collections.defaultdict(list)
    for f in forms: form_by_id[f[1]].append(f[0])
    life = collections.defaultdict(collections.Counter)
    for t, gid, mem, _lu, why in dis:
        fs = [x for x in form_by_id.get(gid, []) if x <= t]
        if not fs: continue
        l = t - max(fs); bucket = "<=2" if l <= 2 else ("<=10" if l <= 10 else ">10")
        life[bucket][tuple(why)] += 1
    for bk in ("<=2", "<=10", ">10"): print(f"    groups ended with lifetime {bk} ticks, by reason: {dict(life[bk])}")
    pool = d["pool"]
    if pool:
        n = len(pool); win = 250
        print("(1) pool series (mean per tick: eligible pool / grouped-listed+ghost / ghost) by 250-tick windows, with formations in the window:")
        for i in range(0, n, win):
            seg = pool[i:i+win]; t0, t1 = seg[0][0], seg[-1][0]
            fw = sum(1 for f in forms if t0 <= f[0] <= t1)
            print(f"    t{t0}-{t1}: pool {sum(x[1] for x in seg)/len(seg):.1f} grouped {sum(x[2] for x in seg)/len(seg):.1f} ghost {sum(x[3] for x in seg)/len(seg):.2f} formations {fw}")
        print(f"    totals: pool-ticks {sum(x[1] for x in pool)}, ghost-ticks {sum(x[3] for x in pool)} (entity-ticks excluded from the pool by a ghost group_id)")
