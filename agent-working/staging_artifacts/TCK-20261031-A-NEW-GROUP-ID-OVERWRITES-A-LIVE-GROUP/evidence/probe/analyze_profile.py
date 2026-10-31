"""Offline answer for (a) and (b) from two profile_run outputs: analyze_profile.py <base.jsonl> <branch.jsonl>"""
import json, sys, collections
b, r = (json.loads(open(p).read().splitlines()[-1]) for p in sys.argv[1:3])
init_b, init_r = set(b["initial_ids"]), set(r["initial_ids"])
ghosts = set(b["ghost_ids"]); both_init = init_b & init_r
print("initial entity ids: base", len(init_b), "branch", len(init_r), "common", len(both_init), "| base ghosts", len(ghosts), "of which initial-state ids on both trees", len(ghosts & both_init), "later-born", len(ghosts - init_b))
for lab, d in (("base", b), ("branch", r)):
    forms = d["forms"]
    by_g = [f for f in forms if set(f[2]) & ghosts]
    by_g_init = [f for f in forms if set(f[2]) & ghosts & both_init]
    print(f"(a) {lab}: formations {len(forms)}; with a base-ghost member {len(by_g)}; with a base-ghost member that is an initial-state id on both trees {len(by_g_init)}; distinct base-ghost entities forming {len(set().union(*[set(f[2]) & ghosts for f in forms]) if forms else set())}")
    last = {}; churn = 0; first = 0; sets = collections.Counter()
    for t, gid, mem in forms:
        k = tuple(mem); sets[k] += 1
        if k in last and t - last[k] <= 10: churn += 1
        else: first += 1
        last[k] = t
    top = sets.most_common(5)
    print(f"(b) {lab}: formations {len(forms)}; same member set re-forming within 10 ticks {churn}; not re-forming within 10 ticks {first}; distinct member sets {len(sets)}; top5 sets {top}; top5 share {sum(c for _, c in top)/max(len(forms),1):.2f}")
