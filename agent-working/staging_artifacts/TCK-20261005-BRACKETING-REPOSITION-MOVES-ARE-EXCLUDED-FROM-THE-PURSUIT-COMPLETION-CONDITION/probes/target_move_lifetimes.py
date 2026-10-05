"""Lifetime of every ENTITY_MOVE that carries a payload target_id, grouped by (movement mode, payload reason).

usage: target_move_lifetimes.py <root> <world> <ticks>

A "move" starts the first tick an entity shows ENTITY_MOVE with a target_id and ends when its (work kind, mode, reason, target id)
signature changes or the entity task stops being that move. Per group: moves, lifetime median/p90/max, how many were still running at
the end of the run, how many outlived their target (target dead/inactive/gone at the last sighting), and how many were held with a
dead target for more than 20 ticks. Settings: audit_mode=True, max_tick_budget_ms=1e9, seed 42.
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
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
LIVE, DONE = {}, []


def sig(e):
    pl = e.task.payload or {}
    if e.task.work_kind == "ENTITY_MOVE" and pl.get("target_id") is not None:
        return (getattr(e.navigation.movement_mode, "name", str(e.navigation.movement_mode)), pl.get("reason"), pl.get("target_id"))
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
            if rec is not None and rec["sig"] != s:
                DONE.append(LIVE.pop(e.id))
                rec = None
            if rec is None:
                rec = LIVE[e.id] = {"entity": e.id, "sig": s, "start": t, "dead_since": None}
            rec["last"] = t
            tgt = st.entities.get(s[2])
            dead = tgt is None or not tgt.combat.alive or not tgt.lifecycle.active
            if dead and rec["dead_since"] is None:
                rec["dead_since"] = t
        for eid in list(LIVE):
            if eid not in seen:
                DONE.append(LIVE.pop(eid))
finally:
    k.shutdown()
for rec in LIVE.values():
    rec["running_at_end"] = True
    DONE.append(rec)
groups = collections.defaultdict(list)
for r in DONE:
    groups[(r["sig"][0], r["sig"][1])].append(r)
out = {}
for g, rs in sorted(groups.items(), key=lambda kv: str(kv[0])):
    life = sorted(r["last"] - r["start"] + 1 for r in rs)
    n = len(life)
    held_dead = sum(1 for r in rs if r["dead_since"] is not None and r["last"] - r["dead_since"] > 20)
    out[f"{g[0]}/{g[1]}"] = {
        "moves": n, "median": life[n // 2], "p90": life[int(n * 0.9)], "max": life[-1],
        "running_at_end": sum(1 for r in rs if r.get("running_at_end")),
        "outlived_target": sum(1 for r in rs if r["dead_since"] is not None),
        "held_with_dead_target_over_20_ticks": held_dead,
    }
print("TARGET-MOVES", WORLD, TICKS, json.dumps(out))
