"""CONFLICT-04 kernel scenarios CP-S18 and CP-S19 (docs/world_rules/scenarios/capability-progression-batch-07.md).

CP-S18: a non-cautious fighter beside an engaged hostile, readiness under 100, holds its tile (a queued ATTACK, reason
HOLD_BETWEEN_BLOWS), takes no opportunity attack, and strikes at readiness 100. Control: a cautious fighter (AGENCY-07 ADJACENT)
leaves and pays an opportunity attack.
CP-S19: an adjacent pair starting past the stall threshold is never sent to a STALEMATE_BREAK wander. Control: the same pair two
tiles apart is.

World: the compiled `mechanic_scenario_combat_judgement_withdrawal` arena (a real hostile pair). The two arms differ only in the
precondition under test. Per-tick facts are read from the real kernel, the opportunity attacks from the authoritative combat
resolution call (`CombatResolutionSystem.resolve_multi_attack`), not from a log line.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List

import pytest

from src.config.profiles import PROD_SMALL
from src.core.state import AuthoritativeState, TaskComponent
from src.engine.combat import CombatResolutionSystem
from src.engine.domain.combat_actions import CombatActions
from src.engine.tactical import TacticalDecisionSystem
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED, compile_world, empty_inventories
from tests.helpers.kernel_pinning import PinnedNormalGovernor

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
F, H = 2, 1  # F is the strong orc_warchief: the arena's posture gate would withhold the weak goblin's attack
F_POS = (1.0, 1.0)  # the arena is the region (0, 0, 3, 3)
ADJ, APART = (1.0, 2.0), (1.0, 3.0)
NON_CAUTIOUS, CAUTIOUS = "undead_purpose", "humanoid_survival"  # safety low / high (need_profiles.yaml)


def _stage(state: AuthoritativeState, *, h_pos, need_profile: str, readiness: float, stale: int = 0, hp: int = 5000) -> AuthoritativeState:
    entities = dict(state.entities)
    for eid, pos in ((F, F_POS), (H, h_pos)):
        e = entities[eid]
        props = dict(e.identity.properties)
        props["need_profile_id"] = need_profile if eid == F else NON_CAUTIOUS  # only F's disposition varies
        props.pop("drive_profile_id", None)
        # Engaged: each names the other as its target (the combat-engaged state); the stall counter is staged when given.
        payload = {"target_id": H if eid == F else F}
        if stale:
            payload["stale_ticks"] = stale
        task = TaskComponent(work_kind="ENTITY_BRAIN", payload=payload)
        entities[eid] = replace(
            e,
            navigation=replace(e.navigation, position=pos, target=None),
            combat=replace(e.combat, hp=hp, max_hp=hp, readiness=readiness if eid == F else 100.0, atk=60, readiness_speed=2.0),
            identity=replace(e.identity, properties=props),
            task=task,
        )
    object.__setattr__(state, "entities", entities)
    # The arena's authored mismatch makes combat_engagement record an 'avoid' posture that withholds the attack (a different
    # mechanic); switch that system off so the scenario isolates CONFLICT-04.
    object.__setattr__(state, "feature_flags", {**(state.feature_flags or {}), "ENABLE_COMBAT_ENGAGEMENT": "OFF"})
    return state


def _trace(state: AuthoritativeState, ticks: int) -> Dict[str, Any]:
    """Tick the real kernel; record F's position and task each tick, the opportunity attacks landed on F, and the swings on H."""
    orig = CombatResolutionSystem.resolve_multi_attack
    oa_on_f: List[int] = []

    def wrapped(attackers, target, c, is_opportunity_attack=False, **kw):
        r = orig(attackers, target, c, is_opportunity_attack=is_opportunity_attack, **kw)
        if is_opportunity_attack and target.id == F and getattr(r, "hp_delta", 0) and r.hp_delta < 0:
            oa_on_f.append(kw.get("tick", 0))
        return r

    orig_decide = TacticalDecisionSystem.evaluate_entity_intent
    orig_attack = CombatActions.execute_attack
    decisions: List[Dict[str, Any]] = []
    swings: List[Dict[str, Any]] = []

    def decide(st, entity, *a, **kw):
        r = orig_decide(st, entity, *a, **kw)
        if entity.id in (F, H) and r is not None and r.task is not None and r.task.payload_set:
            decisions.append(dict(eid=entity.id, tick=st.tick, **{k: r.task.payload_set.get(k) for k in ("action", "reason", "stale_ticks")}))
        return r

    def attack(entity, payload=None, current_tick=0, neighbor_view=None, context=None):
        r = orig_attack(entity, payload, current_tick, neighbor_view, context)
        nav = getattr(r.get(entity.id), "navigation", None)
        swings.append(dict(eid=entity.id, tick=current_tick, failure=getattr(nav, "failure_reason", None)))
        return r

    CombatResolutionSystem.resolve_multi_attack = staticmethod(wrapped)
    TacticalDecisionSystem.evaluate_entity_intent = staticmethod(decide)
    CombatActions.execute_attack = staticmethod(attack)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED),
                    flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
    rows = []
    try:
        for _ in range(ticks):
            kernel.tick_once()
            st = kernel._state
            f, h = st.entities[F], st.entities[H]
            rows.append(dict(f_pos=tuple(f.navigation.position), f_pos_h=tuple(h.navigation.position), f_hp=f.combat.hp, h_hp=h.combat.hp,
                             f_payload=dict(f.task.payload), h_payload=dict(h.task.payload), f_ready=f.combat.readiness))
        return dict(rows=rows, oa_on_f=oa_on_f, decisions=decisions, swings=swings, final=kernel._state)
    finally:
        kernel.shutdown()
        CombatResolutionSystem.resolve_multi_attack = staticmethod(orig)
        TacticalDecisionSystem.evaluate_entity_intent = staticmethod(orig_decide)
        CombatActions.execute_attack = staticmethod(orig_attack)


def test_cp_s18_main_non_cautious_fighter_holds_between_blows():
    state = _stage(empty_inventories(compile_world(WORLD_ID)), h_pos=ADJ, need_profile=NON_CAUTIOUS, readiness=0.0)
    out = _trace(state, 70)  # readiness refills at 2 per tick from 0: 100 at tick 50
    rows = out["rows"]
    assert {r["f_pos"] for r in rows} == {F_POS}, "the fighter stepped between blows"
    assert out["oa_on_f"] == [], "an opportunity attack landed on the holding fighter"
    held = [d for d in out["decisions"] if d["eid"] == F and d["reason"] == "HOLD_BETWEEN_BLOWS"]
    assert held and all(d["action"] == "ATTACK" and d["stale_ticks"] == 0 for d in held)
    assert not any(d["eid"] == F and d["action"] is None for d in out["decisions"]), "the fighter decided a step"
    ok_swings = [s for s in out["swings"] if s["eid"] == F and s["failure"] is None]
    assert ok_swings, "the held swing never resolved"
    assert min(r["h_hp"] for r in rows) < 5000, "the swing did not lower the hostile's HP"


def test_cp_s18_control_cautious_fighter_leaves_and_pays_the_opportunity_attack():
    state = _stage(empty_inventories(compile_world(WORLD_ID)), h_pos=ADJ, need_profile=CAUTIOUS, readiness=0.0)
    out = _trace(state, 40)
    assert {r["f_pos"] for r in out["rows"]} != {F_POS}, "the cautious fighter did not leave"
    assert len(out["oa_on_f"]) >= 1, "leaving the engagement paid no opportunity attack"


def test_cp_s19_main_adjacent_pair_past_the_stall_threshold_never_breaks():
    state = _stage(empty_inventories(compile_world(WORLD_ID)), h_pos=ADJ, need_profile=NON_CAUTIOUS, readiness=100.0, stale=11)
    out = _trace(state, 60)
    assert all(r["f_payload"].get("reason") != "STALEMATE_BREAK" and r["h_payload"].get("reason") != "STALEMATE_BREAK" for r in out["rows"])
    assert {r["f_pos"] for r in out["rows"]} == {F_POS}
    assert {r["f_pos_h"] for r in out["rows"]} == {ADJ}
    assert out["rows"][-1]["f_hp"] > 0 and out["rows"][-1]["h_hp"] > 0


def test_cp_s19_control_pair_two_tiles_apart_gets_the_stalemate_break():
    state = _stage(empty_inventories(compile_world(WORLD_ID)), h_pos=APART, need_profile=NON_CAUTIOUS, readiness=100.0, stale=11)
    out = _trace(state, 12)
    assert any(r["f_payload"].get("reason") == "STALEMATE_BREAK" or r["h_payload"].get("reason") == "STALEMATE_BREAK" for r in out["rows"])
