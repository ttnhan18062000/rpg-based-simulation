"""Per-pillar event counts and first event difference behind each moved pillar. Usage: events_diff.py <label_parent> <label_d914> (files in out/).
event_id is excluded from every comparison (src/observability/events.py:56 defaults it to uuid4; nothing in the simulation reads it).
Rows are quality_scores.jsonl (one per scored event, in event order); a pillar's rows are compared in order."""
import json, sys
from collections import defaultdict
O = "/data/vboxuser/Work/simq_probes/out/"
A, B = sys.argv[1], sys.argv[2]
def rows(l): return [{k: v for k, v in json.loads(x).items() if k != "event_id"} for x in open(O + l + ".quality_scores.jsonl")]
ra, rb = rows(A), rows(B)
pa = json.load(open(O + A + ".report.json"))["pillars"]; pb = json.load(open(O + B + ".report.json"))["pillars"]
first_any = next((i for i, (x, y) in enumerate(zip(ra, rb)) if x != y), None)
if first_any is None and len(ra) != len(rb): first_any = min(len(ra), len(rb))
print(f"scored rows: parent {len(ra)}, d914 {len(rb)}; first differing row index {first_any}"
      + (f" at tick {(ra[first_any] if first_any < len(ra) else rb[first_any])['tick']}" if first_any is not None else ""))
by = lambda R: defaultdict(list, {p: [r for r in R if r["pillar"] == p] for p in {r["pillar"] for r in R}})
ba, bb = by(ra), by(rb)
print("| pillar | score parent | score d914 | events parent | events d914 | scored rows parent | d914 | first differing scored row (tick, event_type, entity, delta) parent -> d914 |")
print("|---|---|---|---|---|---|---|---|")
for p in sorted(set(pa) | set(pb)):
    x, y = pa.get(p, {}), pb.get(p, {})
    la, lb = ba.get(p, []), bb.get(p, [])
    fi = next((i for i, (u, v) in enumerate(zip(la, lb)) if u != v), None)
    if fi is None and len(la) != len(lb): fi = min(len(la), len(lb))
    f = lambda L, i: "-" if i is None or i >= len(L) else f"({L[i]['tick']}, {L[i]['event_type']}, e{L[i]['entity_id']}, {L[i]['delta']})"
    moved = (x.get("normalized_score"), x.get("status")) != (y.get("normalized_score"), y.get("status"))
    print(f"| {p}{' (moved)' if moved else ''} | {x.get('normalized_score')} | {y.get('normalized_score')} | {x.get('event_count')} | {y.get('event_count')} | {len(la)} | {len(lb)} | {f(la, fi)} -> {f(lb, fi)} |")
