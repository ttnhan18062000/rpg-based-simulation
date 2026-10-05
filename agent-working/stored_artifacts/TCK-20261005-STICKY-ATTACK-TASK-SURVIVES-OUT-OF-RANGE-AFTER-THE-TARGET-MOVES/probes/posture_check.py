"""Does the combat-posture gate (action_router.py:94-102) explain a held ATTACK task that never re-dispatches?

usage: posture_check.py <root> <world> <entity_id> <from_tick> <to_tick>

Prints, per tick in the window, the entity's task action/target, its recorded last_combat_posture and the
target that posture was recorded for, and whether the router's gate would withhold the attack. Also counts
ActionRouter ATTACK calls withheld by the gate (return value has no combat update).
"""
import sys

ROOT, WORLD, EID, T0, T1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
sys.path.insert(0, ROOT)
import src  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
ACCEPTED = ("engage", "probe", "skirmish", "vengeance_engage")
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(T1 + 1):
        pre = k._state.tick
        k.tick_once()
        if pre < T0:
            continue
        e = k._state.entities.get(EID)
        if e is None:
            print("t", pre, "GONE")
            continue
        pl = e.task.payload or {}
        props = e.identity.properties
        posture, ptgt = props.get("last_combat_posture"), props.get("last_combat_posture_target")
        withheld = ptgt == pl.get("target_id") and posture is not None and posture not in ACCEPTED
        print("t", pre, "task", e.task.work_kind, pl.get("action"), "tid", pl.get("target_id"), "outcome", pl.get("outcome"),
              "posture", posture, "posture_target", ptgt, "gate_withholds", withheld, "ready", e.combat.readiness)
finally:
    k.shutdown()
