"""What is the attacker's task on the ticks FOLLOWING an OUT_OF_RANGE verdict?

usage: oor_follow.py <root> <world> <ticks>

For each OUT_OF_RANGE verdict inside execute_attack, print the attacker's task (work_kind, payload
action/target/outcome/reason), distance to the verdict's target, target liveness, and readiness for the
verdict tick and the 4 ticks after it. Same settings as oor_probe.py.
"""
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
import src  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.engine.domain.combat_actions import CombatActions  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.legality import LegalityServiceV2  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
LAST = []
WATCH = []  # [attacker, target, verdict_tick]
SEEN = {}
CALLS = []  # (tick, attacker, target, reason) for every execute_attack verdict
_vl = LegalityServiceV2.verify_attack_legality


def vl(attacker, target, state, *a, **k):
    res = _vl(attacker, target, state, *a, **k)
    LAST.append((attacker.id, target.id, state.tick, str(res[1])))
    return res


LegalityServiceV2.verify_attack_legality = staticmethod(vl)
_ea = CombatActions.execute_attack


def ea(*a, **k):
    LAST.clear()
    r = _ea(*a, **k)
    if LAST:
        att, tgt, tick, reason = LAST[-1]
        CALLS.append((tick, att, tgt, reason))
        if reason.endswith("OUT_OF_RANGE"):
            if not any(w[:3] == [att, tgt, tick] for w in WATCH):
                WATCH.append([att, tgt, tick])
            print("OOR-VERDICT tick", tick, "attacker", att, "target", tgt, flush=True)
    return r


CombatActions.execute_attack = staticmethod(ea)
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        pre_tick = k._state.tick
        k.tick_once()
        s = k._state
        for att, tgt, vt in WATCH:
            if not (vt <= pre_tick <= vt + 2000):
                continue
            e, te = s.entities.get(att), s.entities.get(tgt)
            if e is None:
                print("t", pre_tick, "attacker", att, "GONE")
                continue
            pl = e.task.payload or {}
            d = None if te is None else abs(e.navigation.position[0] - te.navigation.position[0]) + abs(e.navigation.position[1] - te.navigation.position[1])
            sig = (att, tgt, vt, e.task.work_kind, pl.get("action"), pl.get("target_id"), te is not None and te.combat.alive)
            if SEEN.get((att, tgt, vt)) == sig:
                continue  # print only when the task/target signature changes
            SEEN[(att, tgt, vt)] = sig
            print("t", pre_tick, "(verdict t", vt, ") attacker", att, "task", e.task.work_kind, "act", pl.get("action"),
                  "tid", pl.get("target_id"), "outcome", pl.get("outcome"), "reason", pl.get("reason"),
                  "dist", d, "target_alive", None if te is None else te.combat.alive, "ready", e.combat.readiness, flush=True)
finally:
    k.shutdown()
print("ALL execute_attack verdicts:", CALLS)
