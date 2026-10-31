"""SimQ corpus sweep compare: every anchored key and pillar, a25619971 vs d914bace7, delta, in/out of the shared tolerance (the test's _within_score_tolerance + band +/-1).
Usage: compare_sweep.py   (run from the repo worktree so tests.simulation_quality imports; reads /data/vboxuser/Work/simq_sweep/<sha>/data/calibration/<key>/quality_report.json)"""
import json, sys, os
sys.path.insert(0, os.getcwd())
from tests.simulation_quality.test_grade_regression import _within_score_tolerance, GRADE_ORDER
R = "/data/vboxuser/Work/simq_sweep"
anch = json.load(open("tests/simulation_quality/fixtures/grade_anchors.json"))
keys = [k for k in anch if not k.startswith("_")]
def rep(sha, key):
    try: return json.load(open(f"{R}/{sha}/data/calibration/{key}/quality_report.json")).get("pillars", {})
    except FileNotFoundError: return None
rows, missing = [], []
for key in keys:
    a, b = rep("a25619971", key), rep("d914bace7", key)
    if a is None or b is None: missing.append(key); continue
    for pillar, tgt in anch[key].items():
        if not isinstance(tgt, dict) or not ("status" in tgt or "grade" in tgt): continue   # fixed 2026-10-31: scored anchors have grade+score and no status
        pa, pb = a.get(pillar), b.get(pillar)
        if pa is None or pb is None: rows.append((key, pillar, "MISSING PILLAR", None, None, None, None, None)); continue
        sa, sb = pa.get("normalized_score"), pb.get("normalized_score")
        moved = (pa.get("status"), pa.get("grade"), sa) != (pb.get("status"), pb.get("grade"), sb)
        def ok(p, s):
            if tgt.get("status", "ok") != "ok": return p.get("status") != "ok"  # no-data anchor stays no-data
            if p.get("status") != "ok": return False
            band = abs(GRADE_ORDER.index(p["grade"]) - GRADE_ORDER.index(tgt["grade"])) <= 1
            return band and _within_score_tolerance(s, tgt["score"], abs_floor=tgt.get("abs_floor", 0.05))
        rows.append((key, pillar, "moved" if moved else "same", tgt.get("score"), sa, sb, ok(pa, sa), ok(pb, sb)))
print("| key | pillar | anchor | a25619971 | d914bace7 | delta | in tolerance before | in tolerance after |")
print("|---|---|---|---|---|---|---|---|")
n_moved = n_out = 0
for key, pillar, st, an, sa, sb, oa, ob in rows:
    if st == "same": continue
    n_moved += 1
    if st == "MISSING PILLAR": print(f"| {key} | {pillar} | - | MISSING PILLAR | | | | |"); continue
    d = None if (sa is None or sb is None) else round(sb - sa, 4)
    out = (oa and not ob)
    n_out += bool(out)
    print(f"| {key} | {pillar} | {an} | {sa} | {sb} | {d} | {oa} | {ob}{'  <<< OUT' if out else ''} |")
print(f"\nkeys with both reports: {len(keys)-len(missing)} of {len(keys)}; missing: {missing}")
print(f"pillar anchors compared: {len(rows)}; moved by #769: {n_moved}; moved from in to out of tolerance: {n_out}; already out before: {sum(1 for r in rows if r[6] is False)}")

print("\n## Already outside tolerance at the parent a25619971 (pre-existing reds, not #769's; no re-anchor under this ticket)\n")
print("| key | pillar | anchor | a25619971 | d914bace7 | moved by #769 |")
print("|---|---|---|---|---|---|")
for key, pillar, st, an, sa, sb, oa, ob in rows:
    if oa is False:
        print(f"| {key} | {pillar} | {an} | {sa} | {sb} | {'yes' if st != 'same' else 'no'} |")
