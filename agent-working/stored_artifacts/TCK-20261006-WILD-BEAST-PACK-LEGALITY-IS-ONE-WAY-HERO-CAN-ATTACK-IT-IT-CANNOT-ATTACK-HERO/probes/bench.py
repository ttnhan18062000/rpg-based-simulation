import os, sys, json
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_movement_state
from src.engine.legality import LegalityServiceV2 as L
from src.content_semantics.faction import get_faction_id_str, get_faction_semantics_service
if os.environ.get("BEFORE"):
    def _old(a, t, c):
        svc = get_faction_semantics_service(); src, tf = get_faction_id_str(a), get_faction_id_str(t)
        if L._declares(svc.repo, src, tf): return bool(svc.is_hostile_compat(src, tf, c))
        return a.identity.faction != t.identity.faction
    L._attack_permitted = staticmethod(_old)
n = int(sys.argv[1])
r = BenchHarness(PERF_PROFILES["PERF_2GB_LOCAL"]).run_benchmark(scenario_id=f"MOVEMENT_{n}", initial_state=build_movement_state(entity_count=n), warmup_ticks=2, sample_ticks=int(sys.argv[2]))
print(json.dumps({"arm": "before" if os.environ.get("BEFORE") else "after", "n": n, "p50": r.get("p50_tick_compute_ms"), "p95": r["p95_tick_compute_ms"], "top": sorted(((k, round(v["avg"], 1)) for k, v in r["phase_breakdown"].items()), key=lambda x: -x[1])[:4]}))
