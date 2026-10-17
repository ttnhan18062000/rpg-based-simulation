"""Forced scenarios for the three terrain mechanics that the gate worlds never exercise (cover, chokepoints, high ground).

Each scenario stages a tiny fight on a real compiled world and runs the real kernel, so the mechanic is reached through the real action
router, the real tactical decision system and the real combat resolver (not by calling the helper). Each has a control arm with the
mechanic's precondition absent. In the gate worlds (4 worlds x seed 42 x 5000t) cover was read on every attack but never true, no
chokepoint was ever found, and high ground never fired (the only mountain world has no fights); these tests are the proof that the
mechanics work when the geometry exists.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest

from src.config.profiles import PROD_SMALL
from src.core.state import AuthoritativeState, TaskComponent
from src.engine.combat import CombatResolutionSystem
from src.engine.domain.action_router import ActionRouter
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.positioning import PositioningService
from src.engine.tactical import TacticalDecisionSystem
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED, compile_world, empty_inventories

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
F, H = 2, 1  # F is the one that acts (attacker, or the vanguard); H is the other body


def _stage(f_pos: Tuple[float, float], h_pos: Tuple[float, float], *, f_task: Dict[str, Any], rng_range: int = 3,
           terrain: Optional[Dict[Tuple[int, int], str]] = None, blocked: Optional[Set[Tuple[int, int]]] = None,
           vanguard: bool = False) -> AuthoritativeState:
    state = empty_inventories(compile_world(WORLD_ID))
    entities = dict(state.entities)
    for eid, pos in ((F, f_pos), (H, h_pos)):
        e = entities[eid]
        props = dict(e.identity.properties)
        props["need_profile_id"] = "undead_purpose"  # not cautious
        entities[eid] = replace(
            e, navigation=replace(e.navigation, position=pos, target=None), identity=replace(e.identity, properties=props),
            combat=replace(e.combat, hp=5000, max_hp=5000, atk=100, def_stat=10, readiness=100.0, range=rng_range,
                           tactical_role="VANGUARD" if (vanguard and eid == F) else e.combat.tactical_role),
            task=TaskComponent(work_kind="ENTITY_ACT", payload=dict(f_task) if eid == F else {}))
    object.__setattr__(state, "entities", entities)
    object.__setattr__(state, "terrain", {**state.terrain, **(terrain or {})})
    object.__setattr__(state, "blocked_tiles", set(blocked or set()))
    object.__setattr__(state, "feature_flags", {**(state.feature_flags or {}), "ENABLE_COMBAT_ENGAGEMENT": "OFF"})
    return state


def _run(state: AuthoritativeState, ticks: int):
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED),
                    flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
    try:
        for _ in range(ticks):
            kernel.tick_once()
    finally:
        kernel.shutdown()


def _first_attack(state: AuthoritativeState):
    """Run the kernel until F's first real attack resolves; return (CombatUpdate, attacker pos, defender pos) as the resolver saw them."""
    seen: List[Any] = []
    orig = CombatResolutionSystem.resolve_attack

    def spy(attacker, defender, st, *a, **kw):
        r = orig(attacker, defender, st, *a, **kw)
        if attacker.id == F and r.outcome_kind != "REJECTED":
            seen.append((r, tuple(attacker.navigation.position), tuple(defender.navigation.position)))
        return r

    CombatResolutionSystem.resolve_attack = staticmethod(spy)
    try:
        _run(state, 3)
    finally:
        CombatResolutionSystem.resolve_attack = staticmethod(orig)
    assert seen, "the kernel never resolved an attack for the staged attacker"
    return seen[0]


ATTACK = {"action": "ATTACK", "target_id": H}
A_POS, D_POS = (1.0, 1.0), (3.0, 1.0)  # two tiles apart (range 3)
# The tile check_cover reads is the one adjacent to the defender on the ATTACKER's side, (2, 1) here (an obstacle between them). The Bible and the
# docstring say "behind the target, away from the attacker"; the code has never done that (pinned by test_terrain_declares_cover_and_high_ground).


def test_a_cover_tile_next_to_the_defender_on_the_attackers_side_reduces_the_damage_of_a_real_attack():
    hit, a, d = _first_attack(_stage(A_POS, D_POS, f_task=ATTACK, terrain={(2, 1): "forest"}))
    control, ca, cd = _first_attack(_stage(A_POS, D_POS, f_task=ATTACK, terrain={(2, 1): "plain"}))
    assert (a, d) == (ca, cd) == (A_POS, D_POS), "the bodies moved before the attack; the scenario is not the staged geometry"
    assert hit.trace.get("COVER_REDUCTION") == CombatResolutionSystem.COVER_REDUCTION
    assert "COVER_REDUCTION" not in control.trace
    assert hit.trace["FINAL_DEF_MULT"] == pytest.approx(1.0 + CombatResolutionSystem.COVER_REDUCTION)
    assert hit.damage_taken < control.damage_taken


def test_cover_on_the_far_side_or_the_flanks_of_the_defender_does_not_count():
    side, a, d = _first_attack(_stage(A_POS, D_POS, f_task=ATTACK, terrain={(4, 1): "forest", (3, 0): "forest", (3, 2): "forest"}))
    assert (a, d) == (A_POS, D_POS)
    assert "COVER_REDUCTION" not in side.trace


def test_attacking_from_high_ground_onto_plain_raises_the_damage_of_a_real_attack():
    hit, a, d = _first_attack(_stage(A_POS, D_POS, f_task=ATTACK, terrain={(1, 1): "mountain", (3, 1): "plain", (4, 1): "plain"}))
    control, ca, cd = _first_attack(_stage(A_POS, D_POS, f_task=ATTACK, terrain={(1, 1): "plain", (3, 1): "plain", (4, 1): "plain"}))
    assert (a, d) == (ca, cd) == (A_POS, D_POS)
    assert hit.trace.get("HIGH_GROUND") == CombatResolutionSystem.HIGH_GROUND_BONUS
    assert "HIGH_GROUND" not in control.trace
    assert hit.trace["FINAL_ATK_MULT"] == pytest.approx(control.trace["FINAL_ATK_MULT"] + CombatResolutionSystem.HIGH_GROUND_BONUS)
    assert hit.damage_taken > control.damage_taken


def test_no_high_ground_when_both_stand_on_mountain():
    both, a, d = _first_attack(_stage(A_POS, D_POS, f_task=ATTACK, terrain={(1, 1): "mountain", (3, 1): "mountain", (4, 1): "plain"}))
    assert (a, d) == (A_POS, D_POS)
    assert "HIGH_GROUND" not in both.trace


V_POS, T_POS = (1.0, 1.0), (1.0, 3.0)  # the vanguard stands in a one-tile gap; the target is 2 tiles away and the vanguard's range is 1


def _chokepoint_run(blocked: Set[Tuple[int, int]]):
    """Run the kernel on a vanguard whose target is out of reach; return (chokepoint sets the finder returned for F, F's decision reasons, F's positions)."""
    state = _stage(V_POS, T_POS, f_task={}, rng_range=1, blocked=blocked, vanguard=True)
    found: List[Set[Tuple[float, float]]] = []
    reasons: List[Optional[str]] = []
    positions: Set[Tuple[float, float]] = set()
    orig_find, orig_decide = PositioningService.identify_chokepoints, TacticalDecisionSystem.evaluate_entity_intent

    def find(entity, st, radius=8):
        r = orig_find(entity, st, radius)
        if entity.id == F:
            found.append(set(r))
        return r

    def decide(st, entity, *a, **kw):
        r = orig_decide(st, entity, *a, **kw)
        if entity.id == F and r is not None and r.task is not None:
            reasons.append((r.task.payload_set or {}).get("reason"))
        return r

    PositioningService.identify_chokepoints = staticmethod(find)
    TacticalDecisionSystem.evaluate_entity_intent = staticmethod(decide)
    try:
        kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED),
                        flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
        try:
            for _ in range(10):
                kernel.tick_once()
                positions.add(tuple(kernel._state.entities[F].navigation.position))
        finally:
            kernel.shutdown()
    finally:
        PositioningService.identify_chokepoints = staticmethod(orig_find)
        TacticalDecisionSystem.evaluate_entity_intent = staticmethod(orig_decide)
    return found, reasons, positions


def test_two_blocked_tiles_opposite_across_one_open_tile_make_a_chokepoint_a_vanguard_holds():
    found, reasons, positions = _chokepoint_run({(0, 1), (2, 1)})
    assert any(V_POS in s for s in found), "the finder never reported the gap tile as a chokepoint"
    assert "HOLD_CHOKEPOINT" in reasons
    assert positions == {V_POS}, "the vanguard left the chokepoint it decided to hold"


def test_without_the_blocked_tiles_there_is_no_chokepoint_and_no_hold():
    found, reasons, _ = _chokepoint_run(set())
    assert found and not any(found)
    assert "HOLD_CHOKEPOINT" not in reasons
