"""Where do the campaign episode's entity actions execute?  One run of the combat_initiated test's own episode.

usage: trace_episode.py <root>   (cwd is set to <root>; content seeds from the cwd-relative data/content)
Counts: tactical decisions made and what they chose; calls of the router phase and the router entry; and, after every tick,
what entities' tasks are (work kind, and the action or reason in the payload)."""
import collections
import json
import os
import sys

ROOT = sys.argv[1]
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import src  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
from src.domains.campaigns.orchestrator import CampaignOrchestrator  # noqa: E402
from src.engine.domain_logic import SimulationDomainLogic  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.pipeline_phases.actions import ActionRoutingPhase  # noqa: E402
from src.engine.scenario_runtime import ScenarioRuntimeService  # noqa: E402
from src.engine.tactical import TacticalDecisionSystem  # noqa: E402
from tests.integration.campaigns.test_catalog_entity_spawn_wiring import _campaign_life_arc_shaped_manifest  # noqa: E402

C = collections.Counter()
TASKS = collections.Counter()
FIRST_ACT_TICK = {}

_ev = TacticalDecisionSystem.evaluate_entity_intent


def ev(*a, **k):
    out = _ev(*a, **k)
    C["tactical_decisions"] += 1
    task = getattr(out, "task", None)
    if task is None:
        C["decision->no task change"] += 1
    else:
        pl = task.payload_set or {}
        C["decision->%s:%s" % (task.work_kind_set, pl.get("action") or pl.get("reason") or "-")] += 1
    return out


TacticalDecisionSystem.evaluate_entity_intent = staticmethod(ev)

_route = ActionRoutingPhase.route


def route(state, update):
    C["ActionRoutingPhase.route calls"] += 1
    n = sum(1 for e in state.entities.values() if e.task.work_kind == "ENTITY_ACT" and (e.task.payload or {}).get("action"))
    C["route: entities holding an ENTITY_ACT with an action (summed over ticks)"] += n
    return _route(state, update)


ActionRoutingPhase.route = staticmethod(route)

_sda = SimulationDomainLogic.execute_action


def sda(entity, payload=None, *a, **k):
    C["SimulationDomainLogic.execute_action calls"] += 1
    C["  action=%s" % ((payload or {}).get("action"))] += 1
    return _sda(entity, payload, *a, **k)


SimulationDomainLogic.execute_action = staticmethod(sda)

_tick = Kernel.tick_once


def tick_once(self, *a, **k):
    out = _tick(self, *a, **k)
    C["ticks"] += 1
    for e in self._state.entities.values():
        if not (e.lifecycle.active and e.combat.alive):
            continue
        pl = e.task.payload or {}
        TASKS["%s:%s" % (e.task.work_kind, pl.get("action") or pl.get("reason") or ("(idle)" if e.task.work_kind == "ENTITY_ACT" else "-"))] += 1
    return out


Kernel.tick_once = tick_once

orch = CampaignOrchestrator(_campaign_life_arc_shaped_manifest(tick_limit=70))
spec = orch._manifest.episodes[0]
svc = ScenarioRuntimeService(spec, initial_state=orch._build_initial_state(42, spec), scenario_event_recorder=None)
svc._kernel = svc._build_kernel()
svc.start(tick_limit=70)
svc.abort()
print("COUNTS", json.dumps(dict(sorted(C.items()))))
print("ENTITY-TICKS BY TASK", json.dumps(dict(sorted(TASKS.items(), key=lambda kv: -kv[1]))))
