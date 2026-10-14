"""TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED: a melee pair that starts
diagonal (Manhattan 2, so out of reach: world rule MOV-07) closes by one orthogonal step and the attacker strikes.

Bound: the brain runs once per strategic cadence (10 ticks, staggered by entity id). The first brain tick decides the
pursuit, the entity steps orthogonally adjacent, the pursuit completes on the next tick, and the second brain tick
decides ATTACK. So the first strike lands within 2 x cadence = 20 ticks of the pair appearing.

Before the fix the completion tick still stepped the entity (movement_routing read the tick-start navigation target
and ignored the update's `target_clear`), so the pursuer sidestepped off adjacency, took an opportunity attack and
waited a whole extra cadence: the first strike landed at tick 39. The target is pinned each tick so the pair's
geometry is the only variable; the attacker is clearly stronger so the combat posture engages instead of withholding.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.engine.combat import CombatResolutionSystem
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.pipeline_phases import movement as movement_phase
from src.platform.rng import DeterministicRNG

CADENCE = 10
BOUND = 2 * CADENCE


def _fighter(eid, pos, faction, *, strong):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (
        V2EntityBuilder(eid)
        .kind("hero" if role == EntityRole.HERO else "monster")
        .location(*pos)
        .identity(role=role, faction=faction)
        .combat(hp=300 if strong else 40, max_hp=300 if strong else 40, atk=60 if strong else 1,
                def_stat=30 if strong else 1, attack_range=1, readiness=100.0, alive=True)
        .lifecycle(active=True)
        .build()
    )


def _first_strike_tick(monkeypatch, ticks=60):
    """Tick of the attacker's first non-opportunity attack on a diagonal, pinned target; None if none in `ticks`."""
    strikes = []
    original = CombatResolutionSystem.resolve_attack

    def spy(attacker, defender, state, is_opportunity_attack=False, is_lethal=True):
        if attacker.id == 1 and not is_opportunity_attack:
            strikes.append(state.tick)
        return original(attacker, defender, state, is_opportunity_attack, is_lethal)

    monkeypatch.setattr(CombatResolutionSystem, "resolve_attack", staticmethod(spy))
    attacker = _fighter(1, (10.0, 10.0), Faction.HERO_GUILD, strong=True)
    target = _fighter(2, (11.0, 11.0), Faction.MONSTER_HORDE, strong=False)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})
    kernel = Kernel(
        profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
        flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor(),
    )
    try:
        for _ in range(ticks):
            kernel.tick_once()
            current = kernel._state
            pinned = replace(target, combat=replace(target.combat, hp=current.entities[2].combat.hp,
                                                    alive=current.entities[2].combat.alive))
            kernel._state = replace(current, entities={**dict(current.entities), 2: pinned})
            if strikes:
                break
    finally:
        kernel.shutdown()
    return strikes[0] if strikes else None


def test_a_diagonal_pair_strikes_within_two_brain_cadences(monkeypatch):
    tick = _first_strike_tick(monkeypatch)

    assert tick is not None and tick <= BOUND, f"first strike at tick {tick}, bound {BOUND}"


def test_control_without_the_completion_tick_guard_the_pursuer_overshoots_and_strikes_late(monkeypatch):
    """Disabling control: the guard restored to the old rule (only `moved_this_tick` settles an entity) puts the
    first strike a whole cadence later, past the bound."""
    monkeypatch.setattr(movement_phase, "_already_settled_this_tick", lambda ent_upd: bool(ent_upd) and ent_upd.moved_this_tick)
    # CONFLICT-04 at the movement layer would also stop the overshoot step (the pursuer is engaged with an adjacent hostile), so
    # switch it off to keep this control about the completion-tick guard alone.
    from src.engine.candidate_selector import MovementCandidateSelector

    monkeypatch.setattr(MovementCandidateSelector, "engaged_adjacent_hostile", staticmethod(lambda *a, **k: False))

    tick = _first_strike_tick(monkeypatch)

    assert tick is None or tick > BOUND, f"first strike at tick {tick} should miss the bound {BOUND} without the guard"


def test_a_bracketing_flank_landing_ends_only_in_orthogonal_reach():
    """MOV-07 confirmation, no change to positioning: bracketing is recorded as de-facto pursuit (it live-tracks its
    target), so its completion is the same reach test. On a diagonal tile (Manhattan 2, not in melee reach) the move
    is NOT complete and keeps walking; one orthogonal step later it is complete."""
    from src.core.movement_modes import MovementMode
    from src.core.state import TaskComponent
    from src.engine.candidate_selector import MovementCandidateSelector

    def bracketer(pos):
        e = _fighter(1, pos, Faction.HERO_GUILD, strong=True)
        nav = replace(e.navigation, movement_mode=MovementMode.REPOSITION, target=(11.0, 11.0))
        task = TaskComponent(work_kind="ENTITY_MOVE", payload={"target_id": 2, "target_position": (11.0, 11.0), "reason": "BRACKETING"})
        return replace(e, navigation=nav, task=task)

    target = _fighter(2, (11.0, 11.0), Faction.MONSTER_HORDE, strong=False)
    complete = MovementCandidateSelector.tracked_move_complete

    diagonal, orthogonal = bracketer((10.0, 10.0)), bracketer((10.0, 11.0))
    assert complete(diagonal, {1: diagonal, 2: target}) is False
    assert complete(orthogonal, {1: orthogonal, 2: target}) is True
