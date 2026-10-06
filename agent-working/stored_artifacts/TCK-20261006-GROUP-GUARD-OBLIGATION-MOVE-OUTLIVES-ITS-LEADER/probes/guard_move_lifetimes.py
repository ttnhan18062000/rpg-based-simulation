"""Lifetime of GUARD ENTITY_MOVEs (reasons CONTRACT_OBLIGATION_GUARD and GUARDING_ALLY), plus, per move, the ticks a LIVE mover
spent on it while its target was no longer interacting and while it no longer shared the target's group.

usage: guard_move_lifetimes.py <root> <world> <ticks> [legacy]
`legacy` patches tracked_move_complete back to the pre-gate-4 PURSUE-only logic (what origin/main 9299891a9 has); a `git archive`
export of main cannot be used because it omits untracked data the ResourceRegistry needs.

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
if len(sys.argv) > 4 and sys.argv[4] == "legacy":
    # The pre-fix completion logic (#347): PURSUE only, live target in reach; a dead or gone target ended nothing.
    from src.core.movement_modes import MovementMode  # noqa: E402
    from src.engine.candidate_selector import MovementCandidateSelector as _M  # noqa: E402

    def _legacy(entity, entities):
        if entity.navigation.movement_mode != MovementMode.PURSUE:
            return False
        tid = entity.task.payload.get("target_id")
        if tid is None:
            return False
        tgt = entities.get(tid)
        if tgt is None or not tgt.lifecycle.active or not tgt.combat.alive:
            return False
        ex, ey = entity.navigation.position
        tx, ty = tgt.navigation.position
        dist = abs(ex - tx) + abs(ey - ty)
        reach = entity.combat.range
        return dist <= reach and not (reach <= 1.5 and dist > 1)

    _M.tracked_move_complete = staticmethod(_legacy)
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
LIVE, DONE = {}, []


def sig(e):
    pl = e.task.payload or {}
    if e.task.work_kind == "ENTITY_MOVE" and pl.get("target_id") is not None and getattr(e.navigation.movement_mode, "name", "") == "GUARD":
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
                rec = LIVE[e.id] = {"entity": e.id, "sig": s, "start": t, "dead_since": None, "live_mover_dead_target_ticks": 0,
                                    "mover_dead": False, "live_not_interacting": 0, "live_group_gone": 0}
            rec["last"] = t
            tgt = st.entities.get(s[2])
            dead = tgt is None or not tgt.combat.alive or not tgt.lifecycle.active
            if dead and rec["dead_since"] is None:
                rec["dead_since"] = t
            mover_ok = e.lifecycle.active and e.combat.alive
            rec["mover_dead"] = not mover_ok
            if mover_ok and not dead:
                tp = tgt.task.payload or {}
                if not (tgt.task.work_kind == "ENTITY_ACT" and tp.get("action") == "INTERACT"):
                    rec["live_not_interacting"] += 1
                if e.identity.group_id is None or e.identity.group_id != tgt.identity.group_id:
                    rec["live_group_gone"] += 1
            if dead and mover_ok:
                rec["live_mover_dead_target_ticks"] += 1  # a LIVE entity holding a move whose target is gone
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
    held_dead = sum(1 for r in rs if r["live_mover_dead_target_ticks"] > 20)
    corpse = sum(1 for r in rs if r["mover_dead"])
    out[f"{g[0]}/{g[1]}"] = {
        "moves": n, "median": life[n // 2], "p90": life[int(n * 0.9)], "max": life[-1],
        "running_at_end": sum(1 for r in rs if r.get("running_at_end")),
        "outlived_target": sum(1 for r in rs if r["dead_since"] is not None),
        "held_by_a_LIVE_mover_with_dead_target_over_20_ticks": held_dead,
        "mover_was_dead_at_last_sighting": corpse,
        "live_mover_ticks_target_not_interacting": sum(r["live_not_interacting"] for r in rs),
        "live_mover_ticks_group_gone": sum(r["live_group_gone"] for r in rs),
        "live_mover_ticks_target_dead": sum(r["live_mover_dead_target_ticks"] for r in rs),
    }
print("GUARD-MOVES", WORLD, TICKS, json.dumps(out))
for r in sorted((r for r in DONE if r.get("running_at_end") or (r["dead_since"] is not None and r["last"] - r["dead_since"] > 20)),
                key=lambda r: -(r["last"] - r["start"]))[:5]:
    print("HELD", json.dumps({"entity": r["entity"], "mode_reason_target": list(r["sig"]), "start": r["start"], "last": r["last"], "dead_since": r["dead_since"], "live_mover_dead_target_ticks": r["live_mover_dead_target_ticks"]}))
