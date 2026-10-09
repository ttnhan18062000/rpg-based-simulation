"""D36 starvation measurement (read-only). usage: d36_probe.py <root> <world> <ticks> <seed>"""
import collections, json, sys, time
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
class Pin(ResourceGovernor):
    def _get_indicated_mode(self, profile, signals): return RuntimeMode.NORMAL
    def force_mode(self, mode, status, current_tick): return None
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED), governor=Pin(),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
C = collections.Counter(); DEAD = {}; CP = {1000, 1500, 2500, 5000, 7500, 10000}
T0 = time.perf_counter()
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state; t = st.tick
        for e in st.entities.values():
            alive = e.combat.alive and e.lifecycle.active
            if alive:
                h = e.biological.hunger
                if h >= 95.0: C["starving_entity_ticks"] += 1
                elif h >= 85.0: C["weakened_entity_ticks"] += 1
            elif e.id not in DEAD:
                c = e.lifecycle.passive_death_cause or e.lifecycle.death_reason
                DEAD[e.id] = (t, str(getattr(c, "value", c)))
        if t in CP:
            C[f"alive_t{t}"] = sum(1 for e in st.entities.values() if e.combat.alive and e.lifecycle.active)
            C[f"dead_t{t}"] = len(DEAD)
            C[f"starved_t{t}"] = sum(1 for v in DEAD.values() if v[1] == "STARVATION")
finally:
    k.shutdown()
for tdead, cause in DEAD.values(): C["death." + cause] += 1
C["deaths"] = len(DEAD); C["wall_seconds_x100"] = int((time.perf_counter() - T0) * 100)
print("D36", json.dumps(dict(world=WORLD, seed=SEED, ticks=TICKS, counts=dict(sorted(C.items())))))
