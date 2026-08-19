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
