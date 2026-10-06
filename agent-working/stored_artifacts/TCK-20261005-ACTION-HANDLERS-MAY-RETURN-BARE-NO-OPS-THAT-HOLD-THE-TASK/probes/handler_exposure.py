"""Held-task exposure per action kind, by handler outcome class.

usage: handler_exposure.py <root> <world> <ticks>

Wraps ActionRouter.execute_action and classifies the ACTOR's returned update:
  FAIL:<reason>  navigation.failure_reason set, or combat.outcome_kind == REJECTED
  BARE           no field set beyond entity_id / readiness_delta (a dispatch that did nothing)
  EFFECT         anything else (the handler changed something)
A "run" is consecutive dispatches BY ONE ENTITY of the same (action, target) with no other dispatch between them:
the same sticky task re-dispatched. Ticks may have gaps (a combat action costs readiness, so a held task repeats
about every 5 ticks); the longest gap inside a run is reported as max_gap. Reports, per action kind: dispatches, class counts, runs, runs >= 2, longest run, and the number of
BARE dispatches that fall in a run >= 2 (the defect: a do-nothing action held).
Settings: audit_mode=True, max_tick_budget_ms=1e9, seed 42.
"""
import collections
import dataclasses
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
IGNORED = {"entity_id", "readiness_delta"}


def classify(upd):
    if upd is None:
        return "FAIL:NO_ACTION_UPDATE"
    nav = upd.navigation
    if nav is not None and nav.failure_reason:
        r = nav.failure_reason
        return "FAIL:" + str(getattr(r, "value", r))
    if upd.combat is not None and upd.combat.outcome_kind == "REJECTED":
        return "FAIL:REJECTED:" + str(upd.combat.failure_reason)
    for f in dataclasses.fields(upd):
        if f.name in IGNORED:
            continue
        v = getattr(upd, f.name)
        if v not in (None, False, 0, 0.0, [], {}, ()):
            return "EFFECT"
    return "BARE"


RECORDS = collections.defaultdict(list)  # entity -> [(tick, action, target, class)]
_ea = ActionRouter.execute_action


def ea(entity, payload=None, current_tick=0, *a, **k):
    out = _ea(entity, payload, current_tick, *a, **k)
    action = payload.get("action") if payload else None
    cls = classify(out.get(entity.id) if out else None)
    RECORDS[entity.id].append((current_tick, action, payload.get("target_id") if payload else None, cls))
    return out


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

per = collections.defaultdict(lambda: collections.Counter())
longest = collections.Counter()
max_gap = collections.Counter()
for eid, recs in RECORDS.items():
    recs = sorted(set(recs), key=lambda r: (r[0], str(r[1]), str(r[2])))
    runs, cur = [], [recs[0]]
    for r in recs[1:]:
        if (r[1], r[2]) == (cur[-1][1], cur[-1][2]):
            cur.append(r)
        else:
            runs.append(cur)
            cur = [r]
    runs.append(cur)
    for run in runs:
        action = run[0][1]
        c = per[action]
        c["runs"] += 1
        longest[action] = max(longest[action], len(run))
        if len(run) >= 2:
            c["runs_ge_2"] += 1
            c["dispatches_in_runs_ge_2"] += len(run)
            c["bare_in_runs_ge_2"] += sum(1 for r in run if r[3] == "BARE")
            max_gap[action] = max([max_gap[action]] + [b[0] - a[0] for a, b in zip(run, run[1:])])
        for r in run:
            c["dispatch"] += 1
            c["class." + r[3]] += 1
for action in sorted(per, key=str):
    out = dict(sorted(per[action].items()))
    out["longest_run"] = longest[action]
    out["max_gap"] = max_gap[action]
    print("HANDLER-EXPOSURE", WORLD, TICKS, action, json.dumps(out))
