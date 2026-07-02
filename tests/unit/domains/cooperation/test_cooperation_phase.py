"""
tests/unit/domains/cooperation/test_cooperation_phase.py
───────────────────────────────────────────────────────────────────────────────
Unit tests verifying CooperationPhase respects the ENABLE_SOCIAL_COOPERATION
feature flag — specifically that last_cooperation_decision is set in
property_updates when the phase runs and eligible entities are present, and
that the phase is a no-op when the flag disables it.

These tests exercise CooperationPhase.execute() directly (not via pipeline
run_phase), so they do not depend on FeatureFlagManager or
AuthoritativeApplyPipeline.

The phase's internal flag check reads:
  flag = getattr(state, "social_cooperation_enabled", True)        # always True
  if "social_cooperation_disabled" in state.periodic_due_ticks:    # OFF path
      flag = False

To bypass the inner-loop guard (``if not help_needs and group_id is None: continue``),
entities are given a non-None group_id, which forces evaluation through the full
cooperation decision path.

TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO
"""
from __future__ import annotations

import pytest
from dataclasses import replace as dc_replace

from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate
from src.domains.cooperation.phase import CooperationPhase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _active_hero_in_group(entity_id: int, group_id: int, x: float = 0.0, y: float = 0.0):
    """Build an active, alive hero entity that belongs to a group.

    Group membership bypasses the inner-loop guard in CooperationPhase
    (``if not help_needs and entity.identity.group_id is None: continue``),
    guaranteeing the decision path is exercised and last_cooperation_decision
    is written to property_updates.
    """
    return (
        V2EntityBuilder(entity_id)
        .kind("HERO")
        .location(x, y)
        .combat(hp=100, max_hp=100, atk=10)
        .lifecycle(active=True)
        .build()
    ), group_id


def _make_group_entity(entity_id: int, group_id: int, x: float = 0.0, y: float = 0.0):
    """Build an active, alive hero with identity.group_id set."""
    entity = (
        V2EntityBuilder(entity_id)
        .kind("HERO")
        .location(x, y)
        .combat(hp=100, max_hp=100, atk=10)
        .lifecycle(active=True)
        .build()
    )
    # Set group_id via init_group_id parameter — EntityState supports this
    from src.core.state import EntityState, IdentityComponent
    new_identity = dc_replace(entity.identity, group_id=group_id)
    entity = dc_replace(entity, identity=new_identity)
    return entity


def _state_flag_on(*entities) -> AuthoritativeState:
    """State where CooperationPhase runs normally (social_cooperation_enabled defaults True)."""
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(entities=ent_map, tick=1, seed=42)


def _state_flag_off(*entities) -> AuthoritativeState:
    """State where CooperationPhase.execute short-circuits via periodic_due_ticks sentinel."""
    ent_map = {e.id: e for e in entities}
    # CooperationPhase checks:
    #   if hasattr(state, "periodic_due_ticks") and "social_cooperation_disabled" in state.periodic_due_ticks:
    #       flag = False
    return AuthoritativeState(
        entities=ent_map,
        tick=1,
        seed=42,
        periodic_due_ticks={"social_cooperation_disabled": 1},
    )


# ---------------------------------------------------------------------------
# Test: flag ON → last_cooperation_decision set for group-member entities
# ---------------------------------------------------------------------------

def test_cooperation_phase_sets_property_when_enabled():
    """
    G-1 (test_plan.md T-4): With ENABLE_SOCIAL_COOPERATION effectively ON,
    CooperationPhase.execute() must set last_cooperation_decision in
    property_updates for at least one eligible active entity that is in a group.
    """
    hero1 = _make_group_entity(1, group_id=10, x=0.0, y=0.0)
    hero2 = _make_group_entity(2, group_id=10, x=5.0, y=0.0)
    state = _state_flag_on(hero1, hero2)
    update = StateUpdate()

    result = CooperationPhase.execute(state, update)

    entities_with_decision = [
        eid
        for eid, eu in result.entity_updates.items()
        if "last_cooperation_decision" in eu.property_updates
    ]
    assert len(entities_with_decision) >= 1, (
        "Expected last_cooperation_decision in property_updates for at least one "
        "group-member entity when CooperationPhase runs with the flag ON."
    )


# ---------------------------------------------------------------------------
# Test: flag OFF → last_cooperation_decision NOT set
# ---------------------------------------------------------------------------

def test_cooperation_phase_skips_when_disabled():
    """
    G-3 (test_plan.md T-4): When periodic_due_ticks contains
    "social_cooperation_disabled", CooperationPhase.execute() must return the
    update unchanged — no last_cooperation_decision in any entity's
    property_updates.
    """
    hero1 = _make_group_entity(1, group_id=10, x=0.0, y=0.0)
    hero2 = _make_group_entity(2, group_id=10, x=5.0, y=0.0)
    state = _state_flag_off(hero1, hero2)
    update = StateUpdate()

    result = CooperationPhase.execute(state, update)

    entities_with_decision = [
        eid
        for eid, eu in result.entity_updates.items()
        if "last_cooperation_decision" in eu.property_updates
    ]
    assert len(entities_with_decision) == 0, (
        "Expected no last_cooperation_decision when social_cooperation_disabled "
        "sentinel is present in periodic_due_ticks."
    )


# ---------------------------------------------------------------------------
# Test: no eligible entities → no property_updates produced
# ---------------------------------------------------------------------------

def test_cooperation_phase_no_output_for_inactive_entities():
    """
    Inactive/dead entities must be skipped by CooperationPhase even when the
    flag is ON — the inner loop guard exits early for them.
    """
    hero = (
        V2EntityBuilder(1)
        .kind("HERO")
        .location(0.0, 0.0)
        .combat(hp=0, max_hp=100)
        .lifecycle(active=False)
        .build()
    )
    state = _state_flag_on(hero)
    update = StateUpdate()

    result = CooperationPhase.execute(state, update)

    entities_with_decision = [
        eid
        for eid, eu in result.entity_updates.items()
        if "last_cooperation_decision" in eu.property_updates
    ]
    assert len(entities_with_decision) == 0, (
        "Inactive/dead entities must not produce last_cooperation_decision updates."
    )
