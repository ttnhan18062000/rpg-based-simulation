"""First-difference attribution from two inst.py outputs (fixed 2026-10-31).

Usage: attribute.py inst_base.jsonl inst_B.jsonl

Trims are aligned by (tick, entity), never by position. `dropped` is compared as a SET. For the first set-differing trim
(smallest tick, then entity) it reports the concerns that differ with their urgencies and says TIE or NOT A TIE, and whether
the two arms had identical inputs (stored + add) at that trim.
"""
import json
import sys
from collections import defaultdict

L = lambda p: [json.loads(l) for l in open(p)]
A, B = L(sys.argv[1]), L(sys.argv[2])
g = lambda R, k: [r for r in R if r["k"] == k]


def trims(R):
    out = defaultdict(list)
    for r in g(R, "trim"):
        out[(r["tick"], r["e"])].append(r)
    return out


def inputs(r):
    """Distinct concern ids with their urgency as the trim sees them: stored first, then adds override (as the rebuilt dict does)."""
    u = {}
    for cid, urg in r["stored"]:
        u[cid] = urg
    for cid, urg in r["add"]:
        u[cid] = urg
    return u


ta, tb = trims(A), trims(B)
ka, kb = set(ta), set(tb)
both = sorted(ka & kb)
only_a, only_b = sorted(ka - kb), sorted(kb - ka)
set_diff, order_only, input_diff = [], 0, []
for k in both:
    x, y = ta[k][0], tb[k][0]  # one trim per (tick, entity) per phase call
    if inputs(x) != inputs(y):
        input_diff.append(k)
    if set(x["dropped"]) != set(y["dropped"]):
        set_diff.append(k)
    elif x["dropped"] != y["dropped"]:
        order_only += 1

print(f"trims: base {sum(len(v) for v in ta.values())}  B {sum(len(v) for v in tb.values())}  ((tick,entity) keys: base {len(ka)}, B {len(kb)}, both {len(both)}, only-base {len(only_a)}, only-B {len(only_b)})")
print(f"real (set) differing trims among shared keys: {len(set_diff)}   order-only differences (same set): {order_only}   shared keys whose inputs differ between arms: {len(input_diff)}")
if only_a or only_b:
    print(f"  first only-base keys: {only_a[:3]}   first only-B keys: {only_b[:3]}")

ha = {r["tick"]: r["h"] for r in g(A, "h")}
hb = {r["tick"]: r["h"] for r in g(B, "h")}
print("first hash-differing checkpoint:", next((t for t in sorted(ha) if ha[t] != hb.get(t)), None))
ca = {r["tick"]: r["c"] for r in g(A, "c")}
cb = {r["tick"]: r["c"] for r in g(B, "c")}
srt = lambda c: {e: sorted(map(tuple, v)) for e, v in c.items()}
t_set = next((t for t in sorted(ca) if srt(ca[t]) != srt(cb.get(t, {}))), None)
print("first tick stored concern sets differ:", t_set,
      [e for e in set(ca[t_set]) | set(cb[t_set]) if srt(ca[t_set]).get(e) != srt(cb[t_set]).get(e)] if t_set else None)

if not set_diff:
    print("FIRST SET DIFFERENCE: none among shared keys")
    sys.exit(0)
k = set_diff[0]
x, y = ta[k][0], tb[k][0]
ux = inputs(x)
da, db = set(x["dropped"]), set(y["dropped"])
only_in_a_drop = sorted(da - db)   # dropped by base, kept by B
only_in_b_drop = sorted(db - da)   # dropped by B, kept by base
urg_a = {c: ux[c] for c in only_in_a_drop}
urg_b = {c: ux[c] for c in only_in_b_drop}
all_urg = set(urg_a.values()) | set(urg_b.values())
tie = len(all_urg) == 1 and len(only_in_a_drop) == len(only_in_b_drop)
print(f"FIRST SET DIFFERENCE: tick {k[0]} entity {k[1]}")
print(f"  inputs identical between arms: {inputs(x) == inputs(y)}")
print(f"  dropped by base only: {[(c, urg_a[c]) for c in only_in_a_drop]}")
print(f"  dropped by B only   : {[(c, urg_b[c]) for c in only_in_b_drop]}")
print(f"  verdict: {'TIE' if tie else 'NOT A TIE'}"
      + (f" (all differing concerns at urgency {next(iter(all_urg))})" if tie else f" (urgencies {sorted(all_urg)})"))
print(f"  base dropped (in order): {x['dropped']}")
print(f"  B dropped (in order)   : {y['dropped']}")
