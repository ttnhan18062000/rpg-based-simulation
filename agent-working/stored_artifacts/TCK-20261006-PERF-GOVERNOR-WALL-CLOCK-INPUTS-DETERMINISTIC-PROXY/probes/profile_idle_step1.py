"""Step-1 profiling pass: idle scenario, cProfile over 5 measured ticks (after 3 warm-up), for n given on argv. Read-only."""
import cProfile, pstats, sys, json
sys.path.insert(0, ".")
from src.config.profiles import HardwareClass, RuntimeProfile
from src.engine.kernel import Kernel
from src.perf.scenarios import build_idle_state
from src.platform.rng import DeterministicRNG
n = int(sys.argv[1])
p = RuntimeProfile(name="calib", hardware_class=HardwareClass.CLASS_B, max_ram_mb=4096, max_cpu_percent=90.0, max_worker_count=0,
                   max_queue_depth=500, max_replay_buffer_kb=4096, max_observability_budget_percent=10.0, max_tick_budget_ms=100000.0)
k = Kernel(p, build_idle_state(entity_count=n), DeterministicRNG(7), flags={"no_frame_pacing": True, "no_replay": True})
for _ in range(3): k.tick_once()
pr = cProfile.Profile(); pr.enable()
buckets = {}
for _ in range(5):
    k.tick_once()
    for b, v in k._phase_costs.items(): buckets[b] = buckets.get(b, 0.0) + v / 5
pr.disable(); k.shutdown()
print("N", n, "BUCKETS(ms/tick) top:", json.dumps(dict(sorted(buckets.items(), key=lambda x: -x[1])[:8]), indent=0))
st = pstats.Stats(pr); st.sort_stats(sys.argv[2] if len(sys.argv) > 2 else "tottime").print_stats(int(sys.argv[3]) if len(sys.argv) > 3 else 12)
