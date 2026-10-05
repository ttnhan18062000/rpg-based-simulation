"""Which term of AppraisalSystem.evaluate_emotional_state drives is_fleeing for entities with a live hostile adjacent?
Recomputes the documented terms (src/engine/cognition.py) on real states. usage: panic_terms.py <root> <world> <ticks>"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.content_semantics.faction import are_entities_allied, are_entities_hostile
from src.content_semantics.relation import RelationContext
from src.engine.cognition import AppraisalSystem, SensoryFilter
from src.engine.domain_logic import SimulationDomainLogic
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

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
            if not any(h.id != e.id and h.combat.alive and abs(h.navigation.position[0] - ex) + abs(h.navigation.position[1] - ey) <= 1
                       and are_entities_hostile(e, h, RelationContext(distance=1.0, combat_engaged=True))
                       for h in st.entities.values()):
                continue
            raw = SimulationDomainLogic.get_neighbor_view(st, e, radius=10.0)
            neigh = SensoryFilter.filter_saliency(e, raw, max_targets=5)
            trauma = SimulationDomainLogic.get_region_trauma(st, e.navigation.position)
            emo = AppraisalSystem.evaluate_emotional_state(e, neigh, region_trauma=trauma, social_context=e.social)
            if not emo.is_fleeing:
                C["not_fleeing"] += 1
                continue
            C["fleeing"] += 1
            hp = e.combat.hp / max(1, e.combat.max_hp)
            allies = 1
            hostiles = 0
            for n in neigh:
                if are_entities_allied(e, n):
                    allies += 1
                elif are_entities_hostile(e, n, RelationContext(distance=abs(n.navigation.position[0] - ex) + abs(n.navigation.position[1] - ey), combat_engaged=True)):
                    hostiles += 1
            terms = []
            if trauma * 0.5 > 0:
                terms.append(f"trauma({round(trauma * 0.5, 2)})")
            if hp < 0.4:
                terms.append("low_hp")
            if hostiles > allies * 2:
                terms.append(f"outnumbered({hostiles}h/{allies}a)")
            nem = sum(1 for n in neigh if n.id in e.social.nemesis_ids or e.social.grudge_history.get(n.id, 0.0) > 0.5)
            if nem:
                terms.append("nemesis_or_grudge")
            C["terms." + "+".join(terms or ["none"])] += 1
            C["trauma_ge_0.8" if trauma >= 0.8 else "trauma_lt_0.8"] += 1
            if len(EX) < 5:
                EX.append({"tick": st.tick, "entity": e.id, "hp": round(hp, 2), "trauma": round(trauma, 2), "panic": round(emo.panic_level, 2),
                           "bravery": round(e.identity.personality.bravery, 2), "allies": allies, "hostiles": hostiles, "terms": terms})
finally:
    k.shutdown()
print("PANIC-TERMS", WORLD, TICKS, json.dumps(dict(sorted(C.items())), indent=1))
for x in EX:
    print("EX", json.dumps(x))
