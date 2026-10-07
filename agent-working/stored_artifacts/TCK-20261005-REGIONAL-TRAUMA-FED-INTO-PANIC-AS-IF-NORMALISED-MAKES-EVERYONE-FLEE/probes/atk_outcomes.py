"""execute_attack call outcomes: failure_reason mix and per-attacker concentration. usage: atk_outcomes.py <root> <world> <ticks>"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.domain.combat_actions import CombatActions
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

C = collections.Counter()
BY = collections.Counter()
_ea = CombatActions.execute_attack


def ea(entity, *a, **k):
    r = _ea(entity, *a, **k)
    up = r.get(entity.id) if isinstance(r, dict) else None
    nav = getattr(up, "navigation", None)
    reason = getattr(nav, "failure_reason", None)
    C[f"reason.{reason}"] += 1
    BY[entity.id] += 1
    return r


CombatActions.execute_attack = staticmethod(ea)
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        k.tick_once()
finally:
    k.shutdown()
print("ATK-OUTCOMES", WORLD, json.dumps(dict(sorted(C.items()))), "top_attackers", BY.most_common(4))
