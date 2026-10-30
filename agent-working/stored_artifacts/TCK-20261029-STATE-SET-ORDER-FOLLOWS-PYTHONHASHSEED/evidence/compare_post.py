"""Post-merge check: base2 (origin/main c5139b410) vs B2 (merged B), s42 1000t, PYTHONHASHSEED=0; single-run tolerance max(1, 5%). Then merged B crowded_frontier s42 cross-seed hashes."""
import json, collections
R = "/data/vboxuser/Work/b_runs/out"
tol = lambda m: max(1, 0.05 * m)
stop = False
for w in ("frontier_living_world", "urban_political", "crowded_frontier"):
    a = json.load(open(f"{R}/post_base2_{w}_42_hs0.json")); b = json.load(open(f"{R}/post_B2_{w}_42_hs0.json"))
    da = collections.Counter(v[1] for v in a["final"].values() if not v[0]); db = collections.Counter(v[1] for v in b["final"].values() if not v[0])
    aa = sorted(int(k) for k, v in a["final"].items() if v[0]); ab = sorted(int(k) for k, v in b["final"].items() if v[0])
    bad = [("deaths", k, da[k], db[k]) for k in set(da) | set(db) if abs(da[k] - db[k]) > tol(da[k])]
    ca, cb = a.get("counters") or {}, b.get("counters") or {}
    bad += [("counter", k, ca.get(k, 0), cb.get(k, 0)) for k in set(ca) | set(cb) if abs((ca.get(k, 0) or 0) - (cb.get(k, 0) or 0)) > tol(ca.get(k, 0) or 0)]
    if abs(len(aa) - len(ab)) > tol(len(aa)): bad.append(("alive", "-", len(aa), len(ab)))
    stop |= bool(bad)
    print(f"{w} s42: hash {'MOVED' if a['final_hash']!=b['final_hash'] else 'same'} ({a['final_hash'][:12]} -> {b['final_hash'][:12]}); alive {len(aa)}/{len(ab)} {'same set' if aa==ab else 'SET DIFFERS'}; deaths {'same' if da==db else 'differ'}; counters {'same' if ca==cb else 'differ'}; outside tolerance: {bad if bad else 'none'}")
hs = {h: json.load(open(f"{R}/post_B2_crowded_frontier_42_hs{h}.json"))["final_hash"] if h else json.load(open(f"{R}/post_B2_crowded_frontier_42_hs0.json"))["final_hash"] for h in range(4)}
print("merged B crowded_frontier s42 1000t final hash by PYTHONHASHSEED:", {k: v[:16] for k, v in hs.items()}, "->", "IDENTICAL" if len(set(hs.values())) == 1 else "DIFFER -> STOP")
print("VERDICT:", "STOP" if stop or len(set(hs.values())) != 1 else "PASS on values and cross-seed (traces of moved hashes still owed)")
