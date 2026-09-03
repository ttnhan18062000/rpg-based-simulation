"""
Unit tests for the Coming of Age archetype-choice roll (TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE).

Covers the pure weighting function (src/ai/coming_of_age.py), the required metamorphic
convergence-guard (AC2) and no-collapse regression guard (AC3), parent-resolution edge cases,
and the seeded-RNG determinism guard -- following test_occupation_change_scorer.py's
fixture-helper conventions.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from src.ai.coming_of_age import (
    _CANDIDATE_ROLES,
    choose_archetype,
    compute_role_weights,
    is_excluded_no_birth_record,
)
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, LifeStage, PersonalityComponent, RegionState
from src.core.updates import StateUpdate
from src.systems.lifecycle_systems.lifecycle import LifecycleSystem

_TOWN = RegionState(id="town", name="Town", bounds=(0, 0, 200, 200))


def _child_at_boundary(eid: int, pos: tuple = (5.0, 5.0), **identity_kwargs):
    """A real (not no-birth-record-excluded) CHILD at the CHILD->ADULT boundary --
    parent_a_entity_id/parent_b_entity_id are set so is_excluded_no_birth_record() is False,
    same as every live CHILD-construction path in the codebase (see coming_of_age.py's
    is_excluded_no_birth_record docstring)."""
    identity_kwargs.setdefault("role", EntityRole.CITIZEN)
    identity_kwargs.setdefault("faction", Faction.TOWN_COUNCIL)
    identity_kwargs.setdefault("life_stage", LifeStage.CHILD)
    return (V2EntityBuilder(eid)
            .kind("citizen")
            .location(*pos)
            .identity(**identity_kwargs)
            .lifecycle(age_ticks=3000, max_age_ticks=100000,
                       parent_a_entity_id=1000 + eid, parent_b_entity_id=2000 + eid, birth_tick=1)
            .build())


def _role_holder(eid: int, role: int, pos: tuple):
    return V2EntityBuilder(eid).kind("npc").location(*pos).identity(role=role).build()


def _state(entities=None, regions=None, tick=100, seed=42):
    return AuthoritativeState(tick=tick, seed=seed, entities=entities or {}, regions=regions or {})


def _entropy(weights: list) -> float:
    total = sum(weights)
    probs = [w / total for w in weights]
    return -sum(p * math.log(p) for p in probs if p > 0)


# --- Test 4: metamorphic regional-need weight guard (AC2, REQUIRED) ----------------------------


class TestComingOfAgeMetamorphicConvergenceGuard:
    def test_coming_of_age_metamorphic_regional_need_weight_increases_variance(self):
        """Holding personality/parental terms fixed, increasing regional_coeff must strictly
        increase the entropy of the resulting weight distribution -- never collapse it further."""
        child = _child_at_boundary(1, personality=PersonalityComponent(bravery=5.0))

        # SHOPKEEPER/GUARD already at their regional target (need=0); WORKER has zero live
        # holders against a target of 4 (need=4) -- a shortfall concentrated in a role distinct
        # from the personality bias (GUARD), so growing regional_coeff pulls mass toward WORKER
        # instead of amplifying the already-dominant GUARD bias.
        others = {
            2: _role_holder(2, EntityRole.SHOPKEEPER, (10.0, 10.0)),
            3: _role_holder(3, EntityRole.SHOPKEEPER, (20.0, 20.0)),
            4: _role_holder(4, EntityRole.GUARD, (30.0, 30.0)),
            5: _role_holder(5, EntityRole.GUARD, (40.0, 40.0)),
        }
        state = _state(entities={1: child, **others}, regions={"town": _TOWN})

        weights_low = compute_role_weights(child, state, regional_coeff=0.0)
        weights_high = compute_role_weights(child, state, regional_coeff=1.0)

        assert weights_low == [
            pytest.approx(1.0), pytest.approx(1.0), pytest.approx(6.0)
        ]
        assert weights_high == [
            pytest.approx(1.0), pytest.approx(5.0), pytest.approx(6.0)
        ]
        assert _entropy(weights_high) > _entropy(weights_low)

    # --- Test 5: same-tick batch no-collapse guard (AC3, REQUIRED) -----------------------------

    def test_coming_of_age_same_tick_batch_does_not_collapse_to_identical_occupation(self):
        """N>=5 same-tick, same-region CHILD entities under one fixed nonzero regional-need
        configuration must not all resolve to the identical role_set through the full
        resolve_lifecycle() path (exercises the real seeded RNG draw)."""
        children = {eid: _child_at_boundary(eid, pos=(float(eid), float(eid))) for eid in range(1, 7)}
        state = _state(entities=children, regions={"town": _TOWN})

        refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())

        role_sets = {refined.entity_updates[eid].identity.role_set for eid in children}
        assert len(role_sets) > 1


# --- Test 7/8: parent-resolution edge cases -----------------------------------------------------


def test_coming_of_age_handles_missing_or_inactive_parent_entity():
    """A dead-and-removed parent id and a present-but-inactive parent id must both degrade to a
    neutral (zero) parental contribution, never raise."""
    inactive_parent = (V2EntityBuilder(100)
                        .location(0.0, 0.0)
                        .identity(role=EntityRole.WORKER)
                        .lifecycle(active=False)
                        .build())
    child = V2EntityBuilder(1).kind("citizen").location(5.0, 5.0).identity(
        role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL, life_stage=LifeStage.CHILD
    ).lifecycle(
        age_ticks=3000, max_age_ticks=100000, parent_a_entity_id=99, parent_b_entity_id=100
    ).build()
    state = _state(entities={1: child, 100: inactive_parent})

    weights = compute_role_weights(child, state)

    assert weights == [pytest.approx(1.0), pytest.approx(1.0), pytest.approx(1.0)]


def test_coming_of_age_parentless_child_uses_neutral_parental_term():
    """A Natural-Creature-path-style parentless CHILD (both parent ids None, nonzero birth_tick)
    still receives a valid weighted roll -- the parental term must not crash or zero out every
    role's probability."""
    child = V2EntityBuilder(1).kind("citizen").location(5.0, 5.0).identity(
        role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL, life_stage=LifeStage.CHILD
    ).lifecycle(
        age_ticks=3000, max_age_ticks=100000,
        parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=50,
    ).build()
    state = _state(entities={1: child})

    weights = compute_role_weights(child, state)

    assert weights == [pytest.approx(1.0), pytest.approx(1.0), pytest.approx(1.0)]
    assert all(w > 0.0 for w in weights)


# --- Test 9: seeded-RNG determinism / no unseeded random guard ---------------------------------


def test_coming_of_age_selection_uses_seeded_rng_not_unseeded_random():
    child = _child_at_boundary(1)
    state = _state(entities={1: child})

    first = choose_archetype(child, state)
    second = choose_archetype(child, state)
    assert first == second
    assert first in _CANDIDATE_ROLES

    children = {eid: _child_at_boundary(eid, pos=(float(eid), float(eid))) for eid in range(1, 4)}
    state_a = _state(entities=children, regions={"town": _TOWN})
    state_b = _state(entities=dict(reversed(list(children.items()))), regions={"town": _TOWN})

    refined_a = LifecycleSystem.resolve_lifecycle(state_a, StateUpdate())
    refined_b = LifecycleSystem.resolve_lifecycle(state_b, StateUpdate())
    for eid in children:
        assert refined_a.entity_updates[eid].identity.role_set == refined_b.entity_updates[eid].identity.role_set

    source = Path("src/ai/coming_of_age.py").read_text()
    assert "import random" not in source
    assert "random.Random" not in source
    assert "random.choice" not in source
