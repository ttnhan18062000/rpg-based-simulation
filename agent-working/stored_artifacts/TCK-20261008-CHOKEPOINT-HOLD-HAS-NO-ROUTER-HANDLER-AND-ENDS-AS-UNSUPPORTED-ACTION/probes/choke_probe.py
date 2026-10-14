import sys, collections
sys.path.insert(0, sys.argv[1])
from dataclasses import replace
from src.config.profiles import PROD_SMALL
from src.core.state import TaskComponent
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.domain.action_router import ActionRouter
from src.engine.tactical import TacticalDecisionSystem as T
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import compile_world, DEFAULT_FLAGS, DEFAULT_SEED
state = compile_world("mechanic_scenario_combat_judgement_withdrawal")
F, H = 2, 1
ents = dict(state.entities)
for eid, pos in ((F, (1.0, 1.0)), (H, (1.0, 3.0))):
    e = ents[eid]
    props = dict(e.identity.properties); props["need_profile_id"] = "undead_purpose"
    ents[eid] = replace(e, navigation=replace(e.navigation, position=pos, target=None), identity=replace(e.identity, properties=props),
                        combat=replace(e.combat, hp=5000, max_hp=5000, atk=1, readiness=100.0, tactical_role="VANGUARD" if eid == F else e.combat.tactical_role, range=1),
                        task=TaskComponent(work_kind="ENTITY_ACT", payload={}))
object.__setattr__(state, "entities", ents)
object.__setattr__(state, "terrain", {(0, 1): "WALL", (2, 1): "WALL"})
object.__setattr__(state, "feature_flags", {**(state.feature_flags or {}), "ENABLE_COMBAT_ENGAGEMENT": "OFF"})
CALLS = collections.Counter(); REASONS = []
oe = ActionRouter.execute_action
def ex(entity, payload=None, current_tick=0, neighbor_view=None, context=None):
    r = oe(entity, payload, current_tick, neighbor_view, context)
    if entity.id == F:
        nav = getattr(r.get(entity.id), "navigation", None)
        REASONS.append((current_tick, (payload or {}).get("action"), str(getattr(nav, "failure_reason", None))))
    return r
ActionRouter.execute_action = staticmethod(ex)
od = T.evaluate_entity_intent
DEC = []
def de(st, entity, *a, **kw):
    r = od(st, entity, *a, **kw)
    if entity.id == F and r is not None and r.task is not None: DEC.append((st.tick, (r.task.payload_set or {}).get("action"), (r.task.payload_set or {}).get("reason")))
    return r
T.evaluate_entity_intent = staticmethod(de)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED),
           flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
rows = []
for i in range(60):
    k.tick_once(); e = k.state.entities[F]
    rows.append((k.state.tick, tuple(e.navigation.position), e.task.work_kind, dict(e.task.payload).get("action"), dict(e.task.payload).get("outcome"), dict(e.task.payload).get("reason"), str(e.navigation.movement_mode).split('.')[-1]))
k.shutdown()
print("DEC", DEC[:12]); print("ROUTER", REASONS[:12])
for r in rows[:14]: print(r)
print(rows[-1])
