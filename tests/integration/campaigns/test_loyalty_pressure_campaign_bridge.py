"""Idea 56 (Drifting Loyalty) real-pipeline bridge proof
(TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE).

Before this ticket, `GroupPhase.resolve()` (the one live per-tick caller of
`PartyLifecycleService.effective_defection_threshold()`/`check_defection()`) always supplied the
`loyalty_pressure` default (0.0) -- `LoyaltyDriftService.compute_loyalty_pressure()`'s real output
never reached live gameplay, confirmed since `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` shipped it.

This test proves the real bridge end-to-end through `GroupPhase.resolve()` itself (not the
already-covered pure `effective_defection_threshold()`/`check_defection()` functions --
`tests/unit/social/test_party_lifecycle.py::test_check_defection_fires_earlier_with_loyalty_pressure`
already proves those): a group anchored inside a real region with a bridged
`state.region_loyalty_pressure` entry defects at fewer grievances than the same group with no
bridged signal (or in a region with none), through the real `GroupPhase.resolve()` call the live
Kernel tick loop actually invokes.
"""
from __future__ import annotations

from src.core.state import AuthoritativeState, EntityState, GroupRecord, RegionState
from src.core.updates import StateUpdate
from src.engine.pipeline_phases.groups import GroupPhase


def _region(region_id: str = "hostile_region") -> RegionState:
    return RegionState(id=region_id, name="Hostile Region", bounds=(0, 0, 100, 100))


def _group(grievance_count: int, anchor=(10.0, 10.0)) -> GroupRecord:
    return GroupRecord(
        id=1,
        leader_id=10,
        member_ids={10, 11},
        anchor=anchor,
        grievance_log=tuple(f"grievance_{i}" for i in range(grievance_count)),
    )


def _members(anchor=(10.0, 10.0)) -> dict:
    # check_defection() requires the candidate entity be live in state.entities. Both members must
    # be positioned within GroupSystem.update_groups()'s own cohesion-radius check of the group's
    # anchor, or update_groups() dissolves the group (< 2 members survive the cohesion filter)
    # before the defection pass this ticket's own bridge feeds ever runs.
    return {
        10: EntityState(id=10, kind="hero", init_position=anchor),
        11: EntityState(id=11, kind="hero", init_position=anchor),
    }


def test_bridged_loyalty_pressure_lowers_the_real_defection_threshold_through_group_phase_resolve():
    # Baseline threshold is 3 (DEFECTION_GRIEVANCE_THRESHOLD, composition_score=0.0 default).
    # A high bridged loyalty_pressure (>= 0.8) lowers it by round(0.8*2)=2 -> effective threshold 1.
    # 2 grievances: below the un-bridged threshold (3), at/above the bridged one (1) -- must defect
    # only once the real pipeline actually reads the bridged signal.
    region = _region()
    group = _group(grievance_count=2)

    state_with_pressure = AuthoritativeState(
        tick=1,
        seed=1,
        regions={region.id: region},
        groups={group.id: group},
        entities=_members(),
        region_loyalty_pressure={region.id: 0.9},
    )
    result_with_pressure = GroupPhase.resolve(state_with_pressure, StateUpdate())
    defected_group = next(g for g in result_with_pressure.groups_add_or_update if g.id == 1)
    assert len(GroupPhase.last_tick_defection_events) == 1, (
        "a real bridged loyalty_pressure >= 0.8 must lower the effective threshold to 1 and fire "
        "a defection at 2 grievances, through the real GroupPhase.resolve() call"
    )
    assert defected_group.member_ids == {10} or defected_group.member_ids == {11}, (
        "exactly one member must have defected"
    )

    # Same group, same 2 grievances, but NO bridged signal for this region (region_loyalty_pressure
    # is empty) -- must reproduce the exact pre-bridge behavior: threshold stays at baseline 3, no
    # defection at 2 grievances.
    state_without_pressure = AuthoritativeState(
        tick=1,
        seed=1,
        regions={region.id: region},
        groups={group.id: group},
        entities=_members(),
        region_loyalty_pressure={},
    )
    GroupPhase.resolve(state_without_pressure, StateUpdate())
    assert len(GroupPhase.last_tick_defection_events) == 0, (
        "with no bridged signal for this region, the effective threshold must stay at the baseline "
        "(3) and 2 grievances must not trigger a defection -- exact pre-bridge behavior preserved"
    )


def test_group_anchored_outside_any_region_defaults_to_zero_pressure_none_safely():
    # anchor (500, 500) is outside the region's bounds (0,0,100,100) -- SpatialQueryService.get_region_at
    # must return None, and the bridge must fall back to 0.0 (not raise) exactly like the pre-bridge
    # default.
    region = _region()
    group = _group(grievance_count=2, anchor=(500.0, 500.0))

    state = AuthoritativeState(
        tick=1,
        seed=1,
        regions={region.id: region},
        groups={group.id: group},
        entities=_members(anchor=(500.0, 500.0)),
        region_loyalty_pressure={region.id: 0.9},
    )
    GroupPhase.resolve(state, StateUpdate())
    assert len(GroupPhase.last_tick_defection_events) == 0, (
        "a group anchored outside any region must fall back to 0.0 loyalty_pressure (None-safe), "
        "not raise or accidentally apply another region's bridged signal"
    )
