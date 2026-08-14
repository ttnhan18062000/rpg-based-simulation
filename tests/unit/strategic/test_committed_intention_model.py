"""
Model-level tests for TCK-20260812-COMMITTED-INTENTION-SEQUENCE (AC1, AC2).

Covers:
- CommittedIntention frozen dataclass shape and StrategicComponent.committed_intentions default
- CognitionProfile.max_committed_intentions default
- V2EntityBuilder.strategic(committed_intentions=...) round-trip (New Test 11)
- CapacityEnforcementPhase order-preserving cap enforcement for committed_intentions (New Test 9)
"""
from __future__ import annotations

import dataclasses

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import CommittedIntention, CognitionProfile, StrategicComponent
from src.core.updates import EntityUpdate, StateUpdate, StrategicUpdate
from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase


def test_committed_intention_dataclass_shape():
    ci = CommittedIntention(
        intention_id="ci_1",
        goal_kind="harvesting",
        target_hint="node_5",
        sequence_index=0,
        status="pending",
    )
    assert dataclasses.is_dataclass(ci)
    assert dataclasses.fields(CommittedIntention)[0].name == "intention_id"
    field_names = [f.name for f in dataclasses.fields(CommittedIntention)]
    assert field_names == ["intention_id", "goal_kind", "target_hint", "sequence_index", "status"]

    # Frozen: attribute assignment must raise.
    with pytest.raises(dataclasses.FrozenInstanceError):
        ci.status = "active"

    strat = StrategicComponent()
    assert strat.committed_intentions == ()


def test_cognition_profile_max_committed_intentions_default():
    profile = CognitionProfile()
    assert profile.max_committed_intentions == 3
    assert profile.max_active_projects == 3  # unmodified, mirrored pattern


def test_builder_supports_committed_intentions():
    ci = CommittedIntention(
        intention_id="ci_1", goal_kind="harvesting", target_hint="node_5",
        sequence_index=0, status="pending",
    )
    entity = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .strategic(committed_intentions=(ci,))
        .build()
    )
    assert entity.strategic.committed_intentions == (ci,)


def test_builder_committed_intentions_defaults_to_empty_tuple():
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    assert entity.strategic.committed_intentions == ()


# ---------------------------------------------------------------------------
# CapacityEnforcementPhase — order-preserving cap enforcement (New Test 9)
# ---------------------------------------------------------------------------

def _ci(idx: int, status: str = "pending") -> CommittedIntention:
    return CommittedIntention(
        intention_id=f"ci_{idx}", goal_kind="harvesting", target_hint=None,
        sequence_index=idx, status=status,
    )


def _entity_with_cap(max_committed_intentions: int, committed_intentions=()):
    return (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .cognition(max_active_projects=3)
        .strategic(committed_intentions=committed_intentions)
        .build()
    )


def _run_capacity_enforcement(entity, strat_upd: StrategicUpdate):
    state = AuthoritativeState(tick=1, seed=1, entities={1: entity})
    update = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, strategic=strat_upd)},
    )
    refined = CapacityEnforcementPhase.enforce(state, update)
    return refined.entity_updates[1].strategic


def test_max_committed_intentions_cap_enforced_on_add():
    """Adding a 4th entry to an entity already at cap (3) drops the highest sequence_index,
    preserving the front of the sequence (Design Decision 7)."""
    entity = _entity_with_cap(
        3, committed_intentions=(_ci(0), _ci(1), _ci(2)),
    )
    profile = dataclasses.replace(entity.strategic.profile, max_committed_intentions=3)
    entity = dataclasses.replace(entity, strategic=dataclasses.replace(entity.strategic, profile=profile))

    strat_upd = StrategicUpdate(committed_intentions_add_or_update=[_ci(3)])
    refined_strat_upd = _run_capacity_enforcement(entity, strat_upd)

    assert "ci_3" in refined_strat_upd.committed_intentions_remove


def test_under_cap_no_removal():
    entity = _entity_with_cap(3, committed_intentions=(_ci(0),))
    profile = dataclasses.replace(entity.strategic.profile, max_committed_intentions=3)
    entity = dataclasses.replace(entity, strategic=dataclasses.replace(entity.strategic, profile=profile))

    strat_upd = StrategicUpdate(committed_intentions_add_or_update=[_ci(1)])
    state = AuthoritativeState(tick=1, seed=1, entities={1: entity})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, strategic=strat_upd)})
    refined = CapacityEnforcementPhase.enforce(state, update)

    # No removals required -> phase is a noop, entity_updates unchanged for this entity.
    assert refined.entity_updates[1].strategic.committed_intentions_remove == []
