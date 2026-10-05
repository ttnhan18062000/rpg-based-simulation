"""Who selects the target of a FRIENDLY_FIRE_ILLEGAL verdict? usage: ff_origin.py <root> <world> <ticks>

For every verify_attack_legality call that returns FRIENDLY_FIRE_ILLEGAL, record the immediate non-legality caller
(function and file), the attacker's task kind/action/payload keys, whether the target is in the attacker's tactical
hostile list (recomputed with tactical's own is_hostile_compat), and whether the attacker has an ACTIVE objective
whose target_entity_id is the target. Aggregates per (caller, task action, objective-targets-it).
"""
import collections
import inspect
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
import src  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.legality import LegalityServiceV2  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
C = collections.Counter()
ROWS = collections.Counter()
_vl = LegalityServiceV2.verify_attack_legality


def objective_targets(attacker, target_id):
    try:
        for proj in attacker.strategic.projects.values():
            for obj in getattr(proj, "objectives", {}).values() if isinstance(getattr(proj, "objectives", None), dict) else getattr(proj, "objectives", []):
                if getattr(obj, "target_entity_id", None) == target_id:
                    return str(getattr(getattr(obj, "status", None), "name", getattr(obj, "status", "?")))
    except Exception as exc:
        return f"err:{type(exc).__name__}"
    return "none"


def vl(attacker, target, state, *a, **k):
    res = _vl(attacker, target, state, *a, **k)
    if str(res[1]).endswith("FRIENDLY_FIRE_ILLEGAL"):
        frames = [f for f in inspect.stack()[1:8] if not f.filename.endswith("legality.py")]
        caller = f"{frames[0].function}@{frames[0].filename.split('src/')[-1]}" if frames else "?"
        chain = ">".join(f.function for f in frames[:4])
        pl = attacker.task.payload or {}
        ROWS[(caller, chain, attacker.task.work_kind, pl.get("action"), pl.get("reason"), objective_targets(attacker, target.id))] += 1
        C["ff_calls"] += 1
    return res


LegalityServiceV2.verify_attack_legality = staticmethod(vl)
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx_ = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx_)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        k.tick_once()
finally:
    k.shutdown()
print("FF-ORIGIN", WORLD, TICKS, json.dumps(dict(C)))
for row, n in ROWS.most_common(10):
    print("ROW", n, "caller,chain,work_kind,action,reason,objective_targets_it =", row)
