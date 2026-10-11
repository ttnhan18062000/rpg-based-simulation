"""
tests/unit/domains/cooperation/test_cooperation_phase.py
───────────────────────────────────────────────────────────────────────────────
Unit tests verifying CooperationPhase respects the ENABLE_SOCIAL_COOPERATION
feature flag — specifically that last_cooperation_decision is set in
property_updates when the phase runs and eligible entities are present, and
that the phase is skipped when the flag turns it OFF.

The ON test exercises CooperationPhase.execute() directly. The OFF test goes
through AuthoritativeApplyPipeline.refine(), because the real OFF switch is the
pipeline's feature-flag gate (``run_phase("cooperation", ..., "ENABLE_SOCIAL_COOPERATION")``).
The phase used to carry a second, test-only OFF switch, a ``social_cooperation_disabled``
key in ``state.periodic_due_ticks``; nothing in src/ ever set it, and it went away
with that field (TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE).

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
    G-3 (test_plan.md T-4): With ENABLE_SOCIAL_COOPERATION OFF, the pipeline skips the
    cooperation phase: it is counted as skipped and no last_cooperation_decision is
    written for any entity. The same state with the flag ON runs the phase (control).
    """
    from src.domains.optimization.feature_flags import FeatureMode
    from src.engine.pipeline import AuthoritativeApplyPipeline

    def refine(mode):
        hero1 = _make_group_entity(1, group_id=10, x=0.0, y=0.0)
        hero2 = _make_group_entity(2, group_id=10, x=5.0, y=0.0)
        state = AuthoritativeState(entities={e.id: e for e in (hero1, hero2)}, tick=1, seed=42,
                                   feature_flags={"ENABLE_SOCIAL_COOPERATION": mode})
        return AuthoritativeApplyPipeline.refine(state, StateUpdate())

    def decisions(update):
        return [eid for eid, eu in update.entity_updates.items() if "last_cooperation_decision" in eu.property_updates]

    on = refine(FeatureMode.ON)
    assert on.metric_counters.get("run_cooperation", 0) == 1 and decisions(on), "the control run did not exercise the phase"

    off = refine(FeatureMode.OFF)
    assert off.metric_counters.get("skip_cooperation", 0) == 1
    assert "run_cooperation" not in off.metric_counters
    assert decisions(off) == []
