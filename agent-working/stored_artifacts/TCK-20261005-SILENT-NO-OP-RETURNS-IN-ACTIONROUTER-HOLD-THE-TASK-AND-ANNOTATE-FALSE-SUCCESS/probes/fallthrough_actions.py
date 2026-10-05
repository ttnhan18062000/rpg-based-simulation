"""Which action names reach ActionRouter.execute_action's final fall-through? usage: fallthrough_actions.py <root> <world> <ticks>

Run on a tree where the fall-through reports UNSUPPORTED_ACTION; tallies every action name that produced that reason.
"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
import src  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.core.enums import ReasonCode  # noqa: E402
from src.engine.domain.action_router import ActionRouter  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
C = collections.Counter()
_ea = ActionRouter.execute_action


def ea(entity, payload=None, current_tick=0, *a, **k):
    res = _ea(entity, payload, current_tick, *a, **k)
    action = payload.get("action") if payload else None
    upd = res.get(entity.id)
    reason = getattr(getattr(upd, "navigation", None), "failure_reason", None)
    if reason == ReasonCode.UNSUPPORTED_ACTION:
        C[f"unsupported:{action}"] += 1
    elif reason == ReasonCode.ACTION_WITHHELD_BY_POSTURE:
        C[f"withheld:{action}"] += 1
    C["dispatch.total"] += 1
    return res


ActionRouter.execute_action = staticmethod(ea)
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
print("FALLTHROUGH", WORLD, TICKS, json.dumps(dict(sorted(C.items()))))
