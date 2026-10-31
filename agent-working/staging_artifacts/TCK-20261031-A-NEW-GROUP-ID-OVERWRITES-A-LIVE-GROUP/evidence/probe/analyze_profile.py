"""Offline answers from two profile_run outputs: analyze_profile.py <base.jsonl> <branch.jsonl>
 (a) formations by entities that were ghosts on base; (b) churn; (1) formation-pool and ghost series; (2) churn split with end reasons; (3) see the profile rows."""
import json, sys, collections
b, r = (json.loads(open(p).read().splitlines()[-1]) for p in sys.argv[1:3])
init_b, init_r = set(b["initial_ids"]), set(r["initial_ids"]); both_init = init_b & init_r; ghosts = set(b["ghost_ids"])
print("initial entity ids: base", len(init_b), "branch", len(init_r), "common", len(both_init), "| base ghost ids", len(ghosts), "initial on both", len(ghosts & both_init), "later-born", len(ghosts - init_b))
for lab, d in (("base", b), ("branch", r)):
    forms = d["forms"]; dis = list(d["dissolutions"]) + [[x[0], x[1], x[2], None, ["defection_pass_left_le1_member"]] for x in d.get("dis_other", [])]
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
    mi = d.get("mirror", {})
    print(f"    mirror check: ticks {mi.get('ticks')}, mirror predicted {mi.get('predicted')} dissolutions, code made {mi.get('actual')}; predicted-not-made {mi.get('n_pred_not_actual')}, made-not-predicted {mi.get('n_actual_not_pred')}; examples {mi.get('pred_not_actual', [])[:5]} / {mi.get('actual_not_pred', [])[:5]}")
    print(f"    dissolutions outside update_groups (defection pass): {len(d.get('dis_other', []))}; cooperation phase: calls {d.get('coop', {}).get('calls')}, dissolutions it made {d.get('coop', {}).get('dissolved')}, cohesion verdicts {d.get('coop', {}).get('statuses')}")
    pool = d["pool"]
    if pool:
        n = len(pool); win = 250
        print("(1) pool series (mean per tick: eligible pool / grouped-listed+ghost / ghost) by 250-tick windows, with formations in the window:")
        for i in range(0, n, win):
            seg = pool[i:i+win]; t0, t1 = seg[0][0], seg[-1][0]
            fw = sum(1 for f in forms if t0 <= f[0] <= t1)
            print(f"    t{t0}-{t1}: pool {sum(x[1] for x in seg)/len(seg):.1f} grouped {sum(x[2] for x in seg)/len(seg):.1f} ghost {sum(x[3] for x in seg)/len(seg):.2f} formations {fw}")
        print(f"    totals: pool-ticks {sum(x[1] for x in pool)}, ghost-ticks {sum(x[3] for x in pool)} (entity-ticks excluded from the pool by a ghost group_id)")

# ---- additions: contract-invalid split, formation-time contract facts, per-entity growth, policy ----
for lab, d in (("base", b), ("branch", r)):
    print(f"\n=== {lab}: audit_mode {d.get('audit_mode')} policy ticks {d.get('policy', {}).get('ticks')} policy changes {d.get('policy', {}).get('changes')}")
    why = collections.Counter(tuple(x[4]) for x in d["dissolutions"])
    print("  end reasons (all dissolutions):", dict(why))
    fc = d.get("form_contract", [])
    st = collections.Counter((x[3], x[5]) for x in fc)
    print(f"  at formation ({len(fc)} groups): (contract status, already past expiry_tick) counts {dict(st)}; contract missing at formation {sum(1 for x in fc if x[3] is None)}")
    exp = [x[4] for x in fc if x[4] is not None]
    print(f"  expiry_tick values at formation: -1 (none) {sum(1 for e in exp if e == -1)}, finite {sum(1 for e in exp if e != -1)}")
ga, gb = b.get("growth", {}), r.get("growth", {})
for t in sorted(set(ga) | set(gb), key=int):
    xa, xb = ga.get(t), gb.get(t)
    if not xa or not xb: continue
    print(f"\n=== per-entity growth at t{t}: living base {xa['living']} branch {xb['living']}")
    for nm in sorted(set(xa["named"]) | set(xb["named"])): print(f"  named {nm}: base {xa['named'].get(nm, 0)} branch {xb['named'].get(nm, 0)}")
    ent = sorted(set(xa["entries"]) | set(xb["entries"]), key=lambda k: -(xb["entries"].get(k, 0) - xa["entries"].get(k, 0)))[:12]
    for k in ent: print(f"  entries {k}: base {xa['entries'].get(k, 0)} branch {xb['entries'].get(k, 0)}")
    for k in sorted(set(xa["canon_json_bytes"]) | set(xb["canon_json_bytes"]), key=lambda k: -(xb["canon_json_bytes"].get(k, 0) - xa["canon_json_bytes"].get(k, 0)))[:8]:
        print(f"  canonical json bytes {k}: base {xa['canon_json_bytes'].get(k, 0)} branch {xb['canon_json_bytes'].get(k, 0)}")
