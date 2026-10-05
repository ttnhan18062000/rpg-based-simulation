"""Tick-by-tick trace of one entity. usage: one_entity.py <root> <world> <entity_id> <ticks>"""
import sys

ROOT, WORLD, EID, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.tactical import TacticalDecisionSystem as T
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

CALLED = {}
_ev = T.evaluate_entity_intent


def ev(state, entity, *a, **k):
    r = _ev(state, entity, *a, **k)
    if entity.id == EID:
        pl = (r.task.payload_set or {}) if r.task is not None else {}
        CALLED[state.tick] = (getattr(r.task, "work_kind_set", None) if r.task is not None else None,
                              pl.get("action"), pl.get("reason"))
    return r


T.evaluate_entity_intent = staticmethod(ev)
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        pre = k._state
        k.tick_once()
        e = k._state.entities.get(EID)
        if e is None:
            continue
        pl = e.task.payload or {}
        tgt = pl.get("target_id")
        te = k._state.entities.get(tgt) if isinstance(tgt, int) else None
        d = None if te is None else abs(e.navigation.position[0] - te.navigation.position[0]) + abs(e.navigation.position[1] - te.navigation.position[1])
        print("t", pre.tick, "pos", e.navigation.position, "nav_target", e.navigation.target, "mode", getattr(e.navigation.movement_mode, "name", e.navigation.movement_mode),
              "task", e.task.work_kind, "reason", pl.get("reason"), "act", pl.get("action"), "tid", tgt, "dist", d,
              "ready", e.combat.readiness, "eval_called", CALLED.get(pre.tick))
finally:
    k.shutdown()
