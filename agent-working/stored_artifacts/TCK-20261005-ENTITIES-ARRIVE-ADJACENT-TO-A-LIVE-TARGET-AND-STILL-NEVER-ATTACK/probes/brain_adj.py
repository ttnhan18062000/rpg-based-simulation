"""What does the tactical pass decide when it runs for an entity with a live hostile adjacent?
usage: brain_adj.py <root> <world> <ticks>"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.content_semantics.faction import are_entities_hostile
from src.content_semantics.relation import RelationContext
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.tactical import TacticalDecisionSystem as T
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

C = collections.Counter()
_ev = T.evaluate_entity_intent


def ev(state, entity, neighbors=None, *a, **k):
    r = _ev(state, entity, neighbors, *a, **k)
    ex, ey = entity.navigation.position
    adj = [e for e in state.entities.values() if e.id != entity.id and e.combat.alive
           and abs(e.navigation.position[0] - ex) + abs(e.navigation.position[1] - ey) <= 1
           and are_entities_hostile(entity, e, RelationContext(distance=1.0, combat_engaged=True))]
    if not adj:
        return r
    C["calls_with_live_hostile_adjacent"] += 1
    pl = (r.task.payload_set or {}) if r.task is not None else {}
    hp = entity.combat.hp / max(1, entity.combat.max_hp)
    key = f"{getattr(r.task, 'work_kind_set', None) if r.task is not None else None}/{pl.get('action')}/{pl.get('reason')}"
    C["decision." + key] += 1
    C["hp_lt_0.4" if hp < 0.4 else "hp_ge_0.4"] += 1
    return r


T.evaluate_entity_intent = staticmethod(ev)
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        k.tick_once()
finally:
    k.shutdown()
print("BRAIN-ADJ", WORLD, TICKS, json.dumps(dict(sorted(C.items())), indent=1))
