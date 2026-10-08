"""SURV-07 funnel. usage: need_funnel.py <root> <world> <ticks> [seed]
Counts survival actions (EAT/SLEEP/REST) and REST_IN_PLACE dispatches, alive at t=1100, deaths by passive cause (ever seen)."""
import collections, json, sys
ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3]); SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 42
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.domain.core_actions import CoreActions
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.tactical import TacticalDecisionSystem as T
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
C = collections.Counter(); E = {}
_es = CoreActions.execute_survival
def es(entity, action, current_tick):
    C[f"executed.{action}"] += 1
    p = entity.strategic.projects.get(entity.strategic.current_project_id) if entity.strategic.current_project_id else None
    C[f"executed.{action}.by_proj.{getattr(p.kind,'value',p.kind) if p else None}"] += 1
    C[f"executed.{action}.entity_distinct"] += 0
    E.setdefault(action, set()).add(entity.id)
    return _es(entity, action, current_tick)
CoreActions.execute_survival = staticmethod(es)
_ev = T.evaluate_entity_intent
def ev(state, entity, *a, **k):
    r = _ev(state, entity, *a, **k)
    pl = (r.task.payload_set or {}) if r is not None and r.task is not None else {}
    if pl.get("action") in ("EAT", "SLEEP", "REST"):
        C[f"decided.{pl['action']}" + (".in_place" if pl.get("reason") == "REST_IN_PLACE" else "")] += 1
    return r
T.evaluate_entity_intent = staticmethod(ev)
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
causes = {}; seen = set(); maxhunger = collections.Counter()
try:
    for t in range(TICKS):
        k.tick_once()
        for e in k.state.entities.values():
            seen.add(e.id)
            c = e.lifecycle.passive_death_cause or e.lifecycle.death_reason
            if c is not None: causes[e.id] = str(getattr(c, "value", c))
        if k.state.tick in (500, 1100, 1500) or t == TICKS - 1:
            alive = sum(1 for e in k.state.entities.values() if e.combat.alive and e.lifecycle.active)
            C[f"alive_at_t{k.state.tick}"] = alive
finally:
    k.shutdown()
C["entities_seen"] = len(seen)
for a, ids in E.items(): C[f"distinct_entities.{a}"] = len(ids)
for c in causes.values(): C[f"death.{c}"] += 1
print("NEED-FUNNEL", WORLD, SEED, TICKS, json.dumps(dict(sorted(C.items()))))
