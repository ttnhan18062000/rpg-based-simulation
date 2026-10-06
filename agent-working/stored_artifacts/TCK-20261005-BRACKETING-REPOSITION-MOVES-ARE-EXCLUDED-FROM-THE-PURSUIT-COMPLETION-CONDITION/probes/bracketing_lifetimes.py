"""Lifetime of every BRACKETING ENTITY_MOVE. usage: bracketing_lifetimes.py <root> <world> <ticks>

For each entity task that is ENTITY_MOVE with payload reason BRACKETING, track from the tick it is first seen until the task
signature (work kind, reason, bracket tile, target id) changes. Records: lifetime in ticks, whether the entity ever stood on the
bracket tile, minimum Manhattan distance to the bracket tile and to the hostile target, whether the hostile target was still
alive at the end, how the move ended, and how many times evaluate_entity_intent was called for the entity while the move was held
(the "was the decision re-entered" question). Settings: audit_mode=True, max_tick_budget_ms=1e9, seed 42.
"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
import src  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.tactical import TacticalDecisionSystem as T  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
EVAL = collections.Counter()  # entity id -> evaluate_entity_intent calls (running total)
_ev = T.evaluate_entity_intent


def ev(state, entity, *a, **k):
    EVAL[entity.id] += 1
    return _ev(state, entity, *a, **k)


T.evaluate_entity_intent = staticmethod(ev)
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
LIVE = {}  # entity id -> record
DONE = []


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def sig(e):
    pl = e.task.payload or {}
    if e.task.work_kind == "ENTITY_MOVE" and pl.get("reason") == "BRACKETING":
        return (tuple(pl.get("target_position") or ()), pl.get("target_id"))
    return None


try:
    for _ in range(TICKS):
        k.tick_once()
        st = k._state
        t = st.tick
        seen = set()
        for e in st.entities.values():
            s = sig(e)
            if s is None:
                continue
            seen.add(e.id)
            rec = LIVE.get(e.id)
            tgt = st.entities.get(s[1])
            if rec is not None and rec["sig"] != s:
                rec["end"] = t
                rec["ended_by"] = "new_bracketing_decision"
                DONE.append(rec)
                rec = None
            if rec is None:
                rec = LIVE[e.id] = {"entity": e.id, "sig": s, "start": t, "evals_at_start": EVAL[e.id], "stood_on_bracket": False,
                                    "min_d_bracket": 10**9, "min_d_target": 10**9, "mode": getattr(e.navigation.movement_mode, "name", None)}
            rec["last"] = t
            rec["stood_on_bracket"] = rec["stood_on_bracket"] or (tuple(e.navigation.position) == s[0])
            rec["min_d_bracket"] = min(rec["min_d_bracket"], dist(e.navigation.position, s[0]))
            if tgt is not None:
                rec["min_d_target"] = min(rec["min_d_target"], dist(e.navigation.position, tgt.navigation.position))
                rec["target_alive"] = bool(tgt.combat.alive and tgt.lifecycle.active)
            rec["nav_target_is_bracket"] = tuple(e.navigation.target or ()) == s[0]
            rec["evals_during"] = EVAL[e.id] - rec["evals_at_start"]
        for eid in list(LIVE):
            if eid not in seen:
                rec = LIVE.pop(eid)
                e = st.entities.get(eid)
                rec["end"] = t
                rec["ended_by"] = "task_changed" if e is not None else "entity_gone"
                DONE.append(rec)
finally:
    k.shutdown()
for rec in LIVE.values():
    rec["end"] = None
    rec["ended_by"] = "still_running_at_end"
    DONE.append(rec)
life = sorted((r["last"] - r["start"] + 1) for r in DONE)
n = len(life)
out = {
    "bracketing_moves": n,
    "lifetime_ticks_sorted_head": life[:10],
    "lifetime_ticks_median": life[n // 2] if n else None,
    "lifetime_ticks_p90": life[int(n * 0.9)] if n else None,
    "lifetime_ticks_max": life[-1] if n else None,
    "ever_stood_on_bracket_tile": sum(1 for r in DONE if r["stood_on_bracket"]),
    "decision_reentered_while_held": sum(1 for r in DONE if r.get("evals_during", 0) > 0),
    "ended_by": dict(collections.Counter(r["ended_by"] for r in DONE)),
    "target_still_alive_at_end": sum(1 for r in DONE if r.get("target_alive")),
    "nav_target_was_bracket_tile_at_last_sight": sum(1 for r in DONE if r.get("nav_target_is_bracket")),
    "distinct_entities": len({r["entity"] for r in DONE}),
}
print("BRACKETING", WORLD, TICKS, json.dumps(out))
for r in sorted(DONE, key=lambda r: -(r["last"] - r["start"]))[:5]:
    print("LONGEST", json.dumps({k2: (list(v) if isinstance(v, tuple) else v) for k2, v in r.items() if k2 != "sig"}), "sig", r["sig"])
