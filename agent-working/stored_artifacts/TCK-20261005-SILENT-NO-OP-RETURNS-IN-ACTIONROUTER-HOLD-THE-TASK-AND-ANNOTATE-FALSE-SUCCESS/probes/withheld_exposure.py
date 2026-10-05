"""Held-task exposure: how many ATTACK/SKILL dispatches does the posture gate withhold, and for how long per entity?

usage: withheld_exposure.py <root> <world> <ticks>

Wraps ActionRouter.execute_action and recomputes the gate's own condition (action_router.py posture gate) from the
entity BEFORE delegating, so the count does not depend on the return shape and is valid before and after the fix.
Reports: total withheld dispatches, entities affected, longest run of consecutive ticks one entity was withheld
against one target, and the number of runs of length >= 2 (a "held" task: the same withheld dispatch repeated).
Settings: audit_mode=True, max_tick_budget_ms=1e9, seed 42.
"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
import src  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.engine.domain.action_router import ActionRouter  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
ACCEPTED = ("engage", "probe", "skirmish", "vengeance_engage")
C = collections.Counter()
LAST = {}  # (entity, target) -> (last_tick, run_len)
RUNS = collections.defaultdict(list)  # (entity, target) -> [run lengths]
ENTS = set()
_ea = ActionRouter.execute_action


def ea(entity, payload=None, current_tick=0, *a, **k):
    action = payload.get("action") if payload else None
    C["dispatch.total"] += 1
    if action in ("ATTACK", "SKILL"):
        C[f"dispatch.{action}"] += 1
        tgt = payload.get("target_id")
        props = entity.identity.properties
        posture = props.get("last_combat_posture") if props.get("last_combat_posture_target") == tgt else None
        if posture is not None and posture not in ACCEPTED:
            C["withheld"] += 1
            ENTS.add(entity.id)
            key = (entity.id, tgt)
            prev = LAST.get(key)
            if prev and current_tick == prev[0]:
                C["withheld.same_tick_duplicate"] += 1  # the same dispatch seen twice in one tick
            elif prev and current_tick == prev[0] + 1:
                LAST[key] = (current_tick, prev[1] + 1)  # run length counts distinct consecutive ticks
            else:
                if prev:
                    RUNS[key].append(prev[1])
                LAST[key] = (current_tick, 1)
    return _ea(entity, payload, current_tick, *a, **k)


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
for key, v in LAST.items():
    RUNS[key].append(v[1])
runs = sorted((n for v in RUNS.values() for n in v), reverse=True)
out = dict(sorted(C.items()))
out["entities_withheld"] = len(ENTS)
out["withheld_distinct_entity_ticks"] = sum(runs)
out["runs"] = len(runs)
out["runs_ge_2"] = sum(1 for n in runs if n >= 2)
out["longest_run_ticks"] = runs[0] if runs else 0
out["top_runs"] = runs[:5]
print("WITHHELD-EXPOSURE", WORLD, TICKS, json.dumps(out))
