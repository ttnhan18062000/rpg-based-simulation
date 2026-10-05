"""Why do dispatched attacks not reach resolve_attack? usage: dispatch_probe.py <root> <world> <ticks>"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.combat import CombatResolutionSystem
from src.engine.domain.combat_actions import CombatActions
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.legality import LegalityServiceV2
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

C = collections.Counter()
ROWS = []
LAST = []
_vl = LegalityServiceV2.verify_attack_legality


def vl(attacker, target, state, *a, **k):
    res = _vl(attacker, target, state, *a, **k)
    LAST.append((attacker.id, target.id, state.tick, bool(res[0]), str(res[1]), attacker.combat.readiness))
    C[f"legality.legal={res[0]}.{res[1]}"] += 1
    return res


LegalityServiceV2.verify_attack_legality = staticmethod(vl)
_ea = CombatActions.execute_attack


def ea(*a, **k):
    C["execute_attack_calls"] += 1
    LAST.clear()
    r = _ea(*a, **k)
    ROWS.append({"inside_execute_attack_legality": list(LAST)})
    ROWS.append({"args": [type(x).__name__ for x in a][:4], "ret_type": type(r).__name__,
                 "keys": sorted(r.keys())[:4] if isinstance(r, dict) else None})
    return r


CombatActions.execute_attack = staticmethod(ea)
_ra = CombatResolutionSystem.resolve_attack


def ra(*a, **k):
    C["resolve_attack_calls"] += 1
    return _ra(*a, **k)


CombatResolutionSystem.resolve_attack = staticmethod(ra)
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
print("DISPATCH-PROBE", WORLD, TICKS, json.dumps(dict(sorted(C.items())), indent=1))
for r in ROWS[:8]:
    print("ROW", r)
