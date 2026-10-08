"""Do penniless subjects eat? usage: free_eat.py <root> <world> <ticks> <seed>"""
import collections, json, sys
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.town_resolution import TownResolutionSystem as TR
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
C = collections.Counter(); PEND = {}
from src.engine.domain.core_actions import CoreActions
_es = CoreActions.execute_survival
def es(entity, action, current_tick):
    if action == "EAT":
        C["eat_executed"] += 1
        C["eat_executed.gold_lt_5" if entity.inventory.gold < 5 else "eat_executed.gold_ge_5"] += 1
        PEND[entity.id] = (current_tick, entity.biological.hunger, entity.inventory.gold)
    return _es(entity, action, current_tick)
CoreActions.execute_survival = staticmethod(es)
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        for eid, (t, h0, g0) in list(PEND.items()):
            if st.tick > t:
                e = st.entities.get(eid)
                if e is not None:
                    dropped = e.biological.hunger < h0 - 5
                    C[f"hunger_dropped.gold_{'lt5' if g0 < 5 else 'ge5'}.{'yes' if dropped else 'no'}"] += 1
                    C[f"gold_after.gold_{'lt5' if g0 < 5 else 'ge5'}.{'lower' if e.inventory.gold < g0 else 'same_or_higher'}"] += 1
                del PEND[eid]
finally:
    k.shutdown()
print("FREE-EAT", WORLD, SEED, json.dumps(dict(sorted(C.items()))))
