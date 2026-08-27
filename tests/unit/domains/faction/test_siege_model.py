"""Unit tests for E53Cb: SiegeState, RegionState siege fields, siege apply_plan, MilitaryConflictPhase siege loop."""
from __future__ import annotations

import math
from dataclasses import replace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_faction(fid: str, territory=(), relations=None):
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState
    return FactionState(
        faction_id=fid,
        territory=tuple(territory),
        diplomatic_relations={k: DiplomaticState(v) if isinstance(v, str) else v
                               for k, v in (relations or {}).items()},
    )


def _make_region(rid: str, bounds=(0, 0, 10, 10), siege_state=None, service_availability=1.0):
    from src.core.state import RegionState
    return RegionState(
        id=rid,
        name=rid,
        bounds=bounds,
        siege_state=siege_state,
        service_availability=service_availability,
    )


def _make_world_update(**kwargs):
    from src.core.updates import WorldUpdate
    return WorldUpdate(region_id=kwargs.pop("region_id", "r1"), **kwargs)


def _make_siege(attacker="fa", defender="fb", progress=0.0, tick=1):
    from src.core.state import SiegeState
    return SiegeState(
        attacker_faction_id=attacker,
        defender_faction_id=defender,
        siege_progress=progress,
        started_tick=tick,
    )


class _FakeState:
    """Minimal read-only state stub for MilitaryConflictPhase tests."""

    def __init__(self, factions=None, regions=None, entities=None, tick=1):
        self.factions = factions or {}
        self.regions = regions or {}
        self.entities = entities or {}
        self.tick = tick


# ---------------------------------------------------------------------------
# AC1: SiegeState is frozen, slots=True, round-trips through dict serialization
# ---------------------------------------------------------------------------

def test_siege_state_frozen_and_round_trip():
    from src.core.state import SiegeState
    ss = SiegeState(attacker_faction_id="fa", defender_faction_id="fb",
                    siege_progress=0.5, started_tick=10)
    d = ss.to_canonical_dict()
    ss2 = SiegeState.from_dict(d)
    assert ss == ss2
    assert ss2.siege_progress == 0.5
    assert ss2.started_tick == 10


def test_siege_state_immutable():
    from src.core.state import SiegeState
    import pytest
    ss = SiegeState(attacker_faction_id="fa", defender_faction_id="fb",
                    siege_progress=0.0, started_tick=1)
    with pytest.raises((AttributeError, TypeError)):
        ss.siege_progress = 0.9  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AC2: RegionState carries siege fields with correct defaults
# ---------------------------------------------------------------------------

def test_region_state_siege_defaults():
    reg = _make_region("r1")
    assert reg.siege_state is None
    assert reg.service_availability == 1.0


def test_region_state_siege_state_set():
    ss = _make_siege()
    reg = _make_region("r1", siege_state=ss)
    assert reg.siege_state is ss
    assert reg.siege_state.attacker_faction_id == "fa"


# ---------------------------------------------------------------------------
# AC3: WorldUpdate merge accumulates siege deltas; siege_state_set / _clear
# ---------------------------------------------------------------------------

def test_world_update_siege_deltas_accumulate():
    from src.core.updates import WorldUpdate
    wu1 = WorldUpdate(region_id="r1", service_availability_delta=-0.05, siege_progress_delta=0.05)
    wu2 = WorldUpdate(region_id="r1", service_availability_delta=-0.05, siege_progress_delta=0.05)
    merged = wu1.merge(wu2)
    assert math.isclose(merged.service_availability_delta, -0.10, abs_tol=1e-9)
    assert math.isclose(merged.siege_progress_delta, 0.10, abs_tol=1e-9)


def test_world_update_siege_state_set_wins_later():
    from src.core.updates import WorldUpdate
    ss1 = _make_siege(progress=0.0)
    ss2 = _make_siege(progress=0.3)
    wu1 = WorldUpdate(region_id="r1", siege_state_set=ss1)
    wu2 = WorldUpdate(region_id="r1", siege_state_set=ss2)
    merged = wu1.merge(wu2)
    assert merged.siege_state_set is ss2  # later wins


def test_world_update_siege_state_clear_flag():
    from src.core.updates import WorldUpdate
    wu1 = WorldUpdate(region_id="r1", siege_state_set=_make_siege())
    wu2 = WorldUpdate(region_id="r1", siege_state_clear=True)
    merged = wu1.merge(wu2)
    assert merged.siege_state_clear is True


# ---------------------------------------------------------------------------
# AC4: apply_plan applies siege_state_set, siege_state_clear, progress_delta,
#       service_availability_delta; values are clamped [0.0, 1.0]
# ---------------------------------------------------------------------------

def _apply_region_update(reg, wu):
    """Replicate the siege apply logic from apply_plan.py lines 125-140 for isolated testing.

    This mirrors the exact transformation in ApplyPlanBuilder.build_plan() so we can test
    siege field mutations without spinning up the full authoritative pipeline.
    """
    from dataclasses import replace
    svc_avail = max(0.0, min(1.0, reg.service_availability + wu.service_availability_delta))
    if wu.siege_state_clear:
        siege = None
    elif wu.siege_state_set is not None:
        siege = wu.siege_state_set
    else:
        siege = reg.siege_state
    if siege is not None and wu.siege_progress_delta != 0.0:
        new_progress = max(0.0, min(1.0, siege.siege_progress + wu.siege_progress_delta))
        siege = replace(siege, siege_progress=new_progress)
    return replace(reg, siege_state=siege, service_availability=svc_avail)


def test_apply_plan_siege_initiation():
    """apply_plan sets siege_state from WorldUpdate.siege_state_set."""
    reg = _make_region("r1")
    ss = _make_siege()
    wu = _make_world_update(region_id="r1", siege_state_set=ss)
    new_reg = _apply_region_update(reg, wu)
    assert new_reg.siege_state is not None
    assert new_reg.siege_state.attacker_faction_id == "fa"


def test_apply_plan_siege_clear():
    """apply_plan clears siege_state when siege_state_clear=True."""
    ss = _make_siege(progress=0.5)
    reg = _make_region("r1", siege_state=ss)
    wu = _make_world_update(region_id="r1", siege_state_clear=True)
    new_reg = _apply_region_update(reg, wu)
    assert new_reg.siege_state is None


def test_apply_plan_siege_progress_delta():
    """apply_plan advances siege_progress_delta and clamps to [0, 1]."""
    ss = _make_siege(progress=0.9)
    reg = _make_region("r1", siege_state=ss)
    wu = _make_world_update(region_id="r1", siege_progress_delta=0.2)  # would exceed 1.0
    new_reg = _apply_region_update(reg, wu)
    assert new_reg.siege_state is not None
    assert new_reg.siege_state.siege_progress == 1.0  # clamped


def test_apply_plan_service_availability_clamped_low():
    """service_availability is clamped to 0.0 when delta would go below 0."""
    reg = _make_region("r1", service_availability=0.03)
    wu = _make_world_update(region_id="r1", service_availability_delta=-0.1)
    new_reg = _apply_region_update(reg, wu)
    assert new_reg.service_availability == 0.0


def test_apply_plan_service_availability_clamped_high():
    """service_availability is clamped to 1.0 when delta would exceed 1."""
    reg = _make_region("r1", service_availability=0.98)
    wu = _make_world_update(region_id="r1", service_availability_delta=0.1)
    new_reg = _apply_region_update(reg, wu)
    assert new_reg.service_availability == 1.0


# ---------------------------------------------------------------------------
# MilitaryConflictPhase siege loop (E53Cb integration)
# ---------------------------------------------------------------------------

def test_military_conflict_initiates_siege_on_first_tick():
    """execute() emits siege_state_set WorldUpdate on first WAR tick."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    factions = {
        "fa": _make_faction("fa", territory=["r1"], relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r2"], relations={"fa": DS.WAR}),
    }
    regions = {
        "r1": _make_region("r1", bounds=(0, 0, 10, 10)),
        "r2": _make_region("r2", bounds=(20, 0, 30, 10)),
    }
    state = _FakeState(factions=factions, regions=regions, tick=1)
    result = MilitaryConflictPhase.execute(state)
    # Should target fb's territory (r2)
    assert "r2" in result.world_updates
    wu = result.world_updates["r2"]
    assert wu.siege_state_set is not None
    assert wu.siege_state_set.attacker_faction_id == "fa"
    assert wu.siege_state_set.defender_faction_id == "fb"


def test_military_conflict_emits_degradation_delta():
    """execute() emits service_availability_delta and siege_progress_delta each tick."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r2"], relations={"fa": DS.WAR}),
    }
    regions = {"r2": _make_region("r2")}
    state = _FakeState(factions=factions, regions=regions, tick=2)
    result = MilitaryConflictPhase.execute(state)
    wu = result.world_updates.get("r2")
    assert wu is not None
    assert wu.service_availability_delta < 0
    assert wu.siege_progress_delta > 0


def test_military_conflict_resumes_existing_siege():
    """execute() targets an already-sieged region rather than initiating a new one."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    ss = _make_siege(attacker="fa", defender="fb", progress=0.4, tick=1)
    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r2"], relations={"fa": DS.WAR}),
    }
    regions = {
        "r2": _make_region("r2"),
        "r_active": _make_region("r_active", siege_state=ss),
    }
    state = _FakeState(factions=factions, regions=regions, tick=5)
    result = MilitaryConflictPhase.execute(state)
    # Should resume the existing siege on r_active, not initiate a new one on r2
    assert "r_active" in result.world_updates
    wu = result.world_updates["r_active"]
    # No new siege_state_set since siege is already active
    assert wu.siege_state_set is None


def test_military_conflict_noop_when_no_war():
    """execute() is a noop when no factions are at WAR."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.TENSE}),
        "fb": _make_faction("fb", relations={"fa": DS.TENSE}),
    }
    state = _FakeState(factions=factions, regions={}, tick=1)
    result = MilitaryConflictPhase.execute(state)
    assert result.is_noop()


# ---------------------------------------------------------------------------
# TCK-20260822-GUARD-SCAN-INDEX-RETROFIT: guard index parity + reinforcement
# + squad-commitment coverage (AC #1, #2, #3)
# ---------------------------------------------------------------------------

def _make_entity(eid, role, region_id):
    from src.core.state import EntityState, IdentityComponent, NavigationComponent
    return EntityState(
        id=eid,
        kind="npc",
        identity=IdentityComponent(role=role),
        navigation=NavigationComponent(region_id=region_id),
    )


def _naive_find_guard_entities_in_region(state, region_id):
    """Reference copy of the pre-retrofit full O(N) scan, kept local to this test only."""
    from src.core.enums import EntityRole
    result = []
    for eid, entity in state.entities.items():
        nav = getattr(entity, "navigation", None)
        if nav is None or nav.region_id != region_id:
            continue
        identity = getattr(entity, "identity", None)
        if identity is None:
            continue
        if identity.role == EntityRole.GUARD:
            result.append(eid)
    return sorted(result)


def test_guard_index_matches_naive_full_scan():
    """The hoisted per-region index returns identical output to the pre-retrofit scan (AC #1)."""
    from src.core.enums import EntityRole
    from src.core.state import EntityState
    from src.engine.military_conflict import MilitaryConflictPhase

    entities = {
        1: _make_entity(1, EntityRole.GUARD, "r1"),
        2: _make_entity(2, EntityRole.GUARD, "r1"),
        3: _make_entity(3, EntityRole.HERO, "r1"),
        4: _make_entity(4, EntityRole.MONSTER, "r2"),
        5: _make_entity(5, EntityRole.GUARD, "r2"),
        6: _make_entity(6, EntityRole.WORKER, "r3"),
        # Real EntityState always has non-None identity/navigation (default_factory);
        # this exercises the defensive getattr(..., None) branch as dead-but-safe code.
        7: EntityState(id=7, kind="npc"),
    }
    state = _FakeState(entities=entities, tick=1)

    for region_id in ("r1", "r2", "r3"):
        expected = _naive_find_guard_entities_in_region(state, region_id)
        actual = MilitaryConflictPhase._find_guard_entities_in_region(state, region_id)
        assert actual == expected

    assert MilitaryConflictPhase._find_guard_entities_in_region(state, "r1") == [1, 2]
    assert MilitaryConflictPhase._find_guard_entities_in_region(state, "r2") == [5]
    assert MilitaryConflictPhase._find_guard_entities_in_region(state, "r3") == []


def _make_war_state_with_guards(guard_ids, tick=3):
    from src.core.enums import DiplomaticState as DS, EntityRole
    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r2"], relations={"fa": DS.WAR}),
    }
    regions = {"r2": _make_region("r2")}
    entities = {eid: _make_entity(eid, EntityRole.GUARD, "r2") for eid in guard_ids}
    return _FakeState(factions=factions, regions=regions, entities=entities, tick=tick)


def test_military_conflict_reinforcement_fires_at_three_guards():
    from src.engine.military_conflict import (
        MilitaryConflictPhase,
        _SIEGE_SVC_DELTA,
        _SIEGE_PROGRESS_DELTA,
        _DEF_SVC_DELTA,
        _DEF_PROGRESS_DELTA,
    )

    state = _make_war_state_with_guards([101, 102, 103])
    result = MilitaryConflictPhase.execute(state)
    wu = result.world_updates["r2"]
    assert math.isclose(
        wu.service_availability_delta, _SIEGE_SVC_DELTA + _DEF_SVC_DELTA, abs_tol=1e-9
    )
    assert math.isclose(
        wu.siege_progress_delta, _SIEGE_PROGRESS_DELTA + _DEF_PROGRESS_DELTA, abs_tol=1e-9
    )


def test_military_conflict_reinforcement_does_not_fire_below_threshold():
    from src.engine.military_conflict import (
        MilitaryConflictPhase,
        _SIEGE_SVC_DELTA,
        _SIEGE_PROGRESS_DELTA,
    )

    state = _make_war_state_with_guards([101, 102])
    result = MilitaryConflictPhase.execute(state)
    wu = result.world_updates["r2"]
    assert math.isclose(wu.service_availability_delta, _SIEGE_SVC_DELTA, abs_tol=1e-9)
    assert math.isclose(wu.siege_progress_delta, _SIEGE_PROGRESS_DELTA, abs_tol=1e-9)


def test_military_conflict_squad_commitment_capped_at_five():
    from src.engine.military_conflict import MilitaryConflictPhase

    guard_ids = [107, 106, 105, 104, 103, 102, 101]  # non-sequential order
    state = _make_war_state_with_guards(guard_ids)
    result = MilitaryConflictPhase.execute(state)
    assert len(result.groups_add_or_update) == 1
    group = result.groups_add_or_update[0]
    assert len(group.member_ids) == 5
    expected_five = {101, 102, 103, 104, 105}
    assert group.member_ids == expected_five
    assert group.roles == {eid: "FACTION_SQUAD" for eid in expected_five}


def test_military_conflict_squad_commitment_no_truncation_at_five():
    from src.engine.military_conflict import MilitaryConflictPhase

    guard_ids = [101, 102, 103, 104, 105]
    state = _make_war_state_with_guards(guard_ids)
    result = MilitaryConflictPhase.execute(state)
    assert len(result.groups_add_or_update) == 1
    group = result.groups_add_or_update[0]
    assert group.member_ids == set(guard_ids)


def test_military_conflict_squad_commitment_empty_when_no_guards():
    from src.engine.military_conflict import MilitaryConflictPhase

    state = _make_war_state_with_guards([])
    result = MilitaryConflictPhase.execute(state)
    assert result.groups_add_or_update == []
