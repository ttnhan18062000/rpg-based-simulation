"""Trace the 'adjacent to a live target, never attacks' case. usage: adj_probe.py <root> <world> <ticks>
Per tick, after the kernel tick, for every LIVE entity holding an ACTIVE defeat_enemy objective whose live target is
within Manhattan distance 1: classify what happened for that entity this tick.
"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.domain.combat_actions import CombatActions
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.legality import LegalityServiceV2
from src.engine.tactical import TacticalDecisionSystem as T
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

C = collections.Counter()
EVAL = {}     # (tick, eid) -> summary of evaluate_entity_intent return
LEG = {}      # (tick, attacker) -> (target, legal, reason)
SAMPLES = []

_ev = T.evaluate_entity_intent


def ev(state, entity, *a, **k):
    r = _ev(state, entity, *a, **k)
    task = r.task
    pl = (task.payload_set or {}) if task is not None else {}
    EVAL[(state.tick, entity.id)] = {
        "work_kind": getattr(task, "work_kind_set", None) if task is not None else None,
        "action": pl.get("action"), "reason": pl.get("reason"), "has_target_id": pl.get("target_id") is not None,
        "empty": r.is_empty() if hasattr(r, "is_empty") else None,
    }
    return r


T.evaluate_entity_intent = staticmethod(ev)
_vl = LegalityServiceV2.verify_attack_legality


def vl(attacker, target, state, *a, **k):
    res = _vl(attacker, target, state, *a, **k)
    LEG[(state.tick, attacker.id)] = (target.id, res[0], str(res[1]))
    return res


LegalityServiceV2.verify_attack_legality = staticmethod(vl)
_ea = CombatActions.execute_attack
EXEC = collections.Counter()


def ea(*a, **k):
    EXEC["execute_attack"] += 1
    return _ea(*a, **k)


CombatActions.execute_attack = staticmethod(ea)

repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        pre = k._state
        k.tick_once()
        tick = pre.tick
        for e in pre.entities.values():
            if not e.combat.alive:
                continue
            s = e.strategic
            proj = s.projects.get(s.current_project_id or "")
            if proj is None:
                continue
            obj = next((o for o in proj.objectives if o.id == s.current_objective_id), None)
            if obj is None or obj.target_entity_id is None or str(getattr(obj.kind, "value", obj.kind)) != "defeat_enemy":
                continue
            tgt = pre.entities.get(obj.target_entity_id)
            if tgt is None or not tgt.combat.alive:
                continue
            d = abs(e.navigation.position[0] - tgt.navigation.position[0]) + abs(e.navigation.position[1] - tgt.navigation.position[1])
            if d > 1:
                continue
            C["adjacent_live_target_samples"] += 1
            C[f"readiness_ge_100.{e.combat.readiness >= 100.0}"] += 1
            ev_r = EVAL.get((tick, e.id))
            lg = LEG.get((tick, e.id))
            if ev_r is None:
                C["tactical_pass_not_called_this_tick"] += 1
                key = "NOT_CALLED"
            else:
                key = f"called->{ev_r['work_kind']}/{ev_r['action']}/{ev_r['reason']}/empty={ev_r['empty']}"
                C["tactical_pass_called"] += 1
            C["outcome." + key] += 1
            if lg is not None:
                C[f"legality_checked.legal={lg[1]}.{lg[2]}"] += 1
            if len(SAMPLES) < 6:
                SAMPLES.append({"tick": tick, "entity": e.id, "target": tgt.id, "readiness": e.combat.readiness,
                                "dist": d, "eval": ev_r, "legality": lg, "task_work_kind": e.task.work_kind,
                                "task_payload_keys": sorted((e.task.payload or {}).keys())})
finally:
    k.shutdown()
print("ADJ-PROBE", WORLD, TICKS, json.dumps(dict(sorted(C.items())), indent=1), dict(EXEC))
for s in SAMPLES:
    print("SAMPLE", json.dumps(s, default=str))
