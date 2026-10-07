"""usage: probe5k.py <mode audit|plain> <out.json> [ticks]; run with cwd = worktree under test."""
import sys, json, time
from dataclasses import replace
mode, out = sys.argv[1], sys.argv[2]
ticks = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from src.engine.kernel import Kernel
from src.engine.metrics import MetricsService
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
spec = WorldRepository("data/worlds").load_world("urban_political")
state, _ = WorldCompiler.compile(spec, seed=42)
fl = dict(state.feature_flags); fl["ENABLE_ADVENTURE_ROUTING"] = 1.0
state = replace(state, feature_flags=fl)
audit = mode == "audit"
prof = RuntimeProfile(name="p", hardware_class=HardwareClass.CLASS_B, max_ram_mb=2048, max_cpu_percent=100.0,
    max_worker_count=1, max_queue_depth=2000, max_replay_buffer_kb=0, max_observability_budget_percent=0.0,
    max_tick_budget_ms=1e9 if audit else 500.0)
flags = {"no_frame_pacing": True}
if audit: flags["audit_mode"] = True
k = Kernel(profile=prof, state=state, rng=DeterministicRNG(42), flags=flags)
s = []; t0 = time.time()
try:
    for t in range(1, ticks + 1):
        k.tick_once()
        if t % 100 == 0:
            m = MetricsService.extract_metrics(k.state)
            s.append({"tick": t, "alive": m.alive_entities, "gold": m.total_gold, "quest_active": m.quest_status_counts.get("ACTIVE", 0)})
            json.dump({"mode": mode, "elapsed": time.time()-t0, "samples": s}, open(out, "w"))
finally:
    k.shutdown()
n = len(s)
print(mode, {k_: round(sum(x[k_] for x in s)/n, 4) for k_ in ("alive", "gold", "quest_active")}, round(time.time()-t0))
