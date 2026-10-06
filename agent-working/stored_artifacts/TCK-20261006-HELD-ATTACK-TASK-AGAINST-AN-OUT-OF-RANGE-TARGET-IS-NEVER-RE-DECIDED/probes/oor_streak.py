"""Combat-volume probe for one run. usage: corpus_probe.py <root> <world|campaign> <ticks> <seed>
Counts (after-the-fact, per run): tactical decisions by kind (ATTACK / PANIC_RETREAT / other), execute_attack calls by
outcome split fresh (decision tick) vs held, resolve_attack non-opportunity, opportunity attackers, and deaths."""
import collections
import json
import os
import sys

ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import src  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.engine.combat import CombatResolutionSystem  # noqa: E402
from src.engine.domain.combat_actions import CombatActions  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.tactical import TacticalDecisionSystem as T  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402

C = collections.Counter()
DECIDED = {}
STREAK = {}
MAXS = [0]
_ev = T.evaluate_entity_intent


def ev(state, entity, *a, **k):
    r = _ev(state, entity, *a, **k)
    pl = (r.task.payload_set or {}) if r is not None and r.task is not None else {}
    if r is not None and r.task is not None:
        C["tactical.decisions"] += 1
        if pl.get("action") == "ATTACK":
            C["tactical.ATTACK"] += 1
            DECIDED[entity.id] = state.tick
        elif pl.get("reason") == "PANIC_RETREAT":
            C["tactical.PANIC_RETREAT"] += 1
    return r


T.evaluate_entity_intent = staticmethod(ev)
_ea = CombatActions.execute_attack


def ea(entity, payload=None, current_tick=0, neighbor_view=None, context=None):
    r = _ea(entity, payload, current_tick, neighbor_view, context)
    up = r.get(entity.id)
    reason = getattr(getattr(up, "navigation", None), "failure_reason", None)
    fresh = DECIDED.get(entity.id) == getattr(context, "tick", current_tick)
    C[f"execute_attack.{'fresh' if fresh else 'held'}.{getattr(reason, 'name', reason)}"] += 1
    C["execute_attack.total"] += 1
    name = getattr(reason, "name", reason)
    if name == "OUT_OF_RANGE":
        STREAK[entity.id] = STREAK.get(entity.id, 0) + 1
        MAXS[0] = max(MAXS[0], STREAK[entity.id])
    else:
        if STREAK.get(entity.id, 0) >= 3:
            C["oor_streaks_ge3"] += 1
        STREAK[entity.id] = 0
    return r


CombatActions.execute_attack = staticmethod(ea)
_ra = CombatResolutionSystem.resolve_attack
_rm = CombatResolutionSystem.resolve_multi_attack


def ra(attacker, defender, state, is_opportunity_attack=False, is_lethal=True):
    C["resolve_attack." + ("opportunity" if is_opportunity_attack else "deliberate")] += 1
    return _ra(attacker, defender, state, is_opportunity_attack, is_lethal)


def rm(attackers, defender, state, is_opportunity_attack=False, is_lethal=True, *a, **k):
    key = "opportunity" if is_opportunity_attack else "other"
    C[f"resolve_multi_attack.{key}.calls"] += 1
    C[f"resolve_multi_attack.{key}.attackers"] += len(attackers)
    return _rm(attackers, defender, state, is_opportunity_attack, is_lethal, *a, **k)


CombatResolutionSystem.resolve_attack = staticmethod(ra)
CombatResolutionSystem.resolve_multi_attack = staticmethod(rm)

if WORLD == "campaign":
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    from src.engine.scenario_runtime import ScenarioRuntimeService
    from tests.integration.campaigns.test_catalog_entity_spawn_wiring import _campaign_life_arc_shaped_manifest

    manifest = _campaign_life_arc_shaped_manifest(tick_limit=TICKS)
    orch = CampaignOrchestrator(manifest)
    spec = orch._manifest.episodes[0]
    initial = orch._build_initial_state(SEED, spec)
    alive0 = {e.id for e in initial.entities.values() if e.combat.alive}
    svc = ScenarioRuntimeService(spec, initial_state=initial, scenario_event_recorder=None)
    svc._kernel = svc._build_kernel()
    svc.start(tick_limit=TICKS)
    final = svc._kernel._state
    C["deaths"] = len(alive0 - {e.id for e in final.entities.values() if e.combat.alive})
    C["entities"] = len(initial.entities)
    svc.abort()
else:
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
    state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
    alive0 = {e.id for e in state.entities.values() if e.combat.alive}
    k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
               flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
    try:
        for _ in range(TICKS):
            k.tick_once()
        C["deaths"] = len(alive0 - {e.id for e in k._state.entities.values() if e.combat.alive})
        C["entities"] = len(state.entities)
    finally:
        k.shutdown()
C["oor_max_consecutive_per_entity"] = MAXS[0]
C["oor_open_streaks_ge3_at_end"] = sum(1 for v in STREAK.values() if v >= 3)
print("CORPUS", WORLD, SEED, TICKS, json.dumps(dict(sorted(C.items()))))
