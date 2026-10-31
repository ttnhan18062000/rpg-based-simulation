"""Designer check 1. Usage: designer_counts.py <log.jsonl> [after_tick=452]
Retreat-active tick = alive entity whose current project id contains 'combat_retreat' (st). Also counted: ticks with a retreat_pull call that changes a score (rp), and ticks where COMBAT_RETREAT is the top RAW score of a goal-scoring call (sc; not the post-modifier order).
Classification (th, computed from the same tick's state): threat present = acting_threat_to (src/ai/goals/present_threat.py: a perceived hostile's current task attacks/pursues the subject, or it hit the subject within NEED_WAKE_CADENCE ticks)
OR a perceived hostile orthogonally adjacent (decision 32, LegalityServiceV2.is_adjacent); hp line = hp ratio 0.5 (CombatRetreatScorer: hp_ratio >= 0.5 and not emotion.is_fleeing -> utility 0, src/ai/goals/scorers.py)."""
import json, sys
from collections import defaultdict
P = sys.argv[1]; AFTER = int(sys.argv[2]) if len(sys.argv) > 2 else 452
st, th, rp, sc = {}, {}, defaultdict(list), defaultdict(list)
for l in open(P):
    r = json.loads(l)
    if r["k"] == "st": st[(r["t"], r["e"])] = r
    elif r["k"] == "th": th[(r["t"], r["e"])] = r
    elif r["k"] == "rp": rp[(r["t"], r["e"])].append(r)
    elif r["k"] == "sc": sc[(r["t"], r["e"])].append(r)
def cls(t, e):
    x = th.get((t, e))
    if x is None: return None
    thr = x["acting"] or x["adj"]; low = x["hpr"] < 0.5
    return ("threat" if thr else "no threat") + (", hp<0.5" if low else ", hp>=0.5"), x
CELLS = ["threat, hp<0.5", "threat, hp>=0.5", "no threat, hp<0.5", "no threat, hp>=0.5"]
def table(title, keys):
    byent = defaultdict(lambda: defaultdict(int))
    for (t, e) in keys:
        c = cls(t, e); byent[e][c[0] if c else "unclassified"] += 1
    print(f"\n### {title}\n"); print("| entity | ticks | " + " | ".join(CELLS) + " | unclassified |"); print("|---|---|" + "---|" * (len(CELLS) + 1))
    tot = defaultdict(int)
    for e in sorted(byent):
        row = byent[e]; n = sum(row.values()); print(f"| {e} | {n} | " + " | ".join(str(row[c]) for c in CELLS) + f" | {row['unclassified']} |")
        for c in CELLS + ["unclassified"]: tot[c] += row[c]
    print(f"| all | {sum(tot.values())} | " + " | ".join(str(tot[c]) for c in CELLS) + f" | {tot['unclassified']} |")
active = sorted(k for k, r in st.items() if r["a"] and "combat_retreat" in (r["pr"] or "") and k[0] > AFTER)
table(f"A. retreat-active project ticks after t{AFTER}", active)
rpt = sorted(k for k in rp if k[0] > AFTER)
table(f"B. ticks with a retreat_pull call that changes a score, after t{AFTER}", rpt)
win = sorted(k for k, L in sc.items() if k[0] > AFTER and any(x["top"] and x["top"][0][0].endswith("COMBAT_RETREAT") and x["top"][0][1] > 0 for x in L))
table(f"C. ticks where COMBAT_RETREAT is the top raw score of a scoring call, after t{AFTER}", win)
# spans over the whole run
print("\n### Retreat project spans (whole run; contiguous ticks with a combat_retreat current project, alive)\n")
print("| entity | spans (start-end, project id) | ends before t2000 | open at the last tick |"); print("|---|---|---|---|")
per = defaultdict(list)
for (t, e), r in sorted(st.items()):
    if r["a"] and "combat_retreat" in (r["pr"] or ""): per[e].append((t, r["pr"]))
last = max(t for t, _ in st)
for e in sorted(per):
    spans = []; s = prev = None
    for t, p in per[e]:
        if s is not None and (t != prev + 1 or p != sp): spans.append((s, prev, sp)); s = None
        if s is None: s, sp = t, p
        prev = t
    spans.append((s, prev, sp))
    print(f"| {e} | " + "; ".join(f"{a}-{b} {p}" for a, b, p in spans) + f" | {sum(1 for a, b, p in spans if b < last)} | {'YES' if spans[-1][1] == last else 'no'} |")
print(f"\nlast tick in log: {last}; alive entities with a retreat span open at the last tick: {sum(1 for e in per if per[e][-1][0] == last)}")
# positive control
x = cls(42, 18)
print("\n### Positive control: entity 18 at t42 (the known retreat_pull case)\n")
print("th record:", th.get((42, 18))); print("rp record(s):", [(r['raw'], r['hp'], r['out']) for r in rp.get((42, 18), [])]); print("classification:", x[0] if x else None)
