"""Run the campaign episode of test_catalog_entity_spawn_wiring on the tree in cwd; print pooled cooperation share and per-seed event totals as JSON."""
import json, sys
sys.path.insert(0, ".")
from tests.integration.campaigns import test_catalog_entity_spawn_wiring as t
out = {}
pc = pt = 0
for seed in t._EPISODE_SEEDS:
    ev, counts = t._run_episode(seed)
    tot = sum(ev.values()); c = ev.get("cooperation_event", 0)
    pc += c; pt += tot
    out[str(seed)] = {"coop": c, "total": tot, "top": dict(ev.most_common(14))}
out["pooled"] = round(pc / max(1, pt), 4)
print("PROBE " + json.dumps(out, sort_keys=True))
