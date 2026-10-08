"""Births of fractional positions: an entity integral at tick t-1 and fractional at tick t, classified by whether the flow
field produced a step from that entity's old position that tick. usage: frac_birth.py <root> <world> <ticks> [seed]"""
import collections, json, sys
ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3]); SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 42
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.systems.world_systems.navigation import FlowFieldService as F
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
def frac(p): return p[0] != int(p[0]) or p[1] != int(p[1])
FLOW = set(); CALLS = collections.Counter()
_g = F.get_flow_direction
def g(cur, kind, state):
    r = _g(cur, kind, state)
    CALLS["flow_calls"] += 1
    if r is not None and r[0] != int(r[0]):
        CALLS["flow_calls_returning_fractional_vector"] += 1
        FLOW.add(tuple(cur))
    return r
F.get_flow_direction = staticmethod(g)
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
C = collections.Counter(); prev = {}; kinds = collections.Counter(); other = []
try:
    for _ in range(TICKS):
        FLOW.clear()
        k.tick_once()
        for e in k.state.entities.values():
            p = tuple(e.navigation.position); o = prev.get(e.id)
            if o is not None and not frac(o) and frac(p):
                C["births"] += 1
                if o in FLOW: C["births_from_flow_field_step"] += 1; kinds[e.kind] += 1
                else:
                    C["births_other"] += 1; other.append((k.state.tick, e.id, e.kind, o, p))
            prev[e.id] = p
finally:
    k.shutdown()
print("FRAC-BIRTH", WORLD, SEED, TICKS, json.dumps(dict(C)), json.dumps(dict(CALLS)), "flow-birth kinds", json.dumps(dict(kinds)))
print("FRAC-BIRTH-OTHER", json.dumps(other[:10]))
