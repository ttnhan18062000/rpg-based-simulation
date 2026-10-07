"""Where do OUT_OF_RANGE attacks come from? usage: atk_origin.py <root> <world> <ticks> [seed]
Counts: ATTACK decisions emitted out of reach at decision time; execute_attack calls by outcome and by whether the
call is on the decision tick (fresh) or later (held)."""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 42
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.domain.combat_actions import CombatActions
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.tactical import TacticalDecisionSystem as T
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

C = collections.Counter()
DECIDED = {}
CUR = {"state": None}
_ev = T.evaluate_entity_intent


def ev(state, entity, *a, **k):
    r = _ev(state, entity, *a, **k)
    CUR["state"] = state
    pl = (r.task.payload_set or {}) if r is not None and r.task is not None else {}
    if pl.get("action") == "ATTACK":
        t = state.entities.get(pl.get("target_id"))
        if t is not None:
            d = abs(t.navigation.position[0] - entity.navigation.position[0]) + abs(t.navigation.position[1] - entity.navigation.position[1])
            C["attack_decisions"] += 1
            if d > max(1, entity.combat.range) or (entity.combat.range <= 1.5 and d > 1):
                C["attack_decisions_out_of_reach_at_decision"] += 1
            DECIDED[entity.id] = state.tick
    return r


T.evaluate_entity_intent = staticmethod(ev)
_ea = CombatActions.execute_attack


def ea(entity, payload=None, current_tick=0, neighbor_view=None, context=None):
    r = _ea(entity, payload, current_tick, neighbor_view, context)
    up = r.get(entity.id)
    nav = getattr(up, "navigation", None)
    reason = getattr(nav, "failure_reason", None)
    tick = getattr(context, "tick", current_tick)
    fresh = DECIDED.get(entity.id) == tick
    C[f"exec.{'fresh' if fresh else 'held'}.{reason}"] += 1
    return r


CombatActions.execute_attack = staticmethod(ea)
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        k.tick_once()
finally:
    k.shutdown()
print("ATK-ORIGIN", WORLD, SEED, json.dumps(dict(sorted(C.items()))))
