"""Action dispatches in the combat_initiated test's own campaign setup (same manifest, seed 42, 70 ticks).

usage: campaign_actions.py <root>   (run with cwd = <root>; content seeds from the cwd-relative data/content)
Wraps ActionRouter.execute_action and counts (action, outcome class) so "attack never attempted" can be told apart from
"attempted but failed". Outcome: FAIL:<reason> | EFFECT | BARE."""
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
from src.engine.domain.action_router import ActionRouter  # noqa: E402
from src.engine.scenario_runtime import ScenarioRuntimeService  # noqa: E402
from tests.integration.campaigns.test_catalog_entity_spawn_wiring import _campaign_life_arc_shaped_manifest  # noqa: E402

C = collections.Counter()
_ea = ActionRouter.execute_action


def ea(entity, payload=None, current_tick=0, *a, **k):
    out = _ea(entity, payload, current_tick, *a, **k)
    action = payload.get("action") if payload else None
    upd = out.get(entity.id) if out else None
    nav = getattr(upd, "navigation", None)
    if upd is None:
        cls = "FAIL:NO_ACTION_UPDATE"
    elif nav is not None and nav.failure_reason:
        cls = "FAIL:" + str(getattr(nav.failure_reason, "value", nav.failure_reason))
    else:
        cls = "EFFECT"
    C[f"{action}/{cls}"] += 1
    return out


ActionRouter.execute_action = staticmethod(ea)

from src.engine.combat import CombatResolutionSystem  # noqa: E402

_ra = CombatResolutionSystem.resolve_attack
_rm = CombatResolutionSystem.resolve_multi_attack


def ra(*a, **k):
    C["combat_entry/resolve_attack"] += 1
    return _ra(*a, **k)


def rm(*a, **k):
    C["combat_entry/resolve_multi_attack opportunity=%s" % bool(k.get("is_opportunity_attack"))] += 1
    return _rm(*a, **k)


CombatResolutionSystem.resolve_attack = staticmethod(ra)
CombatResolutionSystem.resolve_multi_attack = staticmethod(rm)
manifest = _campaign_life_arc_shaped_manifest(tick_limit=70)
orch = CampaignOrchestrator(manifest)
spec = orch._manifest.episodes[0]
initial_state = orch._build_initial_state(42, spec)
n = len(initial_state.entities)
kinds = collections.Counter(getattr(e, "kind", "?") for e in initial_state.entities.values())
svc = ScenarioRuntimeService(spec, initial_state=initial_state, scenario_event_recorder=None)
svc._kernel = svc._build_kernel()
svc.start(tick_limit=70)
svc.abort()
print("ENTITIES", n, json.dumps(dict(kinds)))
print("ACTIONS", json.dumps(dict(sorted(C.items()))))
