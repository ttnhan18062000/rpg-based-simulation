import json, sys, numpy as np
from scipy.optimize import nnls
rows = json.load(open(sys.argv[1]))
for r in rows: r["tick_ex"] = r["tick_ms"] - r["combat_ms"]
def r2(y, p): return 1 - ((y-p)**2).sum()/((y-y.mean())**2).sum()
def fit(rows, target, feats, label, per_ex=False):
    X = np.array([[r[f] for f in feats] for r in rows], float); y = np.array([r[target] for r in rows], float)
    w, _ = nnls(X, y); p = X@w
    print(f"{label}: target={target} feats={feats} w={[round(x,3) for x in w]} pooled R2={r2(y,p):.3f}")
    for fam in sorted({r['sc'] for r in rows}):
        m = np.array([r['sc']==fam for r in rows])
        print(f"   {fam:10s} actual/pred={y[m].sum()/max(p[m].sum(),1e-9):.2f}  R2={r2(y[m],p[m]):.2f}")
    for ex in sorted({r['ex'] for r in rows}):
        m = np.array([r['ex']==ex for r in rows]); print(f"   exec {ex:10s} actual/pred={y[m].sum()/p[m].sum():.2f}")
    return w
print("rows", len(rows))
fit(rows, "tick_ex", ["entities_active","movers","leads"], "A tick_ex demand")
fit(rows, "tick_ex", ["entities_active","movers","leads","dirty_total"], "B +dirty_total")
fit(rows, "tick_ms", ["entities_active","movers","leads"], "C tick incl combat (shows why excluded)")
fit([r for r in rows if r['ex']=='sequential'], "tick_ex", ["entities_active","movers","leads"], "A-seq")
fit([r for r in rows if r['ex']=='thread'], "tick_ex", ["entities_active","movers","leads"], "A-thread")
fit(rows, "loco_ms", ["movers"], "L1 loco~movers")
fit(rows, "loco_ms", ["move_cand"], "L2 loco~move_cand (post-policy)")
fit(rows, "integ_ms", ["dirty_total"], "I1 integ~dirty_total")
fit(rows, "integ_ms", ["dirty_strat"], "I2 integ~dirty_strat")
fit(rows, "integ_ms", ["dirty_total","leads","entities_active"], "I3 integ~dirty+leads+ent")
print("modes seen:", {r['mode'] for r in rows})
