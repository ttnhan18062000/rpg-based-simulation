import json, sys
sys.path.insert(0, ".")
from tests.integration.campaigns import test_catalog_entity_spawn_wiring as t
ev = et = 0; out = {}
for seed in t._EPISODE_SEEDS:
    evt, c = t._run_episode(seed)
    k = evt.get("cooperation_event", 0); ev += k; et += c.entity_ticks
    out[str(seed)] = {"coop": k, "entity_ticks": c.entity_ticks, "basis": dict(c.cooperation_basis), "per": round(k / c.entity_ticks, 4)}
out["pooled_per_entity_tick"] = round(ev / et, 4)
print("PROBE " + json.dumps(out, sort_keys=True))
