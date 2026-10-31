"""First-difference analysis of two probe2 logs. Usage: analyze.py parent.jsonl d914.jsonl
(a) every record before the first difference is identical, for all entities (sc scores, st state);
(b) the first difference is a score changed by retreat_pull: a COMBAT_RETREAT score that differs, backed by an rp record in the second log at that (tick, entity), nothing else differing at that tick for that entity before the state records."""
import json, sys
from collections import defaultdict
def load(p):
    sc, st, rp = defaultdict(list), {}, defaultdict(list)
    n = 0
    for l in open(p):
        r = json.loads(l); n += 1
        if r["k"] == "sc": sc[(r["t"], r["e"])].append(r["s"])
        elif r["k"] == "st": st[(r["t"], r["e"])] = (r["p"], r["hp"], r["a"], r["pr"], r["nt"], r["g"])
        elif r["k"] == "rp": rp[(r["t"], r["e"])].append((r["raw"], r["hp"], r["out"]))
    return sc, st, rp, n
A, B = sys.argv[1], sys.argv[2]
sa, ta, ra, na = load(A); sb, tb, rb, nb = load(B)
print(f"records: parent {na}, d914 {nb}; sc keys {len(sa)}/{len(sb)}; st keys {len(ta)}/{len(tb)}; rp calls parent {sum(map(len,ra.values()))}, d914 {sum(map(len,rb.values()))}")
keys = sorted(set(sa) | set(sb), key=lambda k: (k[0], k[1]))
first_sc = next((k for k in keys if sa.get(k) != sb.get(k)), None)
skeys = sorted(set(ta) | set(tb))
first_st = next((k for k in skeys if ta.get(k) != tb.get(k)), None)
print("first sc difference (tick, entity):", first_sc, "| first state difference:", first_st)
first_t = min([k[0] for k in (first_sc, first_st) if k], default=None)
if first_t is None: print("NO DIFFERENCE"); sys.exit(0)
print("identical for every tick before", first_t, "(all entities, sc and st)")
if first_sc and first_sc[0] <= (first_st[0] if first_st else 10**9):
    k = first_sc
    a, b = sa.get(k), sb.get(k)
    diffs = []
    for ca, cb in zip(a, b):
        for x, y in zip(ca, cb):
            if x != y: diffs.append((x[0], x[1], y[1], x[2], y[2]))
    print(f"at {k}: differing scorers (kind, parent, d914, target_parent, target_d914):")
    for d in diffs: print("  ", d)
    print("   rp calls at this (tick, entity) in d914:", rb.get(k), "| in parent:", ra.get(k))
    others = [d for d in diffs if "COMBAT_RETREAT" not in d[0]]
    # all other differing scorers at this key
    same_tick = sorted({e for (t, e) in set(sa) | set(sb) if t == k[0] and sa.get((t, e)) != sb.get((t, e))})
    print("   entities with any sc difference at this tick:", same_tick)
    ok = bool(rb.get(k)) and not others and (first_st is None or first_st[0] >= k[0])
    print("VERDICT (b): ", "PASS: first difference is a COMBAT_RETREAT score changed by retreat_pull, nothing else" if ok else "STOP: first difference is not only a retreat_pull score; see the lines above")
else:
    print("first difference is in STATE before any score difference:", first_st, ta.get(first_st), tb.get(first_st)); print("VERDICT (b): STOP")
