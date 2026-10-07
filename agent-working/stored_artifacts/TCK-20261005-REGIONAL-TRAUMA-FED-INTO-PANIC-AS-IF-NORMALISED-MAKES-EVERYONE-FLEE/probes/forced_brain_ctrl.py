"""Gate 3: what does the tactical pass DECIDE for a real entity with a live hostile adjacent?
Forces a direct evaluate_entity_intent call (read-only) on real states after each tick. usage: forced_brain.py <root> <world> <ticks>"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.content_semantics.faction import are_entities_hostile
from src.content_semantics.relation import RelationContext
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.tactical import TacticalDecisionSystem as T
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.domain_logic import SimulationDomainLogic as _SDL
_SDL.get_region_trauma = staticmethod(lambda s, p: 0.0)  # CONTROL: trauma off

C = collections.Counter()
EX = []
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        k.tick_once()
        st = k._state
        for e in st.entities.values():
            if not e.combat.alive or not e.lifecycle.active:
                continue
            ex, ey = e.navigation.position
            adj = [h for h in st.entities.values() if h.id != e.id and h.combat.alive and h.lifecycle.active
                   and abs(h.navigation.position[0] - ex) + abs(h.navigation.position[1] - ey) <= 1
                   and are_entities_hostile(e, h, RelationContext(distance=1.0, combat_engaged=True))]
            if not adj:
                continue
            h0 = CanonicalStateHasher.get_hash(st)[:8] if C["calls"] < 3 else None
            r = T.evaluate_entity_intent(st, e)
            pl = (r.task.payload_set or {}) if r.task is not None else {}
            hp = e.combat.hp / max(1, e.combat.max_hp)
            key = f"{getattr(r.task, 'work_kind_set', None) if r.task is not None else None}/{pl.get('action')}/{pl.get('reason')}"
            C["calls"] += 1
            C["decision." + key] += 1
            C["hp_lt_0.4" if hp < 0.4 else "hp_ge_0.4"] += 1
            C[f"decision_by_hp.{'low' if hp < 0.4 else 'ok'}." + key] += 1
            if len(EX) < 6:
                EX.append({"tick": st.tick, "entity": e.id, "hp": round(hp, 2), "bravery": round(e.identity.personality.bravery, 2),
                           "readiness": e.combat.readiness, "adj": [h.id for h in adj], "decision": key})
finally:
    k.shutdown()
print("FORCED-BRAIN", WORLD, TICKS, json.dumps(dict(sorted(C.items())), indent=1))
for x in EX:
    print("EX", json.dumps(x))
